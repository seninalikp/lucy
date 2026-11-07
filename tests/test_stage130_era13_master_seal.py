"""
tests/test_stage130_era13_master_seal.py
Verification suite for Stage 130: Sovereign Singularity Nexus & Era 13 Master Seal
Era 13: Self-Reflective Symbolic Mesh & Cognitive Graph Synthesizer
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.era13_master_seal import (
    CANONICAL_ERA13_MODULES,
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    ERA_NAME,
    STAGE,
    STAGE_NAME,
    Era13MasterSealNexus,
    Era13SealCertificate,
    SymbolicCycleResult,
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


class TestStage130Era13MasterSeal(unittest.TestCase):
    def setUp(self):
        # We point project_root to real repo root to verify live Era 13 modules
        self.project_root = Path(__file__).resolve().parent.parent
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data" / "lucy" / "seals"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = MockReceiptLedger()
        self.nexus = Era13MasterSealNexus(
            project_root=self.project_root,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_metadata(self):
        """Verifies sovereign operator identity and stage/era metadata."""
        self.assertEqual(STAGE, 130)
        self.assertEqual(ERA, 13)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")
        status = self.nexus.status()
        self.assertEqual(status["stage"], 130)
        self.assertEqual(status["era"], 13)
        self.assertEqual(status["creator"], "Senin")
        self.assertEqual(status["creator_full_name"], "Senin Ali K P")

    def test_02_canonical_era13_modules_integrity(self):
        """Verifies that all 10 canonical Era 13 modules exist on disk."""
        self.assertEqual(len(CANONICAL_ERA13_MODULES), 10)
        lucy_core = self.project_root / "backend" / "lucy_core"
        tests_dir = self.project_root / "tests"

        for stg, name, src, tst in CANONICAL_ERA13_MODULES:
            self.assertTrue((lucy_core / src).exists(), f"Missing source file: {src}")
            self.assertTrue((tests_dir / tst).exists(), f"Missing test file: {tst}")

    def test_03_merkle_root_determinism(self):
        """Verifies deterministic Merkle tree calculation."""
        cert1 = self.nexus.generate_era13_master_seal(force=True)
        cert2 = self.nexus.generate_era13_master_seal(force=True)
        self.assertEqual(cert1.merkle_root, cert2.merkle_root)
        self.assertTrue(len(cert1.merkle_root) == 64)
        self.assertTrue(cert1.seal_id.startswith("SEAL-ERA13-"))

    def test_04_parent_era12_chaining(self):
        """Verifies cryptographic chain of custody to Era 12."""
        cert = self.nexus.generate_era13_master_seal()
        self.assertTrue(len(cert.parent_era12_seal_hash) == 64)
        self.assertIsNotNone(cert.parent_era12_seal_hash)

    def test_05_seal_certificate_generation_and_persistence(self):
        """Verifies that the seal certificate is serialized to JSON and reloads reliably."""
        cert = self.nexus.generate_era13_master_seal(force=True)
        self.assertTrue(self.nexus.seal_file.exists())

        # Reload with new instance
        nexus2 = Era13MasterSealNexus(
            project_root=self.project_root,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
        )
        self.assertIsNotNone(nexus2._cached_seal)
        self.assertEqual(nexus2._cached_seal.seal_id, cert.seal_id)
        self.assertEqual(nexus2._cached_seal.total_stages_sealed, 10)

    def test_06_verify_era13_integrity(self):
        """Verifies live integrity audit returns full sovereign verification pass."""
        is_intact, msg, data = self.nexus.verify_era13_integrity()
        self.assertTrue(is_intact, f"Integrity check failed: {msg}")
        self.assertIn("INTACT", msg)
        self.assertEqual(data["integrity_status"], "VERIFIED_SOVEREIGN")

    def test_07_symbolic_mesh_singularity_cycle(self):
        """Verifies end-to-end cognitive loop across all 10 subsystems."""
        result = self.nexus.run_symbolic_mesh_cycle(goal="Achieve sovereign self-reflection")
        self.assertTrue(result.success)
        self.assertGreaterEqual(result.subsystems_active, 9)
        self.assertGreaterEqual(len(result.steps_executed), 9)
        self.assertIn("Stage 130", result.steps_executed[-1])

    def test_08_receipt_ledger_integration(self):
        """Verifies audit trail receipts for seal generation, verification, and pulse cycles."""
        self.nexus.generate_era13_master_seal(force=True)
        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("ERA13_SEAL_GENERATED", actions)

        self.nexus.verify_era13_integrity()
        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("ERA13_SEAL_VERIFIED", actions)

        self.nexus.run_symbolic_mesh_cycle()
        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("SYMBOLIC_CYCLE_EXECUTED", actions)

    def test_09_ascii_seal_certificate_table(self):
        """Verifies CP1252-safe ASCII table formatting."""
        table = self.nexus.format_seal_certificate_table()
        self.assertIn("ERA 13 MASTER SEAL CERTIFICATE", table)
        self.assertIn("SELF-REFLECTIVE SYMBOLIC MESH", table)
        self.assertIn("Senin", table)
        self.assertIn("PASS [OK]", table)
        # Strict CP1252 compatibility test
        table.encode("cp1252")

    def test_10_runtime_integration(self):
        """Verifies LucyRuntime binds and executes Era 13 Master Seal commands."""
        from backend.lucy_core.lucy_runtime import LucyRuntime

        runtime = LucyRuntime(project_root=self.project_root)
        self.assertTrue(hasattr(runtime, "era13_seal"))
        self.assertIsInstance(runtime.era13_seal, Era13MasterSealNexus)

        # Test CLI commands via lucy_respond
        res_seal = runtime.lucy_respond("/era13-seal")
        self.assertIn("ERA 13 MASTER SEAL CERTIFICATE", res_seal)

        res_ver = runtime.lucy_respond("/verify-era13")
        self.assertIn("INTACT", res_ver)

        res_pulse = runtime.lucy_respond("/symbolic-cycle Test Goal")
        self.assertIn("Symbolic Singularity Pulse", res_pulse)


if __name__ == "__main__":
    unittest.main()
