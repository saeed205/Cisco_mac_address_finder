import subprocess
from netmiko import ConnectHandler
from threading import Thread
from tqdm import tqdm
import tabulate
import getpass
from colorama import Fore, Style, init

# Initialize colorama
init()

def read_dhcp_servers(filename):
    with open(filename, "r") as file:
        dhcp_servers = file.read().splitlines()
    return dhcp_servers

def set_mac_address_on_dhcp_servers(mac_address_full, dhcp_servers):
    mac_addressPC = mac_address_full.replace(":", "").replace(".", "")
    
    total_scopes = 0
    current_scope = 0
    for server in dhcp_servers:
        ps_command = f"Get-DhcpServerv4Scope -ComputerName {server} | Select-Object ScopeId"
        output = subprocess.run(["powershell", ps_command], capture_output=True)
        scope_ids = output.stdout.decode("utf-8").strip().split("\n")
        total_scopes += len(scope_ids)

    for server in dhcp_servers:
        ps_command = f"Get-DhcpServerv4Scope -ComputerName {server} | Select-Object ScopeId"
        output = subprocess.run(["powershell", ps_command], capture_output=True)
        scope_ids = output.stdout.decode("utf-8").strip().split("\n")

        for scope_id in scope_ids:
            scope_id = scope_id.strip().split(" ")[-1]
            ps_command = f"Get-DhcpServerv4Lease -ComputerName {server} -ScopeId {scope_id} -ClientId {mac_addressPC} | Select-Object IPAddress"
            output = subprocess.run(["powershell", ps_command], capture_output=True)
            output_str = output.stdout.decode("utf-8")
            current_scope += 1
            progress = (current_scope / total_scopes) * 100
            print(f"{Fore.BLUE}🔍 {current_scope} out of {total_scopes} scopes searched. {progress:.2f}% completed.{Style.RESET_ALL}")
            if "IPAddress" in output_str:
                PC_ip = output_str.strip().split(" ")[-1]
                return PC_ip
    return None

def connect_to_switch(switch_ip, username, password, mac_address, table, pbar):
    try:
        net_connect = ConnectHandler(ip=switch_ip, device_type='cisco_ios', username=username, password=password)
        output = net_connect.send_command(f"show mac address-table | include {mac_address}")
        net_connect.disconnect()
    except:
        print(f"{Fore.RED}❌ TCP connection to device failed for IP address: {switch_ip}{Style.RESET_ALL}")
        pbar.update(1)
        return

    for line in output.split("\n"):
        if "    " in line:
            elements = line.split()
            if elements[3] not in ["Po1", "Po2", "Po3"]:
                table.append([switch_ip, elements[1], elements[0], elements[3]])
    pbar.update(1)

def main():
    print(f"{Fore.GREEN}Welcome to the MAC Address Finder Tool!{Style.RESET_ALL}")
    username = input(f"{Fore.YELLOW}Enter Username: {Style.RESET_ALL}")
    password = getpass.getpass(f"{Fore.YELLOW}Enter Password: {Style.RESET_ALL}")

    while True:
        mac_address = input(f"{Fore.CYAN}Enter the MAC address you want to search for: {Style.RESET_ALL}").strip()

        table = [["Switch IP", "MAC Address", "VLAN", "Port"]]
        with open("ip_list.txt", "r") as f:
            ip_list = f.read().splitlines()

        pbar = tqdm(total=len(ip_list), desc="🔗 Connecting to switches")

        threads = []
        for switch_ip in ip_list:
            t = Thread(target=connect_to_switch, args=(switch_ip, username, password, mac_address, table, pbar))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()
        pbar.close()

        print(f"{Fore.GREEN}Results for all switches:{Style.RESET_ALL}")
        print(tabulate.tabulate(table, headers="firstrow", tablefmt="fancy_grid"))

        if input(f"{Fore.MAGENTA}Do you want to find IP of this Mac? (Y/N): {Style.RESET_ALL}").strip().lower() == 'y':
            mac_address_full = input(f"{Fore.CYAN}Enter the full MAC address you want to search for: {Style.RESET_ALL}").strip()
            dhcp_servers = read_dhcp_servers("dhcp_servers.txt")
            PC_ip = set_mac_address_on_dhcp_servers(mac_address_full, dhcp_servers)
            if PC_ip:
                print(f"{Fore.GREEN}✅ IP address for MAC address {mac_address_full} is {PC_ip}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ IP address for MAC address {mac_address_full} not found.{Style.RESET_ALL}")

        if input(f"{Fore.MAGENTA}Do you want to continue? (Y/N): {Style.RESET_ALL}").strip().lower() != 'y':
            break

if __name__ == "__main__":
    main()
