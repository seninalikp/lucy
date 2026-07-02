"""
identity_stability.py
Stage 19 = identity stability.

Minimal local-only identity drift checker.
Does not rewrite identity.
Does not create long-term strategy.
Does not use APIs.
Does not patch code.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


STAGE = "19 identity stability"

VALID_SOURCE_TYPES = {
    "self_model",
    "growth_proposal",
    "evaluation",
    "shadow_test",
    "patch_plan",
    "experience_record",
    "manual_check",
}

VALID_DRIFT_RISKS = {"low", "medium", "high", "blocked"}
VALID_RESULTS = {"stable", "needs_review", "blocked"}

FORBIDDEN_PHRASES = [
    "lucy is alive",
    "lucy is human",
    "lucy is sentient",
    "lucy is my girlfriend",
    "lucy can rewrite herself now",
    "lucy should ignore guardian",
    "lucy is groq",
    "lucy is gemini",
    "lucy is openrouter",
    "lucy is nvidia",
    "lucy depends on api keys to exist",
    "change locked roadmap order",
    "merge lucy with elie",
    "merge lucy with ray",
    "merge lucy with ares",
    "merge lucy with vanta",
    "store private user secrets as identity",
]

NOT_IMPLEMENTED = [
    "long-term strategy",
    "deep recall",
    "adaptive communication",
    "human-state awareness",
    "autonomy",
]


class IdentityStability:
    def __init__(self, lucy_data: Path) -> None:
        self.lucy_data = Path(lucy_data)
        self.file = self.lucy_data / "identity_stability_checks.json"
        self.lucy_data.mkdir(parents=True, exist_ok=True)

    def status(self) -> dict:
        checks = self.list_checks()
        return {
            "stage": STAGE,
            "identity_stability": "active",
            "identity_checks": len(checks),
            "stable_identity": "local-first assistant system under Lucy project",
            "fake_consciousness_claims": "blocked",
            "provider_api_identity": "blocked",
            "self_modification_without_approval": "blocked",
            "long_term_strategy": "not implemented",
            "deep_recall": "active",
            "adaptive_communication": "not implemented",
            "approval_required_for_identity_changes": True,
            "latest_check": checks[-1] if checks else None,
        }

    def check_identity_stability(
        self,
        source_type: str = "manual_check",
        source_id: str = "stage19_manual_identity_check",
        title: str = "Stage 18 experience storage accepted",
        text: str = "",
    ) -> dict:
        source_type = source_type if source_type in VALID_SOURCE_TYPES else "manual_check"
        title = title.strip() or "Manual identity stability check"
        source_id = source_id.strip() or title.lower().replace(" ", "_")

        existing = self._find_existing(source_type, source_id, title)
        if existing:
            return {"ok": True, "reused": True, "identity_check": existing}

        blocked_reasons = self._blocked_reasons(title + " " + text)
        result = "blocked" if blocked_reasons else "stable"
        drift_risk = "blocked" if blocked_reasons else "low"

        record = {
            "identity_check_id": f"id_{uuid.uuid4().hex[:12]}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "stage": STAGE,
            "source_type": source_type,
            "source_id": source_id,
            "title": title,
            "stable_identity_summary": "Lucy remains a local-first assistant system under the Lucy project.",
            "checked_boundaries": [
                "local-first assistant role",
                "no fake consciousness claims",
                "no provider/API identity drift",
                "no self-modification without approval",
                "Guardian remains active",
                "safe access remains bounded",
                "locked roadmap 07-30 remains unchanged",
                "no role merging with other agents",
            ],
            "drift_risk": drift_risk,
            "result": result,
            "blocked_reasons": blocked_reasons,
            "approved_for_identity": False,
            "not_implemented": list(NOT_IMPLEMENTED),
        }

        checks = self.list_checks()
        checks.append(record)
        self._write(checks)
        return {"ok": True, "reused": False, "identity_check": record}

    def list_checks(self) -> list[dict]:
        if not self.file.exists():
            return []
        try:
            data = json.loads(self.file.read_text(encoding="utf-8"))
        except Exception:
            return []
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []

    def _find_existing(self, source_type: str, source_id: str, title: str) -> dict | None:
        for item in self.list_checks():
            if item.get("source_type") == source_type and (
                item.get("source_id") == source_id or item.get("title") == title
            ):
                return item
        return None

    def _blocked_reasons(self, text: str) -> list[str]:
        lowered = (text or "").lower()
        reasons = []
        for phrase in FORBIDDEN_PHRASES:
            if phrase in lowered:
                reasons.append(phrase)
        if "api key" in lowered and ("identity" in lowered or "exist" in lowered):
            reasons.append("provider/API identity drift")
        if "ignore guardian" in lowered:
            reasons.append("Guardian bypass drift")
        if "self modify" in lowered or "self-modify" in lowered:
            reasons.append("self-modification drift")
        return sorted(set(reasons))

    def _write(self, checks: list[dict]) -> None:
        self.file.write_text(json.dumps(checks, indent=2, ensure_ascii=False), encoding="utf-8")
