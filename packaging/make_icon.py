#!/usr/bin/env python3
"""Generate the Windows icon from the app's own artwork.

The icon is drawn in code (see ``app/ui/icons.py``) rather than kept as an
image file, so this script renders it at every size Windows asks for and packs
them into one ``.ico``.  Run it after changing the logo:

    python packaging/make_icon.py
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import QBuffer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

SIZES = (16, 24, 32, 48, 64, 128, 256)


def png_bytes(icon, size: int) -> bytes:
    buffer = QBuffer()
    buffer.open(QBuffer.WriteOnly)
    icon.pixmap(size, size).toImage().save(buffer, "PNG")
    data = bytes(buffer.data())
    buffer.close()
    return data


def build(target: str) -> str:
    app = QApplication.instance() or QApplication([])
    from app.core import db
    from app.ui import icons, theme
    db.connect()
    theme.apply(app)

    images = [(size, png_bytes(icons.app_icon(), size)) for size in SIZES]

    header = struct.pack("<HHH", 0, 1, len(images))
    offset = len(header) + 16 * len(images)
    entries, payload = b"", b""
    for size, data in images:
        dimension = 0 if size >= 256 else size
        entries += struct.pack("<BBBBHHII", dimension, dimension, 0, 0, 1, 32,
                               len(data), offset)
        payload += data
        offset += len(data)

    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "wb") as handle:
        handle.write(header + entries + payload)
    return target


if __name__ == "__main__":
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = build(os.path.join(here, "app", "resources", "shopdesk.ico"))
    print(f"wrote {path} ({os.path.getsize(path) / 1024:.0f} KB)")
