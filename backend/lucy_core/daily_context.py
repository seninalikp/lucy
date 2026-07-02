"""
daily_context.py
Local daily life context for Lucy.

This is structured context, not surveillance. It records only user-supplied
daily check-ins and keeps them local as JSON.
"""

from __future__ import annotations

import json
import re
import shlex
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


DAILY_CONTEXT_VERSION = "0.1.0"

LIST_FIELDS = {
    "tasks_completed",
    "tasks_avoided",
    "promises_made",
    "people_to_message",
    "important_events",
}

FIELD_ALIASES = {
    "energy": "energy",
    "sleep": "sleep_status",
    "sleep_status": "sleep_status",
    "main": "main_project_today",
    "main_project": "main_project_today",
    "project": "main_project_today",
    "main_project_today": "main_project_today",
    "completed": "tasks_completed",
    "tasks_completed": "tasks_completed",
    "avoided": "tasks_avoided",
    "tasks_avoided": "tasks_avoided",
    "money": "money_pressure",
    "money_pressure": "money_pressure",
    "routine": "routine_status",
    "routine_status": "routine_status",
    "health": "health_gym_status",
    "gym": "health_gym_status",
    "health_gym_status": "health_gym_status",
    "promises": "promises_made",
    "promises_made": "promises_made",
    "people": "people_to_message",
    "people_to_message": "people_to_message",
    "events": "important_events",
    "important_events": "important_events",
    "changed": "what_changed_today",
    "what_changed_today": "what_changed_today",
    "tomorrow": "tomorrow_priority",
    "tomorrow_priority": "tomorrow_priority",
    "lesson": "lesson_learned",
    "lesson_learned": "lesson_learned",
    "notes": "notes",
    "note": "notes",
}

