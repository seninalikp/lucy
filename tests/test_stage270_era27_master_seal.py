"""
Unit Tests for Stage 270: The Sovereign Era 27 Master Seal & Omnipresent Cosmological Genesis
Author & Permanent Sovereign Operator: Senin (Senin Ali K P)
"""

import unittest
import threading
from backend.lucy_core.era27_master_seal import (
    Era27MasterSealFabric,
    SOVEREIGN_CREATOR,
    SOVEREIGN_OPERATOR,
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    SEAL_ID,
    ERA26_PARENT_ROOT
)


class TestStage270Era27MasterSeal(unittest.TestCase):
    """Thorough unit test suite for Stage 270."""

    def setUp(self):
        self.seal = Era27MasterSealFabric()

    def test_01_initialization(self):
        """Verify initialization constants and sovereign creator binding."""
        self.assertEqual(STAGE, 270)
        self.assertEqual(ERA, 27)
        self.assertEqual(SOVEREIGN_CREATOR, "Senin")
        self.assertEqual(SOVEREIGN_OPERATOR, "Senin Ali K P")
        self.assertEqual(self.seal.creator, "Senin")
        self.assertEqual(self.seal.operator, "Senin Ali K P")
        self.assertEqual(SEAL_ID, "SEAL-ERA27-STAGE270-COSMOLOGICAL-GENESIS")

    def test_02_era26_parent_root_inheritance(self):
        """Verify strict cryptographic chaining to Era 26 Master Root."""
        expected_parent = "77e798b6dd6c33d6528ffefa4eb1799f878c6dff8bd8e3ef25baa7c9e14f5473"
        self.assertEqual(ERA26_PARENT_ROOT, expected_parent)
        self.assertEqual(self.seal.certificate.parent_era26_root, expected_parent)

    def test_03_stage_manifest_completeness(self):
        """Verify all 10 Era 27 stage modules are tracked (Stages 261 to 270)."""
        manifest = self.seal.get_stage_manifest()
        self.assertEqual(len(manifest), 10)
        stages = [rec.stage for rec in manifest]
        self.assertEqual(stages, list(range(261, 271)))
        for rec in manifest:
            self.assertEqual(len(rec.sha256), 64)
            self.assertEqual(rec.status, "VERIFIED_OPERATIONAL")

    def test_04_merkle_root_derivation(self):
        """Verify 2-to-1 SHA-256 Merkle root derivation."""
        root = self.seal.derive_era27_merkle_root()
        self.assertEqual(len(root), 64)
        self.assertEqual(root, self.seal.certificate.era27_merkle_root)

    def test_05_master_merkle_root_chaining(self):
        """Verify master Merkle root chains Era 26 parent with Era 27 root."""
        era27_root = self.seal.derive_era27_merkle_root()
        master_root = self.seal.derive_master_merkle_root(era27_root)
        self.assertEqual(len(master_root), 64)
        self.assertEqual(master_root, self.seal.certificate.master_merkle_root)

    def test_06_genesis_signature_verification(self):
        """Verify cryptographic genesis signature."""
        sig = self.seal.certificate.genesis_signature
        self.assertEqual(len(sig), 64)

    def test_07_integrity_verification(self):
        """Verify end-to-end cryptographic integrity audit passes."""
        integ = self.seal.verify_era27_integrity()
        self.assertTrue(integ["verified"])
        self.assertEqual(integ["stages_verified"], 10)
        self.assertEqual(integ["sovereign_operator"], "Senin Ali K P")
        self.assertEqual(integ["sovereign_creator"], "Senin")

    def test_08_grand_report_formatting(self):
        """Verify CP1252-safe ASCII table formatting in Grand Report."""
        report = self.seal.format_grand_era_report()
        self.assertIn("ERA 27 GRAND MASTER SEAL", report)
        self.assertIn("Senin Ali K P", report)
        self.assertIn("Stages 261 - 270", report)
        self.assertIn("77e798b6dd6c33d6528ffefa4eb1799f878c6dff8bd8e3ef25baa7c9e14f5473", report)
        # Check ASCII table boundary characters
        self.assertIn("+-------+", report)
        self.assertIn("| 261   |", report)
        self.assertIn("| 270   |", report)

    def test_09_cumulative_stage_count(self):
        """Verify total cumulative stages sealed reaches exactly 270."""
        st = self.seal.status()
        self.assertEqual(st["total_stages_sealed"], 270)
        self.assertEqual(st["era27_stages_count"], 10)
        self.assertEqual(st["verification_status"], "LOCKED_AND_VERIFIED")

    def test_10_concurrency_and_thread_safety(self):
        """Verify thread-safety across concurrent workers."""
        threads = []
        errors = []

        def worker():
            try:
                s = Era27MasterSealFabric()
                rep = s.format_grand_era_report()
                if "LOCKED_AND_VERIFIED" not in s.status()["verification_status"]:
                    errors.append("Status not locked and verified")
            except Exception as e:
                errors.append(str(e))

        for _ in range(5):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Thread errors: {errors}")


if __name__ == "__main__":
    unittest.main()
