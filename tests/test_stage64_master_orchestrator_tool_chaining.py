"""
test_stage64_master_orchestrator_tool_chaining.py
Stage 64 = Multi-Step Terminal Tool Chaining & Sequential Autonomous Execution Engine.

Verifies:
1. Orchestrator status reports Stage 52 backward compatibility and Stage 64 chaining readiness.
2. Arrow syntax tool chain parsing ('telemetry -> scan -> probe_health').
3. Pipe syntax and natural 'then' sequence parsing.
4. Sequential multi-step tool chain execution.
5. Context propagation across chained steps.
6. Failure in chain gracefully skips downstream dependents.
7. File search -> inspect -> memory record pipeline execution.
8. Terminal ASCII tree rendering with chain progress and step outcomes.
9. Router integration: 'chain ...', '/chain ...', and 'chain parse ...'.
10. Cryptographic execution receipt logged via ExecutionReceiptLedger.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.master_orchestrator import (
    DAGStep,
    GoalDAG,
    GoalStatus,
    MasterOrchestrator,
    StepStatus,
    parse_tool_chain,
    STAGE,
    STAGE_64,
)
from backend.lucy_core.router import CommandRouter


class TestStage64MasterOrchestratorToolChaining(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "data" / "lucy").mkdir(parents=True, exist_ok=True)
        (self.root / "logs").mkdir(parents=True, exist_ok=True)
        self.runtime = LucyRuntime(project_root=self.root)
        self.orchestrator = self.runtime.master_orchestrator
        self.router = CommandRouter(self.runtime)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_01_status_reports_stage52_and_stage64_chaining_readiness(self) -> None:
        """1. Status preserves Stage 52 identity while exposing Stage 64 capabilities."""
        st = self.orchestrator.status()
        self.assertEqual(st["stage"], "52 master orchestrator goal dag loop")
        self.assertEqual(st["stage_64"], "64 multi-step terminal tool chaining")
        self.assertTrue(st["tool_chaining_enabled"])
        self.assertEqual(st["status"], "ready")
        self.assertIn("SYSTEM_TELEMETRY", st["supported_chain_actions"])
        self.assertIn("FILE_SEARCH", st["supported_chain_actions"])

    def test_02_arrow_syntax_tool_chain_parsing(self) -> None:
        """2. Arrow syntax ('telemetry -> scan -> probe_health') parses cleanly."""
        chain_spec = "telemetry -> sentinel_scan -> probe_health"
        steps = parse_tool_chain(chain_spec)
        self.assertEqual(len(steps), 3)
        self.assertEqual(steps[0][1], "SYSTEM_TELEMETRY")
        self.assertEqual(steps[1][1], "SENTINEL_SCAN")
        self.assertEqual(steps[2][1], "PROBE_HEALTH")

    def test_03_pipe_syntax_and_natural_then_syntax_parsing(self) -> None:
        """3. Pipe syntax and 'then' syntax parse into ordered steps."""
        pipe_steps = parse_tool_chain("telemetry | scan")
        self.assertEqual(len(pipe_steps), 2)
        self.assertEqual(pipe_steps[0][1], "SYSTEM_TELEMETRY")
        self.assertEqual(pipe_steps[1][1], "SENTINEL_SCAN")

        natural_steps = parse_tool_chain("check telemetry, then scan workspace, then probe health")
        self.assertEqual(len(natural_steps), 3)
        self.assertEqual(natural_steps[0][1], "SYSTEM_TELEMETRY")
        self.assertEqual(natural_steps[1][1], "SENTINEL_SCAN")
        self.assertEqual(natural_steps[2][1], "PROBE_HEALTH")

    def test_04_sequential_multi_step_tool_chain_execution(self) -> None:
        """4. Executes multi-step tool chain end-to-end to COMPLETED."""
        res = self.runtime.execute_tool_chain("telemetry -> sentinel_scan -> probe_health")
        self.assertTrue(res["ok"])
        self.assertEqual(res["status"], GoalStatus.COMPLETED)
        self.assertEqual(res["progress"]["completed"], 3)
        self.assertEqual(res["progress"]["failed"], 0)

    def test_05_context_propagation_across_chained_steps(self) -> None:
        """5. Context accumulates across chained steps."""
        res = self.runtime.execute_tool_chain("telemetry -> sentinel_scan")
        self.assertTrue(res["ok"])
        ctx = res["context"]
        self.assertIn("telemetry", ctx)
        self.assertIn("sentinel_scan", ctx)

    def test_06_failure_in_chain_skips_downstream_dependents(self) -> None:
        """6. Failure in an upstream step skips all downstream dependent steps."""
        dag = GoalDAG(title="Failure Chain Test")
        dag.add_step(DAGStep("s1", "Step 1 Failing", "CUSTOM", max_retries=0))
        dag.add_step(DAGStep("s2", "Step 2 Dependent", "CUSTOM", dependencies=["s1"]))

        # Force step 1 to fail
        def mock_exec(step: DAGStep, d: GoalDAG) -> dict:
            if step.step_id == "s1":
                return {"ok": False, "error": "Hardware failure"}
            return {"ok": True}

        self.orchestrator._execute_step = mock_exec
        res = self.orchestrator.execute_dag(dag)
        self.assertFalse(res["ok"])
        self.assertEqual(dag.steps["s1"].status, StepStatus.FAILED)
        self.assertEqual(dag.steps["s2"].status, StepStatus.SKIPPED)

    def test_07_file_search_inspect_memory_record_chain(self) -> None:
        """7. Tests real file search -> file inspect -> memory record chain."""
        # Create a test file
        test_file = self.root / "sample_stage64.txt"
        test_file.write_text("Lucy stage 64 tool chaining operational test.", encoding="utf-8")

        res = self.runtime.execute_tool_chain("search sample_stage64.txt -> inspect -> remember")
        self.assertTrue(res["ok"])
        self.assertEqual(res["status"], GoalStatus.COMPLETED)

        # Confirm recorded in memory
        recalled = self.runtime.recall("sample_stage64")
        self.assertGreaterEqual(len(recalled), 1)

    def test_08_terminal_ascii_tree_rendering_with_chain_progress(self) -> None:
        """8. Renders ASCII tree containing [OK] indicators and execution outcomes."""
        res = self.runtime.execute_tool_chain("telemetry -> sentinel_scan")
        tree = res["tree"]
        self.assertIn("[OK]", tree)
        self.assertIn("RAM:", tree)
        self.assertIn("Files Tracked:", tree)
        self.assertIn("100.0%", tree)

    def test_09_router_chain_and_chain_parse_commands(self) -> None:
        """9. Router handles 'chain parse' and 'chain' execution commands."""
        # Parse command
        parse_resp = self.router.handle("chain parse telemetry -> scan -> heal")
        self.assertIn("Parsed Tool Chain (3 steps)", parse_resp.message)
        self.assertIn("SYSTEM_TELEMETRY", parse_resp.message)

        # Execution command
        exec_resp = self.router.handle("chain telemetry -> scan")
        self.assertIn("Master Orchestrator Execution (SUCCESS)", exec_resp.message)
        self.assertIn("[OK]", exec_resp.message)

    def test_10_receipt_ledger_issues_cryptographic_receipt_for_chain(self) -> None:
        """10. Executed chain generates a verified turn receipt in ExecutionReceiptLedger."""
        res = self.runtime.execute_tool_chain("telemetry -> probe_health")
        self.assertTrue(res["ok"])

        receipts = self.runtime.receipt_ledger.current_turn_receipts()
        chain_receipts = [r for r in receipts if r.get("action_category") == "tool_chain"]
        self.assertGreaterEqual(len(chain_receipts), 1)
        self.assertEqual(chain_receipts[-1]["operation"], "execute_chain")


if __name__ == "__main__":
    unittest.main()
