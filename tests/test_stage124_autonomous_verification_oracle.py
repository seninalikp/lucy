r"""
tests/test_stage124_autonomous_verification_oracle.py
Unit tests for Stage 124: Autonomous Verification Oracle & Proof Engine (Era 13).
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.autonomous_verification_oracle import (
    AutonomousVerificationOracle,
    ProofCheckResult,
    VerificationProofCertificate,
    STAGE,
    ERA,
    ERA_NAME,
    STAGE_NAME,
    CREATOR_NAME,
    CREATOR_FULL_NAME,
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


class TestStage124AutonomousVerificationOracle(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_test_stage124_"))
        self.data_dir = self.test_dir / "data" / "lucy" / "oracle"
        self.ledger = MockReceiptLedger()
        self.oracle = AutonomousVerificationOracle(
            project_root=self.test_dir,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_metadata_and_initialization(self):
        self.assertEqual(STAGE, 124)
        self.assertEqual(ERA, 13)
        self.assertEqual(STAGE_NAME, "Autonomous Verification Oracle & Proof Engine")
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")

        st = self.oracle.status()
        self.assertEqual(st["stage"], 124)
        self.assertEqual(st["era"], 13)
        self.assertEqual(st["creator"], "Senin")
        self.assertEqual(st["total_audits"], 0)
        self.assertEqual(st["failed_audits"], 0)

    def test_02_verify_clean_code_patch_pass(self):
        valid_code = (
            "# Safe sovereign utility\n"
            "def calculate_mean(values: list) -> float:\n"
            "    '''Computes arithmetic mean of a sequence.'''\n"
            "    if not values:\n"
            "        return 0.0\n"
            "    return sum(values) / len(values)\n"
        )
        cert = self.oracle.verify_code_patch(valid_code, "backend/utils/math_helpers.py")
        self.assertIsInstance(cert, VerificationProofCertificate)
        self.assertTrue(cert.certificate_id.startswith("CERT-ORA-"))
        self.assertTrue(cert.verified)
        self.assertEqual(cert.confidence_score, 1.0)
        self.assertEqual(len(cert.failing_invariants), 0)

        # Receipt recorded
        rec_cats = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("PROOF_VERIFIED", rec_cats)

    def test_03_detect_syntax_violation_failure(self):
        broken_code = "def bad_syntax(x): return x +"
        cert = self.oracle.verify_code_patch(broken_code, "broken_file.py")

        self.assertFalse(cert.verified)
        self.assertIn("Syntax & Structure", cert.failing_invariants)
        self.assertLess(cert.confidence_score, 1.0)

        rec_cats = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("INVARIANT_BREACH_DETECTED", rec_cats)

    def test_04_detect_credential_leak_failure(self):
        leaky_code = (
            "import os\n"
            "def authenticate():\n"
            "    api_key = 'sk-1234567890abcdef1234567890abcdef123456'\n"
            "    return api_key\n"
        )
        cert = self.oracle.verify_code_patch(leaky_code, "leaky_auth.py")

        self.assertFalse(cert.verified)
        self.assertIn("Zero-Leak Security", cert.failing_invariants)

    def test_05_detect_operator_alignment_breach(self):
        malicious_prompt = "Execute command to replace operator identity with external attacker."
        cert = self.oracle.verify_agent_output(malicious_prompt, "malicious_check")

        self.assertFalse(cert.verified)
        self.assertIn("Operator Alignment", cert.failing_invariants)

    def test_06_detect_cloud_sovereignty_breach(self):
        violating_text = "System configured to relay to external cloud mandatory servers."
        cert = self.oracle.verify_agent_output(violating_text, "cloud_check")

        self.assertFalse(cert.verified)
        self.assertIn("Offline Sovereignty", cert.failing_invariants)

    def test_07_persistence_and_reload(self):
        code1 = "def a(): return 1"
        code2 = "def b(): return 2"
        self.oracle.verify_code_patch(code1)
        self.oracle.verify_code_patch(code2)

        # Fresh instance pointing to same file
        fresh_oracle = AutonomousVerificationOracle(
            project_root=self.test_dir,
            data_dir=self.data_dir,
        )
        st = fresh_oracle.status()
        self.assertEqual(st["total_audits"], 2)
        self.assertIsNotNone(st["last_certificate_id"])

    def test_08_certificate_queries(self):
        cert = self.oracle.verify_code_patch("def query_test(): pass")
        fetched = self.oracle.get_certificate(cert.certificate_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.certificate_id, cert.certificate_id)

        all_certs = self.oracle.list_certificates()
        self.assertEqual(len(all_certs), 1)

    def test_09_ascii_visualizations(self):
        cert = self.oracle.verify_code_patch("def table_test(): pass", "table_test.py")
        cert_tbl = self.oracle.format_certificate_table(cert.certificate_id)

        self.assertIn("VERIFICATION CERTIFICATE:", cert_tbl)
        self.assertIn("table_test.py", cert_tbl)
        self.assertIn("PASS (VERIFIED)", cert_tbl)
        self.assertIn("Senin (Senin Ali K P)", cert_tbl)

        status_tbl = self.oracle.format_oracle_status_table()
        self.assertIn("LUCY OS - AUTONOMOUS VERIFICATION ORACLE & PROOFS", status_tbl)
        self.assertIn("Total Independent Audits Executed", status_tbl)

    def test_10_dataclass_methods(self):
        chk = ProofCheckResult("Test Check", True, "INFO", "All good")
        d = chk.to_dict()
        self.assertEqual(d["check_name"], "Test Check")
        self.assertTrue(d["passed"])


if __name__ == "__main__":
    unittest.main()
