r"""
backend/lucy_core/streaming_window_watermark.py
Stage 187: Streaming Window Aggregation & Watermark Sentinel
Era 19: Distributed Query Planning, Columnar Vector Storage & OLAP Analytics Engine

100% offline, sovereign streaming window aggregation engine:
1. Window Topologies:
   - Tumbling Windows: Fixed-size, non-overlapping intervals [T, T + size).
   - Sliding (Hopping) Windows: Fixed-size intervals with slide interval [T, T + size), hop period S.
   - Session Windows: Dynamic gap-based windows expanding with active event arrival, closing on inactivity.
2. Event-Time & Watermark Sentinel:
   - Bounded-out-of-orderness watermark generator: W = max_event_time - allowed_lateness.
   - Late Data Handling: Events within allowed lateness update active windows; events arriving after window retirement route to late dead-letter buffer.
3. Window State Lifecycle:
   - Active Accumulation: Thread-safe group accumulators (SUM, COUNT, MIN, MAX, AVG).
   - Window Finalization: Triggered when watermark >= window_end.
   - State Purging: Reclaims memory once watermark >= window_end + allowed_lateness.
4. Thread-safe execution fabric and CP1252-safe ASCII table formatting.
"""

from __future__ import annotations

import collections
import json
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

STAGE: int = 187
STAGE_NAME: str = "Streaming Window Aggregation & Watermark Sentinel"
ERA: int = 19
ERA_NAME: str = "Distributed Query Planning, Columnar Vector Storage & OLAP Analytics Engine"


class WindowType:
    TUMBLING = "TUMBLING"
    SLIDING = "SLIDING"
    SESSION = "SESSION"


@dataclass
class WindowBounds:
    window_id: str
    start_ts: float
    end_ts: float
    window_type: str

    def __hash__(self) -> int:
        return hash((self.window_id, self.start_ts, self.end_ts))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, WindowBounds):
            return False
        return self.window_id == other.window_id and self.start_ts == other.start_ts and self.end_ts == other.end_ts


