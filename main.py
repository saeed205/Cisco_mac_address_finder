from netmiko import ConnectHandler
from threading import Thread
from tqdm import tqdm

import subprocess
import tabulate
import getpass


def set_mac_address_on_dhcp_servers(mac_address_full):
    mac_addressPC = mac_address_full.replace(":", "").replace(".", "")
    dhcp_servers = ["Enter DHCP Server1",
                    "Enter DHCP Server2",
                    "Enter DHCP Server3"]

    total_scopes = 0
    current_scope = 0
    for server in dhcp_servers:
        # Get all scope IDs on the DHCP server
        ps_command = f"Get-DhcpServerv4Scope -ComputerName {
            server} | Select-Object ScopeId"
        output = subprocess.run(
            ["powershell", ps_command], capture_output=True)
        scope_ids = output.stdout.decode("utf-8").strip().split("\n")
        total_scopes += len(scope_ids)

    for server in dhcp_servers:
        # Get all scope IDs on the DHCP server
        ps_command = f"Get-DhcpServerv4Scope -ComputerName {
            server} | Select-Object ScopeId"
        output = subprocess.run(
            ["powershell", ps_command], capture_output=True)
        scope_ids = output.stdout.decode("utf-8").strip().split("\n")

        for scope_id in scope_ids:
            scope_id = scope_id.strip().split(" ")[-1]
            # Search for the MAC address on each scope ID
            ps_command = f"Get-DhcpServerv4Lease -ComputerName {server} -ScopeId {
                scope_id} -ClientId {mac_addressPC} | Select-Object IPAddress"
            output = subprocess.run(
                ["powershell", ps_command], capture_output=True)
            output_str = output.stdout.decode("utf-8")
            current_scope += 1
            progress = (current_scope / total_scopes) * 100
            print(f"{current_scope} out of {total_scopes} scopes searched. {progress:.2f}% completed.")
            if "IPAddress" in output_str:
                PC_ip = output_str.strip().split(" ")[-1]
                break
        else:
            continue
        break
    else:
        PC_ip = None

    return PC_ip


username = input("Enter Username: ")
password = getpass.getpass("Enter Password: ")

while True:
    mac_address = input("Enter the MAC address you want to search for: ")

    # Initialize table
    table = []
    table.append(["Switch IP", "MAC Address", "VLAN", "Port"])

    # Read the IP addresses from the file
    with open("ip_list.txt", "r") as f:
        ip_list = f.read().splitlines()
        pbar = tqdm(total=len(ip_list), desc="Connecting to switches")
        # Function to connect to a switch and get output

        def connect_to_switch(switch_ip):
            try:
                net_connect = ConnectHandler(
                    ip=switch_ip, device_type='cisco_ios', username=username, password=password)
                output = net_connect.send_command(
                    f"show mac address-table | include {mac_address}")
                net_connect.disconnect()
            except:
                print("TCP connection to device failed for IP address: ", switch_ip)
                return

            # Parse the output
            for line in output.split("\n"):
                if "    " in line:
                    elements = line.split()
                    table.append(
                        [switch_ip, elements[1], elements[0], elements[3]])
            # Update the progress bar
            pbar.update(1)

        # Create threads
        threads = []
        for switch_ip in ip_list:
            t = Thread(target=connect_to_switch, args=(switch_ip,))
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()
        pbar.close()

    print("Results for all switches:")
    table = [row for row in table if not any(
        x in row[3] for x in ["Po1", "Po2", "Po3"])]
    print(tabulate.tabulate(table, headers="firstrow", tablefmt="fancy_grid"))
    if input("Do you want to find IP of this Mac? (Y/N)").lower() == 'y':
        mac_address_full = input(
            "Enter the MAC address you want to search for: ")
        PC_ip = set_mac_address_on_dhcp_servers(mac_address_full)
        print(f"IP address for MAC address {mac_address_full} is {PC_ip}")
    if input("Do you want to continue? (Y/N)").lower() != 'y':
        break
