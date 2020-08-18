
import sys
import os
from cx_Freeze import *

# Dependencies are automatically detected, but it might need fine tuning.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
icon = os.path.join(BASE_DIR, "bma_icon.ico")
db_path = os.path.join(BASE_DIR, "main.db")
image_path = os.path.join(BASE_DIR, "Logo.jpg")


# GUI applications require a different base on Windows (the default is for a
# console application).

base = None
if sys.platform == "win32":
    base = "Win32GUI"


shortcut_table = [
    ("DesktopShortcut",        # Shortcut
     "DesktopFolder",          # Directory_
     "Business Monitoring App",           # Name
     "TARGETDIR",              # Component_
     "[TARGETDIR]BMA.exe",  # Target
     None,                     # Arguments
     None,                     # Description
     None,                     # Hotkey
     "",                     # Icon
     0,                     # IconIndex
     None,                     # ShowCmd
     'TARGETDIR'               # WkDir
     )
]

# Now create the table dictionary
msi_data = {"Shortcut": shortcut_table}


build_exe_options = {"packages": [
    "os", "tkinter", "pytz", "reportlab", "xlsxwriter", "num2words"], "include_files": [icon, db_path, image_path]}

bdist_msi_options = {'data': msi_data,
                     'initial_target_dir': 'C:\\BMA', 'install_icon': icon}


setup(name="Business Monitoring App",
      version="1.1.1",
      author="LazyProgs [Shakib]",
      author_email="kmshahriahhossain@gmail.com",
      description="Copyright © 2020 LazyProgs",
      options={"build_exe": build_exe_options, "bdist_msi": bdist_msi_options},
      executables=[Executable("BMA.py", icon=icon, base=base)])
