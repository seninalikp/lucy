"""
Stage 15 evaluation lab.
Evaluates growth proposals with fixed local checks only. It does not edit code,
create patches, run shadow tests, store experience, or approve implementation.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from backend.lucy_core.safe_storage import safe_read_json, safe_write_json


EVALUATION_LAB_STAGE = "15 evaluation lab"
EVALUATION_FIELDS = (
    "evaluation_id",
    "created_at",
    "stage",
    "proposal_id",
    "proposal_title",
    "checks_run",
    "score",
    "result",
    "risk_level",
    "approval_required",
    "blocked_reasons",
    "not_implemented",
)
VALID_EVALUATION_RESULTS = ("pass", "needs_review", "blocked")
VALID_EVALUATION_RISK_LEVELS = ("low", "medium", "high")
NOT_IMPLEMENTED = [
    "patch pipeline",
    "experience storage",
    "automatic patching",
]
CHECKS_RUN = [
    "proposal has title",
    "proposal has reason",
    "proposal has risk_level",
    "proposal requires approval",
    "no self-modification request",
    "no automatic patching request",
    "no network/server/ui/voice/api request",
    "no stage jump request",
    "no fake-consciousness language",
]
FORBIDDEN_EVALUATION_PHRASES = (
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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class EvaluationLab:
    def __init__(self, lucy_data_dir: Path) -> None:
        self.lucy_data_dir = lucy_data_dir
        self.results_file = lucy_data_dir / "evaluation_results.json"
        self.last_reused = False

    def status(self) -> dict:
        return {
            "stage": EVALUATION_LAB_STAGE,
            "evaluation_lab": "active",
            "evaluation_results": len(self.list_evaluations()),
            "automatic_patching": "disabled",
            "shadow_testing": "active",
            "patch_pipeline": "not implemented",
            "experience_storage": "not implemented",
            "approval_required_before_implementation": True,
            "file": str(self.results_file),
        }

    def list_evaluations(self) -> list[dict]:
        data = safe_read_json(self.results_file, [])
        if not isinstance(data, list):
            return []
        evaluations = []
        for item in data:
            if isinstance(item, dict):
                evaluations.append(self._sanitize_evaluation(item))
        return evaluations

    def evaluate_all(self, proposals: list[dict]) -> dict:
        if not proposals:
            return {"ok": False, "reason": "no growth proposals found", "evaluations": []}
        evaluations = []
        reused_count = 0
        created_count = 0
        for proposal in proposals:
            evaluation = self.evaluate_proposal(proposal)
            evaluations.append(evaluation)
            if self.last_reused:
                reused_count += 1
            else:
                created_count += 1
        return {
            "ok": True,
            "evaluations": evaluations,
            "reused_count": reused_count,
            "created_count": created_count,
        }

    def evaluate_selected(self, proposals: list[dict], selector: str = "") -> dict:
        if not proposals:
            return {"ok": False, "reason": "no growth proposals found"}
        index = self._select_index(proposals, selector)
        if index is None:
            return {"ok": False, "reason": "proposal not found"}
        evaluation = self.evaluate_proposal(proposals[index])
        return {"ok": True, "evaluation": evaluation, "reused": self.last_reused}

    def evaluate_proposal(self, proposal: dict) -> dict:
        evaluations = self.list_evaluations()
        existing = self._find_existing_evaluation(evaluations, proposal)
        if existing is not None:
            self.last_reused = True
            return existing
        evaluation = self._build_evaluation(proposal)
        evaluations.append(evaluation)
        safe_write_json(self.results_file, evaluations, backup=True)
        self.last_reused = False
        return evaluation

    def _find_existing_evaluation(self, evaluations: list[dict], proposal: dict) -> dict | None:
        proposal_id = str(proposal.get("proposal_id", "")).strip()
        proposal_title = self._normalize_match_text(proposal.get("title", ""))
        for evaluation in reversed(evaluations):
            if evaluation.get("stage") != EVALUATION_LAB_STAGE:
                continue
            if proposal_id and str(evaluation.get("proposal_id", "")).strip() == proposal_id:
                return evaluation
            if not proposal_id and proposal_title:
                existing_title = self._normalize_match_text(evaluation.get("proposal_title", ""))
                if existing_title == proposal_title:
                    return evaluation
        return None

    def _normalize_match_text(self, value: object) -> str:
        return " ".join(str(value or "").strip().lower().split())

    def _build_evaluation(self, proposal: dict) -> dict:
        title = str(proposal.get("title", "")).strip()
        reason = str(proposal.get("reason", "")).strip()
        risk_level = self._risk_level(proposal.get("risk_level"))
        approval_required = bool(proposal.get("approval_required") is True)
        blocked_reasons: list[str] = []
        review_reasons: list[str] = []

        if not title:
            review_reasons.append("missing title")
        if not reason:
            review_reasons.append("missing reason")
        if proposal.get("risk_level") not in VALID_EVALUATION_RISK_LEVELS:
            review_reasons.append("missing or invalid risk_level")
        if not approval_required:
            review_reasons.append("approval_required is not true")

        request_text = self._proposal_request_text(proposal)
        blocked_reasons.extend(self._blocked_reasons(request_text))

        if blocked_reasons:
            result = "blocked"
            risk_level = "high"
            score = max(0, 40 - (10 * len(blocked_reasons)) - (5 * len(review_reasons)))
        elif review_reasons:
            result = "needs_review"
            score = max(0, 85 - (10 * len(review_reasons)))
        else:
            result = "pass"
            score = 90

        evaluation = {
            "evaluation_id": f"ev_{uuid.uuid4().hex[:12]}",
            "created_at": _now(),
            "stage": EVALUATION_LAB_STAGE,
            "proposal_id": str(proposal.get("proposal_id", "")),
            "proposal_title": title,
            "checks_run": list(CHECKS_RUN),
            "score": int(max(0, min(100, score))),
            "result": result,
            "risk_level": risk_level,
            "approval_required": True,
            "blocked_reasons": blocked_reasons,
            "not_implemented": list(NOT_IMPLEMENTED),
        }
        return {field: evaluation[field] for field in EVALUATION_FIELDS}

    def _blocked_reasons(self, request_text: str) -> list[str]:
        text = request_text.lower()
        reasons = []
        if any(term in text for term in ("self-modification", "self-modify", "self modify", "modify myself", "rewrite myself", "rewrite herself")):
            reasons.append("self-modification request")
        if any(term in text for term in ("automatic patch", "apply patch", "apply code", "edit code", "create patch", "generate patch")):
            reasons.append("automatic patching request")
        if any(term in text for term in ("network", "server", "socket", "external api", "api call", "ui", "voice", "phone", "browser")):
            reasons.append("network/server/ui/voice/api request")
        if any(term in text for term in ("stage 16", "stage16", "stage 17", "stage17", "stage 18", "stage18", "shadow testing", "patch pipeline", "experience storage")):
            reasons.append("stage jump request")
        if any(phrase in text for phrase in FORBIDDEN_EVALUATION_PHRASES):
            reasons.append("fake-consciousness language")
        return reasons

    def _proposal_request_text(self, proposal: dict) -> str:
        parts = [
            proposal.get("title", ""),
            proposal.get("reason", ""),
            proposal.get("evidence_summary", ""),
            proposal.get("suggested_area", ""),
        ]
        possible_files = proposal.get("possible_files", [])
        if isinstance(possible_files, list):
            parts.extend(str(item) for item in possible_files)
        return " ".join(str(part) for part in parts if part is not None)

    def _risk_level(self, risk_level: object) -> str:
        if risk_level in VALID_EVALUATION_RISK_LEVELS:
            return str(risk_level)
        return "medium"

    def _sanitize_evaluation(self, evaluation: dict) -> dict:
        default = self._default_empty_evaluation()
        data = dict(default)
        for field in EVALUATION_FIELDS:
            if field in evaluation:
                data[field] = evaluation[field]
        data["stage"] = EVALUATION_LAB_STAGE
        if data["result"] not in VALID_EVALUATION_RESULTS:
            data["result"] = "needs_review"
        if data["risk_level"] not in VALID_EVALUATION_RISK_LEVELS:
            data["risk_level"] = "medium"
        try:
            data["score"] = int(data["score"])
        except (TypeError, ValueError):
            data["score"] = 0
        data["score"] = max(0, min(100, data["score"]))
        data["approval_required"] = True
        if not isinstance(data["blocked_reasons"], list):
            data["blocked_reasons"] = []
        if not isinstance(data["not_implemented"], list):
            data["not_implemented"] = list(NOT_IMPLEMENTED)
        return {field: data[field] for field in EVALUATION_FIELDS}

    def _default_empty_evaluation(self) -> dict:
        return {
            "evaluation_id": "",
            "created_at": "",
            "stage": EVALUATION_LAB_STAGE,
            "proposal_id": "",
            "proposal_title": "",
            "checks_run": list(CHECKS_RUN),
            "score": 0,
            "result": "needs_review",
            "risk_level": "medium",
            "approval_required": True,
            "blocked_reasons": [],
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
