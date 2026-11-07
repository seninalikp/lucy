"""
tests/test_stage88_style_mirror.py
Unit tests for Stage 88: Dynamic Few-Shot Operator Style Mirror & Semantic Preference Ingestion
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lora_harvester import (
    CuratedInteraction,
    HighSignalLoRAHarvester,
)
from backend.lucy_core.style_mirror import (
    DynamicStyleMirror,
    OperatorPreference,
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


class TestStage88StyleMirror(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_stage88_test_"))
        self.prefs_dir = self.test_dir / "preferences"
        self.ledger = MockReceiptLedger()

        # Harvester with sample exemplars
        self.harvester = HighSignalLoRAHarvester(
            project_root=self.test_dir,
            data_dir=self.test_dir / "lora",
        )
        self.harvester.curated_interactions = [
            CuratedInteraction(
                interaction_id="ex_db",
                instruction="How to optimize sqlite database writes?",
                response="I enable WAL journal mode and execute batch inserts in a single transaction context manager.",
                category="coding",
                signal_score=0.94,
                epistemic_grounding=True,
                pushback_detected=False,
                first_person_pure=True,
            ),
            CuratedInteraction(
                interaction_id="ex_api",
                instruction="Should we build a REST or GraphQL endpoint?",
                response="For this CLI tool, I recommend a simple internal RPC function rather than spinning up an HTTP server.",
                category="architecture",
                signal_score=0.91,
                epistemic_grounding=True,
                pushback_detected=True,
                first_person_pure=True,
            ),
        ]

        self.mirror = DynamicStyleMirror(
            project_root=self.test_dir,
            harvester=self.harvester,
            receipt_ledger=self.ledger,
            preferences_dir=self.prefs_dir,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_stage_constant(self):
        self.assertEqual(STAGE, 88)

    def test_02_default_preferences_seeded(self):
        self.assertGreaterEqual(len(self.mirror.preferences), 4)
        self.assertIn("tone_voice", self.mirror.preferences)
        self.assertIn("anti_third_person", self.mirror.preferences)
        self.assertIn("verbosity_pacing", self.mirror.preferences)

    def test_03_explicit_ingest_preference(self):
        pref = self.mirror.ingest_preference(
            key="package_manager",
            value="Use uv for sub-second virtualenv management",
            category="tooling",
        )
        self.assertEqual(pref.key, "package_manager")
        self.assertIn("package_manager", self.mirror.preferences)
        self.assertTrue(self.mirror.preferences_file.exists())

    def test_04_detect_implicit_preference_prefer_over(self):
        stmt = "For unit testing, I prefer pytest over unittest in all new modules."
        detected = self.mirror.detect_implicit_preferences(stmt)
        self.assertEqual(len(detected), 1)
        self.assertEqual(detected[0].key, "prefer_pytest")
        self.assertIn("pytest rather than unittest", detected[0].value)

    def test_05_detect_implicit_preference_always_use(self):
        stmt = "When defining functions, always use type annotations."
        detected = self.mirror.detect_implicit_preferences(stmt)
        self.assertEqual(len(detected), 1)
        self.assertIn("type", detected[0].key)
        self.assertIn("Always use", detected[0].value)

    def test_06_detect_implicit_preference_never_use(self):
        stmt = "In security code, never use eval for parsing."
        detected = self.mirror.detect_implicit_preferences(stmt)
        self.assertEqual(len(detected), 1)
        self.assertEqual(detected[0].key, "avoid_eval")
        self.assertIn("Avoid using eval", detected[0].value)

    def test_07_select_few_shot_exemplars_lexical_overlap(self):
        prompt = "How can we speed up sqlite database transactions?"
        exemplars = self.mirror.select_few_shot_exemplars(prompt, max_exemplars=1)
        self.assertEqual(len(exemplars), 1)
        # ex_db should match because of 'sqlite' and 'database'
        self.assertEqual(exemplars[0].interaction_id, "ex_db")

    def test_08_build_style_steering_block(self):
        block = self.mirror.build_style_steering_block("sqlite query performance")
        self.assertIn("[OPERATOR STYLE & ALIGNMENT DIRECTIVES]", block)
        self.assertIn("first-person", block.lower())
        self.assertIn("[HIGH-SIGNAL IN-CONTEXT EXEMPLARS]", block)
        self.assertIn("WAL journal mode", block)

    def test_09_preference_persistence_and_reload(self):
        self.mirror.ingest_preference("editor", "Neovim with Lua configs", category="tooling")
        self.assertTrue(self.mirror.preferences_file.exists())

        # Reload in new instance
        reloaded = DynamicStyleMirror(
            project_root=self.test_dir,
            preferences_dir=self.prefs_dir,
        )
        self.assertIn("editor", reloaded.preferences)
        self.assertEqual(reloaded.preferences["editor"].value, "Neovim with Lua configs")

    def test_10_terminal_summary_ascii_safe(self):
        summary = self.mirror.format_terminal_summary()
        summary.encode("ascii")  # Must not raise UnicodeEncodeError
        self.assertIn("DYNAMIC FEW-SHOT OPERATOR STYLE MIRROR", summary)
        self.assertIn("Registered Preferences", summary)
        self.assertIn("+", summary)
        self.assertIn("-", summary)
        self.assertIn("|", summary)

    def test_11_receipt_ledger_integration(self):
        self.mirror.ingest_preference("linter", "Ruff", category="tooling")
        self.assertEqual(len(self.ledger.receipts), 1)
        self.assertEqual(self.ledger.receipts[0]["category"], "style_mirror")
        self.assertEqual(self.ledger.receipts[0]["operation"], "ingest_preference")

    def test_12_status_dict(self):
        st = self.mirror.status()
        self.assertEqual(st["status"], "active")
        self.assertIn("preferences_count", st)
        self.assertIn("categories", st)


if __name__ == "__main__":
    unittest.main()
