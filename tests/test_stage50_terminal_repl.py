"""
test_stage50_terminal_repl.py
Stage 50 = High-Performance Terminal REPL & Custom Command Palette.

Verifies:
1. REPL reports Stage 50 and active status with complete schema.
2. ANSI color formatting, stripping, and auto-detection fallback.
3. Persistent history manager with deduping, substring search, and disk persistence.
4. User macro and shortcut engine registration, deletion, and pipeline resolution.
5. Command palette and intelligent autocomplete matching.
6. Command palette structured help rendering and category filtering.
7. Execution pipeline handling palette commands, macros, timing, and exit signals.
8. Interactive REPL stream execution loop with mock I/O and clean EOF shutdown.
9. Full integration with CommandRouter and LucyRuntime.
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.terminal_repl import (
    ANSIColor,
    CommandPalette,
    MacroEngine,
    TerminalHistoryManager,
    TerminalREPL,
    STAGE,
)
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class MockRuntime:
    """Mock runtime for testing REPL dispatch and badge rendering."""
    def __init__(self) -> None:
        self.commands_received = []

    def system_telemetry(self) -> dict:
        return {
            "ram": {"available_mb": 8500, "memory_load_percent": 42},
            "disk": {"free_gb": 190.5, "percent_free": 40.0},
        }

    def sentinel_status(self) -> dict:
        return {
            "background_watcher": {"running": True},
            "files_tracked": 120,
        }

    def provider_pool_status(self) -> dict:
        return {
            "total_keys": 25,
            "active_provider": "groq",
        }

    def respond(self, message: str) -> str:
        self.commands_received.append(message)
        return f"Echo from MockRuntime: {message}"


class Stage50TerminalREPLTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.history_file = self.tmp_path / "terminal_history.json"
        self.macro_file = self.tmp_path / "user_macros.json"

    def tearDown(self) -> None:
        try:
            self.tmp.cleanup()
        except Exception:
            pass

    def test_stage_identity_and_status(self) -> None:
        """1. REPL reports Stage 50 and active status with complete schema."""
        repl = TerminalREPL(
            runtime=MockRuntime(),
            lucy_data=self.tmp_path,
            enable_color=False,
        )
        status = repl.status()
        self.assertEqual(status["stage"], "50 high-performance terminal repl")
        self.assertEqual(status["status"], "ready")
        self.assertFalse(status["color_enabled"])
        self.assertIn("history_count", status)
        self.assertIn("macros_registered", status)
        self.assertIn("palette_commands_count", status)

    def test_ansi_color_system(self) -> None:
        """2. ANSI color formatting, stripping, and auto-detection fallback."""
        colored = ANSIColor.style("Hello Lucy", ANSIColor.CYAN, ANSIColor.BOLD, enabled=True)
        self.assertTrue(colored.startswith("\033[36m\033[1m"))
        self.assertTrue(colored.endswith("\033[0m"))

        # Strip ANSI
        plain = ANSIColor.strip(colored)
        self.assertEqual(plain, "Hello Lucy")

        # Disabled color produces plain text
        disabled = ANSIColor.style("Plain Lucy", ANSIColor.GREEN, enabled=False)
        self.assertEqual(disabled, "Plain Lucy")

    def test_history_manager_persistence_and_search(self) -> None:
        """3. Persistent history manager with deduping, substring search, and disk persistence."""
        hm = TerminalHistoryManager(history_file=self.history_file, max_entries=5)

        # Add commands
        self.assertTrue(hm.add("status"))
        self.assertTrue(hm.add("telemetry"))
        self.assertFalse(hm.add("telemetry"))  # Consecutive deduplication
        self.assertFalse(hm.add("   "))        # Empty string ignored
        self.assertTrue(hm.add("scan workspace"))

        self.assertEqual(hm.count(), 3)
        self.assertEqual(hm.get_history(), ["status", "telemetry", "scan workspace"])

        # Substring search
        matches = hm.search_history("scan")
        self.assertEqual(matches, ["scan workspace"])

        # Disk reload verification
        hm2 = TerminalHistoryManager(history_file=self.history_file, max_entries=5)
        self.assertEqual(hm2.get_history(), ["status", "telemetry", "scan workspace"])

        # Clear
        hm2.clear()
        self.assertEqual(hm2.count(), 0)

    def test_macro_engine_registration_and_expansion(self) -> None:
        """4. User macro and shortcut engine registration, deletion, and pipeline resolution."""
        me = MacroEngine(macro_file=self.macro_file)
        self.assertIn("quickcheck", me.list_macros())

        # Register custom macro
        res = me.register_macro("mytest", "telemetry && sentinel status")
        self.assertTrue(res["ok"])
        self.assertEqual(res["name"], "mytest")

        # Resolve pipeline
        steps = me.resolve_macro("/mytest")
        self.assertEqual(steps, ["telemetry", "sentinel status"])

        # Delete macro
        self.assertTrue(me.delete_macro("mytest"))
        self.assertIsNone(me.resolve_macro("mytest"))

    def test_command_palette_autocomplete(self) -> None:
        """5. Command palette and intelligent autocomplete matching."""
        palette = CommandPalette()
        palette.macros.register_macro("fastscan", "scan workspace")

        # Prefix matching
        matches = palette.autocomplete("/st")
        self.assertIn("/status", matches)

        # Substring matching
        matches_tel = palette.autocomplete("tele")
        self.assertTrue(any("telemetry" in m for m in matches_tel))

        # Macro matching
        matches_macro = palette.autocomplete("fast")
        self.assertTrue(any("fastscan" in m for m in matches_macro))

        # Empty prefix returns all
        all_matches = palette.autocomplete("")
        self.assertGreater(len(all_matches), 10)

    def test_command_palette_help_rendering(self) -> None:
        """6. Command palette structured help rendering and category filtering."""
        palette = CommandPalette()
        full_help = palette.render_help()
        self.assertIn("LUCY COMMAND PALETTE", full_help)
        self.assertIn("[SYSTEM]", full_help)
        self.assertIn("[PROVIDERS]", full_help)
        self.assertIn("[SENTINEL]", full_help)

        # Category filter
        sentinel_help = palette.render_help(category="SENTINEL")
        self.assertIn("[SENTINEL]", sentinel_help)
        self.assertNotIn("[SYSTEM]", sentinel_help)

    def test_repl_execute_one_and_macros(self) -> None:
        """7. Execution pipeline handling palette commands, macros, timing, and exit signals."""
        mock_rt = MockRuntime()
        repl = TerminalREPL(
            runtime=mock_rt,
            lucy_data=self.tmp_path,
            enable_color=False,
        )

        # Builtin palette command: /help
        res_help = repl.execute_one("/help")
        self.assertTrue(res_help["ok"])
        self.assertIn("LUCY COMMAND PALETTE", res_help["output"])
        self.assertGreater(res_help["elapsed_ms"], 0.0)

        # Builtin palette command: /exit
        res_exit = repl.execute_one("/exit")
        self.assertTrue(res_exit["should_exit"])
        self.assertIn("closed cleanly", res_exit["output"])

        # Macro execution
        repl.macros.register_macro("pipe_test", "cmd_one && cmd_two")
        res_macro = repl.execute_one("/pipe_test")
        self.assertIn("[cmd_one]", res_macro["output"])
        self.assertIn("[cmd_two]", res_macro["output"])
        self.assertIn("cmd_one", mock_rt.commands_received)
        self.assertIn("cmd_two", mock_rt.commands_received)

    def test_repl_interactive_stream_loop(self) -> None:
        """8. Interactive REPL stream execution loop with mock I/O and clean EOF shutdown."""
        mock_rt = MockRuntime()
        repl = TerminalREPL(
            runtime=mock_rt,
            lucy_data=self.tmp_path,
            enable_color=False,
        )

        in_stream = io.StringIO("/history\nhello world\n/exit\n")
        out_stream = io.StringIO()

        repl.run_interactive(
            input_stream=in_stream,
            output_stream=out_stream,
            max_turns=5,
        )

        output = out_stream.getvalue()
        self.assertIn("LUCY :: SOVEREIGN TERMINAL OPERATOR", output)
        self.assertIn("lucy::operator > ", output)
        self.assertIn("Echo from MockRuntime: hello world", output)
        self.assertIn("closed cleanly", output)

    def test_lucy_runtime_and_router_integration(self) -> None:
        """9. Full integration with CommandRouter and LucyRuntime."""
        runtime = LucyRuntime(project_root=Path(r"C:\Users\admin\Desktop\senin\LUCY\lucy"))
        router = CommandRouter(runtime)

        # REPL status via router
        resp_status = router.handle("/repl status")
        self.assertIn("Terminal REPL & Command Palette Status:", resp_status.message)
        self.assertIn("50 high-performance terminal repl", resp_status.message)

        # Palette via router
        resp_palette = router.handle("/palette")
        self.assertIn("LUCY COMMAND PALETTE", resp_palette.message)

        # History via router
        runtime.terminal_repl.history.add("test command")
        resp_hist = router.handle("/history")
        self.assertIn("Command History", resp_hist.message)
        self.assertIn("test command", resp_hist.message)

        # Direct runtime methods
        status_dict = runtime.terminal_repl_status()
        self.assertEqual(status_dict["stage"], STAGE)

        autocomplete_results = runtime.repl_autocomplete("/ke")
        self.assertIn("/keys", autocomplete_results)


if __name__ == "__main__":
    unittest.main()
