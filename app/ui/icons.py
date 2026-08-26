"""Line icons drawn from inline SVG.

Keeping the icon set in code means there are no image files to lose, and each
icon can be recoloured to match the current theme.
"""

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from app.ui import theme

_PATHS: dict[str, str] = {
    "sell": "M3 6h18l-2 10H5L3 6z M3 6L2.5 3.5H1 M8 20a1 1 0 100-2 1 1 0 000 2z"
            " M17 20a1 1 0 100-2 1 1 0 000 2z",
    "products": "M21 8l-9-5-9 5 9 5 9-5z M3 8v8l9 5 9-5V8 M12 13v8",
    "stock": "M4 7h16v13H4z M4 7l2-4h12l2 4 M9 12h6",
    "customers": "M16 20v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2 M9 10a4 4 0 100-8 4 4 0 000 8z"
                 " M22 20v-2a4 4 0 00-3-3.87 M17 2.13A4 4 0 0117 10",
    "sales": "M5 3h14v18l-3-2-2 2-2-2-2 2-3-2V3z M9 8h6 M9 12h6 M9 16h3",
    "dues": "M2 7h20v11H2z M2 11h20 M6 15h4",
    "reports": "M4 20V10 M10 20V4 M16 20v-7 M22 20H2",
    "settings": "M12 15a3 3 0 100-6 3 3 0 000 6z"
                " M19.4 15a1.6 1.6 0 00.3 1.8l.1.1a2 2 0 01-2.8 2.8l-.1-.1a1.6 1.6 0"
                " 00-1.8-.3 1.6 1.6 0 00-1 1.5V21a2 2 0 01-4 0v-.1A1.6 1.6 0 008 19.4"
                " a1.6 1.6 0 00-1.8.3l-.1.1a2 2 0 01-2.8-2.8l.1-.1a1.6 1.6 0 00.3-1.8"
                " 1.6 1.6 0 00-1.5-1H2a2 2 0 010-4h.1A1.6 1.6 0 004.6 8a1.6 1.6 0"
                " 00-.3-1.8l-.1-.1a2 2 0 012.8-2.8l.1.1a1.6 1.6 0 001.8.3H9a1.6 1.6 0"
                " 001-1.5V2a2 2 0 014 0v.1a1.6 1.6 0 001 1.5 1.6 1.6 0 001.8-.3l.1-.1"
                " a2 2 0 012.8 2.8l-.1.1a1.6 1.6 0 00-.3 1.8V9a1.6 1.6 0 001.5 1H22"
                " a2 2 0 010 4h-.1a1.6 1.6 0 00-1.5 1z",
    "users": "M12 2l8 4v6c0 5-3.4 8.6-8 10-4.6-1.4-8-5-8-10V6l8-4z M9 12l2 2 4-4",
    "search": "M11 19a8 8 0 100-16 8 8 0 000 16z M21 21l-4.3-4.3",
    "plus": "M12 5v14 M5 12h14",
    "minus": "M5 12h14",
    "trash": "M3 6h18 M8 6V4h8v2 M19 6l-1 14H6L5 6 M10 11v6 M14 11v6",
    "edit": "M11 4H4v16h16v-7 M18.5 2.5a2.1 2.1 0 013 3L12 15l-4 1 1-4 9.5-9.5z",
    "print": "M6 9V2h12v7 M6 18H4v-7h16v7h-2 M6 14h12v8H6z",
    "download": "M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4 M7 10l5 5 5-5 M12 15V3",
    "refresh": "M21 12a9 9 0 11-3-6.7L21 8 M21 3v5h-5",
    "check": "M20 6L9 17l-5-5",
    "close": "M18 6L6 18 M6 6l12 12",
    "back": "M19 12H5 M12 19l-7-7 7-7",
    "hold": "M10 4H6v16h4V4z M18 4h-4v16h4V4z",
    "resume": "M5 3l14 9-14 9V3z",
    "alert": "M12 9v4 M12 17h.01 M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9"
             " a2 2 0 00-3.4 0z",
    "cash": "M2 6h20v12H2z M12 15a3 3 0 100-6 3 3 0 000 6z M6 9v.01 M18 15v.01",
    "card": "M2 6h20v12H2z M2 10h20 M6 15h4",
    "mobile": "M7 2h10v20H7z M11 18h2",
    "bank": "M3 21h18 M5 21V10 M19 21V10 M3 10l9-7 9 7 M9 21v-6h6v6",
    "barcode": "M3 5v14 M6 5v14 M9 5v10 M12 5v14 M15 5v10 M18 5v14 M21 5v14",
    "customer_add": "M14 20v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2 M8 10a4 4 0 100-8 4 4 0 000 8z"
                    " M19 8v6 M22 11h-6",
    "tag": "M20.6 13.4l-7.2 7.2a2 2 0 01-2.8 0l-8-8V3h9.6l8.4 8.4a2 2 0 010 2z M7 7h.01",
    "logout": "M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4 M16 17l5-5-5-5 M21 12H9",
    "moon": "M21 12.8A9 9 0 1111.2 3a7 7 0 009.8 9.8z",
    "sun": "M12 17a5 5 0 100-10 5 5 0 000 10z M12 1v2 M12 21v2 M4.2 4.2l1.4 1.4"
           " M18.4 18.4l1.4 1.4 M1 12h2 M21 12h2 M4.2 19.8l1.4-1.4 M18.4 5.6l1.4-1.4",
    "shop": "M3 9l1.5-6h15L21 9 M3 9v11h18V9 M3 9h18 M9 20v-7h6v7",
    "clock": "M12 21a9 9 0 100-18 9 9 0 000 18z M12 7v5l3 2",
    "up": "M12 19V5 M5 12l7-7 7 7",
    "down": "M12 5v14 M5 12l7 7 7-7",
    "history": "M3 3v5h5 M3.05 13A9 9 0 106 5.3L3 8 M12 7v5l4 2",
    "grid": "M3 3h7v7H3z M14 3h7v7h-7z M14 14h7v7h-7z M3 14h7v7H3z",
    "empty_cart": "M3 6h18l-2 10H5L3 6z M3 6L2.5 3.5H1 M8 20a1 1 0 100-2 1 1 0 000 2z"
                  " M17 20a1 1 0 100-2 1 1 0 000 2z",
}


