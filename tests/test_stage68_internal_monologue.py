"""
test_stage68_internal_monologue.py
Stage 68: Sovereign Internal Monologue & Pre-Output Verification Spine Unit Tests.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.internal_monologue import (
    InternalMonologueSpine,
    ThoughtRecord,
    STAGE as STAGE_68,
)
from backend.lucy_core.lucy_runtime import LucyRuntime


class TestStage68InternalMonologue(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.spine = InternalMonologueSpine()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_01_thought_extraction_and_stripping(self) -> None:
        raw_output = (
            "<thought>\n"
            "User is asking about the database port.\n"
            "Verified port is 5432.\n"
            "Tone: direct and concise.\n"
            "</thought>\n"
            "PostgreSQL is running on port 5432."
        )
        clean_text, record = self.spine.process("what port is the db on?", raw_output)

        self.assertEqual(clean_text, "PostgreSQL is running on port 5432.")
        self.assertIn("User is asking about the database port.", record.raw_thought)
        self.assertNotIn("<thought>", clean_text)
        self.assertNotIn("</thought>", clean_text)

    def test_02_response_unwrapping(self) -> None:
        raw_output = (
            "<thought>Checking status</thought>\n"
            "<response>System is fully operational.</response>"
        )
        clean_text, record = self.spine.process("status?", raw_output)
        self.assertEqual(clean_text, "System is fully operational.")
        self.assertIn("Checking status", record.raw_thought)

    def test_03_vibe_detection(self) -> None:
        vibe_debug = self.spine.parse_user_vibe("I have an error traceback in router.py, please help fix")
        self.assertEqual(vibe_debug, "debugging_high_focus")

        vibe_win = self.spine.parse_user_vibe("finally! all tests passed cleanly!")
        self.assertEqual(vibe_win, "relief_victory")

        vibe_night = self.spine.parse_user_vibe("it is midnight and i'm tired, grinding on this")
        self.assertEqual(vibe_night, "late_night_grind")

        vibe_casual = self.spine.parse_user_vibe("yo lucy, how are you doing bro?")
        self.assertEqual(vibe_casual, "casual_banter")

    def test_04_bot_trope_sanitization(self) -> None:
        raw = "Certainly! I would be delighted to help you. I apologize for the confusion, as an AI language model I am programmed to assist."
        clean, _ = self.spine.process("help me", raw)
        self.assertNotIn("as an ai language model", clean.lower())
        self.assertNotIn("i would be delighted to help you", clean.lower())
        self.assertNotIn("i apologize for the confusion", clean.lower())
        self.assertIn("my bad", clean.lower())

    def test_05_anti_hallucination_action_claims(self) -> None:
        # Without receipts, claiming to have created a file is flagged and sanitized
        raw = "I have created file database_schema.sql and configured it."
        clean, record = self.spine.process("did you make the schema?", raw, receipts=None)

        self.assertTrue(len(record.flagged_claims) > 0)
        self.assertIn("unverified_action_on_database_schema.sql", record.flagged_claims)
        self.assertNotIn("I have created file database_schema.sql", clean)
        self.assertIn("I am referencing database_schema.sql", clean)

    def test_06_action_claim_permitted_with_receipts(self) -> None:
        # With receipts, action claim is permitted
        raw = "I have created file database_schema.sql and configured it."
        receipts = [{"receipt_id": "rcpt_001", "action": "create_file", "file": "database_schema.sql"}]
        clean, record = self.spine.process("did you make the schema?", raw, receipts=receipts)

        self.assertEqual(len(record.flagged_claims), 0)
        self.assertIn("I have created file database_schema.sql", clean)

    def test_07_debug_format_view(self) -> None:
        record = ThoughtRecord(
            user_input="How is Lucy configured?",
            raw_thought="User is checking runtime telemetry.\nVerified Ollama is active on 11434.",
            clean_response="Lucy is running in sovereign terminal mode with Ollama on port 11434.",
            user_vibe="collaborative_operator",
            verified_facts=["Ollama active on 11434"],
            tone_calibration="peer_engineer_direct",
        )
        debug_view = record.format_debug_view()
        self.assertIn("[Lucy Internal Monologue Scratchpad]", debug_view)
        self.assertIn("Timestamp:", debug_view)
        self.assertIn("User Query: 'How is Lucy configured?'", debug_view)
        self.assertIn("Verified Ollama is active on 11434.", debug_view)

    def test_08_runtime_internal_monologue_status(self) -> None:
        runtime = LucyRuntime()
        status = runtime.internal_monologue_status()
        self.assertEqual(status.get("stage"), STAGE_68)
        self.assertEqual(status.get("internal_monologue"), "active")
        self.assertIn("total_thoughts_recorded", status)

    def test_09_runtime_respond_thought_command(self) -> None:
        runtime = LucyRuntime()
        # Seed an interaction so a thought exists
        runtime.lucy_respond("hello lucy")

        thought_output = runtime.lucy_respond("/thought")
        self.assertIn("[Lucy Internal Monologue Scratchpad]", thought_output)

        plural_output = runtime.lucy_respond("/thoughts")
        self.assertIn("[Lucy Internal Monologue Scratchpad]", plural_output)

    def test_10_conversational_chat_processes_internal_monologue(self) -> None:
        runtime = LucyRuntime()
        res = runtime.conversational_chat("Tell me about Drift Music")
        self.assertIsInstance(res, dict)
        self.assertIn("message", res)

        # Last thought should be populated
        last_t = runtime.last_thought()
        self.assertIsInstance(last_t, dict)
        self.assertIn("user_input", last_t)
        self.assertIn("user_vibe", last_t)


if __name__ == "__main__":
    unittest.main()
