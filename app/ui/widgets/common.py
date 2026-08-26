"""Small building blocks shared by every screen."""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (QAbstractItemView, QFrame, QHBoxLayout, QHeaderView,
                               QLabel, QLineEdit, QPushButton, QSizePolicy,
                               QTableWidget, QVBoxLayout, QWidget)

from app.core import settings
from app.core.money import format_plain, parse_amount
from app.core.quantity import format_qty, parse_qty
from app.ui import icons, theme


# ── Layout helpers ────────────────────────────────────────────────────────────

def vbox(parent=None, margins=(0, 0, 0, 0), spacing=0) -> QVBoxLayout:
    layout = QVBoxLayout(parent)
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    return layout


def hbox(parent=None, margins=(0, 0, 0, 0), spacing=0) -> QHBoxLayout:
    layout = QHBoxLayout(parent)
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    return layout


def label(text: str, object_name: str = "", bold: bool = False,
          size: int | None = None, color: str | None = None) -> QLabel:
    widget = QLabel(text)
    if object_name:
        widget.setObjectName(object_name)
    if bold or size:
        font = widget.font()
        if size:
            font.setPointSize(size)
        if bold:
            font.setWeight(QFont.DemiBold)
        widget.setFont(font)
    if color:
        widget.setStyleSheet(f"color: {color};")
    return widget


def hint(text: str) -> QLabel:
    """Small explanatory text under a field, wrapped so it is never clipped."""
    widget = label(text, "Faint")
    widget.setWordWrap(True)
    return widget


def divider(vertical: bool = False) -> QFrame:
    line = QFrame()
    line.setObjectName("VDivider" if vertical else "Divider")
    line.setFrameShape(QFrame.VLine if vertical else QFrame.HLine)
    line.setFixedWidth(1) if vertical else line.setFixedHeight(1)
    return line


def spacer(width: int = 0, height: int = 0) -> QWidget:
    widget = QWidget()
    widget.setFixedSize(QSize(width, height)) if width and height else None
    widget.setSizePolicy(
        QSizePolicy.Expanding if not width else QSizePolicy.Fixed,
        QSizePolicy.Expanding if not height else QSizePolicy.Fixed)
    return widget


def clear_layout(layout) -> None:
    """Empty a layout, detaching its widgets immediately.

    ``deleteLater`` alone is not enough: until the event loop runs the widget
    is still a child of the panel, and a widget with no layout paints itself
    at its default 640x480 over whatever is underneath.
    """
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()
        elif item.layout() is not None:
            clear_layout(item.layout())
            item.layout().deleteLater()


class Card(QFrame):
    """A padded white panel; the standard container for content."""

    def __init__(self, parent=None, padding: int = 18, spacing: int = 12,
                 flat: bool = False):
        super().__init__(parent)
        self.setObjectName("CardFlat" if flat else "Card")
        self.body = vbox(self, (padding, padding, padding, padding), spacing)


class PageHeader(QWidget):
    """Title, one-line description and a row of actions."""

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        row = hbox(self, spacing=12)
        text = vbox(spacing=2)
        text.addWidget(label(title, "PageTitle"))
        if subtitle:
            text.addWidget(label(subtitle, "PageSubtitle"))
        row.addLayout(text)
        row.addStretch(1)
        self.actions = hbox(spacing=8)
        row.addLayout(self.actions)

    def add_action(self, widget: QWidget) -> QWidget:
        self.actions.addWidget(widget)
        return widget


def button(text: str, variant: str = "", icon_name: str = "",
           on_click=None, shortcut: str = "", tooltip: str = "") -> QPushButton:
    widget = QPushButton(text)
    if variant:
        widget.setProperty("variant", variant)
    if icon_name:
        tone = {"primary": "#FFFFFF", "danger": "#FFFFFF"}.get(
            variant, theme.hex_of("accent") if variant == "soft"
            else theme.hex_of("text_muted"))
        widget.setIcon(icons.icon(icon_name, tone, 17))
        widget.setIconSize(QSize(17, 17))
    if on_click:
        widget.clicked.connect(on_click)
    if shortcut:
        widget.setShortcut(QKeySequence(shortcut))
        tooltip = f"{tooltip or text}  ({shortcut})"
    if tooltip:
        widget.setToolTip(tooltip)
    widget.setCursor(Qt.PointingHandCursor)
    return widget


