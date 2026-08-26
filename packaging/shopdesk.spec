# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build for ShopDesk.

Builds a one-folder application (fast to start, easy for an installer to lay
down) and a single-file portable executable from the same analysis.

    pyinstaller packaging/shopdesk.spec --noconfirm
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
sys.path.insert(0, ROOT)

from app import config  # noqa: E402

WINDOWS = sys.platform == "win32"
# The .ico and the version resource are Windows-only; on other platforms the
# spec still builds so the packaging can be checked without a Windows machine.
ICON = os.path.join(ROOT, "app", "resources", "shopdesk.ico") if WINDOWS else None
VERSION_FILE = os.path.join(SPECPATH, "version_info.txt") if WINDOWS else None

# Qt ships far more than a point-of-sale till needs.  Dropping the modules the
# app never imports takes the download from ~140 MB to well under half that.
EXCLUDED_QT = [
    "PySide6.Qt3DAnimation", "PySide6.Qt3DCore", "PySide6.Qt3DExtras",
    "PySide6.Qt3DInput", "PySide6.Qt3DLogic", "PySide6.Qt3DRender",
    "PySide6.QtBluetooth", "PySide6.QtCharts", "PySide6.QtDataVisualization",
    "PySide6.QtDesigner", "PySide6.QtHelp", "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets", "PySide6.QtNfc", "PySide6.QtOpenGL",
    "PySide6.QtOpenGLWidgets", "PySide6.QtPdf", "PySide6.QtPdfWidgets",
    "PySide6.QtPositioning", "PySide6.QtQml", "PySide6.QtQuick",
    "PySide6.QtQuick3D", "PySide6.QtQuickControls2", "PySide6.QtQuickWidgets",
    "PySide6.QtRemoteObjects", "PySide6.QtScxml", "PySide6.QtSensors",
    "PySide6.QtSerialPort", "PySide6.QtSpatialAudio", "PySide6.QtSql",
    "PySide6.QtStateMachine", "PySide6.QtTest", "PySide6.QtTextToSpeech",
    "PySide6.QtWebChannel", "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineQuick", "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebSockets",
]

analysis = Analysis(
    [os.path.join(ROOT, "run.py")],
    pathex=[ROOT],
    binaries=[],
    datas=[(os.path.join(ROOT, "app", "resources"), "app/resources")],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    # Pillow stays: reportlab imports it at module load, so excluding it
    # builds cleanly and then fails the moment an invoice is generated.
    excludes=EXCLUDED_QT + ["tkinter", "unittest", "pydoc_data", "pytest",
                            "numpy", "matplotlib"],
    noarchive=False,
)
pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name=config.APP_NAME,
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=ICON,
    version=VERSION_FILE,
)

COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    name=config.APP_NAME,
)

portable = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name=f"{config.APP_NAME}-portable",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    icon=ICON,
    version=VERSION_FILE,
)
