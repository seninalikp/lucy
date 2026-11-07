r"""
tests/test_stage123_hierarchical_goal_decomposer.py
Unit tests for Stage 123: Hierarchical Goal & Subgoal Decomposer (Era 13).
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.hierarchical_goal_decomposer import (
    HierarchicalGoalDecomposer,
    SubGoalNode,
    DecomposedGoalPlan,
    STAGE,
    ERA,
    ERA_NAME,
    STAGE_NAME,
    CREATOR_NAME,
    CREATOR_FULL_NAME,
)


class MockReceiptLedger:
    def __init__(self):
        self.receipts = []

    def record_receipt(self, action_category: str, operation: str, target: str, verified_outcome: str):
        self.receipts.append({
            "action_category": action_category,
            "operation": operation,
            "target": target,
            "verified_outcome": verified_outcome,
        })


class TestStage123HierarchicalGoalDecomposer(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_test_stage123_"))
        self.data_dir = self.test_dir / "data" / "lucy" / "plans"
        self.ledger = MockReceiptLedger()
        self.decomposer = HierarchicalGoalDecomposer(
            project_root=self.test_dir,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_metadata_and_initialization(self):
        self.assertEqual(STAGE, 123)
        self.assertEqual(ERA, 13)
        self.assertEqual(STAGE_NAME, "Hierarchical Goal & Subgoal Decomposer")
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")

        st = self.decomposer.status()
        self.assertEqual(st["stage"], 123)
        self.assertEqual(st["era"], 13)
        self.assertEqual(st["creator"], "Senin")
        self.assertEqual(st["total_plans"], 0)
        self.assertIsNone(st["last_plan_id"])

    def test_02_code_refactoring_decomposition(self):
        plan = self.decomposer.decompose_goal("Refactor polyglot AST parser node visitor")
        self.assertIsInstance(plan, DecomposedGoalPlan)
        self.assertTrue(plan.plan_id.startswith("plan_"))
        self.assertGreaterEqual(plan.total_subgoals, 5)  # root + 4 phases
        self.assertEqual(plan.status, "ACTIVE")
        self.assertGreaterEqual(plan.max_depth, 1)

        # Check topological ordering
        node_titles = [plan.nodes[nid]["title"] for nid in plan.execution_order]
        self.assertIn("AST Codebase Analysis", node_titles)
        self.assertIn("Surgical Code Synthesis", node_titles)
        self.assertIn("Regression & Invariant Testing", node_titles)
        self.assertIn("Autonomous GitOps Checkpoint", node_titles)

        # Analysis must come before Synthesis, and Synthesis before Testing
        ast_idx = node_titles.index("AST Codebase Analysis")
        synth_idx = node_titles.index("Surgical Code Synthesis")
        test_idx = node_titles.index("Regression & Invariant Testing")
        self.assertLess(ast_idx, synth_idx)
        self.assertLess(synth_idx, test_idx)

    def test_03_optimization_workflow_decomposition(self):
        plan = self.decomposer.decompose_goal("Optimize HNSW vector search speed and memory footprint")
        self.assertGreaterEqual(plan.total_subgoals, 5)
        node_titles = [plan.nodes[nid]["title"] for nid in plan.execution_order]
        self.assertIn("Benchmark Baseline", node_titles)
        self.assertIn("Profile Execution Hotspots", node_titles)
        self.assertIn("Apply Targeted Optimization", node_titles)
        self.assertIn("Verify Performance Gain", node_titles)

    def test_04_investigation_workflow_decomposition(self):
        plan = self.decomposer.decompose_goal("Search knowledge graph and investigate causal links")
        self.assertGreaterEqual(plan.total_subgoals, 4)
        node_titles = [plan.nodes[nid]["title"] for nid in plan.execution_order]
        self.assertIn("Knowledge Graph Query", node_titles)
        self.assertIn("HNSW Vector Retrieval", node_titles)
        self.assertIn("Synthesize Evidence & Findings", node_titles)

    def test_05_general_workflow_decomposition(self):
        plan = self.decomposer.decompose_goal("Execute autonomous cognitive sanity sweep")
        self.assertGreaterEqual(plan.total_subgoals, 4)
        node_titles = [plan.nodes[nid]["title"] for nid in plan.execution_order]
        self.assertIn("Context & Telemetry Intake", node_titles)
        self.assertIn("Counterfactual Simulation", node_titles)
        self.assertIn("Autonomous Execution Pulse", node_titles)

    def test_06_subgoal_status_progression(self):
        plan = self.decomposer.decompose_goal("Refactor cache module")
        phase1_id = [nid for nid in plan.execution_order if "phase1" in nid][0]

        # Transition to IN_PROGRESS
        ok1 = self.decomposer.update_subgoal_status(plan.plan_id, phase1_id, "IN_PROGRESS")
        self.assertTrue(ok1)
        self.assertEqual(plan.nodes[phase1_id]["status"], "IN_PROGRESS")

        # Transition to COMPLETED
        ok2 = self.decomposer.update_subgoal_status(plan.plan_id, phase1_id, "COMPLETED")
        self.assertTrue(ok2)
        self.assertEqual(plan.nodes[phase1_id]["status"], "COMPLETED")

        # Receipts emitted
        rec_cats = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("SUBGOAL_STATUS_UPDATED", rec_cats)

    def test_07_compensation_rollback_on_failure(self):
        plan = self.decomposer.decompose_goal("Refactor database pipeline")
        phase1_id = [nid for nid in plan.execution_order if "phase1" in nid][0]
        phase2_id = [nid for nid in plan.execution_order if "phase2" in nid][0]
        phase3_id = [nid for nid in plan.execution_order if "phase3" in nid][0]

        # Phase 1 & 2 succeed
        self.decomposer.update_subgoal_status(plan.plan_id, phase1_id, "COMPLETED")
        self.decomposer.update_subgoal_status(plan.plan_id, phase2_id, "COMPLETED")

        # Phase 3 fails
        self.decomposer.update_subgoal_status(plan.plan_id, phase3_id, "FAILED", error_msg="Syntax Error")

        # Plan status should be ROLLED_BACK
        self.assertEqual(plan.status, "ROLLED_BACK")

        # Previous completed phase with compensation action rolled back
        self.assertEqual(plan.nodes[phase2_id]["status"], "ROLLED_BACK")

        # Check receipt
        rec_cats = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("COMPENSATION_TRIGGERED", rec_cats)

    def test_08_persistence_and_reload(self):
        self.decomposer.decompose_goal("Goal 1: Memory optimization")
        self.decomposer.decompose_goal("Goal 2: Codebase security scan")

        # Fresh instance pointing to same storage
        fresh_decomp = HierarchicalGoalDecomposer(
            project_root=self.test_dir,
            data_dir=self.data_dir,
        )
        st = fresh_decomp.status()
        self.assertEqual(st["total_plans"], 2)
        self.assertIsNotNone(st["last_plan_id"])

    def test_09_ascii_visualizations(self):
        plan = self.decomposer.decompose_goal("Refactor testing engine")
        tree = self.decomposer.format_goal_tree(plan.plan_id)
        self.assertIn("GOAL PLAN:", tree)
        self.assertIn("Refactor testing engine", tree)
        self.assertIn("+-- [PENDING]", tree)

        table = self.decomposer.format_decomposer_status_table()
        self.assertIn("LUCY OS - HIERARCHICAL GOAL & SUBGOAL DECOMPOSER", table)
        self.assertIn("Total Plans Decomposed", table)
        self.assertIn("Senin (Senin Ali K P)", table)

    def test_10_dataclass_methods(self):
        node = SubGoalNode(
            subgoal_id="sub_01",
            title="Title",
            description="Desc",
            level=1,
            assigned_subsystem="git_ops",
            estimated_duration_ms=25.4,
        )
        d = node.to_dict()
        self.assertEqual(d["subgoal_id"], "sub_01")
        self.assertEqual(d["estimated_duration_ms"], 25.4)


if __name__ == "__main__":
    unittest.main()
