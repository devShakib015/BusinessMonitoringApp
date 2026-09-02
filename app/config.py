"""Application-wide constants and filesystem paths.

Data lives outside the installation directory so that shop data survives
application updates and works when the app is installed to a read-only
location (Program Files, /Applications).  Dropping a file named
``portable.txt`` next to the executable switches the app to portable mode,
keeping the database beside the binary instead — useful for running from a
USB stick on a shop counter.
"""

import os
import sys

APP_NAME = "ShopDesk"
APP_TAGLINE = "Point of sale for small shops"
APP_VERSION = "2.0.1"
APP_ID = "shopdesk"
PUBLISHER = "devShakib015"
PROJECT_URL = "https://github.com/devShakib015/BusinessMonitoringApp"


def is_frozen() -> bool:
    """True when running from a PyInstaller bundle."""
    return getattr(sys, "frozen", False)


def bundle_dir() -> str:
    """Directory holding read-only resources (icons, fonts, sample data)."""
    if is_frozen():
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def install_dir() -> str:
    """Directory the application was launched from."""
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _portable_mode() -> bool:
    return os.path.exists(os.path.join(install_dir(), "portable.txt"))


def data_dir() -> str:
    """Writable directory for the database, backups and generated documents."""
    override = os.environ.get("SHOPDESK_DATA_DIR")
    if override:
        path = override
    elif _portable_mode():
        path = os.path.join(install_dir(), "data")
    elif sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        path = os.path.join(base, APP_NAME)
    elif sys.platform == "darwin":
        path = os.path.expanduser(f"~/Library/Application Support/{APP_NAME}")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
        path = os.path.join(base, APP_ID)
    os.makedirs(path, exist_ok=True)
    return path


def db_path() -> str:
    return os.path.join(data_dir(), "shopdesk.db")


def documents_dir() -> str:
    """Default destination for generated invoices and exports."""
    path = os.path.join(data_dir(), "documents")
    os.makedirs(path, exist_ok=True)
    return path


def resource(*parts: str) -> str:
    """Absolute path to a bundled resource (the Windows icon, for instance)."""
    return os.path.join(bundle_dir(), "resources", *parts)
