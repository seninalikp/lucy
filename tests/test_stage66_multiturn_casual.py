"""
test_stage66_multiturn_casual.py
Verifies Stage 66 native multi-turn message arrays, coreference resolution,
and casual vs operator conversation gating.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class TestStage66MultiTurnCasual(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "data" / "lucy").mkdir(parents=True, exist_ok=True)
        (self.root / "logs").mkdir(parents=True, exist_ok=True)
        self.runtime = LucyRuntime(project_root=self.root)
        self.router = CommandRouter(self.runtime)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_01_casual_chat_detection(self) -> None:
        self.assertTrue(self.runtime.conversational_memory.is_casual_chat("why?"))
        self.assertTrue(self.runtime.conversational_memory.is_casual_chat("tell me more about that"))
        self.assertFalse(self.runtime.conversational_memory.is_casual_chat("workspace status"))

    def test_02_coreference_resolution(self) -> None:
        self.runtime.conversational_memory.record_turn("We are building Drift Music player.", "Got it.")
        resolved = self.runtime.conversational_memory.resolve_coreference("why?")
        self.assertIn("referring to previous topic", resolved)
        self.assertIn("Drift Music player", resolved)

    def test_03_multiturn_memory_continuity_across_turns(self) -> None:
        self.router.handle("Hey Lucy, we are working on Drift Music.")
        self.router.handle("What is our main project?")
        
        turns = self.runtime.conversational_memory.get_sliding_context()
        self.assertGreaterEqual(len(turns), 2)
        self.assertIn("Drift Music", turns[0]["input"])


if __name__ == "__main__":
    unittest.main()
