"""
tests/test_stage85_lora_compiler.py
Unit tests for Stage 85: Local Model Adapter Compiler & Ollama Hot-Swap Engine
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lora_compiler import (
    CompiledAdapterManifest,
    LocalModelAdapterCompiler,
    STAGE,
)
from backend.lucy_core.lora_harvester import (
    CuratedInteraction,
    HighSignalLoRAHarvester,
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


class TestStage85LoRACompiler(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_stage85_test_"))
        self.adapters_dir = self.test_dir / "adapters"
        self.ledger = MockReceiptLedger()

        # Mock harvester with curated exemplars
        self.harvester = HighSignalLoRAHarvester(
            project_root=self.test_dir,
            data_dir=self.test_dir / "lora",
        )
        self.harvester.curated_interactions = [
            CuratedInteraction(
                interaction_id="ex_1",
                instruction="How to structure error boundaries?",
                response="I recommend wrapping domain services in an explicit Result[T, E] monad rather than bubbling bare exceptions.",
                category="coding",
                signal_score=0.92,
                epistemic_grounding=True,
                pushback_detected=False,
                first_person_pure=True,
            ),
            CuratedInteraction(
                interaction_id="ex_2",
                instruction="Should we commit secret keys to git?",
                response="Actually, no. Storing secrets in git creates a critical exposure vulnerability. Let's use environment variables instead.",
                category="anti_sycophancy",
                signal_score=0.95,
                epistemic_grounding=True,
                pushback_detected=True,
                first_person_pure=True,
            ),
        ]

        self.compiler = LocalModelAdapterCompiler(
            project_root=self.test_dir,
            harvester=self.harvester,
            receipt_ledger=self.ledger,
            active_model="qwen2.5:3b",
            adapters_dir=self.adapters_dir,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_stage_constant(self):
        self.assertEqual(STAGE, 85)

    def test_02_build_modelfile(self):
        content, path = self.compiler.build_modelfile(
            base_model="qwen2.5:3b",
            custom_tag="lucy:personal-test",
            max_exemplars=2,
        )
        self.assertTrue(path.exists())
        self.assertIn("FROM qwen2.5:3b", content)
        self.assertIn("PARAMETER temperature 0.2", content)
        self.assertIn("PARAMETER top_p 0.85", content)
        self.assertIn("MESSAGE user", content)
        self.assertIn("MESSAGE assistant", content)
        self.assertIn("Result[T, E]", content)
        self.assertIn("critical exposure vulnerability", content)

    def test_03_build_modelfile_with_gguf_adapter(self):
        fake_gguf = self.adapters_dir / "custom_adapter.gguf"
        fake_gguf.write_bytes(b"GGUF_MOCK_BYTES")

        content, path = self.compiler.build_modelfile(
            base_model="qwen2.5:3b",
            adapter_path=str(fake_gguf),
        )
        self.assertIn(f"ADAPTER {fake_gguf.resolve()}", content)

    def test_04_first_person_enforced_in_system_prompt(self):
        content, _ = self.compiler.build_modelfile()
        self.assertIn("first person", content.lower())
        self.assertIn("Never refer to yourself in the third person as 'Lucy'", content)

    def test_05_hot_swap_success(self):
        res = self.compiler.hot_swap("lucy:personal-v1", skip_health_check=True)
        self.assertTrue(res["success"])
        self.assertEqual(self.compiler.active_model, "lucy:personal-v1")
        self.assertEqual(self.compiler.previous_model, "qwen2.5:3b")

    def test_06_hot_swap_empty_tag_rejected(self):
        res = self.compiler.hot_swap("   ", skip_health_check=True)
        self.assertFalse(res["success"])
        self.assertIn("Empty model tag", res["reason"])

    def test_07_rollback_mechanism(self):
        self.compiler.hot_swap("lucy:personal-v1", skip_health_check=True)
        self.assertEqual(self.compiler.active_model, "lucy:personal-v1")

        rb = self.compiler.rollback()
        self.assertTrue(rb["success"])
        self.assertEqual(self.compiler.active_model, "qwen2.5:3b")

    def test_08_compile_model_mock_success(self):
        res = self.compiler.compile_model(
            custom_tag="lucy:personal-v85.1",
            mock_cli_run=True,
            auto_swap=True,
        )
        self.assertTrue(res["compiled"])
        self.assertEqual(res["tag"], "lucy:personal-v85.1")
        self.assertEqual(self.compiler.active_model, "lucy:personal-v85.1")
        self.assertEqual(len(self.compiler.manifests), 1)
        self.assertEqual(self.compiler.manifests[0].status, "ACTIVE")

    def test_09_registry_persistence_and_reload(self):
        self.compiler.compile_model(
            custom_tag="lucy:personal-v85.2",
            mock_cli_run=True,
            auto_swap=True,
        )
        self.assertTrue(self.compiler.registry_file.exists())

        # Reload in new instance
        reloaded = LocalModelAdapterCompiler(
            project_root=self.test_dir,
            adapters_dir=self.adapters_dir,
        )
        self.assertEqual(reloaded.active_model, "lucy:personal-v85.2")
        self.assertEqual(len(reloaded.manifests), 1)
        self.assertEqual(reloaded.manifests[0].tag, "lucy:personal-v85.2")

    def test_10_terminal_summary_ascii_safe(self):
        self.compiler.compile_model(
            custom_tag="lucy:personal-v85.3",
            mock_cli_run=True,
            auto_swap=True,
        )
        summary = self.compiler.format_terminal_summary()
        summary.encode("ascii")  # Must not raise UnicodeEncodeError
        self.assertIn("LOCAL MODEL ADAPTER COMPILER", summary)
        self.assertIn("lucy:personal-v85.3", summary)
        self.assertIn("+", summary)
        self.assertIn("-", summary)
        self.assertIn("|", summary)

    def test_11_receipt_ledger_integration(self):
        self.compiler.compile_model(
            custom_tag="lucy:personal-v85.4",
            mock_cli_run=True,
            auto_swap=True,
        )
        self.compiler.hot_swap("qwen2.5:3b", skip_health_check=True)
        self.compiler.rollback()

        # Check receipts logged
        categories = [r["category"] for r in self.ledger.receipts]
        self.assertIn("lora_compiler", categories)
        ops = [r["operation"] for r in self.ledger.receipts]
        self.assertIn("compile_model", ops)
        self.assertIn("hot_swap", ops)
        self.assertIn("rollback", ops)

    def test_12_status_dict(self):
        st = self.compiler.status()
        self.assertEqual(st["status"], "active")
        self.assertIn("active_model", st)
        self.assertIn("compiled_adapters_count", st)
        self.assertIn("adapters_directory", st)


if __name__ == "__main__":
    unittest.main()
