"""Verity API Proxy — Entry point with dependency checking.

Usage:
    python main.py              # Normal start
    python main.py --minimized  # Start minimized to tray
"""

import subprocess
import sys
import os


def _check_dependencies():
    """Verify all required packages are installed; auto-install missing ones."""
    PKG_INFO: dict[str, tuple[str, str]] = {
        "flask":     ("flask",     "pip install flask"),
        "waitress":  ("waitress",  "pip install waitress"),
        "requests":  ("requests",  "pip install requests"),
        "PyQt6":     ("PyQt6",     "pip install PyQt6"),
    }

    req_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    if not os.path.isfile(req_path):
        print("[Verity] requirements.txt not found, skipping dependency check.")
        return

    with open(req_path, encoding="utf-8") as f:
        required: list[str] = []
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                # Strip version specifiers
                pkg = line.split(">=")[0].split("==")[0].split("<")[0].split(",")[0].strip()
                required.append(pkg)

    missing: list[str] = []
    for pkg in required:
        import_name = PKG_INFO.get(pkg, (pkg, ""))[0]
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pkg)

    if not missing:
        return

    print(f"[Verity] 缺失依赖: {', '.join(missing)}")
    print("[Verity] 正在自动安装...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", req_path],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        print("[Verity] 安装完成，请重新运行。")
        sys.exit(0)
    except subprocess.CalledProcessError:
        print("\n[Verity] 自动安装失败。请手动执行：", file=sys.stderr)
        for pkg in missing:
            hint = PKG_INFO.get(pkg, (pkg, f"pip install {pkg}"))[1]
            print(f"  {hint}", file=sys.stderr)
        sys.exit(1)


_check_dependencies()

# Ensure the project root is on path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import main

if __name__ == "__main__":
    main()
