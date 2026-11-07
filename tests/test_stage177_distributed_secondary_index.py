r"""
tests/test_stage177_distributed_secondary_index.py
Stage 177 Test Suite: Distributed Secondary Indexing & Global Query Fabric
Era 18: Autonomous Distributed Storage, Geo-Replication & Sharding Primitives
"""

import unittest

from backend.lucy_core.distributed_secondary_index import (
    ERA,
    ERA_NAME,
    STAGE,
    STAGE_NAME,
    DistributedSecondaryIndexFabric,
    QueryOperator,
    QueryPredicate,
    QueryResult,
    SecondaryIndexTable,
    get_secondary_index_fabric,
)


class TestStage177DistributedSecondaryIndex(unittest.TestCase):
    def setUp(self) -> None:
        self.fabric = DistributedSecondaryIndexFabric()

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 177)
        self.assertEqual(ERA, 18)
        self.assertEqual(
            STAGE_NAME,
            "Distributed Secondary Indexing & Global Query Fabric",
        )
        self.assertEqual(
            ERA_NAME,
            "Autonomous Distributed Storage, Geo-Replication & Sharding Primitives",
        )

    def test_02_create_secondary_index_and_backfill(self) -> None:
        # Pre-populate records
        self.fabric.put_record("user_1", {"name": "Alice", "role": "engineer", "age": 28})
        self.fabric.put_record("user_2", {"name": "Bob", "role": "admin", "age": 34})

        # Create index after records exist -> verifies backfill
        idx = self.fabric.create_index("idx_role", "role")
        self.assertIn("engineer", idx.postings)
        self.assertIn("admin", idx.postings)
        self.assertIn("user_1", idx.postings["engineer"])
        self.assertIn("user_2", idx.postings["admin"])

    def test_03_synchronous_index_maintenance_on_put(self) -> None:
        self.fabric.create_index("idx_city", "city")
        self.fabric.put_record("pk_1", {"city": "Berlin"})
        self.fabric.put_record("pk_2", {"city": "Tokyo"})
        self.fabric.put_record("pk_3", {"city": "Berlin"})

        idx = self.fabric._indexes["idx_city"]
        self.assertEqual(len(idx.lookup_equals("Berlin")), 2)
        self.assertEqual(idx.lookup_equals("Berlin"), {"pk_1", "pk_3"})
        self.assertEqual(idx.lookup_equals("Tokyo"), {"pk_2"})

    def test_04_index_cleanup_on_update_and_delete(self) -> None:
        self.fabric.create_index("idx_status", "status")
        self.fabric.put_record("task_1", {"status": "PENDING"})
        self.assertEqual(self.fabric._indexes["idx_status"].lookup_equals("PENDING"), {"task_1"})

        # Update status
        self.fabric.put_record("task_1", {"status": "COMPLETED"})
        self.assertEqual(self.fabric._indexes["idx_status"].lookup_equals("PENDING"), set())
        self.assertEqual(self.fabric._indexes["idx_status"].lookup_equals("COMPLETED"), {"task_1"})

        # Delete record
        self.fabric.delete_record("task_1")
        self.assertEqual(self.fabric._indexes["idx_status"].lookup_equals("COMPLETED"), set())

    def test_05_unique_index_constraint_enforcement(self) -> None:
        self.fabric.create_index("idx_email", "email", is_unique=True)
        self.fabric.put_record("u1", {"email": "senin@lucy.os"})

        with self.assertRaises(ValueError):
            self.fabric.put_record("u2", {"email": "senin@lucy.os"})

    def test_06_equals_and_in_predicates(self) -> None:
        self.fabric.create_index("idx_dept", "dept")
        self.fabric.put_record("emp_1", {"dept": "AI", "salary": 150000})
        self.fabric.put_record("emp_2", {"dept": "Systems", "salary": 140000})
        self.fabric.put_record("emp_3", {"dept": "AI", "salary": 160000})

        # EQ predicate
        res_eq = self.fabric.query([QueryPredicate(field="dept", operator=QueryOperator.EQUALS, value="AI")])
        self.assertEqual(res_eq.total_matched, 2)
        self.assertEqual(set(res_eq.matched_primary_keys), {"emp_1", "emp_3"})

        # IN predicate
        res_in = self.fabric.query([QueryPredicate(field="dept", operator=QueryOperator.IN, values_list=["AI", "Systems"])])
        self.assertEqual(res_in.total_matched, 3)

    def test_07_range_and_prefix_predicates(self) -> None:
        self.fabric.create_index("idx_age", "age")
        self.fabric.create_index("idx_tag", "tag")

        self.fabric.put_record("p1", {"age": 20, "tag": "prod_server_1"})
        self.fabric.put_record("p2", {"age": 30, "tag": "prod_db_1"})
        self.fabric.put_record("p3", {"age": 40, "tag": "stage_web_1"})

        # RANGE predicate (25 <= age <= 45)
        res_range = self.fabric.query([QueryPredicate(field="age", operator=QueryOperator.RANGE, min_val=25, max_val=45)])
        self.assertEqual(set(res_range.matched_primary_keys), {"p2", "p3"})

        # PREFIX predicate
        res_pref = self.fabric.query([QueryPredicate(field="tag", operator=QueryOperator.PREFIX, value="prod_")])
        self.assertEqual(set(res_pref.matched_primary_keys), {"p1", "p2"})

    def test_08_compound_boolean_query_planner(self) -> None:
        self.fabric.create_index("idx_role", "role")
        self.fabric.create_index("idx_level", "level")

        self.fabric.put_record("u1", {"role": "core", "level": 10})
        self.fabric.put_record("u2", {"role": "core", "level": 5})
        self.fabric.put_record("u3", {"role": "daemon", "level": 10})

        # AND query: role == core AND level == 10
        res_and = self.fabric.query(
            predicates=[
                QueryPredicate(field="role", operator=QueryOperator.EQUALS, value="core"),
                QueryPredicate(field="level", operator=QueryOperator.EQUALS, value=10),
            ],
            match_all=True,
        )
        self.assertEqual(res_and.matched_primary_keys, ["u1"])

        # OR query: role == daemon OR level == 5
        res_or = self.fabric.query(
            predicates=[
                QueryPredicate(field="role", operator=QueryOperator.EQUALS, value="daemon"),
                QueryPredicate(field="level", operator=QueryOperator.EQUALS, value=5),
            ],
            match_all=False,
        )
        self.assertEqual(set(res_or.matched_primary_keys), {"u2", "u3"})

    def test_09_aggregation_compute(self) -> None:
        self.fabric.create_index("idx_cat", "category")
        self.fabric.put_record("i1", {"category": "hardware", "price": 100})
        self.fabric.put_record("i2", {"category": "hardware", "price": 200})
        self.fabric.put_record("i3", {"category": "hardware", "price": 300})

        res = self.fabric.query(
            predicates=[QueryPredicate(field="category", operator=QueryOperator.EQUALS, value="hardware")],
            aggregates=["SUM:price", "AVG:price", "MIN:price", "MAX:price"],
        )
        self.assertEqual(res.aggregates["count"], 3)
        self.assertEqual(res.aggregates["SUM:price"], 600)
        self.assertEqual(res.aggregates["AVG:price"], 200.0)
        self.assertEqual(res.aggregates["MIN:price"], 100)
        self.assertEqual(res.aggregates["MAX:price"], 300)

    def test_10_ascii_formatting_and_singleton(self) -> None:
        self.fabric.create_index("idx_team", "team")
        st = self.fabric.status()
        self.assertEqual(st["stage"], 177)
        self.assertIn("idx_team", st["indexes"])

        tbl = self.fabric.format_ascii_status()
        self.assertIn("LUCY STAGE 177: DISTRIBUTED SECONDARY INDEXING & GLOBAL QUERY FABRIC", tbl)
        self.assertIn("idx_team", tbl)

        s1 = get_secondary_index_fabric()
        s2 = get_secondary_index_fabric()
        self.assertIs(s1, s2)


if __name__ == "__main__":
    unittest.main()
