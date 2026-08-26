"""Staff accounts."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QLineEdit, QTableWidgetItem

from app.core import clock
from app.core.security import password_problem
from app.repo import activity, users as user_repo
from app.ui import theme
from app.ui.dialogs.base import Dialog
from app.ui.pages.base import Page
from app.ui.widgets.common import (Card, PageHeader, align_headers, button, label,
                                   table)


class UsersPage(Page):
    def build(self) -> None:
        header = PageHeader("Staff", "Who can use the till, and what they may do.")
        header.add_action(button("Add staff member", "primary", "plus", self._add,
                                 "Ctrl+N"))
        self.layout.addWidget(header)

        card = Card(padding=0, spacing=0)
        self.table = table(["Name", "Username", "Role", "Status", "Added",
                            "Last signed in"], 0, 42)
        self.table.itemDoubleClicked.connect(lambda _: self._edit())
        card.body.addWidget(self.table)
        self.layout.addWidget(card)

        self.layout.addWidget(label("Recent activity", "SectionTitle"))
        log_card = Card(padding=0, spacing=0)
        self.log = table(["When", "Who", "Action", "Detail"], 3, 34)
        log_card.body.addWidget(self.log)
        self.layout.addWidget(log_card, 1)

        self.layout.addWidget(label(
            "Cashiers can sell, take payments and look after customers. Admins "
            "can also change products, stock, reports and settings.", "Faint"))

    def refresh(self) -> None:
        rows = user_repo.list_all()
        self.table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            cells = [
                (row["full_name"] or row["username"], None),
                (row["username"], None),
                ("Admin" if row["role"] == "admin" else "Cashier", None),
                ("Active" if row["is_active"] else "Disabled", Qt.AlignCenter),
                (clock.pretty(row["created_at"], False), None),
                (clock.pretty(row["last_login_at"]) or "never", None),
            ]
            for column, (text, alignment) in enumerate(cells):
                cell = QTableWidgetItem(text)
                if alignment:
                    cell.setTextAlignment(alignment)
                if column == 0:
                    cell.setData(Qt.UserRole, row["id"])
                    font = cell.font()
                    font.setBold(True)
                    cell.setFont(font)
                if column in (1, 4, 5):
                    cell.setForeground(theme.color("text_muted"))
                if column == 3:
                    cell.setForeground(theme.color(
                        "success" if row["is_active"] else "text_faint"))
                self.table.setItem(index, column, cell)

        entries = activity.recent(150)
        self.log.setRowCount(len(entries))
        for index, entry in enumerate(entries):
            cells = [clock.pretty(entry["created_at"]), entry["who"],
                     entry["action"], entry["detail"]]
            for column, text in enumerate(cells):
                cell = QTableWidgetItem(text)
                if column != 3:
                    cell.setForeground(theme.color("text_muted"))
                self.log.setItem(index, column, cell)
        align_headers(self.table)
        align_headers(self.log)

    def _selected_id(self) -> int | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        item = self.table.item(rows[0].row(), 0)
        return item.data(Qt.UserRole) if item else None

    def _add(self) -> None:
        if UserEditor(self).exec():
            self.refresh()
            self.notify("Staff member added.", "success")

    def _edit(self) -> None:
        user_id = self._selected_id()
        if user_id is None:
            return
        if UserEditor(self, user_repo.get(user_id), self.session).exec():
            self.refresh()
            self.notify("Staff member updated.", "success")


class UserEditor(Dialog):
    def __init__(self, parent, user=None, session=None):
        editing = user is not None
        super().__init__(parent, "Edit staff member" if editing else "New staff member",
                         "" if editing else "They sign in with this username and "
                                            "password.", 460)
        self.user = user
        self.user_id = user["id"] if editing else None
        self.session = session

        self._name = QLineEdit(user["full_name"] if editing else "")
        self._name.setPlaceholderText("Their name, as it appears on receipts")
        self._username = QLineEdit(user["username"] if editing else "")
        self._username.setEnabled(not editing)
        self._role = QComboBox()
        self._role.addItem("Cashier", "cashier")
        self._role.addItem("Admin", "admin")
        position = self._role.findData(user["role"] if editing else "cashier")
        self._role.setCurrentIndex(max(0, position))
        self._active = QCheckBox("Can sign in")
        self._active.setChecked(bool(user["is_active"]) if editing else True)

        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.Password)
        self._password.setPlaceholderText(
            "Leave blank to keep the current one" if editing else "At least 6 characters")
        self._confirm = QLineEdit()
        self._confirm.setEchoMode(QLineEdit.Password)

        self.body.addWidget(self.field("Name", self._name))
        self.body.addWidget(self.row(self.field("Username", self._username),
                                     self.field("Role", self._role)))
        self.body.addWidget(self.row(
            self.field("Password" if not editing else "New password", self._password),
            self.field("Confirm", self._confirm)))
        self.body.addWidget(self._active)

        if editing and session and user["id"] != session.user_id:
            self.add_button("Delete", "danger", self._delete)
        self.add_cancel()
        self.add_button("Save", "primary", self._save, default=True)
        self._name.setFocus()

    def _save(self) -> None:
        name = self._name.text().strip()
        username = self._username.text().strip()
        if not username:
            self.show_error("Choose a username.")
            return
        if user_repo.username_taken(username, self.user_id):
            self.show_error(f"“{username}” is already taken.")
            return

        password = self._password.text()
        if password or not self.user_id:
            problem = password_problem(password, self._confirm.text())
            if problem:
                self.show_error(problem)
                return

        role = self._role.currentData()
        active = self._active.isChecked()
        if (self.user_id and self.user["role"] == "admin"
                and (role != "admin" or not active)
                and user_repo.admin_count(self.user_id) == 0):
            self.show_error(
                "This is the only admin account. Make someone else an admin first.")
            return

        if self.user_id:
            user_repo.update(self.user_id, full_name=name, role=role, is_active=active)
            if password:
                user_repo.set_password(self.user_id, password)
        else:
            user_repo.create(username, password, full_name=name, role=role,
                             is_active=active)
        self.accept()

    def _delete(self) -> None:
        if self.user["role"] == "admin" and user_repo.admin_count(self.user_id) == 0:
            self.show_error("You cannot delete the only admin account.")
            return
        parent = self.parent()
        if hasattr(parent, "window") and not parent.window.confirm(
                f"Delete {self.user['username']}?",
                "Their past sales stay in the records.", "Delete", True):
            return
        user_repo.delete(self.user_id)
        self.accept()
