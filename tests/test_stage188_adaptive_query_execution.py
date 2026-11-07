r"""
tests/test_stage188_adaptive_query_execution.py
Unit tests for Stage 188: Adaptive Query Execution (AQE) & Runtime Replanner
Era 19: Distributed Query Planning, Columnar Vector Storage & OLAP Analytics Engine
"""

from __future__ import annotations

import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

import unittest
from backend.lucy_core.adaptive_query_execution import (
    AdaptiveQueryExecutionFabric,
    DynamicPartitionCoalescer,
    PartitionMetric,
    RuntimeJoinReplanner,
    StageStatus,
)


class TestAdaptiveQueryExecution(unittest.TestCase):
    def setUp(self) -> None:
        self.fabric = AdaptiveQueryExecutionFabric(
            target_partition_bytes=64 * 1024,
            broadcast_byte_limit=32 * 1024,
        )

    def test_stage_creation_and_dag_dependencies(self) -> None:
        s1 = self.fabric.add_stage(1, "ScanUsers", "SCAN")
        s2 = self.fabric.add_stage(2, "JoinOrders", "JOIN", dependencies=[1])
        self.assertEqual(s1.status, StageStatus.PENDING)
        self.assertEqual(s2.dependencies, [1])
        self.assertEqual(len(self.fabric.stages), 2)

    def test_dynamic_partition_coalescing(self) -> None:
        # 5 small partitions of 10KB each (total 50KB <= 64KB target)
        metrics = [PartitionMetric(i, 100, 10 * 1024) for i in range(5)]
        ranges = DynamicPartitionCoalescer.coalesce(metrics, target_bytes=64 * 1024)
        # All 5 partitions coalesce into a single range
        self.assertEqual(len(ranges), 1)
        self.assertEqual(ranges[0].start_partition, 0)
        self.assertEqual(ranges[0].end_partition, 4)
        self.assertEqual(ranges[0].total_bytes, 50 * 1024)
        self.assertEqual(ranges[0].total_rows, 500)

    def test_dynamic_partition_coalescing_no_op_when_large(self) -> None:
        # 3 partitions of 80KB each (> 64KB target)
        metrics = [PartitionMetric(i, 500, 80 * 1024) for i in range(3)]
        ranges = DynamicPartitionCoalescer.coalesce(metrics, target_bytes=64 * 1024)
        self.assertEqual(len(ranges), 3)

    def test_runtime_join_broadcast_conversion(self) -> None:
        s1 = self.fabric.add_stage(1, "ScanSmallTable", "SCAN")
        s2 = self.fabric.add_stage(2, "JoinStage", "JOIN", dependencies=[1])

        # Small output: 10KB total <= 32KB broadcast limit
        metrics = [PartitionMetric(0, 100, 10 * 1024)]
        self.fabric.complete_stage_execution(1, metrics)

        self.assertTrue(s2.is_broadcast)
        self.assertEqual(self.fabric._aqe_broadcast_conversions, 1)

    def test_runtime_join_no_broadcast_when_large(self) -> None:
        s1 = self.fabric.add_stage(1, "ScanLargeTable", "SCAN")
        s2 = self.fabric.add_stage(2, "JoinStage", "JOIN", dependencies=[1])

        # Large output: 100KB > 32KB limit
        metrics = [PartitionMetric(0, 5000, 100 * 1024)]
        self.fabric.complete_stage_execution(1, metrics)

        self.assertFalse(s2.is_broadcast)
        self.assertEqual(self.fabric._aqe_broadcast_conversions, 0)

    def test_dynamic_skew_partition_detection(self) -> None:
        # 4 partitions: [10KB, 10KB, 10KB, 100KB]
        # median is 10KB, partition 3 is 100KB > 3 * 10KB
        metrics = [
            PartitionMetric(0, 100, 10 * 1024),
            PartitionMetric(1, 100, 10 * 1024),
            PartitionMetric(2, 100, 10 * 1024),
            PartitionMetric(3, 1000, 100 * 1024),
        ]
        skewed = RuntimeJoinReplanner.detect_skewed_partitions(metrics, skew_factor=3.0)
        self.assertEqual(skewed, [3])

    def test_complete_stage_execution_metrics_aggregation(self) -> None:
        s1 = self.fabric.add_stage(1, "ScanStage", "SCAN")
        metrics = [
            PartitionMetric(0, 150, 1500),
            PartitionMetric(1, 250, 2500),
        ]
        st = self.fabric.complete_stage_execution(1, metrics)
        self.assertEqual(st.status, StageStatus.COMPLETED)
        self.assertEqual(st.output_rows, 400)
        self.assertEqual(st.output_bytes, 4000)

    def test_multi_stage_aqe_pipeline(self) -> None:
        s1 = self.fabric.add_stage(1, "ScanUsers", "SCAN")
        s2 = self.fabric.add_stage(2, "ScanOrders", "SCAN")
        s3 = self.fabric.add_stage(3, "JoinUsersOrders", "JOIN", dependencies=[1, 2])

        # Stage 1 produces skewed partitions and small total bytes
        s1_metrics = [
            PartitionMetric(0, 50, 5 * 1024),
            PartitionMetric(1, 50, 5 * 1024),
            PartitionMetric(2, 500, 50 * 1024),  # skewed
        ]
        self.fabric.complete_stage_execution(1, s1_metrics)
        self.assertTrue(s1.is_skewed)
        self.assertIn(2, s1.skewed_partitions)

        # Stage 2 produces small bytes <= 32KB
        s2_metrics = [PartitionMetric(0, 20, 2 * 1024)]
        self.fabric.complete_stage_execution(2, s2_metrics)

        # Downstream join is converted to broadcast
        self.assertTrue(s3.is_broadcast)

    def test_aqe_fabric_status_counters(self) -> None:
        s1 = self.fabric.add_stage(1, "S1", "SCAN")
        # 4 small partitions coalesced
        m = [PartitionMetric(i, 10, 1000) for i in range(4)]
        self.fabric.complete_stage_execution(1, m)

        stat = self.fabric.status()
        self.assertEqual(stat["total_stages"], 1)
        self.assertEqual(stat["coalesce_optimizations"], 1)

    def test_fabric_format_ascii_status(self) -> None:
        self.fabric.add_stage(1, "TestStage", "SCAN")
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 188: ADAPTIVE QUERY EXECUTION (AQE) & RUNTIME REPLANNER", tbl)
        self.assertIn("TestStage", tbl)


if __name__ == "__main__":
    unittest.main()
