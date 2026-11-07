"""
test_stage48_intent_dispatcher.py
Stage 48 = Autonomous Intent-to-Task Dispatcher (Natural Language -> Tool Execution).

Verifies:
1. Dispatcher reports Stage 48 and active status.
2. Accurate classification of hardware telemetry queries.
3. Accurate classification of process inspection queries.
4. Accurate classification of workspace search queries.
5. Accurate classification of code synthesis requests.
6. Accurate classification of personal LoRA sleep cycle requests.
7. Autonomous dispatch of telemetry execution.
8. Autonomous dispatch of code synthesis tasks into the daemon queue.
9. Full CommandRouter & LucyRuntime integration.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.intent_dispatcher import IntentDispatcher, IntentType, STAGE
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class MockRuntime:
    """Mock runtime for testing autonomous dispatcher execution."""
    def __init__(self) -> None:
        self.submitted_tasks = []

    def system_telemetry(self) -> dict:
        return {
            "ram": {"available_mb": 8500, "memory_load_percent": 45},
            "disk": {"free_gb": 190.5, "percent_free": 40.0},
            "power": {"ac_line_status": "Plugged In", "battery_percent": "65%"},
        }

    def probe_network_ports(self) -> dict:
        return {
            "active_services": 1,
            "total_probed": 4,
            "ports": {
                "11434": {"service": "Ollama", "status": "OPEN (LISTENING)"},
            },
        }

    def inspect_processes(self, query: str = "", limit: int = 10) -> list:
        return [{"pid": "1234", "name": "python.exe", "memory": "25,000 K"}]

    def search_workspace_files(self, pattern: str = "", extension: str = "", search_content: bool = False, limit: int = 10) -> list:
        return [{"name": "target_file.py", "path": "C:/senin/target_file.py", "size_bytes": 1024}]

    def submit_synthesis_task(self, instruction: str) -> dict:
        task_id = f"task_{len(self.submitted_tasks) + 1}"
        self.submitted_tasks.append((task_id, instruction))
        return {"submitted": True, "task_id": task_id, "instruction": instruction}

    def clean_sandbox_cache(self, dry_run: bool = False) -> dict:
        return {"files_found": 3, "bytes_freed": 4096}

    def trigger_personal_sleep_cycle(self) -> dict:
        return {"badge": "[PASSED]", "adapter_name": "lucy_personal_v1.safetensors", "dataset_record_count": 12}


class Stage48IntentDispatcherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_runtime = MockRuntime()
        self.dispatcher = IntentDispatcher(runtime=self.mock_runtime)

    def test_01_initial_status(self) -> None:
        status = self.dispatcher.status()
        self.assertEqual(status["stage"], STAGE)
        self.assertEqual(status["intent_dispatcher"], "active")
        self.assertEqual(status["dispatch_count"], 0)
        self.assertIn(IntentType.SYSTEM_TELEMETRY, status["supported_intents"])
        self.assertIn(IntentType.CODE_SYNTHESIS_REQUEST, status["supported_intents"])

    def test_02_classify_telemetry_intents(self) -> None:
        queries = [
            "How much RAM do I have left?",
            "Can you check the battery status?",
            "What is my disk usage on C drive?",
            "Show hardware status please",
        ]
        for q in queries:
            cl = self.dispatcher.classify_intent(q)
            self.assertEqual(cl.intent_type, IntentType.SYSTEM_TELEMETRY)
            self.assertGreaterEqual(cl.confidence, 0.90)

    def test_03_classify_process_intents(self) -> None:
        cl1 = self.dispatcher.classify_intent("Check if python is running")
        self.assertEqual(cl1.intent_type, IntentType.PROCESS_INSPECTION)

        cl2 = self.dispatcher.classify_intent("What processes are running right now?")
        self.assertEqual(cl2.intent_type, IntentType.PROCESS_INSPECTION)

    def test_04_classify_workspace_search_intents(self) -> None:
        cl1 = self.dispatcher.classify_intent("Where is file test_runner.py?")
        self.assertEqual(cl1.intent_type, IntentType.WORKSPACE_SEARCH)
        self.assertIn("test_runner.py", cl1.extracted_target)

        cl2 = self.dispatcher.classify_intent("Find file config.json")
        self.assertEqual(cl2.intent_type, IntentType.WORKSPACE_SEARCH)

    def test_05_classify_code_synthesis_intents(self) -> None:
        cl = self.dispatcher.classify_intent("Write a python script that monitors network traffic")
        self.assertEqual(cl.intent_type, IntentType.CODE_SYNTHESIS_REQUEST)
        self.assertIn("monitors network traffic", cl.extracted_target)

    def test_06_classify_lora_sleep_cycle_intents(self) -> None:
        cl = self.dispatcher.classify_intent("Please train personal lora and update weights")
        self.assertEqual(cl.intent_type, IntentType.LORA_SLEEP_CYCLE)

    def test_07_dispatch_telemetry_execution(self) -> None:
        res = self.dispatcher.dispatch("How much free memory do I have?")
        self.assertIsNotNone(res)
        self.assertTrue(res["handled"])
        self.assertEqual(res["intent"], IntentType.SYSTEM_TELEMETRY)
        self.assertIn("RAM: 8500 MB free", res["message"])
        self.assertIn("Disk C: 190.5 GB free", res["message"])

    def test_08_dispatch_code_synthesis_task(self) -> None:
        res = self.dispatcher.dispatch("Write a script to backup text files")
        self.assertIsNotNone(res)
        self.assertTrue(res["handled"])
        self.assertEqual(res["intent"], IntentType.CODE_SYNTHESIS_REQUEST)
        self.assertIn("Code Synthesis Task Queued", res["message"])
        self.assertEqual(len(self.mock_runtime.submitted_tasks), 1)


class Stage48RuntimeAndRouterIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "data" / "lucy").mkdir(parents=True, exist_ok=True)
        (self.root / "logs").mkdir(parents=True, exist_ok=True)
        self.runtime = LucyRuntime(project_root=self.root)
        self.router = CommandRouter(self.runtime)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_09_runtime_and_router_intent_methods(self) -> None:
        status = self.runtime.intent_dispatcher_status()
        self.assertEqual(status["stage"], STAGE)

        # Classification check
        cl = self.runtime.classify_user_intent("How much free disk space is there?")
        self.assertEqual(cl["intent_type"], IntentType.SYSTEM_TELEMETRY)

        # Router status command
        res1 = self.router.handle("intent status")
        self.assertIn("Autonomous Intent Dispatcher status:", res1.message)

        # Router classify command
        res2 = self.router.handle("classify Check if python is running")
        self.assertIn("Natural Language Intent Classification:", res2.message)
        self.assertIn("PROCESS_INSPECTION", res2.message)

        # Natural language input through lucy_respond executes autonomous dispatch
        nl_reply = self.runtime.lucy_respond("How much RAM and disk space do I have?")
        self.assertIn("[Telemetry Check]", nl_reply)
        self.assertIn("RAM:", nl_reply)


if __name__ == "__main__":
    unittest.main()
