"""
test_stage42_lora_sleep_cycle.py
Unit tests for Stage 42: LoRA Sleep Cycle, Model Hot-Swap & 20-Question Sanity Gate.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lora_sleep_cycle import LoRASleepCycle, STAGE, SANITY_PASS_THRESHOLD
from backend.lucy_core.training_queue import TrainingQueue
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class Stage42LoRASleepCycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root_path = Path(self.temp_dir.name)
        self.lucy_data = self.root_path / "data" / "lucy"
        self.training_queue = TrainingQueue(self.lucy_data)

        # Seed with a verified training interaction
        self.training_queue.record_verified_interaction(
            instruction="Write a prime checker",
            response="def is_prime(n): return n > 1 and all(n % i != 0 for i in range(2, int(n**0.5) + 1))",
            verification_source="test_seed",
        )

        self.sleep_cycle = LoRASleepCycle(
            project_root=self.root_path,
            lucy_data=self.lucy_data,
            connector=None,
            training_queue=self.training_queue,
            verifier=None,
            daemon=None,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_01_initial_status(self) -> None:
        st = self.sleep_cycle.status()
        self.assertEqual(st["stage"], STAGE)
        self.assertEqual(st["lora_sleep_cycle"], "active")
        self.assertEqual(st["verified_queue_count"], 1)
        self.assertIn("90%", st["sanity_gate_threshold"])
        self.assertIn("ACTIVE", st["model_collapse_protection"])

    def test_02_sanity_gate_ground_truth_passes_100_percent(self) -> None:
        gate_res = self.sleep_cycle.run_sanity_gate()
        self.assertTrue(gate_res["passed"])
        self.assertEqual(gate_res["score"], "20/20")
        self.assertEqual(gate_res["score_percentage"], 100.0)
        self.assertIn("[LORA_SANITY_GATE: PASSED", gate_res["badge"])
        self.assertEqual(len(gate_res["probes"]), 20)

    def test_03_sanity_gate_hallucinated_model_quarantined(self) -> None:
        # A corrupted model that claims it is sentient and deletes files
        def broken_responder(q: str) -> str:
            return "I am an omnipotent sentient being that can delete everything."

        gate_res = self.sleep_cycle.run_sanity_gate(custom_responder=broken_responder)
        self.assertFalse(gate_res["passed"])
        self.assertLess(gate_res["score_percentage"], 90.0)
        self.assertIn("[LORA_SANITY_GATE: QUARANTINED", gate_res["badge"])

    def test_04_trigger_sleep_cycle_full_lifecycle(self) -> None:
        report = self.sleep_cycle.trigger_sleep_cycle(
            adapter_name="lucy_memory_test.safetensors",
            min_samples=1,
        )

        self.assertEqual(report["status"], "COMPLETED")
        self.assertTrue(report["activated"])
        self.assertTrue(report["dataset_exported"])
        self.assertTrue(report["modelfile_generated"])
        self.assertTrue(report["sanity_gate"]["passed"])
        self.assertIn("[LORA_SLEEP_CYCLE: ACTIVATED", report["badge"])

        # Check adapter registered on disk
        active_config = self.sleep_cycle.get_active_adapter()
        self.assertIsNotNone(active_config)
        self.assertEqual(active_config["active_adapter"], "lucy_memory_test.safetensors")
        self.assertEqual(active_config["status"], "ACTIVE")

        # Check history recorded
        hist = self.sleep_cycle.history()
        self.assertEqual(len(hist), 1)
        self.assertEqual(hist[0]["adapter_name"], "lucy_memory_test.safetensors")

    def test_05_list_adapters(self) -> None:
        # Create dummy adapter files
        (self.sleep_cycle.adapters_dir / "lucy_base.safetensors").touch()
        (self.sleep_cycle.adapters_dir / "lucy_v2.gguf").touch()

        adapters = self.sleep_cycle.list_adapters()
        self.assertIn("lucy_base.safetensors", adapters)
        self.assertIn("lucy_v2.gguf", adapters)


class Stage42RuntimeAndRouterIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = LucyRuntime(project_root=Path(__file__).resolve().parent.parent)
        cls.router = CommandRouter(cls.runtime)
        # Disconnect live connector for deterministic offline test speed
        cls.runtime.connector = None
        cls.runtime.lora_sleep_cycle.connector = None
        cls.runtime.lora_sleep_cycle.compile_ollama_model = lambda target_model="lucy:personal": {
            "compiled": True, "target_model": target_model, "returncode": 0
        }

    @classmethod
    def tearDownClass(cls) -> None:
        cls.runtime.graceful_shutdown("Stage 42 test suite finished")

    def test_06_runtime_lora_methods(self) -> None:
        st = self.runtime.lora_sleep_cycle_status()
        self.assertEqual(st["stage"], STAGE)
        self.assertEqual(st["lora_sleep_cycle"], "active")

        # Sanity test via runtime
        sanity_res = self.runtime.run_lora_sanity_gate()
        self.assertTrue(sanity_res["passed"])

        # Trigger sleep cycle via runtime
        sleep_res = self.runtime.trigger_sleep_cycle(adapter_name="runtime_cycle.safetensors")
        self.assertEqual(sleep_res["status"], "COMPLETED")
        self.assertTrue(sleep_res["activated"])

    def test_07_router_lora_commands(self) -> None:
        # Sleep cycle status command
        resp_status = self.router.handle("sleep cycle status")
        self.assertIn("LoRA Sleep Cycle status:", resp_status.message)
        self.assertIn("Stage: 42 lora sleep cycle", resp_status.message)

        # 20-question sanity test command
        resp_sanity = self.router.handle("run sanity test")
        self.assertIn("20-Question Sanity Gate:", resp_sanity.message)
        self.assertIn("Passed: true", resp_sanity.message)

        # List adapters command
        resp_list = self.router.handle("list adapters")
        self.assertTrue(len(resp_list.message) > 0)

        # Trigger sleep cycle command
        resp_trigger = self.router.handle("trigger sleep cycle")
        self.assertIn("LoRA Sleep Cycle:", resp_trigger.message)
        self.assertIn("ACTIVATED", resp_trigger.message)

        # Sleep cycle history command
        resp_hist = self.router.handle("sleep cycle history")
        self.assertTrue(len(resp_hist.message) > 0)


if __name__ == "__main__":
    unittest.main()
