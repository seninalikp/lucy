"""
proactive_awareness.py
Stage 24 = proactive awareness.

This stage prepares a safe awareness scan layer only.
It does not monitor in the background.
It does not send notifications.
It does not trigger reminders automatically.
It does not open apps.
It does not use network/API/provider keys.
It does not take actions without Senin asking.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


STAGE = "24 proactive awareness"

VALID_AWARENESS_TYPES = {
    "manual_state_scan",
    "session_start_awareness_plan",
    "dry_run_awareness_check",
}

VALID_STATUS = {"observed", "blocked", "dry_run_ready", "done"}

NOT_IMPLEMENTED = [
    "background monitoring",
    "automatic notifications",
    "automatic reminder firing",
    "scheduled autonomous checks",
    "app opening",
    "browser automation",
    "phone control",
    "external app bridge execution",
    "network access",
    "API/provider keys",
    "deep recall",
    "judgment",
    "adaptive communication",
    "human-state awareness",
    "time awareness",
    "autonomy boundaries",
]


class ProactiveAwareness:
    def __init__(self, lucy_data: Path) -> None:
        self.lucy_data = Path(lucy_data)
        self.file = self.lucy_data / "proactive_awareness.json"
        self.lucy_data.mkdir(parents=True, exist_ok=True)

    def status(self) -> dict:
        scans = self.list_awareness_scans()
        return {
            "stage": STAGE,
            "proactive_awareness": "active",
            "awareness_scans": len(scans),
            "execution_mode": "manual_dry_run_only",
            "background_monitoring": "blocked",
            "automatic_notifications": "blocked",
            "automatic_reminder_firing": "blocked",
            "scheduled_autonomous_checks": "blocked",
            "real_actions": False,
            "approval_required": True,
            "external_app_bridge_execution": "blocked",
            "network_access": "blocked",
            "api_provider_keys": "blocked",
            "autonomy": "not implemented",
        }

    def create_awareness_scan(self) -> dict:
        title = "Stage 24 manual proactive awareness dry-run scan"
        existing = self._find_existing(title)
        if existing:
            return {"ok": True, "reused": True, "scan": existing}

        scan = {
            "awareness_scan_id": f"pa_{uuid.uuid4().hex[:12]}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "stage": STAGE,
            "title": title,
            "awareness_type": "manual_state_scan",
            "status": "observed",
            "summary": "Prepare a manual-only awareness scan that notices safe local project state without acting.",
            "observations": [
                "Stage 23 external app bridge is accepted and backed up.",
                "Stage 24 is active only after Senin starts it.",
                "Lucy may report safe local awareness status when asked.",
                "Lucy must not monitor in the background.",
                "Lucy must not trigger reminders, notifications, apps, or external bridges.",
            ],
            "dry_run_plan": [
                "Confirm proactive awareness status.",
                "Create one awareness scan.",
                "Show awareness scans.",
                "Dry-run awareness check.",
                "Confirm no background monitoring exists.",
                "Confirm no automatic notifications exist.",
                "Confirm no autonomous reminders/actions exist.",
                "Run tests.",
                "Run manual checks.",
                "Clean restart.",
                "Back up locally and upload to Drive after acceptance.",
            ],
            "requires_approval": True,
            "dry_run_only": True,
            "background_monitoring_allowed": False,
            "automatic_notifications_allowed": False,
            "automatic_reminder_firing_allowed": False,
            "scheduled_autonomous_checks_allowed": False,
            "real_action_allowed": False,
            "external_bridge_execution_allowed": False,
            "network_allowed": False,
            "api_keys_allowed": False,
            "blocked_until": "Stage 24 accepted, backed up locally, uploaded to Drive, and Senin explicitly approves Stage 25.",
            "not_implemented": list(NOT_IMPLEMENTED),
        }

        scans = self.list_awareness_scans()
        scans.append(scan)
        self._write(scans)
        return {"ok": True, "reused": False, "scan": scan}

    def dry_run_awareness_check(self) -> dict:
        scan = self.create_awareness_scan()["scan"]
        return {
            "ok": True,
            "stage": STAGE,
            "dry_run_only": True,
            "would_monitor_background": False,
            "would_notify": False,
            "would_take_action": False,
            "real_action_allowed": False,
            "message": "Dry run complete. No background monitoring, notification, or action was started.",
            "scan": scan,
        }

    def list_awareness_scans(self) -> list[dict]:
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
        for scan in self.list_awareness_scans():
            if scan.get("title") == title:
                return scan
        return None

    def _write(self, scans: list[dict]) -> None:
        self.file.write_text(
            json.dumps(scans, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
