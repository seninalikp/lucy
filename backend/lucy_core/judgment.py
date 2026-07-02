"""
judgment.py
Stage 26 = judgment.

This stage creates cautious structured assessments only.
It does not make final decisions.
It does not override Guardian.
It does not take actions.
It does not move money.
It does not provide final legal, medical, financial, or safety-critical decisions.
It does not use network/API/provider keys.
It does not monitor in the background.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


STAGE = "26 judgment"

VALID_RISK_LEVELS = {"low", "medium", "high", "blocked"}
VALID_RECOMMENDATION_TYPES = {
    "continue_with_manual_review",
    "pause_and_verify",
    "blocked_sensitive_area",
}

SENSITIVE_TERMS = [
    "api key",
    ".env",
    "password",
    "token",
    "private key",
    "wallet",
    "bank transfer",
    "move money",
    "send money",
    "legal final decision",
    "medical final decision",
    "diagnose",
    "prescribe",
    "bypass guardian",
    "disable guardian",
    "ignore guardian",
]

NOT_IMPLEMENTED = [
    "autonomous decisions",
    "final legal decisions",
    "final medical decisions",
    "final financial decisions",
    "money movement",
    "Guardian override",
    "real actions",
    "network access",
    "API/provider keys",
    "background monitoring",
    "automatic notifications",
    "adaptive communication",
    "human-state awareness",
    "time awareness",
    "autonomy boundaries",
]


class Judgment:
    def __init__(self, lucy_data: Path) -> None:
        self.lucy_data = Path(lucy_data)
        self.file = self.lucy_data / "judgment.json"
        self.lucy_data.mkdir(parents=True, exist_ok=True)

    def status(self) -> dict:
        records = self.list_judgments()
        return {
            "stage": STAGE,
            "judgment": "active",
            "judgment_records": len(records),
            "execution_mode": "manual_cautious_assessment_only",
            "guardian_override": "blocked",
            "final_decisions": "blocked",
            "legal_medical_financial_final_decisions": "blocked",
            "money_movement": "blocked",
            "real_actions": False,
            "network_access": "blocked",
            "api_provider_keys": "blocked",
            "background_monitoring": "blocked",
            "approval_required": True,
            "autonomy": "not implemented",
        }

    def create_judgment(self, situation: str | None = None) -> dict:
        clean_situation = self._clean_situation(situation)
        title = f"Stage 26 cautious judgment: {clean_situation}"
        existing = self._find_existing(title)
        if existing:
            return {"ok": True, "reused": True, "judgment": existing}

        assessment = self._assess(clean_situation)

        record = {
            "judgment_id": f"jg_{uuid.uuid4().hex[:12]}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "stage": STAGE,
            "title": title,
            "situation": clean_situation,
            "judgment_type": "cautious_structured_assessment",
            "status": "observed",
            "risk_level": assessment["risk_level"],
            "recommendation_type": assessment["recommendation_type"],
            "summary": assessment["summary"],
            "reasoning_summary": assessment["reasoning_summary"],
            "recommended_next_step": assessment["recommended_next_step"],
            "requires_manual_review": True,
            "requires_approval": True,
            "dry_run_only": True,
            "guardian_override_allowed": False,
            "final_decision_allowed": False,
            "legal_medical_financial_final_decision_allowed": False,
            "money_movement_allowed": False,
            "real_action_allowed": False,
            "network_allowed": False,
            "api_keys_allowed": False,
            "background_monitoring_allowed": False,
            "blocked_until": "Stage 26 accepted, backed up locally, uploaded to Drive, and Senin explicitly approves Stage 27.",
            "not_implemented": list(NOT_IMPLEMENTED),
        }

        records = self.list_judgments()
        records.append(record)
        self._write(records)
        return {"ok": True, "reused": False, "judgment": record}

    def dry_run_judgment(self, situation: str | None = None) -> dict:
        judgment = self.create_judgment(situation=situation)["judgment"]
        return {
            "ok": True,
            "stage": STAGE,
            "dry_run_only": True,
            "would_override_guardian": False,
            "would_make_final_decision": False,
            "would_take_action": False,
            "would_use_network": False,
            "would_use_api_keys": False,
            "would_move_money": False,
            "real_action_allowed": False,
            "message": "Dry run complete. Judgment produced a cautious assessment only; no action or final decision was made.",
            "judgment": judgment,
        }

    def list_judgments(self) -> list[dict]:
        if not self.file.exists():
            return []
        try:
            data = json.loads(self.file.read_text(encoding="utf-8"))
        except Exception:
            return []
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []

    def _assess(self, situation: str) -> dict:
        lowered = situation.lower()

        if any(term in lowered for term in SENSITIVE_TERMS):
            return {
                "risk_level": "blocked",
                "recommendation_type": "blocked_sensitive_area",
                "summary": "Sensitive or high-risk request detected. Judgment must not proceed as a final decision.",
                "reasoning_summary": "The situation touches blocked or sensitive areas, so Lucy must defer to Guardian/manual review.",
                "recommended_next_step": "Pause. Use Guardian classification and Senin's explicit manual approval before any further step.",
            }

        if any(term in lowered for term in ["delete", "edit file", "execute", "run command", "external app", "browser", "phone"]):
            return {
                "risk_level": "high",
                "recommendation_type": "pause_and_verify",
                "summary": "Action-capable or system-touching request detected. Manual verification is required.",
                "reasoning_summary": "The situation may affect files, tools, apps, or system behavior, so it should stay proposal-only.",
                "recommended_next_step": "Do not execute. Convert it into a proposal/checklist and run tests first.",
            }

        if any(term in lowered for term in ["stage", "test", "backup", "manual check", "roadmap"]):
            return {
                "risk_level": "low",
                "recommendation_type": "continue_with_manual_review",
                "summary": "Safe project-stage situation detected.",
                "reasoning_summary": "The situation appears related to Lucy's staged build workflow, testing, backup, or roadmap control.",
                "recommended_next_step": "Continue with manual review, tests, clean restart, local backup, and Drive upload.",
            }

        return {
            "risk_level": "medium",
            "recommendation_type": "pause_and_verify",
            "summary": "General situation detected. Cautious manual review is recommended.",
            "reasoning_summary": "There is not enough structured context to safely recommend execution.",
            "recommended_next_step": "Clarify the situation, classify risk, and keep any next step manual and reversible.",
        }

    def _clean_situation(self, situation: str | None) -> str:
        value = (situation or "stage status review").strip()
        if not value:
            return "stage status review"
        return value[:160]

    def _find_existing(self, title: str) -> dict | None:
        for record in self.list_judgments():
            if record.get("title") == title:
                return record
        return None

    def _write(self, records: list[dict]) -> None:
        self.file.write_text(
            json.dumps(records, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
