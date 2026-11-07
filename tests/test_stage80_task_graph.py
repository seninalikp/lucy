"""
tests/test_stage80_task_graph.py
Unit tests for Stage 80: Multi-Turn Operator Goal Decomposition & Task Graph Engine
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.task_graph import (
    GoalDAG,
    GoalTaskGraphEngine,
    TaskNode,
    STAGE,
)


class MockReceiptLedger:
    def __init__(self):
        self.receipts = []

    def issue_receipt(self, action_category: str, operation: str, target: str, verified_outcome: str):
        self.receipts.append({
            "category": action_category,
            "operation": operation,
            "target": target,
            "outcome": verified_outcome,
        })


class TestStage80TaskGraph(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_stage80_test_"))
        self.storage_file = self.test_dir / "data" / "active_goal.json"
        self.ledger = MockReceiptLedger()
        self.engine = GoalTaskGraphEngine(
            project_root=self.test_dir,
            storage_file=self.storage_file,
            receipt_ledger=self.ledger,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_stage_constant(self):
        self.assertEqual(STAGE, 80)

    def test_02_goal_dag_dependencies(self):
        dag = GoalDAG(goal_id="g1", goal_description="Test Goal", created_at="now", updated_at="now")
        t1 = dag.add_task("Initial Step", task_id="t1")
        t2 = dag.add_task("Dependent Step", dependencies=["t1"], task_id="t2")

        # Initially, only t1 is ready
        ready = dag.get_ready_tasks()
        self.assertEqual(len(ready), 1)
        self.assertEqual(ready[0].task_id, "t1")

        # Mark t1 completed
        dag.mark_completed("t1", summary="Step 1 done")
        self.assertEqual(t1.status, "COMPLETED")
        self.assertEqual(t1.output_summary, "Step 1 done")

        # Now t2 should be unblocked and ready
        ready_after = dag.get_ready_tasks()
        self.assertEqual(len(ready_after), 1)
        self.assertEqual(ready_after[0].task_id, "t2")

    def test_03_progress_percent(self):
        dag = GoalDAG(goal_id="g2", goal_description="Measure Progress", created_at="now", updated_at="now")
        dag.add_task("Step 1", task_id="t1")
        dag.add_task("Step 2", task_id="t2")
        dag.add_task("Step 3", task_id="t3")
        dag.add_task("Step 4", task_id="t4")

        self.assertEqual(dag.progress_percent(), 0)
        self.assertFalse(dag.is_all_completed())

        dag.mark_completed("t1")
        self.assertEqual(dag.progress_percent(), 25)

        dag.mark_completed("t2")
        self.assertEqual(dag.progress_percent(), 50)

        dag.mark_completed("t3")
        dag.mark_completed("t4")
        self.assertEqual(dag.progress_percent(), 100)
        self.assertTrue(dag.is_all_completed())

    def test_04_create_plan_from_numbered_input(self):
        goal = (
            "Refactor auth system:\n"
            "1. Read current auth handlers\n"
            "2. Create JWT token generator\n"
            "3. Update middleware tests\n"
        )
        dag = self.engine.create_plan(goal)
        self.assertEqual(len(dag.nodes), 3)
        self.assertEqual(dag.nodes["t1"].dependencies, [])
        self.assertEqual(dag.nodes["t2"].dependencies, ["t1"])
        self.assertEqual(dag.nodes["t3"].dependencies, ["t2"])
        self.assertEqual(len(self.ledger.receipts), 1)

    def test_05_create_plan_default_pipeline(self):
        goal = "Implement database connection pooling"
        dag = self.engine.create_plan(goal)
        self.assertEqual(len(dag.nodes), 4)
        self.assertIn("t1", dag.nodes)
        self.assertIn("t4", dag.nodes)
        self.assertEqual(dag.nodes["t4"].assigned_tool, "code_reviewer")

    def test_06_complete_task_lifecycle(self):
        self.engine.create_plan("Test lifecycle")
        ok, msg = self.engine.complete_task("t1", summary="Finished analysis")
        self.assertTrue(ok)
        self.assertIn("Next ready task", msg)

        # Invalid task id
        bad_ok, bad_msg = self.engine.complete_task("nonexistent")
        self.assertFalse(bad_ok)

    def test_07_persistence(self):
        self.engine.create_plan("Persisted goal")
        self.engine.complete_task("t1")

        # Create new engine instance
        new_engine = GoalTaskGraphEngine(
            project_root=self.test_dir,
            storage_file=self.storage_file,
        )
        self.assertIsNotNone(new_engine.active_dag)
        self.assertEqual(new_engine.active_dag.nodes["t1"].status, "COMPLETED")

    def test_08_clear_plan(self):
        self.engine.create_plan("Temporary plan")
        self.assertTrue(self.storage_file.exists())

        self.engine.clear_plan()
        self.assertIsNone(self.engine.active_dag)
        self.assertFalse(self.storage_file.exists())

    def test_09_terminal_summary_ascii_safe(self):
        dag = self.engine.create_plan("1. First item\n2. Second item")
        summary = self.engine.format_terminal_summary()

        summary.encode("ascii")
        self.assertIn("PROJECT TASK GRAPH & GOAL DAG", summary)
        self.assertIn("First item", summary)
        self.assertIn("+", summary)
        self.assertIn("-", summary)
        self.assertIn("|", summary)

    def test_10_empty_summary_ascii_safe(self):
        self.engine.clear_plan()
        summary = self.engine.format_terminal_summary()
        summary.encode("ascii")
        self.assertIn("No active goal plan", summary)


if __name__ == "__main__":
    unittest.main()
