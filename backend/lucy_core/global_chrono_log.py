r"""
backend/lucy_core/global_chrono_log.py
Stage 197: Autonomous Global Chrono-Log & Event Sourcing Fabric
Era 20: The Sovereign Bicentennial AGI Singularity & Autonomous Kernel Transcendence

100% offline, sovereign global chronological event sourcing engine:
1. Hybrid Logical Clocks (HLC):
   - Combines physical wall-clock timestamps with causal logical counters.
   - Strictly monotonic total ordering: HLC = (physical_ms, logical_counter, node_id).
2. Append-Only Chrono-Log Store:
   - Immutable historical event ledger with SHA256 cryptographic chain checksums.
3. Time-Travel Replay & Point-In-Time Projection:
   - Reconstructs state machine at any historical HLC timestamp or global sequence.
4. Periodic State Snapshotting:
   - Checkpoints materialized state to accelerate replay across arbitrary temporal horizons.
5. Thread-safe execution fabric and CP1252-safe ASCII table formatting.
"""

from __future__ import annotations

import copy
import hashlib
import json
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

STAGE: int = 197
STAGE_NAME: str = "Autonomous Global Chrono-Log & Event Sourcing Fabric"
ERA: int = 20
ERA_NAME: str = "The Sovereign Bicentennial AGI Singularity & Autonomous Kernel Transcendence"

DEFAULT_NODE_ID: str = "chrono_node_0"


@dataclass(order=True)
class HybridTimestamp:
    physical_ms: int
    logical_counter: int
    node_id: str

    def to_string(self) -> str:
        return f"{self.physical_ms}.{self.logical_counter}@{self.node_id}"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ChronoEvent:
    global_seq: int
    hlc: HybridTimestamp
    stream_id: str
    event_type: str
    payload: Dict[str, Any]
    prev_checksum: str
    checksum: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["hlc"] = self.hlc.to_dict()
        return d


@dataclass
class StreamSnapshot:
    stream_id: str
    up_to_seq: int
    up_to_hlc: HybridTimestamp
    state: Dict[str, Any]
    snapshot_hash: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["up_to_hlc"] = self.up_to_hlc.to_dict()
        return d


