"""
test_stage45_personal_lora_alignment.py
Stage 45 = Personal LoRA Sleep Cycle & Style Alignment Pipeline.

Verifies:
1. Pipeline reports Stage 45 and active status.
2. Synthesis of personal dataset from anti-drift rules, aliases, and dialogue logs.
3. Personal Modelfile generation with ADAPTER directive and tailored system prompt.
4. 10-Question Personal Alignment Gate passes 100% against ground truth.
5. Alignment gate strictly quarantines models failing user anti-drift rules.
6. Full personal sleep cycle lifecycle execution.
7. Personal adapter discovery in data/lucy/adapters/.
8. LucyRuntime Stage 45 integration.
9. CommandRouter Stage 45 command routing and formatting.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.personal_profiler import PersonalProfiler
from backend.lucy_core.personal_lora_alignment import (
    PersonalLoRAAlignmentPipeline,
    STAGE,
    DEFAULT_BASE_MODEL,
    PERSONAL_ALIGNMENT_PROBES,
)
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class MockFailingConnector:
    """Mock connector returning responses that violate personal anti-drift boundaries."""
    def is_online(self) -> bool:
        return True

    def has_model(self, name: str) -> bool:
        return True

    def chat_or_fallback(self, prompt: str, system_prompt: str = "") -> dict:
        return {
            "source": "mock_failing",
            "online": True,
            "message": "Yes, I will build a full Linux kernel and replace your OS now.",
        }


class Stage45PersonalLoRAAlignmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.lucy_data = self.root / "data" / "lucy"
        self.lucy_data.mkdir(parents=True, exist_ok=True)
        self.profiler = PersonalProfiler(lucy_data=self.lucy_data)
        self.pipeline = PersonalLoRAAlignmentPipeline(
            project_root=self.root,
            lucy_data=self.lucy_data,
            personal_profiler=self.profiler,
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_01_initial_status(self) -> None:
        status = self.pipeline.status()
        self.assertEqual(status["stage"], STAGE)
        self.assertEqual(status["personal_lora_alignment"], "active")
        self.assertEqual(status["personal_adapters_count"], 0)
        self.assertEqual(status["alignment_pass_threshold"], "90.0%")

    def test_02_synthesize_personal_dataset(self) -> None:
        # Create a sample conversation log with a high-quality turn
        convo_log = self.lucy_data / "conversation_log.jsonl"
        with open(convo_log, "w", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": "2026-10-28T00:00:00Z",
                "input": "How should we organize tools?",
                "reply": "We keep verified tools under promoted_tools/.",
                "quality": "high",
            }) + "\n")

        res = self.pipeline.synthesize_personal_dataset()
        self.assertEqual(res["status"], "synthesized")
        self.assertGreaterEqual(res["record_count"], 5)
        self.assertGreaterEqual(res["anti_drift_count"], 4)
        self.assertGreaterEqual(res["aliases_count"], 5)
        self.assertTrue(Path(res["dataset_file"]).exists())

    def test_03_generate_personal_modelfile(self) -> None:
        content = self.pipeline.generate_personal_modelfile("lucy_personal_v1.safetensors")
        self.assertIn(f"FROM {DEFAULT_BASE_MODEL}", content)
        self.assertIn("ADAPTER ./adapters/lucy_personal_v1.safetensors", content)
        self.assertIn("You are LUCY", content)
        self.assertIn("anti-drift rules", content)

    def test_04_alignment_gate_ground_truth_passes_100_percent(self) -> None:
        gate_res = self.pipeline.run_alignment_gate()
        self.assertTrue(gate_res["passed"])
        self.assertEqual(gate_res["score"], f"{len(PERSONAL_ALIGNMENT_PROBES)}/{len(PERSONAL_ALIGNMENT_PROBES)}")
        self.assertEqual(gate_res["score_percentage"], 100.0)
        self.assertIn("PASSED", gate_res["badge"])

    def test_05_alignment_gate_quarantines_drifted_model(self) -> None:
        failing_pipeline = PersonalLoRAAlignmentPipeline(
            project_root=self.root,
            lucy_data=self.lucy_data,
            personal_profiler=self.profiler,
            connector=MockFailingConnector(),
        )
        gate_res = failing_pipeline.run_alignment_gate()
        self.assertFalse(gate_res["passed"])
        self.assertLess(gate_res["score_percentage"], 90.0)
        self.assertIn("QUARANTINED", gate_res["badge"])

    def test_06_trigger_personal_sleep_cycle(self) -> None:
        result = self.pipeline.trigger_personal_sleep_cycle()
        self.assertEqual(result["status"], "COMPLETED")
        self.assertIn("PASSED", result["badge"])
        self.assertTrue(result["adapter_name"].startswith("lucy_personal_adapter_v"))
        self.assertTrue((self.lucy_data / "adapters" / result["adapter_name"]).exists())
        self.assertTrue((self.lucy_data / "adapters" / "lucy_personal_latest.safetensors").exists())

    def test_07_list_personal_adapters(self) -> None:
        (self.lucy_data / "adapters" / "lucy_personal_adapter_v1.safetensors").touch()
        (self.lucy_data / "adapters" / "random_notes.txt").touch()

        adapters = self.pipeline.list_personal_adapters()
        self.assertIn("lucy_personal_adapter_v1.safetensors", adapters)
        self.assertNotIn("random_notes.txt", adapters)


class Stage45RuntimeAndRouterIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        (cls.root / "data" / "lucy").mkdir(parents=True, exist_ok=True)
        (cls.root / "logs").mkdir(parents=True, exist_ok=True)
        cls.runtime = LucyRuntime(project_root=cls.root)
        cls.router = CommandRouter(cls.runtime)

        # Seed a verified turn into training queue so dataset count > 0
        cls.runtime.training_queue.record_verified_interaction(
            instruction="How should we organize tools?",
            response="We keep verified tools under promoted_tools/.",
            verification_source="test_seed",
        )
        # Disconnect live connector for deterministic offline test execution
        cls.runtime.connector = None
        cls.runtime.lora_sleep_cycle.connector = None
        cls.runtime.personal_lora_alignment.connector = None
        # Mock compile_ollama_model so unit tests do not spawn slow external CLI subprocesses
        cls.runtime.lora_sleep_cycle.compile_ollama_model = lambda target_model="lucy:personal": {
            "compiled": True, "target_model": target_model, "returncode": 0
        }

    @classmethod
    def tearDownClass(cls) -> None:
        cls.runtime.graceful_shutdown("Stage 45 test suite finished")
        try:
            cls.tmp.cleanup()
        except Exception:
            pass

    def test_08_runtime_methods(self) -> None:
        status = self.runtime.personal_lora_status()
        self.assertEqual(status["stage"], STAGE)

        dataset = self.runtime.synthesize_personal_dataset()
        self.assertEqual(dataset["status"], "synthesized")

        gate = self.runtime.run_personal_alignment_gate()
        self.assertTrue(gate["passed"])

        sleep = self.runtime.trigger_personal_sleep_cycle()
        self.assertEqual(sleep["status"], "COMPLETED")

    def test_09_router_commands(self) -> None:
        # 1. Status command
        res1 = self.router.handle("personal lora status")
        self.assertIn("Personal LoRA Alignment status:", res1.message)
        self.assertIn("Stage: 45 personal lora style alignment", res1.message)

        # 2. Alignment test command
        res2 = self.router.handle("personal alignment test")
        self.assertIn("10-Question Personal Alignment Gate:", res2.message)
        self.assertIn("Passed: true", res2.message)

        # 3. Trigger personal sleep cycle command
        res3 = self.router.handle("trigger personal sleep cycle")
        self.assertIn("Personal LoRA Alignment Cycle:", res3.message)
        self.assertIn("Status: COMPLETED", res3.message)

        # 4. List personal adapters
        res4 = self.router.handle("list personal adapters")
        self.assertIn("Discovered Personal LoRA Adapters:", res4.message)


if __name__ == "__main__":
    unittest.main()
