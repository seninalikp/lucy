"""
reflection.py
Session reflection logging for Lucy.

This is persistent self-review and continuity, not consciousness.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReflectionLog:
    def __init__(self, lucy_data_dir: Path) -> None:
        self.path = lucy_data_dir / "reflection_log.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def write(
        self,
        session: dict,
        session_summary: str,
        what_changed: list[str] | None = None,
        what_was_saved: list[str] | None = None,
        what_is_uncertain: list[str] | None = None,
        what_needs_confirmation: list[str] | None = None,
        next_time_start_here: str = "",
        drift_detected: bool = False,
        safety_events: list[str] | None = None,
        memory_updates: list[str] | None = None,
    ) -> dict:
        entry = {
            "session": session,
            "timestamp": _now(),
            "session_summary": session_summary,
            "what_changed": what_changed or [],
            "what_was_saved": what_was_saved or [],
            "what_is_uncertain": what_is_uncertain or [],
            "what_needs_confirmation": what_needs_confirmation or [],
            "next_time_start_here": next_time_start_here,
            "drift_detected": drift_detected,
            "safety_events": safety_events or [],
            "memory_updates": memory_updates or [],
        }
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        entry["file"] = str(self.path)
        return entry

    def latest(self, limit: int = 5) -> list[dict]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        result: list[dict] = []
        for line in lines[-limit:]:
            try:
                result.append(json.loads(line))
            except Exception:
                continue
        return result
