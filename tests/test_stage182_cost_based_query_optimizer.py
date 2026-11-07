r"""
tests/test_stage182_cost_based_query_optimizer.py
Unit tests for Stage 182: Cost-Based Distributed Query Optimizer (CBO)
Era 19: Distributed Query Planning, Columnar Vector Storage & OLAP Analytics Engine
"""

from __future__ import annotations

import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

import unittest
from backend.lucy_core.cost_based_query_optimizer import (
    CostBasedQueryOptimizerFabric,
    CostModelWeights,
    LogicalAggregate,
    LogicalFilter,
    LogicalJoin,
    LogicalProject,
    LogicalScan,
    PhysicalBroadcastJoin,
    PhysicalHashAggregate,
    PhysicalHashJoin,
    PhysicalIndexScan,
    PhysicalProject,
    PhysicalSeqScan,
)


class TestCostBasedQueryOptimizer(unittest.TestCase):
    def setUp(self) -> None:
        self.cbo = CostBasedQueryOptimizerFabric()
        # Setup sample catalog
        self.cbo.register_table("users", row_count=100000, byte_size=8 * 1024 * 1024)
        self.cbo.add_column_stats("users", "id", data_type="INT64", ndv=100000, null_count=0, min_val=1, max_val=100000)
        self.cbo.add_column_stats("users", "age", data_type="INT64", ndv=80, null_count=100, min_val=18, max_val=98)
        self.cbo.add_column_stats("users", "country", data_type="STRING", ndv=50, null_count=500)
        self.cbo.add_index("users", "idx_users_id", "id", is_unique=True, leaf_pages=200, height=3)

        self.cbo.register_table("orders", row_count=1000, byte_size=128 * 1024)
        self.cbo.add_column_stats("orders", "order_id", data_type="INT64", ndv=1000, min_val=1, max_val=1000)
        self.cbo.add_column_stats("orders", "user_id", data_type="INT64", ndv=500, min_val=1, max_val=100000)
        self.cbo.add_column_stats("orders", "amount", data_type="FLOAT64", ndv=800, min_val=5.0, max_val=5000.0)

    def test_catalog_registration_and_stats(self) -> None:
        tbl = self.cbo.catalog.get("users")
        self.assertIsNotNone(tbl)
        self.assertEqual(tbl.row_count, 100000)
        self.assertEqual(len(tbl.columns), 3)
        self.assertIn("idx_users_id", tbl.indexes)
        self.assertGreater(tbl.page_count, 10)

    def test_selectivity_estimation_equality_and_inequality(self) -> None:
        # Equality on country with NDV=50 -> ~0.02
        sel_country = self.cbo.estimate_predicate_selectivity("users", {"col": "country", "op": "=", "val": "US"})
        self.assertAlmostEqual(sel_country, 0.02, delta=0.005)

        # Inequality on age > 58 with min=18, max=98 (span=80) -> (98-58)/80 = 0.5
        sel_age = self.cbo.estimate_predicate_selectivity("users", {"col": "age", "op": ">", "val": 58})
        self.assertAlmostEqual(sel_age, 0.5, delta=0.05)

        # Compound filters independence
        sel_compound = self.cbo.estimate_filters_selectivity("users", [
            {"col": "country", "op": "=", "val": "US"},
            {"col": "age", "op": ">", "val": 58},
        ])
        self.assertLess(sel_compound, sel_country)

    def test_histogram_selectivity_estimation(self) -> None:
        histogram = [
            (0.0, 100.0, 500),
            (101.0, 500.0, 300),
            (501.0, 1000.0, 200),
        ]
        self.cbo.add_column_stats("orders", "tier_points", data_type="FLOAT64", ndv=200, histogram=histogram)
        sel = self.cbo.estimate_predicate_selectivity("orders", {"col": "tier_points", "op": "=", "val": 50})
        self.assertGreater(sel, 0.0)
        self.assertLess(sel, 0.1)

    def test_cost_seq_scan(self) -> None:
        cost, rows = self.cbo.cost_seq_scan("users", [{"col": "country", "op": "=", "val": "US"}])
        self.assertGreater(cost, 0.0)
        self.assertAlmostEqual(rows, 2000, delta=200)

    def test_index_scan_vs_seq_scan_selection(self) -> None:
        # 1. Point lookup on indexed id -> IndexScan should be selected
        scan_point = LogicalScan("users", projection=["id", "country"], filters=[{"col": "id", "op": "=", "val": 42}])
        phys_point = self.cbo.optimize(scan_point)
        self.assertIsInstance(phys_point, PhysicalIndexScan)
        self.assertEqual(phys_point.index_name, "idx_users_id")

        # 2. Query without filter on indexed col -> SeqScan should be selected
        scan_full = LogicalScan("users", projection=["id", "country"], filters=[{"col": "country", "op": "=", "val": "US"}])
        phys_full = self.cbo.optimize(scan_full)
        self.assertIsInstance(phys_full, PhysicalSeqScan)

    def test_broadcast_join_selection(self) -> None:
        # users (100k rows) join orders (1,000 rows)
        # Because orders <= 5000 rows, optimizer should choose PhysicalBroadcastJoin
        join_logical = LogicalJoin(
            left=LogicalScan("users", projection=["id", "country"]),
            right=LogicalScan("orders", projection=["order_id", "user_id", "amount"]),
            left_keys=["id"],
            right_keys=["user_id"],
        )
        phys_join = self.cbo.optimize(join_logical)
        self.assertIsInstance(phys_join, PhysicalBroadcastJoin)
        self.assertEqual(phys_join.broadcast_side, "right")

    def test_hash_join_build_probe_selection(self) -> None:
        # Two large tables > 5000 rows
        self.cbo.register_table("events_large", row_count=50000, byte_size=4 * 1024 * 1024)
        self.cbo.register_table("logs_huge", row_count=200000, byte_size=16 * 1024 * 1024)

        join_logical = LogicalJoin(
            left=LogicalScan("logs_huge", projection=["log_id", "event_id"]),
            right=LogicalScan("events_large", projection=["event_id", "name"]),
            left_keys=["event_id"],
            right_keys=["event_id"],
        )
        phys_join = self.cbo.optimize(join_logical)
        self.assertIsInstance(phys_join, PhysicalHashJoin)
        # Smaller relation (events_large with 50,000 rows) must be the build side ('right')
        self.assertEqual(phys_join.build_side, "right")

    def test_system_r_dp_join_ordering(self) -> None:
        # Multi-table join across 3 relations
        self.cbo.register_table("items", row_count=500, byte_size=32 * 1024)
        conds = [
            {"left_tbl": "users", "right_tbl": "orders", "left_key": "id", "right_key": "user_id"},
            {"left_tbl": "orders", "right_tbl": "items", "left_key": "order_id", "right_key": "order_id"},
        ]
        phys_dp = self.cbo.optimize_multi_join_dp(["users", "orders", "items"], conds)
        self.assertIsInstance(phys_dp, (PhysicalHashJoin, PhysicalBroadcastJoin))
        self.assertGreater(phys_dp.cost, 0.0)

    def test_aggregate_and_project_plan_generation(self) -> None:
        scan = LogicalScan("orders", projection=["user_id", "amount"])
        agg = LogicalAggregate(
            child=scan,
            group_by=["user_id"],
            aggregates=[("SUM", "amount"), ("COUNT", "order_id")],
        )
        proj = LogicalProject(child=agg, projections=["user_id", "SUM(amount)"])
        phys_proj = self.cbo.optimize(proj)

        self.assertIsInstance(phys_proj, PhysicalProject)
        self.assertIsInstance(phys_proj.children[0], PhysicalHashAggregate)
        self.assertEqual(phys_proj.children[0].group_by, ["user_id"])

    def test_cbo_fabric_status_and_explain_ascii(self) -> None:
        scan = LogicalScan("users", projection=["id", "age"], filters=[{"col": "id", "op": "=", "val": 10}])
        phys = self.cbo.optimize(scan)
        explain_tree = phys.explain()
        self.assertIn("PhysicalIndexScan", explain_tree)
        self.assertIn("idx_users_id", explain_tree)

        status_tbl = self.cbo.format_ascii_status()
        self.assertIn("STAGE 182: COST-BASED DISTRIBUTED QUERY OPTIMIZER", status_tbl)
        self.assertIn("users", status_tbl)
        self.assertIn("orders", status_tbl)


if __name__ == "__main__":
    unittest.main()
