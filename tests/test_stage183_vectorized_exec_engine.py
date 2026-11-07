r"""
tests/test_stage183_vectorized_exec_engine.py
Unit tests for Stage 183: Vectorized Execution Engine & SIMD Batch Operator
Era 19: Distributed Query Planning, Columnar Vector Storage & OLAP Analytics Engine
"""

from __future__ import annotations

import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

import unittest
from backend.lucy_core.vectorized_exec_engine import (
    ColumnVectorChunk,
    MorselQueue,
    SelectionVector,
    VectorChunk,
    VectorizedExecutionFabric,
    VectorizedFilter,
    VectorizedHashAggregate,
    VectorizedProject,
)


class TestVectorizedExecutionEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.fabric = VectorizedExecutionFabric(morsel_size=100)

    def test_selection_vector_bitwise_and_or(self) -> None:
        sel1 = SelectionVector(10, [0, 2, 4, 6, 8])
        sel2 = SelectionVector(10, [0, 1, 2, 3, 4])

        and_sel = sel1.bitwise_and(sel2)
        self.assertEqual(and_sel.to_list(), [0, 2, 4])

        or_sel = sel1.bitwise_or(sel2)
        self.assertEqual(or_sel.to_list(), [0, 1, 2, 3, 4, 6, 8])

    def test_vector_chunk_and_column_vectors(self) -> None:
        c1 = ColumnVectorChunk("id", "INT64", [10, 20, 30])
        c2 = ColumnVectorChunk("val", "FLOAT64", [1.5, 2.5, 3.5])
        chunk = VectorChunk(0, {"id": c1, "val": c2})

        self.assertEqual(chunk.physical_row_count, 3)
        self.assertEqual(chunk.row_count, 3)

        rows = chunk.to_row_dicts()
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[1]["id"], 20)
        self.assertEqual(rows[1]["val"], 2.5)

    def test_vectorized_filter_equality_and_comparison(self) -> None:
        chunk = VectorChunk(0, {
            "score": ColumnVectorChunk("score", "INT64", [50, 80, 95, 30, 80, 100]),
        })

        # Equality
        VectorizedFilter.evaluate(chunk, "score", "=", 80)
        self.assertEqual(chunk.selection.to_list(), [1, 4])

        # Greater than on reset chunk
        chunk.selection = None
        VectorizedFilter.evaluate(chunk, "score", ">=", 80)
        self.assertEqual(chunk.selection.to_list(), [1, 2, 4, 5])

    def test_vectorized_filter_between_and_in(self) -> None:
        chunk = VectorChunk(0, {
            "val": ColumnVectorChunk("val", "INT64", [10, 25, 50, 75, 100]),
            "cat": ColumnVectorChunk("cat", "STRING", ["A", "B", "C", "A", "D"]),
        })

        # Between
        VectorizedFilter.evaluate(chunk, "val", "BETWEEN", (20, 80))
        self.assertEqual(chunk.selection.to_list(), [1, 2, 3])

        # In on categorical
        VectorizedFilter.evaluate(chunk, "cat", "IN", ["A", "D"])
        self.assertEqual(chunk.selection.to_list(), [3])  # index 3 had val=75, cat='A'

    def test_vectorized_project_and_arithmetic(self) -> None:
        chunk = VectorChunk(0, {
            "price": ColumnVectorChunk("price", "FLOAT64", [10.0, 20.0, 30.0]),
            "qty": ColumnVectorChunk("qty", "INT64", [2, 5, 3]),
        })

        # Multiply price * qty -> total
        VectorizedProject.evaluate_arithmetic(chunk, "total", "price", "*", "qty")
        self.assertIn("total", chunk.columns)
        self.assertEqual(chunk.columns["total"].values, [20.0, 100.0, 90.0])

        # Project columns
        proj_chunk = VectorizedProject.project_columns(chunk, ["total"])
        self.assertIn("total", proj_chunk.columns)
        self.assertNotIn("price", proj_chunk.columns)

    def test_vectorized_hash_aggregate_group_by(self) -> None:
        chunk = VectorChunk(0, {
            "dept": ColumnVectorChunk("dept", "STRING", ["IT", "HR", "IT", "HR", "IT"]),
            "salary": ColumnVectorChunk("salary", "INT64", [1000, 800, 1200, 900, 1500]),
        })

        agg = VectorizedHashAggregate(
            group_by=["dept"],
            aggregates=[("SUM", "salary", "total_salary"), ("COUNT", "salary", "headcount")],
        )
        agg.process_morsel(chunk)
        res = agg.finalize()

        res_map = {r["dept"]: r for r in res}
        self.assertEqual(res_map["IT"]["total_salary"], 3700)
        self.assertEqual(res_map["IT"]["headcount"], 3)
        self.assertEqual(res_map["HR"]["total_salary"], 1700)
        self.assertEqual(res_map["HR"]["headcount"], 2)

    def test_vectorized_hash_aggregate_min_max_avg(self) -> None:
        chunk = VectorChunk(0, {
            "dept": ColumnVectorChunk("dept", "STRING", ["Sales", "Sales", "Sales"]),
            "val": ColumnVectorChunk("val", "FLOAT64", [10.0, 20.0, 30.0]),
        })
        agg = VectorizedHashAggregate(
            group_by=["dept"],
            aggregates=[
                ("MIN", "val", "min_val"),
                ("MAX", "val", "max_val"),
                ("AVG", "val", "avg_val"),
            ],
        )
        agg.process_morsel(chunk)
        res = agg.finalize()

        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["min_val"], 10.0)
        self.assertEqual(res[0]["max_val"], 30.0)
        self.assertEqual(res[0]["avg_val"], 20.0)

    def test_morsel_queue_distribution(self) -> None:
        chunks = [VectorChunk(i) for i in range(5)]
        mq = MorselQueue(chunks)
        self.assertEqual(mq.remaining(), 5)

        m1 = mq.get_next()
        self.assertEqual(m1.morsel_id, 0)
        self.assertEqual(mq.remaining(), 4)

        all_retrieved = [m1]
        while True:
            m = mq.get_next()
            if not m:
                break
            all_retrieved.append(m)

        self.assertEqual(len(all_retrieved), 5)
        self.assertEqual(mq.remaining(), 0)

    def test_fabric_load_and_query_execution(self) -> None:
        # Load 250 records into fabric with morsel_size=100 -> 3 morsels
        data = [{"id": i, "score": i * 10, "active": (i % 2 == 0)} for i in range(250)]
        loaded = self.fabric.load_table("users", data)
        self.assertEqual(loaded, 250)
        self.assertEqual(len(self.fabric.tables["users"]), 3)

        # Run filtered query: score > 2000
        rows, telemetry = self.fabric.execute_query(
            "users",
            filters=[("score", ">", 2000)],
            projections=["id", "score"],
        )
        self.assertEqual(len(rows), 49)  # 201..249
        self.assertEqual(telemetry.total_morsels, 3)
        self.assertEqual(telemetry.total_rows_scanned, 250)
        self.assertEqual(telemetry.total_rows_output, 49)
        self.assertGreater(telemetry.throughput_rows_per_sec, 0.0)

    def test_fabric_status_and_ascii_table(self) -> None:
        self.fabric.load_table("orders", [{"id": 1, "amt": 50}, {"id": 2, "amt": 150}])
        stat = self.fabric.status()
        self.assertEqual(stat["tables_count"], 1)

        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 183: VECTORIZED EXECUTION ENGINE & SIMD BATCH OPERATOR", tbl)
        self.assertIn("orders", tbl)


if __name__ == "__main__":
    unittest.main()
