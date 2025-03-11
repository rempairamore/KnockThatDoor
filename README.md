# KnockThatDoor

KnockThatDoor is a simple port knocking utility I built for macOS that sits in your menu bar. If you're not familiar with menu bar apps, they're those small icons that live in the top-right corner of your screen next to your clock and other system stuff. Super convenient for quick access without cluttering your dock.

![Screenshot of the app in action](img/screenshot_placeholder.png)

## What the heck is Port Knocking?

Port knocking is a neat security trick where ports on your server stay closed until someone sends the right sequence of connection attempts. Think of it like a secret knock on a speakeasy door - if you don't know the pattern, you're not getting in. This keeps your services hidden from random port scanners and only opens up when you send the correct "knock" sequence.

## Configuration

Everything is controlled through a `conf.json` file. It's pretty straightforward:

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

Here's what each setting does:
- `service_name`: What you'll see in the menu dropdown
- `ports_to_knock`: The sequence of ports to hit, with protocol (udp/tcp)
- `target_address`: Where to send the knocks (IP or hostname)
- `testing_address_and_port`: What to check after knocking to see if it worked
- `delay_in_milliseconds`: How long to wait between knocks (in ms)

### Editing Your Configuration

No need to hunt down config files manually:

1. Click the KnockThatDoor icon in your menu bar
2. Select "**Edit Config**" from the menu
3. Make your changes in the text editor that pops up
4. Save it
5. Go back to the app and hit "Refresh Config" to apply changes

Dead simple. This way you can quickly add or modify services whenever you need to.

## How To Use It

Once you've set everything up:

1. Click the KnockThatDoor icon
2. Pick a service from the dropdown
3. Let it do its thing - it'll send the knocks and test the connection
4. Check the colored icon to see what happened:
   - 🟢 Green means you're in! Service is accessible
   - 🔴 Red means something went wrong

## Download and Installation

### Option 1: Just Grab the App
Download the pre-built .app from [the releases page](link_to_latest_release) and drag it to your Applications folder. Done.

### Option 2: Build It Yourself

If you prefer to build from source (or don't trust random .app files from the internet, which is fair):

```bash
# Clone the repo
git clone https://github.com/your_username/KnockThatDoor.git
cd KnockThatDoor

# Install dependencies (two options)
pip install -r requirements.txt
# OR install them manually
pip install rumps py2app

# Build it
python3 setup.py py2app
```

The compiled app will be in the `dist` folder - just drag it to Applications.

## Troubleshooting


You can check che logs by clicking "View Logs" inside the app.

## License

KnockThatDoor is free software under the GNU GPL v3. Basically:

- You can use, modify, and share it
- If you distribute modified versions, they need to be under the same license
- No warranties - it might work great or blow up spectacularly

