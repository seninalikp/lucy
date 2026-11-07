"""
tests/test_stage126_dynamic_context_budgeter.py
Verification suite for Stage 126: Dynamic Context Budget Allocator
Era 13: Self-Reflective Symbolic Mesh & Cognitive Graph Synthesizer
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.dynamic_context_budgeter import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    ERA_NAME,
    STAGE,
    STAGE_NAME,
    DynamicContextBudgetAllocator,
    ContextSliceAllocation,
    ContextBudgetSnapshot,
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


class TestStage126DynamicContextBudgeter(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)
        self.data_dir = self.project_root / "data" / "lucy" / "budget"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = MockReceiptLedger()
        self.budgeter = DynamicContextBudgetAllocator(
            project_root=self.project_root,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
            default_budget=4096,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_metadata(self):
        """Verifies sovereign operator identity and stage/era metadata."""
        self.assertEqual(STAGE, 126)
        self.assertEqual(ERA, 13)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")
        status = self.budgeter.status()
        self.assertEqual(status["stage"], 126)
        self.assertEqual(status["era"], 13)
        self.assertEqual(status["creator"], "Senin")
        self.assertEqual(status["creator_full_name"], "Senin Ali K P")

    def test_02_default_budget_allocation(self):
        """Verifies default 4096-token allocation across 5 prioritized slices."""
        status = self.budgeter.status()
        self.assertEqual(status["total_budget"], 4096)
        self.assertEqual(status["slices_count"], 5)

        sys_slice = self.budgeter.get_slice("SYSTEM_CORE_PROMPT")
        self.assertIsNotNone(sys_slice)
        self.assertEqual(sys_slice.priority, 1)
        self.assertTrue(sys_slice.is_immutable)
        self.assertEqual(sys_slice.allocated_tokens, int(4096 * 0.15))

        rag_slice = self.budgeter.get_slice("RETRIEVAL_RAG_KG")
        self.assertIsNotNone(rag_slice)
        self.assertEqual(rag_slice.priority, 3)
        self.assertFalse(rag_slice.is_immutable)
        self.assertEqual(rag_slice.allocated_tokens, int(4096 * 0.30))

    def test_03_hardware_mode_scaling(self):
        """Verifies budget dynamically adjusts to eco, balanced, and turbo hardware profiles."""
        snap_eco = self.budgeter.allocate_slices(hardware_mode="eco")
        self.assertEqual(snap_eco.total_budget_tokens, 2048)
        self.assertEqual(snap_eco.hardware_mode, "eco")

        snap_turbo = self.budgeter.allocate_slices(hardware_mode="turbo")
        self.assertEqual(snap_turbo.total_budget_tokens, 8192)
        self.assertEqual(snap_turbo.hardware_mode, "turbo")

        snap_custom = self.budgeter.allocate_slices(total_budget=16384)
        self.assertEqual(snap_custom.total_budget_tokens, 16384)

    def test_04_usage_tracking_and_overflow_compaction(self):
        """Verifies token usage registration and auto-compaction on slice overflow."""
        # Allocate balanced (4096 tokens, RETRIEVAL_RAG_KG has 1228 tokens)
        self.budgeter.allocate_slices(total_budget=4096)
        rag_slice = self.budgeter.get_slice("RETRIEVAL_RAG_KG")
        alloc = rag_slice.allocated_tokens

        # Register normal usage
        success = self.budgeter.register_usage("RETRIEVAL_RAG_KG", 500)
        self.assertTrue(success)
        rag_slice = self.budgeter.get_slice("RETRIEVAL_RAG_KG")
        self.assertEqual(rag_slice.used_tokens, 500)
        self.assertEqual(rag_slice.compaction_count, 0)

        # Trigger overflow (> alloc)
        self.budgeter.register_usage("RETRIEVAL_RAG_KG", alloc + 500)
        rag_slice = self.budgeter.get_slice("RETRIEVAL_RAG_KG")
        # Auto-compacted to 70% of alloc
        expected_target = int(alloc * 0.70)
        self.assertEqual(rag_slice.used_tokens, expected_target)
        self.assertEqual(rag_slice.compaction_count, 1)

    def test_05_immutable_slice_protection(self):
        """Verifies that SYSTEM_CORE_PROMPT is strictly immutable and immune to compaction."""
        sys_slice = self.budgeter.get_slice("SYSTEM_CORE_PROMPT")
        self.assertTrue(sys_slice.is_immutable)

        # Attempt to compact
        freed = self.budgeter.compact_slice("SYSTEM_CORE_PROMPT")
        self.assertEqual(freed, 0)
        self.assertEqual(sys_slice.compaction_count, 0)

    def test_06_manual_slice_compaction(self):
        """Verifies manual sliding window compaction on mutable slices."""
        self.budgeter.allocate_slices(total_budget=4096)
        op_slice = self.budgeter.get_slice("OPERATOR_DIALOGUE")
        alloc = op_slice.allocated_tokens

        # Set usage to 900
        self.budgeter.register_usage("OPERATOR_DIALOGUE", 900)
        target = int(alloc * 0.70)
        expected_freed = max(0, 900 - target)

        freed = self.budgeter.compact_slice("OPERATOR_DIALOGUE")
        self.assertEqual(freed, expected_freed)
        self.assertEqual(op_slice.used_tokens, target)
        self.assertEqual(op_slice.compaction_count, 1)

    def test_07_persistence_manifest(self):
        """Verifies context budget persists to JSON and reloads reliably."""
        self.budgeter.allocate_slices(total_budget=6000)
        self.budgeter.register_usage("SCRATCHPAD_REASONING", 300)

        # Create new instance with same data directory
        budgeter2 = DynamicContextBudgetAllocator(
            project_root=self.project_root,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
        )
        self.assertEqual(budgeter2._total_budget, 6000)
        scratch2 = budgeter2.get_slice("SCRATCHPAD_REASONING")
        self.assertEqual(scratch2.used_tokens, 300)

    def test_08_receipt_ledger_integration(self):
        """Verifies audit trail receipts emitted to the execution ledger."""
        self.budgeter.allocate_slices(total_budget=4096)
        # Check BUDGET_SLICES_ALLOCATED was recorded
        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("BUDGET_SLICES_ALLOCATED", actions)

        # Trigger compaction and verify CONTEXT_COMPACTED
        self.budgeter.compact_slice("RESPONSE_BUFFER")
        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("CONTEXT_COMPACTED", actions)

    def test_09_ascii_budget_status_table(self):
        """Verifies CP1252-safe ASCII table formatting."""
        table = self.budgeter.format_budget_status_table()
        self.assertIn("DYNAMIC CONTEXT BUDGET ALLOCATOR", table)
        self.assertIn("SYSTEM_CORE_PROMPT", table)
        self.assertIn("OPERATOR_DIALOGUE", table)
        self.assertIn("RETRIEVAL_RAG_KG", table)
        self.assertIn("Senin", table)
        self.assertIn("IMMUTABLE", table)
        # Verify strict CP1252 compatibility
        table.encode("cp1252")

    def test_10_runtime_integration(self):
        """Verifies LucyRuntime binds and executes context budgeter commands."""
        from backend.lucy_core.lucy_runtime import LucyRuntime

        runtime = LucyRuntime(project_root=self.project_root)
        self.assertTrue(hasattr(runtime, "context_budgeter"))
        self.assertIsInstance(runtime.context_budgeter, DynamicContextBudgetAllocator)

        # Test helper methods
        status = runtime.context_budgeter_status()
        self.assertEqual(status["stage"], 126)

        table = runtime.format_budget_status_table()
        self.assertIn("DYNAMIC CONTEXT BUDGET ALLOCATOR", table)

        # Test CLI commands via lucy_respond
        res = runtime.lucy_respond("/budget-status")
        self.assertIn("DYNAMIC CONTEXT BUDGET ALLOCATOR", res)

        res_alloc = runtime.lucy_respond("/allocate-budget turbo")
        self.assertIn("Context Budget Reallocated", res_alloc)

        res_compact = runtime.lucy_respond("/compact-context RETRIEVAL_RAG_KG")
        self.assertIn("Context Compacted", res_compact)


if __name__ == "__main__":
    unittest.main()
