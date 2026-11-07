r"""
tests/test_stage120_era12_master_seal.py
Unit tests for Stage 120: Sovereign Singularity Nexus & Era 12 Master Seal (Era 12).
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.era12_master_seal import (
    Era12MasterSealNexus,
    Era12SealCertificate,
    ModuleIntegrityRecord,
    CognitivePulseResult,
    STAGE,
    ERA,
    ERA_NAME,
    STAGE_NAME,
    CREATOR_NAME,
    CREATOR_FULL_NAME,
    CANONICAL_ERA12_MODULES,
)


class MockReceiptLedger:
    def __init__(self):
        self.receipts = []

    def record_receipt(self, action_category: str, operation: str, target: str, verified_outcome: str):
        self.receipts.append({
            "action_category": action_category,
            "operation": operation,
            "target": target,
            "verified_outcome": verified_outcome,
        })


class MockIPCBus:
    def __init__(self):
        self.events = []

    def publish(self, topic: str, payload: dict):
        self.events.append({"topic": topic, "payload": payload})


class TestStage120Era12MasterSeal(unittest.TestCase):
    def setUp(self):
        self.real_root = Path(__file__).resolve().parent.parent
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_test_stage120_"))
        self.data_dir = self.test_dir / "data" / "lucy" / "seals"
        self.ledger = MockReceiptLedger()
        self.ipc = MockIPCBus()
        self.nexus = Era12MasterSealNexus(
            project_root=self.real_root,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
            ipc_bus=self.ipc,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_metadata_and_constants(self):
        self.assertEqual(STAGE, 120)
        self.assertEqual(ERA, 12)
        self.assertEqual(STAGE_NAME, "Sovereign Singularity Nexus & Era 12 Master Seal")
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")
        self.assertEqual(len(CANONICAL_ERA12_MODULES), 10)

        # Check canonical module ranges
        stages = [m[0] for m in CANONICAL_ERA12_MODULES]
        self.assertEqual(stages, list(range(111, 121)))

    def test_02_merkle_root_computation(self):
        # Empty tree fallback
        empty_root = self.nexus.compute_merkle_root([])
        self.assertEqual(len(empty_root), 64)

        # Single hash
        h1 = "a" * 64
        self.assertEqual(self.nexus.compute_merkle_root([h1]), h1)

        # Deterministic multi-hash Merkle tree
        h2 = "b" * 64
        m_root = self.nexus.compute_merkle_root([h1, h2])
        self.assertEqual(len(m_root), 64)
        # Invariant: identical inputs produce identical root
        self.assertEqual(self.nexus.compute_merkle_root([h1, h2]), m_root)

    def test_03_generate_era12_master_seal(self):
        cert = self.nexus.generate_era12_master_seal(force=True)
        self.assertIsInstance(cert, Era12SealCertificate)
        self.assertTrue(cert.seal_id.startswith("SEAL-ERA12-"))
        self.assertEqual(cert.era, 12)
        self.assertEqual(cert.creator, "Senin")
        self.assertEqual(cert.creator_full_name, "Senin Ali K P")
        self.assertEqual(cert.total_stages_sealed, 10)
        self.assertEqual(len(cert.merkle_root), 64)
        self.assertEqual(len(cert.modules), 10)
        self.assertGreater(cert.total_source_lines, 1000)
        self.assertEqual(cert.integrity_status, "VERIFIED_SOVEREIGN")

        # Check receipt
        rec_cats = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("ERA12_SEAL_GENERATED", rec_cats)

        # Check IPC event published
        topics = [e["topic"] for e in self.ipc.events]
        self.assertIn("lucy/era12/sealed", topics)

    def test_04_seal_persistence_and_reload(self):
        cert1 = self.nexus.generate_era12_master_seal(force=True)
        seal_file = self.data_dir / "era12_master_seal.json"
        self.assertTrue(seal_file.exists())

        # Instantiate fresh nexus pointing to same directory
        fresh_nexus = Era12MasterSealNexus(
            project_root=self.real_root,
            data_dir=self.data_dir,
        )
        st = fresh_nexus.status()
        self.assertEqual(st["seal_id"], cert1.seal_id)
        self.assertEqual(st["merkle_root"], cert1.merkle_root)
        self.assertEqual(st["stages_sealed"], 10)

    def test_05_verify_era12_integrity(self):
        is_valid, msg, details = self.nexus.verify_era12_integrity()
        self.assertTrue(is_valid)
        self.assertIn("verified", msg.lower())
        self.assertEqual(details["total_stages_sealed"], 10)

        # Check receipt
        rec_cats = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("ERA12_SEAL_VERIFIED", rec_cats)

    def test_06_run_cognitive_cycle(self):
        result = self.nexus.run_cognitive_cycle("Test Cognitive Pulse")
        self.assertIsInstance(result, CognitivePulseResult)
        self.assertTrue(result.cycle_id.startswith("cog_"))
        self.assertEqual(result.goal, "Test Cognitive Pulse")
        self.assertTrue(result.success)
        self.assertGreater(result.duration_ms, 0.0)
        self.assertGreaterEqual(len(result.steps_executed), 5)

        # Status tracking
        st = self.nexus.status()
        self.assertEqual(st["cognitive_cycles_run"], 1)

        # Check receipt
        rec_cats = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("COGNITIVE_CYCLE_EXECUTED", rec_cats)

    def test_07_ascii_tables_formatting(self):
        cert_tbl = self.nexus.format_seal_certificate_table()
        self.assertIn("LUCY OS - ERA 12 CRYPTOGRAPHIC MASTER SEAL", cert_tbl)
        self.assertIn("SEAL-ERA12-", cert_tbl)
        self.assertIn("Senin (Senin Ali K P)", cert_tbl)
        self.assertIn("Workspace Sensor Daemon", cert_tbl)
        self.assertIn("Era 12 Master Seal Nexus", cert_tbl)

        sing_tbl = self.nexus.format_singularity_status_table()
        self.assertIn("LUCY OS - COGNITIVE SINGULARITY NEXUS DASHBOARD", sing_tbl)
        self.assertIn("Era 12 (Stages 111-120)", sing_tbl)
        self.assertIn("VERIFIED & CRYPTOGRAPHICALLY SEALED", sing_tbl)

    def test_08_dataclass_serialization(self):
        r = ModuleIntegrityRecord(
            stage=120,
            name="Test Module",
            source_file="backend/lucy_core/test.py",
            test_file="tests/test_test.py",
            source_sha256="1" * 64,
            test_sha256="2" * 64,
            source_lines=100,
            test_lines=50,
            is_verified=True,
        )
        d = r.to_dict()
        self.assertEqual(d["stage"], 120)
        self.assertEqual(d["source_lines"], 100)

        pulse = CognitivePulseResult(
            cycle_id="cog_001",
            goal="Goal",
            timestamp=100.0,
            duration_ms=12.5,
            subsystems_active=8,
            steps_executed=["s1", "s2"],
            success=True,
            summary="Done",
        )
        pd = pulse.to_dict()
        self.assertEqual(pd["cycle_id"], "cog_001")
        self.assertEqual(pd["subsystems_active"], 8)

    def test_09_all_10_modules_exist_on_disk(self):
        lucy_core = self.real_root / "backend" / "lucy_core"
        tests = self.real_root / "tests"
        for stg, name, src_fname, tst_fname in CANONICAL_ERA12_MODULES:
            src = lucy_core / src_fname
            tst = tests / tst_fname
            self.assertTrue(src.exists(), f"Source missing: {src_fname} (Stage {stg})")
            self.assertTrue(tst.exists(), f"Test missing: {tst_fname} (Stage {stg})")


if __name__ == "__main__":
    unittest.main()
