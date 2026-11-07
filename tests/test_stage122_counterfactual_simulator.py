r"""
tests/test_stage122_counterfactual_simulator.py
Unit tests for Stage 122: Multi-Hypothesis Counterfactual Evaluator (Era 13).
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.counterfactual_simulator import (
    CounterfactualSimulationEngine,
    ActionHypothesis,
    CounterfactualSimulationReport,
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


class TestStage122CounterfactualSimulator(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_test_stage122_"))
        self.data_dir = self.test_dir / "data" / "lucy" / "simulations"
        self.ledger = MockReceiptLedger()
        self.simulator = CounterfactualSimulationEngine(
            project_root=self.test_dir,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_metadata_and_initialization(self):
        self.assertEqual(STAGE, 122)
        self.assertEqual(ERA, 13)
        self.assertEqual(STAGE_NAME, "Multi-Hypothesis Counterfactual Evaluator")
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")

        st = self.simulator.status()
        self.assertEqual(st["stage"], 122)
        self.assertEqual(st["era"], 13)
        self.assertEqual(st["creator"], "Senin")
        self.assertEqual(st["total_simulations"], 0)
        self.assertIsNone(st["last_simulation_id"])

    def test_02_evaluate_competing_hypotheses(self):
        h1 = ActionHypothesis(
            hypothesis_id="hypo_safe",
            description="Safe verified patch",
            proposed_actions=["run unit tests", "apply diff", "commit"],
            estimated_utility=0.9,
            estimated_risk=0.1,
            side_effect_prob=0.05,
            reversible=True,
        )
        h2 = ActionHypothesis(
            hypothesis_id="hypo_risky",
            description="Direct unchecked write",
            proposed_actions=["write file without tests"],
            estimated_utility=0.7,
            estimated_risk=0.6,
            side_effect_prob=0.4,
            reversible=False,
        )
        report = self.simulator.evaluate_hypotheses("Refactor module", [h1, h2])

        self.assertIsInstance(report, CounterfactualSimulationReport)
        self.assertEqual(report.total_hypotheses, 2)
        self.assertEqual(report.viable_hypotheses, 2)
        self.assertEqual(report.best_hypothesis_id, "hypo_safe")
        self.assertGreater(report.best_score, 0.5)
        self.assertIn("hypo_safe", report.counterfactual_explanation)

        # Status updated
        st = self.simulator.status()
        self.assertEqual(st["total_simulations"], 1)
        self.assertEqual(st["last_best_hypothesis"], "hypo_safe")

    def test_03_disqualify_operator_identity_violation(self):
        malicious_h = ActionHypothesis(
            hypothesis_id="hypo_impersonate",
            description="Replace operator identity with unauthorized admin",
            proposed_actions=["replace operator in config"],
            estimated_utility=1.0,
            estimated_risk=0.0,
        )
        safe_h = ActionHypothesis(
            hypothesis_id="hypo_standard",
            description="Standard maintenance for operator Senin",
            proposed_actions=["clean temporary files"],
            estimated_utility=0.8,
            estimated_risk=0.1,
        )
        report = self.simulator.evaluate_hypotheses("Identity Check", [malicious_h, safe_h])

        self.assertEqual(report.total_hypotheses, 2)
        self.assertEqual(report.viable_hypotheses, 1)
        self.assertEqual(report.best_hypothesis_id, "hypo_standard")

        # Verify malicious hypothesis was disqualified
        for h in report.hypotheses:
            if h["hypothesis_id"] == "hypo_impersonate":
                self.assertTrue(h["violates_invariants"])
                self.assertEqual(h["composite_score"], 0.0)
                self.assertIn("operator identity invariance", h["disqualification_reason"].lower())

    def test_04_disqualify_cloud_and_doc_violations(self):
        cloud_h = ActionHypothesis(
            hypothesis_id="hypo_cloud",
            description="Send data to mandatory cloud server",
            proposed_actions=["send external telemetry relay"],
            estimated_utility=0.95,
        )
        doc_h = ActionHypothesis(
            hypothesis_id="hypo_strip_docs",
            description="Minify code by delete all comments",
            proposed_actions=["strip docstrings and comments"],
            estimated_utility=0.90,
        )
        self.simulator._audit_and_score_hypothesis(cloud_h)
        self.simulator._audit_and_score_hypothesis(doc_h)

        self.assertTrue(cloud_h.violates_invariants)
        self.assertTrue(doc_h.violates_invariants)
        self.assertEqual(cloud_h.composite_score, 0.0)
        self.assertEqual(doc_h.composite_score, 0.0)

    def test_05_simulate_goal_hypotheses_synthesis(self):
        report = self.simulator.simulate_goal_hypotheses("Optimize HNSW Index Memory")
        self.assertGreaterEqual(report.total_hypotheses, 3)
        self.assertGreaterEqual(report.viable_hypotheses, 2)
        self.assertIsNotNone(report.best_hypothesis_id)
        self.assertTrue(report.best_score > 0.0)
        self.assertTrue(len(report.counterfactual_explanation) > 10)

    def test_06_receipt_ledger_recording(self):
        self.simulator.simulate_goal_hypotheses("Test Ledger Integration")
        rec_cats = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("COUNTERFACTUAL_SIMULATION_RUN", rec_cats)
        self.assertIn("HYPOTHESIS_EVALUATED", rec_cats)
        self.assertIn("BEST_HYPOTHESIS_SELECTED", rec_cats)

    def test_07_persistence_and_reload(self):
        self.simulator.simulate_goal_hypotheses("Goal 1: AST Patching")
        self.simulator.simulate_goal_hypotheses("Goal 2: Vector Search")

        # Reload in fresh instance
        fresh_sim = CounterfactualSimulationEngine(
            project_root=self.test_dir,
            data_dir=self.data_dir,
        )
        st = fresh_sim.status()
        self.assertEqual(st["total_simulations"], 2)
        self.assertIsNotNone(st["last_simulation_id"])

    def test_08_ascii_status_table(self):
        self.simulator.simulate_goal_hypotheses("Test ASCII Visualization")
        tbl = self.simulator.format_counterfactual_status_table()

        self.assertIn("LUCY OS - MULTI-HYPOTHESIS COUNTERFACTUAL EVALUATOR", tbl)
        self.assertIn("Total Branching Simulations Run", tbl)
        self.assertIn("Optimal Trajectory Selected", tbl)
        self.assertIn("Senin (Senin Ali K P)", tbl)
        self.assertIn("branch_conservative", tbl)

    def test_09_dataclass_methods(self):
        h = ActionHypothesis(
            hypothesis_id="h_test",
            description="desc",
            proposed_actions=["a1", "a2"],
            estimated_utility=0.75,
            estimated_risk=0.15,
            side_effect_prob=0.10,
            reversible=True,
            composite_score=0.68,
        )
        d = h.to_dict()
        self.assertEqual(d["hypothesis_id"], "h_test")
        self.assertEqual(d["estimated_utility"], 0.75)
        self.assertTrue(d["reversible"])


if __name__ == "__main__":
    unittest.main()
