"""
Stage 10 persistent local runtime state.
This is a local JSON status marker, not a daemon, service, or network layer.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from backend.lucy_core.safe_storage import safe_read_json, safe_write_json


RUNTIME_STATE_VERSION = "0.1.0"
RUNTIME_STAGE = "10 persistent local runtime"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PersistentLocalRuntime:
    def __init__(self, lucy_data_dir: Path) -> None:
        self.lucy_data_dir = lucy_data_dir
        self.state_file = lucy_data_dir / "runtime_state.json"
        self.lucy_data_dir.mkdir(parents=True, exist_ok=True)
        if not self.state_file.exists():
            self._write(self._default_state())

    def _default_state(self) -> dict:
        return {
            "version": RUNTIME_STATE_VERSION,
            "stage": RUNTIME_STAGE,
            "active_project": "Lucy",
            "guardian_status": "unknown",
            "started_at": None,
            "last_heartbeat": None,
            "last_command": "",
            "clean_shutdown": True,
            "previous_shutdown_clean": True,
            "recovery_mode": False,
            "shutdown_at": None,
            "runtime_id": "",
        }

    def _read(self) -> dict:
        data = safe_read_json(self.state_file, self._default_state())
        if not isinstance(data, dict):
            data = self._default_state()
        default = self._default_state()
        for key, value in default.items():
            data.setdefault(key, value)
        data["version"] = RUNTIME_STATE_VERSION
        data["stage"] = RUNTIME_STAGE
        return data

    def _write(self, data: dict) -> dict:
        safe_write_json(self.state_file, data, backup=True)
        return data

    def start(self, active_project: str = "Lucy", guardian_status: str = "active") -> dict:
        previous = self._read()
        previous_shutdown_clean = bool(previous.get("clean_shutdown", True))
        timestamp = _now()
        data = self._default_state()
        data.update(
            {
                "active_project": active_project or "Lucy",
                "guardian_status": guardian_status or "active",
                "started_at": timestamp,
                "last_heartbeat": timestamp,
                "last_command": "startup",
                "clean_shutdown": False,
                "previous_shutdown_clean": previous_shutdown_clean,
                "recovery_mode": not previous_shutdown_clean,
                "shutdown_at": previous.get("shutdown_at"),
                "runtime_id": uuid.uuid4().hex,
            }
        )
        return self._write(data)

    def heartbeat(
        self,
        last_command: str = "",
        active_project: str = "Lucy",
        guardian_status: str = "active",
    ) -> dict:
        data = self._read()
        data.update(
            {
                "stage": RUNTIME_STAGE,
                "active_project": active_project or data.get("active_project", "Lucy"),
                "guardian_status": guardian_status or data.get("guardian_status", "active"),
                "last_heartbeat": _now(),
                "last_command": " ".join(str(last_command).split())[:240],
                "clean_shutdown": False,
            }
        )
        if not data.get("started_at"):
            data["started_at"] = data["last_heartbeat"]
        if not data.get("runtime_id"):
            data["runtime_id"] = uuid.uuid4().hex
        return self._write(data)

    def shutdown(self, active_project: str = "Lucy", guardian_status: str = "active") -> dict:
        data = self._read()
        timestamp = _now()
        data.update(
            {
                "stage": RUNTIME_STAGE,
                "active_project": active_project or data.get("active_project", "Lucy"),
                "guardian_status": guardian_status or data.get("guardian_status", "active"),
                "last_heartbeat": timestamp,
                "clean_shutdown": True,
                "recovery_mode": False,
                "shutdown_at": timestamp,
            }
        )
        return self._write(data)

    def status(self) -> dict:
        data = self._read()
        data["file"] = str(self.state_file)
        return data
