"""Colours, fonts and the stylesheet.

Everything visual is derived from one palette so the whole app can switch
between light and dark, and between accent colours, without any screen
knowing about it.
"""

from PySide6.QtGui import QColor, QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from app.core import settings

ACCENTS = {
    "indigo": "#4F46E5",
    "emerald": "#059669",
    "blue": "#2563EB",
    "amber": "#D97706",
    "rose": "#E11D48",
    "slate": "#334155",
}

LIGHT = {
    "bg": "#F4F6F8",
    "surface": "#FFFFFF",
    "surface_alt": "#F7F8FA",
    "surface_sunken": "#EDEFF3",
    "border": "#E2E6EC",
    "border_strong": "#CBD2DC",
    "text": "#101828",
    "text_muted": "#5C6675",
    "text_faint": "#98A2B3",
    "sidebar": "#131822",
    "sidebar_text": "#98A2B3",
    "sidebar_hover": "#1D2431",
    "sidebar_active_text": "#FFFFFF",
    "success": "#0E9F6E",
    "success_soft": "#E7F7F1",
    "danger": "#DC2626",
    "danger_soft": "#FDECEC",
    "warning": "#D97706",
    "warning_soft": "#FEF4E6",
    "info_soft": "#EDF1FE",
    "shadow": "rgba(16, 24, 40, 0.06)",
}

DARK = {
    "bg": "#0E1116",
    "surface": "#161A21",
    "surface_alt": "#1B2029",
    "surface_sunken": "#11151B",
    "border": "#262C36",
    "border_strong": "#333B48",
    "text": "#E8EBF0",
    "text_muted": "#98A2B3",
    "text_faint": "#6B7686",
    "sidebar": "#0A0D12",
    "sidebar_text": "#8A94A6",
    "sidebar_hover": "#161B24",
    "sidebar_active_text": "#FFFFFF",
    "success": "#10B981",
    "success_soft": "#10291F",
    "danger": "#F05252",
    "danger_soft": "#2C1618",
    "danger_soft_border": "#4A2226",
    "warning": "#F5A623",
    "warning_soft": "#2A2013",
    "info_soft": "#171C2E",
    "shadow": "rgba(0, 0, 0, 0.35)",
}

_palette: dict[str, str] = dict(LIGHT)


def is_dark() -> bool:
    return settings.get("app.theme") == "dark"


def palette() -> dict[str, str]:
    return _palette


def color(token: str) -> QColor:
    return QColor(_palette.get(token, "#000000"))


def hex_of(token: str) -> str:
    return _palette.get(token, "#000000")


def ui_font(size: int = 10, weight: QFont.Weight = QFont.Normal) -> QFont:
    font = QFont(_family(), size)
    font.setWeight(weight)
    return font


def number_font(size: int = 12, weight: QFont.Weight = QFont.DemiBold) -> QFont:
    """Tabular figures, so columns of money line up."""
    font = QFont(_family(), size)
    font.setWeight(weight)
    font.setStyleHint(QFont.SansSerif)
    font.setFeature("tnum", 1) if hasattr(font, "setFeature") else None
    return font


def _family() -> str:
    for candidate in ("Segoe UI Variable Text", "Segoe UI", "SF Pro Text",
                      "Inter", "Helvetica Neue", "Ubuntu", "Cantarell"):
        if candidate in QFontDatabase.families():
            return candidate
    return QApplication.font().family()


def apply(app: QApplication) -> None:
    """Recompute the palette from settings and restyle the whole application."""
    global _palette
    _palette = dict(DARK if is_dark() else LIGHT)
    accent = ACCENTS.get(settings.get("app.accent"), ACCENTS["indigo"])
    _palette["accent"] = accent
    _palette["accent_hover"] = _shade(accent, -14)
    _palette["accent_pressed"] = _shade(accent, -26)
    _palette["accent_soft"] = _mix(accent, _palette["surface"], 0.12)
    _palette["accent_soft_border"] = _mix(accent, _palette["surface"], 0.35)
    _palette["selection"] = _mix(accent, _palette["surface"], 0.18)

    app.setFont(ui_font(10))
    app.setStyleSheet(stylesheet())


