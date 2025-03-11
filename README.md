# KnockThatDoor

KnockThatDoor is a port knocking utility for macOS that runs in your menu bar. A menu bar app lives in the top-right corner of your screen alongside other system icons, providing quick access without cluttering your dock or taking up space in your application switcher.

![Application Screenshot](img/screenshot_placeholder.png)

## Configuration

KnockThatDoor is configured through a `conf.json` file that defines the services and their knocking sequences.

### The conf.json Structure

```json
{
  "services": [
    {
      "service_name": "my_ssh_server",
      "ports_to_knock": ["8000udp", "9000tcp", "7000udp"],
      "target_address": "192.168.1.10",
      "testing_address_and_port": "192.168.1.10:22",
      "delay_in_milliseconds": 300
    },
    {
      "service_name": "home_plex_server",
      "ports_to_knock": ["51320udp", "3231udp", "8080tcp", "7040udp"],
      "target_address": "10.0.0.5",
      "testing_address_and_port": "10.0.0.5:32400",
      "delay_in_milliseconds": 300
    }
  ]
}
```

Parameters explained:
- `service_name`: The name that will appear in the menu bar dropdown
- `ports_to_knock`: The sequence of ports to knock on, with protocol specified (udp/tcp)
- `target_address`: The IP address or hostname where to send the knocks
- `testing_address_and_port`: The address and port to test after knocking to verify success
- `delay_in_milliseconds`: The delay between each knock in the sequence

### Editing Configuration Directly from the App

The app allows you to edit the configuration file without having to locate it manually:

1. Click on the KnockThatDoor icon in your menu bar
2. Select "**Edit Config**" from the dropdown menu
3. Your default text editor will open with the conf.json file
4. Make your changes and save the file
5. Go back to the app and select "Refresh Config" to apply your changes

This makes it easy to add new services or modify existing ones without leaving the app interface.

## How to Use

After configuring your services:

1. Click the KnockThatDoor icon in the menu bar
2. Select a service from the dropdown menu
3. The app will send the knock sequence and test if the service is accessible
4. A color indicator will show the result:
   - 🟢 Green: The service is now accessible
   - 🔴 Red: Failed to access the service

## What is Port Knocking?

Port knocking is a security method where a server's ports remain closed and invisible until a specific sequence of connection attempts is detected. This adds an extra layer of security by hiding services from port scanners and only opening ports after receiving the correct "secret knock."

## Download and Installation

You can download the pre-compiled application (.app) directly from [here](link_to_latest_release) and move it to your Applications folder.

If you prefer to build from source:

```bash
# Install dependencies
pip install rumps py2app

# Clone the repository
git clone https://github.com/your_username/KnockThatDoor.git
cd KnockThatDoor

# Build the application
python3 setup.py py2app
```

## Logs

Logs are stored in the `./log` folder within the application directory. Check these files if you're experiencing issues with the application.

## License

KnockThatDoor is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

KnockThatDoor is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.