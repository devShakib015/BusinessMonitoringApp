#!/usr/bin/env python3
"""Regenerate the Windows version resource from ``app/config.py``."""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app import config  # noqa: E402

TEMPLATE = '''# Windows version resource for the built executable.
# Regenerate with: python packaging/make_version.py
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({parts}, 0),
    prodvers=({parts}, 0),
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable("040904B0", [
        StringStruct("CompanyName", "{publisher}"),
        StringStruct("FileDescription", "{name} - {tagline}"),
        StringStruct("FileVersion", "{version}"),
        StringStruct("InternalName", "{name}"),
        StringStruct("LegalCopyright", "MIT Licence"),
        StringStruct("OriginalFilename", "{name}.exe"),
        StringStruct("ProductName", "{name}"),
        StringStruct("ProductVersion", "{version}"),
      ])
    ]),
    VarFileInfo([VarStruct("Translation", [1033, 1200])])
  ]
)
'''

if __name__ == "__main__":
    numbers = re.findall(r"\d+", config.APP_VERSION)[:3]
    while len(numbers) < 3:
        numbers.append("0")
    target = os.path.join(ROOT, "packaging", "version_info.txt")
    with open(target, "w") as handle:
        handle.write(TEMPLATE.format(
            parts=", ".join(numbers), version=config.APP_VERSION,
            name=config.APP_NAME, tagline=config.APP_TAGLINE.lower(),
            publisher=config.PUBLISHER))
    print(f"wrote {target}")
