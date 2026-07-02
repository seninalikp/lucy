#!/usr/bin/env python3
"""
run_lucy_core.py
Entry point for Lucy Core Runtime.

Usage:
    python run_lucy_core.py status
    python run_lucy_core.py spine
    python run_lucy_core.py agents
    python run_lucy_core.py agent ELIE
    python run_lucy_core.py check "delete my files"
    python run_lucy_core.py check "what is your status"
    python run_lucy_core.py checkpoint "Part 1 test checkpoint"
    python run_lucy_core.py health

LUCY = Living Unified Cognitive Yield
Stage: Core Runtime Prototype / Agent-Ready Foundation / Not Beta Yet
"""

import signal
import sys
import traceback
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


_RUNTIME = None


def _handle_shutdown_signal(signum, _frame) -> None:
    if _RUNTIME is not None:
        try:
            _RUNTIME.graceful_shutdown(f"Shutdown signal received: {signum}")
        except Exception:
            pass
    raise SystemExit(0)


def main() -> None:
    global _RUNTIME
    signal.signal(signal.SIGINT, _handle_shutdown_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_shutdown_signal)
    try:
        from backend.lucy_core.lucy_runtime import LucyRuntime
        from backend.lucy_core.cli import run_cli

        runtime = LucyRuntime(project_root=PROJECT_ROOT)
        _RUNTIME = runtime
        run_cli(runtime)

    except Exception as exc:
        print(f"\n[Lucy Runtime Error] {exc}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
