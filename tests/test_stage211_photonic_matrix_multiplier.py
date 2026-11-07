r"""
tests/test_stage211_photonic_matrix_multiplier.py
Stage 211: Autonomous Photonic Matrix Multiplier & Optical Waveguide Emulation Fabric
Era 22: Autonomous Galactic Hyper-Mesh, Hardware-Accelerated Photonic Emulation & Trans-Universal Reasoning Fabrics
"""

import math
import unittest
from backend.lucy_core.photonic_matrix_multiplier import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    MZIUnit,
    OpticalSignal,
    PhotonicMatrixMultiplierFabric,
)


class TestStage211PhotonicMatrixMultiplier(unittest.TestCase):
    """10 Unit Tests for Stage 211 Photonic Matrix Multiplier Fabric."""

    def setUp(self):
        self.fabric = PhotonicMatrixMultiplierFabric(dimension=4)

    def test_01_fabric_initialization(self):
        self.assertEqual(STAGE, 211)
        self.assertEqual(ERA, 22)
        self.assertEqual(self.fabric.dimension, 4)
        self.assertEqual(len(self.fabric.mzi_grid), 4)
        self.assertEqual(len(self.fabric.mzi_grid[0]), 4)
        self.assertEqual(self.fabric.operations_count, 0)

    def test_02_mzi_unit_transfer_matrix_unitary(self):
        mzi = MZIUnit(theta=math.pi / 4.0, phi=0.0, insertion_loss_db=0.0)
        tm = mzi.transfer_matrix()
        self.assertEqual(len(tm), 2)
        self.assertEqual(len(tm[0]), 2)

        # Check approximate unitarity: |det(T)| ~ 1.0
        det = tm[0][0] * tm[1][1] - tm[0][1] * tm[1][0]
        self.assertAlmostEqual(abs(det), 1.0, places=4)

    def test_03_mzi_insertion_loss(self):
        lossless = MZIUnit(theta=0.0, phi=0.0, insertion_loss_db=0.0).transfer_matrix()
        lossy = MZIUnit(theta=0.0, phi=0.0, insertion_loss_db=3.0).transfer_matrix()
        # 3dB loss cuts amplitude by ~1/sqrt(2) = ~0.707
        self.assertLess(abs(lossy[0][0]), abs(lossless[0][0]))

    def test_04_set_mzi_phases_valid_and_bounds(self):
        ok = self.fabric.set_mzi_phases(1, 2, math.pi / 3.0, math.pi / 6.0)
        self.assertTrue(ok)
        self.assertAlmostEqual(self.fabric.mzi_grid[1][2].theta, math.pi / 3.0)
        self.assertAlmostEqual(self.fabric.mzi_grid[1][2].phi, math.pi / 6.0)

        # Out-of-bounds
        self.assertFalse(self.fabric.set_mzi_phases(10, 10, 0.0, 0.0))
        self.assertFalse(self.fabric.set_mzi_phases(-1, 0, 0.0, 0.0))

    def test_05_build_effective_unitary(self):
        U = self.fabric.build_effective_unitary()
        self.assertEqual(len(U), 4)
        self.assertEqual(len(U[0]), 4)
        for r in range(4):
            for c in range(4):
                self.assertIsInstance(U[r][c], complex)

    def test_06_propagate_signal_vector(self):
        inputs = [1.0, 0.0, 0.0, 0.0]
        out_signal = self.fabric.propagate_signal(inputs)
        self.assertIsInstance(out_signal, OpticalSignal)
        self.assertEqual(len(out_signal.amplitudes), 4)
        # Power should be non-zero
        total_pwr = sum(abs(a) ** 2 for a in out_signal.amplitudes)
        self.assertGreater(total_pwr, 0.0)

    def test_07_optical_signal_intensity(self):
        sig = OpticalSignal(amplitudes=[complex(0.6, 0.8), complex(0.0, 1.0)])
        intensities = sig.intensities()
        # |0.6 + 0.8j|^2 = 0.36 + 0.64 = 1.0
        self.assertAlmostEqual(intensities[0], 1.0, places=4)
        # |1.0j|^2 = 1.0
        self.assertAlmostEqual(intensities[1], 1.0, places=4)

    def test_08_optical_activation_thresholding(self):
        sig = OpticalSignal(amplitudes=[0.5, 0.2, 0.05])
        # Intensities: [0.25, 0.04, 0.0025]
        act = self.fabric.apply_optical_activation(sig, threshold=0.1)
        self.assertAlmostEqual(act[0], 0.15, places=4)
        self.assertEqual(act[1], 0.0)
        self.assertEqual(act[2], 0.0)

    def test_09_operations_counter_and_energy(self):
        self.fabric.propagate_signal([1.0, 1.0, 1.0, 1.0])
        self.fabric.propagate_signal([0.5, 0.5, 0.5, 0.5])
        s = self.fabric.status()
        self.assertEqual(s["operations_count"], 2)
        self.assertGreater(s["total_optical_energy_pj"], 0.0)

    def test_10_ascii_status_formatting(self):
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 211: PHOTONIC MATRIX MULTIPLIER & WAVEGUIDE EMULATOR", tbl)
        self.assertIn("Mesh Topology", tbl)
        self.assertIn("Speed-of-Light Passive Coherent Photonics", tbl)


if __name__ == "__main__":
    unittest.main()
