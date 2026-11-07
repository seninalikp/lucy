"""
test_lora_two_speed_adaptation.py
Verifies Stage 36 (VerifiedTrainingQueue), Stage 42 (LoRASleepCycleEngine + Modelfile baking),
and Stage 45 (PersonalLoRAAlignmentEngine Two-Speed Cloud/Local bridge).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class TestLoRATwoSpeedAdaptation(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.runtime = LucyRuntime(project_root=self.root)
        self.router = CommandRouter(self.runtime)

    def tearDown(self) -> None:
        self.runtime.graceful_shutdown("test teardown")
        self.temp_dir.cleanup()

    def test_hallucinated_turns_barred_from_training_queue(self) -> None:
        bad_res = self.runtime.personal_alignment.maybe_admit_verified_turn(
            user_text="Create imaginary.py",
            reply_text="I created imaginary.py [ELIE: HALLUCINATION_INTERCEPTED]",
            disk_verified=False,
            receipt_verified=True,
            source="test",
        )
        self.assertFalse(bad_res["admitted"])
        self.assertEqual(self.runtime.training_queue.status()["verified_records_count"], 0)

    def test_verified_turns_admitted_and_baked_into_modelfile(self) -> None:
        good_res = self.runtime.personal_alignment.maybe_admit_verified_turn(
            user_text="How should you write Python code for Senin?",
            reply_text="Complete, untruncated production Python code with 4-space indentation and zero placeholders.",
            disk_verified=True,
            receipt_verified=True,
            source="test",
        )
        self.assertTrue(good_res["admitted"])

        # Cloud few-shot block should now include the verified exemplar
        few_shot = self.runtime.personal_alignment.build_cloud_few_shot_block()
        self.assertIn("Complete, untruncated production Python code", few_shot)

        # Running sleep cycle should export Alpaca dataset and bake MESSAGE into Modelfile.lucy
        cycle = self.runtime.trigger_personal_sleep_cycle()
        self.assertTrue(cycle["sanity_gate"]["passed"])
        self.assertEqual(cycle["dataset_record_count"], 1)
        self.assertEqual(cycle["baked_exemplars_count"], 1)

        modelfile_text = Path(cycle["modelfile_path"]).read_text(encoding="utf-8")
        self.assertIn("MESSAGE user", modelfile_text)
        self.assertIn("Complete, untruncated production Python code", modelfile_text)

    def test_physical_adapter_uncomments_adapter_directive(self) -> None:
        dummy_gguf = self.runtime.lora_sleep.adapters_dir / "lucy_personal_lora.gguf"
        dummy_gguf.write_bytes(b"GGUF_TEST_WEIGHTS")

        mf = self.runtime.lora_sleep.generate_modelfile(adapter_name="lucy_personal_lora.gguf")
        self.assertTrue(mf["adapter_active_on_disk"])
        modelfile_text = Path(mf["modelfile_path"]).read_text(encoding="utf-8")
        self.assertIn(f"ADAPTER {dummy_gguf}", modelfile_text)
        self.assertNotIn("# ADAPTER", modelfile_text)


if __name__ == "__main__":
    unittest.main()
