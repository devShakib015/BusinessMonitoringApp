"""Spreadsheet export.

Every list in the app can leave as an ``.xlsx`` file, because the first thing
a shop owner does with their numbers is open them somewhere else.
"""

import os

import xlsxwriter
from PySide6.QtWidgets import QFileDialog

from app import config
from app.core import clock


def write(rows: list[list], path: str, sheet_name: str = "Sheet1") -> str:
    """Write ``rows`` (first row is the header) to an Excel file."""
    with xlsxwriter.Workbook(path) as book:
        sheet = book.add_worksheet(sheet_name[:31])
        header_format = book.add_format({
            "bold": True, "bg_color": "#F1F3F6", "border": 1,
            "border_color": "#D8DDE5", "align": "left"})
        money_format = book.add_format({"num_format": "#,##0.00"})

        widths: dict[int, int] = {}
        for row_index, row in enumerate(rows):
            for column, value in enumerate(row):
                if row_index == 0:
                    sheet.write(row_index, column, str(value), header_format)
                elif isinstance(value, (int, float)):
                    sheet.write_number(row_index, column, value, money_format)
                else:
                    sheet.write(row_index, column, str(value))
                widths[column] = max(widths.get(column, 10), min(42, len(str(value)) + 3))

        for column, width in widths.items():
            sheet.set_column(column, column, width)
        sheet.freeze_panes(1, 0)
        if len(rows) > 1:
            sheet.autofilter(0, 0, len(rows) - 1, len(rows[0]) - 1)
    return path


def save_as(parent, rows: list[list], basename: str,
            sheet_name: str = "Export") -> str | None:
    """Ask where to save, then write the file.  Returns the path or ``None``."""
    suggested = os.path.join(config.documents_dir(),
                             f"{basename}-{clock.today()}.xlsx")
    path, _ = QFileDialog.getSaveFileName(parent, "Export to Excel", suggested,
                                          "Excel files (*.xlsx)")
    if not path:
        return None
    return write(rows, path, sheet_name)
