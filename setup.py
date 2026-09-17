"""
setup.py
Build script for converting app.py into a native macOS .app bundle via py2app inside Conda.
Usage:
    python setup.py py2app
"""

import sys
from setuptools import setup

# 1. Raise recursion limit to prevent py2app dependency graph analyzer from crashing
sys.setrecursionlimit(10000)

APP = ['app.py']
DATA_FILES = []

OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'AppIcon.icns',
    'plist': {
        'LSUIElement': True,  # Hides Dock icon; runs as pure menu bar item
        'CFBundleName': "STT Menu Server",
        'CFBundleDisplayName': "STT Menu Server",
        'CFBundleIdentifier': "com.local.stt.menuapp",
        'CFBundleVersion': "1.0.0",
        'NSHighResolutionCapable': True,
    },
    'packages': [
        'rumps',
        'fastapi',
        'uvicorn',
        'python_multipart',
        'starlette',
        'numpy',
    ],
    # Treat mlx and mlx_whisper as site-packages / framework binaries to stop deep recursion loop
    'includes': [
        'subprocess',
        'threading',
        'tempfile',
        'mlx',
        'mlx_whisper',
    ],
    'site_packages': True,
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)