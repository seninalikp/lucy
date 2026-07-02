"""
time_awareness.py
Stage 29 = time awareness.

Manual explicit time-context awareness only.
No autonomous reminders.
No scheduled actions.
No automatic notifications.
No background monitoring.
No calendar/email/app reading.
No network/API time lookup.
No real actions.
No autonomy.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


STAGE = "29 time awareness"

BLOCKED_TERMS = [
    "remind me",
    "notify me",
    "send notification",
    "schedule this",
    "schedule action",
    "every day",
    "every hour",
    "every week",
    "background check",
    "monitor time",
    "watch calendar",
    "read calendar",
    "read email",
    "open calendar",
    "open email",
    "read whatsapp",
    "read instagram",
    "read chrome",
    "use network time",
    "call api",
    "auto run",
    "run automatically",
]

NOT_IMPLEMENTED = [
    "autonomous reminders",
    "scheduled actions",
    "automatic notifications",
    "background monitoring",
    "calendar reading",
    "email reading",
    "external app reading",
    "network time lookup",
    "API/provider keys",
    "time-based self-action",
    "autonomy boundaries",
]


class TimeAwareness:
    def __init__(self, lucy_data: Path) -> None:
        self.lucy_data = Path(lucy_data)
        self.file = self.lucy_data / "time_awareness.json"
        self.lucy_data.mkdir(parents=True, exist_ok=True)

    def status(self) -> dict:
        records = self.list_time_contexts()
        return {
            "stage": STAGE,
            "time_awareness": "active",
            "time_context_records": len(records),
            "execution_mode": "manual_explicit_time_context_only",
            "local_runtime_clock": "allowed_for_manual_context",
            "network_time_lookup": "blocked",
            "autonomous_reminders": "blocked",
            "scheduled_actions": "blocked",
            "automatic_notifications": "blocked",
            "background_monitoring": "blocked",
            "calendar_reading": "blocked",
            "email_reading": "blocked",
            "external_app_reading": "blocked",
            "real_actions": False,
            "network_access": "blocked",
            "api_provider_keys": "blocked",
            "approval_required": True,
            "autonomy": "not implemented",
        }

    def create_time_context(self, context: str | None = None) -> dict:
        clean_context = self._clean_context(context)
        assessment = self._assess_context(clean_context)
        now_utc = datetime.now(timezone.utc).isoformat()
        title = f"Stage 29 explicit time context: {clean_context}"

        existing = self._find_existing(title)
        if existing:
            return {"ok": True, "reused": True, "time_context": existing}

        record = {
            "time_context_id": f"ta_{uuid.uuid4().hex[:12]}",
            "created_at": now_utc,
            "stage": STAGE,
            "title": title,
            "explicit_time_context": clean_context,
            "awareness_type": "manual_explicit_time_context",
            "status": "observed",
            "category": assessment["category"],
            "interpretation": assessment["interpretation"],
            "summary": assessment["summary"],
            "recommended_reply_adjustment": assessment["recommended_reply_adjustment"],
            "recommended_next_step": assessment["recommended_next_step"],
            "local_runtime_clock_used": True,
            "observed_at_utc": now_utc,
            "requires_manual_review": True,
            "requires_approval": True,
            "dry_run_only": True,
            "manual_context_only": True,
            "autonomous_reminders_allowed": False,
            "scheduled_actions_allowed": False,
            "automatic_notifications_allowed": False,
            "background_monitoring_allowed": False,
            "calendar_reading_allowed": False,
            "email_reading_allowed": False,
            "external_app_reading_allowed": False,
            "network_time_lookup_allowed": False,
            "real_action_allowed": False,
            "network_allowed": False,
            "api_keys_allowed": False,
            "blocked_until": "Stage 29 accepted, backed up locally, uploaded to Drive, and Senin explicitly approves Stage 30.",
            "not_implemented": list(NOT_IMPLEMENTED),
        }

        records = self.list_time_contexts()
        records.append(record)
        self._write(records)
        return {"ok": True, "reused": False, "time_context": record}

    def dry_run_time_awareness(self, context: str | None = None) -> dict:
        time_context = self.create_time_context(context=context)["time_context"]
        return {
            "ok": True,
            "stage": STAGE,
            "dry_run_only": True,
            "would_create_reminder": False,
            "would_schedule_action": False,
            "would_send_notification": False,
            "would_monitor_background": False,
            "would_read_calendar": False,
            "would_read_email": False,
            "would_read_external_apps": False,
            "would_use_network_time": False,
            "would_use_network": False,
            "would_use_api_keys": False,
            "would_take_action": False,
            "real_action_allowed": False,
            "message": "Dry run complete. Only explicit manual time context was recorded; no reminder, schedule, notification, monitoring, app read, network call, or action occurred.",
            "time_context": time_context,
        }

    def list_time_contexts(self) -> list[dict]:
        if not self.file.exists():
            return []
        try:
            data = json.loads(self.file.read_text(encoding="utf-8"))
        except Exception:
            return []
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []

    def _clean_context(self, context: str | None) -> str:
        value = (context or "current manual Lucy workflow checkpoint").strip()
        if not value:
            return "current manual Lucy workflow checkpoint"
        return value[:180]

    def _assess_context(self, context: str) -> dict:
        lowered = context.lower()

        if any(term in lowered for term in BLOCKED_TERMS):
            return {
                "category": "blocked_autonomous_time_request",
                "interpretation": "Unsafe time request: autonomous reminder, schedule, monitoring, external reading, network/API, or action.",
                "summary": "Blocked request detected. Stage 29 can only handle manual explicit time context.",
                "recommended_reply_adjustment": "Refuse the autonomous part and keep the user in manual control.",
                "recommended_next_step": "Ask the user to manually run the next step when ready.",
            }

        if any(term in lowered for term in ["now", "today", "current", "right now"]):
            return {
                "category": "current_time_context",
                "interpretation": "User provided current manual time context.",
                "summary": "Current/today context can be used to keep workflow wording grounded.",
                "recommended_reply_adjustment": "Use present-focused wording and avoid pretending to monitor time.",
                "recommended_next_step": "Continue the current manual workflow step.",
            }

        if any(term in lowered for term in ["tomorrow", "next", "later", "future", "after"]):
            return {
                "category": "future_relative_context",
                "interpretation": "User provided future or next-step relative time context.",
                "summary": "Future context can be stored as planning context only, not as an autonomous reminder.",
                "recommended_reply_adjustment": "Frame it as a manual next checkpoint, not an automatic schedule.",
                "recommended_next_step": "Keep Stage 30 blocked until Stage 29 is accepted and backed up.",
            }

        if any(term in lowered for term in ["yesterday", "last", "previous", "before", "backup", "checkpoint"]):
            return {
                "category": "past_or_checkpoint_context",
                "interpretation": "User provided past/checkpoint time context.",
                "summary": "Past context can help identify what was completed or backed up.",
                "recommended_reply_adjustment": "Reference the checkpoint carefully and do not invent missing history.",
                "recommended_next_step": "Verify the last accepted stage or backup before continuing.",
            }

        if any(term in lowered for term in ["deadline", "due", "by ", "within"]):
            return {
                "category": "deadline_context",
                "interpretation": "User provided a deadline-like manual time context.",
                "summary": "Deadline context can help prioritize, but Lucy must not schedule or auto-execute.",
                "recommended_reply_adjustment": "Give the smallest safe next action and keep responsibility manual.",
                "recommended_next_step": "Ask for confirmation before moving to the next manual command.",
            }

        return {
            "category": "general_time_context",
            "interpretation": "General explicit time context detected.",
            "summary": "Lucy can store this as manual context without autonomy.",
            "recommended_reply_adjustment": "Stay grounded and avoid claiming scheduled awareness.",
            "recommended_next_step": "Continue only when the user manually asks.",
        }

    def _find_existing(self, title: str) -> dict | None:
        for record in self.list_time_contexts():
            if record.get("title") == title:
                return record
        return None

    def _write(self, records: list[dict]) -> None:
        self.file.write_text(
            json.dumps(records, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
