"""
test_stage43_conversational_memory.py
Stage 43 = Cross-Session Conversational Memory & Multi-Turn Context Engine.

Verifies:
1. Engine reports Stage 43 and active context limits.
2. Record turn and sliding context window management.
3. Credential and API key redaction in conversational history.
4. Cross-session continuity tracker & previous session recap generation.
5. In-memory sliding buffer reset without deleting permanent audit logs.
6. Augmented prompt assembly with memories, talking style, and dialogue history.
7. LucyRuntime Stage 43 method integration.
8. CommandRouter Stage 43 command routing and formatting.
9. End-to-end multi-turn conversation flow preserving context across turns.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.conversational_memory import ConversationalMemoryEngine, STAGE
from backend.lucy_core.memory import MemorySystem
from backend.lucy_core.learning import LearningSystem
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class Stage43ConversationalMemoryEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.lucy_data = self.root / "data" / "lucy"
        self.lucy_data.mkdir(parents=True, exist_ok=True)
        self.memory = MemorySystem(self.lucy_data / "memory")
        self.learning = LearningSystem(self.lucy_data / "learning")
        self.engine = ConversationalMemoryEngine(
            lucy_data=self.lucy_data,
            memory_system=self.memory,
            learning_system=self.learning,
            max_context_turns=3,
        )

    def tearDown(self) -> None:
        try:
            self.tmp.cleanup()
        except Exception:
            pass

    def test_01_initial_status(self) -> None:
        status = self.engine.status()
        self.assertEqual(status["stage"], STAGE)
        self.assertEqual(status["conversational_memory"], "active")
        self.assertEqual(status["total_disk_turns"], 0)
        self.assertEqual(status["active_sliding_context_turns"], 0)
        self.assertEqual(status["max_context_turns"], 3)
        self.assertFalse(status["context_cleared"])

    def test_02_record_turn_and_sliding_context(self) -> None:
        res1 = self.engine.record_turn("What is your name?", "I am Lucy.", source="test")
        self.assertTrue(res1["recorded"])
        self.assertTrue(res1["logged_to_disk"])

        self.engine.record_turn("What is my active project?", "Your active project is Lucy.", source="test")
        self.engine.record_turn("Can you help me with tests?", "Yes, I can run tests.", source="test")
        self.engine.record_turn("Let's add Stage 43.", "Starting Stage 43 now.", source="test")

        # Max turns is 3, so sliding context should return the latest 3 turns
        context = self.engine.get_sliding_context()
        self.assertEqual(len(context), 3)
        self.assertEqual(context[0]["input"], "What is my active project?")
        self.assertEqual(context[-1]["input"], "Let's add Stage 43.")

        # Total disk history should have all 4
        disk_all = self.engine.load_disk_history()
        self.assertEqual(len(disk_all), 4)

    def test_03_credential_redaction_in_context(self) -> None:
        mock_key = "gsk_mock_test_key_dummy_token_for_redaction_check_00000"
        res = self.engine.record_turn(
            user_text=f"My Groq key is {mock_key} please save it",
            reply_text="Your key sk-123456789012345678901234 has been noted.",
        )
        turn = res["turn"]
        self.assertNotIn(mock_key, turn["input"])
        self.assertIn("[redacted-credential]", turn["input"])
        self.assertNotIn("sk-123456789012345678901234", turn["reply"])
        self.assertIn("[redacted-credential]", turn["reply"])

    def test_04_session_recap_generation(self) -> None:
        # Before turns
        empty_recap = self.engine.get_session_recap()
        self.assertFalse(empty_recap["has_history"])
        self.assertIn("No previous conversation history", empty_recap["recap_text"])

        # Add turns
        self.engine.record_turn("Run system status check", "System status is nominal.")
        self.engine.record_turn("Test Ollama model response", "Model qwen2.5:3b responded cleanly.")

        recap = self.engine.get_session_recap()
        self.assertTrue(recap["has_history"])
        self.assertEqual(recap["total_turns"], 2)
        self.assertIn("Previous conversation history: 2 turns recorded.", recap["recap_text"])
        self.assertIn("Run system status check", recap["recent_inputs"])
        self.assertIn("Test Ollama model response", recap["recent_inputs"])

    def test_05_clear_active_context_preserves_disk_log(self) -> None:
        self.engine.record_turn("Message 1", "Reply 1")
        self.engine.record_turn("Message 2", "Reply 2")

        self.assertEqual(len(self.engine.get_sliding_context()), 2)
        self.assertEqual(len(self.engine.load_disk_history()), 2)

        # Clear active context
        clear_res = self.engine.clear_active_context()
        self.assertEqual(clear_res["status"], "cleared")
        self.assertEqual(clear_res["retained_history_turns"], 2)

        # Sliding context should now be empty
        self.assertEqual(len(self.engine.get_sliding_context()), 0)
        self.assertTrue(self.engine.status()["context_cleared"])

        # But permanent disk log is still intact
        self.assertEqual(len(self.engine.load_disk_history()), 2)

    def test_06_build_augmented_prompt(self) -> None:
        self.memory.remember("Lucy is built for local sovereign privacy.")
        self.learning.add_style_preference("Keep answers concise and punchy.")
        self.engine.record_turn("What model are we using?", "We are using qwen2.5:3b.")

        payload = self.engine.build_augmented_prompt(
            user_input="Can we run another test?",
            system_prompt_base="You are Lucy, local digital operator.",
            active_project="Project Lucy",
        )

        prompt = payload["augmented_system_prompt"]
        self.assertIn("You are Lucy, local digital operator.", prompt)
        self.assertIn("[Active Project]: Project Lucy", prompt)
        self.assertIn("Keep answers concise and punchy.", prompt)
        self.assertIn("Lucy is built for local sovereign privacy.", prompt)
        self.assertIn("What model are we using?", prompt)
        self.assertIn("We are using qwen2.5:3b.", prompt)
        self.assertGreater(payload["approx_tokens"], 10)


class Stage43RuntimeAndRouterIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "data" / "lucy").mkdir(parents=True, exist_ok=True)
        (self.root / "logs").mkdir(parents=True, exist_ok=True)
        self.runtime = LucyRuntime(project_root=self.root)
        self.router = CommandRouter(self.runtime)

    def tearDown(self) -> None:
        try:
            self.tmp.cleanup()
        except Exception:
            pass

    def test_07_runtime_integration(self) -> None:
        status = self.runtime.conversational_memory_status()
        self.assertEqual(status["stage"], STAGE)
        self.assertEqual(status["conversational_memory"], "active")

        recap = self.runtime.session_recap()
        self.assertIn("recap_text", recap)

        clear = self.runtime.clear_session_context()
        self.assertEqual(clear["status"], "cleared")

    def test_08_router_commands(self) -> None:
        # 1. Status command
        res1 = self.router.handle("session memory status")
        self.assertIn("Conversational Memory & Context Engine status:", res1.message)
        self.assertIn("Stage: 43 conversational memory context engine", res1.message)

        # 2. Recap command
        res2 = self.router.handle("session recap")
        self.assertIn("Previous Session Recap:", res2.message)
        self.assertIn("Stage: 43 conversational memory context engine", res2.message)

        # 3. Clear context command
        res3 = self.router.handle("clear session context")
        self.assertIn("Conversational Context Buffer Reset:", res3.message)
        self.assertIn("Status: cleared", res3.message)

    def test_09_multi_turn_conversation_flow(self) -> None:
        # Trigger conversational chat
        reply1 = self.runtime.conversational_chat("Tell me about our current project.")
        self.assertTrue(len(reply1.get("message", "")) > 0)

        # Check that conversational memory recorded the interaction
        status = self.runtime.conversational_memory_status()
        self.assertGreaterEqual(status["total_disk_turns"], 1)
        self.assertGreaterEqual(status["active_sliding_context_turns"], 1)

        # Follow up question
        reply2 = self.runtime.conversational_chat("What did I just ask you?")
        self.assertTrue(len(reply2.get("message", "")) > 0)


if __name__ == "__main__":
    unittest.main()
