# MAC Address Finder Tool

This tool searches for a MAC address across multiple Cisco IOS switches and can
optionally resolve the matching IP address from Windows DHCP servers. It queries
the switches concurrently and presents the results (switch IP, VLAN, and port)
in a table.

## Features

- **Search MAC addresses on network switches:** Connects to every switch in
  `ip_list.txt` concurrently and reports where the MAC address is learned,
  including the switch IP, VLAN, and port.
- **Retrieve IP address from DHCP servers:** Optionally searches the Windows
  DHCP servers listed in `dhcp_servers.txt` for the lease matching the MAC.
- **Input validation:** Accepts MAC addresses in any common notation
  (`aa:bb:cc:dd:ee:ff`, `aa-bb-...`, `aabb.ccdd.eeff`, or `aabbccddeeff`) and
  normalizes them automatically.
- **Robust connectivity:** Bounded concurrency, per-connection timeouts, and
  clear logging instead of silently swallowed errors.

## Requirements

- Python 3.9+
- Required Python libraries (see `requirements.txt`):
  - `netmiko`
  - `tqdm`
  - `tabulate`
  - `colorama`
- For the optional DHCP lookup: a Windows environment (or a host with `pwsh`)
  where the `DhcpServer` PowerShell module is available.

## Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/saeed205/Cisco_mac_address_finder.git
    cd Cisco_mac_address_finder
    ```

2. **Install the required Python libraries:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Create the inventory files** from the provided templates:
    ```bash
    cp ip_list.txt.example ip_list.txt
    cp dhcp_servers.txt.example dhcp_servers.txt
    ```
    Then edit `ip_list.txt` (switch IPs, one per line) and `dhcp_servers.txt`
    (DHCP server hostnames/IPs, one per line). These files are git-ignored so
    your real addresses are never committed.

## Usage

```bash
python main.py
```

Optional arguments:

```text
--ip-list PATH      Switch IP list file (default: ip_list.txt)
--dhcp-list PATH    DHCP server list file (default: dhcp_servers.txt)
--username NAME     Switch username (prompted if omitted)
--workers N         Concurrent switch connections (default: 10)
--no-color          Disable colored output
-v, --verbose       Enable debug logging
```

Follow the prompts to enter your credentials and the MAC address to search for.
If you choose to resolve the IP, the tool searches the configured DHCP servers.

## File Descriptions

- `main.py`: The main script.
- `ip_list.txt`: Switch IP addresses to query (created from the template).
- `dhcp_servers.txt`: DHCP servers to query (created from the template).
- `*.example`: Templates for the inventory files.

## Notes

- Ensure you have permission to access the switches and DHCP servers.
- The DHCP lookup uses PowerShell (`pwsh` or `powershell`) and the `DhcpServer`
  module; it only works where those are available.
- The tool assumes Cisco IOS switches. Adjust the `device_type` in
  `find_mac_on_switch` for other platforms.

## License

This project is licensed under the MIT License.

---

Happy networking!
