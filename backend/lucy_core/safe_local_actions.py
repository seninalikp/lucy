"""
safe_local_actions.py
Stage 22 = safe local actions.

This stage prepares a safe local action proposal layer only.
It does not execute actions.
It does not run shell commands.
It does not delete, move, or edit files.
It does not open apps.
It does not use network/API/provider access.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


STAGE = "22 safe local actions"

VALID_ACTION_TYPES = {
    "organize_project_note",
    "create_backup_reminder_note",
    "prepare_manual_checklist",
}

VALID_STATUS = {"proposed", "blocked", "dry_run_ready", "done"}

NOT_IMPLEMENTED = [
    "real file modification",
    "file deletion",
    "file moving",
    "shell command execution",
    "app opening",
    "network access",
    "browser control",
    "phone control",
    "background automation",
    "proactive monitoring",
    "external app bridge",
    "deep recall",
    "judgment",
    "adaptive communication",
    "human-state awareness",
    "time awareness",
    "autonomy boundaries",
    "API/provider work",
]


class SafeLocalActions:
    def __init__(self, lucy_data: Path) -> None:
        self.lucy_data = Path(lucy_data)
        self.file = self.lucy_data / "safe_local_actions.json"
        self.lucy_data.mkdir(parents=True, exist_ok=True)

    def status(self) -> dict:
        proposals = self.list_actions()
        return {
            "stage": STAGE,
            "safe_local_actions": "active",
            "action_proposals": len(proposals),
            "execution_mode": "dry_run_only",
            "real_execution": False,
            "approval_required": True,
            "shell_execution": "blocked",
            "file_deletion": "blocked",
            "file_moving": "blocked",
            "file_editing": "blocked",
            "app_opening": "blocked",
            "network_access": "blocked",
            "background_automation": "blocked",
            "external_app_bridge": "not implemented",
            "proactive_monitoring": "not implemented",
            "autonomy": "not implemented",
        }

    def create_action_proposal(self) -> dict:
        title = "Stage 22 dry-run backup checklist proposal"
        existing = self._find_existing(title)
        if existing:
            return {"ok": True, "reused": True, "action": existing}

        action = {
            "safe_action_id": f"sa_{uuid.uuid4().hex[:12]}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "stage": STAGE,
            "title": title,
            "action_type": "prepare_manual_checklist",
            "status": "proposed",
            "summary": "Prepare a dry-run checklist for Stage 22 tests, manual checks, clean restart, local backup, and Drive upload.",
            "dry_run_plan": [
                "Confirm Stage 22 status.",
                "Create one safe action proposal.",
                "Show proposed safe actions.",
                "Confirm no real execution exists.",
                "Run tests.",
                "Run manual checks.",
                "Clean restart.",
                "Back up locally and upload to Drive after acceptance.",
            ],
            "requires_approval": True,
            "dry_run_only": True,
            "real_execution_allowed": False,
            "shell_execution_allowed": False,
            "file_delete_allowed": False,
            "file_move_allowed": False,
            "file_edit_allowed": False,
            "app_open_allowed": False,
            "network_allowed": False,
            "background_allowed": False,
            "blocked_until": "Stage 22 accepted, backed up locally, uploaded to Drive, and Senin explicitly approves Stage 23.",
            "not_implemented": list(NOT_IMPLEMENTED),
        }

        actions = self.list_actions()
        actions.append(action)
        self._write(actions)
        return {"ok": True, "reused": False, "action": action}

    def dry_run_action(self) -> dict:
        proposal = self.create_action_proposal()["action"]
        return {
            "ok": True,
            "stage": STAGE,
            "dry_run_only": True,
            "would_execute": False,
            "real_execution_allowed": False,
            "message": "Dry run complete. No local action was executed.",
            "action": proposal,
        }

    def list_actions(self) -> list[dict]:
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
        for action in self.list_actions():
            if action.get("title") == title:
                return action
        return None

    def _write(self, actions: list[dict]) -> None:
        self.file.write_text(
            json.dumps(actions, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
