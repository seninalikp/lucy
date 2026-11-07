"""
test_stage63_memory_contradiction_resolver.py
Verifies Stage 63 Semantic Memory Contradiction, Slot Override, Explicit Pivot,
Retraction Handling, Causal Lineage, Pinning, and Zero Stale Prompt Leakage.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class TestStage63MemoryContradictionResolver(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "data" / "lucy").mkdir(parents=True, exist_ok=True)
        (self.root / "logs").mkdir(parents=True, exist_ok=True)
        self.runtime = LucyRuntime(project_root=self.root)
        self.router = CommandRouter(self.runtime)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_01_slot_override_supersedes_old_focus_with_zero_value_overlap(self) -> None:
        r1 = self.runtime.remember("My primary focus is Drift Music")
        self.assertTrue(r1["saved"])

        r2 = self.runtime.remember("My primary focus is LUCY")
        self.assertTrue(r2["saved"])
        self.assertEqual(len(r2["superseded_ids"]), 1)

        st = self.runtime.memory_graph.status()
        self.assertEqual(st["active_nodes"], 1)
        self.assertEqual(st["superseded_nodes"], 1)
        self.assertEqual(st["conflicts_resolved_count"], 1)

        active_hits = self.runtime.recall("primary focus")
        self.assertEqual(len(active_hits), 1)
        self.assertIn("LUCY", active_hits[0]["fact"])

    def test_02_explicit_pivot_syntax_supersedes_previous_tool(self) -> None:
        self.runtime.remember("We use SQLite for local storage")
        pivot = self.runtime.remember("Switch database from SQLite to PostgreSQL")

        self.assertTrue(pivot["saved"])
        self.assertEqual(len(pivot["superseded_ids"]), 1)

        active = self.runtime.memory_graph.query("")
        facts = [n["fact"] for n in active]
        self.assertIn("Switch database from SQLite to PostgreSQL", facts)
        self.assertNotIn("We use SQLite for local storage", facts)

    def test_03_explicit_retraction_retires_old_preference(self) -> None:
        self.runtime.remember("I use Windows CE video streaming on my headunit")
        retract = self.runtime.remember("I don't use Windows CE video streaming anymore")

        self.assertTrue(retract["saved"])
        self.assertEqual(len(retract["superseded_ids"]), 1)

    def test_04_causal_lineage_traces_three_step_evolution(self) -> None:
        self.runtime.remember("My code editor is VS Code")
        self.runtime.remember("My code editor is Cursor")
        self.runtime.remember("My code editor is Neovim")

        lineage = self.runtime.memory_lineage("editor")
        self.assertTrue(lineage["ok"])
        self.assertEqual(lineage["chain_length"], 3)
        self.assertIn("VS Code", lineage["formatted_chain"])
        self.assertIn("Cursor", lineage["formatted_chain"])
        self.assertIn("Neovim", lineage["formatted_chain"])

    def test_05_superseded_facts_never_leak_into_augmented_prompt(self) -> None:
        self.runtime.remember("My active project is OldPrototype")
        self.runtime.remember("My active project is LUCY")

        pkg = self.runtime.conversational_memory.build_augmented_prompt(
            user_input="What is my active project?",
            system_prompt_base="You are LUCY.",
        )
        prompt_text = pkg["augmented_system_prompt"]
        self.assertIn("My active project is LUCY", prompt_text)
        self.assertNotIn("OldPrototype", prompt_text)

    def test_06_router_pin_conflicts_and_lineage_commands_work(self) -> None:
        self.router.handle("remember My preferred distro is Arch Linux")
        pin_res = self.router.handle("pin memory Arch Linux")
        self.assertIn("Pinned memory", pin_res.message)

        self.router.handle("remember My preferred distro is Omarchy")
        conflicts_res = self.router.handle("memory conflicts")
        self.assertIn("slot:os", conflicts_res.message)

        lineage_res = self.router.handle("memory lineage distro")
        self.assertIn("Arch Linux", lineage_res.message)
        self.assertIn("Omarchy", lineage_res.message)


if __name__ == "__main__":
    unittest.main()
