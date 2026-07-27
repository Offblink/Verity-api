#!/usr/bin/env python
"""Build standalone .exe with PyInstaller.

Usage:
    python build.py          # one-file .exe
    python build.py --clean  # remove build/ and dist/ first
"""

import os
import subprocess
import sys
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))

if "--clean" in sys.argv:
    for d in ["build", "dist"]:
        p = os.path.join(ROOT, d)
        if os.path.isdir(p):
            shutil.rmtree(p)
            print(f"Removed {d}/")

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    "--windowed",
    "--name", "Verity-API-Proxy",
    "--icon", os.path.join(ROOT, "resources", "icon.ico"),
    "--add-data", f"{os.path.join(ROOT, 'resources', 'icon.ico')}{os.pathsep}resources",
    os.path.join(ROOT, "main.py"),
]

print("Running:", " ".join(cmd))
subprocess.check_call(cmd, cwd=ROOT)
print(f"\nDone! Output: {os.path.join(ROOT, 'dist', 'Verity-API-Proxy.exe')}")
