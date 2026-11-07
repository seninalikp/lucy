r"""
tests/test_stage152_hal_cpu_topology.py
Stage 152 Test Suite: Hardware Abstraction Layer (HAL) & CPU Topology Sentinel
Era 16: Autonomous Microkernel, Bare-Metal HAL & Sovereign Operating System Primitives
"""

import unittest

from backend.lucy_core.hal_cpu_topology import (
    CREATOR,
    ERA,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    CPUTopology,
    HALCpuTopologySentinel,
    get_hal_cpu_topology,
)


class TestStage152HALCpuTopology(unittest.TestCase):
    def setUp(self) -> None:
        self.hal = HALCpuTopologySentinel()

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 152)
        self.assertEqual(ERA, 16)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")
        self.assertEqual(
            STAGE_NAME,
            "Hardware Abstraction Layer (HAL) & CPU Topology Sentinel",
        )

    def test_02_cpu_topology_discovery(self) -> None:
        top = self.hal.topology
        self.assertIsInstance(top, CPUTopology)
        self.assertTrue(top.logical_threads_count >= 1)
        self.assertTrue(top.physical_cores_count >= 1)
        self.assertIn(top.architecture, ("x86_64", "aarch64", "arm64", "amd64"))
        self.assertIsNotNone(top.model_name)

    def test_03_cache_hierarchy_mapping(self) -> None:
        caches = self.hal.topology.caches
        self.assertTrue(len(caches) >= 3)
        levels = {c.level for c in caches}
        self.assertIn("L1i", levels)
        self.assertIn("L1d", levels)
        self.assertIn("L2", levels)
        for c in caches:
            self.assertTrue(c.size_kb > 0)
            self.assertEqual(c.line_size_bytes, 64)

    def test_04_isa_features_detection(self) -> None:
        features = self.hal.topology.isa_features
        self.assertTrue(len(features) >= 10)
        self.assertIn("TSC", features)
        self.assertIn("SSE", features)
        self.assertIn("AVX", features)
        self.assertIn("APIC", features)

    def test_05_tsc_calibration_and_timing(self) -> None:
        ghz = self.hal.calibrate_tsc(sample_duration_ms=10)
        self.assertTrue(ghz >= 1.0)
        c1 = self.hal.rdtsc()
        c2 = self.hal.rdtsc()
        self.assertTrue(c2 >= c1)

    def test_06_cycles_ns_conversions(self) -> None:
        ns = 1000.0  # 1 microsecond
        cycles = self.hal.ns_to_cycles(ns)
        self.assertTrue(cycles > 0)
        recovered_ns = self.hal.cycles_to_ns(cycles)
        self.assertAlmostEqual(ns, recovered_ns, delta=1.0)

    def test_07_simulated_io_ports(self) -> None:
        # Default unwritten port returns 0xFF (floating bus)
        self.assertEqual(self.hal.inb(0x3F8), 0xFF)

        # Write 8-bit value
        self.hal.outb(0x3F8, 0x41)  # ASCII 'A'
        self.assertEqual(self.hal.inb(0x3F8), 0x41)

        # Out-of-range value masks to 8-bit
        self.hal.outb(0x80, 0x1234)
        self.assertEqual(self.hal.inb(0x80), 0x34)

    def test_08_mmio_window_mapping_and_lookup(self) -> None:
        # Standard default regions exist
        self.assertIsNotNone(self.hal.is_mmio_address(0xFEE00010))  # Inside APIC_BASE
        self.assertIsNotNone(self.hal.is_mmio_address(0xFED00050))  # Inside HPET_BASE
        self.assertIsNone(self.hal.is_mmio_address(0x1000))        # Regular RAM

        # Map new custom MMIO window
        ok = self.hal.map_mmio_window("VIRTIO_NET", 0x10000000, 0x4000)
        self.assertTrue(ok)
        self.assertEqual(self.hal.is_mmio_address(0x10002000), "VIRTIO_NET")

        # Overlapping window must fail
        fail_overlap = self.hal.map_mmio_window("BAD_OVERLAP", 0x10001000, 0x2000)
        self.assertFalse(fail_overlap)

    def test_09_hardware_attestation(self) -> None:
        att = self.hal.get_hardware_attestation()
        self.assertEqual(att["creator"], "Senin")
        self.assertEqual(att["operator"], "Senin Ali K P")
        self.assertEqual(len(att["sha256"]), 64)
        self.assertEqual(len(att["hmac_signature"]), 64)

    def test_10_ascii_status_presentation(self) -> None:
        status = self.hal.format_ascii_status()
        self.assertIn("LUCY STAGE 152", status)
        self.assertIn("Senin", status)
        self.assertIn("APIC_BASE", status)
        self.assertIn("L1d", status)


if __name__ == "__main__":
    unittest.main()
