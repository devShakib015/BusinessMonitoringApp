"""A small bar chart, painted directly.

A shop owner reads their week as a shape before they read it as numbers, so
the reports screen draws one.  Painting it here keeps the download free of a
charting dependency.
"""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPainterPath
from PySide6.QtWidgets import QSizePolicy, QWidget

from app.core import settings
from app.ui import theme


class BarChart(QWidget):
    """Vertical bars with a value axis and hover read-out."""

    def __init__(self, parent=None, height: int = 220):
        super().__init__(parent)
        self._points: list[tuple[str, int]] = []
        self._hover = -1
        self.setMinimumHeight(height)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMouseTracking(True)

    def set_points(self, points: list[tuple[str, int]]) -> None:
        self._points = points
        self.update()

    def mouseMoveEvent(self, event):  # noqa: N802 - Qt naming
        index = self._bar_at(event.position().x())
        if index != self._hover:
            self._hover = index
            self.update()

    def leaveEvent(self, event):  # noqa: N802 - Qt naming
        self._hover = -1
        self.update()

    def _bar_at(self, x: float) -> int:
        if not self._points:
            return -1
        left, width = 52, max(1, self.width() - 62)
        slot = width / len(self._points)
        index = int((x - left) // slot)
        return index if 0 <= index < len(self._points) else -1

    def paintEvent(self, event):  # noqa: N802 - Qt naming
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self._points:
            painter.setPen(theme.color("text_faint"))
            painter.drawText(self.rect(), Qt.AlignCenter, "No sales in this period")
            return

        peak = max(value for _label, value in self._points) or 1
        left, right = 52, self.width() - 10
        top, bottom = 12, self.height() - 24
        plot_height = bottom - top
        slot = (right - left) / len(self._points)
        bar_width = max(4.0, min(38.0, slot * 0.6))

        # Grid lines and axis labels
        painter.setFont(theme.ui_font(8))
        metrics = QFontMetrics(painter.font())
        for step in range(5):
            value = peak * step / 4
            y = bottom - plot_height * step / 4
            painter.setPen(QColor(theme.hex_of("border")))
            painter.drawLine(left - 6, int(y), right, int(y))
            painter.setPen(theme.color("text_faint"))
            painter.drawText(0, int(y) - metrics.height() // 2, left - 12,
                             metrics.height(), Qt.AlignRight | Qt.AlignVCenter,
                             _compact(int(value)))

        accent = theme.color("accent")
        for index, (label_text, value) in enumerate(self._points):
            height = plot_height * value / peak
            x = left + slot * index + (slot - bar_width) / 2
            rect = QRectF(x, bottom - height, bar_width, max(2.0, height))

            path = QPainterPath()
            path.addRoundedRect(rect, 4, 4)
            colour = QColor(accent)
            if self._hover == index:
                colour = colour.lighter(118)
            elif self._hover >= 0:
                colour.setAlpha(120)
            painter.fillPath(path, colour)

            if len(self._points) <= 16 or index % max(1, len(self._points) // 10) == 0:
                painter.setPen(theme.color("text_faint"))
                painter.drawText(QRectF(left + slot * index, bottom + 4, slot, 18),
                                 Qt.AlignCenter, label_text)

        if self._hover >= 0:
            label_text, value = self._points[self._hover]
            painter.setPen(theme.color("text"))
            painter.setFont(theme.ui_font(9, painter.font().Bold))
            painter.drawText(QRectF(left, 0, right - left, 14),
                             Qt.AlignRight | Qt.AlignVCenter,
                             f"{label_text}   {settings.money(value)}")


class BarList(QWidget):
    """Ranked horizontal bars — used for best sellers."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[tuple[str, int, str]] = []
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def set_rows(self, rows: list[tuple[str, int, str]]) -> None:
        self._rows = rows
        self.setMinimumHeight(max(60, len(rows) * 34 + 8))
        self.update()

    def paintEvent(self, event):  # noqa: N802 - Qt naming
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if not self._rows:
            painter.setPen(theme.color("text_faint"))
            painter.drawText(self.rect(), Qt.AlignCenter, "Nothing sold yet")
            return

        peak = max(value for _name, value, _detail in self._rows) or 1
        painter.setFont(theme.ui_font(9))
        for index, (name, value, detail) in enumerate(self._rows):
            y = 4 + index * 34
            track = QRectF(0, y + 17, self.width(), 7)
            painter.fillPath(_rounded(track, 3), QColor(theme.hex_of("surface_sunken")))

            filled = QRectF(0, y + 17, self.width() * value / peak, 7)
            painter.fillPath(_rounded(filled, 3), theme.color("accent"))

            painter.setPen(theme.color("text"))
            painter.drawText(QRectF(0, y, self.width() - 120, 16),
                             Qt.AlignLeft | Qt.AlignVCenter, name)
            painter.setPen(theme.color("text_muted"))
            painter.drawText(QRectF(self.width() - 120, y, 120, 16),
                             Qt.AlignRight | Qt.AlignVCenter, detail)


def _rounded(rect: QRectF, radius: float) -> QPainterPath:
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    return path


def _compact(minor: int) -> str:
    """Axis labels: 1.2k rather than 1,200.00."""
    unit = 10 ** settings.decimals()
    value = minor / unit if unit else minor
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}k"
    return f"{value:.0f}"
