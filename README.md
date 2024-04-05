
# MAC Address Search Script

This script is a Python script that is used to search for a specific MAC address on multiple Cisco switches and DHCP servers. It uses the netmiko library to connect to the switches, the 'ConnectHandler' function to establish the connection, and the 'send_command' function to execute the command 'show mac address-table' on each switch. The 'getpass' library is used to hide the password entered by the user. The 'tabulate' library is used to display the results in a table format. The 'tqdm' library is used to show the progress bar. The 'Threading' library is used to create multiple threads to connect to the switches in parallel. The script also uses PowerShell commands to search for the specific MAC address on DHCP servers and returns the associated IP address if found.

## Getting Started

To use this script, you need to have a list of IP addresses of the switches in a text file named "ip_list.txt" in the same directory as the script. The script will read the IP addresses from this file and connect to each switch in parallel using the netmiko library.

You also need to install the libraries by `pip install -r requirements.txt`

## Usage

1.  Run the script using the command `python main.py`
2.  The script will prompt you to enter your username and password. These will be used to connect to the switches.
3.  The script will then prompt you to enter the MAC address you want to search for.
4.  The script will search for the MAC address on all the switches in the "ip_list.txt" file, and also on DHCP servers.
5.  The script will display the results in a table format, showing the switch IP, MAC address, VLAN, and port.
6.  The script will also show the associated IP address of the MAC address on DHCP servers.
7.  The script will then prompt you if you want to continue searching for another MAC address.
8.  If you choose to continue, the script will repeat steps 3-6. If you choose to exit, the script will end.

## Changelog

### v1.1

-   Added a new function `set_mac_address_on_dhcp_servers` that uses PowerShell commands to search for a specific MAC address on DHCP servers and returns the associated IP address if found.
-   Now, the script will search for the mac address on both switches and DHCP servers, and show the result.
-   Updated the `tqdm` library to show the progress of searching on DHCP servers too.

### v1.0

-   Initial release of the script that searches for a specific MAC address on multiple Cisco switches.
-   Script uses the netmiko library to connect to the switches, the 'ConnectHandler' function to establish the connection, and the 'send_command' function to execute the command 'show mac address-table' on each switch.
-   The 'getpass' library is used to hide the password entered by the user.
-   The 'tabulate' library is used to display the results in a table format.
-   The 'tqdm' library is used to show the progress bar.
-   The 'Threading' library is used to create multiple threads to connect to the switches in parallel.
