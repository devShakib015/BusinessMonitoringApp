#!/usr/bin/env python3
"""Launch ShopDesk.

``python run.py --selftest`` runs a headless check of the whole stack; the
release build uses it to verify the packaged executable.
"""

import sys

from app.main import run, selftest

if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else run())
