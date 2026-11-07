r"""
tests/test_stage116_local_vector_db.py
Comprehensive test suite for Stage 116: Persistent HNSW Vector DB
Era 12: The Autonomous Cognitive Matrix & Distributed IPC Fabric
"""

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.local_vector_db import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    STAGE,
    PersistentLocalVectorDB,
    SearchResult,
    VectorDoc,
    cosine_distance,
    euclidean_distance,
    text_to_dense_vector,
)


class MockReceiptLedger:
    def __init__(self) -> None:
        self.receipts = []

    def record_receipt(self, action_category: str, operation: str, target: str, verified_outcome: str):
        rcpt = {
            "action_category": action_category,
            "operation": operation,
            "target": target,
            "verified_outcome": verified_outcome,
        }
        self.receipts.append(rcpt)
        return rcpt


class TestStage116LocalVectorDB(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.data_dir = self.root / "data" / "vector_db"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.receipt_ledger = MockReceiptLedger()

        self.db = PersistentLocalVectorDB(
            project_root=self.root,
            data_dir=self.data_dir,
            receipt_ledger=self.receipt_ledger,
            dim=64,
            m=4,
            ef_construction=16,
            ef_search=16,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_01_initialization(self) -> None:
        st = self.db.status()
        self.assertEqual(st["stage"], 116)
        self.assertEqual(st["era"], 12)
        self.assertEqual(st["creator"], CREATOR_NAME)
        self.assertEqual(st["creator_full_name"], CREATOR_FULL_NAME)
        self.assertEqual(st["total_vectors"], 0)
        self.assertEqual(st["dim"], 64)

    def test_02_distance_metrics(self) -> None:
        u = [1.0, 0.0, 0.0]
        v = [1.0, 0.0, 0.0]
        w = [0.0, 1.0, 0.0]

        # Cosine distance
        self.assertAlmostEqual(cosine_distance(u, v), 0.0, places=4)
        self.assertAlmostEqual(cosine_distance(u, w), 1.0, places=4)

        # Euclidean distance
        self.assertAlmostEqual(euclidean_distance(u, v), 0.0, places=4)
        self.assertGreater(euclidean_distance(u, w), 1.4)

    def test_03_text_embedding_consistency(self) -> None:
        v1 = text_to_dense_vector("Lucy OS sovereign offline intelligence core", dim=16)
        v2 = text_to_dense_vector("Lucy OS sovereign offline intelligence core", dim=16)
        v3 = text_to_dense_vector("Bake chocolate chip cookies recipe", dim=16)

        self.assertEqual(len(v1), 16)
        self.assertEqual(v1, v2)  # Deterministic reproduction

        d_same = cosine_distance(v1, v2)
        d_diff = cosine_distance(v1, v3)
        self.assertAlmostEqual(d_same, 0.0, places=4)
        self.assertGreater(d_diff, 0.2)

    def test_04_insert_and_exact_search(self) -> None:
        target_vec = [100.0 + float(i) for i in range(16)]
        self.db.insert("doc_target", target_vec, {"tag": "target"})

        # Insert distractors (distinct vector ranges)
        for i in range(1, 6):
            self.db.insert(f"doc_{i}", [float(i * 10 + j) for j in range(16)])

        results = self.db.search(target_vec, top_k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].doc_id, "doc_target")
        self.assertAlmostEqual(results[0].distance, 0.0, places=4)
        self.assertGreaterEqual(results[0].score, 0.999)

    def test_05_search_top_k(self) -> None:
        for i in range(15):
            vec = [float(i + j) for j in range(16)]
            self.db.insert(f"vec_{i}", vec)

        q = [5.0 for _ in range(16)]
        results = self.db.search(q, top_k=4)
        self.assertEqual(len(results), 4)
        # Results must be sorted in ascending distance order
        distances = [r.distance for r in results]
        self.assertEqual(distances, sorted(distances))

    def test_06_insert_text_and_search_text(self) -> None:
        self.db.insert_text("doc_lucy", "Lucy OS sovereign local desktop core architecture")
        self.db.insert_text("doc_coffee", "Brewing dark roast espresso coffee in the morning")
        self.db.insert_text("doc_git", "Git commit push repository merge rebase branch")

        matches = self.db.search_text("Lucy desktop operating system", top_k=1)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].doc_id, "doc_lucy")

    def test_07_delete_vector(self) -> None:
        self.db.insert("to_delete", [1.0] * 16)
        self.assertIsNotNone(self.db.get("to_delete"))

        ok = self.db.delete("to_delete")
        self.assertTrue(ok)
        self.assertIsNone(self.db.get("to_delete"))
        self.assertEqual(len(self.db._nodes), 0)

    def test_08_multi_layer_graph_hierarchy(self) -> None:
        for i in range(25):
            self.db.insert(f"node_{i}", [float(i * j) for j in range(16)])

        st = self.db.status()
        self.assertEqual(st["total_vectors"], 25)
        self.assertGreaterEqual(st["max_level"], 0)

    def test_09_persistence_and_reload(self) -> None:
        self.db.insert_text("persistent_doc", "Persistent memory across process restarts")

        # Create second instance loading from disk
        db2 = PersistentLocalVectorDB(
            project_root=self.root,
            data_dir=self.data_dir,
            dim=64,
        )

        self.assertEqual(len(db2._nodes), 1)
        res = db2.search_text("Persistent memory restarts", top_k=1)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].doc_id, "persistent_doc")

    def test_10_receipt_ledger_integration(self) -> None:
        self.db.insert("receipt_doc", [0.5] * 16)
        self.db.search([0.5] * 16, top_k=1)

        cats = [r["action_category"] for r in self.receipt_ledger.receipts]
        self.assertIn("HNSW_VECTOR_INSERT", cats)
        self.assertIn("HNSW_VECTOR_SEARCH", cats)

    def test_11_ascii_status_table_formatting(self) -> None:
        self.db.insert_text("status_doc", "Status table test vector")
        tbl = self.db.format_vectordb_status_table()

        self.assertIn("LUCY OS - PERSISTENT HNSW VECTOR DB", tbl)
        self.assertIn("Vector Dimensionality", tbl)
        self.assertIn(CREATOR_NAME, tbl)
        self.assertIn(CREATOR_FULL_NAME, tbl)
        self.assertTrue(tbl.startswith("+--"))


if __name__ == "__main__":
    unittest.main()
