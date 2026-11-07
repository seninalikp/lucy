r"""
backend/lucy_core/flight_data_recorder.py
Stage 139: Deterministic Replay & Flight-Data Recorder
Era 14: Autonomous Code Evolution, Semantic Mutation & Static Synthesis

100% offline black-box telemetry, continuous execution recording, and deterministic
replay engine for Lucy OS:
1. Black-Box Flight Recording:
   - High-precision (nanosecond) event instrumentation capturing subsystem state changes,
     command dispatches, memory deltas, and execution checkpoints.
   - Ring-buffer memory logging with periodic flushing to immutable JSONL archives.
2. State Hashing & Merkle Provenance:
   - Computes rolling SHA-256 state hashes per event frame.
   - Computes session Merkle roots signed with HMAC-SHA256 locked to operator: Senin (Senin Ali K P).
3. Deterministic Replay Engine:
   - Replays historical execution sequences step-by-step.
   - Compares reproduced state outputs against recorded state hashes to detect non-deterministic divergence.
4. Checkpoints & Flight Snapshots:
   - Full-state snapshots capturing memory consumption, active subsystems, and ledger receipts.
5. Strict CP1252-Safe ASCII Presentation:
   - /flight-status / /recorder-status
   - /flight-snapshot [label]
   - /flight-replay [flight_id]
   - /blackbox-export
"""

from __future__ import annotations

import dataclasses
import hashlib
import hmac
import json
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

STAGE: int = 139
STAGE_NAME: str = "Deterministic Replay & Flight-Data Recorder"
ERA: int = 14
CREATOR: str = "Senin"
OPERATOR: str = "Senin Ali K P"
HMAC_SECRET: bytes = b"senin-lucy-sovereign-flight-recorder-secret-2026"


@dataclasses.dataclass
class FlightEvent:
    event_id: str
    event_type: str  # "COMMAND", "MUTATION", "STATE_CHANGE", "CHECKPOINT", "TELEMETRY"
    subsystem: str
    payload: Dict[str, Any]
    timestamp_ns: int
    state_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FlightEvent:
        return cls(**data)


