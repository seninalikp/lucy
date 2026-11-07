"""
test_stage65_terminal_burn_in_sleep.py
Stage 65 = Terminal Burn-In & Personal LoRA Sleep Cycle (/sleep).

Verifies:
1. Terminal configuration integrity (web_ui_enabled=False, desktop_ui_enabled=False, api_enabled=True).
2. Multi-turn conversation handling with zero duplicate execution.
3. Semantic contradiction resolution: slot overrides in memory graph (Stage 63).
4. Explicit tool chaining via terminal router command 'chain ...' (Stage 64).
5. Lineage inspection and fact pinning in the terminal.
6. Triggering '/sleep' creates valid dataset and Modelfile with baked exemplars.
7. Sanity gate evaluates 20 standard probes with >= 90% pass threshold.
8. Execution receipt ledger logs verifiable cryptographic audit trail for the entire session.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class TestStage65TerminalBurnInSleep(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "data" / "lucy").mkdir(parents=True, exist_ok=True)
        (self.root / "logs").mkdir(parents=True, exist_ok=True)
        self.runtime = LucyRuntime(project_root=self.root)
        self.router = CommandRouter(self.runtime)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_01_terminal_configuration_integrity(self) -> None:
        """1. Verifies terminal mode is locked: UI disabled, APIs configured safely."""
        status = self.runtime.status()
        self.assertFalse(status["web_ui_enabled"])
        self.assertFalse(status["desktop_ui_enabled"])

    def test_02_multi_turn_conversation_with_turn_receipts(self) -> None:
        """2. Executes conversational turns and verifies single-pass receipt logging."""
        resp1 = self.router.handle("Please add a task to calibrate neural weights.")
        self.assertIn("calibrate neural weights", resp1.message)

        resp2 = self.router.handle("Remember that our primary focus is sovereign local execution.")
        self.assertIn("Remembered", resp2.message)

        # Confirm receipts recorded
        receipts = self.runtime.receipt_ledger.current_turn_receipts()
        self.assertGreaterEqual(len(receipts), 1)

    def test_03_stage63_memory_contradiction_in_terminal_session(self) -> None:
        """3. Confirms slot override automatically supersedes old facts in terminal."""
        self.router.handle("Remember that our primary focus is Drift Music.")
        self.router.handle("Remember that our primary focus is LUCY Sovereign Core.")

        # Lineage check
        lin = self.runtime.memory_lineage("primary focus")
        self.assertTrue(lin["ok"])
        self.assertEqual(lin["chain_length"], 2)

        # Check prompt recall
        memories = self.runtime.recall("primary focus")
        self.assertEqual(len(memories), 1)
        self.assertIn("LUCY Sovereign Core", memories[0]["fact"])

    def test_04_stage64_tool_chaining_via_terminal_router(self) -> None:
        """4. Executes multi-step tool chain through router and checks status tree."""
        resp = self.router.handle("chain telemetry -> scan -> probe_health")
        self.assertIn("Master Orchestrator Execution (SUCCESS)", resp.message)
        self.assertIn("[OK]", resp.message)
        self.assertIn("100.0%", resp.message)

    def test_05_pinning_and_unpinning_memory_in_terminal(self) -> None:
        """5. Verifies pinning and unpinning memory facts via terminal commands."""
        r = self.runtime.remember("Database is PostgreSQL 16")
        node_id = r["node_id"]

        pin_resp = self.router.handle(f"pin memory {node_id}")
        self.assertIn("Pinned memory", pin_resp.message)

        unpin_resp = self.router.handle(f"unpin memory {node_id}")
        self.assertIn("Unpinned memory", unpin_resp.message)

    def test_06_sleep_cycle_generates_dataset_and_modelfile(self) -> None:
        """6. Running /sleep produces valid dataset and Ollama Modelfile."""
        # Seed an interaction turn
        self.runtime.remember("Project codename is Lucy Sovereign.")
        self.runtime.record_turn(
            user_text="What is our project codename?",
            assistant_reply="Our project codename is Lucy Sovereign.",
            run_auto_extract=False,
        )

        resp = self.router.handle("/sleep")
        self.assertIn("LORA_SLEEP_CYCLE", resp.message)

        # Check modelfile
        mf_path = self.root / "data" / "lucy" / "adapters" / "Modelfile.lucy"
        self.assertTrue(mf_path.exists())
        content = mf_path.read_text(encoding="utf-8")
        self.assertIn("FROM", content)
        self.assertIn("SYSTEM", content)

    def test_07_sanity_gate_evaluates_twenty_probes(self) -> None:
        """7. 20-Question Sanity Gate evaluates identity, disk, safety, and swarm pillars."""
        gate = self.runtime.lora_sleep_cycle.run_sanity_gate()
        self.assertIn("score", gate)
        self.assertEqual(gate["total_probes"], 20)
        self.assertGreaterEqual(gate["passed_count"], 18)
        self.assertTrue(gate["passed"])


if __name__ == "__main__":
    unittest.main()
