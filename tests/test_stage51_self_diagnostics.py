"""
test_stage51_self_diagnostics.py
Stage 51 = Self-Diagnostics & Crash Recovery Daemon.

Verifies:
1. Daemon reports Stage 51 and ready status with complete schema.
2. State file auditor validates healthy JSON files and creates .bak backups.
3. State file auditor recovers corrupted JSON files from .bak backups.
4. State file auditor reconstructs default schemas when no backup exists.
5. Log hygiene monitor enforces size limits and performs rolling rotation.
6. Log hygiene monitor removes orphaned .tmp scratch files.
7. Subsystem health prober generates overall health matrix and probes services.
8. Crash recovery daemon executes auto-heal pipeline and reports actions taken.
9. Full integration with CommandRouter and LucyRuntime.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.self_diagnostics import (
    CrashRecoveryDaemon,
    LogHygieneMonitor,
    StateFileAuditor,
    SubsystemHealthProber,
    STAGE,
)
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class MockSentinel:
    def __init__(self, running: bool = True) -> None:
        self._running = running

    def is_watching(self) -> bool:
        return self._running

    def start_background_watcher(self, interval_seconds: float = 30.0) -> dict:
        self._running = True
        return {"status": "started"}

    def status(self) -> dict:
        return {
            "background_watcher": {"running": self._running},
            "files_tracked": 50,
            "pending_alerts_count": 0,
        }


class MockTaskDaemon:
    def get_queue_length(self) -> int:
        return 0


class MockRuntime:
    """Mock runtime for self-diagnostics unit tests."""
    def __init__(self) -> None:
        self.workspace_sentinel = MockSentinel(running=False)
        self.task_daemon = MockTaskDaemon()

    def sentinel_status(self) -> dict:
        return self.workspace_sentinel.status()

    def provider_pool_status(self) -> dict:
        return {
            "total_keys": 25,
            "healthy_keys": 25,
            "active_provider": "groq",
        }


class Stage51SelfDiagnosticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.project_root = self.tmp_path / "project"
        self.lucy_data = self.project_root / "data" / "lucy"
        self.logs_dir = self.project_root / "logs"

        self.project_root.mkdir(parents=True, exist_ok=True)
        self.lucy_data.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        try:
            self.tmp.cleanup()
        except Exception:
            pass

    def test_stage_identity_and_status(self) -> None:
        """1. Daemon reports Stage 51 and ready status with complete schema."""
        daemon = CrashRecoveryDaemon(
            project_root=self.project_root,
            lucy_data=self.lucy_data,
        )
        status = daemon.status()
        self.assertEqual(status["stage"], "51 self-diagnostics & crash recovery daemon")
        self.assertEqual(status["status"], "ready")
        self.assertIn("monitored_critical_files", status)
        self.assertIn("last_check", status)

    def test_state_file_auditor_healthy_files(self) -> None:
        """2. State file auditor validates healthy JSON files and creates .bak backups."""
        auditor = StateFileAuditor(project_root=self.project_root, lucy_data=self.lucy_data)
        test_file = self.lucy_data / "test_state.json"
        test_file.write_text(json.dumps({"counter": 42}), encoding="utf-8")

        valid, reason = auditor.validate_file(test_file)
        self.assertTrue(valid)
        self.assertEqual(reason, "valid")

        bak = auditor.create_backup(test_file)
        self.assertIsNotNone(bak)
        self.assertTrue(bak.exists())
        self.assertEqual(bak.suffix, ".bak")

    def test_state_file_auditor_corruption_recovery(self) -> None:
        """3. State file auditor recovers corrupted JSON files from .bak backups."""
        auditor = StateFileAuditor(project_root=self.project_root, lucy_data=self.lucy_data)
        test_file = self.lucy_data / "terminal_history.json"
        healthy_content = json.dumps([{"command": "status"}])
        test_file.write_text(healthy_content, encoding="utf-8")

        # Create valid backup
        auditor.create_backup(test_file)

        # Corrupt file with malformed syntax
        test_file.write_text("{corrupted json without closing", encoding="utf-8")
        valid, reason = auditor.validate_file(test_file)
        self.assertFalse(valid)
        self.assertTrue("json_decode_error" in reason)

        # Restore from backup
        restored = auditor.restore_from_backup(test_file)
        self.assertTrue(restored)

        # Validate that restored content is healthy
        valid_now, _ = auditor.validate_file(test_file)
        self.assertTrue(valid_now)
        self.assertEqual(test_file.read_text(encoding="utf-8"), healthy_content)

    def test_state_file_auditor_default_reconstruction(self) -> None:
        """4. State file auditor reconstructs default schemas when no backup exists."""
        auditor = StateFileAuditor(project_root=self.project_root, lucy_data=self.lucy_data)
        missing_file = self.lucy_data / "user_macros.json"
        self.assertFalse(missing_file.exists())

        reconstructed = auditor.reconstruct_default(missing_file)
        self.assertTrue(reconstructed)
        self.assertTrue(missing_file.exists())

        data = json.loads(missing_file.read_text(encoding="utf-8"))
        self.assertIn("quickcheck", data)

    def test_log_hygiene_monitor_rotation(self) -> None:
        """5. Log hygiene monitor enforces size limits and performs rolling rotation."""
        monitor = LogHygieneMonitor(
            log_dirs=[self.logs_dir],
            max_size_bytes=100,  # 100 bytes threshold for test
            max_rotations=2,
        )
        log_file = self.logs_dir / "test.log"
        log_file.write_text("A" * 200, encoding="utf-8")

        res = monitor.check_and_clean()
        self.assertIn("test.log", res["rotated_logs"])

        # Rotated file should exist as .1
        rot_1 = self.logs_dir / "test.log.1"
        self.assertTrue(rot_1.exists())
        self.assertEqual(rot_1.stat().st_size, 200)

        # Main log should be truncated/fresh
        self.assertTrue(log_file.exists())
        self.assertEqual(log_file.stat().st_size, 0)

    def test_log_hygiene_orphaned_tmp_cleanup(self) -> None:
        """6. Log hygiene monitor removes orphaned .tmp scratch files."""
        monitor = LogHygieneMonitor(log_dirs=[self.logs_dir])
        tmp_file = self.lucy_data / "orphaned.tmp"
        tmp_file.write_text("temporary scratch data", encoding="utf-8")

        count, freed = monitor.clean_orphaned_tmp_files(self.lucy_data)
        self.assertEqual(count, 1)
        self.assertGreater(freed, 0)
        self.assertFalse(tmp_file.exists())

    def test_subsystem_health_prober(self) -> None:
        """7. Subsystem health prober generates overall health matrix and probes services."""
        prober = SubsystemHealthProber()
        mock_rt = MockRuntime()
        report = prober.probe_all(mock_rt)

        self.assertIn("overall_health", report)
        self.assertIn("timestamp", report)
        self.assertIn("subsystems", report)
        subsystems = report["subsystems"]
        self.assertIn("ollama", subsystems)
        self.assertIn("workspace_sentinel", subsystems)
        self.assertIn("task_daemon", subsystems)
        self.assertIn("provider_pool", subsystems)

    def test_auto_heal_execution(self) -> None:
        """8. Crash recovery daemon executes auto-heal pipeline and reports actions taken."""
        mock_rt = MockRuntime()
        self.assertFalse(mock_rt.workspace_sentinel.is_watching())

        daemon = CrashRecoveryDaemon(
            project_root=self.project_root,
            lucy_data=self.lucy_data,
            runtime=mock_rt,
        )

        heal_res = daemon.auto_heal()
        self.assertIn("healed", heal_res)
        self.assertIn("actions_taken", heal_res)
        self.assertIn("current_health", heal_res)

        # Sentinel watcher should have been restarted
        self.assertTrue(mock_rt.workspace_sentinel.is_watching())
        self.assertTrue(any("Restarted WorkspaceSentinel" in a for a in heal_res["actions_taken"]))

    def test_lucy_runtime_and_router_integration(self) -> None:
        """9. Full integration with CommandRouter and LucyRuntime."""
        runtime = LucyRuntime(project_root=Path(r"C:\Users\admin\Desktop\senin\LUCY\lucy"))
        router = CommandRouter(runtime)

        # Diagnostics via router
        resp_diag = router.handle("/diagnostics")
        self.assertIn("Lucy Self-Diagnostics Report", resp_diag.message)
        self.assertIn("Subsystem Statuses:", resp_diag.message)

        # Auto-heal via router
        resp_heal = router.handle("/heal")
        self.assertIn("Lucy Auto-Heal Execution", resp_heal.message)

        # Snapshot backups via router
        resp_backup = router.handle("/backup")
        self.assertIn("Lucy State Snapshot Complete", resp_backup.message)

        # Direct runtime methods
        status_dict = runtime.self_diagnostics_status()
        self.assertEqual(status_dict["stage"], STAGE)


if __name__ == "__main__":
    unittest.main()
