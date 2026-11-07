r"""
tests/test_stage186_materialized_view_ivm.py
Unit tests for Stage 186: Materialized View Refresh & Incremental View Maintenance (IVM)
Era 19: Distributed Query Planning, Columnar Vector Storage & OLAP Analytics Engine
"""

from __future__ import annotations

import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

import unittest
from backend.lucy_core.materialized_view_ivm import (
    MaterializedViewIVMFabric,
    RefreshPolicy,
    ViewAggregationSpec,
    ViewStatus,
)


class TestMaterializedViewIVM(unittest.TestCase):
    def setUp(self) -> None:
        self.fabric = MaterializedViewIVMFabric()
        self.users = [
            {"id": 1, "name": "Alice", "country": "US", "spend": 100.0},
            {"id": 2, "name": "Bob", "country": "UK", "spend": 250.0},
            {"id": 3, "name": "Charlie", "country": "US", "spend": 300.0},
        ]
        self.fabric.register_base_table("users", self.users)

    def test_create_view_and_initial_materialization(self) -> None:
        vdef = self.fabric.create_materialized_view("mv_users_all", ["users"])
        self.assertEqual(vdef.row_count, 3)
        self.assertEqual(vdef.status, ViewStatus.FRESH)
        rows = self.fabric.query_view("mv_users_all")
        self.assertEqual(len(rows), 3)

    def test_eager_ivm_insert_propagation(self) -> None:
        self.fabric.create_materialized_view("mv_users_eager", ["users"], refresh_policy=RefreshPolicy.EAGER)
        new_row = {"id": 4, "name": "Diana", "country": "CA", "spend": 400.0}
        self.fabric.mutate_table("users", inserted=[new_row])

        rows = self.fabric.query_view("mv_users_eager")
        self.assertEqual(len(rows), 4)
        names = {r["name"] for r in rows}
        self.assertIn("Diana", names)

    def test_eager_ivm_delete_propagation(self) -> None:
        self.fabric.create_materialized_view("mv_users_del", ["users"], refresh_policy=RefreshPolicy.EAGER)
        del_row = {"id": 2, "name": "Bob", "country": "UK", "spend": 250.0}
        self.fabric.mutate_table("users", deleted=[del_row])

        rows = self.fabric.query_view("mv_users_del")
        self.assertEqual(len(rows), 2)
        names = {r["name"] for r in rows}
        self.assertNotIn("Bob", names)

    def test_lazy_refresh_policy_staleness(self) -> None:
        vdef = self.fabric.create_materialized_view("mv_users_lazy", ["users"], refresh_policy=RefreshPolicy.LAZY)
        self.assertEqual(vdef.status, ViewStatus.FRESH)

        # Mutating table marks lazy view STALE
        self.fabric.mutate_table("users", inserted=[{"id": 5, "name": "Evan", "country": "FR", "spend": 120.0}])
        self.assertEqual(vdef.status, ViewStatus.STALE)

        # Querying triggers on-demand recompute
        rows = self.fabric.query_view("mv_users_lazy")
        self.assertEqual(len(rows), 4)
        self.assertEqual(vdef.status, ViewStatus.FRESH)

    def test_ivm_with_filters(self) -> None:
        # Only US users
        self.fabric.create_materialized_view(
            "mv_us_users", ["users"],
            filters=[("country", "=", "US")],
        )
        rows = self.fabric.query_view("mv_us_users")
        self.assertEqual(len(rows), 2)  # Alice and Charlie

        # Insert UK user (should NOT be added to view)
        self.fabric.mutate_table("users", inserted=[{"id": 6, "name": "Fiona", "country": "UK", "spend": 50.0}])
        self.assertEqual(len(self.fabric.query_view("mv_us_users")), 2)

        # Insert US user (SHOULD be added)
        self.fabric.mutate_table("users", inserted=[{"id": 7, "name": "George", "country": "US", "spend": 90.0}])
        self.assertEqual(len(self.fabric.query_view("mv_us_users")), 3)

    def test_ivm_with_projections(self) -> None:
        self.fabric.create_materialized_view(
            "mv_names_only", ["users"],
            projections=["name", "spend"],
        )
        rows = self.fabric.query_view("mv_names_only")
        self.assertEqual(len(rows), 3)
        self.assertNotIn("country", rows[0])
        self.assertIn("spend", rows[0])

    def test_ivm_aggregation_sum_and_count(self) -> None:
        # Aggregation view: GROUP BY country -> SUM(spend), COUNT(id)
        agg_spec = ViewAggregationSpec(
            group_by=["country"],
            aggregates=[("SUM", "spend", "total_spend"), ("COUNT", "id", "user_count")],
        )
        self.fabric.create_materialized_view(
            "mv_spend_by_country", ["users"],
            aggregation_spec=agg_spec,
        )
        rows = self.fabric.query_view("mv_spend_by_country")
        row_map = {r["country"]: r for r in rows}
        self.assertEqual(row_map["US"]["total_spend"], 400.0)
        self.assertEqual(row_map["US"]["user_count"], 2)
        self.assertEqual(row_map["UK"]["total_spend"], 250.0)
        self.assertEqual(row_map["UK"]["user_count"], 1)

        # Eager IVM update: add new US user spending 150.0
        self.fabric.mutate_table("users", inserted=[{"id": 8, "name": "Hannah", "country": "US", "spend": 150.0}])
        rows_after = self.fabric.query_view("mv_spend_by_country")
        row_map_after = {r["country"]: r for r in rows_after}
        self.assertEqual(row_map_after["US"]["total_spend"], 550.0)
        self.assertEqual(row_map_after["US"]["user_count"], 3)

    def test_ivm_join_materialized_view(self) -> None:
        departments = [
            {"dept_id": 10, "dept_name": "Sales"},
            {"dept_id": 20, "dept_name": "R&D"},
        ]
        employees = [
            {"emp_id": 101, "dept_id": 10, "name": "Ian"},
            {"emp_id": 102, "dept_id": 20, "name": "Julia"},
        ]
        self.fabric.register_base_table("departments", departments)
        self.fabric.register_base_table("employees", employees)

        join_spec = {
            "left_tbl": "employees",
            "right_tbl": "departments",
            "left_key": "dept_id",
            "right_key": "dept_id",
        }
        self.fabric.create_materialized_view("mv_emp_dept", ["employees", "departments"], join_spec=join_spec)
        rows = self.fabric.query_view("mv_emp_dept")
        self.assertEqual(len(rows), 2)
        dept_names = {r["dept_name"] for r in rows}
        self.assertEqual(dept_names, {"Sales", "R&D"})

    def test_lsn_multi_version_tracking(self) -> None:
        initial_lsn = self.fabric._global_lsn
        lsn1 = self.fabric.mutate_table("users", inserted=[{"id": 9, "name": "Kevin", "country": "US", "spend": 10.0}])
        self.assertGreater(lsn1, initial_lsn)
        self.assertEqual(self.fabric.base_table_lsns["users"], lsn1)

    def test_fabric_status_and_ascii_table(self) -> None:
        self.fabric.create_materialized_view("mv_stat_test", ["users"])
        stat = self.fabric.status()
        self.assertGreaterEqual(stat["views_count"], 1)

        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 186: MATERIALIZED VIEW & INCREMENTAL VIEW MAINTENANCE (IVM)", tbl)
        self.assertIn("mv_stat_test", tbl)


if __name__ == "__main__":
    unittest.main()
