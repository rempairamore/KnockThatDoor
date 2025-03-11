## How to Create a DMG for KnockThatDoor

This document describes the process of creating a macOS DMG installer for the KnockThatDoor application.

### Prerequisites

1. Build the app using py2app:
   ```
   python3.11 setup.py py2app
   ```
   This creates the application bundle in the `dist/` directory.

### Creating the DMG

1. Install the create-dmg tool:
   ```
   brew install create-dmgbrew install create-dmg
   ```

2. Run the create-dmg command:
   ```
   create-dmg \
     --volname "KnockThatDoor" \
     --volicon "img/icona.icns" \
     --window-pos 200 120 \
     --window-size 800 400 \
     --icon-size 100 \
     --icon "KnockThatDoor.app" 200 190 \
     --app-drop-link 600 185 \
     --no-internet-enable \
     "KnockThatDoor.dmg" \
     "dist/KnockThatDoor.app"
   ```

### Parameter Explanation

- `--volname "KnockThatDoor"`: Sets the volume name that appears when mounted
- `--volicon "img/icona.icns"`: Uses the specified icon for the DMG volume
- `--window-pos 200 120`: Position of the Finder window when opened
- `--window-size 800 400`: Size of the Finder window
- `--icon-size 100`: Size of icons in the Finder window
- `--icon "KnockThatDoor.app" 200 190`: Position of the app icon in the window
- `--app-drop-link 600 185`: Position of the Applications folder symbolic link
- `--no-internet-enable`: Disables internet-enabled DMG features
- `"KnockThatDoor.dmg"`: Output DMG filename
- `"dist/KnockThatDoor.app"`: Path to the application bundle

### Notes

- A temporary file named `rw_.dmg` might be created during the process. This is a read-write version used during creation and can be safely deleted.
- To verify the DMG, mount it by double-clicking and check that:
  1. The app icon appears at the specified position
  2. The Applications folder symbolic link appears
  3. The volume has the correct icon and name

### Distribution

The final DMG file (`KnockThatDoor.dmg`) can be distributed to users who can then install the application by dragging it to the Applications folder using the provided symbolic link.