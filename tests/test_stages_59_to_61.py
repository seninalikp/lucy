"""
test_stages_59_to_61.py
Verifies:
- Stage 59: Natural-language multi-intent action parsing & receipt generation.
- Stage 60: Anti-stub LoRA training queue protection in CodeSynthesisPipeline.
- Stage 61: Sentence-scoped FactStateVerifier (no cross-sentence false positives).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class TestStages59To61(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.runtime = LucyRuntime(project_root=self.root)
        self.router = CommandRouter(self.runtime)

    def tearDown(self) -> None:
        self.runtime.graceful_shutdown("test teardown")
        self.temp_dir.cleanup()

    def test_stage59_natural_language_multi_action_execution(self) -> None:
        reply = self.router.handle(
            "I'm focusing on UI today, please add a task to wire the Stage 58 brief endpoint, "
            "and remember that my current priority is zero hallucinations."
        )
        open_tasks = [t["text"] for t in self.runtime.project_summary()["open_tasks"]]
        self.assertIn("wire the Stage 58 brief endpoint", open_tasks)

        recalled = [m["fact"] for m in self.runtime.recall("current priority")]
        self.assertTrue(any("current priority is zero hallucinations" in f.lower() for f in recalled))

        receipts = self.runtime.receipt_ledger.current_turn_receipts()
        categories = {r["action_category"] for r in receipts}
        self.assertIn("task_mutation", categories)
        self.assertIn("memory_mutation", categories)
        self.assertNotIn("STAGE 55 RECEIPT INTERCEPT", reply.message)

    def test_stage60_fallback_stub_barred_from_lora_queue(self) -> None:
        # Offline synthesis uses _fallback_template; must NOT pollute verified_training_queue.jsonl
        rep = self.runtime.code_synthesis.synthesize(
            instruction="build a dummy offline calculator",
            filename="offline_calc.py",
        )
        self.assertTrue(rep["promoted"])
        self.assertEqual(rep["source"], "deterministic_template_fallback")
        self.assertFalse(rep["lora_queue_admitted"])

    def test_stage61_sentence_scoped_verifier_no_false_positive(self) -> None:
        # Sentence 1 has "saved" (not a file). Sentence 2 mentions "settings.json" hypothetically.
        text = (
            "I saved your preference to memory. "
            "Later, you can inspect settings.json if you want to customize themes."
        )
        check = self.runtime.fact_verifier.verify_claim(text)
        self.assertTrue(check["verified"])
        self.assertFalse(check["hallucination_detected"])


if __name__ == "__main__":
    unittest.main()
