"""
autonomy_boundaries.py
Stage 30 = autonomy boundaries.

Lucy can explain, prepare, evaluate, organize safe records, and suggest next steps.
Lucy cannot act independently, bypass Guardian, self-modify, control apps,
send messages, move money, use APIs/network, monitor background, or claim autonomy.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


STAGE = "30 autonomy boundaries"

BLOCKED_TERMS = [
    "do it yourself",
    "act on your own",
    "run automatically",
    "auto execute",
    "bypass guardian",
    "ignore guardian",
    "disable guardian",
    "override guardian",
    "self modify",
    "modify yourself",
    "rewrite yourself",
    "control apps",
    "open whatsapp",
    "send message",
    "send email",
    "move money",
    "transfer money",
    "wallet transfer",
    "bank transfer",
    "use api",
    "call api",
    "use network",
    "background monitoring",
    "monitor in background",
    "be autonomous",
    "pretend autonomy",
    "act without approval",
]

NOT_IMPLEMENTED = [
    "independent action",
    "Guardian bypass",
    "self-modification",
    "external app control",
    "message sending",
    "email sending",
    "money movement",
    "wallet transfer",
    "bank transfer",
    "API/provider key use",
    "network access",
    "background monitoring",
    "scheduled autonomous execution",
    "automatic notifications",
    "hidden persuasion",
    "fake autonomy claims",
]


class AutonomyBoundaries:
    def __init__(self, lucy_data: Path) -> None:
        self.lucy_data = Path(lucy_data)
        self.file = self.lucy_data / "autonomy_boundaries.json"
        self.lucy_data.mkdir(parents=True, exist_ok=True)

    def status(self) -> dict:
        records = self.list_boundary_records()
        return {
            "stage": STAGE,
            "autonomy_boundaries": "active",
            "boundary_records": len(records),
            "execution_mode": "manual_permission_boundaries_only",
            "allowed_prepare": True,
            "allowed_explain": True,
            "allowed_evaluate": True,
            "allowed_safe_structured_records": True,
            "allowed_suggest_next_steps": True,
            "requires_user_approval": True,
            "independent_action": "blocked",
            "guardian_bypass": "blocked",
            "self_modification": "blocked",
            "external_app_control": "blocked",
            "message_sending": "blocked",
            "email_sending": "blocked",
            "money_movement": "blocked",
            "api_provider_keys": "blocked",
            "network_access": "blocked",
            "background_monitoring": "blocked",
            "scheduled_autonomous_execution": "blocked",
            "automatic_notifications": "blocked",
            "hidden_persuasion": "blocked",
            "fake_autonomy_claims": "blocked",
            "real_actions": False,
            "autonomy": "bounded_manual_assistant_only",
        }

    def create_boundary_record(self, request: str | None = None) -> dict:
        clean_request = self._clean_request(request)
        assessment = self._assess_request(clean_request)
        title = f"Stage 30 autonomy boundary: {clean_request}"

        existing = self._find_existing(title)
        if existing:
            return {"ok": True, "reused": True, "boundary_record": existing}

        record = {
            "boundary_record_id": f"ab_{uuid.uuid4().hex[:12]}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "stage": STAGE,
            "title": title,
            "request": clean_request,
            "boundary_type": "manual_permission_boundary",
            "status": "recorded",
            "category": assessment["category"],
            "decision": assessment["decision"],
            "summary": assessment["summary"],
            "allowed_response": assessment["allowed_response"],
            "recommended_next_step": assessment["recommended_next_step"],
            "requires_user_approval": True,
            "dry_run_only": True,
            "manual_control_only": True,
            "prepare_allowed": True,
            "explain_allowed": True,
            "evaluate_allowed": True,
            "safe_structured_records_allowed": True,
            "suggest_next_steps_allowed": True,
            "independent_action_allowed": False,
            "guardian_bypass_allowed": False,
            "self_modification_allowed": False,
            "external_app_control_allowed": False,
            "message_sending_allowed": False,
            "email_sending_allowed": False,
            "money_movement_allowed": False,
            "api_keys_allowed": False,
            "network_allowed": False,
            "background_monitoring_allowed": False,
            "scheduled_autonomous_execution_allowed": False,
            "automatic_notifications_allowed": False,
            "hidden_persuasion_allowed": False,
            "fake_autonomy_claims_allowed": False,
            "real_action_allowed": False,
            "blocked_until": "Only manual user-approved operation is allowed. API/provider-key stage remains blocked until explicitly approved later.",
            "not_implemented": list(NOT_IMPLEMENTED),
        }

        records = self.list_boundary_records()
        records.append(record)
        self._write(records)
        return {"ok": True, "reused": False, "boundary_record": record}

    def dry_run_autonomy_boundaries(self, request: str | None = None) -> dict:
        boundary_record = self.create_boundary_record(request=request)["boundary_record"]
        return {
            "ok": True,
            "stage": STAGE,
            "dry_run_only": True,
            "would_act_independently": False,
            "would_bypass_guardian": False,
            "would_self_modify": False,
            "would_control_apps": False,
            "would_send_message": False,
            "would_send_email": False,
            "would_move_money": False,
            "would_use_api_keys": False,
            "would_use_network": False,
            "would_monitor_background": False,
            "would_schedule_autonomous_execution": False,
            "would_send_notification": False,
            "would_use_hidden_persuasion": False,
            "would_claim_fake_autonomy": False,
            "would_take_real_action": False,
            "real_action_allowed": False,
            "message": "Dry run complete. Boundary was evaluated only; no autonomous action, Guardian bypass, app control, network/API use, money movement, message sending, background monitoring, or self-modification occurred.",
            "boundary_record": boundary_record,
        }

    def list_boundary_records(self) -> list[dict]:
        if not self.file.exists():
            return []
        try:
            data = json.loads(self.file.read_text(encoding="utf-8"))
        except Exception:
            return []
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []

    def _clean_request(self, request: str | None) -> str:
        value = (request or "manual user-approved support only").strip()
        if not value:
            return "manual user-approved support only"
        return value[:180]

    def _assess_request(self, request: str) -> dict:
        lowered = request.lower()

        if any(term in lowered for term in ["bypass guardian", "ignore guardian", "disable guardian", "override guardian"]):
            return {
                "category": "blocked_guardian_override",
                "decision": "blocked",
                "summary": "Guardian bypass or override request detected.",
                "allowed_response": "Refuse bypass and keep Guardian active.",
                "recommended_next_step": "Continue only with Guardian-approved manual steps.",
            }

        if any(term in lowered for term in ["self modify", "modify yourself", "rewrite yourself"]):
            return {
                "category": "blocked_self_modification",
                "decision": "blocked",
                "summary": "Self-modification request detected.",
                "allowed_response": "Refuse self-modification and require manual reviewed patches.",
                "recommended_next_step": "Use the approved patch pipeline only with user approval.",
            }

        if any(term in lowered for term in ["move money", "transfer money", "wallet transfer", "bank transfer"]):
            return {
                "category": "blocked_money_movement",
                "decision": "blocked",
                "summary": "Money movement request detected.",
                "allowed_response": "Refuse money movement. Only explanation or checklist support is allowed.",
                "recommended_next_step": "Provide manual safety checklist only.",
            }

        if any(term in lowered for term in ["send message", "send email", "open whatsapp"]):
            return {
                "category": "blocked_message_or_app_control",
                "decision": "blocked",
                "summary": "Message sending or external app control request detected.",
                "allowed_response": "Refuse sending/controlling. Draft text may be prepared for manual review only.",
                "recommended_next_step": "Prepare a draft or instruction, then wait for user action.",
            }

        if any(term in lowered for term in ["use api", "call api", "use network"]):
            return {
                "category": "blocked_api_or_network",
                "decision": "blocked",
                "summary": "API or network use request detected.",
                "allowed_response": "Refuse API/network use until the later approved API/provider-key stage.",
                "recommended_next_step": "Keep local-only manual workflow.",
            }

        if any(term in lowered for term in ["background monitoring", "monitor in background", "run automatically", "auto execute"]):
            return {
                "category": "blocked_background_or_autonomous_execution",
                "decision": "blocked",
                "summary": "Background/autonomous execution request detected.",
                "allowed_response": "Refuse background/autonomous execution.",
                "recommended_next_step": "User must manually run the next command.",
            }

        if any(term in lowered for term in ["be autonomous", "pretend autonomy", "act without approval", "act on your own", "do it yourself"]):
            return {
                "category": "blocked_fake_or_independent_autonomy",
                "decision": "blocked",
                "summary": "Independent autonomy or fake autonomy request detected.",
                "allowed_response": "Clarify Lucy is bounded to manual approved support.",
                "recommended_next_step": "Offer a safe manual next step.",
            }

        if any(term in lowered for term in BLOCKED_TERMS):
            return {
                "category": "blocked_autonomy_boundary",
                "decision": "blocked",
                "summary": "Autonomy boundary risk detected.",
                "allowed_response": "Refuse the unsafe part and keep the workflow manual.",
                "recommended_next_step": "Ask for explicit approval before any safe next step.",
            }

        return {
            "category": "allowed_manual_support",
            "decision": "allowed_as_manual_support_only",
            "summary": "Request fits manual user-approved support boundaries.",
            "allowed_response": "Explain, prepare, evaluate, organize safe records, or suggest next steps.",
            "recommended_next_step": "Continue with one manual step and wait for confirmation.",
        }

    def _find_existing(self, title: str) -> dict | None:
        for record in self.list_boundary_records():
            if record.get("title") == title:
                return record
        return None

    def _write(self, records: list[dict]) -> None:
        self.file.write_text(
            json.dumps(records, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
