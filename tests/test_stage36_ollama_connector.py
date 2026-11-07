"""
test_stage36_ollama_connector.py
Stage 36 = Sovereign Local Ollama Connector & Verified LoRA Training Queue.

Verifies:
1. Ollama connector reports endpoint, online/offline status, and active adapters.
2. Graceful offline fallback: if Ollama is not running, returns deterministic spine message.
3. TrainingQueue logs verified samples and redacts sensitive tokens.
4. Modelfile generation with ADAPTER directive for hot-swapping.
5. Router commands: "ollama status", "training queue status".
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter
from backend.lucy_core.ollama_connector import OllamaConnector
from backend.lucy_core.training_queue import TrainingQueue


class TestStage36OllamaConnector(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "data" / "lucy").mkdir(parents=True, exist_ok=True)
        (self.root / "logs").mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _runtime_and_router(self):
        runtime = LucyRuntime(project_root=self.root)
        router = CommandRouter(runtime)
        return runtime, router

    def test_01_ollama_status_router_command(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("ollama status")
        self.assertIn("Ollama Sovereign Connector status:", response.message)
        self.assertIn("Stage: 36 local ollama sovereign connector", response.message)
        self.assertIn("Endpoint: http://localhost:11434", response.message)
        self.assertIn("Default Sovereign Model: qwen2.5:3b", response.message)

    def test_02_ollama_status_aliases_work(self) -> None:
        _, router = self._runtime_and_router()
        for cmd in ["ollama connector status", "local engine status", "local mind status"]:
            response = router.handle(cmd)
            self.assertIn("Ollama Sovereign Connector status:", response.message)

    def test_03_training_queue_status_router_command(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("training queue status")
        self.assertIn("Verified LoRA Training Queue status:", response.message)
        self.assertIn("Stage: 36 verified lora training queue", response.message)
        self.assertIn("Anti-Hallucination Gate: active", response.message)

    def test_04_ollama_graceful_offline_fallback(self) -> None:
        lucy_data = self.root / "data" / "lucy"
        # Fast unreachable endpoint to test offline fallback
        connector = OllamaConnector(lucy_data, endpoint="http://127.0.0.1:9999")
        self.assertFalse(connector.is_online())
        self.assertEqual(connector.list_local_models(), [])

        # Chat when offline -> deterministic spine message
        result = connector.chat_or_fallback("Hello Lucy")
        self.assertEqual(result["source"], "deterministic_spine")
        self.assertFalse(result["online"])
        self.assertIn("deterministic spine mode", result["message"])

    def test_05_adapter_detection(self) -> None:
        lucy_data = self.root / "data" / "lucy"
        connector = OllamaConnector(lucy_data)
        adapters_dir = lucy_data / "adapters"
        (adapters_dir / "lucy_memory_v1.safetensors").touch()
        (adapters_dir / "random_notes.txt").touch()

        active = connector.detect_active_adapters()
        self.assertEqual(active, ["lucy_memory_v1.safetensors"])

    def test_06_training_queue_records_and_redacts(self) -> None:
        lucy_data = self.root / "data" / "lucy"
        queue = TrainingQueue(lucy_data)

        # Record normal interaction
        res1 = queue.record_verified_interaction(
            instruction="How do I list files in Python?",
            response="Use os.listdir() or Path.iterdir().",
            verification_source="pytest_verified"
        )
        self.assertTrue(res1["recorded"])
        self.assertEqual(queue.count(), 1)

        # Record interaction with sensitive key -> verified redaction
        res2 = queue.record_verified_interaction(
            instruction="My groq key is sk-123456789012345678901234",
            response="Key received",
            verification_source="test_redaction"
        )
        self.assertTrue(res2["recorded"])
        self.assertTrue(res2["had_redactions"])

        # Check export format (Alpaca)
        export_file = lucy_data / "export_test.json"
        queue.export_alpaca_dataset(export_file)
        self.assertTrue(export_file.exists())

    def test_07_modelfile_generation_with_adapter(self) -> None:
        lucy_data = self.root / "data" / "lucy"
        queue = TrainingQueue(lucy_data)
        modelfile = queue.generate_modelfile_for_adapter("lucy_v1.safetensors", base_model="llama3.1:8b")
        self.assertIn("FROM llama3.1:8b", modelfile)
        self.assertIn("ADAPTER ./adapters/lucy_v1.safetensors", modelfile)
        self.assertIn("You are LUCY", modelfile)


if __name__ == "__main__":
    unittest.main()
