# MAC Address Finder Tool

This tool allows users to search for MAC addresses on multiple network switches and optionally find the corresponding IP address through DHCP servers. The tool uses Python and various libraries to automate the process of querying switches and DHCP servers to retrieve the necessary information.

## Features

- **Search MAC addresses on network switches:** The tool connects to a list of network switches and searches for the specified MAC address, displaying the results including the switch IP, VLAN, and port.
- **Retrieve IP address from DHCP servers:** If the user opts to find the IP address associated with the MAC address, the tool will search the provided DHCP servers for this information.

## Requirements

- Python 3.x
- Required Python libraries:
  - `netmiko`
  - `tqdm`
  - `tabulate`
  - `colorama`

## Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/saeed205/Cisco_mac_address_finder.git
    cd Cisco_mac_address_finder
    ```

2. **Install the required Python libraries:**
    ```bash
    pip install netmiko tqdm tabulate colorama
    ```

3. **Create the necessary files:**
    - `ip_list.txt`: A text file containing the IP addresses of the switches, one per line.
    - `dhcp_servers.txt`: A text file containing the hostnames or IP addresses of the DHCP servers, one per line.

## Usage

1. **Run the script:**
    ```bash
    python main.py
    ```

2. **Follow the prompts:**
    - Enter your username and password for the switches.
    - Enter the MAC address you want to search for.
    - If you choose to find the IP address for the MAC, enter the full MAC address when prompted.

## Example

```bash
$ python main.py
```

You will be prompted to enter your username and password, followed by the MAC address you want to search for. The tool will then connect to the switches listed in `ip_list.txt` and search for the specified MAC address. The results will be displayed in a table format.

If you choose to find the IP address for the MAC, you will be prompted to enter the full MAC address, and the tool will search the DHCP servers listed in `dhcp_servers.txt` for the corresponding IP address.

## File Descriptions

- `main.py`: The main script to run the MAC address finder tool.
- `ip_list.txt`: A list of switch IP addresses to be queried.
- `dhcp_servers.txt`: A list of DHCP server hostnames or IP addresses to be queried.

## Notes

- Ensure you have the necessary permissions to access the switches and DHCP servers.
- The tool uses `subprocess` to run PowerShell commands on the DHCP servers. Ensure PowerShell is available on your system.
- The tool assumes that the network switches are Cisco IOS devices. Modify the `ConnectHandler` parameters as needed for different device types.

## License

This project is licensed under the MIT License.

---

Happy networking!