#!/usr/bin/env python3
"""MAC Address Finder Tool.

Searches for a MAC address across a list of Cisco IOS switches and, optionally,
resolves the matching IP address from Windows DHCP servers via PowerShell.
"""

from __future__ import annotations

import argparse
import getpass
import logging
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import tabulate
from colorama import Fore, Style, init as colorama_init
from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
)
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Configuration defaults
# ---------------------------------------------------------------------------
DEFAULT_IP_LIST = "ip_list.txt"
DEFAULT_DHCP_LIST = "dhcp_servers.txt"
DEFAULT_MAX_WORKERS = 10
CONNECT_TIMEOUT = 15  # seconds, per switch
POWERSHELL_TIMEOUT = 60  # seconds, per DHCP query
# Uplink/port-channel interfaces that should be ignored in the results.
EXCLUDED_PORTS = {"Po1", "Po2", "Po3"}

# A MAC address in any common notation (colon, dash, dot, or no separator).
_MAC_RE = re.compile(
    r"^(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$"  # aa:bb:cc:dd:ee:ff / aa-bb-...
    r"|^(?:[0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}$"   # aabb.ccdd.eeff
    r"|^[0-9A-Fa-f]{12}$"                          # aabbccddeeff
)
# Hostname or IPv4 address, used to validate DHCP server entries before they
# are interpolated into a PowerShell command line.
_HOST_RE = re.compile(r"^[A-Za-z0-9._-]+$")
_IPV4_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")

log = logging.getLogger("mac_finder")


# ---------------------------------------------------------------------------
# MAC address helpers
# ---------------------------------------------------------------------------
def normalize_mac(raw: str) -> str:
    """Return the 12 hex digits of a MAC address, lowercased.

    Raises ValueError if the input is not a valid MAC address.
    """
    candidate = raw.strip()
    if not _MAC_RE.match(candidate):
        raise ValueError(f"Invalid MAC address: {raw!r}")
    return re.sub(r"[.:-]", "", candidate).lower()


def to_cisco_mac(digits: str) -> str:
    """Format 12 hex digits as Cisco dotted notation (aabb.ccdd.eeff)."""
    return f"{digits[0:4]}.{digits[4:8]}.{digits[8:12]}"


def to_dhcp_client_id(digits: str) -> str:
    """Format 12 hex digits as a Windows DHCP ClientId (aa-bb-cc-dd-ee-ff)."""
    return "-".join(digits[i : i + 2] for i in range(0, 12, 2))


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------
def read_lines(filename: str) -> list[str]:
    """Read non-empty, non-comment lines from a text file."""
    path = Path(filename)
    if not path.is_file():
        raise FileNotFoundError(f"Required file not found: {filename}")
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            lines.append(stripped)
    return lines


# ---------------------------------------------------------------------------
# Switch lookup
# ---------------------------------------------------------------------------
@dataclass
class MacEntry:
    switch_ip: str
    mac_address: str
    vlan: str
    port: str


def find_mac_on_switch(
    switch_ip: str, username: str, password: str, cisco_mac: str
) -> list[MacEntry]:
    """Connect to a single switch and return matching MAC table entries."""
    device = {
        "device_type": "cisco_ios",
        "host": switch_ip,
        "username": username,
        "password": password,
        "timeout": CONNECT_TIMEOUT,
        "fast_cli": False,
    }
    try:
        with ConnectHandler(**device) as conn:
            output = conn.send_command(
                f"show mac address-table | include {cisco_mac}"
            )
    except NetmikoAuthenticationException:
        log.warning("Authentication failed for %s", switch_ip)
        return []
    except NetmikoTimeoutException:
        log.warning("Connection timed out for %s", switch_ip)
        return []
    except Exception as exc:  # noqa: BLE001 - report and continue with others
        log.warning("Connection to %s failed: %s", switch_ip, exc)
        return []

    entries: list[MacEntry] = []
    for line in output.splitlines():
        fields = line.split()
        # Expected layout: VLAN  MAC  TYPE  PORT
        if len(fields) < 4:
            continue
        vlan, mac, _type, port = fields[0], fields[1], fields[2], fields[3]
        if cisco_mac.lower() not in mac.lower():
            continue
        if port in EXCLUDED_PORTS:
            continue
        entries.append(MacEntry(switch_ip, mac, vlan, port))
    return entries


def search_switches(
    ip_list: list[str],
    username: str,
    password: str,
    cisco_mac: str,
    max_workers: int,
) -> list[MacEntry]:
    """Query all switches concurrently using a bounded thread pool."""
    results: list[MacEntry] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                find_mac_on_switch, ip, username, password, cisco_mac
            ): ip
            for ip in ip_list
        }
        with tqdm(total=len(futures), desc="🔗 Connecting to switches") as pbar:
            for future in as_completed(futures):
                results.extend(future.result())
                pbar.update(1)
    return results


