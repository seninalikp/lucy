r"""
tests/test_stage187_streaming_window_watermark.py
Unit tests for Stage 187: Streaming Window Aggregation & Watermark Sentinel
Era 19: Distributed Query Planning, Columnar Vector Storage & OLAP Analytics Engine
"""

from __future__ import annotations

import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

import unittest
from backend.lucy_core.streaming_window_watermark import (
    StreamingWindowFabric,
    WindowType,
)


class TestStreamingWindowWatermark(unittest.TestCase):
    def setUp(self) -> None:
        self.fabric = StreamingWindowFabric(allowed_lateness=5.0)

    def test_tumbling_window_assignment(self) -> None:
        self.fabric.register_stream("tumb_stream", WindowType.TUMBLING, window_size=10.0)
        wins1 = self.fabric._assign_windows("tumb_stream", 3.0)
        self.assertEqual(len(wins1), 1)
        self.assertEqual(wins1[0].start_ts, 0.0)
        self.assertEqual(wins1[0].end_ts, 10.0)

        wins2 = self.fabric._assign_windows("tumb_stream", 15.0)
        self.assertEqual(len(wins2), 1)
        self.assertEqual(wins2[0].start_ts, 10.0)
        self.assertEqual(wins2[0].end_ts, 20.0)

    def test_sliding_window_assignment(self) -> None:
        # 10s window sliding every 5s
        self.fabric.register_stream("slide_stream", WindowType.SLIDING, window_size=10.0, slide=5.0)
        wins = self.fabric._assign_windows("slide_stream", 7.0)
        # Should fall into [0, 10) and [5, 15)
        self.assertEqual(len(wins), 2)
        starts = {w.start_ts for w in wins}
        self.assertEqual(starts, {0.0, 5.0})

    def test_session_window_expansion(self) -> None:
        self.fabric.register_stream("sess_stream", WindowType.SESSION, session_gap=10.0)
        self.fabric.ingest_event("sess_stream", 10.0, {"val": 1})
        self.fabric.ingest_event("sess_stream", 15.0, {"val": 2})

        # Session should expand to include 15.0
        active_sess = [wb for (sid, wb, _), _ in self.fabric.window_states.items() if sid == "sess_stream"]
        self.assertEqual(len(active_sess), 1)
        self.assertGreaterEqual(active_sess[0].end_ts, 15.0)

    def test_watermark_advancement(self) -> None:
        self.fabric.register_stream("s1", WindowType.TUMBLING, window_size=10.0)
        self.fabric.ingest_event("s1", 20.0, {"val": 1})
        self.assertEqual(self.fabric.max_event_ts, 20.0)
        self.assertEqual(self.fabric.watermark, 15.0)  # 20 - 5.0 lateness

    def test_late_event_rejection_after_watermark(self) -> None:
        self.fabric.register_stream("s1", WindowType.TUMBLING, window_size=10.0)
        # Event at 30.0 sets watermark to 25.0
        self.fabric.ingest_event("s1", 30.0, {"val": 1})
        self.assertEqual(self.fabric.watermark, 25.0)

        # Event at 20.0 is late (20.0 < 25.0 watermark)
        accepted = self.fabric.ingest_event("s1", 20.0, {"val": 2})
        self.assertFalse(accepted)
        self.assertEqual(self.fabric.late_events_dropped, 1)

    def test_window_emission_on_watermark_advance(self) -> None:
        self.fabric.register_stream("s1", WindowType.TUMBLING, window_size=10.0)
        # Ingest events in window [0, 10)
        self.fabric.ingest_event("s1", 2.0, {"val": 10})
        self.fabric.ingest_event("s1", 5.0, {"val": 20})
        self.assertEqual(len(self.fabric.emitted_windows), 0)

        # Advance event time to 16.0 -> watermark = 11.0 >= 10.0 (window end)
        self.fabric.advance_time(16.0)
        self.assertEqual(len(self.fabric.emitted_windows), 1)
        res = self.fabric.emitted_windows[0]
        self.assertEqual(res.start_ts, 0.0)
        self.assertEqual(res.end_ts, 10.0)
        self.assertEqual(res.aggregates["event_count"], 2)

    def test_window_aggregations_sum_count_avg(self) -> None:
        self.fabric.register_stream(
            "metrics", WindowType.TUMBLING, window_size=10.0,
            aggregates=[("SUM", "bytes", "total_bytes"), ("COUNT", "bytes", "cnt"), ("AVG", "bytes", "avg_bytes")],
        )
        self.fabric.ingest_event("metrics", 1.0, {"bytes": 100})
        self.fabric.ingest_event("metrics", 3.0, {"bytes": 300})
        self.fabric.advance_time(16.0)

        self.assertEqual(len(self.fabric.emitted_windows), 1)
        aggs = self.fabric.emitted_windows[0].aggregates
        self.assertEqual(aggs["total_bytes"], 400.0)
        self.assertEqual(aggs["cnt"], 2)
        self.assertEqual(aggs["avg_bytes"], 200.0)

    def test_window_aggregations_min_max(self) -> None:
        self.fabric.register_stream(
            "temp_sensor", WindowType.TUMBLING, window_size=10.0,
            aggregates=[("MIN", "temp", "min_temp"), ("MAX", "temp", "max_temp")],
        )
        self.fabric.ingest_event("temp_sensor", 2.0, {"temp": 22.5})
        self.fabric.ingest_event("temp_sensor", 4.0, {"temp": 18.0})
        self.fabric.ingest_event("temp_sensor", 8.0, {"temp": 29.0})
        self.fabric.advance_time(16.0)

        aggs = self.fabric.emitted_windows[0].aggregates
        self.assertEqual(aggs["min_temp"], 18.0)
        self.assertEqual(aggs["max_temp"], 29.0)

    def test_grouped_window_aggregations(self) -> None:
        self.fabric.register_stream(
            "click_stream", WindowType.TUMBLING, window_size=10.0,
            group_by=["page"],
            aggregates=[("COUNT", "*", "clicks")],
        )
        self.fabric.ingest_event("click_stream", 1.0, {"page": "home"})
        self.fabric.ingest_event("click_stream", 2.0, {"page": "home"})
        self.fabric.ingest_event("click_stream", 3.0, {"page": "cart"})
        self.fabric.advance_time(16.0)

        self.assertEqual(len(self.fabric.emitted_windows), 2)
        by_grp = {w.group_key[0]: w.aggregates["clicks"] for w in self.fabric.emitted_windows}
        self.assertEqual(by_grp["home"], 2)
        self.assertEqual(by_grp["cart"], 1)

    def test_fabric_status_and_ascii_table(self) -> None:
        self.fabric.register_stream("iot", WindowType.TUMBLING)
        self.fabric.ingest_event("iot", 5.0, {})
        stat = self.fabric.status()
        self.assertEqual(stat["total_events_processed"], 1)

        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 187: STREAMING WINDOW AGGREGATION & WATERMARK SENTINEL", tbl)
        self.assertIn("Current Watermark", tbl)


if __name__ == "__main__":
    unittest.main()
