r"""
tests/test_stage150_era15_master_seal.py
Stage 150 Test Suite: Sovereign Singularity Nexus & Era 15 Master Seal
Era 15: Autonomous Self-Hosting Compiler & Multi-Tier Optimization Pipeline
"""

import json
import unittest
from pathlib import Path

from backend.lucy_core.era15_master_seal import (
    CANONICAL_ERA15_MODULES,
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    ERA_NAME,
    PARENT_ERA14_SEAL_HASH,
    STAGE,
    STAGE_NAME,
    CompilerCycleResult,
    Era15MasterSealNexus,
    Era15SealCertificate,
    get_era15_master_seal,
)


class TestStage150Era15MasterSeal(unittest.TestCase):
    def setUp(self) -> None:
        self.nexus = Era15MasterSealNexus()

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 150)
        self.assertEqual(ERA, 15)
        self.assertEqual(
            ERA_NAME,
            "Autonomous Self-Hosting Compiler & Multi-Tier Optimization Pipeline",
        )
        self.assertEqual(
            STAGE_NAME,
            "Sovereign Singularity Nexus & Era 15 Master Seal",
        )
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")

    def test_02_canonical_modules_definition(self) -> None:
        self.assertEqual(len(CANONICAL_ERA15_MODULES), 10)
        expected_stages = list(range(141, 151))
        actual_stages = [m[0] for m in CANONICAL_ERA15_MODULES]
        self.assertEqual(actual_stages, expected_stages)

    def test_03_era14_parent_lineage(self) -> None:
        self.assertEqual(len(PARENT_ERA14_SEAL_HASH), 64)
        # Check that parent seal hash is non-empty and hexadecimal
        int(PARENT_ERA14_SEAL_HASH, 16)

    def test_04_merkle_root_computation(self) -> None:
        leaves = ["hash1", "hash2", "hash3"]
        root = self.nexus._compute_merkle_root(leaves)
        self.assertEqual(len(root), 64)

        # Consistency
        root2 = self.nexus._compute_merkle_root(leaves)
        self.assertEqual(root, root2)

    def test_05_verify_era15_integrity(self) -> None:
        cert = self.nexus.verify_era15_integrity(force_refresh=True)
        self.assertIsInstance(cert, Era15SealCertificate)
        self.assertTrue(cert.seal_id.startswith("SEAL-ERA15-"))
        self.assertEqual(cert.total_stages_sealed, 10)
        self.assertEqual(cert.integrity_status, "VERIFIED_SOVEREIGN")
        self.assertEqual(cert.creator, "Senin")
        self.assertEqual(cert.creator_full_name, "Senin Ali K P")
        self.assertTrue(cert.total_source_lines > 2000)
        self.assertTrue(cert.total_test_lines > 1000)

        # Ensure all 10 modules verified
        for m in cert.modules:
            self.assertTrue(m["is_verified"], f"Stage {m['stage']} failed verification!")
            self.assertTrue(len(m["source_sha256"]) == 64)
            self.assertTrue(len(m["test_sha256"]) == 64)

    def test_06_seal_persistence_and_loading(self) -> None:
        cert = self.nexus.verify_era15_integrity(force_refresh=True)
        self.assertTrue(self.nexus.seal_file.exists())

        raw_data = json.loads(self.nexus.seal_file.read_text(encoding="utf-8"))
        self.assertEqual(raw_data["seal_id"], cert.seal_id)
        self.assertEqual(raw_data["merkle_root"], cert.merkle_root)

    def test_07_autonomous_compiler_cycle_execution(self) -> None:
        cycle = self.nexus.run_compiler_cycle()
        self.assertIsInstance(cycle, CompilerCycleResult)
        self.assertTrue(cycle.success)
        self.assertEqual(cycle.pipeline_stages_executed, 9)
        self.assertTrue(cycle.binary_size_bytes > 512)
        self.assertEqual(cycle.binary_format, "PE")

    def test_08_compiler_cycle_result_integrity(self) -> None:
        cycle = self.nexus.run_compiler_cycle()
        self.assertTrue(cycle.duration_ms >= 0)
        self.assertEqual(len(cycle.sha256_hash), 64)
        self.assertTrue(cycle.ir_instructions_lowered > 0)
        self.assertIn("Successfully executed", cycle.summary)

    def test_09_ascii_status_presentation(self) -> None:
        status = self.nexus.format_ascii_status()
        self.assertIn("LUCY STAGE 150", status)
        self.assertIn("SEAL-ERA15-", status)
        self.assertIn("Senin Ali K P", status)
        self.assertIn("VERIFIED_SOVEREIGN", status)
        for stage_num in range(141, 151):
            self.assertIn(str(stage_num), status)

    def test_10_ascii_cycle_presentation(self) -> None:
        cycle = self.nexus.run_compiler_cycle()
        tbl = self.nexus.format_ascii_cycle_table(cycle)
        self.assertIn("AUTONOMOUS COMPILER CYCLE:", tbl)
        self.assertIn("PE", tbl)
        self.assertIn("SUCCESS", tbl)


if __name__ == "__main__":
    unittest.main()
