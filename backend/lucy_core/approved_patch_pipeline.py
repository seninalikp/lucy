"""
Stage 17 approved patch pipeline.

Creates approval-required patch plan records from passed shadow tests only. It
does not generate diffs, apply patches, execute code, or store experience.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from backend.lucy_core.safe_storage import safe_read_json, safe_write_json


PATCH_PIPELINE_STAGE = "17 approved patch pipeline"
PATCH_PLAN_FIELDS = (
    "patch_plan_id",
    "created_at",
    "stage",
    "source_proposal_id",
    "source_evaluation_id",
    "source_shadow_test_id",
    "proposal_title",
    "status",
    "approval_required",
    "real_patching_enabled",
    "implementation_allowed",
    "suggested_files",
    "safety_checks",
    "blocked_reasons",
    "not_implemented",
)
VALID_PATCH_PLAN_STATUSES = ("planned", "needs_review", "blocked")
SAFETY_CHECKS = [
    "shadow test exists",
    "shadow test result is pass",
    "evaluation exists",
    "proposal exists",
    "approval is required",
    "real patching is disabled",
    "no experience storage",
    "no API/provider work",
    "no fake-consciousness language",
    "no roadmap jump",
]
NOT_IMPLEMENTED = [
    "real patching",
    "experience storage",
    "automatic application",
    "provider/API work",
]
FORBIDDEN_PATCH_PLAN_PHRASES = (
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
PROVIDER_TERMS = ("nvidia", "groq", "gemini", "openrouter", "provider router", "api key", "provider key")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ApprovedPatchPipeline:
    def __init__(self, lucy_data_dir: Path) -> None:
        self.lucy_data_dir = lucy_data_dir
        self.patch_plans_file = lucy_data_dir / "patch_plans.json"

    def status(self) -> dict:
        plans = self.list_patch_plans()
        return {
            "stage": PATCH_PIPELINE_STAGE,
            "approved_patch_pipeline": "active",
            "patch_plans": len(plans),
            "real_patching": "disabled",
            "real_patching_enabled": False,
            "implementation_allowed": False,
            "experience_storage": "not implemented",
            "approval_required_before_implementation": True,
            "file": str(self.patch_plans_file),
            "latest_plan": plans[-1] if plans else None,
        }

    def list_patch_plans(self) -> list[dict]:
        data = safe_read_json(self.patch_plans_file, [])
        if not isinstance(data, list):
            return []
        plans = []
        for item in data:
            if isinstance(item, dict):
                plans.append(self._sanitize_patch_plan(item))
        return plans

    def create_patch_plan(
        self,
        shadow_tests: list[dict],
        evaluations: list[dict],
        proposals: list[dict],
        selector: str = "",
    ) -> dict:
        shadow_test = self._select_shadow_test(shadow_tests, selector)
        if shadow_test is None:
            return {"ok": False, "reason": "no passed shadow test found"}
        if str(shadow_test.get("result", "")).strip().lower() != "pass":
            return {"ok": False, "reason": "shadow test result is not pass"}

        plans = self.list_patch_plans()
        existing = self._find_existing_plan(plans, shadow_test)
        if existing is not None:
            return {"ok": True, "patch_plan": existing, "reused": True}

        evaluation = self._find_evaluation(evaluations, shadow_test)
        proposal = self._find_proposal(proposals, shadow_test)
        patch_plan = self._build_patch_plan(shadow_test, evaluation, proposal)
        plans.append(patch_plan)
        safe_write_json(self.patch_plans_file, plans, backup=True)
        return {"ok": True, "patch_plan": patch_plan, "reused": False}

    def _select_shadow_test(self, shadow_tests: list[dict], selector: str) -> dict | None:
        cleaned = str(selector or "").strip()
        if cleaned:
            if cleaned.isdigit():
                index = int(cleaned) - 1
                if 0 <= index < len(shadow_tests):
                    return shadow_tests[index]
            for shadow_test in shadow_tests:
                if str(shadow_test.get("shadow_test_id", "")).startswith(cleaned):
                    return shadow_test
                if str(shadow_test.get("proposal_id", "")).startswith(cleaned):
                    return shadow_test
                if str(shadow_test.get("evaluation_id", "")).startswith(cleaned):
                    return shadow_test
            return None
        for shadow_test in reversed(shadow_tests):
            if str(shadow_test.get("result", "")).strip().lower() == "pass":
                return shadow_test
        return None

    def _find_existing_plan(self, plans: list[dict], shadow_test: dict) -> dict | None:
        shadow_id = str(shadow_test.get("shadow_test_id", "")).strip()
        title = self._normalize_match_text(shadow_test.get("proposal_title", ""))
        for plan in reversed(plans):
            if plan.get("stage") != PATCH_PIPELINE_STAGE:
                continue
            if shadow_id and str(plan.get("source_shadow_test_id", "")).strip() == shadow_id:
                return plan
            if title and self._normalize_match_text(plan.get("proposal_title", "")) == title:
                return plan
        return None

    def _find_evaluation(self, evaluations: list[dict], shadow_test: dict) -> dict | None:
        evaluation_id = str(shadow_test.get("evaluation_id", "")).strip()
        proposal_id = str(shadow_test.get("proposal_id", "")).strip()
        for evaluation in evaluations:
            if evaluation_id and str(evaluation.get("evaluation_id", "")) == evaluation_id:
                return evaluation
            if proposal_id and str(evaluation.get("proposal_id", "")) == proposal_id:
                return evaluation
        return None

    def _find_proposal(self, proposals: list[dict], shadow_test: dict) -> dict | None:
        proposal_id = str(shadow_test.get("proposal_id", "")).strip()
        title = self._normalize_match_text(shadow_test.get("proposal_title", ""))
        for proposal in proposals:
            if proposal_id and str(proposal.get("proposal_id", "")) == proposal_id:
                return proposal
            if title and self._normalize_match_text(proposal.get("title", "")) == title:
                return proposal
        return None

    def _build_patch_plan(self, shadow_test: dict, evaluation: dict | None, proposal: dict | None) -> dict:
        blocked_reasons: list[str] = []
        if evaluation is None:
            blocked_reasons.append("matching evaluation not found")
        if proposal is None:
            blocked_reasons.append("matching growth proposal not found")

        suggested_files = self._suggested_files(proposal)
        text = " ".join(
            [
                str(shadow_test.get("proposal_title", "")),
                " ".join(suggested_files),
                str(proposal.get("reason", "") if proposal else ""),
                str(proposal.get("evidence_summary", "") if proposal else ""),
            ]
        ).lower()
        if any(term in text for term in PROVIDER_TERMS):
            blocked_reasons.append("provider/API work request")
        if any(phrase in text for phrase in FORBIDDEN_PATCH_PLAN_PHRASES):
            blocked_reasons.append("fake-consciousness language")
        if "stage 18" in text or "stage18" in text or "experience storage" in text:
            blocked_reasons.append("roadmap jump request")

        status = "planned" if not blocked_reasons else "needs_review"
        patch_plan = {
            "patch_plan_id": f"pp_{uuid.uuid4().hex[:12]}",
            "created_at": _now(),
            "stage": PATCH_PIPELINE_STAGE,
            "source_proposal_id": str(shadow_test.get("proposal_id", "")),
            "source_evaluation_id": str(shadow_test.get("evaluation_id", "")),
            "source_shadow_test_id": str(shadow_test.get("shadow_test_id", "")),
            "proposal_title": str(shadow_test.get("proposal_title", "")).strip(),
            "status": status,
            "approval_required": True,
            "real_patching_enabled": False,
            "implementation_allowed": False,
            "suggested_files": suggested_files,
            "safety_checks": list(SAFETY_CHECKS),
            "blocked_reasons": blocked_reasons,
            "not_implemented": list(NOT_IMPLEMENTED),
        }
        return {field: patch_plan[field] for field in PATCH_PLAN_FIELDS}

    def _suggested_files(self, proposal: dict | None) -> list[str]:
        if proposal is None:
            return []
        possible_files = proposal.get("possible_files", [])
        if not isinstance(possible_files, list):
            return []
        files = []
        for item in possible_files:
            text = str(item or "").strip()
            if text and text not in files:
                files.append(text)
        return files

    def _sanitize_patch_plan(self, patch_plan: dict) -> dict:
        default = self._default_empty_patch_plan()
        data = dict(default)
        for field in PATCH_PLAN_FIELDS:
            if field in patch_plan:
                data[field] = patch_plan[field]
        data["stage"] = PATCH_PIPELINE_STAGE
        if data["status"] not in VALID_PATCH_PLAN_STATUSES:
            data["status"] = "needs_review"
        data["approval_required"] = True
        data["real_patching_enabled"] = False
        data["implementation_allowed"] = False
        if not isinstance(data["suggested_files"], list):
            data["suggested_files"] = []
        if not isinstance(data["safety_checks"], list):
            data["safety_checks"] = list(SAFETY_CHECKS)
        if not isinstance(data["blocked_reasons"], list):
            data["blocked_reasons"] = []
        if not isinstance(data["not_implemented"], list):
            data["not_implemented"] = list(NOT_IMPLEMENTED)
        return {field: data[field] for field in PATCH_PLAN_FIELDS}

    def _default_empty_patch_plan(self) -> dict:
        return {
            "patch_plan_id": "",
            "created_at": "",
            "stage": PATCH_PIPELINE_STAGE,
            "source_proposal_id": "",
            "source_evaluation_id": "",
            "source_shadow_test_id": "",
            "proposal_title": "",
            "status": "needs_review",
            "approval_required": True,
            "real_patching_enabled": False,
            "implementation_allowed": False,
            "suggested_files": [],
            "safety_checks": list(SAFETY_CHECKS),
            "blocked_reasons": [],
            "not_implemented": list(NOT_IMPLEMENTED),
        }

    def _normalize_match_text(self, value: object) -> str:
        return " ".join(str(value or "").strip().lower().split())
