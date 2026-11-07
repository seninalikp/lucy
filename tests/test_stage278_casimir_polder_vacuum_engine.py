"""
Unit Tests for Stage 278: Microscopic Casimir-Polder Vacuum Dispersion Force & Metamaterial Levitation Engine
Author & Permanent Sovereign Operator: Senin (Senin Ali K P)
"""

import unittest
import math
import threading
from backend.lucy_core.casimir_polder_vacuum_engine import (
    CasimirPolderVacuumEngine,
    SOVEREIGN_OPERATOR,
    SOVEREIGN_LEGAL_NAME,
    STAGE_ID,
    STAGE_NAME,
    ERA_ID
)


class TestStage278CasimirPolderVacuumEngine(unittest.TestCase):
    """Thorough unit test suite for Stage 278."""

    def setUp(self):
        self.engine = CasimirPolderVacuumEngine(plate_area_m2=1e-4)

    def test_01_initialization(self):
        """Verify initialization constants and physical parameters."""
        self.assertEqual(self.engine.area, 1e-4)
        self.assertEqual(len(self.engine.levitation_experiments), 0)

    def test_02_ideal_casimir_pressure_scaling(self):
        """Verify Casimir pressure falls off as 1/d^4: doubling d drops P by factor 16."""
        p1 = self.engine.compute_ideal_casimir_pressure(separation_d_m=100e-9)
        p2 = self.engine.compute_ideal_casimir_pressure(separation_d_m=200e-9)
        ratio = p1["pressure_pascal"] / p2["pressure_pascal"]
        self.assertAlmostEqual(ratio, 16.0, places=4)

    def test_03_ideal_casimir_force_sign(self):
        """Verify ideal Casimir force is strictly attractive (negative)."""
        res = self.engine.compute_ideal_casimir_pressure(separation_d_m=50e-9)
        self.assertLess(res["pressure_pascal"], 0.0)
        self.assertLess(res["force_newtons"], 0.0)
        self.assertEqual(res["force_sign"], "ATTRACTIVE")

    def test_04_casimir_polder_potential_scaling(self):
        """Verify retarded Casimir-Polder potential falls off as 1/d^4."""
        u1 = self.engine.compute_casimir_polder_potential(distance_d_m=50e-9)
        u2 = self.engine.compute_casimir_polder_potential(distance_d_m=100e-9)
        ratio = u1["potential_joules"] / u2["potential_joules"]
        self.assertAlmostEqual(ratio, 16.0, places=4)

    def test_05_casimir_polder_dielectric_dependence(self):
        """Verify potential approaches zero when surface permittivity epsilon -> 1."""
        u_vac = self.engine.compute_casimir_polder_potential(distance_d_m=50e-9, surface_permittivity=1.0)
        self.assertEqual(u_vac["potential_joules"], 0.0)

    def test_06_dlp_repulsive_condition(self):
        """Verify DLP condition eps_1 < eps_m < eps_2 yields repulsive force."""
        # Teflon (eps=2.1) in Bromobenzene (eps=5.4) facing Gold (eps=large ~ 100)
        res = self.engine.evaluate_repulsive_casimir_levitation(
            eps_plate_1=2.1,
            eps_fluid_medium=5.4,
            eps_plate_2=100.0,
            separation_d_m=50e-9
        )
        self.assertTrue(res["dlp_condition_satisfied"])
        self.assertGreater(res["casimir_pressure_pa"], 0.0)
        self.assertGreater(res["casimir_force_n"], 0.0)

    def test_07_dlp_attractive_condition(self):
        """Verify eps_m < eps_1, eps_2 yields attractive force."""
        # Vacuum/Air (eps_m = 1) between Silica (eps=4) and Gold (eps=100)
        res = self.engine.evaluate_repulsive_casimir_levitation(
            eps_plate_1=4.0,
            eps_fluid_medium=1.0,
            eps_plate_2=100.0,
            separation_d_m=50e-9
        )
        self.assertFalse(res["dlp_condition_satisfied"])
        self.assertLess(res["casimir_pressure_pa"], 0.0)
        self.assertLess(res["casimir_force_n"], 0.0)

    def test_08_quantum_levitation_trap_stiffness(self):
        """Verify stable trap stiffness k > 0 for repulsive levitation."""
        res = self.engine.evaluate_repulsive_casimir_levitation(
            eps_plate_1=2.0,
            eps_fluid_medium=4.0,
            eps_plate_2=80.0,
            separation_d_m=40e-9,
            flake_mass_kg=1e-18
        )
        self.assertGreater(res["trap_stiffness_n_m"], 0.0)
        self.assertTrue(res["is_stably_levitated"])

    def test_09_operator_binding_and_status(self):
        """Verify sovereign creator binding to Senin and legal name."""
        status = self.engine.get_status()
        self.assertEqual(status["stage"], 278)
        self.assertEqual(status["era"], 28)
        self.assertEqual(status["sovereign_operator"], "Senin")
        self.assertEqual(status["sovereign_legal_name"], "Senin Ali K P")
        self.assertEqual(SOVEREIGN_OPERATOR, "Senin")
        self.assertEqual(SOVEREIGN_LEGAL_NAME, "Senin Ali K P")
        self.assertEqual(STAGE_ID, 278)
        self.assertEqual(ERA_ID, 28)

    def test_10_concurrency_and_thread_safety(self):
        """Verify thread-safety across concurrent workers."""
        threads = []
        errors = []

        def worker():
            try:
                engine = CasimirPolderVacuumEngine()
                _ = engine.compute_ideal_casimir_pressure(100e-9)
                _ = engine.compute_casimir_polder_potential(50e-9)
                _ = engine.evaluate_repulsive_casimir_levitation(2.1, 5.4, 100.0)
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
