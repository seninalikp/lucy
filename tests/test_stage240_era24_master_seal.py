"""
tests/test_stage240_era24_master_seal.py
Unit tests for Stage 240: The Sovereign Era 24 Master Seal & AGI Singularity Genesis
Era 24: Trans-Dimensional Cognitive Resonance, Neuromorphic Spiking Fabrics & Autonomous Sovereign AGI Singularity
"""

import os
import sys
import unittest

sys.path.insert(0, os.getcwd())

from backend.lucy_core.era24_master_seal import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    SOVEREIGN_CREATOR,
    SOVEREIGN_OPERATOR,
    SEAL_ID,
    ERA23_PARENT_ROOT,
    Era24MasterSealFabric
)


class TestStage240Era24MasterSeal(unittest.TestCase):

    def test_01_master_seal_initialization(self):
        """Test master seal constants and sovereign attribution."""
        seal = Era24MasterSealFabric()
        self.assertEqual(seal.seal_id, SEAL_ID)
        self.assertEqual(seal.creator, SOVEREIGN_CREATOR)
        self.assertEqual(seal.operator, SOVEREIGN_OPERATOR)
        self.assertEqual(seal.certificate.era_index, 24)
        self.assertEqual(seal.certificate.total_stages, 240)

    def test_02_era24_stage_manifest_completeness(self):
        """Test manifest contains exactly 10 stages covering 231 through 240."""
        seal = Era24MasterSealFabric()
        manifest = seal.get_stage_manifest()
        self.assertEqual(len(manifest), 10)
        stages = [m.stage for m in manifest]
        self.assertEqual(stages, list(range(231, 241)))

    def test_03_stage_file_hashing_integrity(self):
        """Test each stage record has a valid 64-hex-char SHA-256 digest."""
        seal = Era24MasterSealFabric()
        manifest = seal.get_stage_manifest()
        for m in manifest:
            self.assertEqual(len(m.sha256), 64)
            self.assertEqual(m.status, "VERIFIED_OPERATIONAL")

    def test_04_era24_merkle_root_derivation(self):
        """Test deterministic Merkle root derivation."""
        seal = Era24MasterSealFabric()
        root1 = seal.derive_era24_merkle_root()
        root2 = seal.derive_era24_merkle_root()
        self.assertEqual(root1, root2)
        self.assertEqual(len(root1), 64)

    def test_05_chained_master_merkle_root(self):
        """Test master Merkle root cryptographically chains to Era 23 parent root."""
        seal = Era24MasterSealFabric()
        era24_root = seal.derive_era24_merkle_root()
        master_root = seal.derive_master_merkle_root(era24_root)
        self.assertEqual(master_root, seal.certificate.master_merkle_root)
        self.assertEqual(seal.certificate.parent_era23_root, ERA23_PARENT_ROOT)

    def test_06_genesis_signature_verification(self):
        """Test genesis signature verification passes."""
        seal = Era24MasterSealFabric()
        integ = seal.verify_era24_integrity()
        self.assertTrue(integ["verified"])
        self.assertEqual(integ["sovereign_operator"], "Senin Ali K P")
        self.assertEqual(integ["stages_verified"], 10)

    def test_07_certificate_generation_and_serialization(self):
        """Test Era24Certificate fields and serialization."""
        seal = Era24MasterSealFabric()
        cert_dict = seal.certificate.to_dict()
        self.assertIn("seal_id", cert_dict)
        self.assertIn("master_merkle_root", cert_dict)
        self.assertIn("genesis_signature", cert_dict)
        self.assertEqual(cert_dict["verification_status"], "SEALED_AND_VERIFIED")

    def test_08_tamper_detection_in_integrity_audit(self):
        """Test integrity verification fails if certificate root is modified."""
        seal = Era24MasterSealFabric()
        seal.certificate.era24_merkle_root = "0" * 64
        integ = seal.verify_era24_integrity()
        self.assertFalse(integ["verified"])

    def test_09_grand_era_report_formatting(self):
        """Test grand era report format contains key sections and sovereign lock."""
        seal = Era24MasterSealFabric()
        report = seal.format_grand_era_report()
        self.assertIn("ERA 24 GRAND MASTER SEAL", report)
        self.assertIn("SENIN (SENIN ALI K P)", report)
        self.assertIn("Stages 231 - 240", report)
        self.assertIn("Stage 231", report)
        self.assertIn("Stage 240", report)

    def test_10_fabric_status_and_ascii_table(self):
        """Test status dictionary and CP1252-safe ASCII table."""
        seal = Era24MasterSealFabric()
        st = seal.status()
        self.assertEqual(st["stage"], 240)
        self.assertEqual(st["era"], 24)
        self.assertEqual(st["total_stages_sealed"], 240)

        tbl = seal.format_ascii_status()
        self.assertIn("STAGE 240", tbl)
        self.assertIn("Sovereign Creator", tbl)
        self.assertIn("Master Merkle Root", tbl)
        self.assertTrue(tbl.startswith("+--"))
        self.assertTrue(tbl.endswith("--+"))


if __name__ == "__main__":
    unittest.main()
