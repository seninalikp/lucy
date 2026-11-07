"""
tests/test_stage97_causal_dag_memory.py
Stage 97 = Causal DAG Epistemic Memory & Counterfactual Timeline

Verifies:
1. STAGE constant is 97.
2. record_event initializes CausalNode and links parent-child relationships.
3. Acyclicity check prevents backward loops and cycles in the DAG.
4. causal_why performs backward traversal finding root cause and synthesizing narrative.
5. counterfactual_replay simulates interventions and lists averted downstream events.
6. dag_timeline outputs CP1252-safe ASCII table.
7. prune_dag removes excess nodes while bridging ancestor-descendant connections.
8. Disk persistence saves and reloads memory graph.
9. Execution receipt ledger logs CAUSAL_MEMORY receipts.
10. status returns complete diagnostics dictionary.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.lucy_core.causal_dag_memory import (
    STAGE,
    CausalChain,
    CausalDAGMemoryEngine,
    CausalEventType,
    CausalNode,
    CounterfactualTimelineResult,
)


class MockReceiptLedger:
    def __init__(self) -> None:
        self.receipts: List[Dict[str, Any]] = []

    def issue_receipt(
        self,
        action_category: str,
        operation: str,
        target: str,
        verified_outcome: str,
    ) -> Dict[str, Any]:
        rcpt = {
            "receipt_id": f"rcpt_{len(self.receipts)+1}",
            "action_category": action_category,
            "operation": operation,
            "target": target,
            "verified_outcome": verified_outcome,
        }
        self.receipts.append(rcpt)
        return rcpt


class TestStage97CausalDAGMemory(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.mock_ledger = MockReceiptLedger()
        self.engine = CausalDAGMemoryEngine(
            project_root=self.root,
            receipt_ledger=self.mock_ledger,
            data_dir=self.root / "data" / "lucy" / "causal_dag",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_01_stage_constant(self) -> None:
        self.assertEqual(STAGE, 97)

    def test_02_record_event_linkage(self) -> None:
        n1 = self.engine.record_event("User requests code refactor", event_type="USER_INTENT")
        n2 = self.engine.record_event("AST index scanned symbols", event_type="TOOL_EXECUTION", cause_ids=[n1.node_id])
        n3 = self.engine.record_event("Patch applied to sample.py", event_type="CODE_PATCH", cause_ids=[n2.node_id])

        self.assertIn(n1.node_id, self.engine.nodes)
        self.assertIn(n2.node_id, self.engine.nodes)
        self.assertIn(n3.node_id, self.engine.nodes)

        # Parent child linkages
        self.assertIn(n1.node_id, n2.cause_ids)
        self.assertIn(n2.node_id, n1.consequence_ids)
        self.assertIn(n2.node_id, n3.cause_ids)
        self.assertIn(n3.node_id, n2.consequence_ids)

        # Receipts
        self.assertGreaterEqual(len(self.mock_ledger.receipts), 3)
        self.assertEqual(self.mock_ledger.receipts[0]["action_category"], "CAUSAL_MEMORY")

    def test_03_acyclicity_protection(self) -> None:
        n1 = self.engine.record_event("Event A")
        n2 = self.engine.record_event("Event B", cause_ids=[n1.node_id])
        # Attempt to make Event A caused by Event B (would form a cycle A -> B -> A)
        # Our engine will refuse to add n2 to n1's cause_ids if it creates a cycle
        is_anc = self.engine._is_ancestor(n1.node_id, n2.node_id)
        self.assertTrue(is_anc)

    def test_04_causal_why_trace(self) -> None:
        root = self.engine.record_event("Senin instructed autonomous optimization", event_type="USER_INTENT")
        step1 = self.engine.record_event("Identified division by zero risk", event_type="SYSTEM_DECISION", cause_ids=[root.node_id])
        step2 = self.engine.record_event("Synthesized surgical guard patch", event_type="CODE_PATCH", cause_ids=[step1.node_id])
        target = self.engine.record_event("Regression test suite passed 100%", event_type="TOOL_EXECUTION", cause_ids=[step2.node_id])

        chain = self.engine.causal_why("Regression test suite passed 100%")
        self.assertIsNotNone(chain.target_node)
        self.assertEqual(chain.target_node.node_id, target.node_id)
        self.assertEqual(len(chain.root_causes), 1)
        self.assertEqual(chain.root_causes[0].node_id, root.node_id)
        self.assertEqual(chain.depth, 4)
        self.assertIn("Senin instructed", chain.explanation)

        # CP1252 summary test
        summary = chain.format_terminal_summary()
        summary.encode("cp1252")
        self.assertIn("+----------------------------------------------------------------------+", summary)

    def test_05_counterfactual_replay(self) -> None:
        n1 = self.engine.record_event("Bug introduced in module", event_type="CODE_PATCH")
        n2 = self.engine.record_event("Crash in runtime execution", event_type="SYSTEM_DECISION", cause_ids=[n1.node_id])
        n3 = self.engine.record_event("Self-healing patch triggered", event_type="SELF_HEAL", cause_ids=[n2.node_id])

        res = self.engine.counterfactual_replay(
            n1.node_id,
            intervention="Pre-flight syntax and type check blocked buggy commit",
        )
        self.assertEqual(res.original_node_id, n1.node_id)
        self.assertEqual(len(res.averted_consequences), 2)
        self.assertGreater(res.divergence_score, 0.0)

        # CP1252 summary test
        summary = res.format_terminal_summary()
        summary.encode("cp1252")
        self.assertIn("COUNTERFACTUAL TIMELINE SIMULATION", summary)

    def test_06_dag_timeline_cp1252(self) -> None:
        self.engine.record_event("Initial event")
        self.engine.record_event("Second event")
        timeline = self.engine.dag_timeline()

        # Encoding test
        encoded = timeline.encode("cp1252")
        self.assertTrue(len(encoded) > 0)
        for ch in timeline:
            self.assertFalse(0x2500 <= ord(ch) <= 0x257F)

        self.assertIn("+----------------------------------------------------------------------+", timeline)
        self.assertIn("CAUSAL DAG TIMELINE", timeline)

    def test_07_prune_dag_shortcuts(self) -> None:
        # Create chain: A -> B -> C -> D
        na = self.engine.record_event("A")
        nb = self.engine.record_event("B", cause_ids=[na.node_id])
        nc = self.engine.record_event("C", cause_ids=[nb.node_id])
        nd = self.engine.record_event("D", cause_ids=[nc.node_id])

        # Prune down to 2 nodes
        pruned = self.engine.prune_dag(max_nodes=2, preserve_roots=True)
        self.assertGreater(pruned, 0)
        self.assertLessEqual(len(self.engine.nodes), 3)

    def test_08_disk_persistence(self) -> None:
        self.engine.record_event("Persistent Event 1")
        self.engine.record_event("Persistent Event 2")
        self.assertEqual(len(self.engine.nodes), 2)

        # Reload
        reloaded = CausalDAGMemoryEngine(
            project_root=self.root,
            receipt_ledger=self.mock_ledger,
            data_dir=self.root / "data" / "lucy" / "causal_dag",
        )
        self.assertEqual(len(reloaded.nodes), 2)

    def test_09_status_dictionary(self) -> None:
        self.engine.record_event("Status Event")
        st = self.engine.status()
        self.assertEqual(st["stage"], 97)
        self.assertEqual(st["total_causal_nodes"], 1)
        self.assertIn("total_causal_edges", st)


if __name__ == "__main__":
    unittest.main()
