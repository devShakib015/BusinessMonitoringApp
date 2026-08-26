"""A dialog shell with a title, a body and a right-aligned button row."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QFrame, QLabel, QWidget

from app.ui import theme
from app.ui.widgets.common import button, hbox, label, vbox


class Dialog(QDialog):
    def __init__(self, parent, title: str, subtitle: str = "", width: int = 460):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(width)
        self.setStyleSheet(f"QDialog {{ background: {theme.hex_of('bg')}; }}")

        outer = vbox(self, (22, 20, 22, 18), 14)

        heading = vbox(spacing=3)
        heading.addWidget(label(title, "PageTitle"))
        if subtitle:
            note = label(subtitle, "PageSubtitle")
            note.setWordWrap(True)
            heading.addWidget(note)
        outer.addLayout(heading)

        self.body = vbox(spacing=12)
        outer.addLayout(self.body, 1)

        self.footer = hbox(spacing=8)
        self.footer.addStretch(1)
        outer.addLayout(self.footer)

        self._error = QLabel()
        self._error.setWordWrap(True)
        self._error.setStyleSheet(
            f"color: {theme.hex_of('danger')}; background: {theme.hex_of('danger_soft')};"
            f"border-radius: 8px; padding: 9px 11px; font-weight: 600;")
        self._error.hide()
        outer.insertWidget(outer.count() - 1, self._error)

    def add_button(self, text: str, variant: str = "", on_click=None,
                   default: bool = False):
        widget = button(text, variant, on_click=on_click)
        widget.setDefault(default)
        widget.setAutoDefault(default)
        self.footer.addWidget(widget)
        return widget

    def add_cancel(self, text: str = "Cancel"):
        return self.add_button(text, "ghost", self.reject)

    def show_error(self, message: str) -> None:
        self._error.setText(message)
        self._error.setVisible(bool(message))

    def clear_error(self) -> None:
        self._error.hide()

    def field(self, caption: str, widget: QWidget, hint: str = "") -> QWidget:
        """Label above an input, with an optional hint underneath."""
        holder = QFrame()
        column = vbox(holder, spacing=5)
        column.addWidget(label(caption, "SectionTitle"))
        column.addWidget(widget)
        if hint:
            column.addWidget(label(hint, "Faint"))
        return holder

    def row(self, *widgets, spacing: int = 10):
        holder = QFrame()
        line = hbox(holder, spacing=spacing)
        for widget in widgets:
            line.addWidget(widget, 1)
        return holder

    def keyPressEvent(self, event):  # noqa: N802 - Qt naming
        # Enter inside a plain field should not close the dialog by accident.
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not self.focusWidget():
            return
        super().keyPressEvent(event)
