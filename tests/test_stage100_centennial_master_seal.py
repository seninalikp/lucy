"""
tests/test_stage100_centennial_master_seal.py
Stage 100: Centennial Sovereign Master Seal & Cryptographic Self-Attestation Fabric Unit Tests
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.centennial_master_seal import (
    CANONICAL_STAGES,
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    STAGE,
    CentennialMasterSealEngine,
    CentennialSealCertificate,
    StageMilestone,
)


class MockReceiptLedger:
    def __init__(self):
        self.receipts = []

    def issue_receipt(self, action_category, operation, target, verified_outcome):
        rec = {
            "category": action_category,
            "operation": operation,
            "target": target,
            "outcome": verified_outcome,
        }
        self.receipts.append(rec)
        return rec


class TestStage100CentennialMasterSeal(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="lucy_stage100_test_")
        self.temp_path = Path(self.temp_dir)
        self.project_root = Path(__file__).resolve().parent.parent

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_constants_and_metadata(self):
        self.assertEqual(STAGE, 100)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")
        self.assertEqual(len(CANONICAL_STAGES), 100)
        self.assertEqual(CANONICAL_STAGES[0].stage_num, 1)
        self.assertEqual(CANONICAL_STAGES[99].stage_num, 100)

    def test_02_canonical_stages_integrity(self):
        # Verify 100 strictly consecutive numbered stages
        for idx, milestone in enumerate(CANONICAL_STAGES):
            expected_num = idx + 1
            self.assertEqual(milestone.stage_num, expected_num)
            self.assertTrue(len(milestone.codename) > 0)
            self.assertTrue(len(milestone.description) > 0)
            self.assertTrue(len(milestone.era) > 0)

        # Verify distinct eras
        eras = {m.era for m in CANONICAL_STAGES}
        self.assertEqual(len(eras), 10)
        self.assertIn("Era 10: Centennial Block", eras)

    def test_03_merkle_root_computation(self):
        engine = CentennialMasterSealEngine(
            project_root=self.project_root,
            data_dir=self.temp_path / "centennial",
        )
        merkle_root, file_count = engine._compute_merkle_root()
        self.assertEqual(len(merkle_root), 64)
        self.assertGreater(file_count, 50)

        # Deterministic
        merkle_root_2, file_count_2 = engine._compute_merkle_root()
        self.assertEqual(merkle_root, merkle_root_2)
        self.assertEqual(file_count, file_count_2)

    def test_04_master_seal_generation(self):
        ledger = MockReceiptLedger()
        engine = CentennialMasterSealEngine(
            project_root=self.project_root,
            receipt_ledger=ledger,
            data_dir=self.temp_path / "centennial",
        )
        cert = engine.generate_seal()

        self.assertIsInstance(cert, CentennialSealCertificate)
        self.assertTrue(cert.seal_id.startswith("seal_"))
        self.assertEqual(cert.creator, "Senin")
        self.assertEqual(cert.creator_full_name, "Senin Ali K P")
        self.assertEqual(cert.total_stages_sealed, 100)
        self.assertGreater(cert.codebase_files_count, 50)
        self.assertEqual(len(cert.merkle_root_sha256), 64)
        self.assertEqual(len(cert.master_seal_signature), 64)
        self.assertEqual(cert.verification_status, "CERTIFIED_VALID")
        self.assertIn("Senin Ali K P", cert.sovereignty_attestation)
        self.assertIn("100", cert.sovereignty_attestation)

        # Check receipt
        self.assertEqual(len(ledger.receipts), 1)
        self.assertEqual(ledger.receipts[0]["category"], "CENTENNIAL_MASTER_SEAL")

    def test_05_seal_verification_valid(self):
        engine = CentennialMasterSealEngine(
            project_root=self.project_root,
            data_dir=self.temp_path / "centennial",
        )
        engine.generate_seal()
        res = engine.verify_seal()

        self.assertTrue(res["valid"])
        self.assertEqual(res["status"], "VERIFIED_VALID")
        self.assertTrue(res["creator_intact"])
        self.assertEqual(res["sealed_merkle_root"], res["current_merkle_root"])

    def test_06_seal_verification_tamper_detection(self):
        engine = CentennialMasterSealEngine(
            project_root=self.project_root,
            data_dir=self.temp_path / "centennial",
        )
        cert = engine.generate_seal()

        # Simulate tamper by mutating the stored certificate merkle root
        cert.merkle_root_sha256 = "0000000000000000000000000000000000000000000000000000000000000000"
        engine._save_seal(cert)
        engine.last_certificate = cert

        res = engine.verify_seal()
        self.assertFalse(res["valid"])
        self.assertEqual(res["status"], "MUTATION_DETECTED")

    def test_07_centennial_banner_rendering(self):
        engine = CentennialMasterSealEngine(
            project_root=self.project_root,
            data_dir=self.temp_path / "centennial",
        )
        banner = engine.get_centennial_banner()
        self.assertIn("L U C Y   O S   C E N T E N N I A L", banner)
        self.assertIn("100 / 100 STAGES COMPLETED & SEALED", banner)
        self.assertIn("Senin Ali K P", banner)
        self.assertIn("Centennial Block (91-100)", banner)
        # Verify CP1252 compatibility
        banner.encode("cp1252")

    def test_08_terminal_summary_rendering(self):
        engine = CentennialMasterSealEngine(
            project_root=self.project_root,
            data_dir=self.temp_path / "centennial",
        )
        cert = engine.generate_seal()
        summary = cert.format_terminal_summary()
        self.assertIn("LUCY OS - CENTENNIAL SOVEREIGN MASTER SEAL", summary)
        self.assertIn("STAGE 100 / 100 MILESTONE CONVERGENCE", summary)
        self.assertIn("Senin", summary)
        summary.encode("cp1252")

    def test_09_engine_status(self):
        engine = CentennialMasterSealEngine(
            project_root=self.project_root,
            data_dir=self.temp_path / "centennial",
        )
        st_pre = engine.status()
        self.assertEqual(st_pre["stage"], 100)
        self.assertEqual(st_pre["total_stages"], 100)
        self.assertEqual(st_pre["creator"], "Senin")

        engine.generate_seal()
        st_post = engine.status()
        self.assertTrue(st_post["seal_present"])
        self.assertEqual(st_post["verification_status"], "CERTIFIED_VALID")

    def test_10_stage_milestone_dict(self):
        m = CANONICAL_STAGES[99]
        d = m.to_dict()
        self.assertEqual(d["stage_num"], 100)
        self.assertEqual(d["codename"], "Centennial Sovereign Master Seal")
        self.assertEqual(d["era"], "Era 10: Centennial Block")


if __name__ == "__main__":
    unittest.main()
