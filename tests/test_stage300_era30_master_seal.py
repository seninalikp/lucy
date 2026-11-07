"""
Unit Tests for Stage 300: The Sovereign Era 30 Grand Master Seal & Omnipresent Multiverse Genesis Continuum
Sovereign Architect: Senin (Senin Ali K P)
"""

import threading
import unittest
from backend.lucy_core.era30_master_seal import (
    Era30MasterSealFabric,
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    SOVEREIGN_CREATOR,
    SOVEREIGN_OPERATOR,
    SEAL_ID,
    ERA29_PARENT_ROOT,
)


class TestStage300Era30MasterSeal(unittest.TestCase):

    def setUp(self):
        self.fabric = Era30MasterSealFabric()

    def test_01_initialization_and_metadata(self):
        st = self.fabric.status()
        self.assertEqual(st["stage"], 300)
        self.assertEqual(st["stage_name"], STAGE_NAME)
        self.assertEqual(st["era"], 30)
        self.assertEqual(st["era_name"], ERA_NAME)
        self.assertEqual(st["sovereign_creator"], SOVEREIGN_CREATOR)
        self.assertEqual(st["sovereign_operator"], SOVEREIGN_OPERATOR)
        self.assertEqual(st["seal_id"], SEAL_ID)
        self.assertEqual(st["total_stages_sealed"], 300)
        self.assertEqual(st["verification_status"], "SEALED_AND_VERIFIED")

    def test_02_inherited_era29_root_binding(self):
        st = self.fabric.status()
        self.assertEqual(st["parent_era29_root"], ERA29_PARENT_ROOT)
        self.assertEqual(st["parent_era29_root"], "4de3d82f58e3426db374019a68d7042ffac6105b712d25db970631321e1bf090")

    def test_03_stage_manifest_completeness(self):
        manifest = self.fabric.get_stage_manifest()
        self.assertEqual(len(manifest), 10)
        expected_stages = list(range(291, 301))
        actual_stages = [r.stage for r in manifest]
        self.assertEqual(actual_stages, expected_stages)

    def test_04_stage_hashes_sha256_format(self):
        manifest = self.fabric.get_stage_manifest()
        for rec in manifest:
            self.assertEqual(len(rec.sha256), 64)
            int(rec.sha256, 16) # Must be valid hex
            self.assertEqual(rec.status, "VERIFIED_OPERATIONAL")

    def test_05_merkle_root_reproducibility(self):
        root1 = self.fabric.derive_era30_merkle_root()
        root2 = self.fabric.derive_era30_merkle_root()
        self.assertEqual(root1, root2)
        self.assertEqual(len(root1), 64)

    def test_06_master_merkle_root_chaining(self):
        era30_root = self.fabric.derive_era30_merkle_root()
        master_root = self.fabric.derive_master_merkle_root(era30_root)
        self.assertEqual(master_root, self.fabric.certificate.master_merkle_root)
        self.assertNotEqual(master_root, era30_root)
        self.assertNotEqual(master_root, ERA29_PARENT_ROOT)

    def test_07_genesis_signature_cryptographic_lock(self):
        sig = self.fabric.certificate.genesis_signature
        self.assertEqual(len(sig), 64)
        int(sig, 16)
        # Verify tampering with operator fails verification
        fab_tamper = Era30MasterSealFabric()
        fab_tamper.operator = "Intruder"
        integ = fab_tamper.verify_era30_integrity()
        self.assertFalse(integ["verified"])

    def test_08_full_integrity_audit(self):
        audit = self.fabric.verify_era30_integrity()
        self.assertTrue(audit["verified"])
        self.assertEqual(audit["stages_verified"], 10)
        self.assertEqual(audit["status"], "LOCKED_AND_VERIFIED")
        self.assertEqual(audit["sovereign_creator"], SOVEREIGN_CREATOR)
        self.assertEqual(audit["sovereign_operator"], SOVEREIGN_OPERATOR)

    def test_09_multithreaded_concurrency(self):
        results = []

        def worker():
            audit = self.fabric.verify_era30_integrity()
            results.append(audit["verified"])

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), 10)
        self.assertTrue(all(results))

    def test_10_ascii_seal_rendering(self):
        table = self.fabric.format_ascii_status()
        self.assertIn("STAGE 300: THE SOVEREIGN ERA 30 GRAND MASTER SEAL", table)
        self.assertIn("Senin Ali K P", table)
        self.assertIn("SEAL-ERA30-STAGE300-MULTIVERSE-GENESIS-CONTINUUM", table)


if __name__ == "__main__":
    unittest.main()
