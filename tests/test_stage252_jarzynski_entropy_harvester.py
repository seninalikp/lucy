"""
Unit Tests for Stage 252: Non-Equilibrium Fluctuation-Dissipation & Crooks Jarzynski Entropy Harvester
Era 26: Cosmic-Scale Holomorphic Field Dynamics, Non-Equilibrium Thermodynamic Entropy Engines & Autonomous Sovereign Multi-Verse Orchestration

Sovereign Human Operator: Senin (Senin Ali K P)
"""

import math
import threading
import unittest
from backend.lucy_core.jarzynski_entropy_harvester import (
    JarzynskiEntropyHarvesterFabric,
    get_jarzynski_harvester,
    K_BOLTZMANN,
    STAGE,
    ERA,
)


class TestStage252JarzynskiEntropyHarvester(unittest.TestCase):

    def setUp(self):
        self.fabric = JarzynskiEntropyHarvesterFabric(temperature_k=300.0)

    def test_01_singleton_and_initialization(self):
        singleton = get_jarzynski_harvester()
        self.assertIsNotNone(singleton)
        self.assertEqual(STAGE, 252)
        self.assertEqual(ERA, 26)
        self.assertEqual(self.fabric.temperature_k, 300.0)
        self.assertAlmostEqual(self.fabric.thermal_energy_joules, 300.0 * K_BOLTZMANN)

    def test_02_jarzynski_equality_single_value(self):
        # If work is constant w = 4.0, Delta f must equal exactly 4.0
        res = self.fabric.compute_jarzynski_free_energy([4.0] * 50)
        self.assertAlmostEqual(res["delta_f_kbt"], 4.0)
        self.assertAlmostEqual(res["dissipated_work_kbt"], 0.0)
        self.assertTrue(res["second_law_holds"])

    def test_03_jarzynski_recovers_known_free_energy(self):
        # Generate ensemble with true Delta F = 5.0 k_B T, dissipation = 1.0 k_B T
        fwd, rev = self.fabric.generate_synthetic_work_ensemble(
            true_delta_f=5.0,
            dissipation=1.0,
            samples=1000,
            seed=123
        )
        res = self.fabric.compute_jarzynski_free_energy(fwd)
        # Jarzynski estimate should be close to 5.0
        self.assertAlmostEqual(res["delta_f_kbt"], 5.0, delta=0.2)
        self.assertGreater(res["mean_work_kbt"], res["delta_f_kbt"])

    def test_04_second_law_jensen_dissipation(self):
        work_samples = [2.0, 3.5, 4.0, 5.2, 6.1]
        res = self.fabric.compute_jarzynski_free_energy(work_samples)
        self.assertTrue(res["second_law_holds"])
        self.assertGreaterEqual(res["dissipated_work_kbt"], 0.0)

    def test_05_empty_ensemble_rejection(self):
        with self.assertRaises(ValueError):
            self.fabric.compute_jarzynski_free_energy([])

    def test_06_crooks_crossing_verification(self):
        fwd, rev = self.fabric.generate_synthetic_work_ensemble(
            true_delta_f=4.0,
            dissipation=1.5,
            samples=800,
            seed=999
        )
        crooks_res = self.fabric.verify_crooks_crossing(fwd, rev)
        self.assertTrue(crooks_res["crossing_verified"])
        self.assertLess(crooks_res["discrepancy"], 0.5)

    def test_07_harvest_stochastic_fluctuation_negative_dissipation(self):
        # Fluctuation where w = 2.0 while Delta F = 3.0 -> negative entropy production
        h_res = self.fabric.harvest_stochastic_fluctuation(
            work_kbt=2.0,
            delta_f_kbt=3.0,
            mutual_info_bits=2.0
        )
        self.assertIn("HARVEST-", h_res["event_id"])
        self.assertLess(h_res["entropy_production_kbt"], 0.0)
        self.assertGreater(h_res["harvested_joules"], 0.0)
        self.assertEqual(len(self.fabric.harvest_events), 1)

    def test_08_harvest_bound_by_szilard_limit(self):
        # Huge fluctuation, bounded by mutual info
        h_res = self.fabric.harvest_stochastic_fluctuation(
            work_kbt=-50.0,
            delta_f_kbt=10.0,
            mutual_info_bits=1.0
        )
        max_allowed = self.fabric.thermal_energy_joules * math.log(2.0) * 1.0
        self.assertLessEqual(h_res["harvested_joules"], max_allowed + 1e-30)

    def test_09_thread_safe_concurrent_harvesting(self):
        def worker():
            for _ in range(25):
                self.fabric.harvest_stochastic_fluctuation(1.5, 2.0, 1.0)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(self.fabric.harvest_events), 100)
        self.assertGreater(self.fabric.total_joules_harvested, 0.0)

    def test_10_ascii_status_and_metrics(self):
        self.fabric.harvest_stochastic_fluctuation(1.0, 2.0, 1.0)
        ascii_table = self.fabric.format_ascii_status()
        self.assertIn("STAGE 252: Crooks-Jarzynski Non-Equilibrium Entropy Harvester", ascii_table)
        self.assertIn("Operating Temp", ascii_table)
        self.assertIn("Harvested Energy", ascii_table)

        # CP1252 verification
        ascii_table.encode("cp1252")

        metrics = self.fabric.get_metrics()
        self.assertEqual(metrics["stage"], 252)
        self.assertEqual(metrics["era"], 26)
        self.assertEqual(metrics["temperature_k"], 300.0)
        self.assertGreater(metrics["total_joules_harvested"], 0.0)


if __name__ == "__main__":
    unittest.main()
