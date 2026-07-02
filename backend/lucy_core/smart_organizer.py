"""
smart_organizer.py
Stage 21 = smart organizer.

Minimal local-only organizer for Lucy project information.
Does not take actions.
Does not access apps/files beyond its own structured data file.
Does not schedule, monitor, remind, or act proactively.
Does not use APIs/network.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


STAGE = "21 smart organizer"

VALID_GROUPS = {
    "current_stage",
    "blocked_until_approval",
    "backup_required",
    "manual_checks",
    "future_parking_lot",
    "safety_boundary",
}

VALID_STATUS = {"open", "blocked", "ready", "done"}
VALID_PRIORITY = {"low", "medium", "high"}

NOT_IMPLEMENTED = [
    "safe local actions",
    "external app bridge",
    "proactive awareness",
    "deep recall",
    "judgment",
    "adaptive communication",
    "human-state awareness",
    "time awareness",
    "autonomy boundaries",
    "API/provider work",
]


class SmartOrganizer:
    def __init__(self, lucy_data: Path) -> None:
        self.lucy_data = Path(lucy_data)
        self.file = self.lucy_data / "smart_organizer.json"
        self.lucy_data.mkdir(parents=True, exist_ok=True)

    def status(self) -> dict:
        items = self.list_items()
        return {
            "stage": STAGE,
            "smart_organizer": "active",
            "organizer_items": len(items),
            "takes_actions": False,
            "proactive_monitoring": "not implemented",
            "safe_local_actions": "not implemented",
            "external_app_bridge": "not implemented",
            "deep_recall": "active",
            "autonomy": "not implemented",
            "approval_required_for_action": True,
        }

    def create_organizer_item(self) -> dict:
        title = "Stage 21 smart organizer checks before backup"
        existing = self._find_existing(title)
        if existing:
            return {"ok": True, "reused": True, "item": existing}

        item = {
            "organizer_item_id": f"so_{uuid.uuid4().hex[:12]}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "stage": STAGE,
            "title": title,
            "group": "current_stage",
            "status": "open",
            "priority": "medium",
            "summary": "Keep Stage 21 focused on organizing status only, without actions or autonomy.",
            "next_visible_step": "Run tests, manual checks, clean restart, local backup, and Drive upload before Stage 22.",
            "blocked_until": "Stage 21 accepted, backed up locally, uploaded to Drive, and Senin explicitly approves Stage 22.",
            "safety_notes": [
                "Organizer can list and group information only.",
                "Organizer cannot take local actions.",
                "Organizer cannot monitor proactively.",
                "Organizer cannot access external apps or APIs.",
                "Organizer cannot become deep recall or autonomy.",
            ],
            "approval_required": True,
            "action_allowed": False,
            "proactive_allowed": False,
            "not_implemented": list(NOT_IMPLEMENTED),
        }

        items = self.list_items()
        items.append(item)
        self._write(items)
        return {"ok": True, "reused": False, "item": item}

    def list_items(self) -> list[dict]:
        if not self.file.exists():
            return []
        try:
            data = json.loads(self.file.read_text(encoding="utf-8"))
        except Exception:
            return []
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []

    def _find_existing(self, title: str) -> dict | None:
        for item in self.list_items():
            if item.get("title") == title:
                return item
        return None

    def _write(self, items: list[dict]) -> None:
        self.file.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
