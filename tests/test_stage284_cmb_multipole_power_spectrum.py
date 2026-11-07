"""
Unit Tests for Stage 284: Cosmic Microwave Background (CMB) Multipole Power Spectrum & Inflationary Tensor Perturbation Engine
Sovereign Architect: Senin (Senin Ali K P)
"""

import unittest
import threading
import math
from backend.lucy_core.cmb_multipole_power_spectrum import (
    CMBMultipolePowerSpectrumFabric,
    STAGE,
    STAGE_NAME,
    SOVEREIGN_OPERATOR,
    FIRST_ACOUSTIC_PEAK_L,
    SECOND_ACOUSTIC_PEAK_L,
)


class TestStage284CMBMultipolePowerSpectrum(unittest.TestCase):

    def setUp(self):
        self.fabric = CMBMultipolePowerSpectrumFabric()

    def test_01_initialization_and_metadata(self):
        st = self.fabric.status()
        self.assertEqual(st["stage"], 284)
        self.assertEqual(st["stage_name"], STAGE_NAME)
        self.assertEqual(st["sovereign_operator"], SOVEREIGN_OPERATOR)
        self.assertEqual(st["evaluations_count"], 0)
        self.assertIsNone(st["last_snapshot"])

    def test_02_sachs_wolfe_plateau_scale(self):
        # At l=10, Sachs-Wolfe plateau is ~ 1000 uK^2
        d_10 = self.fabric.evaluate_multipole_d_l(10)
        self.assertGreater(d_10, 800.0)
        self.assertLess(d_10, 1200.0)

    def test_03_first_acoustic_peak_prominence(self):
        # First acoustic peak at l=220 should dominate the spectrum (D_220 > 4000 uK^2)
        d_peak1 = self.fabric.evaluate_multipole_d_l(int(FIRST_ACOUSTIC_PEAK_L))
        self.assertGreater(d_peak1, 4000.0)
        # Should be much larger than Sachs-Wolfe plateau at l=10
        d_10 = self.fabric.evaluate_multipole_d_l(10)
        self.assertGreater(d_peak1, 3.0 * d_10)

    def test_04_acoustic_peak_hierarchy(self):
        # In Concordance cosmology, peak 1 is significantly higher than peak 2
        d_p1 = self.fabric.evaluate_multipole_d_l(int(FIRST_ACOUSTIC_PEAK_L))
        d_p2 = self.fabric.evaluate_multipole_d_l(int(SECOND_ACOUSTIC_PEAK_L))
        self.assertGreater(d_p1, d_p2)
        self.assertGreater(d_p2, 1000.0)

    def test_05_silk_damping_tail_exponential_suppression(self):
        # High l > 1500 should be strongly attenuated by Silk damping
        d_p1 = self.fabric.evaluate_multipole_d_l(int(FIRST_ACOUSTIC_PEAK_L))
        d_high = self.fabric.evaluate_multipole_d_l(2000)
        self.assertLess(d_high, 0.25 * d_p1)

    def test_06_baryon_density_suppression_of_second_peak(self):
        # Higher baryon density reduces the relative height of the second peak (compression vs rarefaction asymmetry)
        d_p2_low_b = self.fabric.evaluate_multipole_d_l(int(SECOND_ACOUSTIC_PEAK_L), omega_b=0.015)
        d_p2_high_b = self.fabric.evaluate_multipole_d_l(int(SECOND_ACOUSTIC_PEAK_L), omega_b=0.035)
        self.assertGreater(d_p2_low_b, d_p2_high_b)

    def test_07_inflation_energy_scale_quartic_root_scaling(self):
        # V^(1/4) scales as r^(1/4) -> 16-fold increase in r doubles inflation energy scale
        res1 = self.fabric.compute_inflation_tensor_ratio(tensor_to_scalar_r=0.01)
        res2 = self.fabric.compute_inflation_tensor_ratio(tensor_to_scalar_r=0.16)
        ratio = res2["inflation_energy_scale_gev"] / res1["inflation_energy_scale_gev"]
        self.assertAlmostEqual(ratio, 2.0, places=3)

    def test_08_lyth_bound_field_excursion(self):
        # For r = 0.03, N=60: Delta_phi / M_Pl = sqrt(0.03/8) * 60 ~ 3.67 > 1.0 (large field)
        res = self.fabric.compute_inflation_tensor_ratio(tensor_to_scalar_r=0.03, e_folds=60.0)
        expected_lyth = math.sqrt(0.03 / 8.0) * 60.0
        self.assertAlmostEqual(res["lyth_bound_delta_phi_planck"], expected_lyth, places=3)
        self.assertTrue(res["is_large_field_inflation"])
        self.assertTrue(res["primordial_gw_detectable"])

    def test_09_multithreaded_concurrency(self):
        def worker(idx):
            self.fabric.compute_multipole_spectrum(l_max=500 + idx * 50)
            self.fabric.compute_inflation_tensor_ratio(tensor_to_scalar_r=0.01 * (idx + 1))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        st = self.fabric.status()
        self.assertEqual(st["evaluations_count"], 10)
        self.assertEqual(st["history_length"], 10)

    def test_10_ascii_formatting_and_cp1252_encoding(self):
        self.fabric.compute_inflation_tensor_ratio(tensor_to_scalar_r=0.05)
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 284", tbl)
        self.assertIn("Senin (Senin Ali K P)", tbl)
        self.assertIn("Peak 1 (l=220)", tbl)
        encoded = tbl.encode("cp1252")
        self.assertIsInstance(encoded, bytes)


if __name__ == "__main__":
    unittest.main()