class GlobalChronoLogFabric:
    """
    Sovereign Global Chrono-Log & Event Sourcing Fabric:
    Provides total causal ordering, immutable event streams,
    time-travel replay, and checkpoint snapshots.
    """

    def __init__(self, node_id: str = DEFAULT_NODE_ID) -> None:
        self.node_id = node_id
        self._lock = threading.RLock()

        # HLC state
        self._last_physical_ms: int = 0
        self._logical_counter: int = 0

        # Event storage
        self.events: List[ChronoEvent] = []
        self.streams: Dict[str, List[int]] = {}  # stream_id -> list of event indices
        self.snapshots: Dict[str, List[StreamSnapshot]] = {}  # stream_id -> snapshots

        self._last_checksum: str = "GENESIS_CHRONO_0000000000000000000000000000000000000000000000000000"
        self._replays_executed: int = 0

    def _get_hlc(self) -> HybridTimestamp:
        """Generates monotonically increasing Hybrid Logical Clock timestamp."""
        now_ms = int(time.time() * 1000)
        if now_ms > self._last_physical_ms:
            self._last_physical_ms = now_ms
            self._logical_counter = 0
        else:
            self._logical_counter += 1

        return HybridTimestamp(
            physical_ms=self._last_physical_ms,
            logical_counter=self._logical_counter,
            node_id=self.node_id,
        )

    def _compute_checksum(self, prev_hash: str, seq: int, hlc_str: str, stream_id: str,
                          event_type: str, payload: Dict[str, Any]) -> str:
        b = json.dumps(
            {
                "prev": prev_hash,
                "seq": seq,
                "hlc": hlc_str,
                "stream": stream_id,
                "type": event_type,
                "payload": payload,
            },
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(b).hexdigest()

    def append_event(self, stream_id: str, event_type: str, payload: Dict[str, Any]) -> ChronoEvent:
        """Appends an immutable event to the total-ordered global chrono-log."""
        with self._lock:
            seq = len(self.events) + 1
            hlc = self._get_hlc()
            csum = self._compute_checksum(
                self._last_checksum, seq, hlc.to_string(), stream_id, event_type, payload
            )

            event = ChronoEvent(
                global_seq=seq,
                hlc=hlc,
                stream_id=stream_id,
                event_type=event_type,
                payload=copy.deepcopy(payload),
                prev_checksum=self._last_checksum,
                checksum=csum,
            )

            self.events.append(event)
            self._last_checksum = csum

            if stream_id not in self.streams:
                self.streams[stream_id] = []
            self.streams[stream_id].append(seq - 1)

            return event

    def create_snapshot(self, stream_id: str) -> StreamSnapshot:
        """Materializes and saves a verified snapshot of the stream state up to current head."""
        with self._lock:
            state = self.time_travel_replay(stream_id)
            indices = self.streams.get(stream_id, [])
            last_ev = self.events[indices[-1]] if indices else None
            up_to_seq = last_ev.global_seq if last_ev else 0
            up_to_hlc = last_ev.hlc if last_ev else HybridTimestamp(0, 0, self.node_id)

            b = json.dumps(state, sort_keys=True).encode("utf-8")
            snap_hash = hashlib.sha256(b).hexdigest()

            snap = StreamSnapshot(
                stream_id=stream_id,
                up_to_seq=up_to_seq,
                up_to_hlc=up_to_hlc,
                state=state,
                snapshot_hash=snap_hash,
            )

            if stream_id not in self.snapshots:
                self.snapshots[stream_id] = []
            self.snapshots[stream_id].append(snap)
            return snap

    def time_travel_replay(
        self,
        stream_id: str,
        target_hlc: Optional[HybridTimestamp] = None,
        target_seq: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Reconstructs the materialized state of a stream up to target_hlc or target_seq.
        If both are None, replays all events up to the latest known event.
        """
        with self._lock:
            self._replays_executed += 1
            indices = self.streams.get(stream_id, [])
            state: Dict[str, Any] = {}

            # Fast forward from latest applicable snapshot
            start_idx = 0
            best_snap: Optional[StreamSnapshot] = None
            if stream_id in self.snapshots:
                for snap in reversed(self.snapshots[stream_id]):
                    if target_seq is not None and snap.up_to_seq > target_seq:
                        continue
                    if target_hlc is not None and snap.up_to_hlc > target_hlc:
                        continue
                    best_snap = snap
                    break

            if best_snap:
                state = copy.deepcopy(best_snap.state)
                # Find event index following best_snap.up_to_seq
                for i, ev_idx in enumerate(indices):
                    if self.events[ev_idx].global_seq > best_snap.up_to_seq:
                        start_idx = i
                        break
                else:
                    start_idx = len(indices)

            # Apply remaining events
            for i in range(start_idx, len(indices)):
                ev = self.events[indices[i]]
                if target_seq is not None and ev.global_seq > target_seq:
                    break
                if target_hlc is not None and ev.hlc > target_hlc:
                    break

                # Apply event payload mutations to state
                if ev.event_type == "SET":
                    for k, v in ev.payload.items():
                        state[k] = v
                elif ev.event_type == "DELETE":
                    for k in ev.payload.get("keys", []):
                        state.pop(k, None)
                elif ev.event_type == "INCREMENT":
                    k = ev.payload.get("key")
                    amount = ev.payload.get("amount", 1)
                    if k:
                        state[k] = state.get(k, 0) + amount
                else:
                    # Generic merge
                    state.update(ev.payload)

            return state

    def verify_ledger_integrity(self) -> Tuple[bool, int]:
        """Cryptographically verifies entire sequential SHA-256 hash chain."""
        with self._lock:
            prev = "GENESIS_CHRONO_0000000000000000000000000000000000000000000000000000"
            for ev in self.events:
                if ev.prev_checksum != prev:
                    return False, ev.global_seq
                expected = self._compute_checksum(
                    prev, ev.global_seq, ev.hlc.to_string(), ev.stream_id, ev.event_type, ev.payload
                )
                if ev.checksum != expected:
                    return False, ev.global_seq
                prev = ev.checksum
            return True, len(self.events)

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "node_id": self.node_id,
                "total_events": len(self.events),
                "active_streams": len(self.streams),
                "snapshots_count": sum(len(snaps) for snaps in self.snapshots.values()),
                "replays_executed": self._replays_executed,
                "head_checksum": self._last_checksum[:16] + "...",
            }

    def format_ascii_status(self) -> str:
        s = self.status()
        header = (
            "+-------------------------------------------------------------------------+\n"
            "|      STAGE 197: AUTONOMOUS GLOBAL CHRONO-LOG & EVENT SOURCING           |\n"
            "+-------------------------------------------------------------------------+\n"
        )
        body = (
            f"| Chrono Node ID        : {s['node_id']:<48} |\n"
            f"| Total Events Logged   : {s['total_events']:<48} |\n"
            f"| Active Event Streams  : {s['active_streams']:<48} |\n"
            f"| Materialized Snaps    : {s['snapshots_count']:<48} |\n"
            f"| Time-Travel Replays   : {s['replays_executed']:<48} |\n"
            f"| Ledger Head Hash      : {s['head_checksum']:<48} |\n"
            "+-------------------------------------------------------------------------+\n"
        )
        return header + body
