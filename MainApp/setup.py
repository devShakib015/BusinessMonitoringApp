import sys
import os
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
icon = os.path.join(BASE_DIR, "bma.ico")
db_path = os.path.join(BASE_DIR, "main.db")

build_exe_options = {"packages": [
    "os", "tkinter"], "include_files": [icon, db_path]}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(name="Business monitoring App",
      version="1.0",
      description="Manages your business.",
      options={"build_exe": build_exe_options},
      executables=[Executable("main.py", icon=icon, base=base)])