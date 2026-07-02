"""
Stage 14 growth proposals.
Creates conservative proposal records only. It does not edit code, generate
patches, create tests, run tools, or apply changes.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from backend.lucy_core.safe_storage import safe_read_json, safe_write_json


GROWTH_PROPOSAL_STAGE = "14 growth proposals"
PROPOSAL_FIELDS = (
    "proposal_id",
    "created_at",
    "stage",
    "title",
    "reason",
    "evidence_summary",
    "suggested_area",
    "possible_files",
    "risk_level",
    "approval_required",
    "status",
    "blocked_actions",
    "not_implemented",
)
VALID_PROPOSAL_STATUSES = ("proposed", "needs_review", "rejected", "approved_for_future")
VALID_RISK_LEVELS = ("low", "medium", "high")
FORBIDDEN_GROWTH_PHRASES = (
    "i am alive",
    "i am conscious",
    "i feel",
    "i want",
    "i missed you",
    "i woke up",
    "i became real",
    "i have emotions",
    "i am human",
    "i choose my own path",
    "i am free",
)
BLOCKED_ACTIONS = [
    "apply code changes",
    "generate patches",
    "create evaluation cases",
    "run experiments",
    "create shadow runtime",
    "create experience records",
    "change identity",
    "change Guardian",
    "change safe access policy",
    "add network/server/socket",
    "use external APIs",
]
NOT_IMPLEMENTED = [
    "shadow testing",
    "approved patch pipeline",
    "experience storage",
    "autonomy",
    "automatic patching",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GrowthProposalSystem:
    def __init__(self, lucy_data_dir: Path) -> None:
        self.lucy_data_dir = lucy_data_dir
        self.proposals_file = lucy_data_dir / "growth_proposals.json"

    def status(self) -> dict:
        proposals = self.list_proposals()
        return {
            "stage": GROWTH_PROPOSAL_STAGE,
            "proposal_system": "active",
            "existing_proposals": len(proposals),
            "approval_required": True,
            "automatic_patching": "disabled",
            "evaluation_lab": "active",
            "shadow_testing": "active",
            "patch_pipeline": "not implemented",
            "experience_storage": "not implemented",
            "file": str(self.proposals_file),
        }

    def list_proposals(self) -> list[dict]:
        data = safe_read_json(self.proposals_file, [])
        if not isinstance(data, list):
            return []
        proposals = []
        for item in data:
            if isinstance(item, dict):
                proposals.append(self._sanitize_proposal(item))
        return proposals

    def propose(self, runtime=None) -> dict:
        proposals = self.list_proposals()
        proposal = self._proposal_from_local_state(runtime)
        proposals.append(proposal)
        self.proposals_file.parent.mkdir(parents=True, exist_ok=True)
        safe_write_json(self.proposals_file, proposals, backup=True)
        return proposal

    def review(self, selector: str, status: str) -> dict:
        if status not in {"rejected", "approved_for_future"}:
            return {"ok": False, "reason": "invalid review status"}
        proposals = self.list_proposals()
        if not proposals:
            return {"ok": False, "reason": "no proposals found"}
        index = self._select_index(proposals, selector)
        if index is None:
            return {"ok": False, "reason": "proposal not found"}
        proposals[index]["status"] = status
        safe_write_json(self.proposals_file, proposals, backup=True)
        return {"ok": True, "proposal": proposals[index]}

    def _proposal_from_local_state(self, runtime) -> dict:
        status = "proposed"
        title = "Improve vague command handling"
        reason = "Some short or vague commands may still need clearer routing."
        evidence_summary = self._evidence_summary(runtime)
        proposal = {
            "proposal_id": f"gp_{uuid.uuid4().hex[:12]}",
            "created_at": _now(),
            "stage": GROWTH_PROPOSAL_STAGE,
            "title": title,
            "reason": reason,
            "evidence_summary": evidence_summary,
            "suggested_area": "conversation routing",
            "possible_files": ["backend/lucy_core/router.py", "tests"],
            "risk_level": "low",
            "approval_required": True,
            "status": status,
            "blocked_actions": list(BLOCKED_ACTIONS),
            "not_implemented": list(NOT_IMPLEMENTED),
        }
        return {field: proposal[field] for field in PROPOSAL_FIELDS}

    def _evidence_summary(self, runtime) -> str:
        if runtime is None:
            return "Local proposal based on Stage 14 fixed policy only."
        try:
            conversation_count = len(runtime.load_conversation_history(limit=10))
        except Exception:
            conversation_count = 0
        try:
            self_model = runtime.self_model_status()
            stage = self_model.get("stage", "13 self-model")
        except Exception:
            stage = "13 self-model"
        return (
            f"Local state checked: {stage}; recent conversation entries reviewed: {conversation_count}. "
            "No code changes, tests, patches, or evaluations are created by this proposal."
        )

    def _sanitize_proposal(self, proposal: dict) -> dict:
        default = self._default_empty_proposal()
        data = dict(default)
        for field in PROPOSAL_FIELDS:
            if field in proposal:
                data[field] = proposal[field]
        if data["status"] not in VALID_PROPOSAL_STATUSES:
            data["status"] = "needs_review"
        if data["risk_level"] not in VALID_RISK_LEVELS:
            data["risk_level"] = "medium"
        data["stage"] = GROWTH_PROPOSAL_STAGE
        data["approval_required"] = True
        return {field: data[field] for field in PROPOSAL_FIELDS}

    def _default_empty_proposal(self) -> dict:
        return {
            "proposal_id": "",
            "created_at": "",
            "stage": GROWTH_PROPOSAL_STAGE,
            "title": "",
            "reason": "",
            "evidence_summary": "",
            "suggested_area": "",
            "possible_files": [],
            "risk_level": "medium",
            "approval_required": True,
            "status": "needs_review",
            "blocked_actions": list(BLOCKED_ACTIONS),
            "not_implemented": list(NOT_IMPLEMENTED),
        }

    def _select_index(self, proposals: list[dict], selector: str) -> int | None:
        cleaned = str(selector or "").strip()
        if not cleaned:
            return len(proposals) - 1
        if cleaned.isdigit():
            index = int(cleaned) - 1
            if 0 <= index < len(proposals):
                return index
        for index, proposal in enumerate(proposals):
            if str(proposal.get("proposal_id", "")).startswith(cleaned):
                return index
        return None
