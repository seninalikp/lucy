r"""
tests/test_stage112_semantic_cache.py
Comprehensive test suite for Stage 112: Semantic Inference Cache
Era 12: The Autonomous Cognitive Matrix & Distributed IPC Fabric
"""

import tempfile
import time
import unittest
from pathlib import Path

from backend.lucy_core.semantic_cache import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    STAGE,
    CacheEntry,
    SemanticInferenceCache,
    _compute_vector,
    _cosine_similarity,
    _estimate_tokens,
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


class TestStage112SemanticCache(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.data_dir = self.root / "data" / "cache"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.receipt_ledger = MockReceiptLedger()

        self.cache = SemanticInferenceCache(
            project_root=self.root,
            data_dir=self.data_dir,
            receipt_ledger=self.receipt_ledger,
            similarity_threshold=0.85,
            max_entries=10,
            auto_persist=True,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_01_initialization_defaults(self) -> None:
        st = self.cache.status()
        self.assertEqual(st["stage"], 112)
        self.assertEqual(st["era"], 12)
        self.assertEqual(st["creator"], CREATOR_NAME)
        self.assertEqual(st["creator_full_name"], CREATOR_FULL_NAME)
        self.assertEqual(st["active_entries"], 0)
        self.assertEqual(st["max_entries"], 10)
        self.assertEqual(st["similarity_threshold"], 0.85)

    def test_02_vector_math_and_token_estimation(self) -> None:
        toks = _estimate_tokens("Lucy OS sovereign offline intelligence core")
        self.assertGreater(toks, 3)

        v1 = _compute_vector("git commit and push changes to remote")
        v2 = _compute_vector("git commit and push changes to origin")
        v3 = _compute_vector("make a delicious cup of espresso coffee")

        sim_git = _cosine_similarity(v1, v2)
        sim_coffee = _cosine_similarity(v1, v3)

        self.assertGreater(sim_git, 0.70)
        self.assertLess(sim_coffee, 0.30)

    def test_03_store_and_exact_match(self) -> None:
        entry = self.cache.store("What is Lucy OS?", "Lucy OS is a sovereign offline desktop operating assistant.")
        self.assertIsInstance(entry, CacheEntry)
        self.assertEqual(entry.prompt, "What is Lucy OS?")

        res = self.cache.lookup("what is lucy os?")
        self.assertIsNotNone(res)
        found_entry, match_type, sim = res
        self.assertEqual(match_type, "EXACT")
        self.assertEqual(sim, 1.0)
        self.assertEqual(found_entry.hits, 1)
        self.assertIn("sovereign offline", found_entry.response)

    def test_04_semantic_similarity_lookup(self) -> None:
        self.cache.store(
            "How do I setup a proxy server on windows?",
            "Use netsh winhttp set proxy 127.0.0.1:8080 in administrative PowerShell.",
        )

        res = self.cache.lookup("How to setup proxy server on windows?")
        self.assertIsNotNone(res)
        found_entry, match_type, sim = res
        self.assertEqual(match_type, "SEMANTIC")
        self.assertGreaterEqual(sim, 0.85)
        self.assertIn("netsh winhttp", found_entry.response)

    def test_05_dissimilar_query_miss(self) -> None:
        self.cache.store("Show system CPU temperature", "CPU temperature is currently 42C.")
        res = self.cache.lookup("Write a fast binary search algorithm in Python")
        self.assertIsNone(res)

        st = self.cache.status()
        self.assertEqual(st["misses"], 1)

    def test_06_threshold_override(self) -> None:
        self.cache.store("Configure PostgreSQL connection string", "host=localhost dbname=lucy user=admin")

        # Stricter threshold misses
        miss = self.cache.lookup("PostgreSQL connection string setup", threshold=0.95)
        self.assertIsNone(miss)

        # Permissive threshold hits
        hit = self.cache.lookup("PostgreSQL connection string setup", threshold=0.70)
        self.assertIsNotNone(hit)

    def test_07_lru_eviction(self) -> None:
        small_cache = SemanticInferenceCache(
            project_root=self.root,
            data_dir=self.data_dir / "small",
            max_entries=3,
            auto_persist=False,
        )

        small_cache.store("q1", "r1")
        time.sleep(0.01)
        small_cache.store("q2", "r2")
        time.sleep(0.01)
        small_cache.store("q3", "r3")
        time.sleep(0.01)

        # Access q1 to make q2 oldest
        small_cache.lookup("q1")
        time.sleep(0.01)

        # Store q4 -> should evict q2
        small_cache.store("q4", "r4")

        self.assertEqual(len(small_cache._entries), 3)
        self.assertIsNotNone(small_cache.lookup("q1"))
        self.assertIsNone(small_cache.lookup("q2"))  # evicted!
        self.assertIsNotNone(small_cache.lookup("q3"))
        self.assertIsNotNone(small_cache.lookup("q4"))

    def test_08_ttl_expiration(self) -> None:
        self.cache.store("transient query", "transient response", ttl_sec=0.1)
        # Immediate lookup succeeds
        self.assertIsNotNone(self.cache.lookup("transient query"))

        # Sleep past TTL
        time.sleep(0.15)
        self.assertIsNone(self.cache.lookup("transient query"))

    def test_09_persistence_and_reload(self) -> None:
        self.cache.store("Persistent Prompt A", "Persistent Response A")
        self.cache.store("Persistent Prompt B", "Persistent Response B")

        # Create new instance pointing to same data_dir
        cache2 = SemanticInferenceCache(
            project_root=self.root,
            data_dir=self.data_dir,
            auto_persist=True,
        )

        self.assertEqual(len(cache2._entries), 2)
        res = cache2.lookup("persistent prompt a")
        self.assertIsNotNone(res)
        self.assertEqual(res[0].response, "Persistent Response A")

    def test_10_flush_cache(self) -> None:
        self.cache.store("Query 1", "Ans 1")
        self.cache.store("Query 2", "Ans 2")
        self.assertEqual(len(self.cache._entries), 2)

        flushed = self.cache.flush()
        self.assertEqual(flushed, 2)
        self.assertEqual(len(self.cache._entries), 0)
        self.assertIsNone(self.cache.lookup("Query 1"))

    def test_11_receipt_ledger_integration(self) -> None:
        self.cache.store("Receipt test query", "Receipt test answer")
        self.cache.lookup("Receipt test query")
        self.cache.flush()

        cats = [r["action_category"] for r in self.receipt_ledger.receipts]
        self.assertIn("INFERENCE_CACHE_STORE", cats)
        self.assertIn("INFERENCE_CACHE_HIT", cats)
        self.assertIn("INFERENCE_CACHE_FLUSH", cats)

    def test_12_ascii_status_table_format(self) -> None:
        self.cache.store("Show Lucy status", "Lucy is operational.")
        tbl = self.cache.format_cache_status_table()

        self.assertIn("LUCY OS - SEMANTIC INFERENCE CACHE", tbl)
        self.assertIn("Active Cached Entries", tbl)
        self.assertIn(CREATOR_NAME, tbl)
        self.assertIn(CREATOR_FULL_NAME, tbl)
        self.assertTrue(tbl.startswith("+--"))


if __name__ == "__main__":
    unittest.main()
