from setuptools import setup
import os

APP = ['main.py']

# Get all files in the img directory
img_dir = 'img'
img_files = []
if os.path.exists(img_dir):
    img_files = [os.path.join('img', f) for f in os.listdir(img_dir) if not f.startswith('.')]

DATA_FILES = [
    ('', ['conf.json']),  # Put conf.json in the Resources folder
    ('img', img_files)    # Keep the img directory structure
]

OPTIONS = {
    'argv_emulation': False,  # Disable for better compatibility
    'plist': {
        'LSUIElement': True,  # Makes it a menubar app without dock icon
        'CFBundleName': 'KnockThatDoor',
        'CFBundleDisplayName': 'KnockThatDoor',
        'CFBundleIdentifier': 'com.rempairamore.knockthatdoor',
        'CFBundleVersion': '1.1.0',
        'CFBundleShortVersionString': '1.1.0',
        'NSHumanReadableCopyright': 'Copyleft rempairamore'
    },
    'packages': ['rumps'],
    'iconfile': os.path.join(img_dir, 'icona.icns') if os.path.exists(os.path.join(img_dir, 'icona.icns')) else None,
    'includes': ['rumps', 'socket', 'select', 'json', 'datetime', 'logging', 'threading'],
}

setup(
    app=APP,
    name='KnockThatDoor',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    license='GPL-3.0',
)