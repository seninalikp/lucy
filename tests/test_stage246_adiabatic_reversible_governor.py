"""
tests/test_stage246_adiabatic_reversible_governor.py
Unit tests for Stage 246: Thermodynamically Reversible Landauer-Zero Computation & Adiabatic Switching Governor
Era 25: Omni-Dimensional Super-Intelligence Matrix, Astro-Cognitive Planetary Orchestration & Sovereign Trans-Singularity Metamaterials
"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.getcwd())

from backend.lucy_core.adiabatic_reversible_governor import (
    STAGE,
    STAGE_NAME,
    ERA,
    AdiabaticReversibleGovernorFabric
)


class TestStage246AdiabaticReversibleGovernor(unittest.TestCase):

    def test_01_landauer_limit_at_300k(self):
        """Test Landauer energy bound E = k_B * T * ln(2) at 300 Kelvin."""
        gov = AdiabaticReversibleGovernorFabric(temperature_kelvin=300.0)
        e_j = gov.landauer_energy_per_bit_joules
        # ~2.871e-21 Joules, ~0.0179 eV
        self.assertAlmostEqual(e_j / 1e-21, 2.8710, places=3)
        ev = e_j / 1.602176634e-19
        self.assertAlmostEqual(ev, 0.01792, places=4)

    def test_02_feynman_cnot_truth_table_and_inversion(self):
        """Test Feynman CNOT truth table and self-inverse involution property."""
        gov = AdiabaticReversibleGovernorFabric()
        truth_table = [
            ((0, 0), (0, 0)),
            ((0, 1), (0, 1)),
            ((1, 0), (1, 1)),
            ((1, 1), (1, 0)),
        ]
        for (c_in, t_in), (c_exp, t_exp) in truth_table:
            c_out, t_out = gov.execute_feynman_cnot(c_in, t_in)
            self.assertEqual((c_out, t_out), (c_exp, t_exp))
            # Test self-inverse
            c_inv, t_inv = gov.execute_feynman_cnot(c_out, t_out)
            self.assertEqual((c_inv, t_inv), (c_in, t_in))

    def test_03_fredkin_cswap_conservative_weight(self):
        """Test Fredkin gate strictly conserves Hamming weight (number of 1s)."""
        gov = AdiabaticReversibleGovernorFabric()
        for c in (0, 1):
            for a in (0, 1):
                for b in (0, 1):
                    c_out, a_out, b_out = gov.execute_fredkin_cswap(c, a, b)
                    # Bit conservation
                    in_weight = c + a + b
                    out_weight = c_out + a_out + b_out
                    self.assertEqual(in_weight, out_weight)

    def test_04_fredkin_cswap_inversion(self):
        """Test Fredkin CSWAP is self-inverse: applying twice recovers original input."""
        gov = AdiabaticReversibleGovernorFabric()
        c_out, a_out, b_out = gov.execute_fredkin_cswap(1, 1, 0)
        self.assertEqual((c_out, a_out, b_out), (1, 0, 1))

        c_inv, a_inv, b_inv = gov.execute_fredkin_cswap(c_out, a_out, b_out)
        self.assertEqual((c_inv, a_inv, b_inv), (1, 1, 0))

    def test_05_toffoli_ccnot_truth_table_and_inversion(self):
        """Test Toffoli CCNOT gate flips target iff both controls are 1."""
        gov = AdiabaticReversibleGovernorFabric()
        # (1, 1, 0) -> (1, 1, 1)
        self.assertEqual(gov.execute_toffoli_ccnot(1, 1, 0), (1, 1, 1))
        # (1, 0, 1) -> (1, 0, 1)
        self.assertEqual(gov.execute_toffoli_ccnot(1, 0, 1), (1, 0, 1))
        # Self-inverse
        c1, c2, t = gov.execute_toffoli_ccnot(1, 1, 1)
        self.assertEqual((c1, c2, t), (1, 1, 0))
        self.assertEqual(gov.execute_toffoli_ccnot(c1, c2, t), (1, 1, 1))

    def test_06_adiabatic_switching_dissipation_reduction(self):
        """Test adiabatic slow charging drastically reduces dissipated energy vs abrupt CMOS."""
        gov = AdiabaticReversibleGovernorFabric()
        res = gov.compute_adiabatic_switching_dissipation(
            capacitance_f=1e-15,
            voltage_v=0.8,
            resistance_ohms=1000.0,
            ramp_time_seconds=10e-9 # 10 ns
        )
        self.assertGreater(res["energy_reduction_factor"], 100.0)
        self.assertLess(res["adiabatic_dissipated_energy_joules"], res["conventional_cmos_energy_joules"])

    def test_07_irreversible_erasure_heat_accumulation(self):
        """Test heat dissipation from irreversible erasure matches Landauer limit."""
        gov = AdiabaticReversibleGovernorFabric(temperature_kelvin=300.0)
        heat = gov.simulate_irreversible_erasure(1000)
        expected_heat = 1000 * gov.landauer_energy_per_bit_joules
        self.assertAlmostEqual(heat, expected_heat, places=15)
        self.assertEqual(gov.total_bits_erased, 1000)

    def test_08_temperature_scaling_of_landauer_limit(self):
        """Test Landauer energy scales linearly with temperature."""
        gov_300 = AdiabaticReversibleGovernorFabric(temperature_kelvin=300.0)
        gov_400 = AdiabaticReversibleGovernorFabric(temperature_kelvin=400.0)

        e_300 = gov_300.landauer_energy_per_bit_joules
        e_400 = gov_400.landauer_energy_per_bit_joules

        self.assertAlmostEqual(e_400 / e_300, 4.0 / 3.0, places=4)

    def test_09_fabric_status_dictionary(self):
        """Test status dictionary output."""
        gov = AdiabaticReversibleGovernorFabric()
        st = gov.status()
        self.assertEqual(st["stage"], 246)
        self.assertEqual(st["era"], 25)
        self.assertEqual(st["temperature_k"], 300.0)
        self.assertIn("landauer_limit_joules_per_bit", st)

    def test_10_ascii_status_table(self):
        """Test CP1252-safe ASCII table formatting."""
        gov = AdiabaticReversibleGovernorFabric()
        tbl = gov.format_ascii_status()
        self.assertIn("STAGE 246", tbl)
        self.assertIn("Landauer Limit Bound", tbl)
        self.assertIn("Reversible Logic Ops", tbl)
        self.assertTrue(tbl.startswith("+--"))
        self.assertTrue(tbl.endswith("--+"))


if __name__ == "__main__":
    unittest.main()
