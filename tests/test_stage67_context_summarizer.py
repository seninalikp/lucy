"""
test_stage67_context_summarizer.py
Stage 67: Rolling Episodic Context Summarizer & Context Window Guard Unit Tests.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.context_summarizer import (
    EpisodicContextSummarizer,
    EpisodicSessionDigest,
    ContextWindowGuard,
    estimate_tokens,
    STAGE as STAGE_67,
)
from backend.lucy_core.conversational_memory import ConversationalMemoryEngine
from backend.lucy_core.lucy_runtime import LucyRuntime


class TestStage67ContextSummarizer(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_path = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_01_token_estimation_and_digest_structure(self) -> None:
        text = "Hello world! This is a test of the token estimator."
        toks = estimate_tokens(text)
        self.assertGreater(toks, 5)
        self.assertEqual(estimate_tokens(""), 0)

        digest = EpisodicSessionDigest()
        digest.summary_points.append("Discussed initial setup")
        digest.key_entities.append("FastAPI")
        digest.decisions_made.append("Use port 8000")
        digest.vibe_spectrum.add("casual_banter")
        digest.total_compressed_turns = 3

        d_dict = digest.to_dict()
        self.assertEqual(d_dict["total_compressed_turns"], 3)
        self.assertIn("FastAPI", d_dict["key_entities"])
        self.assertIn("casual_banter", d_dict["vibe_spectrum"])

        reloaded = EpisodicSessionDigest.from_dict(d_dict)
        self.assertEqual(reloaded.total_compressed_turns, 3)
        self.assertEqual(reloaded.key_entities, ["FastAPI"])

    def test_02_signal_extraction_decisions_entities_vibes(self) -> None:
        summarizer = EpisodicContextSummarizer()
        user_input = "Hey Lucy, let's switch to Neovim and configure server.py on port 8080. We had a broken traceback earlier."
        reply = "Got it. I fixed the error and all tests passed cleanly."

        signals = summarizer.extract_turn_signals(user_input, reply)

        # Check entities
        self.assertTrue(any("server.py" in ent for ent in signals["entities"]))
        self.assertTrue(any("port 8080" in ent.lower() for ent in signals["entities"]))
        self.assertTrue(any("Neovim" in ent for ent in signals["entities"]))

        # Check decisions
        self.assertTrue(len(signals["decisions"]) >= 1)
        self.assertTrue(any("neovim" in d.lower() for d in signals["decisions"]))

        # Check vibes
        self.assertIn("focused_debugging", signals["vibes"])
        self.assertIn("relief_satisfaction", signals["vibes"])

    def test_03_compress_older_turns_preserves_recent(self) -> None:
        summarizer = EpisodicContextSummarizer(lucy_data=self.data_path, max_sliding_turns=4)

        turns = [
            {"input": f"Turn {i}: let's use tool_{i}.py", "reply": f"Acknowledged {i}"}
            for i in range(1, 9)  # 8 turns
        ]

        remaining, digest = summarizer.compress_older_turns(turns, keep_recent=3)

        # Remaining should be exactly the last 3 turns
        self.assertEqual(len(remaining), 3)
        self.assertEqual(remaining[0]["input"], "Turn 6: let's use tool_6.py")
        self.assertEqual(remaining[-1]["input"], "Turn 8: let's use tool_8.py")

        # Digest should have compressed 5 turns
        self.assertEqual(digest.total_compressed_turns, 5)
        self.assertGreater(len(digest.summary_points), 0)

    def test_04_format_context_block_injection(self) -> None:
        digest = EpisodicSessionDigest()
        digest.summary_points = ["Discussed Drift Music audio pipeline", "Optimized buffer chunk size"]
        digest.decisions_made = ["Set chunk size to 1024", "Use port 8000"]
        digest.key_entities = ["Drift Music", "FastAPI", "port 8000"]
        digest.vibe_spectrum = {"focused_debugging", "relief_satisfaction"}
        digest.total_compressed_turns = 6

        block = digest.format_context_block()
        self.assertIn("[Session Episodic Memory (6 earlier turns compressed)]:", block)
        self.assertIn("Drift Music", block)
        self.assertIn("1024", block)
        self.assertIn("focused_debugging", block)

    def test_05_context_window_guard_truncation_and_pruning(self) -> None:
        guard = ContextWindowGuard(max_tokens=60)

        # Build verbose messages
        messages = [
            {"role": "system", "content": "You are Lucy."},
            {"role": "user", "content": "Tell me about the project."},
            {"role": "assistant", "content": "A" * 800},  # Very long reply
            {"role": "user", "content": "What else?"},
            {"role": "assistant", "content": "B" * 600},
            {"role": "user", "content": "And now?"},
        ]

        guarded = guard.guard_messages(messages)

        # Should retain system prompt at 0 and current user at last
        self.assertEqual(guarded[0]["role"], "system")
        self.assertEqual(guarded[-1]["role"], "user")
        self.assertEqual(guarded[-1]["content"], "And now?")

        # Estimated tokens should be within reasonable bounds
        total_toks = guard.estimate_messages_tokens(guarded)
        self.assertLessEqual(total_toks, 200)

    def test_06_conversational_memory_rolling_compression(self) -> None:
        engine = ConversationalMemoryEngine(
            lucy_data=self.data_path,
            max_context_turns=4,
        )

        # Record 8 turns
        for i in range(1, 9):
            engine.record_turn(
                user_text=f"Turn {i}: let's configure service_{i}.py",
                reply_text=f"Confirmed service {i} is ready.",
                run_auto_extract=False,
            )

        # In-memory turns should be capped around max_context_turns
        self.assertLessEqual(len(engine._in_memory_turns), 4)

        # Episodic digest should have captured compressed turns
        digest_data = engine.get_episodic_digest()
        self.assertGreater(digest_data["total_compressed_turns"], 0)
        self.assertTrue(engine.context_summarizer.has_digest())

    def test_07_build_messages_array_injects_episodic_digest(self) -> None:
        engine = ConversationalMemoryEngine(
            lucy_data=self.data_path,
            max_context_turns=3,
        )

        for i in range(1, 7):
            engine.record_turn(
                user_text=f"Decision {i}: we will use FastAPI and port {8000 + i}",
                reply_text=f"Done with {i}.",
                run_auto_extract=False,
            )

        # Messages array should have episodic context block in system message
        messages = engine.build_messages_array(
            user_input="How is the server configured?",
            system_prompt_base="You are Lucy.",
            is_casual=False,
        )

        self.assertGreaterEqual(len(messages), 2)
        system_content = messages[0]["content"]
        self.assertIn("[Session Episodic Memory", system_content)
        self.assertIn("Decision", system_content)

    def test_08_clear_active_context_clears_digest(self) -> None:
        engine = ConversationalMemoryEngine(
            lucy_data=self.data_path,
            max_context_turns=3,
        )

        for i in range(5):
            engine.record_turn(f"hello {i}", f"world {i}", run_auto_extract=False)

        self.assertTrue(engine.context_summarizer.has_digest())

        engine.clear_active_context()

        self.assertFalse(engine.context_summarizer.has_digest())
        self.assertEqual(engine.get_episodic_digest()["total_compressed_turns"], 0)

    def test_09_runtime_episodic_digest_status(self) -> None:
        runtime = LucyRuntime()
        status = runtime.episodic_digest_status()
        self.assertIsInstance(status, dict)
        self.assertIn("total_compressed_turns", status)

    def test_10_persistence_roundtrip(self) -> None:
        summarizer1 = EpisodicContextSummarizer(lucy_data=self.data_path, max_sliding_turns=3)
        turns = [
            {"input": "We will switch to Neovim and run tests", "reply": "Tests passed"}
            for _ in range(5)
        ]
        summarizer1.compress_older_turns(turns, keep_recent=2)
        summarizer1.save()

        # Create new instance pointing to same data_path
        summarizer2 = EpisodicContextSummarizer(lucy_data=self.data_path, max_sliding_turns=3)
        self.assertTrue(summarizer2.has_digest())
        self.assertEqual(summarizer2.digest.total_compressed_turns, summarizer1.digest.total_compressed_turns)


if __name__ == "__main__":
    unittest.main()
