"""
tests/test_stage111_workspace_daemon.py
Stage 111: Proactive Workspace & Process Sensor Daemon Unit Tests
"""

import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path

from backend.lucy_core.workspace_daemon import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    STAGE,
    DaemonState,
    FileChangeEvent,
    StagedContext,
    WorkspaceSensorDaemon,
)


class MockReceiptLedger:
    def __init__(self):
        self.receipts = []

    def issue_receipt(self, action_category, operation, target, verified_outcome):
        rec = {
            "category": action_category,
            "operation": operation,
            "target": target,
            "outcome": verified_outcome,
        }
        self.receipts.append(rec)
        return rec


class TestStage111WorkspaceDaemon(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="lucy_stage111_test_")
        self.temp_path = Path(self.temp_dir)
        self.project_root = Path(__file__).resolve().parent.parent

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_constants_and_metadata(self):
        self.assertEqual(STAGE, 111)
        self.assertEqual(ERA, 12)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")

    def test_02_initialization_and_snapshot(self):
        daemon = WorkspaceSensorDaemon(
            project_root=self.project_root,
            data_dir=self.temp_path / "daemon",
        )
        self.assertGreater(daemon.status()["watched_files_count"], 10)
        self.assertGreaterEqual(daemon.status()["total_scans"], 1)

    def test_03_stage_file_context(self):
        daemon = WorkspaceSensorDaemon(
            project_root=self.project_root,
            data_dir=self.temp_path / "daemon",
        )
        staged = daemon.stage_file_context("backend/lucy_core/token_compressor.py")
        self.assertIsNotNone(staged)
        self.assertEqual(staged.source_file, "backend/lucy_core/token_compressor.py")
        self.assertIn("SemanticTokenCompressor", staged.symbols)
        self.assertGreater(staged.line_count, 100)
        self.assertEqual(len(staged.sha256), 64)
        self.assertTrue(staged.matching_test_file.endswith("test_stage107_token_compressor.py"))

    def test_04_delta_detection_on_file_write(self):
        # Create a mock workspace root
        ws_root = self.temp_path / "mock_workspace"
        ws_root.mkdir()
        daemon = WorkspaceSensorDaemon(
            project_root=ws_root,
            data_dir=self.temp_path / "daemon",
        )

        # 1. Create file
        test_file = ws_root / "sample.py"
        test_file.write_text("def hello(): return 1\n", encoding="utf-8")
        changes = daemon.scan_now()
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].change_type, "CREATED")
        self.assertEqual(changes[0].path, "sample.py")

        # 2. Modify file
        time.sleep(0.05)
        test_file.write_text("def hello(): return 42\n", encoding="utf-8")
        changes2 = daemon.scan_now()
        self.assertEqual(len(changes2), 1)
        self.assertEqual(changes2[0].change_type, "MODIFIED")

        # 3. Delete file
        test_file.unlink()
        changes3 = daemon.scan_now()
        self.assertEqual(len(changes3), 1)
        self.assertEqual(changes3[0].change_type, "DELETED")

    def test_05_lifecycle_start_stop_toggle(self):
        daemon = WorkspaceSensorDaemon(
            project_root=self.project_root,
            data_dir=self.temp_path / "daemon",
            scan_interval_sec=0.1,
        )
        self.assertFalse(daemon.is_running())

        daemon.start()
        self.assertTrue(daemon.is_running())

        res_toggle = daemon.toggle()
        self.assertFalse(daemon.is_running())
        self.assertIn("STOPPED", res_toggle)

        res_toggle2 = daemon.toggle()
        self.assertTrue(daemon.is_running())
        self.assertIn("RUNNING", res_toggle2)

        daemon.stop()
        self.assertFalse(daemon.is_running())

    def test_06_receipt_ledger_emission(self):
        ledger = MockReceiptLedger()
        daemon = WorkspaceSensorDaemon(
            project_root=self.project_root,
            data_dir=self.temp_path / "daemon",
            receipt_ledger=ledger,
        )
        daemon.stage_file_context("backend/lucy_core/token_compressor.py")
        self.assertGreaterEqual(len(ledger.receipts), 1)
        self.assertEqual(ledger.receipts[0]["category"], "CONTEXT_STAGED_RECEIPT")

    def test_07_ascii_formatting(self):
        daemon = WorkspaceSensorDaemon(
            project_root=self.project_root,
            data_dir=self.temp_path / "daemon",
        )
        daemon.stage_file_context("backend/lucy_core/token_compressor.py")
        tbl = daemon.format_daemon_status_table()
        self.assertIn("+--------------------------------------------------------------------------------+", tbl)
        self.assertIn("LUCY OS - PROACTIVE WORKSPACE & SENSOR DAEMON", tbl)
        self.assertIn("Senin Ali K P", tbl)
        self.assertIn("token_compressor.py", tbl)

    def test_08_status_dictionary(self):
        daemon = WorkspaceSensorDaemon(
            project_root=self.project_root,
            data_dir=self.temp_path / "daemon",
        )
        st = daemon.status()
        self.assertEqual(st["stage"], 111)
        self.assertEqual(st["era"], 12)
        self.assertEqual(st["creator"], "Senin")
        self.assertEqual(st["creator_full_name"], "Senin Ali K P")
        self.assertIn("watched_files_count", st)

    def test_09_get_staged_context_lookup(self):
        daemon = WorkspaceSensorDaemon(
            project_root=self.project_root,
            data_dir=self.temp_path / "daemon",
        )
        daemon.stage_file_context("backend/lucy_core/token_compressor.py")
        ctx = daemon.get_staged_context("backend\\lucy_core\\token_compressor.py")
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.source_file, "backend/lucy_core/token_compressor.py")

    def test_10_ignore_dirs_and_extensions(self):
        ws_root = self.temp_path / "custom_ws"
        ws_root.mkdir()
        daemon = WorkspaceSensorDaemon(
            project_root=ws_root,
            data_dir=self.temp_path / "daemon",
        )
        # Create non-watched file
        bin_file = ws_root / "binary.bin"
        bin_file.write_bytes(b"\x00\x01\x02")
        # Create file in ignored directory
        git_dir = ws_root / ".git"
        git_dir.mkdir()
        (git_dir / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")

        changes = daemon.scan_now()
        self.assertEqual(len(changes), 0)

    def test_11_daemon_pulse_delta_buffer(self):
        ws_root = self.temp_path / "pulse_ws"
        ws_root.mkdir()
        daemon = WorkspaceSensorDaemon(
            project_root=ws_root,
            data_dir=self.temp_path / "daemon",
        )
        f1 = ws_root / "file1.py"
        f1.write_text("x = 1\n", encoding="utf-8")
        changes = daemon.scan_now()
        self.assertEqual(len(changes), 1)
        self.assertEqual(len(daemon._recent_events), 1)


if __name__ == "__main__":
    unittest.main()
