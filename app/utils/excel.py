import xlsxwriter
from tkinter import filedialog


def export_to_excel(data):
    """Open a save-as dialog and write *data* (list of tuples) to an Excel file."""
    file_path = filedialog.asksaveasfilename(
        initialdir="/",
        defaultextension=".xlsx",
        title="Save Excel File",
        filetypes=(("Excel Files", "*.xlsx"), ("All Files", "*.*")),
    )
    if not file_path:
        return
    with xlsxwriter.Workbook(file_path) as workbook:
        worksheet = workbook.add_worksheet()
        for row_num, row_data in enumerate(data):
            worksheet.write_row(row_num, 0, row_data)
