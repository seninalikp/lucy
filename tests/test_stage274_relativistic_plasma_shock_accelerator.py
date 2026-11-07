"""
Unit Tests for Stage 274: Relativistic Plasma Shock Magnetosonic Wave Accelerator & Fermi Cosmic-Ray Compressor
Author & Permanent Sovereign Operator: Senin (Senin Ali K P)
"""

import unittest
import threading
from backend.lucy_core.relativistic_plasma_shock_accelerator import (
    RelativisticPlasmaShockAccelerator,
    SOVEREIGN_OPERATOR,
    SOVEREIGN_LEGAL_NAME,
    STAGE_ID,
    STAGE_NAME,
    ERA_ID
)


class TestStage274RelativisticPlasmaShockAccelerator(unittest.TestCase):
    """Thorough unit test suite for Stage 274."""

    def setUp(self):
        self.accel = RelativisticPlasmaShockAccelerator(shock_speed_c=0.1, adiabatic_index=5.0 / 3.0)

    def test_01_initialization(self):
        """Verify initialization constants and physical parameters."""
        self.assertEqual(self.accel.beta_shock, 0.1)
        self.assertAlmostEqual(self.accel.gamma_ad, 5.0 / 3.0, places=4)
        self.assertEqual(len(self.accel.shock_acceleration_events), 0)

    def test_02_strong_shock_compression_limit(self):
        """Verify strong shock compression ratio approaches r_max = 4.0 for gamma = 5/3."""
        jumps = self.accel.compute_shock_jump_conditions(mach_number=100.0)
        self.assertAlmostEqual(jumps["compression_ratio_r"], 4.0, places=2)
        self.assertEqual(jumps["asymptotic_r_max"], 4.0)

    def test_03_relativistic_adiabatic_index_limit(self):
        """Verify strong shock compression ratio approaches r_max = 7.0 for ultra-relativistic gas (gamma = 4/3)."""
        rel_accel = RelativisticPlasmaShockAccelerator(shock_speed_c=0.5, adiabatic_index=4.0 / 3.0)
        jumps = rel_accel.compute_shock_jump_conditions(mach_number=100.0)
        self.assertAlmostEqual(jumps["compression_ratio_r"], 7.0, places=2)
        self.assertEqual(jumps["asymptotic_r_max"], 7.0)

    def test_04_magnetic_compression(self):
        """Verify magnetic field compression across shock: B_2 = r * B_1."""
        jumps = self.accel.compute_shock_jump_conditions(mach_number=20.0)
        r = jumps["compression_ratio_r"]
        ratio = jumps["downstream_b_tesla"] / jumps["upstream_b_tesla"]
        self.assertAlmostEqual(ratio, r, places=4)

    def test_05_fermi_spectral_index_strong_shock(self):
        """Verify universal power-law index p = (r+2)/(r-1) ~ 2.0 for strong shock."""
        res = self.accel.compute_fermi_acceleration_spectrum(mach_number=100.0, initial_energy_gev=1.0)
        self.assertAlmostEqual(res["spectral_index_p"], 2.0, places=2)

    def test_06_diffusive_energy_amplification(self):
        """Verify multi-cycle diffusive acceleration increases particle energy."""
        res10 = self.accel.compute_fermi_acceleration_spectrum(mach_number=20.0, initial_energy_gev=1.0, num_cycles=10)
        res50 = self.accel.compute_fermi_acceleration_spectrum(mach_number=20.0, initial_energy_gev=1.0, num_cycles=50)
        self.assertGreater(res50["final_energy_gev"], res10["final_energy_gev"])
        self.assertGreater(res50["energy_amplification_factor"], 1.0)

    def test_07_hillas_maximum_energy_scaling(self):
        """Verify Hillas maximum energy scales linearly with atomic charge Z."""
        hillas_proton = self.accel.compute_hillas_maximum_energy(charge_number_z=1)
        hillas_iron = self.accel.compute_hillas_maximum_energy(charge_number_z=26)
        self.assertAlmostEqual(hillas_iron["max_energy_ev"] / hillas_proton["max_energy_ev"], 26.0, places=4)

    def test_08_escape_probability(self):
        """Verify escape probability per cycle is strictly between 0 and 1."""
        res = self.accel.compute_fermi_acceleration_spectrum(mach_number=15.0)
        self.assertGreater(res["escape_probability_per_cycle"], 0.0)
        self.assertLess(res["escape_probability_per_cycle"], 1.0)

    def test_09_operator_binding_and_status(self):
        """Verify sovereign creator binding to Senin and legal name."""
        status = self.accel.get_status()
        self.assertEqual(status["stage"], 274)
        self.assertEqual(status["era"], 28)
        self.assertEqual(status["sovereign_operator"], "Senin")
        self.assertEqual(status["sovereign_legal_name"], "Senin Ali K P")
        self.assertEqual(SOVEREIGN_OPERATOR, "Senin")
        self.assertEqual(SOVEREIGN_LEGAL_NAME, "Senin Ali K P")
        self.assertEqual(STAGE_ID, 274)
        self.assertEqual(ERA_ID, 28)

    def test_10_concurrency_and_thread_safety(self):
        """Verify thread-safety across concurrent workers."""
        threads = []
        errors = []

        def worker():
            try:
                engine = RelativisticPlasmaShockAccelerator()
                _ = engine.compute_shock_jump_conditions(25.0)
                _ = engine.compute_fermi_acceleration_spectrum(20.0, 1.0, 20)
                _ = engine.compute_hillas_maximum_energy()
            except Exception as e:
                errors.append(str(e))

        for _ in range(5):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Thread errors: {errors}")


if __name__ == "__main__":
    unittest.main()
