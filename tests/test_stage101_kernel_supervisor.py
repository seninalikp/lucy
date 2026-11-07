"""
tests/test_stage101_kernel_supervisor.py
Stage 101: Autonomous Kernel & Process Watchdog Fabric Unit Tests
"""

import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path

from backend.lucy_core.kernel_supervisor import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    STAGE,
    KernelSupervisor,
    SubsystemRegistration,
    SubsystemStatus,
    SupervisorAuditReport,
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


class TestStage101KernelSupervisor(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="lucy_stage101_test_")
        self.temp_path = Path(self.temp_dir)
        self.project_root = Path(__file__).resolve().parent.parent

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_constants_and_metadata(self):
        self.assertEqual(STAGE, 101)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")

    def test_02_register_and_unregister(self):
        supervisor = KernelSupervisor(
            project_root=self.project_root,
            data_dir=self.temp_path / "supervisor",
        )
        reg = supervisor.register_subsystem("cron_daemon", subsystem_type="daemon", stall_timeout_sec=10.0)
        self.assertEqual(reg.name, "cron_daemon")
        self.assertEqual(reg.subsystem_type, "daemon")
        self.assertEqual(reg.stall_timeout_sec, 10.0)
        self.assertEqual(reg.status, SubsystemStatus.HEALTHY)

        self.assertIn("cron_daemon", supervisor._registry)
        unreg = supervisor.unregister_subsystem("cron_daemon")
        self.assertTrue(unreg)
        self.assertNotIn("cron_daemon", supervisor._registry)

    def test_03_heartbeat_recording(self):
        supervisor = KernelSupervisor(
            project_root=self.project_root,
            data_dir=self.temp_path / "supervisor",
        )
        reg = supervisor.register_subsystem("workspace_sensor", stall_timeout_sec=5.0)
        old_hb = reg.last_heartbeat

        time.sleep(0.01)
        res = supervisor.heartbeat("workspace_sensor")
        self.assertTrue(res)
        self.assertGreater(reg.last_heartbeat, old_hb)

        # Heartbeat to unregistered subsystem returns False
        self.assertFalse(supervisor.heartbeat("unknown_subsystem"))

    def test_04_stall_detection(self):
        supervisor = KernelSupervisor(
            project_root=self.project_root,
            data_dir=self.temp_path / "supervisor",
            default_stall_timeout_sec=1.0,
        )
        reg = supervisor.register_subsystem("hardware_telemetry", stall_timeout_sec=0.1)

        # Artificially age the heartbeat
        reg.last_heartbeat = time.time() - 10.0

        report = supervisor.audit_heartbeats(auto_recover=False)
        self.assertEqual(report.stalled_count, 1)
        self.assertEqual(reg.status, SubsystemStatus.STALLED)
        self.assertIn("hardware_telemetry", report.action_taken)

    def test_05_custom_check_fn_failure(self):
        supervisor = KernelSupervisor(
            project_root=self.project_root,
            data_dir=self.temp_path / "supervisor",
        )
        supervisor.register_subsystem("failing_worker", check_fn=lambda: False)

        report = supervisor.audit_heartbeats(auto_recover=False)
        self.assertEqual(report.stalled_count, 1)
        self.assertEqual(supervisor._registry["failing_worker"].status, SubsystemStatus.STALLED)

    def test_06_autonomous_recovery_success(self):
        restarted = False

        def mock_restart():
            nonlocal restarted
            restarted = True
            return True

        supervisor = KernelSupervisor(
            project_root=self.project_root,
            data_dir=self.temp_path / "supervisor",
        )
        supervisor.register_subsystem("flaky_service", restart_fn=mock_restart)

        # Trigger recovery
        res = supervisor.recover_subsystem("flaky_service")
        self.assertTrue(res["success"])
        self.assertTrue(restarted)
        self.assertEqual(res["restarts_count"], 1)
        self.assertEqual(supervisor._registry["flaky_service"].status, SubsystemStatus.RECOVERED)

    def test_07_recovery_failure_handling(self):
        def bad_restart():
            raise RuntimeError("Hardware bus locked")

        supervisor = KernelSupervisor(
            project_root=self.project_root,
            data_dir=self.temp_path / "supervisor",
        )
        supervisor.register_subsystem("broken_device", restart_fn=bad_restart)

        res = supervisor.recover_subsystem("broken_device")
        self.assertFalse(res["success"])
        self.assertIn("Hardware bus locked", res["error"])
        self.assertEqual(supervisor._registry["broken_device"].status, SubsystemStatus.FAILED)

    def test_08_native_memory_inspection(self):
        supervisor = KernelSupervisor(
            project_root=self.project_root,
            data_dir=self.temp_path / "supervisor",
        )
        ws_mb, priv_mb = supervisor.get_process_memory()
        self.assertGreater(ws_mb, 0.0)
        self.assertGreater(priv_mb, 0.0)

        mem_check = supervisor.check_memory_runaway(threshold_mb=10000.0)
        self.assertFalse(mem_check["runaway_detected"])
        self.assertEqual(mem_check["action"], "NORMAL")

    def test_09_memory_runaway_emergency_gc(self):
        ledger = MockReceiptLedger()
        supervisor = KernelSupervisor(
            project_root=self.project_root,
            receipt_ledger=ledger,
            data_dir=self.temp_path / "supervisor",
        )
        # Force threshold very low to test runaway response
        res = supervisor.check_memory_runaway(threshold_mb=0.0001)
        self.assertTrue(res["runaway_detected"])
        self.assertEqual(res["action"], "EMERGENCY_GC_TRIGGERED")

        # Verify receipt
        self.assertEqual(len(ledger.receipts), 1)
        self.assertEqual(ledger.receipts[0]["category"], "SUPERVISOR_MEMORY_GUARD")

    def test_10_receipt_ledger_recovery_receipt(self):
        ledger = MockReceiptLedger()
        supervisor = KernelSupervisor(
            project_root=self.project_root,
            receipt_ledger=ledger,
            data_dir=self.temp_path / "supervisor",
        )
        supervisor.register_subsystem("audit_worker", restart_fn=lambda: True)
        supervisor.recover_subsystem("audit_worker")

        self.assertEqual(len(ledger.receipts), 1)
        self.assertEqual(ledger.receipts[0]["category"], "SUPERVISOR_RECOVERY")
        self.assertEqual(ledger.receipts[0]["target"], "audit_worker")

    def test_11_cp1252_ascii_summary_and_status(self):
        supervisor = KernelSupervisor(
            project_root=self.project_root,
            data_dir=self.temp_path / "supervisor",
        )
        supervisor.register_subsystem("cron_scheduler", subsystem_type="daemon")
        supervisor.register_subsystem("hardware_telemetry", subsystem_type="sensor")

        summary = supervisor.supervisor_status()
        self.assertIn("LUCY OS - AUTONOMOUS KERNEL SUPERVISOR", summary)
        self.assertIn("STAGE 101: PROCESS WATCHDOG FABRIC", summary)
        self.assertIn("cron_scheduler", summary)
        self.assertIn("hardware_telemet", summary)

        # CP1252 verification
        summary.encode("cp1252")

        st = supervisor.status()
        self.assertEqual(st["stage"], 101)
        self.assertEqual(st["total_registered"], 2)


if __name__ == "__main__":
    unittest.main()
