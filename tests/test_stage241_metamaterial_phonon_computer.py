"""
tests/test_stage241_metamaterial_phonon_computer.py
Unit tests for Stage 241: Programmable Metamaterial Phonon-Polariton Waveguide Computing & Analog Tensor Interconnect
Era 25: Omni-Dimensional Super-Intelligence Matrix, Astro-Cognitive Planetary Orchestration & Sovereign Trans-Singularity Metamaterials
"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.getcwd())

from backend.lucy_core.metamaterial_phonon_computer import (
    STAGE,
    STAGE_NAME,
    ERA,
    PhononicLatticeUnit,
    BandgapRange,
    MetamaterialPhononComputerFabric
)


class TestStage241MetamaterialPhononComputer(unittest.TestCase):

    def test_01_phononic_lattice_creation_and_velocities(self):
        """Test lattice unit creation and acoustic velocity formula v = sqrt(E / rho)."""
        unit = PhononicLatticeUnit(cell_id=0, density_kg_m3=2330.0, elastic_modulus_gpa=160.0)
        # v = sqrt(160e9 / 2330) ~ 8286.7 m/s
        self.assertAlmostEqual(unit.acoustic_velocity_m_s, 8286.7, places=1)

    def test_02_acoustic_bandgap_detection(self):
        """Test frequency membership in acoustic bandgap."""
        bg = BandgapRange(lower_freq_ghz=1.2, upper_freq_ghz=2.8)
        self.assertTrue(bg.contains(1.5))
        self.assertTrue(bg.contains(2.0))
        self.assertFalse(bg.contains(0.8))
        self.assertFalse(bg.contains(3.5))

    def test_03_passband_transmission_low_damping(self):
        """Test transmission at passband frequency (0.8 GHz)."""
        fabric = MetamaterialPhononComputerFabric()
        res = fabric.propagate_phonon_wave(freq_ghz=0.8, initial_amplitude=1.0, distance_um=10.0)
        self.assertEqual(res["transmission_mode"], "PASSBAND_TRANSMISSION")
        self.assertGreater(res["output_amplitude"], 0.9)
        self.assertFalse(res["topological_protection"])

    def test_04_bandgap_forbidden_rejection(self):
        """Test wave inside bandgap is heavily attenuated without topological defect."""
        fabric = MetamaterialPhononComputerFabric()
        res = fabric.propagate_phonon_wave(
            freq_ghz=2.0,
            initial_amplitude=1.0,
            distance_um=10.0,
            use_topological_defect=False
        )
        self.assertEqual(res["transmission_mode"], "BANDGAP_FORBIDDEN")
        self.assertGreaterEqual(res["attenuation_db"], 30.0)
        self.assertLess(res["output_amplitude"], 0.05)

    def test_05_topological_defect_waveguide_protection(self):
        """Test topological defect guides forbidden frequency with minimal loss."""
        fabric = MetamaterialPhononComputerFabric()
        res = fabric.propagate_phonon_wave(
            freq_ghz=2.0,
            initial_amplitude=1.0,
            distance_um=10.0,
            use_topological_defect=True
        )
        self.assertEqual(res["transmission_mode"], "TOPOLOGICALLY_PROTECTED_TRANSMISSION")
        self.assertTrue(res["topological_protection"])
        self.assertGreater(res["output_amplitude"], 0.9)

    def test_06_acoustic_propagation_flight_delay(self):
        """Test acoustic propagation delay matches distance / velocity."""
        fabric = MetamaterialPhononComputerFabric()
        res = fabric.propagate_phonon_wave(freq_ghz=0.8, distance_um=20.0)
        # ~20 um at ~8000 m/s is ~2.5 nanoseconds = 2500 ps
        self.assertGreater(res["delay_ps"], 1000.0)
        self.assertLess(res["delay_ps"], 5000.0)

    def test_07_analog_wave_mac_orthogonal_interference(self):
        """Test analog wave-based MAC computation for positive inputs."""
        fabric = MetamaterialPhononComputerFabric()
        inputs = [1.0, 2.0, 3.0]
        weights = [4.0, 5.0, 6.0]
        # Dot product = 1*4 + 2*5 + 3*6 = 4 + 10 + 18 = 32.0
        res = fabric.execute_analog_wave_mac(inputs, weights)
        self.assertAlmostEqual(res["analog_mac_result"], 32.0, places=4)
        self.assertAlmostEqual(res["theoretical_dot_product"], 32.0, places=4)
        self.assertAlmostEqual(res["mac_fidelity"], 1.0, places=4)

    def test_08_analog_wave_mac_negative_weights(self):
        """Test analog wave-based MAC computation with destructive wave interference."""
        fabric = MetamaterialPhononComputerFabric()
        inputs = [2.0, 3.0]
        weights = [5.0, -4.0]
        # Dot product = 2*5 + 3*(-4) = 10 - 12 = -2.0
        res = fabric.execute_analog_wave_mac(inputs, weights)
        self.assertAlmostEqual(res["analog_mac_result"], -2.0, places=4)
        self.assertAlmostEqual(res["theoretical_dot_product"], -2.0, places=4)

    def test_09_analog_mac_dimension_mismatch_error(self):
        """Test dimension mismatch raises ValueError."""
        fabric = MetamaterialPhononComputerFabric()
        with self.assertRaises(ValueError):
            fabric.execute_analog_wave_mac([1.0, 2.0], [1.0])

    def test_10_fabric_status_and_ascii_table(self):
        """Test status dictionary and CP1252-safe ASCII table."""
        fabric = MetamaterialPhononComputerFabric()
        st = fabric.status()
        self.assertEqual(st["stage"], 241)
        self.assertEqual(st["era"], 25)
        self.assertIn("lattice_cells", st)

        tbl = fabric.format_ascii_status()
        self.assertIn("STAGE 241", tbl)
        self.assertIn("Lattice Dimension", tbl)
        self.assertIn("Acoustic Bandgap", tbl)
        self.assertTrue(tbl.startswith("+--"))
        self.assertTrue(tbl.endswith("--+"))


if __name__ == "__main__":
    unittest.main()
