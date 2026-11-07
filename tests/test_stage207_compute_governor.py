r"""
tests/test_stage207_compute_governor.py
Stage 207: Autonomous Latency-Adaptive Compute Governor & Dynamic Frequency Scaler
Era 21: Autonomous Hyper-Scale Multi-Kernel Federation, Quantum-Resistant Keys & Post-Singularity Architecture
"""

import unittest
from backend.lucy_core.compute_governor import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    GovernorProfile,
    TaskPriority,
    ScheduledTask,
    ComputeGovernorFabric,
)


class TestStage207ComputeGovernor(unittest.TestCase):
    """10 Unit Tests for Stage 207 Compute Governor Fabric."""

    def setUp(self):
        self.fabric = ComputeGovernorFabric(sla_target_ms=50.0)

    def test_01_fabric_initialization(self):
        self.assertEqual(self.fabric.profile, GovernorProfile.BALANCED)
        self.assertEqual(self.fabric.sla_target_ms, 50.0)
        self.assertEqual(self.fabric.status()["stage"], 207)
        self.assertEqual(self.fabric.status()["era"], 21)

    def test_02_record_latency_and_quantiles(self):
        for val in range(1, 101):
            self.fabric.record_latency(float(val))
        q = self.fabric.compute_quantiles()
        self.assertEqual(q["p50"], 51.0)
        self.assertAlmostEqual(q["p95"], 95.0, delta=2.0)
        self.assertAlmostEqual(q["p99"], 99.0, delta=2.0)

    def test_03_dynamic_scale_up_to_turbo(self):
        # Inject high latency exceeding 50ms SLA target
        prof = self.fabric.record_latency(75.0)
        self.assertEqual(prof, GovernorProfile.TURBO)
        self.assertEqual(self.fabric.profile, GovernorProfile.TURBO)

    def test_04_dynamic_scale_down_to_powersave(self):
        # Inject 30 low latency samples (< 20ms)
        for _ in range(30):
            prof = self.fabric.record_latency(5.0)
        self.assertEqual(prof, GovernorProfile.POWERSAVE)
        self.assertEqual(self.fabric.profile, GovernorProfile.POWERSAVE)

    def test_05_execute_task_wrapper(self):
        def sample_compute():
            return sum(x * x for x in range(100))

        res, task = self.fabric.execute_task("sample_task", TaskPriority.HIGH, sample_compute)
        self.assertEqual(res, 328350)
        self.assertEqual(task.name, "sample_task")
        self.assertEqual(task.priority, TaskPriority.HIGH)
        self.assertEqual(task.status, "COMPLETED")
        self.assertGreaterEqual(task.latency_ms, 0.0)

    def test_06_priority_enumeration_values(self):
        self.assertLess(TaskPriority.CRITICAL, TaskPriority.HIGH)
        self.assertLess(TaskPriority.HIGH, TaskPriority.NORMAL)
        self.assertLess(TaskPriority.NORMAL, TaskPriority.BACKGROUND)

    def test_07_profile_shift_counter(self):
        self.assertEqual(self.fabric._profile_transitions_count, 0)
        # Shift to TURBO
        self.fabric.record_latency(100.0)
        self.assertGreaterEqual(self.fabric._profile_transitions_count, 1)

    def test_08_sliding_window_maxlen(self):
        for i in range(150):
            self.fabric.record_latency(float(i))
        self.assertEqual(len(self.fabric.latencies), 100)

    def test_09_task_serialization(self):
        task = ScheduledTask(
            task_id="T1",
            name="test_serialization",
            priority=TaskPriority.CRITICAL,
            latency_ms=12.5,
        )
        d = task.to_dict()
        self.assertEqual(d["task_id"], "T1")
        self.assertEqual(d["priority"], "CRITICAL")
        self.assertEqual(d["latency_ms"], 12.5)

    def test_10_ascii_status_and_metadata(self):
        ascii_out = self.fabric.format_ascii_status()
        self.assertIn("STAGE 207: LATENCY-ADAPTIVE COMPUTE GOVERNOR & SCALER", ascii_out)
        self.assertIn("Latency SLA Target    : < 50.0 ms", ascii_out)
        self.assertIn("Era 21 (Post-Singularity Compute Governor)", ascii_out)


if __name__ == "__main__":
    unittest.main()
