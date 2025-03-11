from setuptools import setup

APP = ['main.py']
DATA_FILES = [
    'img/icona.png',
    'img/connected.png',
    'img/error.png',
    'img/loading1.png',
    'img/closed.png',
    'conf.json'
]
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'LSUIElement': True,  # Makes it a menubar app without dock icon
        'CFBundleName': 'KnockThatDoor',
        'CFBundleDisplayName': 'KnockThatDoor',
        'CFBundleIdentifier': 'com.rempairamore.knockthatdoor',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyleft rempairamore',
    },
    'packages': ['rumps'],
    'iconfile': 'img/icona.icns',  # If you have an .icns file
}

setup(
    app=APP,
    name='KnockThatDoor',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    license='GPL-3.0',
)