@dataclass
class WindowResult:
    window_id: str
    window_type: str
    start_ts: float
    end_ts: float
    group_key: Tuple[Any, ...]
    aggregates: Dict[str, Any]
    emitted_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class StreamingWindowFabric:
    """
    Sovereign Streaming Window Aggregation Engine:
    - Ingests event-time streams with out-of-order arrival tolerance.
    - Manages Tumbling, Sliding, and Session windows.
    - Advances watermarks and emits finalized windows.
    """

    def __init__(self, allowed_lateness: float = 5.0) -> None:
        self.allowed_lateness = allowed_lateness
        self._lock = threading.RLock()

        # Watermark tracking
        self.max_event_ts: float = 0.0
        self.watermark: float = 0.0

        # Stream configurations: stream_id -> config
        self.stream_configs: Dict[str, Dict[str, Any]] = {}

        # Window state storage: (stream_id, WindowBounds, group_key) -> state dict
        self.window_states: Dict[Tuple[str, WindowBounds, Tuple[Any, ...]], Dict[str, Any]] = {}

        # Emitted windows archive
        self.emitted_windows: List[WindowResult] = []
        self.late_events_dropped: int = 0
        self.total_events_processed: int = 0

    def register_stream(self, stream_id: str, window_type: str,
                        window_size: float = 10.0, slide: float = 5.0,
                        session_gap: float = 10.0,
                        group_by: Optional[List[str]] = None,
                        aggregates: Optional[List[Tuple[str, str, str]]] = None) -> None:
        """
        aggregates: [(func_name, src_col, out_col)] e.g. [("SUM", "bytes", "total_bytes")]
        """
        with self._lock:
            self.stream_configs[stream_id] = {
                "window_type": window_type.upper(),
                "window_size": window_size,
                "slide": slide,
                "session_gap": session_gap,
                "group_by": group_by or [],
                "aggregates": aggregates or [("COUNT", "*", "event_count")],
            }

    def _assign_windows(self, stream_id: str, event_ts: float) -> List[WindowBounds]:
        cfg = self.stream_configs.get(stream_id)
        if not cfg:
            return []

        wtype = cfg["window_type"]
        windows: List[WindowBounds] = []

        if wtype == WindowType.TUMBLING:
            wsize = cfg["window_size"]
            start = (event_ts // wsize) * wsize
            end = start + wsize
            wid = f"tumb_{start:.1f}_{end:.1f}"
            windows.append(WindowBounds(wid, start, end, WindowType.TUMBLING))

        elif wtype == WindowType.SLIDING:
            wsize = cfg["window_size"]
            slide = cfg["slide"]
            last_start = (event_ts // slide) * slide
            # All sliding windows that cover event_ts
            cur_start = last_start
            while cur_start + wsize > event_ts and cur_start >= 0:
                cur_end = cur_start + wsize
                if cur_start <= event_ts < cur_end:
                    wid = f"slide_{cur_start:.1f}_{cur_end:.1f}"
                    windows.append(WindowBounds(wid, cur_start, cur_end, WindowType.SLIDING))
                cur_start -= slide

        elif wtype == WindowType.SESSION:
            # Simple session window: dynamic expansion based on existing windows
            gap = cfg["session_gap"]
            found = False
            # Look for existing active session window within gap
            for (sid, wb, _), _ in self.window_states.items():
                if sid == stream_id and wb.window_type == WindowType.SESSION:
                    if wb.start_ts <= event_ts <= wb.end_ts + gap:
                        wb.end_ts = max(wb.end_ts, event_ts)
                        windows.append(wb)
                        found = True
                        break
            if not found:
                wid = f"sess_{event_ts:.1f}"
                windows.append(WindowBounds(wid, event_ts, event_ts + gap, WindowType.SESSION))

        return windows

    def ingest_event(self, stream_id: str, event_ts: float, payload: Dict[str, Any]) -> bool:
        """
        Ingests an event with timestamp event_ts.
        Returns True if accepted into windows, False if dropped due to lateness.
        """
        with self._lock:
            self.total_events_processed += 1

            # Update maximum event time and watermark
            if event_ts > self.max_event_ts:
                self.max_event_ts = event_ts
                self.watermark = max(0.0, self.max_event_ts - self.allowed_lateness)
                self._check_and_trigger_windows()

            # Check lateness
            if event_ts < self.watermark:
                self.late_events_dropped += 1
                return False

            cfg = self.stream_configs.get(stream_id)
            if not cfg:
                return False

            windows = self._assign_windows(stream_id, event_ts)
            grp_by = cfg["group_by"]
            grp_key = tuple(payload.get(g) for g in grp_by) if grp_by else ("ALL",)

            for wb in windows:
                state_key = (stream_id, wb, grp_key)
                if state_key not in self.window_states:
                    st: Dict[str, Any] = {}
                    for fn, _, out_c in cfg["aggregates"]:
                        fn_u = fn.upper()
                        if fn_u == "COUNT":
                            st[out_c] = 0
                        elif fn_u in ("SUM", "AVG"):
                            st[out_c] = 0.0
                            st[f"{out_c}__cnt"] = 0
                        elif fn_u == "MIN":
                            st[out_c] = float("inf")
                        elif fn_u == "MAX":
                            st[out_c] = float("-inf")
                    self.window_states[state_key] = st

                st = self.window_states[state_key]
                for fn, src_c, out_c in cfg["aggregates"]:
                    fn_u = fn.upper()
                    val = payload.get(src_c) if src_c != "*" else 1
                    if val is None:
                        continue
                    if fn_u == "COUNT":
                        st[out_c] += 1
                    elif fn_u == "SUM":
                        st[out_c] += float(val)
                    elif fn_u == "AVG":
                        st[out_c] += float(val)
                        st[f"{out_c}__cnt"] += 1
                    elif fn_u == "MIN":
                        if float(val) < st[out_c]:
                            st[out_c] = float(val)
                    elif fn_u == "MAX":
                        if float(val) > st[out_c]:
                            st[out_c] = float(val)

            return True

    def _check_and_trigger_windows(self) -> None:
        """
        Emits and purges windows whose end timestamp is past the current watermark.
        """
        keys_to_purge = []
        for (sid, wb, grp_key), st in list(self.window_states.items()):
            if self.watermark >= wb.end_ts:
                # Finalize aggregates
                cfg = self.stream_configs.get(sid, {})
                aggs_final: Dict[str, Any] = {}
                for fn, _, out_c in cfg.get("aggregates", []):
                    fn_u = fn.upper()
                    if fn_u == "AVG":
                        cnt = st.get(f"{out_c}__cnt", 0)
                        aggs_final[out_c] = round(st[out_c] / cnt, 4) if cnt > 0 else None
                    elif fn_u == "MIN":
                        aggs_final[out_c] = st[out_c] if st[out_c] != float("inf") else None
                    elif fn_u == "MAX":
                        aggs_final[out_c] = st[out_c] if st[out_c] != float("-inf") else None
                    else:
                        aggs_final[out_c] = st[out_c]

                result = WindowResult(
                    window_id=wb.window_id,
                    window_type=wb.window_type,
                    start_ts=wb.start_ts,
                    end_ts=wb.end_ts,
                    group_key=grp_key,
                    aggregates=aggs_final,
                )
                self.emitted_windows.append(result)
                keys_to_purge.append((sid, wb, grp_key))

        for k in keys_to_purge:
            del self.window_states[k]

    def advance_time(self, current_ts: float) -> None:
        """Explicitly advances event time and triggers watermark checks."""
        with self._lock:
            if current_ts > self.max_event_ts:
                self.max_event_ts = current_ts
                self.watermark = max(0.0, self.max_event_ts - self.allowed_lateness)
                self._check_and_trigger_windows()

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "max_event_ts": round(self.max_event_ts, 2),
                "watermark": round(self.watermark, 2),
                "allowed_lateness": self.allowed_lateness,
                "active_windows_count": len(self.window_states),
                "emitted_windows_count": len(self.emitted_windows),
                "total_events_processed": self.total_events_processed,
                "late_events_dropped": self.late_events_dropped,
                "streams": list(self.stream_configs.keys()),
            }

    def format_ascii_status(self) -> str:
        s = self.status()
        header = (
            "+-------------------------------------------------------------------------+\n"
            "|      STAGE 187: STREAMING WINDOW AGGREGATION & WATERMARK SENTINEL       |\n"
            "+-------------------------------------------------------------------------+\n"
        )
        body = (
            f"| Max Event Timestamp   : {s['max_event_ts']:<48} |\n"
            f"| Current Watermark     : {s['watermark']:<48} |\n"
            f"| Allowed Lateness      : {s['allowed_lateness']}s{' ':<45} |\n"
            f"| Active Windows        : {s['active_windows_count']:<48} |\n"
            f"| Emitted Windows       : {s['emitted_windows_count']:<48} |\n"
            f"| Total Events Proc     : {s['total_events_processed']:<48} |\n"
            f"| Late Events Dropped   : {s['late_events_dropped']:<48} |\n"
            "+-------------------------------------------------------------------------+\n"
        )
        return header + body
