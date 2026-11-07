#!/usr/bin/env python3
"""
run_lucy.py
Pure Terminal Sovereign Launcher for LUCY (Stage 66).
No Web UI, no Desktop UI — 100% terminal-first adaptive assistant with auto-Ollama bootstrap.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


def main() -> int:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    runtime = LucyRuntime(project_root=PROJECT_ROOT)
    router = CommandRouter(runtime)

    # Ensure local Ollama engine is online
    ollama_msg = "Offline (failover pool active)"
    if hasattr(runtime, "ollama_connector"):
        try:
            if runtime.ollama_connector.ensure_online(max_wait_seconds=2.0):
                models = runtime.ollama_connector.list_local_models()
                m_tag = "lucy:personal" if "lucy:personal" in models else (models[0] if models else "lucy:personal")
                ollama_msg = f"Connected ({m_tag} active @ 127.0.0.1:11434)"
        except Exception:
            pass

    print("=" * 68)
    print("  LUCY — SOVEREIGN TERMINAL OPERATING ASSISTANT (STAGE 66)")
    print("  Mode: Pure Terminal | Anti-Hallucination: 2-Layer Enforced")
    print(f"  Neural Engine: Local Ollama [{ollama_msg}]")
    print("=" * 68)

    # Display Proactive Executive Brief on terminal boot
    if hasattr(runtime, "proactive_briefer"):
        try:
            brief = runtime.proactive_briefer.generate_brief()
            if brief.get("brief_text"):
                print(brief["brief_text"])
                print("-" * 68)
        except Exception:
            pass

    print("Type naturally, use '/palette' or 'help' for commands, 'exit' to quit.")
    print("-" * 68)

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

        if hasattr(runtime, "terminal_repl") and raw.strip():

            runtime.terminal_repl.history.add(raw.strip())

        response = router.handle(raw)
        print("lucy> " + response.message)
        if getattr(response, "should_exit", False):
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
