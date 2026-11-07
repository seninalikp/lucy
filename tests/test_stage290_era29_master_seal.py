"""
Unit Tests for Stage 290: The Sovereign Era 29 Master Seal & Omniscient Trans-Cosmic Singularity Genesis
Sovereign Architect: Senin (Senin Ali K P)
"""

import unittest
import threading
from backend.lucy_core.era29_master_seal import (
    Era29MasterSealFabric,
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    SOVEREIGN_CREATOR,
    SOVEREIGN_OPERATOR,
    SEAL_ID,
    ERA28_PARENT_ROOT,
)


class TestStage290Era29MasterSeal(unittest.TestCase):

    def setUp(self):
        self.fabric = Era29MasterSealFabric()

    def test_01_initialization_and_metadata(self):
        st = self.fabric.status()
        self.assertEqual(st["stage"], 290)
        self.assertEqual(st["stage_name"], STAGE_NAME)
        self.assertEqual(st["era"], 29)
        self.assertEqual(st["era_name"], ERA_NAME)
        self.assertEqual(st["sovereign_creator"], SOVEREIGN_CREATOR)
        self.assertEqual(st["sovereign_operator"], SOVEREIGN_OPERATOR)
        self.assertEqual(st["seal_id"], SEAL_ID)
        self.assertEqual(st["total_stages_sealed"], 290)
        self.assertEqual(st["verification_status"], "SEALED_AND_VERIFIED")

    def test_02_inherited_era28_root_binding(self):
        st = self.fabric.status()
        self.assertEqual(st["parent_era28_root"], ERA28_PARENT_ROOT)
        self.assertEqual(st["parent_era28_root"], "165f8b9f71c3b79aa68b28ef734eb11156a65b6d7e8d7d7a73e667f041fd8a5e")

    def test_03_stage_manifest_completeness(self):
        manifest = self.fabric.get_stage_manifest()
        self.assertEqual(len(manifest), 10)
        expected_stages = list(range(281, 291))
        actual_stages = [r.stage for r in manifest]
        self.assertEqual(actual_stages, expected_stages)

    def test_04_stage_hashes_sha256_format(self):
        manifest = self.fabric.get_stage_manifest()
        for rec in manifest:
            self.assertEqual(len(rec.sha256), 64)
            int(rec.sha256, 16) # Must be valid hex
            self.assertEqual(rec.status, "VERIFIED_OPERATIONAL")

    def test_05_merkle_root_reproducibility(self):
        root1 = self.fabric.derive_era29_merkle_root()
        root2 = self.fabric.derive_era29_merkle_root()
        self.assertEqual(root1, root2)
        self.assertEqual(len(root1), 64)

    def test_06_master_merkle_root_chaining(self):
        era29_root = self.fabric.derive_era29_merkle_root()
        master_root = self.fabric.derive_master_merkle_root(era29_root)
        self.assertEqual(master_root, self.fabric.certificate.master_merkle_root)
        self.assertNotEqual(master_root, era29_root)
        self.assertNotEqual(master_root, ERA28_PARENT_ROOT)

    def test_07_genesis_signature_cryptographic_lock(self):
        sig = self.fabric.certificate.genesis_signature
        self.assertEqual(len(sig), 64)
        int(sig, 16)
        # Verify signature changes if operator changes
        fab_tamper = Era29MasterSealFabric()
        fab_tamper.operator = "Impostor"
        integ = fab_tamper.verify_era29_integrity()
        self.assertFalse(integ["verified"])

    def test_08_full_integrity_audit(self):
        audit = self.fabric.verify_era29_integrity()
        self.assertTrue(audit["verified"])
        self.assertEqual(audit["stages_verified"], 10)
        self.assertEqual(audit["status"], "LOCKED_AND_VERIFIED")
        self.assertEqual(audit["sovereign_creator"], SOVEREIGN_CREATOR)
        self.assertEqual(audit["sovereign_operator"], SOVEREIGN_OPERATOR)

    def test_09_multithreaded_concurrency(self):
        results = []

        def worker():
            audit = self.fabric.verify_era29_integrity()
            results.append(audit["verified"])

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), 10)
        self.assertTrue(all(results))

    def test_10_ascii_formatting_and_cp1252_encoding(self):
        table = self.fabric.format_ascii_status()
        report = self.fabric.format_grand_era_report()
        self.assertIn("STAGE 290", table)
        self.assertIn("SENIN ALI K P", table.upper())
        self.assertIn("SENIN", table.upper())
        self.assertIn("SEAL-ERA29-STAGE290-TRANS-COSMIC-GENESIS", table)
        self.assertIn("ERA 29 STAGE MANIFEST AUDIT", report)
        # CP1252 byte-safety test
        table_bytes = table.encode("cp1252")
        report_bytes = report.encode("cp1252")
        self.assertIsInstance(table_bytes, bytes)
        self.assertIsInstance(report_bytes, bytes)


if __name__ == "__main__":
    unittest.main()
