"""
test_stages_54_to_58.py
Unit tests for Stages 54–58:
- Stage 54: Temporal & Semantic Memory Graph (BM25 + Fact Superseding)
- Stage 55: Cryptographic Execution Receipt Ledger & Anti-Hallucination Claim Binder
- Stage 56: Behavioral Correction & Workflow Habit Learner
- Stage 57: Live Workspace Context & Git Sensor
- Stage 58: Proactive Session Briefer & Follow-Through Engine
- End-to-End Runtime and CommandRouter Integration
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.memory_graph import TemporalMemoryGraph, STAGE as STAGE_54
from backend.lucy_core.execution_receipts import ExecutionReceiptLedger, STAGE as STAGE_55
from backend.lucy_core.workflow_learner import WorkflowHabitLearner, STAGE as STAGE_56
from backend.lucy_core.live_workspace_context import LiveWorkspaceSensor, STAGE as STAGE_57
from backend.lucy_core.proactive_briefer import ProactiveSessionBriefer, STAGE as STAGE_58
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class Stages54To58UnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.lucy_data = self.root / "data" / "lucy"
        self.lucy_data.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    # ---------- STAGE 54: TEMPORAL MEMORY GRAPH ----------
    def test_01_temporal_fact_superseding(self) -> None:
        graph = TemporalMemoryGraph(self.lucy_data / "memory")
        st = graph.status()
        self.assertEqual(st["stage"], STAGE_54)
        self.assertEqual(st["active_nodes"], 0)

        # 1. Insert initial fact
        r1 = graph.upsert_fact("My primary focus is Stage 53 scheduler", category="focus")
        self.assertTrue(r1["saved"])
        self.assertEqual(len(r1["superseded_ids"]), 0)
        node1_id = r1["node"]["id"]

        # 2. Duplicate fact should not duplicate
        r_dup = graph.upsert_fact("My primary focus is Stage 53 scheduler")
        self.assertFalse(r_dup["saved"])
        self.assertTrue(r_dup["duplicate"])

        # 3. Update the fact on the same subject
        r2 = graph.upsert_fact("My primary focus is Stage 54 memory graph", category="focus")
        self.assertTrue(r2["saved"])
        self.assertIn(node1_id, r2["superseded_ids"])

        # Check graph status
        st = graph.status()
        self.assertEqual(st["active_nodes"], 1)
        self.assertEqual(st["superseded_nodes"], 1)

        # Query should return ONLY the active fact
        hits = graph.query("primary focus", limit=5)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["fact"], "My primary focus is Stage 54 memory graph")

        # 4. Test conversational prefix stripping: "remember that my primary focus is Z"
        r3 = graph.upsert_fact("remember that my primary focus is Stage 55 receipts", category="focus")
        self.assertTrue(r3["saved"])
        self.assertIn(r2["node"]["id"], r3["superseded_ids"])

        # 5. Test graph forget method
        forget_res = graph.forget("Stage 55 receipts")
        self.assertEqual(forget_res["forgotten"], 1)
        self.assertEqual(len(graph.query("receipts", limit=5)), 0)

    def test_02_bm25_semantic_ranking(self) -> None:
        graph = TemporalMemoryGraph(self.lucy_data / "memory")
        graph.upsert_fact("The backend runs on Python and FastAPI.", category="stack")
        graph.upsert_fact("Senin develops Windows digital operating tools.", category="role")
        graph.upsert_fact("Never write shell scripts, use standard library.", category="constraint", pinned=True)

        # Pinned constraint should be returned first when query is empty
        empty_hits = graph.query("", limit=3)
        self.assertTrue(empty_hits[0]["pinned"])

        # BM25 search for "FastAPI"
        hits = graph.query("FastAPI backend", limit=2)
        self.assertGreaterEqual(len(hits), 1)
        self.assertIn("FastAPI", hits[0]["fact"])

    # ---------- STAGE 55: EXECUTION RECEIPT LEDGER ----------
    def test_03_execution_receipts_and_claim_binder(self) -> None:
        ledger = ExecutionReceiptLedger(self.lucy_data)
        st = ledger.status()
        self.assertEqual(st["stage"], STAGE_55)
        self.assertEqual(st["current_turn_receipts"], 0)

        # 1. LLM claims it added a task without a receipt in this turn
        unbacked_reply = "I have successfully added the task for you."
        check1 = ledger.verify_response_actions(unbacked_reply)
        self.assertFalse(check1["verified"])
        self.assertIn("task_mutation", check1["unbacked_claims"])
        self.assertIn("[STAGE 55 RECEIPT INTERCEPT: UNBACKED ACTION CLAIM]", check1["guarded_text"])

        # 2. Issue a real receipt
        rcpt = ledger.issue_receipt(
            action_category="task_mutation",
            operation="add_task",
            target="task_001",
            verified_outcome="Created task",
        )
        self.assertTrue(rcpt["receipt_id"].startswith("rcpt_"))
        self.assertEqual(ledger.status()["current_turn_receipts"], 1)

        # 3. Now verify the same response
        check2 = ledger.verify_response_actions(unbacked_reply)
        self.assertTrue(check2["verified"])
        self.assertEqual(len(check2["unbacked_claims"]), 0)
        self.assertIn("[RECEIPT_LEDGER: VERIFIED", check2["badge"])

        # 4. Begin turn resets the turn receipts
        ledger.begin_turn()
        self.assertEqual(len(ledger.current_turn_receipts()), 0)

    # ---------- STAGE 56: WORKFLOW HABIT LEARNER ----------
    def test_04_workflow_learner_corrections_and_macros(self) -> None:
        learner = WorkflowHabitLearner(self.lucy_data)
        st = learner.status()
        self.assertEqual(st["stage"], STAGE_56)

        # 1. Detect user correction
        res = learner.observe_for_corrections("Wrong, stop using external bash scripts for our tests.")
        self.assertTrue(res["correction_detected"])
        self.assertGreaterEqual(len(res["rules_added"]), 1)

        # Prompt guardrail block
        block = learner.prompt_guardrails_block()
        self.assertIn("[Enforced Behavioral Corrections (Stage 56)]:", block)
        self.assertIn("stop using external bash scripts", block)

        # 2. Save macro
        macro_res = learner.save_macro("daily_pulse", ["status", "workspace pulse", "brief me"])
        self.assertTrue(macro_res["ok"])
        self.assertEqual(learner.get_macro("daily_pulse"), ["status", "workspace pulse", "brief me"])

    # ---------- STAGE 57: LIVE WORKSPACE CONTEXT SENSOR ----------
    def test_05_live_workspace_sensor(self) -> None:
        sensor = LiveWorkspaceSensor(self.root)
        st = sensor.status()
        self.assertEqual(st["stage"], STAGE_57)

        # Create dummy recent files
        (self.root / "module_a.py").write_text("# module a", encoding="utf-8")
        (self.root / "config.json").write_text("{}", encoding="utf-8")

        recent = sensor.recently_modified_files(limit=5)
        self.assertGreaterEqual(len(recent), 2)
        paths = [r["path"] for r in recent]
        self.assertIn("module_a.py", paths)

        # Workspace prompt snippet
        snippet = sensor.build_workspace_prompt_snippet()
        self.assertIn("[Live Physical Workspace State (Stage 57)]:", snippet)
        self.assertIn("module_a.py", snippet)


class Stages54To58RuntimeAndRouterIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "data" / "lucy").mkdir(parents=True, exist_ok=True)
        (self.root / "logs").mkdir(parents=True, exist_ok=True)
        self.runtime = LucyRuntime(project_root=self.root)
        self.router = CommandRouter(self.runtime)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_06_runtime_memory_and_receipt_integration(self) -> None:
        # Remember issues a Stage 55 receipt
        rem_res = self.runtime.remember("My current priority is Stage 55 execution ledger")
        self.assertTrue(rem_res["saved"])

        # Check turn receipts
        turn_rcpts = self.runtime.receipt_ledger.current_turn_receipts()
        self.assertGreaterEqual(len(turn_rcpts), 1)
        self.assertEqual(turn_rcpts[0]["action_category"], "memory_mutation")

        # Recall pulls from Stage 54 memory graph
        hits = self.runtime.recall("priority")
        self.assertGreaterEqual(len(hits), 1)
        self.assertIn("Stage 55 execution ledger", hits[0]["fact"])

        # Adding a task issues a task_mutation receipt
        task_res = self.runtime.add_task("Implement claim binder tests")
        self.assertTrue(task_res["added"])
        turn_categories = [r["action_category"] for r in self.runtime.receipt_ledger.current_turn_receipts()]
        self.assertIn("task_mutation", turn_categories)

    def test_07_proactive_briefer(self) -> None:
        # Add open task
        self.runtime.add_task("Review Stage 58 session briefer")

        brief = self.runtime.generate_brief()
        self.assertEqual(brief["stage"], STAGE_58)
        self.assertIn("LUCY EXECUTIVE SESSION BRIEF", brief["brief_text"])
        self.assertIn("Review Stage 58 session briefer", brief["brief_text"])
        self.assertIn("Recommended Immediate Step:", brief["brief_text"])

    def test_08_router_commands_stages_54_to_58(self) -> None:
        # 1. Brief command
        res_brief = self.router.handle("brief me")
        self.assertIn("LUCY EXECUTIVE SESSION BRIEF", res_brief.message)

        # 2. Workspace pulse command
        res_pulse = self.router.handle("workspace pulse")
        self.assertIn("[Live Physical Workspace State (Stage 57)]:", res_pulse.message)

        # 3. Receipts command
        res_rcpt = self.router.handle("receipts")
        self.assertIn("execution_receipt_ledger", res_rcpt.message)

        # 4. Define macro
        res_macro_def = self.router.handle("macro test_flow = workspace pulse ; receipts")
        self.assertIn("Saved macro 'test_flow'", res_macro_def.message)

        # 5. Execute macro
        res_macro_run = self.router.handle("macro test_flow")
        self.assertIn("[Live Physical Workspace State (Stage 57)]:", res_macro_run.message)
        self.assertIn("execution_receipt_ledger", res_macro_run.message)



class TestStages54To58(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "sample_module.py").write_text("x = 42\n", encoding="utf-8")
        self.runtime = LucyRuntime(project_root=self.root)
        self.router = CommandRouter(self.runtime)

    def tearDown(self) -> None:
        self.runtime.graceful_shutdown("test teardown")
        self.temp_dir.cleanup()

    def test_stage54_temporal_fact_superseding(self) -> None:
        r1 = self.runtime.remember("My main project is OldAlpha")
        self.assertTrue(r1["saved"])
        first_id = r1["memory"]["id"]

        r2 = self.runtime.remember("My main project is LucyOS")
        self.assertTrue(r2["saved"])
        self.assertIn(first_id, r2["superseded_ids"])

        recalled = self.runtime.recall("main project")
        facts = [m["fact"] for m in recalled]
        self.assertIn("My main project is LucyOS", facts)
        self.assertNotIn("My main project is OldAlpha", facts)

    def test_stage55_execution_receipt_interception(self) -> None:
        self.runtime.receipt_ledger.begin_turn()
        unbacked = "I have added the task to your project list."
        check = self.runtime.receipt_ledger.verify_response_actions(unbacked)
        self.assertFalse(check["verified"])
        self.assertIn("task_mutation", check["unbacked_claims"])
        self.assertIn("STAGE 55 RECEIPT INTERCEPT", check["guarded_text"])

        # Now actually execute the tool and verify it passes
        self.runtime.projects.add_task("Write unit tests")
        check_valid = self.runtime.receipt_ledger.verify_response_actions(unbacked)
        self.assertTrue(check_valid["verified"])

    def test_stage56_behavioral_correction_and_macros(self) -> None:
        res = self.runtime.workflow_learner.observe_for_corrections(
            "No, don't ever use truncated placeholder comments in code."
        )
        self.assertTrue(res["correction_detected"])
        self.assertIn("truncated placeholder", self.runtime.workflow_learner.prompt_guardrails_block())

        m_res = self.router.handle("macro quickcheck = status ; tasks")
        self.assertIn("Saved macro 'quickcheck'", m_res.message)
        run_res = self.router.handle("macro quickcheck")
        self.assertIn("LUCY", run_res.message)

    def test_stage57_live_workspace_sensor(self) -> None:
        recent = self.runtime.workspace_sensor.recently_modified_files(limit=5)
        paths = [r["path"] for r in recent]
        self.assertIn("sample_module.py", paths)

    def test_stage58_proactive_session_briefer(self) -> None:
        self.runtime.projects.add_task("Verify Stage 58 briefer")
        resp = self.router.handle("brief me")
        self.assertIn("LUCY EXECUTIVE SESSION BRIEF", resp.message)
        self.assertIn("Verify Stage 58 briefer", resp.message)


if __name__ == "__main__":
    unittest.main()
