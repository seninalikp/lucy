"""
tests/test_stage128_meta_policy_refiner.py
Verification suite for Stage 128: Autonomous Meta-Policy Refiner
Era 13: Self-Reflective Symbolic Mesh & Cognitive Graph Synthesizer
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.meta_policy_refiner import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    ERA_NAME,
    STAGE,
    STAGE_NAME,
    AutonomousMetaPolicyRefiner,
    MetaPolicyParam,
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


class TestStage128MetaPolicyRefiner(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)
        self.data_dir = self.project_root / "data" / "lucy" / "policies"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = MockReceiptLedger()
        self.refiner = AutonomousMetaPolicyRefiner(
            project_root=self.project_root,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_metadata(self):
        """Verifies sovereign operator identity and stage/era metadata."""
        self.assertEqual(STAGE, 128)
        self.assertEqual(ERA, 13)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")
        status = self.refiner.status()
        self.assertEqual(status["stage"], 128)
        self.assertEqual(status["era"], 13)
        self.assertEqual(status["creator"], "Senin")
        self.assertEqual(status["creator_full_name"], "Senin Ali K P")

    def test_02_default_policies_initialization(self):
        """Verifies default meta-policies are seeded with valid bounds and types."""
        status = self.refiner.status()
        self.assertEqual(status["total_policies"], 6)

        retry = self.refiner.get_policy("RETRY_BUDGET")
        self.assertIsNotNone(retry)
        self.assertEqual(retry.current_value, 3.0)
        self.assertEqual(retry.min_bound, 1.0)
        self.assertEqual(retry.max_bound, 10.0)

        sandbox = self.refiner.get_policy("SANDBOX_STRICTNESS")
        self.assertIsNotNone(sandbox)
        self.assertTrue(sandbox.is_locked)

    def test_03_tune_policy_within_bounds(self):
        """Verifies policy parameter tuning clamps strictly within min/max bounds."""
        # Valid adjustment within bounds
        success, msg, val = self.refiner.tune_policy("EXPLORATION_RATIO", 0.35)
        self.assertTrue(success)
        self.assertEqual(val, 0.35)
        self.assertEqual(self.refiner.get_value("EXPLORATION_RATIO"), 0.35)

        # Out-of-bounds adjustment (exceeds max_bound 0.50)
        success, msg, val = self.refiner.tune_policy("EXPLORATION_RATIO", 0.99)
        self.assertTrue(success)
        self.assertEqual(val, 0.50)  # Clamped to max_bound

        # Out-of-bounds adjustment (below min_bound 0.05)
        success, msg, val = self.refiner.tune_policy("EXPLORATION_RATIO", 0.01)
        self.assertTrue(success)
        self.assertEqual(val, 0.05)  # Clamped to min_bound

    def test_04_locked_policy_safety_invariants(self):
        """Verifies that locked security policies cannot be downgraded below safety floor."""
        success, msg, val = self.refiner.tune_policy("SANDBOX_STRICTNESS", 1.0)
        self.assertFalse(success)
        self.assertIn("locked", msg.lower())
        self.assertEqual(val, 4.0)

        # But increasing strictness above baseline is permitted
        success, msg, val = self.refiner.tune_policy("SANDBOX_STRICTNESS", 5.0)
        self.assertTrue(success)
        self.assertEqual(val, 5.0)

    def test_05_autonomous_evaluation_sweep_high_success(self):
        """Verifies autonomous policy tuning rewards high success with exploration headroom."""
        res = self.refiner.evaluate_and_refine_policies(
            recent_success_rate=0.98,
            average_latency_ms=100.0,
            ram_utilization_pct=35.0,
        )
        self.assertEqual(res["sweep_id"], 1)
        self.assertGreaterEqual(res["adjustments_count"], 1)
        exp_val = self.refiner.get_value("EXPLORATION_RATIO")
        self.assertGreater(exp_val, 0.20)

    def test_06_autonomous_evaluation_sweep_low_success(self):
        """Verifies autonomous policy tuning enforces strict verification upon failures."""
        res = self.refiner.evaluate_and_refine_policies(
            recent_success_rate=0.60,
            average_latency_ms=600.0,
            ram_utilization_pct=85.0,
        )
        self.assertEqual(res["sweep_id"], 1)
        self.assertEqual(self.refiner.get_value("VERIFICATION_RIGOR"), 3.0)
        self.assertEqual(self.refiner.get_value("COMPRESSION_THRESHOLD"), 0.65)

    def test_07_persistence_manifest(self):
        """Verifies policies persist to disk and reload reliably across instances."""
        self.refiner.tune_policy("RETRY_BUDGET", 5.0)

        refiner2 = AutonomousMetaPolicyRefiner(
            project_root=self.project_root,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
        )
        self.assertEqual(refiner2.get_value("RETRY_BUDGET"), 5.0)
        p = refiner2.get_policy("RETRY_BUDGET")
        self.assertEqual(p.total_adjustments, 1)

    def test_08_receipt_ledger_integration(self):
        """Verifies receipts are recorded for evaluations, tuning, and invariant locks."""
        # Invariant lock protection
        self.refiner.tune_policy("SANDBOX_STRICTNESS", 1.0)
        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("POLICY_INVARIANT_PROTECTED", actions)

        # Policy tuning
        self.refiner.tune_policy("RETRY_BUDGET", 4.0)
        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("META_POLICY_TUNED", actions)

        # Policy evaluation
        self.refiner.evaluate_and_refine_policies()
        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("META_POLICY_EVALUATED", actions)

    def test_09_ascii_policy_status_table(self):
        """Verifies CP1252-safe ASCII table formatting."""
        table = self.refiner.format_policy_status_table()
        self.assertIn("AUTONOMOUS META-POLICY REFINER", table)
        self.assertIn("RETRY_BUDGET", table)
        self.assertIn("SANDBOX_STRICTNESS", table)
        self.assertIn("Senin", table)
        # Strict CP1252 compatibility test
        table.encode("cp1252")

    def test_10_runtime_integration(self):
        """Verifies LucyRuntime binds and executes meta-policy refiner commands."""
        from backend.lucy_core.lucy_runtime import LucyRuntime

        runtime = LucyRuntime(project_root=self.project_root)
        self.assertTrue(hasattr(runtime, "meta_policy_refiner"))
        self.assertIsInstance(runtime.meta_policy_refiner, AutonomousMetaPolicyRefiner)

        # Test CLI commands via lucy_respond
        res = runtime.lucy_respond("/policy-status")
        self.assertIn("AUTONOMOUS META-POLICY REFINER", res)

        res_tune = runtime.lucy_respond("/tune-policy RETRY_BUDGET 6")
        self.assertIn("RETRY_BUDGET", res_tune)

        res_eval = runtime.lucy_respond("/evaluate-policies")
        self.assertIn("Meta-Policy Evaluation Sweep Complete", res_eval)


if __name__ == "__main__":
    unittest.main()
