r"""
tests/test_stage181_columnar_vector_storage.py
Stage 181 Test Suite: Columnar Vector Storage & Compressed Arrow Layout
Era 19: Distributed Query Planning, Columnar Vector Storage & OLAP Analytics Engine
"""

import unittest

from backend.lucy_core.columnar_vector_storage import (
    ColumnEncoding,
    ColumnField,
    ColumnStatistics,
    ColumnType,
    ColumnVector,
    ColumnarVectorStorageFabric,
    ERA,
    ERA_NAME,
    RecordBatch,
    STAGE,
    STAGE_NAME,
    get_columnar_vector_storage,
)


class TestStage181ColumnarVectorStorage(unittest.TestCase):
    def setUp(self) -> None:
        self.fabric = ColumnarVectorStorageFabric(batch_capacity=32)

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 181)
        self.assertEqual(ERA, 19)
        self.assertEqual(
            STAGE_NAME,
            "Columnar Vector Storage & Compressed Arrow-Style Layout",
        )
        self.assertEqual(
            ERA_NAME,
            "Distributed Query Planning, Columnar Vector Storage & OLAP Analytics Engine",
        )

    def test_02_column_vector_creation_and_null_bitmap(self) -> None:
        field_def = ColumnField("age", ColumnType.INT64, nullable=True)
        col = ColumnVector(field_def)

        col.append(25)
        col.append(None)
        col.append(30)

        self.assertEqual(col.stats.total_count, 3)
        self.assertEqual(col.stats.null_count, 1)
        self.assertEqual(col.validity_bitmap, [True, False, True])
        self.assertEqual(col.get(0), 25)
        self.assertIsNone(col.get(1))
        self.assertEqual(col.get(2), 30)
        self.assertEqual(col.stats.min_value, 25)
        self.assertEqual(col.stats.max_value, 30)

    def test_03_dictionary_encoding_compression(self) -> None:
        field_def = ColumnField("country", ColumnType.STRING, nullable=False)
        col = ColumnVector(field_def)

        # Append repeated low-cardinality values
        for _ in range(20):
            col.append("US")
            col.append("EU")
            col.append("AP")

        col.encode(ColumnEncoding.DICTIONARY)
        self.assertEqual(len(col.dictionary), 3)
        self.assertIn("US", col.dictionary)
        self.assertIn("EU", col.dictionary)
        self.assertIn("AP", col.dictionary)
        self.assertGreater(col.stats.uncompressed_bytes, col.stats.compressed_bytes)
        self.assertGreater(col.stats.compression_ratio, 1.0)

    def test_04_run_length_encoding_compression(self) -> None:
        field_def = ColumnField("status", ColumnType.STRING)
        col = ColumnVector(field_def)

        for _ in range(10):
            col.append("QUEUED")
        for _ in range(15):
            col.append("RUNNING")

        col.encode(ColumnEncoding.RLE)
        self.assertEqual(len(col.rle_runs), 2)
        self.assertEqual(col.rle_runs[0], ("QUEUED", 10))
        self.assertEqual(col.rle_runs[1], ("RUNNING", 15))

    def test_05_delta_encoding_integers(self) -> None:
        field_def = ColumnField("seq_id", ColumnType.INT64)
        col = ColumnVector(field_def)

        for i in range(100, 150):
            col.append(i)

        col.encode(ColumnEncoding.DELTA)
        self.assertEqual(col.field.encoding, ColumnEncoding.DELTA)
        self.assertGreater(col.stats.uncompressed_bytes, 0)
        self.assertGreater(col.stats.compressed_bytes, 0)

    def test_06_record_batch_append_and_projection(self) -> None:
        schema = [
            ColumnField("id", ColumnType.INT64),
            ColumnField("name", ColumnType.STRING),
            ColumnField("score", ColumnType.FLOAT64),
        ]
        batch = RecordBatch(schema)

        batch.append_row({"id": 1, "name": "Alpha", "score": 95.5})
        batch.append_row({"id": 2, "name": "Beta", "score": 88.0})

        self.assertEqual(batch.row_count, 2)
        self.assertEqual(batch.columns["name"].get(0), "Alpha")

        # Projection pushdown: only request 'id' and 'score'
        projected = batch.project(["id", "score"])
        self.assertEqual(len(projected.columns), 2)
        self.assertIn("id", projected.columns)
        self.assertIn("score", projected.columns)
        self.assertNotIn("name", projected.columns)
        self.assertEqual(projected.row_count, 2)

    def test_07_filter_pushdown_selection(self) -> None:
        schema = [ColumnField("val", ColumnType.INT64), ColumnField("tag", ColumnType.STRING)]
        batch = RecordBatch(schema)

        for i in range(10):
            batch.append_row({"val": i, "tag": "even" if i % 2 == 0 else "odd"})

        evens = batch.filter(lambda row: row["tag"] == "even")
        self.assertEqual(len(evens), 5)
        self.assertTrue(all(r["val"] % 2 == 0 for r in evens))

    def test_08_table_chunking_and_auto_encoding(self) -> None:
        schema = [ColumnField("key", ColumnType.STRING), ColumnField("metric", ColumnType.FLOAT64)]
        self.fabric.create_table("analytics_events", schema)

        rows = [{"key": f"event_{i % 5}", "metric": float(i * 10)} for i in range(75)]
        inserted = self.fabric.insert_rows("analytics_events", rows)
        self.assertEqual(inserted, 75)

        batches = self.fabric.tables["analytics_events"]
        # Batch capacity = 32 -> 75 rows spans 3 batches (32, 32, 11)
        self.assertEqual(len(batches), 3)

    def test_09_vectorized_aggregations(self) -> None:
        schema = [ColumnField("sensor", ColumnType.STRING), ColumnField("temp", ColumnType.FLOAT64)]
        self.fabric.create_table("iot_telemetry", schema)

        rows = [
            {"sensor": "s1", "temp": 20.0},
            {"sensor": "s2", "temp": 30.0},
            {"sensor": "s3", "temp": 40.0},
        ]
        self.fabric.insert_rows("iot_telemetry", rows)

        sum_val = self.fabric.query_aggregation("iot_telemetry", "SUM", "temp")
        avg_val = self.fabric.query_aggregation("iot_telemetry", "AVG", "temp")
        min_val = self.fabric.query_aggregation("iot_telemetry", "MIN", "temp")
        max_val = self.fabric.query_aggregation("iot_telemetry", "MAX", "temp")

        self.assertEqual(sum_val, 90.0)
        self.assertEqual(avg_val, 30.0)
        self.assertEqual(min_val, 20.0)
        self.assertEqual(max_val, 40.0)

    def test_10_ascii_formatting_and_singleton(self) -> None:
        st = self.fabric.status()
        self.assertEqual(st["stage"], 181)

        tbl = self.fabric.format_ascii_status()
        self.assertIn("LUCY STAGE 181: COLUMNAR VECTOR STORAGE & COMPRESSED ARROW LAYOUT", tbl)

        f1 = get_columnar_vector_storage()
        f2 = get_columnar_vector_storage()
        self.assertIs(f1, f2)


if __name__ == "__main__":
    unittest.main()
