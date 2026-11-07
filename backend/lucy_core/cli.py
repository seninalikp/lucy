"""
cli.py
Terminal interface for Lucy Core Runtime.
Stage 50 = High-Performance Terminal REPL & Custom Command Palette.
"""

from __future__ import annotations

import sys

from backend.lucy_core.router import CommandRouter
from backend.lucy_core.terminal_repl import TerminalREPL


def run_chat(router: CommandRouter) -> None:
    repl = getattr(router.runtime, "terminal_repl", None)
    if repl is None:
        repl = TerminalREPL(runtime=router.runtime, router=router)
    else:
        repl.router = router
    repl.run_interactive()


def run_cli(runtime) -> None:
    """Parse sys.argv and dispatch to chat or one-shot command mode."""
    router = CommandRouter(runtime)
    args = sys.argv[1:]

    try:
        if not args:
            run_chat(router)
            return

        if args[0].lower() == "chat":
            run_chat(router)
            return

        repl = getattr(runtime, "terminal_repl", None)
        if repl is not None:
            repl.router = router
            res = repl.execute_one(" ".join(args))
            if res.get("output"):
                print(res["output"])
        else:
            response = router.handle(" ".join(args))
            if response.message:
                print(response.message)
    finally:
        try:
            if not runtime.session_state.status().get("graceful_shutdown"):
                runtime.graceful_shutdown("CLI session ended cleanly.")
        except Exception:
            pass
