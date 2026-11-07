r"""
tests/test_stage140_era14_master_seal.py
Unit tests for Stage 140: Sovereign Singularity Nexus & Era 14 Master Seal.
Era 14: Autonomous Code Evolution, Semantic Mutation & Static Synthesis
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.era14_master_seal import (
    CANONICAL_ERA14_MODULES,
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    ERA_NAME,
    STAGE,
    STAGE_NAME,
    Era14MasterSealNexus,
    Era14SealCertificate,
    EvolutionCycleResult,
)


class TestStage140Era14MasterSeal(unittest.TestCase):
    def setUp(self):
        # We point project_root to real repo root so it can inspect all 10 modules
        self.repo_root = Path(__file__).resolve().parent.parent
        self.test_dir = tempfile.mkdtemp()
        self.nexus = Era14MasterSealNexus(
            project_root=self.repo_root,
            data_dir=Path(self.test_dir) / "seals",
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_metadata_and_constants(self):
        self.assertEqual(STAGE, 140)
        self.assertEqual(ERA, 14)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")
        self.assertEqual(len(CANONICAL_ERA14_MODULES), 10)
        self.assertEqual(CANONICAL_ERA14_MODULES[0][0], 131)
        self.assertEqual(CANONICAL_ERA14_MODULES[-1][0], 140)

    def test_02_merkle_root_computation(self):
        empty_root = self.nexus.compute_merkle_root([])
        self.assertEqual(len(empty_root), 64)

        hashes = ["a" * 64, "b" * 64, "c" * 64]
        root = self.nexus.compute_merkle_root(hashes)
        self.assertEqual(len(root), 64)
        # Deterministic
        self.assertEqual(root, self.nexus.compute_merkle_root(hashes))

    def test_03_generate_master_seal_certificate(self):
        cert = self.nexus.generate_era14_master_seal(force=True)
        self.assertIsInstance(cert, Era14SealCertificate)
        self.assertTrue(cert.seal_id.startswith("SEAL-ERA14-"))
        self.assertEqual(cert.era, 14)
        self.assertEqual(cert.total_stages_sealed, 10)
        self.assertEqual(len(cert.merkle_root), 64)
        self.assertGreater(cert.total_source_lines, 2000)
        self.assertGreater(cert.total_test_lines, 800)

    def test_04_chain_parent_era13_hash(self):
        cert = self.nexus.generate_era14_master_seal(force=True)
        self.assertEqual(cert.parent_era13_seal_hash, "0a65c26dd94f2d53b9690050322ded11f9e4398840c3c172cb1300130f46de5c")

    def test_05_all_canonical_modules_verified(self):
        cert = self.nexus.generate_era14_master_seal(force=True)
        self.assertEqual(cert.integrity_status, "VERIFIED_SOVEREIGN")
        for m in cert.modules:
            self.assertTrue(m["is_verified"])
            self.assertGreater(m["source_lines"], 10)
            self.assertEqual(len(m["source_sha256"]), 64)

    def test_06_verify_era14_manifest(self):
        manifest = self.nexus.verify_era14_manifest()
        self.assertTrue(manifest["is_valid"])
        self.assertEqual(manifest["total_modules"], 10)
        self.assertEqual(manifest["creator"], "Senin Ali K P")
        self.assertGreater(manifest["total_source_lines"], 2500)

    def test_07_persistence_and_cache_loading(self):
        cert = self.nexus.generate_era14_master_seal(force=True)
        seal_file = Path(self.test_dir) / "seals" / "era14_master_seal.json"
        self.assertTrue(seal_file.exists())

        nexus2 = Era14MasterSealNexus(
            project_root=self.repo_root,
            data_dir=Path(self.test_dir) / "seals",
        )
        st = nexus2.status()
        self.assertEqual(st["seal_id"], cert.seal_id)
        self.assertEqual(st["merkle_root"], cert.merkle_root)

    def test_08_autonomous_evolution_cycle(self):
        res = self.nexus.run_evolution_cycle("test_evolution_run")
        self.assertIsInstance(res, EvolutionCycleResult)
        self.assertTrue(res.success)
        self.assertGreaterEqual(res.subsystems_active, 5)
        self.assertGreater(len(res.steps_executed), 4)

    def test_09_ascii_status_and_cycle_tables(self):
        tbl = self.nexus.format_era14_status_table()
        self.assertIn("+=============================================================================+", tbl)
        self.assertIn("SOVEREIGN SINGULARITY NEXUS & ERA 14 MASTER SEAL [STAGE 140 | ERA 14]", tbl)
        self.assertIn("CANONICAL ERA 14 MODULE ATTESTATION MATRIX (STAGES 131 - 140)", tbl)
        self.assertIn("Senin Ali K P", tbl)

        res = self.nexus.run_evolution_cycle("matrix_test")
        c_tbl = self.nexus.format_cycle_result_table(res)
        self.assertIn("AUTONOMOUS CODE EVOLUTION CYCLE:", c_tbl)
        self.assertIn("PIPELINE EXECUTION STEPS", c_tbl)

    def test_10_sovereign_operator_attestation(self):
        st = self.nexus.status()
        self.assertEqual(st["creator"], "Senin Ali K P")
        self.assertEqual(st["era_name"], "Autonomous Code Evolution, Semantic Mutation & Static Synthesis")


if __name__ == "__main__":
    unittest.main()