def svg(name: str, color: str, size: int = 20, width: float = 1.7) -> str:
    path = _PATHS.get(name, _PATHS["grid"])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'width="{size}" height="{size}" fill="none" stroke="{color}" '
        f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round">'
        f'<path d="{path}"/></svg>')


def pixmap(name: str, color: str | None = None, size: int = 20,
           width: float = 1.7, ratio: float = 2.0) -> QPixmap:
    tone = color or theme.hex_of("text_muted")
    renderer = QSvgRenderer(QByteArray(svg(name, tone, size, width).encode()))
    canvas = QPixmap(int(size * ratio), int(size * ratio))
    canvas.setDevicePixelRatio(ratio)
    canvas.fill(Qt.transparent)
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.Antialiasing)
    # The painter on a high-DPI pixmap works in logical units, so the target
    # rect is the icon's nominal size -- not the pixmap's pixel dimensions.
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    return canvas


def icon(name: str, color: str | None = None, size: int = 20,
         width: float = 1.7) -> QIcon:
    return QIcon(pixmap(name, color, size, width))


def app_icon() -> QIcon:
    """Window and taskbar icon: a shop front on the accent colour."""
    size = 256
    canvas = QPixmap(size, size)
    canvas.fill(Qt.transparent)
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(theme.color("accent"))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(0, 0, size, size, 56, 56)
    renderer = QSvgRenderer(QByteArray(svg("shop", "#FFFFFF", 24, 1.9).encode()))
    renderer.render(painter, canvas.rect().adjusted(58, 58, -58, -58))
    painter.end()
    return QIcon(canvas)
