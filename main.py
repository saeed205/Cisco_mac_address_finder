
from netmiko import ConnectHandler
from threading import Thread
from tqdm import tqdm
import getpass
import tabulate
# Make sure to install the tqdm library before running this script
# Use this command: pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org tqdm

username = input("Enter Username: ")
password = getpass.getpass("Enter Password: ")
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
