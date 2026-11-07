"""
tests/test_stage74_terminal_sentinel.py
Unit tests for Stage 74: Proactive Terminal Sentinel & Non-Intrusive Status Broadcaster
"""

import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path

from backend.lucy_core.terminal_sentinel import (
    FileDelta,
    SentinelPulse,
    TerminalSentinel,
    STAGE,
)


class MockRuntime:
    def __init__(self):
        self.memory_graph = MockMemoryGraph()
        self.task_daemon = MockTaskDaemon()
        self.tool_synthesizer = MockToolSynthesizer()


class MockMemoryGraph:
    def _read(self):
        return {"nodes": [{"id": "n1"}, {"id": "n2"}, {"id": "n3"}]}


class MockTaskDaemon:
    def list_tasks(self, status="running"):
        return [{"id": "t1"}]


class MockToolSynthesizer:
    def __init__(self):
        self.tools = {"tool_a": 1, "tool_b": 2}


class TestStage74TerminalSentinel(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_stage74_test_"))
        self.mock_runtime = MockRuntime()
        self.sentinel = TerminalSentinel(
            project_root=self.test_dir,
            runtime=self.mock_runtime,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_stage_constant(self):
        self.assertEqual(STAGE, 74)

    def test_02_snapshot_initialization(self):
        f1 = self.test_dir / "file1.txt"
        f1.write_text("hello", encoding="utf-8")
        f2 = self.test_dir / "file2.py"
        f2.write_text("print(1)", encoding="utf-8")

        count = self.sentinel.take_snapshot()
        self.assertEqual(count, 2)
        deltas = self.sentinel.detect_workspace_deltas()
        self.assertEqual(len(deltas), 0)

    def test_03_detect_file_addition(self):
        self.sentinel.take_snapshot()
        new_f = self.test_dir / "new_file.py"
        new_f.write_text("x = 10", encoding="utf-8")

        deltas = self.sentinel.detect_workspace_deltas()
        self.assertEqual(len(deltas), 1)
        self.assertEqual(deltas[0].change_type, "added")
        self.assertEqual(deltas[0].path, "new_file.py")

    def test_04_detect_file_modification(self):
        f = self.test_dir / "mod_file.py"
        f.write_text("original", encoding="utf-8")
        self.sentinel.take_snapshot()

        time.sleep(0.05)
        f.write_text("modified content", encoding="utf-8")

        deltas = self.sentinel.detect_workspace_deltas()
        self.assertEqual(len(deltas), 1)
        self.assertEqual(deltas[0].change_type, "modified")
        self.assertEqual(deltas[0].path, "mod_file.py")

    def test_05_detect_file_deletion(self):
        f = self.test_dir / "del_file.py"
        f.write_text("delete me", encoding="utf-8")
        self.sentinel.take_snapshot()

        f.unlink()

        deltas = self.sentinel.detect_workspace_deltas()
        self.assertEqual(len(deltas), 1)
        self.assertEqual(deltas[0].change_type, "deleted")
        self.assertEqual(deltas[0].path, "del_file.py")

    def test_06_pulse_telemetry_gathering(self):
        pulse = self.sentinel.pulse()
        self.assertIsInstance(pulse, SentinelPulse)
        self.assertEqual(pulse.memory_nodes_count, 3)
        self.assertEqual(pulse.background_tasks_count, 1)
        self.assertEqual(pulse.synthesized_tools_count, 2)
        one_line = pulse.to_one_line()
        self.assertIn("[SENTINEL |", one_line)
        self.assertIn("MemNodes:3", one_line)
        self.assertIn("Tools:2", one_line)

    def test_07_toggle_banner(self):
        self.assertFalse(self.sentinel.banner_enabled)
        res1 = self.sentinel.toggle_banner()
        self.assertTrue(res1)
        self.assertTrue(self.sentinel.banner_enabled)
        res2 = self.sentinel.toggle_banner()
        self.assertFalse(res2)

    def test_08_dashboard_ascii_safety(self):
        f = self.test_dir / "code.py"
        f.write_text("pass", encoding="utf-8")
        self.sentinel.take_snapshot()

        f2 = self.test_dir / "added.py"
        f2.write_text("x = 1", encoding="utf-8")

        dashboard = self.sentinel.format_terminal_dashboard()
        # Verify strict ASCII compatibility (no crashes on cp1252)
        dashboard.encode("ascii")
        self.assertIn("LUCY TERMINAL SENTINEL DASHBOARD", dashboard)
        self.assertIn("+", dashboard)
        self.assertIn("-", dashboard)
        self.assertIn("|", dashboard)
        self.assertIn("added.py", dashboard)

    def test_09_diff_list_formatting(self):
        self.sentinel.take_snapshot()
        f = self.test_dir / "diff_target.txt"
        f.write_text("content", encoding="utf-8")

        diff_str = self.sentinel.format_diff_list()
        self.assertIn("Workspace Deltas", diff_str)
        self.assertIn("[ADDED] diff_target.txt", diff_str)

    def test_10_git_and_ollama_fallback(self):
        # Even with nonexistent git repo and invalid url, should not raise
        git_res = self.sentinel.check_git_status()
        self.assertIn("branch", git_res)
        self.assertIn("dirty", git_res)

        ollama_res = self.sentinel.check_ollama_health()
        self.assertIn("online", ollama_res)
        self.assertIn("model", ollama_res)


if __name__ == "__main__":
    unittest.main()
