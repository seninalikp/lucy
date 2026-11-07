r"""
tests/test_stage189_olap_chunk_compactor.py
Unit tests for Stage 189: Distributed OLAP Storage Chunk Compactor & Parquet Encoder
Era 19: Distributed Query Planning, Columnar Vector Storage & OLAP Analytics Engine
"""

from __future__ import annotations

import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

import unittest
from backend.lucy_core.olap_chunk_compactor import (
    MAGIC_BYTES,
    OLAPChunkCompactorFabric,
    ParquetEncoder,
)


class TestOLAPChunkCompactor(unittest.TestCase):
    def setUp(self) -> None:
        self.fabric = OLAPChunkCompactorFabric(target_row_group_size=100)

    def test_parquet_encoder_magic_bytes(self) -> None:
        schema = {"id": "INT64", "name": "STRING"}
        rows = [[{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]]
        encoded = ParquetEncoder.encode_file(schema, rows)
        self.assertTrue(encoded.startswith(MAGIC_BYTES))
        self.assertTrue(encoded.endswith(MAGIC_BYTES))

    def test_parquet_metadata_serialization_roundtrip(self) -> None:
        schema = {"sku": "STRING", "price": "FLOAT64"}
        rows = [[{"sku": "A101", "price": 19.99}, {"sku": "B202", "price": 49.99}]]
        encoded = ParquetEncoder.encode_file(schema, rows)

        meta = ParquetEncoder.decode_metadata(encoded)
        self.assertEqual(meta.schema, schema)
        self.assertEqual(meta.total_rows, 2)
        self.assertEqual(len(meta.row_groups), 1)

    def test_parquet_data_page_zlib_and_crc32(self) -> None:
        schema = {"val": "INT64"}
        rows = [[{"val": i} for i in range(50)]]
        encoded = ParquetEncoder.encode_file(schema, rows)
        meta = ParquetEncoder.decode_metadata(encoded)

        rg_rows = ParquetEncoder.decode_row_group(encoded, meta.row_groups[0])
        self.assertEqual(len(rg_rows), 50)
        self.assertEqual(rg_rows[25]["val"], 25)

    def test_column_statistics_min_max_nulls(self) -> None:
        schema = {"score": "INT64"}
        rows = [[{"score": 10}, {"score": None}, {"score": 90}, {"score": 50}]]
        encoded = ParquetEncoder.encode_file(schema, rows)
        meta = ParquetEncoder.decode_metadata(encoded)

        col_meta = meta.row_groups[0].columns["score"]
        self.assertEqual(col_meta.min_value, 10)
        self.assertEqual(col_meta.max_value, 90)
        self.assertEqual(col_meta.null_count, 1)
        self.assertGreater(col_meta.uncompressed_bytes, 0)
        self.assertGreater(col_meta.compressed_bytes, 0)

    def test_row_group_chunking_on_compaction(self) -> None:
        # Ingest 250 rows with row_group_size = 100 -> 3 row groups
        data = [{"id": i, "val": i * 2} for i in range(250)]
        self.fabric.append_rows("metrics", data)
        meta = self.fabric.compact_table("metrics")

        self.assertEqual(meta.total_rows, 250)
        self.assertEqual(len(meta.row_groups), 3)
        self.assertEqual(meta.row_groups[0].num_rows, 100)
        self.assertEqual(meta.row_groups[1].num_rows, 100)
        self.assertEqual(meta.row_groups[2].num_rows, 50)

    def test_predicate_pushdown_row_group_pruning_equality(self) -> None:
        # Group 0: 0..99, Group 1: 100..199, Group 2: 200..249
        data = [{"id": i, "tag": f"t_{i}"} for i in range(250)]
        self.fabric.append_rows("items", data)
        self.fabric.compact_table("items")

        # Search for id = 150: should prune Group 0 and Group 2, reading only Group 1
        res = self.fabric.scan_with_pruning("items", filters=[("id", "=", 150)])
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["id"], 150)
        # Pruned 2 row groups
        self.assertEqual(self.fabric._row_groups_pruned_count, 2)

    def test_predicate_pushdown_row_group_pruning_inequality(self) -> None:
        # Group 0: id 0..99, Group 1: id 100..199
        data = [{"id": i} for i in range(200)]
        self.fabric.append_rows("events", data)
        self.fabric.compact_table("events")

        # Filter: id > 150 -> should prune Group 0 (max_value = 99 < 150)
        res = self.fabric.scan_with_pruning("events", filters=[("id", ">", 150)])
        self.assertEqual(len(res), 49)  # 151..199
        self.assertGreaterEqual(self.fabric._row_groups_pruned_count, 1)

    def test_scan_with_projections(self) -> None:
        data = [{"id": 1, "a": 10, "b": 20, "c": 30}]
        self.fabric.append_rows("proj_table", data)
        self.fabric.compact_table("proj_table")

        res = self.fabric.scan_with_pruning("proj_table", projections=["id", "c"])
        self.assertEqual(len(res), 1)
        self.assertIn("c", res[0])
        self.assertNotIn("a", res[0])
        self.assertNotIn("b", res[0])

    def test_compactor_fabric_appends_and_metrics(self) -> None:
        self.fabric.append_rows("tbl", [{"x": 1}])
        self.fabric.append_rows("tbl", [{"x": 2}])
        meta = self.fabric.compact_table("tbl")

        self.assertEqual(meta.total_rows, 2)
        stat = self.fabric.status()
        self.assertEqual(stat["compactions_executed"], 1)
        self.assertGreater(stat["total_bytes_compacted"], 0)

    def test_fabric_status_and_ascii_table(self) -> None:
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 189: OLAP STORAGE CHUNK COMPACTOR & PARQUET ENCODER", tbl)
        self.assertIn("Target Row Group Size", tbl)


if __name__ == "__main__":
    unittest.main()
