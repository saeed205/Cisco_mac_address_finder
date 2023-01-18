
# MAC Address Search Script

This script is used to search for a specific MAC address on multiple Cisco switches. The script uses the following libraries:

-   netmiko
-   threading
-   tqdm
-   tabulate

## Requirements

-   Make sure to install the tqdm library before running this script
-   Use this command: `pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org tqdm`

## Usage

1.  Run the script
2.  Input the following:

-   Username
-   Password
-   MAC address you want to search for

3.  The script reads the IP addresses from the file "ip_list.txt" and create a thread for each IP address to connect to the switch and search for the MAC address
4.  The results are collected in a table and displayed at the end, with the option to exclude specific ports
5.  The script uses the Cisco IOS command "show mac address-table" to search for the MAC address in the output.

## Note

-   Make sure the IP_list.txt file is present in the same directory as the script
-   Make sure that the devices you want to search for is reachable via the IPs provided in the IP_list.txt
-   Make sure that the provided credentials have enough privilage to run the "show mac address-table" command.
-   The script is tested on Cisco IOS devices and may not work on other network devices.

## Additional Info

This script is designed to search for a specific MAC address on multiple Cisco switches at a time. It uses the netmiko library to connect to the switches, threading to connect to multiple switches in parallel, tqdm to display a progress bar, and tabulate to display the results in a table format. The script prompts the user for a username, password, and the MAC address to search for.

## Support

For any questions or issues please open an issue on this repository or contact the developer.
