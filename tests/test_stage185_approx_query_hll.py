r"""
tests/test_stage185_approx_query_hll.py
Unit tests for Stage 185: Approximate Query Processing & HyperLogLog Count-Distinct
Era 19: Distributed Query Planning, Columnar Vector Storage & OLAP Analytics Engine
"""

from __future__ import annotations

import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

import math
import random
import unittest
from backend.lucy_core.approx_query_hll import (
    ApproxQueryFabric,
    CountMinSketch,
    HyperLogLog,
    TDigest,
)


class TestApproxQueryHLL(unittest.TestCase):
    def setUp(self) -> None:
        self.fabric = ApproxQueryFabric()

    def test_hll_cardinality_estimation_small_range(self) -> None:
        hll = HyperLogLog(precision=10)  # m = 1024
        # Insert 100 distinct elements
        for i in range(100):
            hll.add(f"user_{i}")
        card = hll.cardinality()
        # Small range linear counting should be very precise (< 5% error)
        self.assertAlmostEqual(card, 100, delta=10)

    def test_hll_cardinality_estimation_large_range(self) -> None:
        hll = HyperLogLog(precision=10)  # m = 1024, error ~ 3.25%
        # Insert 10,000 distinct items
        for i in range(10000):
            hll.add(f"item_uuid_{i}")
        card = hll.cardinality()
        # Standard error 3.25% of 10000 is 325, allowing 3 sigma (~1000)
        self.assertGreater(card, 9000)
        self.assertLess(card, 11000)

    def test_hll_merge_preservation(self) -> None:
        hll1 = HyperLogLog(precision=10)
        hll2 = HyperLogLog(precision=10)

        for i in range(500):
            hll1.add(f"token_{i}")
        for i in range(400, 900):  # 100 overlap, 800 total distinct
            hll2.add(f"token_{i}")

        merged = hll1.merge(hll2)
        card = merged.cardinality()
        # Expected ~900 distinct
        self.assertAlmostEqual(card, 900, delta=90)

    def test_count_min_sketch_point_query(self) -> None:
        cms = CountMinSketch(depth=5, width=1024)
        for _ in range(500):
            cms.add("heavy_key")
        for i in range(100):
            cms.add(f"light_key_{i}")

        est_heavy = cms.estimate("heavy_key")
        self.assertGreaterEqual(est_heavy, 500)
        self.assertLessEqual(est_heavy, 520)

        est_light = cms.estimate("light_key_5")
        self.assertGreaterEqual(est_light, 1)
        self.assertLessEqual(est_light, 10)

        est_nonexistent = cms.estimate("never_seen")
        self.assertLessEqual(est_nonexistent, 5)

    def test_count_min_sketch_merge(self) -> None:
        cms1 = CountMinSketch(depth=4, width=512)
        cms2 = CountMinSketch(depth=4, width=512)

        cms1.add("apple", 15)
        cms2.add("apple", 25)
        cms2.add("orange", 10)

        merged = cms1.merge(cms2)
        self.assertGreaterEqual(merged.estimate("apple"), 40)
        self.assertGreaterEqual(merged.estimate("orange"), 10)

    def test_tdigest_uniform_distribution_quantiles(self) -> None:
        td = TDigest(delta=100.0)
        # 1,000 uniform values from 0.0 to 1000.0
        for i in range(1001):
            td.add(float(i))

        p50 = td.quantile(0.5)
        p90 = td.quantile(0.9)
        p99 = td.quantile(0.99)

        self.assertIsNotNone(p50)
        self.assertAlmostEqual(p50, 500.0, delta=20.0)
        self.assertAlmostEqual(p90, 900.0, delta=30.0)
        self.assertAlmostEqual(p99, 990.0, delta=15.0)

    def test_tdigest_extreme_tail_precision(self) -> None:
        td = TDigest(delta=150.0)
        # Skewed tail values
        for i in range(500):
            td.add(float(i))
        # Add 5 extreme outliers
        for _ in range(5):
            td.add(5000.0)

        p99 = td.quantile(0.99)
        self.assertIsNotNone(p99)
        self.assertGreater(p99, 450.0)

    def test_fabric_streaming_observation(self) -> None:
        for i in range(200):
            self.fabric.observe("web_traffic", "ip_address", f"192.168.1.{i % 50}")
            self.fabric.observe("web_traffic", "latency_ms", float(i % 100))

        self.assertEqual(self.fabric._total_observations, 400)
        k_ip = self.fabric._key("web_traffic", "ip_address")
        self.assertIn(k_ip, self.fabric.hll_sketches)
        self.assertIn(k_ip, self.fabric.cms_sketches)

    def test_fabric_approx_queries(self) -> None:
        # Batch observe 500 items with 100 distinct
        vals = [f"sku_{i % 100}" for i in range(500)]
        self.fabric.observe_batch("store", "sku", vals)

        card = self.fabric.approx_count_distinct("store", "sku")
        self.assertAlmostEqual(card, 100, delta=15)

        freq = self.fabric.approx_frequency("store", "sku", "sku_10")
        self.assertGreaterEqual(freq, 5)

        # Numerical column for percentile
        self.fabric.observe_batch("store", "price", [float(i) for i in range(100)])
        p50 = self.fabric.approx_percentile("store", "price", 0.5)
        self.assertIsNotNone(p50)
        self.assertAlmostEqual(p50, 50.0, delta=10.0)

    def test_fabric_status_and_ascii_table(self) -> None:
        self.fabric.observe("metrics", "cpu", 45.0)
        stat = self.fabric.status()
        self.assertGreaterEqual(stat["columns_tracked_count"], 1)

        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 185: APPROXIMATE QUERY PROCESSING & HLL COUNT-DISTINCT", tbl)
        self.assertIn("metrics.cpu", tbl)


if __name__ == "__main__":
    unittest.main()
