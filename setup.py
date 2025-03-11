from setuptools import setup
import os

APP = ['main.py']

# Get all image files
img_files = [os.path.join('img', f) for f in os.listdir('img') if os.path.isfile(os.path.join('img', f))]

DATA_FILES = [
    ('', ['conf.json']),
    ('img', img_files)
]

OPTIONS = {
    'argv_emulation': False,  # Set to False for better compatibility
    'plist': {
        'LSUIElement': True,  # Makes it a menubar app without dock icon
        'CFBundleName': 'KnockThatDoor',
        'CFBundleDisplayName': 'KnockThatDoor',
        'CFBundleIdentifier': 'com.rempairamore.knockthatdoor',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyleft Mr nobody'
    },
    'packages': ['rumps'],
    'iconfile': 'img/icona.icns',
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