"""
Unit Tests for Stage 295: Cosmic String Network Evolution & Gravitational Wave Burst Engine
Sovereign Architect: Senin (Senin Ali K P)
"""

import math
import threading
import unittest
from backend.lucy_core.cosmic_string_network_evolution import (
    CosmicStringNetworkEvolutionFabric,
    STAGE,
    STAGE_NAME,
    SOVEREIGN_OPERATOR,
)


class TestStage295CosmicStringNetworkEvolution(unittest.TestCase):

    def setUp(self):
        self.fabric = CosmicStringNetworkEvolutionFabric(tension_gmu=1.0e-10, p_intercommute=1.0)

    def test_01_initialization_and_metadata(self):
        st = self.fabric.status()
        self.assertEqual(st["stage"], 295)
        self.assertEqual(st["stage_name"], STAGE_NAME)
        self.assertEqual(st["sovereign_operator"], SOVEREIGN_OPERATOR)
        self.assertEqual(st["dimensionless_tension_gmu"], 1.0e-10)
        self.assertEqual(st["intercommutation_probability_P"], 1.0)
        self.assertEqual(st["status"], "OPERATIONAL")

    def test_02_linear_scaling_horizon_growth(self):
        # xi(t) grows linearly with cosmic time t
        t1 = 1.0e5
        t2 = 2.0e5
        xi1 = self.fabric.compute_scaling_length(t1)
        xi2 = self.fabric.compute_scaling_length(t2)
        self.assertAlmostEqual(xi2 / xi1, 2.0, places=6)

    def test_03_density_inverse_square_time_decay(self):
        # rho proportional to 1 / t^2 in scaling regime
        t1 = 1.0e6
        t2 = 3.0e6
        rho1 = self.fabric.compute_string_density(t1)
        rho2 = self.fabric.compute_string_density(t2)
        self.assertAlmostEqual(rho1 / rho2, 9.0, places=4)

    def test_04_universal_loop_gw_emission_power(self):
        # P_GW is independent of loop length L
        p1 = self.fabric.compute_cusp_power(loop_length_m=1.0e10)
        p2 = self.fabric.compute_cusp_power(loop_length_m=5.0e14)
        self.assertAlmostEqual(p1, p2, places=6)
        self.assertGreater(p1, 0.0)

    def test_05_gw_power_quadratic_tension_scaling(self):
        # P_GW is proportional to (G*mu)^2
        f1 = CosmicStringNetworkEvolutionFabric(tension_gmu=1.0e-10)
        f2 = CosmicStringNetworkEvolutionFabric(tension_gmu=2.0e-10)
        p1 = f1.compute_cusp_power(1.0e12)
        p2 = f2.compute_cusp_power(1.0e12)
        self.assertAlmostEqual(p2 / p1, 4.0, places=4)

    def test_06_stochastic_gw_plateau_scaling(self):
        # Omega_GW proportional to sqrt(G*mu)
        f1 = CosmicStringNetworkEvolutionFabric(tension_gmu=1.0e-10)
        f2 = CosmicStringNetworkEvolutionFabric(tension_gmu=4.0e-10)
        om1 = f1.compute_stochastic_gw_plateau()
        om2 = f2.compute_stochastic_gw_plateau()
        self.assertAlmostEqual(om2 / om1, 2.0, places=5)

    def test_07_full_network_state_evaluation(self):
        metrics = self.fabric.evaluate_network_state(cosmic_time_s=1.0e10)
        self.assertTrue(metrics.is_in_scaling_regime)
        self.assertGreater(metrics.characteristic_length_scale_m, 1e17)
        self.assertGreater(metrics.stochastic_gw_plateau_omega, 0.0)

    def test_08_invalid_parameters_raise(self):
        with self.assertRaises(ValueError):
            CosmicStringNetworkEvolutionFabric(tension_gmu=-1.0e-10)
        with self.assertRaises(ValueError):
            CosmicStringNetworkEvolutionFabric(p_intercommute=1.5)

    def test_09_multithreaded_concurrency(self):
        results = []

        def worker():
            m = self.fabric.evaluate_network_state(1.0e8)
            results.append(m.characteristic_length_scale_m)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), 10)
        self.assertTrue(all(r > 0 for r in results))

    def test_10_invalid_loop_length_raises(self):
        with self.assertRaises(ValueError):
            self.fabric.compute_cusp_power(-10.0)


if __name__ == "__main__":
    unittest.main()