class StatCard(QFrame):
    """One headline number with a label and an optional hint underneath."""

    def __init__(self, caption: str, value: str = "—", hint: str = "",
                 accent: str | None = None, icon_name: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        body = vbox(self, (16, 14, 16, 14), 4)

        top = hbox(spacing=8)
        top.addWidget(label(caption.upper(), "StatLabel"))
        top.addStretch(1)
        if icon_name:
            badge = QLabel()
            badge.setPixmap(icons.pixmap(icon_name, accent or theme.hex_of("text_faint"), 16))
            top.addWidget(badge)
        body.addLayout(top)

        self._value = label(value, "StatValue")
        if accent:
            self._value.setStyleSheet(f"color: {accent};")
        body.addWidget(self._value)

        self._hint = label(hint, "StatHint")
        self._hint.setVisible(bool(hint))
        body.addWidget(self._hint)

    def set_value(self, value: str, hint: str = "") -> None:
        self._value.setText(value)
        self._hint.setText(hint)
        self._hint.setVisible(bool(hint))


class EmptyState(QWidget):
    """Shown in place of a table when there is genuinely nothing to show."""

    def __init__(self, icon_name: str, title: str, hint: str = "", parent=None):
        super().__init__(parent)
        body = vbox(self, (20, 40, 20, 40), 10)
        body.setAlignment(Qt.AlignCenter)

        art = QLabel()
        art.setPixmap(icons.pixmap(icon_name, theme.hex_of("text_faint"), 40, 1.4))
        art.setAlignment(Qt.AlignCenter)
        body.addWidget(art)

        heading = label(title, "EmptyTitle")
        heading.setAlignment(Qt.AlignCenter)
        body.addWidget(heading)

        if hint:
            note = label(hint, "EmptyHint")
            note.setAlignment(Qt.AlignCenter)
            note.setWordWrap(True)
            body.addWidget(note)


class SearchField(QLineEdit):
    """Search box with a magnifier, a clear button and Escape-to-clear."""

    def __init__(self, placeholder: str = "Search…", parent=None, big: bool = False):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setClearButtonEnabled(True)
        self.addAction(icons.icon("search", theme.hex_of("text_faint"),
                                  20 if big else 16), QLineEdit.LeadingPosition)
        if big:
            self.setObjectName("SearchField")
        QShortcut(QKeySequence(Qt.Key_Escape), self, activated=self.clear)


class MoneyEdit(QLineEdit):
    """Text field that reads and writes amounts in minor units."""

    value_changed = Signal(int)

    def __init__(self, parent=None, allow_empty: bool = True,
                 placeholder: str | None = None):
        super().__init__(parent)
        self._allow_empty = allow_empty
        self.setAlignment(Qt.AlignRight)
        self.setPlaceholderText(
            placeholder if placeholder is not None
            else format_plain(0, settings.decimals(), grouping=False))
        self.textChanged.connect(self._announce)

    def value(self) -> int:
        text = self.text().strip()
        if not text:
            if self._allow_empty:
                return 0
            raise ValueError("Enter an amount.")
        return parse_amount(text, settings.decimals())

    def value_or_none(self) -> int | None:
        try:
            return self.value()
        except ValueError:
            return None

    def set_value(self, minor: int, grouping: bool = False) -> None:
        self.setText(format_plain(minor, settings.decimals(), grouping))

    def clear_value(self) -> None:
        self.clear()

    def mark(self, invalid: bool) -> None:
        self.setProperty("state", "error" if invalid else "")
        self.style().unpolish(self)
        self.style().polish(self)

    def _announce(self) -> None:
        value = self.value_or_none()
        self.mark(value is None)
        if value is not None:
            self.value_changed.emit(value)


class QuantityEdit(QLineEdit):
    """Text field that reads and writes quantities in thousandths."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignRight)
        self.setPlaceholderText("1")

    def value(self) -> int:
        return parse_qty(self.text().strip() or "1")

    def value_or_none(self) -> int | None:
        try:
            return self.value()
        except ValueError:
            return None

    def set_value(self, qty: int) -> None:
        self.setText(format_qty(qty))


def table(headers: list[str], stretch_column: int = 0,
          row_height: int = 38) -> QTableWidget:
    """A read-only table configured the way every list in the app wants it."""
    widget = QTableWidget(0, len(headers))
    widget.setHorizontalHeaderLabels(headers)
    widget.verticalHeader().setVisible(False)
    widget.setSelectionBehavior(QAbstractItemView.SelectRows)
    widget.setSelectionMode(QAbstractItemView.SingleSelection)
    widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
    widget.setAlternatingRowColors(False)
    widget.setShowGrid(False)
    widget.setWordWrap(False)
    widget.verticalHeader().setDefaultSectionSize(row_height)
    widget.horizontalHeader().setHighlightSections(False)
    widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    widget.horizontalHeader().setSectionResizeMode(stretch_column, QHeaderView.Stretch)
    widget.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
    widget.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
    widget.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    return widget


def align_headers(widget: QTableWidget) -> None:
    """Line each header up with the cells beneath it.

    Money columns are right-aligned in the body; a centred header above them
    reads as a different column.
    """
    if widget.rowCount() == 0:
        return
    for column in range(widget.columnCount()):
        cell = widget.item(0, column)
        header = widget.horizontalHeaderItem(column)
        if cell is not None and header is not None:
            header.setTextAlignment(Qt.AlignmentFlag(int(cell.textAlignment())))


class Badge(QLabel):
    """Small coloured pill for statuses."""

    TONES = {"": "Badge", "success": "BadgeSuccess",
             "danger": "BadgeDanger", "warning": "BadgeWarning"}

    def __init__(self, text: str = "", tone: str = "", parent=None):
        super().__init__(text, parent)
        self.setObjectName(self.TONES.get(tone, "Badge"))
        self.setAlignment(Qt.AlignCenter)

    def set_tone(self, tone: str) -> None:
        self.setObjectName(self.TONES.get(tone, "Badge"))
        self.style().unpolish(self)
        self.style().polish(self)
