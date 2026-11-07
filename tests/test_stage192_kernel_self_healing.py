r"""
tests/test_stage192_kernel_self_healing.py
Unit tests for Stage 192: Dynamic Kernel Self-Healing & Crash Recovery Supervisor
Era 20: The Sovereign Bicentennial AGI Singularity & Autonomous Kernel Transcendence
"""

from __future__ import annotations

import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

import unittest
from backend.lucy_core.kernel_self_healing import (
    KernelSelfHealingFabric,
    RecoveryStrategy,
    SubsystemHealth,
)


class TestKernelSelfHealing(unittest.TestCase):
    def setUp(self) -> None:
        self.supervisor = KernelSelfHealingFabric(heartbeat_timeout=2.0, circuit_threshold=3)

    def test_subsystem_registration_and_initial_health(self) -> None:
        desc = self.supervisor.register_subsystem("ipc_bus", RecoveryStrategy.RESTART_CLEAN, {"queue": [1, 2]})
        self.assertEqual(desc.health, SubsystemHealth.HEALTHY)
        self.assertEqual(desc.name, "ipc_bus")
        self.assertEqual(desc.state["queue"], [1, 2])

    def test_heartbeat_recording_and_liveness(self) -> None:
        self.supervisor.register_subsystem("storage_engine")
        ok = self.supervisor.record_heartbeat("storage_engine")
        self.assertTrue(ok)
        self.assertEqual(self.supervisor.subsystems["storage_engine"].consecutive_failures, 0)

    def test_watchdog_timeout_detection(self) -> None:
        self.supervisor.register_subsystem("consensus_raft")
        # Simulate time passing 5 seconds in future (> 2.0s heartbeat_timeout)
        future_time = self.supervisor.subsystems["consensus_raft"].last_heartbeat + 5.0
        timed_out = self.supervisor.check_watchdogs(current_time=future_time)

        self.assertIn("consensus_raft", timed_out)
        self.assertEqual(len(self.supervisor.incidents), 1)
        self.assertEqual(self.supervisor.incidents[0].fault_type, "TIMEOUT")

    def test_fault_injection_clean_restart(self) -> None:
        self.supervisor.register_subsystem("jit_worker", RecoveryStrategy.RESTART_CLEAN, {"cache": "warm"})
        inc = self.supervisor.inject_fault("jit_worker", "CRASH")

        self.assertTrue(inc.recovery_successful)
        self.assertEqual(self.supervisor.subsystems["jit_worker"].health, SubsystemHealth.HEALTHY)
        self.assertEqual(self.supervisor.subsystems["jit_worker"].state, {})  # clean restart

    def test_fault_injection_rollback_checkpoint(self) -> None:
        self.supervisor.register_subsystem("kv_engine", RecoveryStrategy.ROLLBACK_CHECKPOINT, {"val": 10})
        # Save validated snapshot
        self.supervisor.save_checkpoint("kv_engine", lsn=42, state={"val": 100, "sealed": True})
        # Corrupt state
        self.supervisor.subsystems["kv_engine"].state["val"] = 9999

        # Inject memory corruption
        inc = self.supervisor.inject_fault("kv_engine", "CORRUPTION")
        self.assertTrue(inc.recovery_successful)
        # Verify rollback to checkpoint
        self.assertEqual(self.supervisor.subsystems["kv_engine"].state["val"], 100)
        self.assertTrue(self.supervisor.subsystems["kv_engine"].state["sealed"])

    def test_fault_injection_drain_and_reinitialize(self) -> None:
        self.supervisor.register_subsystem("ring_buffer", RecoveryStrategy.DRAIN_AND_REINITIALIZE, {"pending": [10, 20]})
        inc = self.supervisor.inject_fault("ring_buffer", "OOM")

        self.assertTrue(inc.recovery_successful)
        self.assertEqual(self.supervisor.subsystems["ring_buffer"].state, {})

    def test_circuit_breaker_tripping(self) -> None:
        self.supervisor.register_subsystem("unstable_proc", RecoveryStrategy.RESTART_CLEAN)
        # Circuit threshold = 3 failures
        self.supervisor.inject_fault("unstable_proc", "FAIL_1")
        self.supervisor.inject_fault("unstable_proc", "FAIL_2")
        self.supervisor.inject_fault("unstable_proc", "FAIL_3")

        desc = self.supervisor.subsystems["unstable_proc"]
        self.assertEqual(desc.health, SubsystemHealth.CIRCUIT_TRIPPED)
        self.assertEqual(desc.consecutive_failures, 3)

    def test_circuit_breaker_manual_reset(self) -> None:
        self.supervisor.register_subsystem("flapping_net")
        for _ in range(3):
            self.supervisor.inject_fault("flapping_net", "DISCONNECT")
        self.assertEqual(self.supervisor.subsystems["flapping_net"].health, SubsystemHealth.CIRCUIT_TRIPPED)

        # Reset circuit breaker
        ok = self.supervisor.reset_circuit_breaker("flapping_net")
        self.assertTrue(ok)
        self.assertEqual(self.supervisor.subsystems["flapping_net"].health, SubsystemHealth.HEALTHY)
        self.assertEqual(self.supervisor.subsystems["flapping_net"].consecutive_failures, 0)

    def test_incident_logging_metrics(self) -> None:
        self.supervisor.register_subsystem("db_router")
        self.supervisor.inject_fault("db_router", "DEADLOCK")

        self.assertEqual(len(self.supervisor.incidents), 1)
        inc = self.supervisor.incidents[0]
        self.assertEqual(inc.subsystem_name, "db_router")
        self.assertEqual(inc.fault_type, "DEADLOCK")
        self.assertGreaterEqual(inc.recovery_duration_ms, 0.0)

    def test_fabric_status_and_ascii_table(self) -> None:
        self.supervisor.register_subsystem("sentinel_core")
        stat = self.supervisor.status()
        self.assertEqual(stat["subsystems_count"], 1)

        tbl = self.supervisor.format_ascii_status()
        self.assertIn("STAGE 192: KERNEL SELF-HEALING & CRASH RECOVERY SUPERVISOR", tbl)
        self.assertIn("sentinel_core", tbl)


if __name__ == "__main__":
    unittest.main()
