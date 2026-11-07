"""
test_stage39_swarm_dispatcher.py
Unit tests for Stage 39: Swarm Dispatcher Bridge (Connecting LUCY to the 4 Groq bots).
"""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from backend.lucy_core.swarm_dispatcher import SwarmDispatcher, STAGE
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class Stage39SwarmDispatcherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.lucy_data = Path(self.temp_dir.name)
        self.dispatcher = SwarmDispatcher(self.lucy_data)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_01_initial_status_and_config(self) -> None:
        st = self.dispatcher.status()
        self.assertEqual(st["stage"], STAGE)
        self.assertEqual(st["swarm_dispatcher"], "active")
        self.assertEqual(st["total_bots_monitored"], 3)
        self.assertIn("writer", st)
        self.assertIn("checker", st)
        self.assertIn("director", st)
        self.assertIn("planner", st)
        self.assertIn("ENFORCED", st["boundary_safety"])

    def test_02_fast_socket_probe(self) -> None:
        start_time = time.time()
        probe = self.dispatcher.probe_bot("writer")
        elapsed = time.time() - start_time
        # Probing an offline port must be fast (under 0.5s)
        self.assertLess(elapsed, 0.5)
        self.assertEqual(probe["bot"], "writer")
        self.assertEqual(probe["port"], 5820)
        self.assertIn(probe["status"], ("ONLINE", "OFFLINE"))

    def test_03_sanitize_payload_boundary(self) -> None:
        dangerous_payload = {
            "instruction": "Write a fast prime checker in python.",
            "filename": "primes.py",
            "spine": {"lucy": "Private Persona Data"},
            "persona": "Living Unified Cognitive Yield",
            "memory": [{"fact": "Senin's private setup"}],
            "private_keys": ["gsk_private_secret_key"],
            "system_prompt": "You are Lucy",
        }
        sanitized = self.dispatcher.sanitize_payload(dangerous_payload)

        self.assertIn("instruction", sanitized)
        self.assertIn("filename", sanitized)
        self.assertNotIn("spine", sanitized)
        self.assertNotIn("persona", sanitized)
        self.assertNotIn("memory", sanitized)
        self.assertNotIn("private_keys", sanitized)
        self.assertNotIn("system_prompt", sanitized)

    def test_04_dispatch_write_offline_fallback(self) -> None:
        res = self.dispatcher.dispatch_write(
            instruction="Create a simple hello.py file",
            filename="hello.py",
        )
        self.assertIsInstance(res, dict)
        if res.get("offline"):
            self.assertIn("offline on port 5820", res["message"])
            self.assertFalse(res["success"])

        # History was logged
        history = self.dispatcher.history()
        self.assertGreaterEqual(len(history), 1)
        self.assertEqual(history[0]["target_bot"], "writer")

    def test_05_dispatch_check_local_ast_fallback(self) -> None:
        # Valid code
        valid_code = "def add(a, b):\n    return a + b\n"
        res_valid = self.dispatcher.dispatch_check(code=valid_code, filepath="math_utils.py")
        self.assertIsInstance(res_valid, dict)
        if not res_valid.get("online"):
            self.assertTrue(res_valid.get("syntax_valid", False) or res_valid.get("ast_valid", False))
            self.assertEqual(res_valid["status"], "APPROVED")
        else:
            self.assertTrue(res_valid.get("ast_valid", False) or res_valid.get("status") in ("APPROVED", "COMPLETED"))

        # Invalid code
        invalid_code = "def broken(a, b\n    return a +"
        res_invalid = self.dispatcher.dispatch_check(code=invalid_code, filepath="broken.py")
        self.assertIsInstance(res_invalid, dict)
        if not res_invalid.get("online"):
            self.assertFalse(res_invalid.get("syntax_valid", True))
            self.assertEqual(res_invalid["status"], "SYNTAX_ERROR")
            self.assertGreaterEqual(len(res_invalid["issues"]), 1)
        else:
            self.assertFalse(res_invalid.get("ast_valid", True))
            self.assertIn(res_invalid.get("status"), ("REJECTED", "SYNTAX_ERROR", "ERROR"))

    def test_06_dispatch_director_offline_fallback(self) -> None:
        res = self.dispatcher.dispatch_director(
            blueprint="build stage 40 pipeline",
            stage="40",
        )
        self.assertIsInstance(res, dict)
        if res.get("offline"):
            self.assertIn("Director Bot is offline", res["message"])
            self.assertFalse(res["success"])