# ---------------------------------------------------------------------------
# DHCP lookup (Windows / PowerShell)
# ---------------------------------------------------------------------------
def _run_powershell(command: str) -> str:
    """Run a PowerShell command and return its stdout, or '' on failure."""
    executable = shutil.which("pwsh") or shutil.which("powershell")
    if not executable:
        raise RuntimeError(
            "PowerShell (pwsh/powershell) is required for DHCP lookups "
            "but was not found on this system."
        )
    try:
        completed = subprocess.run(
            [executable, "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=True,
            timeout=POWERSHELL_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        log.warning("PowerShell command timed out")
        return ""
    if completed.returncode != 0 and completed.stderr.strip():
        log.debug("PowerShell error: %s", completed.stderr.strip())
    return completed.stdout


def _validate_server(server: str) -> bool:
    if not _HOST_RE.match(server):
        log.warning("Skipping invalid DHCP server entry: %r", server)
        return False
    return True


def get_dhcp_scopes(server: str) -> list[str]:
    """Return the list of ScopeIds defined on a DHCP server."""
    command = (
        f"Get-DhcpServerv4Scope -ComputerName '{server}' "
        f"-ErrorAction SilentlyContinue | "
        f"Select-Object -ExpandProperty ScopeId"
    )
    output = _run_powershell(command)
    return [s.strip() for s in output.splitlines() if _IPV4_RE.match(s.strip())]


def find_ip_for_mac(mac_digits: str, dhcp_servers: list[str]) -> str | None:
    """Search DHCP leases on each server/scope for the given MAC address."""
    client_id = to_dhcp_client_id(mac_digits)
    servers = [s for s in dhcp_servers if _validate_server(s)]

    # Enumerate scopes once per server.
    scopes_by_server = {server: get_dhcp_scopes(server) for server in servers}
    total = sum(len(scopes) for scopes in scopes_by_server.values())
    if total == 0:
        log.warning("No DHCP scopes were found on the configured servers.")
        return None

    done = 0
    for server, scopes in scopes_by_server.items():
        for scope_id in scopes:
            command = (
                f"Get-DhcpServerv4Lease -ComputerName '{server}' "
                f"-ScopeId '{scope_id}' -ClientId '{client_id}' "
                f"-ErrorAction SilentlyContinue | "
                f"Select-Object -ExpandProperty IPAddress"
            )
            output = _run_powershell(command).strip()
            done += 1
            progress = (done / total) * 100
            print(
                f"{Fore.BLUE}🔍 {done}/{total} scopes searched "
                f"({progress:.1f}%).{Style.RESET_ALL}"
            )
            for line in output.splitlines():
                line = line.strip()
                if _IPV4_RE.match(line):
                    return line
    return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def prompt_mac(message: str) -> str:
    """Prompt until a valid MAC address is entered, return its 12 hex digits."""
    while True:
        raw = input(f"{Fore.CYAN}{message}{Style.RESET_ALL}").strip()
        try:
            return normalize_mac(raw)
        except ValueError as exc:
            print(f"{Fore.RED}❌ {exc}{Style.RESET_ALL}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find a MAC address across Cisco switches and DHCP servers."
    )
    parser.add_argument(
        "--ip-list", default=DEFAULT_IP_LIST,
        help=f"File with switch IPs, one per line (default: {DEFAULT_IP_LIST})",
    )
    parser.add_argument(
        "--dhcp-list", default=DEFAULT_DHCP_LIST,
        help=f"File with DHCP servers (default: {DEFAULT_DHCP_LIST})",
    )
    parser.add_argument(
        "--username", help="Switch username (prompted if omitted)",
    )
    parser.add_argument(
        "--workers", type=int, default=DEFAULT_MAX_WORKERS,
        help=f"Concurrent switch connections (default: {DEFAULT_MAX_WORKERS})",
    )
    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug logging",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    colorama_init(strip=args.no_color)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    try:
        ip_list = read_lines(args.ip_list)
    except FileNotFoundError as exc:
        print(f"{Fore.RED}❌ {exc}{Style.RESET_ALL}")
        return 1
    if not ip_list:
        print(f"{Fore.RED}❌ No switch IPs found in {args.ip_list}.{Style.RESET_ALL}")
        return 1

    print(f"{Fore.GREEN}Welcome to the MAC Address Finder Tool!{Style.RESET_ALL}")
    username = args.username or input(f"{Fore.YELLOW}Enter Username: {Style.RESET_ALL}")
    password = getpass.getpass(f"{Fore.YELLOW}Enter Password: {Style.RESET_ALL}")

    while True:
        mac_digits = prompt_mac("Enter the MAC address you want to search for: ")
        cisco_mac = to_cisco_mac(mac_digits)

        entries = search_switches(
            ip_list, username, password, cisco_mac, args.workers
        )

        table = [["Switch IP", "MAC Address", "VLAN", "Port"]]
        table.extend([e.switch_ip, e.mac_address, e.vlan, e.port] for e in entries)

        print(f"{Fore.GREEN}Results for all switches:{Style.RESET_ALL}")
        if len(table) == 1:
            print(f"{Fore.YELLOW}No matching entries found.{Style.RESET_ALL}")
        else:
            print(tabulate.tabulate(table, headers="firstrow", tablefmt="fancy_grid"))

        if input(
            f"{Fore.MAGENTA}Do you want to find the IP of this MAC? (Y/N): "
            f"{Style.RESET_ALL}"
        ).strip().lower() == "y":
            try:
                dhcp_servers = read_lines(args.dhcp_list)
                ip = find_ip_for_mac(mac_digits, dhcp_servers)
            except (FileNotFoundError, RuntimeError) as exc:
                print(f"{Fore.RED}❌ {exc}{Style.RESET_ALL}")
            else:
                if ip:
                    print(
                        f"{Fore.GREEN}✅ IP address for {cisco_mac} is "
                        f"{ip}{Style.RESET_ALL}"
                    )
                else:
                    print(
                        f"{Fore.RED}❌ IP address for {cisco_mac} not "
                        f"found.{Style.RESET_ALL}"
                    )

        if input(
            f"{Fore.MAGENTA}Do you want to continue? (Y/N): {Style.RESET_ALL}"
        ).strip().lower() != "y":
            break

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        sys.exit(130)
