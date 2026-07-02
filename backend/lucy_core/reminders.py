"""
reminders.py
Small local reminder list for Lucy.

This is not a background scheduler. It stores reminders and shows due items
when Lucy is asked for a daily brief or reminder list.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


REMINDERS_VERSION = "0.1.0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_due(raw_due: str | None) -> str | None:
    if raw_due is None:
        return None
    cleaned = raw_due.strip()
    if not cleaned:
        return None
    try:
        return datetime.fromisoformat(cleaned.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return cleaned


class ReminderStore:
    def __init__(self, lucy_data_dir: Path) -> None:
        self.reminders_file = lucy_data_dir / "reminders.json"
        lucy_data_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_file()

    def _default_data(self) -> dict:
        return {
            "version": REMINDERS_VERSION,
            "created_at": _now(),
            "updated_at": _now(),
            "reminders": [],
        }

    def _ensure_file(self) -> None:
        if not self.reminders_file.exists():
            self._write(self._default_data())

    def _read(self) -> dict:
        try:
            data = json.loads(self.reminders_file.read_text(encoding="utf-8"))
        except Exception:
            data = self._default_data()
        data.setdefault("version", REMINDERS_VERSION)
        data.setdefault("reminders", [])
        return data

    def _write(self, data: dict) -> None:
        data["updated_at"] = _now()
        self.reminders_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _next_id(self, reminders: list[dict]) -> str:
        highest = 0
        for reminder in reminders:
            raw_id = str(reminder.get("id", ""))
            if raw_id.startswith("rem_"):
                try:
                    highest = max(highest, int(raw_id.split("_", 1)[1]))
                except ValueError:
                    continue
        return f"rem_{highest + 1:04d}"

    def add(self, text: str, due: str | None = None) -> dict:
        cleaned = text.strip()
        if not cleaned:
            return {"added": False, "reason": "Reminder text was empty."}
        data = self._read()
        reminder = {
            "id": self._next_id(data["reminders"]),
            "text": cleaned,
            "status": "open",
            "due": _parse_due(due),
            "created_at": _now(),
            "completed_at": None,
        }
        data["reminders"].append(reminder)
        self._write(data)
        return {"added": True, "reminder": reminder}

    def list_open(self) -> list[dict]:
        return [item for item in self._read()["reminders"] if item.get("status") == "open"]

    def complete(self, selector: str) -> dict:
        cleaned = selector.strip()
        if not cleaned:
            return {"completed": False, "reason": "Reminder ID or number was empty."}

        data = self._read()
        open_items = [item for item in data["reminders"] if item.get("status") == "open"]
        selected: dict | None = None
        if cleaned.isdigit():
            index = int(cleaned) - 1
            if 0 <= index < len(open_items):
                selected = open_items[index]
        else:
            for item in open_items:
                if str(item.get("id", "")).startswith(cleaned) or cleaned.lower() in item.get("text", "").lower():
                    selected = item
                    break

        if selected is None:
            return {"completed": False, "reason": "No matching open reminder found."}

        selected["status"] = "done"
        selected["completed_at"] = _now()
        self._write(data)
        return {"completed": True, "reminder": selected}

    def due_items(self) -> list[dict]:
        now = datetime.now(timezone.utc)
        due: list[dict] = []
        for item in self.list_open():
            raw_due = item.get("due")
            if not raw_due:
                continue
            try:
                due_at = datetime.fromisoformat(str(raw_due).replace("Z", "+00:00"))
            except ValueError:
                continue
            if due_at <= now:
                due.append(item)
        return due
