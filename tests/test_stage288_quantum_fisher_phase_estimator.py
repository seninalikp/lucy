"""
Unit Tests for Stage 288: Quantum Optic Mach-Zehnder Non-Linear Phase Estimator & Quantum Fisher Information Engine
Sovereign Architect: Senin (Senin Ali K P)
"""

import unittest
import threading
import math
from backend.lucy_core.quantum_fisher_phase_estimator import (
    QuantumFisherPhaseEstimatorFabric,
    STAGE,
    STAGE_NAME,
    SOVEREIGN_OPERATOR,
)


class TestStage288QuantumFisherPhaseEstimator(unittest.TestCase):

    def setUp(self):
        self.fabric = QuantumFisherPhaseEstimatorFabric()

    def test_01_initialization_and_metadata(self):
        st = self.fabric.status()
        self.assertEqual(st["stage"], 288)
        self.assertEqual(st["stage_name"], STAGE_NAME)
        self.assertEqual(st["sovereign_operator"], SOVEREIGN_OPERATOR)
        self.assertEqual(st["evaluations_count"], 0)
        self.assertIsNone(st["last_snapshot"])

    def test_02_coherent_state_standard_quantum_limit(self):
        # N = 100 coherent state -> F_Q = 100, Delta_phi = 1/sqrt(100) = 0.1 rad
        res = self.fabric.calculate_quantum_fisher_info(mean_photons=100.0, state_type="COHERENT")
        self.assertEqual(res["state_type"], "COHERENT_SQL")
        self.assertAlmostEqual(res["quantum_fisher_info"], 100.0, places=4)
        self.assertAlmostEqual(res["cramer_rao_bound_radians"], 0.1, places=4)
        self.assertAlmostEqual(res["quantum_advantage_ratio"], 1.0, places=4)

    def test_03_noon_state_heisenberg_limit(self):
        # N = 100 N00N state -> F_Q = 10000, Delta_phi = 1/100 = 0.01 rad
        res = self.fabric.calculate_quantum_fisher_info(mean_photons=100.0, state_type="N00N")
        self.assertEqual(res["state_type"], "N00N_HEISENBERG")
        self.assertAlmostEqual(res["quantum_fisher_info"], 10000.0, places=4)
        self.assertAlmostEqual(res["cramer_rao_bound_radians"], 0.01, places=4)
        self.assertAlmostEqual(res["heisenberg_limit"], 0.01, places=4)

    def test_04_quantum_advantage_ratio_scaling(self):
        # Advantage of N00N over SQL is sqrt(N) = sqrt(64) = 8.0
        res = self.fabric.calculate_quantum_fisher_info(mean_photons=64.0, state_type="N00N")
        self.assertAlmostEqual(res["quantum_advantage_ratio"], 8.0, places=4)

    def test_05_squeezed_vacuum_enhancement(self):
        # Squeezed vacuum with r = 1.0 -> F_Q = N * exp(2)
        n = 50.0
        r = 1.0
        res = self.fabric.calculate_quantum_fisher_info(mean_photons=n, state_type="SQUEEZED", squeezing_r=r)
        expected_fq = n * math.exp(2.0 * r)
        self.assertAlmostEqual(res["quantum_fisher_info"], expected_fq, places=3)
        self.assertGreater(res["quantum_advantage_ratio"], math.exp(r) - 0.01)

    def test_06_kerr_nonlinear_super_heisenberg_scaling(self):
        # Kerr non-linear F_Q = N^4 * chi^2 -> Doubling N increases F_Q by 16x
        res1 = self.fabric.calculate_quantum_fisher_info(mean_photons=10.0, state_type="KERR", kerr_chi=0.1)
        res2 = self.fabric.calculate_quantum_fisher_info(mean_photons=20.0, state_type="KERR", kerr_chi=0.1)
        ratio = res2["quantum_fisher_info"] / res1["quantum_fisher_info"]
        self.assertAlmostEqual(ratio, 16.0, places=3)

    def test_07_classical_mach_zehnder_fringes(self):
        sim = self.fabric.simulate_mach_zehnder_fringes(true_phase_rad=0.0, n_photons=10, state_type="COHERENT")
        self.assertEqual(sim["state_type"], "CLASSICAL_MACH_ZEHNDER")
        self.assertAlmostEqual(sim["transmission_at_true_phase"], 1.0, places=4)

    def test_08_noon_state_super_resolution(self):
        # N00N state with N=4 has transmission cos^2(4 * phi / 2) = cos^2(2*phi)
        # At phi = pi/4: cos^2(pi/2) = 0.0
        sim = self.fabric.simulate_mach_zehnder_fringes(true_phase_rad=math.pi / 4.0, n_photons=4, state_type="N00N")
        self.assertEqual(sim["state_type"], "N00N_SUPER_RESOLUTION")
        self.assertEqual(sim["fringe_finesse_multiplier"], 4.0)
        self.assertAlmostEqual(sim["transmission_at_true_phase"], 0.0, places=4)

    def test_09_multithreaded_concurrency(self):
        def worker(idx):
            self.fabric.calculate_quantum_fisher_info(mean_photons=10.0 * (idx + 1))
            self.fabric.simulate_mach_zehnder_fringes(n_photons=idx + 2)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        st = self.fabric.status()
        self.assertEqual(st["evaluations_count"], 10)
        self.assertEqual(st["history_length"], 10)

    def test_10_ascii_formatting_and_cp1252_encoding(self):
        self.fabric.calculate_quantum_fisher_info(mean_photons=256.0, state_type="N00N")
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 288", tbl)
        self.assertIn("Senin (Senin Ali K P)", tbl)
        self.assertIn("Cramer-Rao Bound", tbl)
        encoded = tbl.encode("cp1252")
        self.assertIsInstance(encoded, bytes)


if __name__ == "__main__":
    unittest.main()
