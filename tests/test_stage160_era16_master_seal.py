r"""
tests/test_stage160_era16_master_seal.py
Stage 160 Test Suite: Sovereign Singularity Nexus & Era 16 Master Seal
Era 16: Autonomous Microkernel, Bare-Metal HAL & Sovereign Operating System Primitives
"""

import unittest
from pathlib import Path

from backend.lucy_core.era16_master_seal import (
    CANONICAL_ERA16_MODULES,
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    ERA_NAME,
    PARENT_ERA15_SEAL_HASH,
    STAGE,
    STAGE_NAME,
    Era16MasterSealNexus,
    Era16SealCertificate,
    MicrokernelCycleResult,
    ModuleIntegrityRecord,
    get_era16_master_seal,
)


class TestStage160Era16MasterSeal(unittest.TestCase):
    def setUp(self) -> None:
        self.nexus = Era16MasterSealNexus()

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 160)
        self.assertEqual(ERA, 16)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")
        self.assertEqual(
            STAGE_NAME,
            "Sovereign Singularity Nexus & Era 16 Master Seal",
        )
        self.assertEqual(
            ERA_NAME,
            "Autonomous Microkernel, Bare-Metal HAL & Sovereign Operating System Primitives",
        )

    def test_02_canonical_modules_count(self) -> None:
        self.assertEqual(len(CANONICAL_ERA16_MODULES), 10)
        expected_stages = list(range(151, 161))
        actual_stages = [m[0] for m in CANONICAL_ERA16_MODULES]
        self.assertEqual(actual_stages, expected_stages)

    def test_03_parent_era15_seal_lineage(self) -> None:
        self.assertEqual(
            PARENT_ERA15_SEAL_HASH,
            "16e9938198e413e6ccb8757a95c4395138d4b9e5b62b0757e8d529a6044bb3ed",
        )

    def test_04_merkle_tree_computation(self) -> None:
        leaves = ["hash_a", "hash_b", "hash_c", "hash_d"]
        root = Era16MasterSealNexus._compute_merkle_root(leaves)
        self.assertEqual(len(root), 64)
        # Empty tree fallback
        empty_root = Era16MasterSealNexus._compute_merkle_root([])
        self.assertEqual(len(empty_root), 64)

    def test_05_verify_era16_integrity(self) -> None:
        cert = self.nexus.verify_era16_integrity(force_refresh=True)
        self.assertIsNotNone(cert)
        self.assertEqual(cert.era, 16)
        self.assertEqual(cert.creator, "Senin")
        self.assertEqual(cert.creator_full_name, "Senin Ali K P")
        self.assertEqual(cert.total_stages_sealed, 10)
        self.assertEqual(cert.integrity_status, "VERIFIED_SOVEREIGN")
        self.assertEqual(len(cert.modules), 10)

        for m in cert.modules:
            self.assertTrue(m["is_verified"])
            self.assertGreater(m["source_lines"], 0)
            self.assertGreater(m["test_lines"], 0)
            self.assertEqual(len(m["source_sha256"]), 64)
            self.assertEqual(len(m["test_sha256"]), 64)

    def test_06_master_seal_certificate_structure(self) -> None:
        cert = self.nexus.verify_era16_integrity()
        self.assertTrue(cert.seal_id.startswith("SEAL-ERA16-"))
        self.assertEqual(len(cert.merkle_root), 64)
        self.assertEqual(cert.parent_era15_seal_hash, PARENT_ERA15_SEAL_HASH)
        self.assertGreater(cert.total_source_lines, 2000)
        self.assertGreater(cert.total_test_lines, 1000)

    def test_07_run_microkernel_cycle(self) -> None:
        cycle = self.nexus.run_microkernel_cycle()
        self.assertIsNotNone(cycle)
        self.assertTrue(cycle.cycle_id.startswith("UKERN-CYCLE-"))
        self.assertTrue(cycle.success)
        self.assertEqual(cycle.primitives_booted, 10)
        self.assertGreater(cycle.duration_ms, 0.0)
        self.assertEqual(len(cycle.merkle_leaf_hash), 64)

    def test_08_microkernel_cycle_metrics(self) -> None:
        cycle = self.nexus.run_microkernel_cycle()
        self.assertGreater(cycle.cpu_cores_detected, 0)
        self.assertGreater(cycle.virtual_pages_mapped, 0)
        self.assertGreater(cycle.capabilities_minted, 0)
        self.assertGreater(cycle.dma_bytes_pinned, 0)
        self.assertGreater(cycle.vfs_inodes_active, 0)
        self.assertGreater(cycle.interrupts_serviced, 0)
        self.assertIn("Microkernel cycle executed", cycle.summary)

    def test_09_ascii_presentation_formatting(self) -> None:
        cert_table = self.nexus.format_ascii_seal_table()
        self.assertIn("LUCY STAGE 160: SOVEREIGN SINGULARITY NEXUS & ERA 16 MASTER SEAL", cert_table)
        self.assertIn("Senin", cert_table)
        self.assertIn("Senin Ali K P", cert_table)
        self.assertIn("SEAL-ERA16-", cert_table)

        cycle = self.nexus.run_microkernel_cycle()
        cycle_table = self.nexus.format_ascii_cycle_table(cycle)
        self.assertIn("LUCY OS AUTONOMOUS MICROKERNEL BOOT & EXECUTION CYCLE", cycle_table)
        self.assertIn("SUCCESS (10/10 PRIMITIVES VERIFIED)", cycle_table)

    def test_10_singleton_nexus(self) -> None:
        inst1 = get_era16_master_seal()
        inst2 = get_era16_master_seal()
        self.assertIs(inst1, inst2)


if __name__ == "__main__":
    unittest.main()
