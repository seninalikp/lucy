"""
test_stage44_personal_profiler.py
Stage 44 = Personal Behavioral Profiler & Habit Engine (Real-Time Adaptation).

Verifies:
1. Profiler reports Stage 44 and active status.
2. Real-time negative constraint and mandatory directive extraction.
3. Duplicate rule prevention.
4. Workspace alias registration and query resolution.
5. Personal preferences update (brevity, tone, coding rules).
6. Personal prompt snippet generation for local Ollama.
7. LucyRuntime Stage 44 integration.
8. CommandRouter Stage 44 command routing and formatting.
9. Automatic correction learning during conversational chat turns.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.personal_profiler import PersonalProfiler, STAGE
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class Stage44PersonalProfilerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.lucy_data = self.root / "data" / "lucy"
        self.lucy_data.mkdir(parents=True, exist_ok=True)
        self.profiler = PersonalProfiler(lucy_data=self.lucy_data)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_01_initial_status(self) -> None:
        status = self.profiler.status()
        self.assertEqual(status["stage"], STAGE)
        self.assertEqual(status["personal_profiler"], "active")
        self.assertGreaterEqual(status["anti_drift_rules_count"], 4)
        self.assertGreaterEqual(status["workspace_aliases_count"], 5)
        self.assertEqual(status["learned_corrections_count"], 0)
        self.assertEqual(status["user_persona"]["brevity"], "concise")

    def test_02_detect_and_learn_negative_constraint(self) -> None:
        # Issue a negative constraint: "don't create linux kernel code"
        res = self.profiler.detect_and_learn_correction("Lucy, don't create external bash scripts for this.")
        self.assertIsNotNone(res)
        self.assertTrue(res["learned"])
        self.assertEqual(res["correction"]["rule_type"], "negative_constraint")
        self.assertIn("don't create external bash scripts for this", res["correction"]["extracted_rule"])

        status = self.profiler.status()
        self.assertEqual(status["learned_corrections_count"], 1)
        self.assertIn(res["correction"]["extracted_rule"], status["anti_drift_rules"])

    def test_03_detect_mandatory_directive(self) -> None:
        # Issue a mandatory directive: "always use type hints"
        res = self.profiler.detect_and_learn_correction("Please always include docstrings in python functions.")
        self.assertIsNotNone(res)
        self.assertTrue(res["learned"])
        self.assertEqual(res["correction"]["rule_type"], "mandatory_directive")

    def test_04_duplicate_rule_prevention(self) -> None:
        res1 = self.profiler.detect_and_learn_correction("Never delete logs without user confirmation.")
        self.assertIsNotNone(res1)
        self.assertTrue(res1["learned"])

        # Second time with the exact same directive should return None and not duplicate
        res2 = self.profiler.detect_and_learn_correction("Never delete logs without user confirmation.")
        self.assertIsNone(res2)
        self.assertEqual(self.profiler.status()["learned_corrections_count"], 1)

    def test_05_workspace_alias_resolution(self) -> None:
        # Check default alias resolution
        resolved = self.profiler.resolve_alias("check the tv folder and keys file")
        self.assertIn("android tv wallpaper", resolved)
        self.assertIn("api keys.txt", resolved)

        # Add custom alias
        res = self.profiler.add_alias("music", "C:/Users/admin/Music/Tracks")
        self.assertTrue(res["saved"])
        res_text = self.profiler.resolve_alias("play music now")
        self.assertIn("C:/Users/admin/Music/Tracks", res_text)

    def test_06_personal_prompt_snippet(self) -> None:
        snippet = self.profiler.get_personal_prompt_snippet()
        self.assertIn("[User Personal Alignment & Habits]:", snippet)
        self.assertIn("Brevity=concise", snippet)
        self.assertIn("Stdlib preferred=True", snippet)
        self.assertIn("Anti-Drift Guardrails:", snippet)


class Stage44RuntimeAndRouterIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "data" / "lucy").mkdir(parents=True, exist_ok=True)
        (self.root / "logs").mkdir(parents=True, exist_ok=True)
        self.runtime = LucyRuntime(project_root=self.root)
        self.router = CommandRouter(self.runtime)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_07_runtime_methods(self) -> None:
        status = self.runtime.personal_profile_status()
        self.assertEqual(status["stage"], STAGE)

        # Add anti-drift rule
        r1 = self.runtime.add_anti_drift_rule("Always keep code clean and tested.")
        self.assertTrue(r1["saved"])

        # Add alias
        r2 = self.runtime.add_workspace_alias("docs", "C:/Users/admin/Documents")
        self.assertTrue(r2["saved"])

    def test_08_router_commands(self) -> None:
        # Profile status
        res1 = self.router.handle("personal profile status")
        self.assertIn("Personal Behavioral Profile status:", res1.message)
        self.assertIn("Stage: 44 personal profiler habit engine", res1.message)

        # Preferences
        res2 = self.router.handle("my preferences")
        self.assertIn("User Personal Preferences:", res2.message)
        self.assertIn("Brevity: concise", res2.message)

        # Anti-drift rules
        res3 = self.router.handle("anti drift rules")
        self.assertIn("Active Anti-Drift Guardrails", res3.message)

        # Add alias command
        res4 = self.router.handle("add alias notes = C:/senin/notes.txt")
        self.assertIn("Workspace alias registered: 'notes' -> 'C:/senin/notes.txt'", res4.message)

        # Add rule command
        res5 = self.router.handle("add rule Never overwrite user configuration.")
        self.assertIn("Anti-drift rule locked in:", res5.message)

    def test_09_conversational_correction_learning(self) -> None:
        # User tells Lucy a correction in natural dialogue
        self.runtime.conversational_chat("Lucy, don't use external docker containers for our tests.")
        
        # Check that profiler automatically registered the rule
        status = self.runtime.personal_profile_status()
        self.assertGreaterEqual(status["learned_corrections_count"], 1)
        has_rule = any("don't use external docker containers" in r.lower() for r in status["anti_drift_rules"])
        self.assertTrue(has_rule)


if __name__ == "__main__":
    unittest.main()
