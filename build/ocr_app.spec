# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for OCR Desktop Application.
Builds a portable Windows executable.

Usage:
    pyinstaller build/ocr_app.spec
"""

import sys
from pathlib import Path

# Project root
PROJECT_ROOT = Path(SPECPATH).parent.resolve()

# Application name
APP_NAME = 'OCR_Dokument'

# Main script
MAIN_SCRIPT = str(PROJECT_ROOT / 'main.py')

# Data files to include
datas = [
    # Add any additional data files here
    # (str(PROJECT_ROOT / 'assets'), 'assets'),
]

# Hidden imports that PyInstaller might miss
hiddenimports = [
    'customtkinter',
    'PIL',
    'PIL.Image',
    'pytesseract',
    'pandas',
    'openpyxl',
    'docx',
    'reportlab',
    'reportlab.lib',
    'reportlab.platypus',
    'pdf2image',
    'tkinter',
    'tkinter.filedialog',
    'tkinter.messagebox',
]

# Analysis
a = Analysis(
    [MAIN_SCRIPT],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

# Create PYZ archive
pyz = PYZ(a.pure, a.zipped_data)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here: icon='assets/icon.ico'
)
