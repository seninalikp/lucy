"""
tests/test_stage76_memory_distiller.py
Unit tests for Stage 76: Autonomous Memory Pruning & Cognitive Distillation
"""

import json
import os
import shutil
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

from backend.lucy_core.memory_distiller import (
    CognitiveDistiller,
    DistillationCandidate,
    DistillationReport,
    STAGE,
)


class MockMemoryGraph:
    def __init__(self, nodes=None):
        self.data = {"version": 63, "nodes": nodes or []}

    def _read(self):
        return self.data

    def _write(self, data):
        self.data = data


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


class TestStage76MemoryDistiller(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_stage76_test_"))
        self.ledger = MockReceiptLedger()

        now_str = datetime.now().isoformat()
        old_str = "2024-01-01T00:00:00"

        self.sample_nodes = [
            # Pinned fact: should NEVER be pruned
            {"id": "n1_pinned", "fact": "User prefers sovereign CLI terminal", "pinned": True, "created_at": old_str, "status": "active"},
            # Fresh active fact: should be kept
            {"id": "n2_fresh", "fact": "User is building Lucy Stage 76", "pinned": False, "created_at": now_str, "status": "active", "reference_count": 2},
            # Stale superseded fact: should be pruned
            {"id": "n3_superseded", "fact": "User was testing old UI interface", "pinned": False, "created_at": old_str, "status": "superseded"},
            # Ancient unreferenced fact: should be pruned
            {"id": "n4_ancient", "fact": "Temporary test variable 1234", "pinned": False, "created_at": old_str, "status": "active", "reference_count": 0},
        ]
        self.graph = MockMemoryGraph(self.sample_nodes)
        self.distiller = CognitiveDistiller(
            memory_graph=self.graph,
            receipt_ledger=self.ledger,
            archive_dir=self.test_dir,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_stage_constant(self):
        self.assertEqual(STAGE, 76)

    def test_02_pinned_protection(self):
        candidates = self.distiller.evaluate_nodes(self.sample_nodes)
        pinned_c = next(c for c in candidates if c.node_id == "n1_pinned")
        self.assertEqual(pinned_c.salience_score, 1.0)
        self.assertEqual(pinned_c.action, "keep")
        self.assertIn("Pinned fact", pinned_c.reason)

    def test_03_superseded_and_ancient_pruned(self):
        candidates = self.distiller.evaluate_nodes(self.sample_nodes)
        sup_c = next(c for c in candidates if c.node_id == "n3_superseded")
        self.assertEqual(sup_c.action, "prune")

        ancient_c = next(c for c in candidates if c.node_id == "n4_ancient")
        self.assertEqual(ancient_c.action, "prune")

        fresh_c = next(c for c in candidates if c.node_id == "n2_fresh")
        self.assertEqual(fresh_c.action, "keep")

    def test_04_dry_run_non_mutating(self):
        report = self.distiller.dry_run()
        self.assertEqual(report.total_nodes_before, 4)
        self.assertEqual(report.total_nodes_after, 2)
        self.assertEqual(report.pruned_count, 2)
        self.assertEqual(report.pinned_protected_count, 1)

        # Ensure graph itself was NOT modified
        self.assertEqual(len(self.graph._read()["nodes"]), 4)

    def test_05_distill_execution(self):
        report = self.distiller.distill()
        self.assertEqual(report.pruned_count, 2)
        self.assertEqual(report.total_nodes_after, 2)

        # Memory graph now only contains 2 nodes
        remaining_ids = [n["id"] for n in self.graph._read()["nodes"]]
        self.assertEqual(set(remaining_ids), {"n1_pinned", "n2_fresh"})

        # Checkpoint file exists
        self.assertTrue(self.distiller.checkpoint_file.exists())
        with open(self.distiller.checkpoint_file, "r", encoding="utf-8") as f:
            cp_data = json.load(f)
        self.assertEqual(cp_data["total_nodes"], 2)
        self.assertEqual(cp_data["pruned_count"], 2)

        # Receipt recorded
        self.assertEqual(len(self.ledger.receipts), 1)
        self.assertEqual(self.ledger.receipts[0]["operation"], "distill_memory_graph")

    def test_06_archived_pruned_nodes(self):
        self.distiller.distill(archive_pruned=True)
        self.assertTrue(self.distiller.pruned_archive_file.exists())

        with open(self.distiller.pruned_archive_file, "r", encoding="utf-8") as f:
            lines = [json.loads(l) for l in f if l.strip()]
        self.assertEqual(len(lines), 2)
        archived_ids = [l["node"]["id"] for l in lines]
        self.assertIn("n3_superseded", archived_ids)
        self.assertIn("n4_ancient", archived_ids)

    def test_07_stats(self):
        stats = self.distiller.stats()
        self.assertEqual(stats["total_nodes"], 4)
        self.assertEqual(stats["pinned_nodes"], 1)
        self.assertEqual(stats["superseded_nodes"], 1)

    def test_08_terminal_summary_ascii_safe(self):
        report = self.distiller.distill()
        summary = report.format_terminal_summary()

        # Strict ASCII encode
        summary.encode("ascii")
        self.assertIn("COGNITIVE MEMORY DISTILLATION REPORT", summary)
        self.assertIn("+", summary)
        self.assertIn("-", summary)
        self.assertIn("|", summary)
        self.assertIn("n3_superseded", summary)


if __name__ == "__main__":
    unittest.main()
