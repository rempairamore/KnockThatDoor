from setuptools import setup
import os
import sys
from cx_Freeze import setup, Executable

# Base directory
base_dir = os.path.dirname(os.path.abspath(__file__))

# Define icon path explicitly
icon_path = os.path.join(base_dir, 'img', 'icona.ico')

# Check if icon file exists and print a message
if os.path.exists(icon_path):
    print(f"ICON FOUND: {icon_path}")
else:
    print(f"WARNING: Icon not found at {icon_path}!")

# Get all files in the img directory
img_dir = os.path.join(base_dir, 'img')
img_files = []
if os.path.exists(img_dir):
    for f in os.listdir(img_dir):
        if not f.startswith('.'):
            source = os.path.join(img_dir, f)
            dest = os.path.join('img', f)
            img_files.append((source, dest))

# Include the configuration file
additional_files = [
    (os.path.join(base_dir, 'conf.json'), 'conf.json')
]

# Combine all data files
build_exe_options = {
    "packages": [
        "os", 
        "json", 
        "socket", 
        "threading", 
        "PIL", 
        "pystray", 
        "tkinter",
        "logging",
        "datetime",
        "traceback",
        "subprocess"
    ],
    "excludes": ["tkinter.test", "unittest"],
    "include_files": img_files + additional_files,
    "include_msvcr": True,
}

# Create a shortcut in the Start Menu / Programs folder
shortcut_table = [
    # Desktop shortcut
    ("DesktopShortcut",            # Shortcut
     "DesktopFolder",              # Directory_
     "KnockThatDoor",              # Name
     "TARGETDIR",                  # Component_
     "[TARGETDIR]KnockThatDoor.exe", # Target
     None,                         # Arguments
     None,                         # Description
     None,                         # Hotkey
     None,                         # Icon
     None,                         # IconIndex
     None,                         # ShowCmd
     "TARGETDIR",                  # WkDir
     ),
    
    # Start menu shortcut
    ("StartMenuShortcut",          # Shortcut
     "ProgramMenuFolder",          # Directory_
     "KnockThatDoor",              # Name
     "TARGETDIR",                  # Component_
     "[TARGETDIR]KnockThatDoor.exe", # Target
     None,                         # Arguments
     None,                         # Description
     None,                         # Hotkey
     None,                         # Icon
     None,                         # IconIndex
     None,                         # ShowCmd
     "TARGETDIR",                  # WkDir
     ),
    
    # Autostart shortcut
    ("AutostartShortcut",          # Shortcut
     "StartupFolder",              # Directory_
     "KnockThatDoor",              # Name
     "TARGETDIR",                  # Component_
     "[TARGETDIR]KnockThatDoor.exe", # Target
     None,                         # Arguments
     None,                         # Description
     None,                         # Hotkey
     None,                         # Icon
     None,                         # IconIndex
     None,                         # ShowCmd
     "TARGETDIR",                  # WkDir
     ),
]

# Create .MSI installer with specified options
msi_data = {
    "Shortcut": shortcut_table,
}

# Configure how MSI interfaces with users
bdist_msi_options = {
    "data": msi_data,
    "upgrade_code": "{12345678-1234-1234-1234-123456789012}",
    "add_to_path": False,
    "initial_target_dir": r"[ProgramFilesFolder]\KnockThatDoor",
}

# Base for the executable
base = None
if sys.platform == "win32":
    base = "Win32GUI"  # Use this to hide the console window

setup(
    name="KnockThatDoor",
    version="1.2.0",
    description="A port knocking utility for Windows",
    author="rempairamore",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options
    },
    executables=[
        Executable(
            "main.py",
            base=base,
            icon=icon_path,  # Use the defined path directly
            target_name="KnockThatDoor.exe",
            shortcut_name="KnockThatDoor",
            shortcut_dir="ProgramMenuFolder"
        )
    ],
    install_requires=[
        'pillow>=9.0.0',
        'pystray>=0.19.0',
        'win10toast>=0.9.0;platform_system=="Windows"',
        'pywin32>=300;platform_system=="Windows"',
    ],
)