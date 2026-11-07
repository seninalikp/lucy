"""
test_stage38_task_daemon.py
Unit tests for Stage 38: Autonomous Task Daemon & Dynamic Conversational Router.
"""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from backend.lucy_core.task_daemon import (
    TaskDaemon,
    STAGE,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_FAILED,
    TASK_STATUS_CANCELLED,
    TASK_STATUS_RUNNING,
)
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class Stage38TaskDaemonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.lucy_data = Path(self.temp_dir.name)
        self.daemon = TaskDaemon(self.lucy_data, max_workers=2)

    def tearDown(self) -> None:
        self.daemon.shutdown(wait=False)
        self.temp_dir.cleanup()

    def test_01_initial_status(self) -> None:
        st = self.daemon.status()
        self.assertEqual(st["stage"], STAGE)
        self.assertEqual(st["task_daemon"], "active")
        self.assertEqual(st["total_tasks"], 0)
        self.assertEqual(st["pending_count"], 0)
        self.assertEqual(st["running_count"], 0)
        self.assertEqual(st["completed_count"], 0)

    def test_02_submit_and_complete_task(self) -> None:
        def simple_worker(x: int, y: int) -> int:
            time.sleep(0.05)
            return x + y

        task_id = self.daemon.submit_task("Add Numbers", simple_worker, 10, 25, total_steps=1)
        self.assertTrue(task_id.startswith("task_"))

        # Wait briefly for completion
        time.sleep(0.2)

        task = self.daemon.get_task(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task["status"], TASK_STATUS_COMPLETED)
        self.assertEqual(task["result"], 35)
        self.assertIsNotNone(task["started_at"])
        self.assertIsNotNone(task["completed_at"])
        self.assertGreaterEqual(task["duration_seconds"], 0.04)

        # Check list_tasks
        tasks = self.daemon.list_tasks(status="COMPLETED")
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["task_id"], task_id)

    def test_03_task_progress_tracking(self) -> None:
        def stepped_worker(task_id: str, progress_callback) -> str:
            progress_callback(1, 3, "Step 1 complete")
            time.sleep(0.05)
            progress_callback(2, 3, "Step 2 complete")
            time.sleep(0.05)
            return "done"

        task_id = self.daemon.submit_task("Stepped Job", stepped_worker, total_steps=3)
        time.sleep(0.2)

        task = self.daemon.get_task(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task["status"], TASK_STATUS_COMPLETED)
        self.assertEqual(task["progress_step"], 3)
        self.assertEqual(task["result"], "done")

    def test_04_task_failure_handling(self) -> None:
        def faulty_worker() -> None:
            raise ValueError("Simulated worker crash")

        task_id = self.daemon.submit_task("Faulty Job", faulty_worker)
        time.sleep(0.15)

        task = self.daemon.get_task(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task["status"], TASK_STATUS_FAILED)
        self.assertIn("Simulated worker crash", task["error"])
        self.assertIn("Failed:", task["progress_message"])

    def test_05_task_cancellation(self) -> None:
        def cancellable_worker(cancel_event) -> str:
            for _ in range(50):
                if cancel_event.is_set():
                    return "cancelled_early"
                time.sleep(0.02)
            return "finished"

        task_id = self.daemon.submit_task("Long Job", cancellable_worker)
        time.sleep(0.05)
        cancel_res = self.daemon.cancel_task(task_id)
        self.assertTrue(cancel_res["cancelled"])

        time.sleep(0.15)
        task = self.daemon.get_task(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task["status"], TASK_STATUS_CANCELLED)

    def test_06_history_persistence_and_reload(self) -> None:
        def quick_job() -> str:
            return "saved"

        task_id = self.daemon.submit_task("Persistent Job", quick_job)
        time.sleep(0.1)

        # Check history file
        self.assertTrue(self.daemon.history_file.exists())

        # Create new daemon instance on same data path
        new_daemon = TaskDaemon(self.lucy_data, max_workers=1)
        reloaded_task = new_daemon.get_task(task_id)
        new_daemon.shutdown(wait=False)

        self.assertIsNotNone(reloaded_task)
        self.assertEqual(reloaded_task["name"], "Persistent Job")
        self.assertEqual(reloaded_task["status"], TASK_STATUS_COMPLETED)
        self.assertEqual(reloaded_task["result"], "saved")


class Stage38RuntimeAndRouterIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = LucyRuntime(project_root=Path(__file__).resolve().parent.parent)
        cls.router = CommandRouter(cls.runtime)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.runtime.graceful_shutdown("Stage 38 test suite finished")

    def test_07_runtime_task_daemon_integration(self) -> None:
        st = self.runtime.task_daemon_status()
        self.assertEqual(st["stage"], STAGE)
        self.assertEqual(st["task_daemon"], "active")

        # Submit background task via runtime
        def runtime_bg_work() -> dict:
            return {"status": "ok", "processed": 42}

        task_id = self.runtime.submit_background_task("Runtime Job", runtime_bg_work)
        time.sleep(0.15)

        task = self.runtime.get_background_task(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task["status"], TASK_STATUS_COMPLETED)
        self.assertEqual(task["result"]["processed"], 42)

    def test_08_conversational_chat_and_routing(self) -> None:
        # Conversational chat with empty input
        res_empty = self.runtime.conversational_chat("")
        self.assertIn("listening", res_empty["message"])

        # Conversational chat with query
        res_query = self.runtime.conversational_chat("Tell me about our current project status.")
        self.assertIn("message", res_query)
        self.assertIn("source", res_query)
        self.assertIn("model", res_query)
        self.assertTrue(len(res_query["message"]) > 0)

        # Standard greetings still preserve immediate response
        greeting_res = self.runtime.lucy_respond("hello lucy")
        self.assertIn("Hey. I'm here. Active project:", greeting_res)

    def test_09_router_task_commands(self) -> None:
        # Daemon status command
        resp_status = self.router.handle("task daemon status")
        self.assertIn("Task Daemon status:", resp_status.message)
        self.assertIn("Stage: 38 autonomous task daemon", resp_status.message)

        # Background tasks command
        resp_list = self.router.handle("background tasks")
        self.assertIn("Background Tasks:", resp_list.message)

        # Submit a task to inspect via router
        def dummy_task() -> str:
            return "done"

        task_id = self.runtime.submit_background_task("Inspection Task", dummy_task)
        time.sleep(0.1)

        resp_detail = self.router.handle(f"task status {task_id}")
        self.assertIn(task_id, resp_detail.message)
        self.assertIn("Status: COMPLETED", resp_detail.message)

        # Cancel test via router
        def cancellable_cli(cancel_event) -> None:
            while not cancel_event.is_set():
                time.sleep(0.01)

        cancel_tid = self.runtime.submit_background_task("Cancel via Router", cancellable_cli)
        time.sleep(0.05)
        resp_cancel = self.router.handle(f"cancel task {cancel_tid}")
        self.assertIn("successfully cancelled", resp_cancel.message)


if __name__ == "__main__":
    unittest.main()
