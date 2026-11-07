"""
test_stage59_natural_action_parser.py
Automated test suite for Stage 59: Natural-Language Multi-Intent Action Parser & Grounded Executor.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.natural_action_parser import NaturalActionParser, STAGE
from backend.lucy_core.router import CommandRouter


class TestStage59NaturalActionParser(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.runtime = LucyRuntime(project_root=self.root)
        self.parser = NaturalActionParser(self.runtime)
        self.router = CommandRouter(self.runtime)

    def tearDown(self) -> None:
        self.runtime.graceful_shutdown("teardown")
        self.tmp.cleanup()

    def test_status(self) -> None:
        st = self.parser.status()
        self.assertEqual(st["stage"], STAGE)
        self.assertEqual(st["natural_action_parser"], "active")
        self.assertIn("natural_task_add", st["capabilities"])

    def test_natural_task_add(self) -> None:
        text = "Hey Lucy, please add a task to implement natural action parser"
        res = self.parser.parse_and_execute(text)
        self.assertGreaterEqual(res["actions_executed"], 1)
        self.assertTrue(any(a["type"] == "task_added" for a in res["actions"]))

        # Verify task is in projects
        tasks = self.runtime.projects.list_tasks()
        self.assertTrue(any("implement natural action parser" in t["text"].lower() for t in tasks))

        # Verify Stage 55 execution receipt was issued
        receipts = self.runtime.receipt_ledger.current_turn_receipts()
        self.assertTrue(any(r["operation"] == "add_task" for r in receipts))

    def test_natural_task_done(self) -> None:
        # Pre-create task
        res_add = self.runtime.projects.add_task("test LoRA fine tuning")
        tid = res_add["task"]["id"]

        text = "I finished the task test LoRA fine tuning"
        res = self.parser.parse_and_execute(text)
        self.assertGreaterEqual(res["actions_executed"], 1)
        self.assertTrue(any(a["type"] == "task_completed" for a in res["actions"]))

        # Verify task is completed
        tasks = self.runtime.projects.list_tasks()
        task_obj = next(task for task in tasks if task["id"] == tid)
        self.assertIn(task_obj["status"], ["done", "completed"])

    def test_cli_commands_skipped(self) -> None:
        text = "add task manual cli task"
        res = self.parser.parse_and_execute(text)
        self.assertEqual(res["actions_executed"], 0)

    def test_router_natural_action_status(self) -> None:
        resp = self.router.handle("natural action status")
        self.assertIn("59 natural language action parser", resp.message)

    def test_router_natural_flow_executes_actions(self) -> None:
        # Turn with natural task addition
        user_msg = "Please add a task to review the api server endpoints"
        resp = self.router.handle(user_msg)
        self.assertIn("[Verified Turn Actions Already Executed (Stage 59)]", resp.message)
        tasks = self.runtime.projects.list_tasks()
        self.assertTrue(any("review the api server endpoints" in t["text"].lower() for t in tasks))

    def test_subject_preservation_in_memory(self) -> None:
        user_msg = "My primary focus is anti-drift stability"
        res = self.parser.parse_and_execute(user_msg)
        self.assertGreaterEqual(res["actions_executed"], 1)
        mem_action = next(a for a in res["actions"] if a["type"] == "memory_saved")
        # Ensure subject "my primary focus is" is preserved, not stripped away
        self.assertIn("my primary focus is anti-drift stability", mem_action["detail"].lower())


if __name__ == "__main__":
    unittest.main()
