"""
tests/test_stage237_photonic_optical_switch.py
Unit tests for Stage 237: Autonomous Photonic Optical Neural Interconnect & Ultra-Low-Latency Switch Fabric
Era 24: Trans-Dimensional Cognitive Resonance, Neuromorphic Spiking Fabrics & Autonomous Sovereign AGI Singularity
"""

import math
import unittest
from backend.lucy_core.photonic_optical_switch import (
    STAGE,
    STAGE_NAME,
    ERA,
    OpticalChannel,
    MZIUnit,
    PhotonicOpticalSwitchFabric
)


class TestStage237PhotonicOpticalSwitch(unittest.TestCase):

    def test_01_optical_channel_frequencies(self):
        """Test WDM C-band channel frequencies and wavelengths."""
        ch0 = OpticalChannel.create_c_band(0, base_nm=1530.0, channel_spacing_nm=0.8)
        self.assertEqual(ch0.channel_id, 0)
        self.assertEqual(ch0.wavelength_nm, 1530.0)
        # f = c / lambda = 2.9979e8 / 1530e-9 ~ 195.94 THz
        self.assertAlmostEqual(ch0.frequency_thz, 195.94, places=1)

        ch1 = OpticalChannel.create_c_band(1, base_nm=1530.0, channel_spacing_nm=0.8)
        self.assertEqual(ch1.wavelength_nm, 1530.8)
        self.assertTrue(ch1.frequency_thz < ch0.frequency_thz)

    def test_02_mzi_transfer_matrix_unitary(self):
        """Test 2x2 MZI transfer matrix structure and power conservation."""
        unit = MZIUnit(mzi_id="test_mzi", theta=math.pi / 4.0, phi=0.0, insertion_loss_db=0.0)
        m = unit.transfer_matrix()
        self.assertEqual(len(m), 2)
        self.assertEqual(len(m[0]), 2)

        # 50:50 beam splitter cos(pi/4) = sin(pi/4) ~ 0.7071
        self.assertAlmostEqual(abs(m[0][0]), 1.0 / math.sqrt(2), places=4)
        self.assertAlmostEqual(abs(m[1][0]), 1.0 / math.sqrt(2), places=4)

    def test_03_mzi_vector_transformation(self):
        """Test field transformation through a single MZI unit."""
        unit = MZIUnit(mzi_id="mzi_1", theta=math.pi / 4.0, phi=0.0, insertion_loss_db=0.0)
        out1, out2 = unit.transform_vector(1.0 + 0j, 0.0 + 0j)
        p_in = 1.0
        p_out = (abs(out1) ** 2) + (abs(out2) ** 2)
        self.assertAlmostEqual(p_in, p_out, places=4)

    def test_04_optical_packet_flight_time_and_loss(self):
        """Test sub-nanosecond optical flight time and attenuation in silicon waveguide."""
        fabric = PhotonicOpticalSwitchFabric()
        res = fabric.route_optical_packet(ingress_port=0, packet_bytes=b"NEURAL_TENSOR_WEIGHTS", waveguide_length_cm=2.0)

        # 2 cm at ~8.69e7 m/s is ~230 picoseconds
        self.assertTrue(100.0 < res["latency_ps"] < 400.0)
        self.assertGreater(res["loss_db"], 0.5)
        self.assertGreater(res["output_power_mw"], 0.0)
        self.assertEqual(res["ingress_port"], 0)
        self.assertEqual(res["egress_port"], 0)

    def test_05_crossbar_routing_program(self):
        """Test programming arbitrary crossbar routing configuration."""
        fabric = PhotonicOpticalSwitchFabric(num_channels=8)
        fabric.program_route(ingress_port=2, egress_port=7)

        res = fabric.route_optical_packet(ingress_port=2, packet_bytes=b"BURST_DATA")
        self.assertEqual(res["ingress_port"], 2)
        self.assertEqual(res["egress_port"], 7)

        with self.assertRaises(ValueError):
            fabric.program_route(99, 100)

    def test_06_photonic_matrix_vector_clements_mesh(self):
        """Test coherent GEMM through N=4 Clements MZI mesh."""
        fabric = PhotonicOpticalSwitchFabric(mesh_dim=4)
        in_vec = [1.0 + 0j, 0.5 + 0.2j, -0.3 + 0.1j, 0.0 + 0.8j]
        out_vec = fabric.execute_optical_matrix_vector(in_vec)

        self.assertEqual(len(out_vec), 4)
        self.assertTrue(all(isinstance(v, complex) for v in out_vec))
        self.assertEqual(fabric.total_photonic_gemms, 1)

    def test_07_photodetector_responsivity(self):
        """Test conversion from complex field amplitudes to detected photocurrents."""
        fabric = PhotonicOpticalSwitchFabric()
        fields = [1.0 + 0j, 0.0 + 1.0j, 0.5 + 0.5j]
        intensities = fabric.photodetect_intensities(fields, responsivity_a_w=0.85)

        self.assertEqual(len(intensities), 3)
        self.assertAlmostEqual(intensities[0], 0.85, places=4)
        self.assertAlmostEqual(intensities[1], 0.85, places=4)
        self.assertAlmostEqual(intensities[2], 0.85 * 0.5, places=4)

    def test_08_thermal_phase_drift_simulation(self):
        """Test thermo-optic drift alters MZI phases."""
        fabric = PhotonicOpticalSwitchFabric(mesh_dim=2)
        mzi_sample = fabric.mzi_mesh["mzi_0_0"]
        initial_theta = mzi_sample.theta

        fabric.induce_thermal_drift(delta_kelvin=20.0)
        self.assertEqual(fabric.temperature_kelvin, 320.0)
        self.assertNotEqual(mzi_sample.theta, initial_theta)

    def test_09_autonomous_closed_loop_calibration(self):
        """Test autonomous thermal drift compensation loop."""
        fabric = PhotonicOpticalSwitchFabric(mesh_dim=2)
        fabric.induce_thermal_drift(delta_kelvin=10.0)

        # Calibrate
        corrected = fabric.calibrate_thermo_optic_phases(target_theta=math.pi / 4.0)
        self.assertGreater(corrected, 0)
        self.assertEqual(fabric.calibrations_performed, 1)

        for unit in fabric.mzi_mesh.values():
            self.assertAlmostEqual(unit.theta, math.pi / 4.0, places=4)

    def test_10_fabric_status_and_ascii_table(self):
        """Test status dictionary and CP1252-safe ASCII table."""
        fabric = PhotonicOpticalSwitchFabric()
        st = fabric.status()
        self.assertEqual(st["stage"], 237)
        self.assertEqual(st["era"], 24)
        self.assertIn("wdm_channels", st)

        tbl = fabric.format_ascii_status()
        self.assertIn("STAGE 237", tbl)
        self.assertIn("WDM Optical Channels", tbl)
        self.assertIn("Mesh Topology", tbl)
        self.assertTrue(tbl.startswith("+--"))
        self.assertTrue(tbl.endswith("--+"))


if __name__ == "__main__":
    unittest.main()
