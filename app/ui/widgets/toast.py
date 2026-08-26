"""Transient confirmation messages.

A sale that saved, a backup that was written -- feedback that matters for a
second and should not need dismissing.
"""

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtWidgets import QGraphicsOpacityEffect, QHBoxLayout, QLabel, QWidget

from app.ui import icons, theme

_TONES = {
    "info": ("check", "accent"),
    "success": ("check", "success"),
    "warning": ("alert", "warning"),
    "error": ("alert", "danger"),
}


class Toast(QWidget):
    def __init__(self, parent, message: str, tone: str = "info"):
        super().__init__(parent)
        icon_name, color_token = _TONES.get(tone, _TONES["info"])
        accent = theme.hex_of(color_token)

        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setStyleSheet(
            f"background: {theme.hex_of('surface')};"
            f"border: 1px solid {theme.hex_of('border_strong')};"
            f"border-left: 3px solid {accent}; border-radius: 10px;")

        row = QHBoxLayout(self)
        row.setContentsMargins(14, 11, 16, 11)
        row.setSpacing(10)

        badge = QLabel()
        badge.setPixmap(icons.pixmap(icon_name, accent, 18))
        badge.setStyleSheet("border: none;")
        row.addWidget(badge)

        text = QLabel(message)
        text.setStyleSheet(f"border: none; color: {theme.hex_of('text')}; font-weight: 600;")
        text.setWordWrap(True)
        text.setMaximumWidth(420)
        row.addWidget(text)

        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._effect.setOpacity(0.0)
        self.adjustSize()

    def show_for(self, milliseconds: int = 2600) -> None:
        self._place()
        self.show()
        self.raise_()
        self._fade(0.0, 1.0, 160)
        QTimer.singleShot(milliseconds, self._dismiss)

    def _place(self) -> None:
        parent = self.parentWidget()
        if not parent:
            return
        self.adjustSize()
        self.move(parent.width() - self.width() - 28,
                  parent.height() - self.height() - 28)

    def _fade(self, start: float, end: float, duration: int, then=None) -> None:
        self._animation = QPropertyAnimation(self._effect, b"opacity", self)
        self._animation.setDuration(duration)
        self._animation.setStartValue(start)
        self._animation.setEndValue(end)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        if then:
            self._animation.finished.connect(then)
        self._animation.start()

    def _dismiss(self) -> None:
        self._fade(1.0, 0.0, 220, self.deleteLater)