def _shade(hex_color: str, percent: int) -> str:
    color_ = QColor(hex_color)
    return (color_.lighter(100 + percent) if percent > 0
            else color_.darker(100 - percent)).name()


def _mix(front: str, back: str, ratio: float) -> str:
    a, b = QColor(front), QColor(back)
    return QColor(
        int(a.red() * ratio + b.red() * (1 - ratio)),
        int(a.green() * ratio + b.green() * (1 - ratio)),
        int(a.blue() * ratio + b.blue() * (1 - ratio)),
    ).name()


def stylesheet() -> str:
    p = _palette
    return f"""
* {{
    outline: none;
}}
QWidget {{
    color: {p['text']};
    font-size: 13px;
}}
QMainWindow, QDialog, #Root {{
    background: {p['bg']};
}}

/* ── Sidebar ─────────────────────────────────────────────────────────── */
#Sidebar {{
    background: {p['sidebar']};
    border: none;
}}
#SidebarBrand {{
    color: #FFFFFF;
    font-size: 16px;
    font-weight: 700;
    padding: 18px 18px 4px 18px;
}}
#SidebarTagline {{
    color: {p['sidebar_text']};
    font-size: 11px;
    padding: 0 18px 14px 18px;
}}
#SidebarSection {{
    color: #5C6675;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 14px 20px 6px 20px;
}}
QPushButton#NavItem {{
    background: transparent;
    color: {p['sidebar_text']};
    border: none;
    border-radius: 8px;
    padding: 9px 12px;
    margin: 1px 10px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton#NavItem:hover {{
    background: {p['sidebar_hover']};
    color: #E6E9EF;
}}
QPushButton#NavItem:checked {{
    background: {p['accent']};
    color: {p['sidebar_active_text']};
    font-weight: 600;
}}
#SidebarFooter {{
    color: #5C6675;
    font-size: 11px;
    padding: 10px 18px;
}}
#UserChip {{
    background: {p['sidebar_hover']};
    border-radius: 8px;
    margin: 8px 10px;
    padding: 8px 10px;
}}
#UserChipName {{ color: #E6E9EF; font-size: 12px; font-weight: 600; }}
#UserChipRole {{ color: {p['sidebar_text']}; font-size: 11px; }}

/* ── Headings and cards ──────────────────────────────────────────────── */
#PageTitle {{ font-size: 21px; font-weight: 700; color: {p['text']}; }}
#PageSubtitle {{ font-size: 12px; color: {p['text_muted']}; }}
#SectionTitle {{ font-size: 13px; font-weight: 700; color: {p['text']}; }}
#Muted {{ color: {p['text_muted']}; }}
#Faint {{ color: {p['text_faint']}; font-size: 12px; }}

#Card, QFrame#Card {{
    background: {p['surface']};
    border: 1px solid {p['border']};
    border-radius: 12px;
}}
#CardFlat {{
    background: {p['surface_alt']};
    border: 1px solid {p['border']};
    border-radius: 10px;
}}
#StatValue {{ font-size: 22px; font-weight: 700; color: {p['text']}; }}
#StatLabel {{ font-size: 11px; font-weight: 600; color: {p['text_muted']};
              letter-spacing: 0.4px; }}
#StatHint {{ font-size: 11px; color: {p['text_faint']}; }}

/* ── Inputs ──────────────────────────────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox {{
    background: {p['surface']};
    border: 1px solid {p['border_strong']};
    border-radius: 8px;
    padding: 7px 10px;
    selection-background-color: {p['accent']};
    selection-color: #FFFFFF;
    min-height: 18px;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus,
QDoubleSpinBox:focus, QDateEdit:focus, QComboBox:focus {{
    border: 1px solid {p['accent']};
    background: {p['surface']};
}}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled {{
    background: {p['surface_sunken']};
    color: {p['text_faint']};
}}
QLineEdit[state="error"] {{ border: 1px solid {p['danger']}; }}
QLineEdit#SearchField {{
    font-size: 15px;
    padding: 11px 14px;
    border-radius: 10px;
}}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {p['text_muted']};
    margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background: {p['surface']};
    border: 1px solid {p['border_strong']};
    border-radius: 8px;
    padding: 4px;
    selection-background-color: {p['selection']};
    selection-color: {p['text']};
}}
QCheckBox, QRadioButton {{ spacing: 8px; }}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 17px; height: 17px;
    border: 1px solid {p['border_strong']};
    background: {p['surface']};
}}
QCheckBox::indicator {{ border-radius: 5px; }}
QRadioButton::indicator {{ border-radius: 9px; }}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background: {p['accent']};
    border-color: {p['accent']};
    image: none;
}}

/* ── Buttons ─────────────────────────────────────────────────────────── */
QPushButton {{
    background: {p['surface']};
    color: {p['text']};
    border: 1px solid {p['border_strong']};
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 600;
    min-height: 18px;
}}
QPushButton:hover {{ background: {p['surface_alt']}; border-color: {p['text_faint']}; }}
QPushButton:pressed {{ background: {p['surface_sunken']}; }}
QPushButton:disabled {{ color: {p['text_faint']}; background: {p['surface_sunken']};
                        border-color: {p['border']}; }}
QPushButton[variant="primary"] {{
    background: {p['accent']}; color: #FFFFFF; border: 1px solid {p['accent']};
}}
QPushButton[variant="primary"]:hover {{ background: {p['accent_hover']};
                                        border-color: {p['accent_hover']}; }}
QPushButton[variant="primary"]:pressed {{ background: {p['accent_pressed']}; }}
QPushButton[variant="primary"]:disabled {{ background: {p['border_strong']};
                                           border-color: {p['border_strong']};
                                           color: {p['surface']}; }}
QPushButton[variant="danger"] {{
    background: {p['danger']}; color: #FFFFFF; border-color: {p['danger']};
}}
QPushButton[variant="danger"]:hover {{ background: {_shade(p['danger'], -12)}; }}
QPushButton[variant="ghost"] {{
    background: transparent; border-color: transparent; color: {p['text_muted']};
}}
QPushButton[variant="ghost"]:hover {{ background: {p['surface_alt']};
                                      color: {p['text']}; }}
QPushButton[variant="soft"] {{
    background: {p['accent_soft']}; color: {p['accent']};
    border-color: {p['accent_soft_border']};
}}
QPushButton#ChargeButton {{
    background: {p['success']}; color: #FFFFFF; border: none;
    border-radius: 10px; padding: 16px; font-size: 16px; font-weight: 700;
}}
QPushButton#ChargeButton:hover {{ background: {_shade(p['success'], -10)}; }}
QPushButton#ChargeButton:disabled {{ background: {p['border_strong']};
                                     color: {p['surface']}; }}
QPushButton#PayMethod {{
    padding: 9px 6px; font-size: 12px; font-weight: 600;
    background: {p['surface_alt']}; color: {p['text_muted']};
}}
QPushButton#PayMethod:checked {{
    background: {p['accent_soft']}; color: {p['accent']};
    border: 1px solid {p['accent']};
}}
QPushButton#QuickCash {{
    padding: 7px 4px; font-size: 12px; font-weight: 600;
    color: {p['text_muted']};
}}
QToolButton {{
    background: transparent; border: none; border-radius: 7px; padding: 5px;
}}
QToolButton:hover {{ background: {p['surface_alt']}; }}

/* ── Tables ──────────────────────────────────────────────────────────── */
QTableView, QTreeView {{
    background: {p['surface']};
    alternate-background-color: {p['surface_alt']};
    border: 1px solid {p['border']};
    border-radius: 10px;
    gridline-color: transparent;
    selection-background-color: {p['selection']};
    selection-color: {p['text']};
}}
QTableView::item, QTreeView::item {{
    padding: 7px 6px;
    border-bottom: 1px solid {p['border']};
}}
QTableView::item:selected, QTreeView::item:selected {{
    background: {p['selection']}; color: {p['text']};
}}
QHeaderView::section {{
    background: {p['surface_alt']};
    color: {p['text_muted']};
    border: none;
    border-bottom: 1px solid {p['border']};
    padding: 9px 6px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.3px;
}}
QHeaderView::section:first {{ border-top-left-radius: 10px; }}
QHeaderView::section:last {{ border-top-right-radius: 10px; }}
QTableCornerButton::section {{ background: {p['surface_alt']}; border: none; }}

/* ── Scrollbars ──────────────────────────────────────────────────────── */
QScrollBar:vertical {{ background: transparent; width: 11px; margin: 2px; }}
QScrollBar::handle:vertical {{
    background: {p['border_strong']}; border-radius: 5px; min-height: 28px;
}}
QScrollBar::handle:vertical:hover {{ background: {p['text_faint']}; }}
QScrollBar:horizontal {{ background: transparent; height: 11px; margin: 2px; }}
QScrollBar::handle:horizontal {{
    background: {p['border_strong']}; border-radius: 5px; min-width: 28px;
}}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* ── Tabs, menus, tooltips ───────────────────────────────────────────── */
QTabWidget::pane {{ border: none; background: transparent; top: 0; }}
QTabBar::tab {{
    background: transparent; color: {p['text_muted']};
    padding: 8px 16px; margin-right: 2px;
    border-bottom: 2px solid transparent; font-weight: 600;
}}
QTabBar::tab:selected {{ color: {p['accent']}; border-bottom: 2px solid {p['accent']}; }}
QMenu {{
    background: {p['surface']}; border: 1px solid {p['border_strong']};
    border-radius: 8px; padding: 5px;
}}
QMenu::item {{ padding: 7px 22px 7px 12px; border-radius: 6px; }}
QMenu::item:selected {{ background: {p['selection']}; }}
QMenu::separator {{ height: 1px; background: {p['border']}; margin: 4px 8px; }}
QToolTip {{
    background: {p['text']}; color: {p['surface']};
    border: none; border-radius: 6px; padding: 6px 9px;
}}

/* ── Misc ────────────────────────────────────────────────────────────── */
QProgressBar {{
    background: {p['surface_sunken']}; border: none; border-radius: 5px;
    height: 8px; text-align: center;
}}
QProgressBar::chunk {{ background: {p['accent']}; border-radius: 5px; }}
#Divider {{ background: {p['border']}; max-height: 1px; border: none; }}
#VDivider {{ background: {p['border']}; max-width: 1px; border: none; }}
#Badge {{
    background: {p['surface_sunken']}; color: {p['text_muted']};
    border-radius: 9px; padding: 2px 9px; font-size: 11px; font-weight: 700;
}}
#BadgeSuccess {{ background: {p['success_soft']}; color: {p['success']};
                 border-radius: 9px; padding: 2px 9px; font-size: 11px;
                 font-weight: 700; }}
#BadgeDanger {{ background: {p['danger_soft']}; color: {p['danger']};
                border-radius: 9px; padding: 2px 9px; font-size: 11px;
                font-weight: 700; }}
#BadgeWarning {{ background: {p['warning_soft']}; color: {p['warning']};
                 border-radius: 9px; padding: 2px 9px; font-size: 11px;
                 font-weight: 700; }}
#TotalRowLabel {{ color: {p['text_muted']}; font-size: 13px; }}
#TotalRowValue {{ color: {p['text']}; font-size: 13px; font-weight: 600; }}
#GrandTotalLabel {{ color: {p['text']}; font-size: 15px; font-weight: 700; }}
#GrandTotalValue {{ color: {p['text']}; font-size: 27px; font-weight: 800; }}
#ChangeValue {{ color: {p['success']}; font-size: 19px; font-weight: 700; }}
#EmptyTitle {{ color: {p['text_muted']}; font-size: 14px; font-weight: 600; }}
#EmptyHint {{ color: {p['text_faint']}; font-size: 12px; }}
"""
