r"""
tests/test_stage184_distributed_hash_join.py
Unit tests for Stage 184: Distributed Hash Join & Broadcast Shuffle Fabric
Era 19: Distributed Query Planning, Columnar Vector Storage & OLAP Analytics Engine
"""

from __future__ import annotations

import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

import unittest
from backend.lucy_core.distributed_hash_join import (
    DistributedHashJoinFabric,
    JoinStrategy,
    JoinType,
    PartitionWorker,
)


class TestDistributedHashJoin(unittest.TestCase):
    def setUp(self) -> None:
        self.fabric = DistributedHashJoinFabric(num_partitions=4, broadcast_threshold=50, skew_threshold=0.25)

    def test_partition_worker_inner_join(self) -> None:
        worker = PartitionWorker(0)
        worker.add_build_row(101, {"id": 101, "dept": "Engineering"})
        worker.add_probe_row({"emp_id": 1, "dept_id": 101, "name": "Alice"})
        worker.add_probe_row({"emp_id": 2, "dept_id": 999, "name": "Bob"})

        res = worker.execute_local_join("dept_id", "id", JoinType.INNER)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "Alice")
        self.assertEqual(res[0]["dept"], "Engineering")

    def test_partition_worker_left_outer_join(self) -> None:
        worker = PartitionWorker(0)
        worker.add_build_row(101, {"id": 101, "dept": "Engineering"})
        worker.add_probe_row({"emp_id": 1, "dept_id": 101, "name": "Alice"})
        worker.add_probe_row({"emp_id": 2, "dept_id": 999, "name": "Bob"})

        res = worker.execute_local_join("dept_id", "id", JoinType.LEFT_OUTER)
        self.assertEqual(len(res), 2)
        names = {r["name"] for r in res}
        self.assertEqual(names, {"Alice", "Bob"})

    def test_partition_worker_semi_and_anti_join(self) -> None:
        worker = PartitionWorker(0)
        worker.add_build_row(101, {"id": 101})
        worker.add_probe_row({"emp_id": 1, "dept_id": 101})
        worker.add_probe_row({"emp_id": 2, "dept_id": 999})

        # Semi: only emp 1
        semi_res = worker.execute_local_join("dept_id", "id", JoinType.SEMI)
        self.assertEqual(len(semi_res), 1)
        self.assertEqual(semi_res[0]["emp_id"], 1)

        # Anti: only emp 2
        anti_res = worker.execute_local_join("dept_id", "id", JoinType.ANTI)
        self.assertEqual(len(anti_res), 1)
        self.assertEqual(anti_res[0]["emp_id"], 2)

    def test_partition_worker_right_and_full_outer_join(self) -> None:
        worker = PartitionWorker(0)
        worker.add_build_row(101, {"id": 101, "dept": "IT"})
        worker.add_build_row(202, {"id": 202, "dept": "Finance"})
        worker.add_probe_row({"emp_id": 1, "dept_id": 101, "name": "Alice"})
        worker.add_probe_row({"emp_id": 2, "dept_id": 303, "name": "Charlie"})

        # Right Outer: should contain Alice (matched) and Finance (unmatched build)
        right_res = worker.execute_local_join("dept_id", "id", JoinType.RIGHT_OUTER)
        self.assertEqual(len(right_res), 2)
        depts = {r.get("dept") for r in right_res}
        self.assertIn("IT", depts)
        self.assertIn("Finance", depts)

        # Full Outer: should contain Alice (matched), Charlie (unmatched probe), and Finance (unmatched build)
        full_res = worker.execute_local_join("dept_id", "id", JoinType.FULL_OUTER)
        self.assertEqual(len(full_res), 3)

    def test_broadcast_hash_join_execution(self) -> None:
        # Build relation has 10 rows (<= broadcast_threshold of 50)
        right = [{"id": i, "dept": f"Dept_{i}"} for i in range(10)]
        left = [{"emp_id": j, "dept_id": j % 10, "name": f"User_{j}"} for j in range(100)]

        results, telemetry = self.fabric.execute_join(left, right, "dept_id", "id")
        self.assertEqual(telemetry.strategy_used, JoinStrategy.BROADCAST)
        self.assertEqual(len(results), 100)
        self.assertEqual(telemetry.output_rows, 100)

    def test_shuffle_hash_join_execution(self) -> None:
        # Build relation has 100 rows (> broadcast_threshold of 50), uniform keys
        right = [{"id": i, "dept": f"Dept_{i}"} for i in range(100)]
        left = [{"emp_id": j, "dept_id": j % 100, "name": f"User_{j}"} for j in range(200)]

        results, telemetry = self.fabric.execute_join(left, right, "dept_id", "id")
        self.assertEqual(telemetry.strategy_used, JoinStrategy.SHUFFLE_HASH)
        self.assertEqual(len(results), 200)

    def test_join_skew_detection(self) -> None:
        # 100 rows, key 42 appears 40 times (40% > 25% threshold)
        rows = [{"k": 42} for _ in range(40)] + [{"k": i} for i in range(60)]
        skewed = self.fabric.detect_skew(rows, "k")
        self.assertEqual(len(skewed), 1)
        self.assertEqual(skewed[0][0], 42)
        self.assertGreaterEqual(skewed[0][2], 0.25)

    def test_skew_mitigated_shuffle_join(self) -> None:
        # Create skewed probe relation (key 99 appears 50 times out of 100 rows)
        left = [{"emp_id": i, "dept_id": 99} for i in range(50)] + [{"emp_id": i, "dept_id": i} for i in range(50)]
        right = [{"id": i, "dept": f"D_{i}"} for i in range(100)]  # > 50 to avoid broadcast

        results, telemetry = self.fabric.execute_join(left, right, "dept_id", "id")
        self.assertEqual(telemetry.strategy_used, JoinStrategy.SKEW_MITIGATED_SHUFFLE)
        self.assertIn("99", telemetry.skewed_keys_detected)
        self.assertGreater(len(results), 50)

    def test_shuffled_network_bytes_tracking(self) -> None:
        left = [{"id": 1, "val": "abc"}, {"id": 2, "val": "def"}]
        right = [{"rid": 1, "desc": "one"}, {"rid": 2, "desc": "two"}]
        results, telemetry = self.fabric.execute_join(left, right, "id", "rid")
        self.assertGreater(telemetry.network_bytes_shuffled, 0)
        self.assertEqual(self.fabric.status()["total_shuffled_bytes"], telemetry.network_bytes_shuffled)

    def test_fabric_status_and_ascii_table(self) -> None:
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 184: DISTRIBUTED HASH JOIN & BROADCAST SHUFFLE FABRIC", tbl)
        self.assertIn("Cluster Partitions", tbl)
        self.assertIn("Broadcast Threshold", tbl)


if __name__ == "__main__":
    unittest.main()
