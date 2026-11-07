"""
test_stage62_terminal_core_hardening.py
Verifies Stage 62 Pure Terminal Mode, Single-Pass Natural Action Execution,
Full Subject Memory Extraction, and Two-Layer Anti-Hallucination Guard.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class TestStage62TerminalCoreHardening(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "data" / "lucy").mkdir(parents=True, exist_ok=True)
        (self.root / "logs").mkdir(parents=True, exist_ok=True)
        self.runtime = LucyRuntime(project_root=self.root)
        self.router = CommandRouter(self.runtime)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_01_ui_is_disabled_by_default_in_terminal_mode(self) -> None:
        st = self.runtime.status()
        self.assertFalse(st["web_ui_enabled"])
        self.assertFalse(st["desktop_ui_enabled"])

    def test_02_natural_action_parser_preserves_full_subject_clause(self) -> None:
        res = self.runtime.natural_action_parser.parse_and_execute(
            "My primary focus is hardening Lucy in pure terminal mode."
        )
        self.assertGreaterEqual(res["actions_executed"], 1)
        mem_actions = [a for a in res["actions"] if a["type"] == "memory_saved"]
        self.assertTrue(mem_actions)
        self.assertIn("my primary focus is hardening lucy", mem_actions[0]["detail"].lower())

    def test_03_single_pass_turn_does_not_duplicate_tasks_or_memories(self) -> None:
        reply = self.router.handle(
            "Please add a task to benchmark terminal latency and remember that I prefer zero UI bloat."
        )
        self.assertIn("task_added", reply.message)
        open_tasks = self.runtime.project_summary().get("open_tasks", [])
        matching = [t for t in open_tasks if "benchmark terminal latency" in t.get("text", "").lower()]
        self.assertEqual(len(matching), 1)

    def test_04_conversational_chat_injects_workspace_and_guardrails(self) -> None:
        res = self.runtime.conversational_chat("tell me")
        self.assertIn("stage", res)
        self.assertTrue(res["verification"]["verified"])

    def test_05_hallucinated_file_claim_is_intercepted_in_terminal(self) -> None:
        guarded = self.runtime.fact_verifier.guard_response(
            "I have created the file phantom_terminal_module.py on disk.",
            runtime=self.runtime,
        )
        self.assertTrue(guarded["hallucination_detected"])
        self.assertIn("[ELIE: HALLUCINATION_INTERCEPTED", guarded["guarded_text"])


if __name__ == "__main__":
    unittest.main()
