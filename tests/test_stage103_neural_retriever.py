"""
tests/test_stage103_neural_retriever.py
Stage 103: Hybrid Neural-Lexical Vector RAG Engine Unit Tests
"""

import math
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.neural_retriever import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    STAGE,
    VECTOR_DIM,
    CodeChunk,
    HybridNeuralRetriever,
    SearchResponse,
    SearchResultItem,
)


class MockReceiptLedger:
    def __init__(self):
        self.receipts = []

    def issue_receipt(self, action_category, operation, target, verified_outcome):
        rec = {
            "category": action_category,
            "operation": operation,
            "target": target,
            "outcome": verified_outcome,
        }
        self.receipts.append(rec)
        return rec


class TestStage103NeuralRetriever(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="lucy_stage103_test_")
        self.temp_path = Path(self.temp_dir)
        self.project_root = Path(__file__).resolve().parent.parent

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_constants_and_metadata(self):
        self.assertEqual(STAGE, 103)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")
        self.assertEqual(VECTOR_DIM, 64)

    def test_02_tokenize_and_projection(self):
        retriever = HybridNeuralRetriever(
            project_root=self.project_root,
            data_dir=self.temp_path / "rag",
        )
        tokens = retriever._tokenize("def compute_kernel_telemetry(data_stream):")
        self.assertIn("compute", tokens)
        self.assertIn("kernel", tokens)
        self.assertIn("telemetry", tokens)

        vec = retriever._project_dense_vector("def compute_kernel_telemetry(data_stream):")
        self.assertEqual(len(vec), 64)
        norm = math.sqrt(sum(v * v for v in vec))
        self.assertAlmostEqual(norm, 1.0, places=3)

    def test_03_cosine_similarity(self):
        retriever = HybridNeuralRetriever(
            project_root=self.project_root,
            data_dir=self.temp_path / "rag",
        )
        v1 = retriever._project_dense_vector("hardware throttle guard telemetry")
        v2 = retriever._project_dense_vector("hardware throttle guard telemetry")
        v3 = retriever._project_dense_vector("unrelated cooking recipe apple pie")

        sim_identical = retriever._cosine_sim(v1, v2)
        sim_dissimilar = retriever._cosine_sim(v1, v3)

        self.assertAlmostEqual(sim_identical, 1.0, places=2)
        self.assertLess(sim_dissimilar, sim_identical)

    def test_04_chunk_python_file(self):
        test_py = self.temp_path / "sample_service.py"
        test_py.write_text(
            'class SecurityAuditor:\n'
            '    """Audits local sandbox."""\n'
            '    def run_audit(self):\n'
            '        return "SECURE"\n\n'
            'def standalone_helper():\n'
            '    return 42\n',
            encoding="utf-8",
        )

        retriever = HybridNeuralRetriever(
            project_root=self.temp_path,
            data_dir=self.temp_path / "rag",
        )
        chunks = retriever._chunk_python_file(test_py)
        self.assertGreaterEqual(len(chunks), 2)

        sym_names = [c.symbol_name for c in chunks]
        self.assertIn("SecurityAuditor", sym_names)
        self.assertIn("standalone_helper", sym_names)

        c = chunks[0]
        self.assertIsInstance(c, CodeChunk)
        self.assertEqual(len(c.dense_vector), 64)

    def test_05_reindex_and_bm25_search(self):
        retriever = HybridNeuralRetriever(
            project_root=self.project_root,
            data_dir=self.temp_path / "rag",
        )
        res = retriever.reindex()
        self.assertGreater(res["chunks_indexed"], 50)
        self.assertGreater(res["unique_terms"], 100)

        search_res = retriever.search("supervisor watchdog heartbeat", top_k=3)
        self.assertIsInstance(search_res, SearchResponse)
        self.assertGreater(len(search_res.results), 0)

        top_hit = search_res.results[0]
        self.assertIsInstance(top_hit, SearchResultItem)
        self.assertGreater(top_hit.rrf_score, 0.0)

    def test_06_exact_symbol_boosting(self):
        retriever = HybridNeuralRetriever(
            project_root=self.project_root,
            data_dir=self.temp_path / "rag",
        )
        search_res = retriever.search("KernelSupervisor", top_k=5)
        self.assertGreater(len(search_res.results), 0)

        # At least one result should have exact match flag set
        exact_matches = [r for r in search_res.results if r.exact_match]
        self.assertGreater(len(exact_matches), 0)
        self.assertIn("KernelSupervisor", exact_matches[0].chunk.symbol_name)

    def test_07_retrieve_context_window(self):
        retriever = HybridNeuralRetriever(
            project_root=self.project_root,
            data_dir=self.temp_path / "rag",
        )
        context = retriever.retrieve_context_window("ExecutionProfiler", max_tokens=1000)
        self.assertIn("Sovereign Neural RAG Context", context)
        self.assertIn("```python", context)
        self.assertIn("ExecutionProfiler", context)

    def test_08_receipt_ledger_integration(self):
        ledger = MockReceiptLedger()
        retriever = HybridNeuralRetriever(
            project_root=self.project_root,
            receipt_ledger=ledger,
            data_dir=self.temp_path / "rag",
        )
        retriever.reindex()
        retriever.search("telemetry vram", top_k=2)

        categories = [r["category"] for r in ledger.receipts]
        self.assertIn("RAG_REINDEX", categories)
        self.assertIn("HYBRID_RETRIEVAL_QUERY", categories)

    def test_09_cp1252_terminal_summary(self):
        retriever = HybridNeuralRetriever(
            project_root=self.project_root,
            data_dir=self.temp_path / "rag",
        )
        search_res = retriever.search("mutation fuzzer patcher", top_k=3)
        summary = search_res.format_terminal_summary()
        self.assertIn("LUCY OS - HYBRID NEURAL-LEXICAL RAG", summary)
        self.assertIn("STAGE 103: DENSE BM25 + VECTOR RRF", summary)
        summary.encode("cp1252")

    def test_10_status_and_persistence(self):
        retriever = HybridNeuralRetriever(
            project_root=self.project_root,
            data_dir=self.temp_path / "rag",
        )
        st = retriever.status()
        self.assertEqual(st["stage"], 103)
        self.assertEqual(st["creator"], "Senin")
        self.assertGreater(st["total_chunks"], 0)
        self.assertTrue(st["index_persisted"])

        # Reload from saved disk index
        retriever_reloaded = HybridNeuralRetriever(
            project_root=self.project_root,
            data_dir=self.temp_path / "rag",
        )
        self.assertEqual(len(retriever_reloaded.chunks), st["total_chunks"])


if __name__ == "__main__":
    unittest.main()
