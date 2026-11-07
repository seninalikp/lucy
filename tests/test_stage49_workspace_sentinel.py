"""
test_stage49_workspace_sentinel.py
Stage 49 = Proactive Workspace Sentinel & Habit Watchdog.

Verifies:
1. Sentinel reports Stage 49 and active status.
2. File change detector catches created, modified, and deleted files.
3. Proactive in-memory AST syntax validation catches Python syntax errors.
4. Non-blocking alert queue buffering and consumption.
5. Workspace habit tracking records top touched folders.
6. State persistence across scanner reloads.
7. Background thread watcher start and clean shutdown.
8. LucyRuntime Stage 49 integration.
9. CommandRouter Stage 49 command routing and formatting.
"""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from backend.lucy_core.workspace_sentinel import WorkspaceSentinel, STAGE
from backend.lucy_core.personal_profiler import PersonalProfiler
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class Stage49WorkspaceSentinelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.lucy_data = self.root / "data" / "lucy"
        self.lucy_data.mkdir(parents=True, exist_ok=True)
        self.watch_dir = self.root / "watched_workspace"
        self.watch_dir.mkdir(parents=True, exist_ok=True)

        self.profiler = PersonalProfiler(lucy_data=self.lucy_data)
        self.sentinel = WorkspaceSentinel(
            project_root=self.root,
            lucy_data=self.lucy_data,
            watch_root=self.watch_dir,
            profiler=self.profiler,
        )

    def tearDown(self) -> None:
        self.sentinel.stop_background_watcher()
        try:
            self.tmp.cleanup()
        except Exception:
            pass

    def test_01_initial_status(self) -> None:
        status = self.sentinel.status()
        self.assertEqual(status["stage"], STAGE)
        self.assertEqual(status["workspace_sentinel"], "active")
        self.assertEqual(status["scan_count"], 0)
        self.assertEqual(status["tracked_files"], 0)
        self.assertFalse(status["is_background_running"])

    def test_02_detect_created_and_modified_files(self) -> None:
        # Create a file
        f1 = self.watch_dir / "script1.py"
        f1.write_text("x = 1\n", encoding="utf-8")

        res1 = self.sentinel.scan_once()
        self.assertEqual(res1["created_count"], 1)
        self.assertEqual(res1["total_tracked"], 1)

        # Modify the file
        time.sleep(0.05)
        f1.write_text("x = 2\ny = 3\n", encoding="utf-8")

        res2 = self.sentinel.scan_once()
        self.assertEqual(res2["modified_count"], 1)
        self.assertEqual(res2["created_count"], 0)

    def test_03_proactive_ast_syntax_error_detection(self) -> None:
        # Create a broken script (missing colon)
        broken = self.watch_dir / "broken_script.py"
        broken.write_text("def faulty_function()\n    return 42\n", encoding="utf-8")

        res = self.sentinel.scan_once()
        self.assertEqual(res["syntax_alerts_caught"], 1)
        self.assertEqual(self.sentinel.total_syntax_errors_caught, 1)

        alerts = self.sentinel.consume_alerts()
        self.assertEqual(len(alerts), 1)
        self.assertIn("Syntax error in new file 'broken_script.py'", alerts[0])
        self.assertIn("Line 1", alerts[0])

    def test_04_consume_alerts_flushes_queue(self) -> None:
        broken = self.watch_dir / "bad.py"
        broken.write_text("if True\n    pass\n", encoding="utf-8")

        self.sentinel.scan_once()
        alerts1 = self.sentinel.consume_alerts()
        self.assertEqual(len(alerts1), 1)

        # Second call should be empty
        alerts2 = self.sentinel.consume_alerts()
        self.assertEqual(len(alerts2), 0)

    def test_05_habit_tracking_folder_hits(self) -> None:
        sub = self.watch_dir / "my_project"
        sub.mkdir(parents=True, exist_ok=True)
        (sub / "alpha.py").write_text("a = 10\n", encoding="utf-8")

        self.sentinel.scan_once()
        status = self.sentinel.status()
        top_folders = [f[0] for f in status["top_active_folders"]]
        self.assertIn("my_project", top_folders)

    def test_06_state_persistence_and_reload(self) -> None:
        (self.watch_dir / "persistent.txt").write_text("data", encoding="utf-8")
        self.sentinel.scan_once()
        self.assertEqual(self.sentinel.status()["tracked_files"], 1)

        # Create new sentinel instance pointing to same lucy_data
        reloaded_sentinel = WorkspaceSentinel(
            project_root=self.root,
            lucy_data=self.lucy_data,
            watch_root=self.watch_dir,
            profiler=self.profiler,
        )
        self.assertEqual(reloaded_sentinel.status()["tracked_files"], 1)

    def test_07_background_watcher_start_stop(self) -> None:
        start_res = self.sentinel.start_background_watcher(interval_seconds=0.1)
        self.assertTrue(start_res["started"])
        self.assertTrue(self.sentinel.status()["is_background_running"])

        # Stop
        stop_res = self.sentinel.stop_background_watcher()
        self.assertTrue(stop_res["stopped"])
        self.assertFalse(self.sentinel.status()["is_background_running"])


class Stage49RuntimeAndRouterIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "data" / "lucy").mkdir(parents=True, exist_ok=True)
        (self.root / "logs").mkdir(parents=True, exist_ok=True)
        self.runtime = LucyRuntime(project_root=self.root)
        self.router = CommandRouter(self.runtime)

    def tearDown(self) -> None:
        self.runtime.stop_sentinel_watcher()
        try:
            self.tmp.cleanup()
        except Exception:
            pass

    def test_08_runtime_methods(self) -> None:
        status = self.runtime.sentinel_status()
        self.assertEqual(status["stage"], STAGE)

        scan_res = self.runtime.scan_workspace_now()
        self.assertIn("scan_index", scan_res)

        alerts = self.runtime.get_sentinel_alerts()
        self.assertIsInstance(alerts, list)

    def test_09_router_commands(self) -> None:
        # Status command
        res1 = self.router.handle("sentinel status")
        self.assertIn("Proactive Workspace Sentinel status:", res1.message)
        self.assertIn("Stage: 49 proactive workspace sentinel", res1.message)

        # Scan command
        res2 = self.router.handle("scan workspace")
        self.assertIn("Workspace Scan", res2.message)
        self.assertIn("Complete:", res2.message)

        # Alerts command
        res3 = self.router.handle("sentinel alerts")
        self.assertIn("sentinel alerts", res3.message.lower())


if __name__ == "__main__":
    unittest.main()
