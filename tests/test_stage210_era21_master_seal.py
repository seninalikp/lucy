r"""
tests/test_stage210_era21_master_seal.py
Stage 210: Era 21 Sovereign Master Seal & Hyper-Federation Genesis
Era 21: Autonomous Hyper-Scale Multi-Kernel Federation, Quantum-Resistant Keys & Post-Singularity Architecture
"""

import unittest
from backend.lucy_core.era21_master_seal import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    SOVEREIGN_CREATOR,
    SOVEREIGN_OPERATOR,
    ERA21_SEAL_ID,
    STAGE200_BICENTENNIAL_ROOT,
    Era21Certificate,
    Era21MasterSealFabric,
)


class TestStage210Era21MasterSeal(unittest.TestCase):
    """10 Unit Tests for Stage 210 Era 21 Master Seal Fabric."""

    def setUp(self):
        self.fabric = Era21MasterSealFabric()

    def test_01_fabric_initialization(self):
        self.assertEqual(STAGE, 210)
        self.assertEqual(ERA, 21)
        self.assertEqual(self.fabric.creator, SOVEREIGN_CREATOR)
        self.assertEqual(self.fabric.operator, SOVEREIGN_OPERATOR)
        self.assertEqual(self.fabric.seal_id, ERA21_SEAL_ID)
        self.assertEqual(len(self.fabric.era21_stage_modules), 10)

    def test_02_certificate_generation(self):
        cert = self.fabric.certificate
        self.assertIsNotNone(cert)
        self.assertEqual(cert.seal_id, ERA21_SEAL_ID)
        self.assertEqual(cert.creator, SOVEREIGN_CREATOR)
        self.assertEqual(cert.operator, SOVEREIGN_OPERATOR)
        self.assertEqual(cert.total_stages, 210)
        self.assertEqual(cert.total_eras, 21)

    def test_03_stage200_parent_root_binding(self):
        cert = self.fabric.certificate
        self.assertEqual(cert.parent_bicentennial_root, STAGE200_BICENTENNIAL_ROOT)
        self.assertEqual(len(cert.parent_bicentennial_root), 64)

    def test_04_derive_era21_merkle_root_determinism(self):
        root1 = self.fabric.derive_era21_merkle_root()
        root2 = self.fabric.derive_era21_merkle_root()
        self.assertEqual(root1, root2)
        self.assertEqual(len(root1), 64)

    def test_05_derive_master_merkle_root(self):
        era21_root = self.fabric.derive_era21_merkle_root()
        master_root = self.fabric.derive_master_merkle_root(era21_root)
        self.assertIsInstance(master_root, str)
        self.assertEqual(len(master_root), 64)
        self.assertEqual(self.fabric.certificate.master_merkle_root, master_root)

    def test_06_verify_era21_integrity_valid(self):
        valid, details = self.fabric.verify_era21_integrity()
        self.assertTrue(valid)
        self.assertEqual(details["seal_id"], ERA21_SEAL_ID)
        self.assertEqual(details["creator"], SOVEREIGN_CREATOR)
        self.assertEqual(details["operator"], SOVEREIGN_OPERATOR)

    def test_07_tamper_detection_creator(self):
        # Mutate creator -> verification must fail
        self.fabric.creator = "Unauthorized Impostor"
        valid, _ = self.fabric.verify_era21_integrity()
        self.assertFalse(valid)

    def test_08_tamper_detection_signature(self):
        # Tamper signature on certificate -> verification must fail
        self.fabric.certificate.genesis_signature = "0" * 64
        valid, _ = self.fabric.verify_era21_integrity()
        self.assertFalse(valid)

    def test_09_stage_manifest_completeness(self):
        manifest = self.fabric.get_stage_manifest()
        self.assertEqual(len(manifest), 10)
        stages = [m.stage for m in manifest]
        self.assertEqual(stages, list(range(201, 211)))
        for rec in manifest:
            self.assertEqual(len(rec.sha256), 64)
            self.assertEqual(rec.status, "VERIFIED")

    def test_10_ascii_status_and_grand_report(self):
        status_tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 210: ERA 21 SOVEREIGN MASTER SEAL & HYPER-FEDERATION", status_tbl)
        self.assertIn("Completed Stages      : 210 / 210 Stages Fully Verified", status_tbl)

        report_tbl = self.fabric.format_grand_era_report()
        self.assertIn("LUCY AGI - ERA 21 SOVEREIGN HYPER-FEDERATION MASTER AUDIT", report_tbl)
        self.assertIn("Autonomous Multi-Kernel Federation Bus", report_tbl)
        self.assertIn("Autonomous Hyper-Scale Cluster Mesh Synchronizer", report_tbl)


if __name__ == "__main__":
    unittest.main()
