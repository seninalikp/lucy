#!/usr/bin/env python3
"""
run_lucy_desktop.py
Start Lucy's Python desktop UI.
"""

import sys
import traceback
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> None:
    try:
        from backend.lucy_core.desktop_ui import run_desktop_ui
        from backend.lucy_core.lucy_runtime import LucyRuntime

        runtime = LucyRuntime(project_root=PROJECT_ROOT)
        run_desktop_ui(runtime)
    except Exception as exc:
        print(f"\n[Lucy Desktop Error] {exc}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
