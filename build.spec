# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Add src directory to path
src_path = str(Path('.').absolute() / 'src')

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[src_path],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'qasync',
        'aiohttp',
        'yt_dlp',
        'urllib.request',
        'ui',
        'ui.main_window',
        'ui.download_item',
        'ui.settings_dialog',
        'ui.styles',
        'core',
        'core.chzzk_api',
        'core.downloader',
        'core.config',
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
    name='ChzzkDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ChzzkDownloader',
)

app = BUNDLE(
    coll,
    name='ChzzkDownloader.app',
    icon=None,
    bundle_identifier='com.chzzkdownloader.app',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
    },
)
