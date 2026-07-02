#!/usr/bin/env python3
"""
run_lucy.py
Simple interactive launcher for LUCY.

This is a thin ENTRY POINT only. It does not add, change, or alter any Lucy
behaviour. It instantiates the existing LucyRuntime and CommandRouter exactly
the way backend/server.py does, forwards whatever you type to the router, and
prints Lucy's reply. No new logic, no network, no model calls.

Run from the project root:

    python run_lucy.py

Commands once running:
    help            show Lucy's built-in command list
    exit / quit     shut Lucy down cleanly
    Ctrl-C / Ctrl-D also exit cleanly
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make `from backend.lucy_core...` importable when run from the project root,
# mirroring the sys.path setup in backend/server.py.
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


def main() -> int:
    runtime = LucyRuntime(project_root=PROJECT_ROOT)
    router = CommandRouter(runtime)

    print("LUCY interactive launcher")
    print("Type 'help' for commands, 'exit' to quit.")
    print("-" * 40)

    while True:
        try:
            raw = input("you> ")
        except (EOFError, KeyboardInterrupt):
            print()
            try:
                result = runtime.graceful_shutdown("User exited Lucy via signal.")
                print("lucy> " + result.get("shutdown_message", "Lucy shutting down cleanly."))
            except Exception:
                print("lucy> Lucy shutting down.")
            return 0

        response = router.handle(raw)
        print("lucy> " + response.message)
        if getattr(response, "should_exit", False):
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
