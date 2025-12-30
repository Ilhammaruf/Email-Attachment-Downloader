# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Email Attachment Downloader
#
# Build command:
#   pyinstaller EmailAttachmentDownloader.spec

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all customtkinter data files (themes, etc.)
customtkinter_datas = collect_data_files('customtkinter')

# Collect tkcalendar data files
tkcalendar_datas = collect_data_files('tkcalendar')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        *customtkinter_datas,
        *tkcalendar_datas,
    ],
    hiddenimports=[
        'customtkinter',
        'PIL',
        'PIL._tkinter_finder',
        'dateutil',
        'tkcalendar',
        'babel.numbers',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EmailAttachmentDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to True if you want a console window for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EmailAttachmentDownloader',
)