class Stage39RuntimeAndRouterIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = LucyRuntime(project_root=Path(__file__).resolve().parent.parent)
        cls.router = CommandRouter(cls.runtime)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.runtime.graceful_shutdown("Stage 39 test suite finished")

    def test_07_runtime_swarm_integration(self) -> None:
        st = self.runtime.swarm_status()
        self.assertEqual(st["stage"], STAGE)
        self.assertEqual(st["swarm_dispatcher"], "active")

        # Dispatch write via runtime
        write_res = self.runtime.dispatch_write("Write a calculator in python", filename="calc.py")
        self.assertIsInstance(write_res, dict)

        # Dispatch check via runtime
        check_res = self.runtime.dispatch_check("print('hello swarm')")
        self.assertIsInstance(check_res, dict)

    def test_08_router_swarm_commands(self) -> None:
        # Swarm status
        resp_status = self.router.handle("swarm status")
        self.assertIn("External Bot Swarm status:", resp_status.message)
        self.assertIn("Stage: 39 swarm dispatcher bridge", resp_status.message)
        self.assertIn("Writer Bot", resp_status.message)
        self.assertIn("Checker Bot", resp_status.message)
        self.assertIn("Director Bot", resp_status.message)

        # Dispatch write command
        resp_write = self.router.handle("dispatch write create helper.py with uuid utils")
        self.assertTrue(len(resp_write.message) > 0)

        # Dispatch check command with valid code
        resp_check_valid = self.router.handle("dispatch check def compute(): return 42")
        self.assertIn("Swarm Checker:", resp_check_valid.message)

        # Dispatch check command with syntax error
        resp_check_err = self.router.handle("dispatch check def bad(: syntax error")
        self.assertIn("Swarm Checker:", resp_check_err.message)

    def test_09_sovereign_hierarchy_policy(self) -> None:
        from backend.lucy_core.swarm_dispatcher import SOVEREIGN_POLICY
        self.assertIn("UNIDIRECTIONAL_AUTHORITY", SOVEREIGN_POLICY)
        self.assertIn("sovereign mind", SOVEREIGN_POLICY)

        # Check router swarm hierarchy and policy commands
        resp_h = self.router.handle("swarm hierarchy")
        self.assertIn("SOVEREIGN BOT HIERARCHY", resp_h.message)
        self.assertIn("MASTER / ORCHESTRATOR", resp_h.message)
        self.assertIn("WORKER TOOLS", resp_h.message)
        self.assertIn("UNIDIRECTIONAL CONTROL", resp_h.message)

        resp_p = self.router.handle("swarm policy")
        self.assertIn("SOVEREIGN BOT HIERARCHY", resp_p.message)

    def test_10_connect_swarm_and_runtime_methods(self) -> None:
        # Runtime swarm connectivity check
        swarm_conn = self.runtime.connect_swarm()
        self.assertIsInstance(swarm_conn, dict)
        self.assertIn("status", swarm_conn)
        self.assertIn("writer", swarm_conn)
        self.assertIn("checker", swarm_conn)
        self.assertIn("director", swarm_conn)
        self.assertIn("sovereign_policy", swarm_conn)

        # Router connect swarm command
        resp_conn = self.router.handle("connect swarm")
        self.assertIn("Senin AI Swarm Connection:", resp_conn.message)
        self.assertIn("Writer Bot", resp_conn.message)

        # Router connect writer
        resp_writer = self.router.handle("connect writer")
        self.assertIn("Writer Bot", resp_writer.message)
        self.assertIn("Status:", resp_writer.message)


if __name__ == "__main__":
    unittest.main()
