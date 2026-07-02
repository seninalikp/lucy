"""
session_state.py
Explicit boot/shutdown state for Lucy.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from backend.lucy_core.safe_storage import safe_read_json, safe_write_json


SESSION_STATE_VERSION = "0.1.0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _summarize(text: str, limit: int = 300) -> str:
    return " ".join(str(text).split())[:limit]


class SessionStateManager:
    def __init__(self, lucy_data_dir: Path) -> None:
        self.lucy_data_dir = lucy_data_dir
        self.state_file = lucy_data_dir / "session_state.json"
        self.lucy_data_dir.mkdir(parents=True, exist_ok=True)
        if not self.state_file.exists():
            safe_write_json(self.state_file, self._default_state())

    def _default_state(self) -> dict:
        return {
            "version": SESSION_STATE_VERSION,
            "session_count": 0,
            "last_opened": None,
            "last_closed": None,
            "graceful_shutdown": True,
            "crash_recovery_needed": False,
            "active_project": "Lucy",
            "current_checkpoint": "",
            "last_user_intent": "",
            "last_command": "",
            "last_response_summary": "",
            "next_action": "",
            "unsaved_items": [],
            "system_status": "not_booted",
            "last_error": "",
        }

    def _read(self) -> dict:
        data = safe_read_json(self.state_file, self._default_state())
        default = self._default_state()
        for key, value in default.items():
            data.setdefault(key, value)
        data["version"] = SESSION_STATE_VERSION
        return data

    def _write(self, data: dict) -> dict:
        safe_write_json(self.state_file, data, backup=True)
        return data

    def boot_sequence(
        self,
        active_project: str = "Lucy",
        current_checkpoint: str = "",
        next_action: str = "",
        system_status: str = "online",
    ) -> dict:
        data = self._read()
        previous_unclean = not bool(data.get("graceful_shutdown", True))
        data["session_count"] = int(data.get("session_count", 0)) + 1
        data["last_opened"] = _now()
        data["graceful_shutdown"] = False
        data["crash_recovery_needed"] = previous_unclean
        data["active_project"] = active_project or data.get("active_project", "Lucy")
        data["current_checkpoint"] = current_checkpoint or data.get("current_checkpoint", "")
        data["next_action"] = next_action or data.get("next_action", "")
        data["system_status"] = system_status
        return self._write(data)

    def greeting(self) -> str:
        data = self._read()
        if data.get("crash_recovery_needed"):
            return "Lucy is back online. The previous session did not shut down cleanly; review where did we stop."
        return f"Lucy is online. Session {data.get('session_count', 0)} is active."

    def update(self, **changes) -> dict:
        data = self._read()
        allowed = set(self._default_state())
        for key, value in changes.items():
            if key in allowed:
                data[key] = value
        return self._write(data)

    def record_command(self, command: str, response: str = "", user_intent: str = "") -> dict:
        return self.update(
            last_command=_summarize(command, 240),
            last_user_intent=_summarize(user_intent or command, 240),
            last_response_summary=_summarize(response, 420),
            system_status="online",
        )

    def graceful_shutdown(self, summary: str = "") -> dict:
        data = self._read()
        data["last_closed"] = _now()
        data["graceful_shutdown"] = True
        data["crash_recovery_needed"] = False
        data["system_status"] = "closed"
        if summary:
            data["last_response_summary"] = _summarize(summary, 420)
        return self._write(data)

    def status(self) -> dict:
        data = self._read()
        data["file"] = str(self.state_file)
        return data

    def is_crash_recovery(self) -> bool:
        return bool(self._read().get("crash_recovery_needed", False))
