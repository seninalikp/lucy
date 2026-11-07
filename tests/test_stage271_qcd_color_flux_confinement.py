"""
Unit Tests for Stage 271: Quantum Chromodynamic (QCD) Asymptotic Freedom, Color Flux Tube Confinement & Hadronization Engine
Author & Permanent Sovereign Operator: Senin (Senin Ali K P)
"""

import unittest
import threading
from backend.lucy_core.qcd_color_flux_confinement import (
    QCDColorFluxConfinement,
    SOVEREIGN_OPERATOR,
    SOVEREIGN_LEGAL_NAME,
    STAGE_ID,
    STAGE_NAME,
    ERA_ID
)


class TestStage271QCDColorFluxConfinement(unittest.TestCase):
    """Thorough unit test suite for Stage 271."""

    def setUp(self):
        self.qcd = QCDColorFluxConfinement()

    def test_01_initialization(self):
        """Verify initialization constants and physical parameters."""
        self.assertEqual(self.qcd.lambda_qcd, 0.217)
        self.assertEqual(self.qcd.sigma, 0.9)
        self.assertEqual(self.qcd.n_f, 4)
        self.assertAlmostEqual(self.qcd.casimir_cf, 4.0 / 3.0, places=5)
        self.assertEqual(len(self.qcd.hadronization_events), 0)

    def test_02_asymptotic_freedom_running(self):
        """Verify asymptotic freedom: coupling decreases as energy increases."""
        low_energy = self.qcd.compute_running_coupling(2.0)
        high_energy = self.qcd.compute_running_coupling(100.0)
        self.assertGreater(low_energy["alpha_s"], high_energy["alpha_s"])
        self.assertTrue(high_energy["is_asymptotically_free"])

    def test_03_beta_function_positivity(self):
        """Verify beta_0 is strictly positive (QCD anti-screening)."""
        res = self.qcd.compute_running_coupling(10.0)
        # beta_0 = 33 - 2 * 4 = 25
        self.assertEqual(res["beta_0"], 25.0)

    def test_04_cornell_potential_short_range_coulomb(self):
        """Verify short-range Coulombic dominance at small r (r = 0.05 fm)."""
        res = self.qcd.compute_cornell_potential(separation_r_fm=0.05)
        self.assertLess(res["v_coulomb_gev"], 0.0)
        self.assertLess(res["v_total_gev"], 0.0)
        self.assertLess(abs(res["v_string_gev"]), abs(res["v_coulomb_gev"]))

    def test_05_cornell_potential_long_range_confinement(self):
        """Verify long-range linear confinement string dominance at large r (r = 2.0 fm)."""
        res = self.qcd.compute_cornell_potential(separation_r_fm=2.0)
        self.assertGreater(res["v_string_gev"], 0.0)
        self.assertGreater(res["v_total_gev"], 0.0)
        self.assertGreater(res["v_string_gev"], abs(res["v_coulomb_gev"]))

    def test_06_flux_tube_breaking_threshold(self):
        """Verify string breaks when energy exceeds 2 * m_q."""
        mq = 0.35 # 350 MeV
        res = self.qcd.simulate_flux_tube_breaking(quark_mass_gev=mq, max_separation_fm=2.0)
        expected_snap_r = (2.0 * mq) / self.qcd.sigma
        self.assertAlmostEqual(res["critical_snap_distance_fm"], expected_snap_r, places=3)
        self.assertTrue(res["tube_snapped"])
        self.assertEqual(len(res["hadron_fragments"]), 2)

    def test_07_color_singlet_meson_and_baryon(self):
        """Verify singlet projection for physical mesons and baryons."""
        meson = self.qcd.project_color_multiplet(num_quarks=1, num_antiquarks=1)
        self.assertTrue(meson["singlet_available"])
        self.assertEqual(meson["confinement_status"], "CONFINED_OBSERVABLE")

        baryon = self.qcd.project_color_multiplet(num_quarks=3, num_antiquarks=0)
        self.assertTrue(baryon["singlet_available"])
        self.assertEqual(baryon["confinement_status"], "CONFINED_OBSERVABLE")

    def test_08_unphysical_free_quark_triality(self):
        """Verify isolated single quark with non-zero triality is confined."""
        isolated = self.qcd.project_color_multiplet(num_quarks=1, num_antiquarks=0)
        self.assertFalse(isolated["singlet_available"])
        self.assertEqual(isolated["confinement_status"], "UNPHYSICAL_FREE_COLOR")

    def test_09_operator_binding_and_status(self):
        """Verify sovereign creator binding to Senin and legal name."""
        status = self.qcd.get_status()
        self.assertEqual(status["stage"], 271)
        self.assertEqual(status["era"], 28)
        self.assertEqual(status["sovereign_operator"], "Senin")
        self.assertEqual(status["sovereign_legal_name"], "Senin Ali K P")
        self.assertEqual(SOVEREIGN_OPERATOR, "Senin")
        self.assertEqual(SOVEREIGN_LEGAL_NAME, "Senin Ali K P")
        self.assertEqual(STAGE_ID, 271)
        self.assertEqual(ERA_ID, 28)

    def test_10_concurrency_and_thread_safety(self):
        """Verify thread-safety across concurrent workers."""
        threads = []
        errors = []

        def worker():
            try:
                engine = QCDColorFluxConfinement()
                _ = engine.compute_running_coupling(50.0)
                _ = engine.compute_cornell_potential(0.8)
                _ = engine.simulate_flux_tube_breaking()
                _ = engine.project_color_multiplet(3, 0)
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