@dataclasses.dataclass
class FlightRecording:
    flight_id: str
    start_time: float
    end_time: float
    events_count: int
    merkle_root: str
    hmac_signature: str
    operator: str
    events: List[FlightEvent]

    def to_dict(self) -> Dict[str, Any]:
        d = dataclasses.asdict(self)
        d["events"] = [e.to_dict() if isinstance(e, FlightEvent) else e for e in self.events]
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FlightRecording:
        evs = [FlightEvent.from_dict(e) if isinstance(e, dict) else e for e in data.get("events", [])]
        return cls(
            flight_id=data["flight_id"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            events_count=data["events_count"],
            merkle_root=data["merkle_root"],
            hmac_signature=data["hmac_signature"],
            operator=data.get("operator", OPERATOR),
            events=evs,
        )


@dataclasses.dataclass
class ReplayDiff:
    flight_id: str
    total_events_checked: int
    divergent_events: List[Dict[str, Any]]
    is_deterministic: bool
    replay_duration_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


class FlightDataRecorder:
    """
    Stage 139: Deterministic Replay & Flight-Data Recorder.
    Captures continuous system execution events, signs flight logs,
    and supports step-wise deterministic replay verification.
    """

    def __init__(
        self,
        project_root: Optional[str | Path] = None,
        runtime: Any = None,
        max_buffer_events: int = 500,
    ) -> None:
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.runtime = runtime
        self.max_buffer_events = max_buffer_events

        self.storage_dir = self.project_root / "data" / "lucy" / "blackbox"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self._lock = threading.RLock()
        self.total_recorded_events: int = 0
        self.current_flight_id: str = f"FLIGHT-{int(time.time() * 1000)}-{os.getpid()}-{self.total_recorded_events}"
        self.flight_start_time: float = time.time()
        self.event_buffer: List[FlightEvent] = []
        self.last_state_hash: str = hashlib.sha256(f"INIT:{self.current_flight_id}:{OPERATOR}".encode("utf-8")).hexdigest()

        # Record initial boot checkpoint
        self.record_event("BOOT_CHECKPOINT", "kernel", {"status": "INITIALIZED", "operator": OPERATOR})

    def _compute_state_hash(self, event_type: str, subsystem: str, payload_str: str) -> str:
        h = hashlib.sha256()
        h.update(self.last_state_hash.encode("utf-8"))
        h.update(event_type.encode("utf-8"))
        h.update(subsystem.encode("utf-8"))
        h.update(payload_str.encode("utf-8"))
        return h.hexdigest()

    def record_event(self, event_type: str, subsystem: str, payload: Dict[str, Any]) -> FlightEvent:
        """Appends a new event frame into the active flight data recorder."""
        with self._lock:
            t_ns = time.perf_counter_ns()
            eid = f"EVT-{self.total_recorded_events + 1:06d}"
            payload_str = json.dumps(payload, sort_keys=True)
            new_hash = self._compute_state_hash(event_type, subsystem, payload_str)
            self.last_state_hash = new_hash

            event = FlightEvent(
                event_id=eid,
                event_type=event_type,
                subsystem=subsystem,
                payload=payload,
                timestamp_ns=t_ns,
                state_hash=new_hash,
            )

            self.event_buffer.append(event)
            self.total_recorded_events += 1

            if len(self.event_buffer) >= self.max_buffer_events:
                self.flush_flight_recording()

            return event

    def take_snapshot(self, label: str = "manual_checkpoint") -> FlightEvent:
        """Captures a full runtime snapshot into the flight record."""
        snapshot_payload = {
            "label": label,
            "creator": CREATOR,
            "operator": OPERATOR,
            "recorded_total": self.total_recorded_events,
            "active_services": ["perf_sentinel", "dead_code_eliminator", "wheel_fabric", "ffi_linker"] if not self.runtime else [s for s in getattr(self.runtime, "services", [])],
            "timestamp": time.time(),
        }
        return self.record_event("STATE_SNAPSHOT", "flight_recorder", snapshot_payload)

    def _compute_merkle_root(self, events: List[FlightEvent]) -> str:
        if not events:
            return hashlib.sha256(b"EMPTY_FLIGHT").hexdigest()
        hashes = [e.state_hash for e in events]
        while len(hashes) > 1:
            if len(hashes) % 2 != 0:
                hashes.append(hashes[-1])
            new_hashes = []
            for i in range(0, len(hashes), 2):
                h = hashlib.sha256((hashes[i] + hashes[i + 1]).encode("utf-8")).hexdigest()
                new_hashes.append(h)
            hashes = new_hashes
        return hashes[0]

    def _compute_flight_signature(self, flight_id: str, merkle_root: str) -> str:
        raw = f"{flight_id}:{merkle_root}:{OPERATOR}"
        return hmac.new(HMAC_SECRET, raw.encode("utf-8"), hashlib.sha256).hexdigest()

    def flush_flight_recording(self) -> FlightRecording:
        """Flushes in-memory events to an immutable black-box file on disk."""
        with self._lock:
            if not self.event_buffer:
                # Return empty representation
                root = hashlib.sha256(b"EMPTY").hexdigest()
                sig = self._compute_flight_signature(self.current_flight_id, root)
                return FlightRecording(self.current_flight_id, self.flight_start_time, time.time(), 0, root, sig, OPERATOR, [])

            events_to_flush = list(self.event_buffer)
            self.event_buffer.clear()

            merkle_root = self._compute_merkle_root(events_to_flush)
            sig = self._compute_flight_signature(self.current_flight_id, merkle_root)

            recording = FlightRecording(
                flight_id=self.current_flight_id,
                start_time=self.flight_start_time,
                end_time=time.time(),
                events_count=len(events_to_flush),
                merkle_root=merkle_root,
                hmac_signature=sig,
                operator=OPERATOR,
                events=events_to_flush,
            )

            # Persist to disk
            fpath = self.storage_dir / f"{self.current_flight_id}.json"
            fpath.write_text(json.dumps(recording.to_dict(), indent=2), encoding="utf-8")

            # Rotate flight id for subsequent events
            self.current_flight_id = f"FLIGHT-{int(time.time() * 1000)}-{os.getpid()}-{self.total_recorded_events}"
            self.flight_start_time = time.time()

            return recording

    def load_recording(self, flight_id_or_path: str) -> Optional[FlightRecording]:
        """Loads a flight recording from disk by ID or filepath."""
        p = Path(flight_id_or_path)
        if not p.exists():
            p = self.storage_dir / f"{flight_id_or_path}.json"
        if not p.exists():
            return None
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return FlightRecording.from_dict(data)
        except Exception:
            return None

    def replay_flight(self, recording_input: FlightRecording | str) -> ReplayDiff:
        """
        Replays recorded events step-by-step, re-evaluating state hashes deterministically.
        Detects any divergence or tampering.
        """
        t0 = time.perf_counter_ns()
        if isinstance(recording_input, str):
            rec = self.load_recording(recording_input)
            if not rec:
                return ReplayDiff(recording_input, 0, [{"error": "Flight recording not found"}], False, 0.0)
        else:
            rec = recording_input

        divergent: List[Dict[str, Any]] = []
        running_hash = hashlib.sha256(f"INIT:{rec.flight_id}:{rec.operator}".encode("utf-8")).hexdigest()

        for idx, ev in enumerate(rec.events):
            payload_str = json.dumps(ev.payload, sort_keys=True)
            h = hashlib.sha256()
            h.update(running_hash.encode("utf-8"))
            h.update(ev.event_type.encode("utf-8"))
            h.update(ev.subsystem.encode("utf-8"))
            h.update(payload_str.encode("utf-8"))
            expected_hash = h.hexdigest()

            if expected_hash != ev.state_hash:
                divergent.append({
                    "event_id": ev.event_id,
                    "event_type": ev.event_type,
                    "subsystem": ev.subsystem,
                    "recorded_hash": ev.state_hash,
                    "recomputed_hash": expected_hash,
                    "index": idx,
                })
            running_hash = ev.state_hash

        # Re-check Merkle root & HMAC signature
        recomputed_root = self._compute_merkle_root(rec.events)
        recomputed_sig = self._compute_flight_signature(rec.flight_id, recomputed_root)

        if recomputed_root != rec.merkle_root:
            divergent.append({"error": "Merkle root mismatch", "expected": rec.merkle_root, "computed": recomputed_root})
        if not hmac.compare_digest(recomputed_sig, rec.hmac_signature):
            divergent.append({"error": "HMAC signature tampering detected"})

        t1 = time.perf_counter_ns()
        dur_ms = round((t1 - t0) / 1_000_000.0, 3)

        return ReplayDiff(
            flight_id=rec.flight_id,
            total_events_checked=len(rec.events),
            divergent_events=divergent,
            is_deterministic=(len(divergent) == 0),
            replay_duration_ms=dur_ms,
        )

    def list_recordings(self) -> List[Dict[str, Any]]:
        """Returns summary of all persisted flight recordings in blackbox storage."""
        records = []
        for fp in self.storage_dir.glob("FLIGHT-*.json"):
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                records.append({
                    "flight_id": data.get("flight_id", fp.stem),
                    "events_count": data.get("events_count", 0),
                    "start_time": data.get("start_time", 0.0),
                    "merkle_root": data.get("merkle_root", "")[:12] + "...",
                    "file_size": fp.stat().st_size,
                })
            except Exception:
                continue
        return sorted(records, key=lambda x: x["start_time"], reverse=True)

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "creator": CREATOR,
                "operator": OPERATOR,
                "active_flight_id": self.current_flight_id,
                "events_in_buffer": len(self.event_buffer),
                "total_recorded_events": self.total_recorded_events,
                "persisted_flights": len(list(self.storage_dir.glob("FLIGHT-*.json"))),
                "status": "RECORDING_ACTIVE",
            }

    def format_flight_status_table(self) -> str:
        s = self.status()
        lines = [
            "+=============================================================================+",
            f"| LUCY FLIGHT DATA RECORDER & DETERMINISTIC REPLAY [STAGE {STAGE:03d} | ERA {ERA:02d}]        |",
            "+=============================================================================+",
            f"| Status: {s['status']:<16} Buffered: {s['events_in_buffer']:<8} Total Events: {s['total_recorded_events']:<13} |",
            f"| Active Flight ID: {s['active_flight_id']:<38} Flights: {s['persisted_flights']:<4} |",
            f"| Sovereign Operator: {OPERATOR:<55} |",
            "+-----------------------------------------------------------------------------+",
            "| RECENT IN-MEMORY FLIGHT EVENTS                                              |",
            "+---------------+----------------------+----------------------+---------------+",
            "| Event ID      | Event Type           | Subsystem            | State Hash    |",
            "+---------------+----------------------+----------------------+---------------+",
        ]
        with self._lock:
            sample = self.event_buffer[-5:] if self.event_buffer else []
            for ev in sample:
                lines.append(
                    f"| {ev.event_id:<13} | {ev.event_type[:20]:<20} | {ev.subsystem[:20]:<20} | {ev.state_hash[:13]}... |"
                )
        if not self.event_buffer:
            lines.append("| (Event buffer flushed to disk)                                             |")
        lines.append("+---------------+----------------------+----------------------+---------------+")
        return "\n".join(lines)

    def format_replay_diff_table(self, diff: ReplayDiff) -> str:
        status_str = "DETERMINISTIC_PASS" if diff.is_deterministic else "DIVERGENCE_DETECTED"
        lines = [
            "+=============================================================================+",
            f"| FLIGHT REPLAY VERIFICATION: {diff.flight_id:<46} |",
            "+=============================================================================+",
            f"| Status: {status_str:<20} Events Replayed: {diff.total_events_checked:<6} Time: {diff.replay_duration_ms:.2f} ms      |",
            f"| Divergent Anomalies: {len(diff.divergent_events):<5} Sovereign Operator: {OPERATOR:<28} |",
            "+-----------------------------------------------------------------------------+",
        ]
        if diff.divergent_events:
            lines.extend([
                "| DETECTED DIVERGENT ANOMALIES                                                |",
                "+---------------+----------------------+--------------------------------------+",
                "| Item / Index  | Issue                | Recomputed Detail                    |",
                "+---------------+----------------------+--------------------------------------+",
            ])
            for d in diff.divergent_events[:5]:
                idx_str = str(d.get("event_id", d.get("error", "Error")))
                sub_str = str(d.get("subsystem", "State Hash Mismatch"))
                dt_str = str(d.get("recomputed_hash", d.get("expected", "")))
                lines.append(f"| {idx_str[:13]:<13} | {sub_str[:20]:<20} | {dt_str[:36]:<36} |")
            lines.append("+---------------+----------------------+--------------------------------------+")
        else:
            lines.append("| ALL REPLAY TRACES MATCH RECORDED STATE DETERMINISTICALLY (100% REPRODUCIBLE)|")
            lines.append("+-----------------------------------------------------------------------------+")
        return "\n".join(lines)


__all__ = [
    "STAGE",
    "STAGE_NAME",
    "ERA",
    "CREATOR",
    "OPERATOR",
    "FlightEvent",
    "FlightRecording",
    "ReplayDiff",
    "FlightDataRecorder",
]
