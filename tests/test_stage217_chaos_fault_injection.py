r"""
tests/test_stage217_chaos_fault_injection.py
Stage 217: Autonomous Dynamic Fault-Injection & Chaos Mesh Resilience Engine
Era 22: Autonomous Galactic Hyper-Mesh, Hardware-Accelerated Photonic Emulation & Trans-Universal Reasoning Fabrics
"""

import unittest
from backend.lucy_core.chaos_fault_injection import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    ChaosExperiment,
    ChaosFaultInjectionFabric,
    FaultType,
)


class TestStage217ChaosFaultInjection(unittest.TestCase):
    """10 Unit Tests for Stage 217 Chaos Fault Injection Fabric."""

    def setUp(self):
        self.fabric = ChaosFaultInjectionFabric()

    def test_01_fabric_initialization(self):
        self.assertEqual(STAGE, 217)
        self.assertEqual(ERA, 22)
        self.assertEqual(self.fabric.faults_injected, 0)
        self.assertEqual(self.fabric.recoveries_count, 0)
        self.assertEqual(len(self.fabric.experiments), 0)
        self.assertEqual(self.fabric.status()["stage"], 217)

    def test_02_register_health_predicate(self):
        self.fabric.register_health_predicate("subsystem_alpha", lambda: True)
        self.assertTrue(self.fabric.verify_steady_state("subsystem_alpha"))

        self.fabric.register_health_predicate("subsystem_beta", lambda: False)
        self.assertFalse(self.fabric.verify_steady_state("subsystem_beta"))

    def test_03_inject_fault_latency_spike(self):
        exp = self.fabric.inject_fault(FaultType.LATENCY_SPIKE, "ipc_shm_channel", intensity=0.8, duration_ms=250.0)
        self.assertIsNotNone(exp)
        self.assertEqual(exp.fault_type, FaultType.LATENCY_SPIKE)
        self.assertEqual(exp.target_subsystem, "ipc_shm_channel")
        self.assertTrue(exp.active)
        self.assertEqual(self.fabric.faults_injected, 1)

    def test_04_intensity_clamping(self):
        e1 = self.fabric.inject_fault(FaultType.PACKET_CORRUPTION, "modem", intensity=-0.5)
        self.assertEqual(e1.intensity, 0.0)

        e2 = self.fabric.inject_fault(FaultType.RESOURCE_STARVATION, "modem", intensity=1.5)
        self.assertEqual(e2.intensity, 1.0)

    def test_05_resolve_fault_healthy_recovery(self):
        self.fabric.register_health_predicate("cluster_node_1", lambda: True)
        exp = self.fabric.inject_fault(FaultType.THREAD_CRASH, "cluster_node_1")
        ok = self.fabric.resolve_fault(exp.experiment_id)
        self.assertTrue(ok)
        self.assertFalse(exp.active)
        self.assertTrue(exp.recovered)
        self.assertEqual(self.fabric.recoveries_count, 1)

    def test_06_resolve_fault_failed_recovery(self):
        self.fabric.register_health_predicate("faulty_service", lambda: False)
        exp = self.fabric.inject_fault(FaultType.NETWORK_PARTITION, "faulty_service")
        ok = self.fabric.resolve_fault(exp.experiment_id)
        self.assertFalse(ok)
        self.assertFalse(exp.recovered)
        self.assertEqual(self.fabric.recoveries_count, 0)

    def test_07_resolve_nonexistent_or_inactive_fault(self):
        self.assertFalse(self.fabric.resolve_fault("non_existent_chaos_id"))

        exp = self.fabric.inject_fault(FaultType.LATENCY_SPIKE, "target")
        self.fabric.resolve_fault(exp.experiment_id)
        # Attempting to resolve already resolved fault
        self.assertFalse(self.fabric.resolve_fault(exp.experiment_id))

    def test_08_run_chaos_campaign_multi_target(self):
        targets = ["router", "storage"]
        # Both healthy
        self.fabric.register_health_predicate("router", lambda: True)
        self.fabric.register_health_predicate("storage", lambda: True)

        res = self.fabric.run_chaos_campaign(targets)
        self.assertEqual(res["total_experiments"], 6)  # 3 faults * 2 targets
        self.assertEqual(res["success_ratio"], 1.0)
        self.assertEqual(res["resilience_score"], "100%")

    def test_09_resilience_index_metric(self):
        self.fabric.register_health_predicate("resilient_worker", lambda: True)
        for i in range(4):
            e = self.fabric.inject_fault(FaultType.LATENCY_SPIKE, "resilient_worker")
            self.fabric.resolve_fault(e.experiment_id)

        s = self.fabric.status()
        self.assertEqual(s["faults_injected"], 4)
        self.assertEqual(s["recoveries_count"], 4)
        self.assertEqual(s["resilience_index"], 1.0)

    def test_10_ascii_status_formatting(self):
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 217: DYNAMIC FAULT-INJECTION & CHAOS RESILIENCE ENGINE", tbl)
        self.assertIn("Chaos Resilience Index", tbl)
        self.assertIn("Anti-Fragile Self-Healing", tbl)


if __name__ == "__main__":
    unittest.main()
