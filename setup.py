"""
setup.py
Build script for converting app.py into a native macOS .app bundle via py2app inside Conda.
Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ['app.py']
DATA_FILES = []

OPTIONS = {
    'argv_emulation': False,
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
        'mlx_whisper',
        'python_multipart',
        'starlette',
        'mlx',
        'numpy',
    ],
    'includes': [
        'subprocess',
        'threading',
        'tempfile',
    ],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)