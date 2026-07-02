"""
tool_confirmations.py
Manual confirmation store for Lucy Stage 5 local tools.

Confirmations are explicit and never auto-approved.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from backend.lucy_core.safe_storage import safe_read_json, safe_write_json


CONFIRMATION_VERSION = "0.1.0"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat()


class ToolConfirmationManager:
    def __init__(self, lucy_data_dir: Path, ttl_minutes: int = 120) -> None:
        self.lucy_data_dir = lucy_data_dir
        self.confirmations_file = lucy_data_dir / "tool_confirmations.json"
        self.log_file = lucy_data_dir / "tool_confirmations_log.jsonl"
        self.ttl_minutes = ttl_minutes
        self.lucy_data_dir.mkdir(parents=True, exist_ok=True)
        if not self.confirmations_file.exists():
            safe_write_json(self.confirmations_file, self._default_data())

    def create_confirmation(
        self,
        action: str,
        reason: str,
        risk_level: str,
        target_path: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict:
        data = self._read()
        created_at = _now()
        confirmation = {
            "id": f"tool_{uuid.uuid4().hex[:10]}",
            "action": action,
            "target_path": target_path,
            "reason": reason,
            "risk_level": risk_level,
            "status": "pending",
            "created_at": _iso(created_at),
            "updated_at": _iso(created_at),
            "expires_at": _iso(created_at + timedelta(minutes=self.ttl_minutes)),
            "metadata": self._safe_metadata(metadata or {}),
        }
        data["confirmations"].append(confirmation)
        self._write(data)
        self._log("created", confirmation)
        return {"ok": True, "confirmation": confirmation}

    def list_pending_confirmations(self) -> dict:
        data = self._mark_stale(self._read())
        pending = [item for item in data["confirmations"] if item.get("status") == "pending"]
        return {"ok": True, "confirmations": pending, "file": str(self.confirmations_file)}

    def approve_confirmation(self, confirmation_id: str) -> dict:
        return self._set_status(confirmation_id, "approved")

    def reject_confirmation(self, confirmation_id: str) -> dict:
        return self._set_status(confirmation_id, "rejected")

    def consume_confirmation(self, confirmation_id: str) -> dict:
        data = self._mark_stale(self._read())
        for item in data["confirmations"]:
            if item.get("id") != confirmation_id:
                continue
            status = item.get("status")
            if status != "approved":
                return {
                    "ok": False,
                    "consumed": False,
                    "confirmation": item,
                    "reason": f"Confirmation is {status or 'unknown'}, not approved.",
                }
            item["status"] = "consumed"
            item["updated_at"] = _iso(_now())
            self._write(data)
            self._log("consumed", item)
            return {"ok": True, "consumed": True, "confirmation": item}
        return {"ok": False, "consumed": False, "reason": "Confirmation id was not found."}

    def get_confirmation(self, confirmation_id: str) -> dict | None:
        data = self._mark_stale(self._read())
        for item in data["confirmations"]:
            if item.get("id") == confirmation_id:
                return item
        return None

    def _set_status(self, confirmation_id: str, status: str) -> dict:
        data = self._mark_stale(self._read())
        for item in data["confirmations"]:
            if item.get("id") != confirmation_id:
                continue
            if item.get("status") != "pending":
                return {
                    "ok": False,
                    "confirmation": item,
                    "reason": f"Confirmation is already {item.get('status')}.",
                }
            item["status"] = status
            item["updated_at"] = _iso(_now())
            self._write(data)
            self._log(status, item)
            return {"ok": True, "confirmation": item}
        return {"ok": False, "reason": "Confirmation id was not found."}

    def _default_data(self) -> dict:
        return {"version": CONFIRMATION_VERSION, "confirmations": []}

    def _read(self) -> dict:
        data = safe_read_json(self.confirmations_file, self._default_data())
        data.setdefault("version", CONFIRMATION_VERSION)
        data.setdefault("confirmations", [])
        return data

    def _write(self, data: dict) -> None:
        data["version"] = CONFIRMATION_VERSION
        safe_write_json(self.confirmations_file, data, backup=True)

    def _mark_stale(self, data: dict) -> dict:
        changed = False
        now = _now()
        for item in data.get("confirmations", []):
            if item.get("status") != "pending":
                continue
            expires_at = self._parse_time(item.get("expires_at"))
            if expires_at and expires_at < now:
                item["status"] = "stale"
                item["updated_at"] = _iso(now)
                self._log("stale", item)
                changed = True
        if changed:
            self._write(data)
        return data

    def _parse_time(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def _safe_metadata(self, metadata: dict[str, Any]) -> dict:
        safe = {}
        for key in ["tool_category", "file_size", "extension", "max_results", "max_depth", "max_items"]:
            if key in metadata:
                safe[key] = metadata[key]
        return safe

    def _log(self, event: str, confirmation: dict) -> None:
        record = {
            "timestamp": _iso(_now()),
            "event": event,
            "confirmation_id": confirmation.get("id"),
            "action": confirmation.get("action"),
            "target_path": confirmation.get("target_path"),
            "risk_level": confirmation.get("risk_level"),
            "status": confirmation.get("status"),
            "reason": confirmation.get("reason"),
        }
        try:
            with open(self.log_file, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass
