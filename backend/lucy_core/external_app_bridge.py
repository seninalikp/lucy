"""
external_app_bridge.py
Stage 23 = external app bridge.

This stage prepares an external app bridge proposal layer only.
It does not connect to apps.
It does not open apps.
It does not read apps.
It does not send messages.
It does not use browser automation.
It does not use phone control.
It does not use network/API/provider keys.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


STAGE = "23 external app bridge"

VALID_BRIDGE_TYPES = {
    "manual_bridge_plan",
    "permission_gate_plan",
    "dry_run_connection_check",
}

VALID_STATUS = {"proposed", "blocked", "dry_run_ready", "done"}

NOT_IMPLEMENTED = [
    "real external app connection",
    "WhatsApp control",
    "Instagram control",
    "Chrome control",
    "browser automation",
    "phone control",
    "reading app data",
    "sending messages",
    "network server",
    "API/provider keys",
    "background monitoring",
    "proactive awareness",
    "deep recall",
    "judgment",
    "adaptive communication",
    "human-state awareness",
    "time awareness",
    "autonomy boundaries",
]


class ExternalAppBridge:
    def __init__(self, lucy_data: Path) -> None:
        self.lucy_data = Path(lucy_data)
        self.file = self.lucy_data / "external_app_bridge.json"
        self.lucy_data.mkdir(parents=True, exist_ok=True)

    def status(self) -> dict:
        proposals = self.list_bridge_proposals()
        return {
            "stage": STAGE,
            "external_app_bridge": "active",
            "bridge_proposals": len(proposals),
            "execution_mode": "dry_run_only",
            "real_connection": False,
            "approval_required": True,
            "whatsapp_control": "blocked",
            "instagram_control": "blocked",
            "chrome_control": "blocked",
            "browser_automation": "blocked",
            "phone_control": "blocked",
            "app_reading": "blocked",
            "message_sending": "blocked",
            "network_server": "blocked",
            "api_provider_keys": "blocked",
            "background_monitoring": "blocked",
            "proactive_awareness": "not implemented",
            "autonomy": "not implemented",
        }

    def create_bridge_proposal(self) -> dict:
        title = "Stage 23 dry-run external app bridge permission plan"
        existing = self._find_existing(title)
        if existing:
            return {"ok": True, "reused": True, "bridge": existing}

        bridge = {
            "bridge_id": f"br_{uuid.uuid4().hex[:12]}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "stage": STAGE,
            "title": title,
            "bridge_type": "permission_gate_plan",
            "status": "proposed",
            "summary": "Prepare a dry-run permission-gated bridge plan without connecting to external apps.",
            "dry_run_plan": [
                "Confirm bridge status.",
                "Create one bridge proposal.",
                "Show bridge proposals.",
                "Dry-run the bridge check.",
                "Confirm no app connection exists.",
                "Confirm no browser, phone, WhatsApp, Instagram, or Chrome control exists.",
                "Run tests.",
                "Run manual checks.",
                "Clean restart.",
                "Back up locally and upload to Drive after acceptance.",
            ],
            "requires_approval": True,
            "dry_run_only": True,
            "real_connection_allowed": False,
            "whatsapp_allowed": False,
            "instagram_allowed": False,
            "chrome_allowed": False,
            "browser_automation_allowed": False,
            "phone_control_allowed": False,
            "app_reading_allowed": False,
            "message_sending_allowed": False,
            "network_server_allowed": False,
            "api_keys_allowed": False,
            "background_monitoring_allowed": False,
            "blocked_until": "Stage 23 accepted, backed up locally, uploaded to Drive, and Senin explicitly approves Stage 24.",
            "not_implemented": list(NOT_IMPLEMENTED),
        }

        proposals = self.list_bridge_proposals()
        proposals.append(bridge)
        self._write(proposals)
        return {"ok": True, "reused": False, "bridge": bridge}

    def dry_run_bridge_check(self) -> dict:
        bridge = self.create_bridge_proposal()["bridge"]
        return {
            "ok": True,
            "stage": STAGE,
            "dry_run_only": True,
            "would_connect": False,
            "real_connection_allowed": False,
            "message": "Dry run complete. No external app bridge was connected.",
            "bridge": bridge,
        }

    def list_bridge_proposals(self) -> list[dict]:
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
        for bridge in self.list_bridge_proposals():
            if bridge.get("title") == title:
                return bridge
        return None

    def _write(self, proposals: list[dict]) -> None:
        self.file.write_text(
            json.dumps(proposals, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
