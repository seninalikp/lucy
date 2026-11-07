"""
tests/test_stage87_epistemic_provenance.py
Unit tests for Stage 87: Epistemic Provenance Tracker & Anti-Hallucination Confidence Spine
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.epistemic_provenance import (
    EpistemicAttestation,
    EpistemicLevel,
    EpistemicProvenanceTracker,
    GroundedEntity,
    STAGE,
)


class MockReceiptLedger:
    def __init__(self):
        self.receipts = []

    def issue_receipt(self, action_category: str, operation: str, target: str, verified_outcome: str):
        self.receipts.append({
            "category": action_category,
            "operation": operation,
            "target": target,
            "outcome": verified_outcome,
        })


class TestStage87EpistemicProvenance(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_stage87_test_"))
        self.data_dir = self.test_dir / "epistemic"
        self.ledger = MockReceiptLedger()

        # Create a real sample file in project root for empirical checks
        self.real_file = self.test_dir / "backend" / "real_service.py"
        self.real_file.parent.mkdir(parents=True, exist_ok=True)
        self.real_file.write_text("print('empirical reality')", encoding="utf-8")

        self.tracker = EpistemicProvenanceTracker(
            project_root=self.test_dir,
            receipt_ledger=self.ledger,
            data_dir=self.data_dir,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_stage_constant(self):
        self.assertEqual(STAGE, 87)

    def test_02_extract_file_references(self):
        text = "Check `backend/real_service.py` and `config.json`. Do not confuse with python.org or example.com."
        files = self.tracker.extract_file_references(text)
        self.assertIn("backend/real_service.py", files)
        self.assertIn("config.json", files)
        self.assertNotIn("python.org", files)
        self.assertNotIn("example.com", files)

    def test_03_verify_real_file_on_disk(self):
        text = "I inspected backend/real_service.py and confirmed the service initialization."
        att = self.tracker.verify_response_provenance(text)
        self.assertFalse(att.has_hallucination)
        self.assertEqual(att.risk_level, "MINIMAL")
        self.assertGreaterEqual(att.integrity_score, 0.90)
        self.assertEqual(len(att.entities), 1)
        self.assertEqual(att.entities[0].level, EpistemicLevel.VERIFIED_EMPIRICAL)
        self.assertTrue(att.entities[0].verified)

    def test_04_intercept_fabricated_file_creation(self):
        text = "I created backend/imaginary_phantom_ghost.py for you to solve the issue."
        att = self.tracker.verify_response_provenance(text)
        self.assertTrue(att.has_hallucination)
        self.assertEqual(att.risk_level, "CRITICAL_HALLUCINATION")
        self.assertLess(att.integrity_score, 0.45)
        self.assertGreaterEqual(len(att.hallucinations_intercepted), 1)
        self.assertIn("imaginary_phantom_ghost.py", att.hallucinations_intercepted[0])

    def test_05_hypothetical_file_reference(self):
        text = "In your setup, you could create a handler in routes.py to process events."
        att = self.tracker.verify_response_provenance(text)
        self.assertFalse(att.has_hallucination)
        self.assertIn(att.risk_level, ["LOW", "MODERATE"])
        self.assertEqual(att.entities[0].level, EpistemicLevel.HYPOTHESIS_SPECULATION)

    def test_06_web_grounded_provenance(self):
        text = "According to latest Python docs, distutils has been retired."
        att = self.tracker.verify_response_provenance(text, web_grounded=True)
        self.assertFalse(att.has_hallucination)
        levels = [e.level for e in att.entities]
        self.assertIn(EpistemicLevel.CORROBORATED_EXTERNAL, levels)

    def test_07_memory_grounded_provenance(self):
        text = "You prefer using Arch Linux as your primary desktop distro."
        att = self.tracker.verify_response_provenance(text, memory_grounded=True)
        self.assertFalse(att.has_hallucination)
        levels = [e.level for e in att.entities]
        self.assertIn(EpistemicLevel.INTERNAL_USER_MEMORY, levels)

    def test_08_conversational_turn_default_integrity(self):
        text = "Hey. I'm ready to help you with the refactor. Let's inspect the architecture."
        att = self.tracker.verify_response_provenance(text)
        self.assertFalse(att.has_hallucination)
        self.assertEqual(att.risk_level, "MINIMAL")
        self.assertEqual(att.integrity_score, 0.75)

    def test_09_attestation_persistence(self):
        self.tracker.verify_response_provenance("Inspecting backend/real_service.py.")
        self.assertTrue(self.tracker.log_file.exists())

        lines = self.tracker.log_file.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertIn("integrity_score", record)
        self.assertIn("entities", record)

    def test_10_terminal_summary_ascii_safe(self):
        att = self.tracker.verify_response_provenance("I checked backend/real_service.py.")
        summary = self.tracker.format_terminal_summary(att)
        summary.encode("ascii")  # Must not raise UnicodeEncodeError
        self.assertIn("EPISTEMIC PROVENANCE ATTESTATION", summary)
        self.assertIn("MINIMAL", summary)
        self.assertIn("+", summary)
        self.assertIn("-", summary)
        self.assertIn("|", summary)

    def test_11_receipt_ledger_integration(self):
        self.tracker.verify_response_provenance("Verifying backend/real_service.py.")
        self.assertEqual(len(self.ledger.receipts), 1)
        self.assertEqual(self.ledger.receipts[0]["category"], "epistemic_audit")
        self.assertEqual(self.ledger.receipts[0]["operation"], "verify_provenance")

    def test_12_status_dict(self):
        st = self.tracker.status()
        self.assertEqual(st["status"], "active")
        self.assertIn("log_file", st)
        self.assertIn("project_root", st)


if __name__ == "__main__":
    unittest.main()
