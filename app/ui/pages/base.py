"""Common behaviour for the screens in the main window."""

from PySide6.QtWidgets import QWidget

from app.core.security import Session
from app.ui.widgets.common import vbox


class Page(QWidget):
    """A screen in the sidebar.

    ``refresh`` runs every time the page becomes visible, so a sale made on
    the sell screen shows up on the reports screen without anything having to
    wire the two together.
    """

    title = ""
    subtitle = ""

    def __init__(self, session: Session, window, parent=None):
        super().__init__(parent)
        self.session = session
        self.window = window
        self.layout = vbox(self, (24, 22, 24, 22), 16)
        self.build()

    def build(self) -> None:  # pragma: no cover - overridden by every page
        raise NotImplementedError

    def refresh(self) -> None:
        """Reload data from the database."""

    def on_shown(self) -> None:
        self.refresh()

    def notify(self, message: str, tone: str = "info") -> None:
        self.window.notify(message, tone)
