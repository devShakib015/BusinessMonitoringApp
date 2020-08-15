
import sys
import os
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
icon = os.path.join(BASE_DIR, "b.ico")
db_path = os.path.join(BASE_DIR, "main.db")

build_exe_options = {"packages": [
    "os", "tkinter", "pytz", "reportlab", "xlsxwriter"], "include_files": [icon, db_path]}

# GUI applications require a different base on Windows (the default is for a
# console application).

base = "Win32GUI"

setup(name="Business monitoring App By Shakib",
      version="4.0",
      description="This app will monitor your business and generate invoices and excel sheets. This is very useful for small business with limited products.",
      options={"build_exe": build_exe_options},
      executables=[Executable("BMA.py", icon=icon, base=base)])
