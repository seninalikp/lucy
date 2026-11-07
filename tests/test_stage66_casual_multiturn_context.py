"""
test_stage66_casual_multiturn_context.py
Stage 66 = Native Multi-Turn Message Arrays & Coreference Resolver.

Verifies:
1. CoreferenceTracker status and readiness.
2. Native OpenAI/Ollama messages array format structure.
3. Shorthand "why?" binds to previous statement / active topic.
4. Shorthand "do that one" binds to suggested action.
5. Shorthand "what about the other file?" binds to secondary entity.
6. Casual vs. Operator turn classification accuracy.
7. Casual context gating mutes noisy workspace/task telemetry blocks.
8. OllamaConnector generates valid /api/chat payload with multi-turn messages array.
9. MultiProviderPool accepts and routes native messages array.
10. CommandRouter routes 'dialogue status' / '/dialogue' commands cleanly.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.dialogue_tracker import CoreferenceTracker, STAGE as TRACKER_STAGE
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class TestStage66CasualMultiTurnContext(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "data" / "lucy").mkdir(parents=True, exist_ok=True)
        (self.root / "logs").mkdir(parents=True, exist_ok=True)
        self.runtime = LucyRuntime(project_root=self.root)
        self.convo_mem = self.runtime.conversational_memory
        self.tracker = self.convo_mem.dialogue_tracker
        self.router = CommandRouter(self.runtime)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_01_coreference_tracker_status_and_readiness(self) -> None:
        """1. CoreferenceTracker reports Stage 66 active status."""
        st = self.tracker.status()
        self.assertEqual(st["stage"], TRACKER_STAGE)
        self.assertEqual(st["dialogue_tracker"], "active")
        self.assertIn("current_topic", st)
        self.assertIn("active_entities", st)

    def test_02_native_messages_array_format_structure(self) -> None:
        """2. build_messages_array produces true [{"role": ...}] discrete turns."""
        self.convo_mem.record_turn(
            user_text="What stack do you recommend for our metrics service?",
            assistant_reply="I recommend FastAPI with PostgreSQL for high throughput.",
            run_auto_extract=False,
        )

        messages = self.convo_mem.build_messages_array(
            user_input="Sounds good, tell me more.",
            system_prompt_base="You are Lucy.",
        )

        self.assertGreaterEqual(len(messages), 3)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(messages[1]["content"], "What stack do you recommend for our metrics service?")
        self.assertEqual(messages[2]["role"], "assistant")
        self.assertIn("FastAPI with PostgreSQL", messages[2]["content"])
        self.assertEqual(messages[-1]["role"], "user")

    def test_03_shorthand_why_resolves_to_previous_statement(self) -> None:
        """3. Shorthand 'why?' automatically binds to the previous statement."""
        self.tracker.observe_turn(
            user_text="Should we use PostgreSQL or Redis for persistent storage?",
            reply_text="PostgreSQL is recommended because it provides relational integrity and ACID guarantees.",
        )

        resolved, meta = self.tracker.resolve_shorthand("why?")
        self.assertTrue(meta["is_shorthand"])
        self.assertEqual(meta["shorthand_type"], "inquiry_justification")
        self.assertIn("relational integrity", resolved.lower())

    def test_04_shorthand_action_do_that_resolves_to_previous_suggestion(self) -> None:
        """4. Shorthand 'do that' binds to the suggested action in the previous turn."""
        self.tracker.observe_turn(
            user_text="How do we fix the database schema drift?",
            reply_text="We could run a migration script to update the table definitions.",
        )

        resolved, meta = self.tracker.resolve_shorthand("do that")
        self.assertTrue(meta["is_shorthand"])
        self.assertEqual(meta["shorthand_type"], "action_affirmation")
        self.assertIn("migration script", resolved.lower())

    def test_05_shorthand_pronoun_other_file_resolves_to_entity(self) -> None:
        """5. 'what about the other file?' binds to secondary tracked entity."""
        self.tracker.observe_turn(
            user_text="I modified server.py and router.py today.",
            reply_text="Got it. server.py handles the HTTP API endpoints.",
        )

        resolved, meta = self.tracker.resolve_shorthand("what about the other file?")
        self.assertTrue(meta["is_shorthand"])
        self.assertEqual(meta["shorthand_type"], "alternate_entity")
        self.assertIn("router.py", resolved.lower())

    def test_06_casual_vs_operator_classification(self) -> None:
        """6. Accurately distinguishes casual banter from system operator commands."""
        # Casual queries
        self.assertTrue(self.tracker.is_casual_turn("hey lucy"))
        self.assertTrue(self.tracker.is_casual_turn("how are you doing today?"))
        self.assertTrue(self.tracker.is_casual_turn("tell me a joke"))
        self.assertTrue(self.tracker.is_casual_turn("what do you think about clean architecture?"))

        # Operator / system queries
        self.assertFalse(self.tracker.is_casual_turn("scan the workspace for modified files"))
        self.assertFalse(self.tracker.is_casual_turn("add task to test docker connectivity"))
        self.assertFalse(self.tracker.is_casual_turn("run git status"))
        self.assertFalse(self.tracker.is_casual_turn("inspect backend/server.py"))

    def test_07_casual_context_gating_mutes_noisy_telemetry(self) -> None:
        """7. Casual mode mutes noisy open tasks and git telemetry from the system prompt."""
        # Casual prompt
        casual_payload = self.convo_mem.build_augmented_prompt(
            user_input="hey lucy, how's your day going?",
            system_prompt_base="You are Lucy.",
            open_tasks=["task 1", "task 2", "task 3"],
        )
        self.assertTrue(casual_payload["is_casual"])
        casual_sys = casual_payload["messages"][0]["content"]
        self.assertNotIn("[Open Tasks]:", casual_sys)

        # Operator prompt
        operator_payload = self.convo_mem.build_augmented_prompt(
            user_input="run git status and check task 1",
            system_prompt_base="You are Lucy.",
            open_tasks=["task 1", "task 2", "task 3"],
        )
        self.assertFalse(operator_payload["is_casual"])
        operator_sys = operator_payload["messages"][0]["content"]
        self.assertIn("[Open Tasks]:", operator_sys)

    def test_08_ollama_connector_chat_api_payload_generation(self) -> None:
        """8. OllamaConnector.chat handles messages array gracefully."""
        conn = self.runtime.ollama_connector
        res = conn.chat(messages=[
            {"role": "system", "content": "You are Lucy."},
            {"role": "user", "content": "Hello."},
        ])
        self.assertIn("source", res)
        # In offline test environment, falls back cleanly without crashing
        self.assertIn(res["source"], {"local_ollama", "deterministic_spine"})

    def test_09_multi_provider_pool_accepts_and_routes_messages_array(self) -> None:
        """9. ExternalTools / MultiProviderPool accepts messages array parameter."""
        tools = self.runtime.external_tools
        res = tools.chat(
            prompt="Hello",
            system_prompt="You are Lucy.",
            messages=[
                {"role": "system", "content": "You are Lucy."},
                {"role": "user", "content": "Hello"},
            ],
            provider="unsupported_dummy_provider",
        )
        self.assertFalse(res["ok"])
        self.assertEqual(res["provider"], "none")

    def test_10_router_dialogue_status_command(self) -> None:
        """10. CommandRouter returns structured JSON for 'dialogue status'."""
        resp = self.router.handle("dialogue status")
        self.assertIn("dialogue_tracker", resp.message)
        self.assertIn("current_topic", resp.message)


if __name__ == "__main__":
    unittest.main()
