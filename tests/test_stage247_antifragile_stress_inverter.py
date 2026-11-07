"""
Unit Tests for Stage 247: Sovereign Anti-Fragile Black-Swan Catastrophe Immunity & Systemic Stress Inversion Engine
Era 25: Omni-Dimensional Super-Intelligence Matrix, Astro-Cognitive Planetary Orchestration & Sovereign Trans-Singularity Metamaterials

Sovereign Human Operator: Senin (Senin Ali K P)
"""

import unittest
import threading
import time

from backend.lucy_core.antifragile_stress_inverter import (
    AntiFragileStressInverterFabric,
    FragilityRegime,
    get_antifragile_inverter,
    STAGE,
    ERA,
)


class TestStage247AntiFragileStressInverter(unittest.TestCase):

    def setUp(self):
        self.fabric = AntiFragileStressInverterFabric(
            base_capacity=100.0,
            convexity_alpha=0.3,
            convexity_gamma=1.5,
            stress_threshold=0.1,
        )

    def test_01_singleton_and_initialization(self):
        inverter = get_antifragile_inverter()
        self.assertIsNotNone(inverter)
        self.assertEqual(STAGE, 247)
        self.assertEqual(ERA, 25)
        self.assertEqual(self.fabric.base_capacity, 100.0)
        self.assertEqual(self.fabric.current_capacity, 100.0)
        self.assertEqual(self.fabric.cumulative_convex_gain, 0.0)

    def test_02_convex_payoff_evaluation(self):
        # Stress = 0 should return base capacity with ROBUST regime
        v0, regime0 = self.fabric.calculate_payoff(100.0, 0.0)
        self.assertEqual(v0, 100.0)
        self.assertEqual(regime0, FragilityRegime.ROBUST)

        # Non-zero stress should trigger ANTIFRAGILE gain
        v1, regime1 = self.fabric.calculate_payoff(100.0, 0.5)
        v2, regime2 = self.fabric.calculate_payoff(100.0, 1.0)
        self.assertEqual(regime1, FragilityRegime.ANTIFRAGILE)
        self.assertEqual(regime2, FragilityRegime.ANTIFRAGILE)
        self.assertGreater(v1, 100.0)
        self.assertGreater(v2, v1)

    def test_03_taleb_second_derivative_convexity(self):
        # Numerically verify d^2 V / d sigma^2 > 0
        conv_res = self.fabric.evaluate_convexity(100.0, [0.05, 0.1, 0.2, 0.5])
        self.assertTrue(conv_res["strictly_convex"])
        self.assertEqual(conv_res["regime"], "ANTIFRAGILE")
        for ev in conv_res["evaluations"]:
            self.assertGreater(ev["second_derivative"], 0.0)
            self.assertTrue(ev["is_convex"])

    def test_04_jensen_inequality_holds(self):
        # Samples with volatility
        shocks = [0.1, 0.8, 0.2, 1.5, 0.05, 2.0]
        jensen_res = self.fabric.verify_jensen_inequality(100.0, shocks)
        self.assertTrue(jensen_res["jensens_inequality_holds"])
        self.assertGreaterEqual(jensen_res["jensen_convexity_gap"], 0.0)
        self.assertGreater(jensen_res["expected_of_payoff"], jensen_res["payoff_of_expected"])

    def test_05_inject_stress_and_capacity_upgrade(self):
        res = self.fabric.inject_stress(
            stressor_type="network_partition_latency",
            magnitude=0.75,
            duration=2.5,
            metadata={"source": "byzantine_drop"}
        )
        self.assertIn("STRESS-", res["stress_id"])
        self.assertEqual(res["stressor_type"], "network_partition_latency")
        self.assertGreater(res["convex_gain"], 0.0)
        self.assertGreater(res["new_capacity"], 100.0)
        self.assertEqual(self.fabric.total_stressors_absorbed, 1)
        self.assertEqual(len(self.fabric.stress_history), 1)

    def test_06_barbell_allocation_core_and_periphery(self):
        alloc = self.fabric.apply_barbell_allocation(total_resources=1000.0, conservative_ratio=0.90)
        self.assertEqual(alloc.total_resources, 1000.0)
        self.assertAlmostEqual(alloc.conservative_core, 900.0)
        self.assertAlmostEqual(alloc.exploratory_convex_periphery, 100.0)
        self.assertEqual(alloc.conservative_ratio, 0.90)
        self.assertAlmostEqual(alloc.periphery_ratio, 0.10)

    def test_07_black_swan_kurtosis_detection(self):
        # Normal small shocks
        normal_shocks = [0.05, 0.06, 0.04, 0.05, 0.055, 0.045]
        normal_eval = self.fabric.detect_black_swan(normal_shocks)
        self.assertFalse(normal_eval["is_black_swan_regime"])

        # Inject extreme fat-tail black swan shock
        tail_shocks = [0.05, 0.04, 0.05, 0.06, 0.045, 10.0]
        swan_eval = self.fabric.detect_black_swan(tail_shocks)
        self.assertTrue(swan_eval["is_black_swan_regime"])
        self.assertGreater(swan_eval["kurtosis"], 3.5)

    def test_08_catastrophe_transmutation(self):
        trans_res = self.fabric.transmute_catastrophe(
            severity=4.5,
            domain="orbital_radiation_storm"
        )
        self.assertEqual(trans_res["status"], "CATASTROPHE_INVERTED_TO_IMMUNITY")
        self.assertGreater(trans_res["transmutation_gain"], 1.0)
        self.assertGreater(trans_res["post_capacity"], trans_res["pre_capacity"])
        self.assertEqual(self.fabric.black_swan_count, 1)

    def test_09_thread_safe_concurrent_stress_injection(self):
        def worker():
            for _ in range(25):
                self.fabric.inject_stress("synthetic_concurrency_perturbation", 0.2)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(self.fabric.total_stressors_absorbed, 100)
        self.assertGreater(self.fabric.current_capacity, 100.0)

    def test_10_ascii_status_and_metrics(self):
        self.fabric.inject_stress("thermal_fluctuation", 0.4)
        ascii_table = self.fabric.format_ascii_status()
        self.assertIn("STAGE 247: Sovereign Anti-Fragile Black-Swan Stress Inverter", ascii_table)
        self.assertIn("Current Capacity", ascii_table)
        self.assertIn("Operating Regime", ascii_table)

        # CP1252 encode verification
        ascii_table.encode("cp1252")

        metrics = self.fabric.get_metrics()
        self.assertEqual(metrics["stage"], 247)
        self.assertEqual(metrics["era"], 25)
        self.assertEqual(metrics["regime"], "ANTIFRAGILE")
        self.assertGreater(metrics["current_capacity"], 100.0)


if __name__ == "__main__":
    unittest.main()