SENSITIVE_TERMS = {
    "api key",
    "password",
    "passphrase",
    "private key",
    "seed phrase",
    "otp",
    "token",
    "secret",
    "credential",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today() -> str:
    return date.today().isoformat()


def _clean_text(text: str, limit: int = 500) -> tuple[str, bool]:
    cleaned = re.sub(r"\s+", " ", str(text)).strip()
    lowered = cleaned.lower()
    if any(term in lowered for term in SENSITIVE_TERMS):
        return "[redacted-sensitive-daily-context]", True

    patterns = [
        r"sk-[A-Za-z0-9]{20,}",
        r"gsk_[A-Za-z0-9_\-]+",
        r"AIza[A-Za-z0-9_\-]+",
        r"or-[A-Za-z0-9_\-]{20,}",
    ]
    redacted = False
    for pattern in patterns:
        updated = re.sub(pattern, "[redacted-token]", cleaned)
        if updated != cleaned:
            redacted = True
        cleaned = updated
    return cleaned[:limit], redacted


def _split_list(value: str) -> list[str]:
    parts = re.split(r"[;,]", value)
    cleaned: list[str] = []
    for part in parts:
        item, _ = _clean_text(part, limit=180)
        if item:
            cleaned.append(item)
    return cleaned


class DailyContextEngine:
    """Structured, local-only daily check-ins."""

    def __init__(self, daily_dir: Path) -> None:
        self.daily_dir = daily_dir
        self.daily_dir.mkdir(parents=True, exist_ok=True)
        self.daily_file = self.daily_dir / "daily_context.json"
        self._ensure_file()

    def _default_data(self) -> dict:
        return {
            "version": DAILY_CONTEXT_VERSION,
            "mode": "local_json_user_supplied_daily_context",
            "created_at": _now(),
            "updated_at": _now(),
            "entries": {},
        }

    def _default_entry(self, day: str, project_context: dict | None = None) -> dict:
        project_context = project_context or {}
        return {
            "date": day,
            "energy": None,
            "sleep_status": "",
            "main_project_today": project_context.get("name", ""),
            "tasks_completed": [],
            "tasks_avoided": [],
            "money_pressure": "",
            "routine_status": "",
            "health_gym_status": "",
            "promises_made": [],
            "people_to_message": [],
            "important_events": [],
            "what_changed_today": "",
            "tomorrow_priority": project_context.get("next_action", ""),
            "lesson_learned": "",
            "notes": "",
            "created_at": _now(),
            "updated_at": _now(),
        }

    def _ensure_file(self) -> None:
        if not self.daily_file.exists():
            self._write(self._default_data())

    def _read(self) -> dict:
        try:
            data = json.loads(self.daily_file.read_text(encoding="utf-8"))
        except Exception:
            data = self._default_data()
        data.setdefault("version", DAILY_CONTEXT_VERSION)
        data.setdefault("mode", "local_json_user_supplied_daily_context")
        data.setdefault("entries", {})
        return data

    def _write(self, data: dict) -> None:
        data["updated_at"] = _now()
        self.daily_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _parse_fields(self, text: str) -> tuple[dict, str, int]:
        if not text.strip():
            return {}, "", 0

        try:
            tokens = shlex.split(text)
        except ValueError:
            tokens = text.split()

        fields: dict = {}
        note_parts: list[str] = []
        redacted_count = 0

        for token in tokens:
            if "=" not in token:
                note_parts.append(token)
                continue
            key, value = token.split("=", 1)
            field = FIELD_ALIASES.get(key.strip().lower())
            if field is None:
                note_parts.append(token)
                continue
            cleaned, redacted = _clean_text(value)
            if redacted:
                redacted_count += 1
            if field in LIST_FIELDS:
                fields[field] = _split_list(cleaned)
            elif field == "energy":
                fields[field] = self._clean_energy(cleaned)
            else:
                fields[field] = cleaned

        notes = " ".join(note_parts).strip()
        if notes:
            notes, redacted = _clean_text(notes, limit=700)
            if redacted:
                redacted_count += 1
        return fields, notes, redacted_count

    def _clean_energy(self, value: str) -> int | str:
        try:
            number = int(value)
        except ValueError:
            return value[:40]
        return max(1, min(number, 10))

    def checkin(self, text: str = "", project_context: dict | None = None, day: str | None = None) -> dict:
        day = day or _today()
        data = self._read()
        entries = data["entries"]
        entry = entries.get(day) or self._default_entry(day, project_context)
        fields, notes, redacted_count = self._parse_fields(text)

        for field, value in fields.items():
            if field in LIST_FIELDS:
                existing = entry.setdefault(field, [])
                for item in value:
                    if item and item not in existing:
                        existing.append(item)
            else:
                entry[field] = value

        if notes:
            if entry.get("notes"):
                entry["notes"] = f"{entry['notes']} {notes}".strip()
            else:
                entry["notes"] = notes

        if not entry.get("main_project_today") and project_context:
            entry["main_project_today"] = project_context.get("name", "")
        if not entry.get("tomorrow_priority") and project_context:
            entry["tomorrow_priority"] = project_context.get("next_action", "")

        entry["updated_at"] = _now()
        entries[day] = entry
        self._write(data)
        return {
            "updated": True,
            "date": day,
            "entry": entry,
            "fields_updated": sorted(fields.keys()) + (["notes"] if notes else []),
            "redacted_count": redacted_count,
            "file": str(self.daily_file),
        }

    def entry_for(self, day: str) -> dict:
        data = self._read()
        entry = data.get("entries", {}).get(day)
        return {
            "found": entry is not None,
            "date": day,
            "entry": entry,
            "file": str(self.daily_file),
        }

    def today(self) -> dict:
        return self.entry_for(_today())

    def yesterday(self) -> dict:
        day = (date.today() - timedelta(days=1)).isoformat()
        return self.entry_for(day)

    def weekly_review(self) -> dict:
        data = self._read()
        entries = data.get("entries", {})
        end = date.today()
        start = end - timedelta(days=6)
        days = [(start + timedelta(days=offset)).isoformat() for offset in range(7)]
        found = [entries[day] for day in days if day in entries]

        completed: list[str] = []
        avoided: list[str] = []
        promises: list[str] = []
        people: list[str] = []
        lessons: list[str] = []
        priorities: list[str] = []

        for entry in found:
            completed.extend(entry.get("tasks_completed", []))
            avoided.extend(entry.get("tasks_avoided", []))
            promises.extend(entry.get("promises_made", []))
            people.extend(entry.get("people_to_message", []))
            if entry.get("lesson_learned"):
                lessons.append(entry["lesson_learned"])
            if entry.get("tomorrow_priority"):
                priorities.append(entry["tomorrow_priority"])

        return {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "days_checked": len(days),
            "days_found": len(found),
            "entries": found,
            "tasks_completed": completed,
            "tasks_avoided": avoided,
            "promises_made": promises,
            "people_to_message": people,
            "lessons_learned": lessons,
            "tomorrow_priorities": priorities[-3:],
            "anti_drift_reminder": (
                "Foundation first: Guardian, memory, projects, logs, tests, then power."
            ),
            "file": str(self.daily_file),
        }

    def brief_context(self) -> dict:
        today = self.today()
        entry = today.get("entry") or {}
        return {
            "date": today["date"],
            "has_today_log": today["found"],
            "energy": entry.get("energy"),
            "sleep_status": entry.get("sleep_status", ""),
            "main_project_today": entry.get("main_project_today", ""),
            "tomorrow_priority": entry.get("tomorrow_priority", ""),
            "notes": entry.get("notes", "")[:240],
        }
