"""
Stage 18 experience storage.

Stores small, structured lessons from verified local project events only. It is
not raw memory, deep recall, identity stability, long-term strategy, or a diary.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from backend.lucy_core.safe_storage import safe_read_json, safe_write_json


EXPERIENCE_STAGE = "18 experience storage"
EXPERIENCE_RECORD_FIELDS = (
    "experience_id",
    "created_at",
    "stage",
    "source_stage",
    "event_type",
    "title",
    "summary",
    "lesson",
    "risk_noted",
    "future_rule",
    "confidence",
    "sensitivity",
    "approved_for_storage",
    "blocked_content",
    "not_implemented",
)
VALID_EVENT_TYPES = (
    "accepted_stage",
    "failed_test",
    "manual_check",
    "blocked_drift",
    "cleanup_patch",
    "patch_plan_created",
    "safety_rule_confirmed",
)
VALID_CONFIDENCE_VALUES = ("low", "medium", "high")
VALID_SENSITIVITY_VALUES = ("safe_project", "private_do_not_store", "secret_do_not_store")
NOT_IMPLEMENTED = ["deep recall", "identity stability", "long-term strategy"]
FORBIDDEN_EXPERIENCE_PHRASES = (
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
SECRET_PATTERNS = (
    re.compile(r"\bsk-[a-z0-9_-]{8,}", re.IGNORECASE),
    re.compile(r"\bghp_[a-z0-9_]{8,}", re.IGNORECASE),
    re.compile(r"\bAIza[a-z0-9_-]{8,}", re.IGNORECASE),
    re.compile(r"\b(api[_ -]?key|password|token|secret|private[_ -]?key)\s*[:=]\s*\S+", re.IGNORECASE),
)
SENSITIVE_TERMS = {
    "api key": "secret/API key/token",
    "apikey": "secret/API key/token",
    "password": "secret/API key/token",
    "token": "secret/API key/token",
    "secret": "secret/API key/token",
    "private key": "secret/API key/token",
    "seed phrase": "secret/API key/token",
    "otp": "secret/API key/token",
    "provider credential": "secret/API key/token",
    "provider credentials": "secret/API key/token",
    "nvidia key": "secret/API key/token",
    "groq key": "secret/API key/token",
    "gemini key": "secret/API key/token",
    "openrouter key": "secret/API key/token",
    "raw chat log": "raw chat log",
    "full chat log": "raw chat log",
    "chat transcript": "raw chat log",
    "private diary": "private diary",
    "dear diary": "private diary",
    "diary entry": "private diary",
    "bank account": "bank/payment data",
    "payment card": "bank/payment data",
    "credit card": "bank/payment data",
    "romantic relationship": "private relationship history",
    "private relationship": "private relationship history",
    "medical record": "medical/mental-health detail",
    "mental health": "medical/mental-health detail",
    "exact address": "exact address",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExperienceStorage:
    def __init__(self, lucy_data_dir: Path) -> None:
        self.lucy_data_dir = lucy_data_dir
        self.records_file = lucy_data_dir / "experience_records.json"

    def status(self) -> dict:
        records = self.list_experiences()
        return {
            "stage": EXPERIENCE_STAGE,
            "experience_storage": "active",
            "experience_records": len(records),
            "stores_raw_chat_logs": "no",
            "stores_secrets": "no",
            "deep_recall": "not implemented",
            "identity_stability": "not implemented",
            "long_term_strategy": "not implemented",
            "approval_required_for_sensitive_storage": True,
            "file": str(self.records_file),
            "latest_record": records[-1] if records else None,
        }

    def list_experiences(self) -> list[dict]:
        data = safe_read_json(self.records_file, [])
        if not isinstance(data, list):
            return []
        records = []
        for item in data:
            if isinstance(item, dict):
                records.append(self._sanitize_record(item, for_listing=True))
        return records

    def record_stage_experience(self) -> dict:
        return self.record_experience(self._default_stage_record())

    def record_experience(self, candidate: dict | None = None) -> dict:
        record = self._sanitize_record(candidate or self._default_stage_record())
        blocked_content = self._blocked_content(record)
        if blocked_content:
            return {
                "ok": False,
                "stored": False,
                "reused": False,
                "reason": "content blocked by experience storage policy",
                "blocked_content": blocked_content,
            }

        records = self.list_experiences()
        existing = self._find_existing_record(records, record)
        if existing is not None:
            return {"ok": True, "stored": True, "reused": True, "experience_record": existing}

        records.append(record)
        safe_write_json(self.records_file, records, backup=True)
        return {"ok": True, "stored": True, "reused": False, "experience_record": record}

    def _sanitize_record(self, record: dict, for_listing: bool = False) -> dict:
        default = self._default_empty_record()
        data = dict(default)
        for field in EXPERIENCE_RECORD_FIELDS:
            if field in record:
                data[field] = record[field]

        data["experience_id"] = str(data.get("experience_id") or f"ex_{uuid.uuid4().hex[:12]}")
        data["created_at"] = str(data.get("created_at") or _now())
        data["stage"] = EXPERIENCE_STAGE

        event_type = str(data.get("event_type") or "").strip()
        data["event_type"] = event_type if event_type in VALID_EVENT_TYPES else "safety_rule_confirmed"

        confidence = str(data.get("confidence") or "").strip()
        data["confidence"] = confidence if confidence in VALID_CONFIDENCE_VALUES else "medium"

        sensitivity = str(data.get("sensitivity") or "").strip()
        data["sensitivity"] = sensitivity if sensitivity in VALID_SENSITIVITY_VALUES else "private_do_not_store"

        data["approved_for_storage"] = bool(data.get("approved_for_storage") is True)
        for field in ("source_stage", "title", "summary", "lesson", "risk_noted", "future_rule"):
            data[field] = self._safe_text(data.get(field, ""))

        blocked_content = data.get("blocked_content", [])
        if not isinstance(blocked_content, list):
            blocked_content = []
        data["blocked_content"] = [self._safe_text(item) for item in blocked_content]

        data["not_implemented"] = list(NOT_IMPLEMENTED)
        if for_listing and data["sensitivity"] != "safe_project":
            data["blocked_content"] = ["non-safe sensitivity record sanitized"]
        return {field: data[field] for field in EXPERIENCE_RECORD_FIELDS}

    def _blocked_content(self, record: dict) -> list[str]:
        reasons: list[str] = []
        if record.get("sensitivity") != "safe_project":
            reasons.append(str(record.get("sensitivity") or "non-safe sensitivity"))
        if record.get("approved_for_storage") is not True:
            reasons.append("approval missing")

        text = " ".join(
            str(record.get(field, ""))
            for field in ("source_stage", "title", "summary", "lesson", "risk_noted", "future_rule")
        ).lower()
        for phrase in FORBIDDEN_EXPERIENCE_PHRASES:
            if phrase in text:
                reasons.append("fake-consciousness language")
                break
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                reasons.append("secret/API key/token")
                break
        for term, reason in SENSITIVE_TERMS.items():
            if term in text:
                reasons.append(reason)
        return self._unique(reasons)

    def _find_existing_record(self, records: list[dict], record: dict) -> dict | None:
        source_stage = self._normalize_match_text(record.get("source_stage", ""))
        event_type = str(record.get("event_type", "")).strip()
        title = self._normalize_match_text(record.get("title", ""))
        for existing in reversed(records):
            if existing.get("stage") != EXPERIENCE_STAGE:
                continue
            if (
                self._normalize_match_text(existing.get("source_stage", "")) == source_stage
                and str(existing.get("event_type", "")).strip() == event_type
                and self._normalize_match_text(existing.get("title", "")) == title
            ):
                return existing
        return None

    def _default_stage_record(self) -> dict:
        return {
            "source_stage": "17 approved patch pipeline",
            "event_type": "accepted_stage",
            "title": "Stage 17 approved patch pipeline accepted",
            "summary": "Stage 17 added approval-required patch plan records from passed shadow tests only.",
            "lesson": "Patch plans must require approval and must not apply code automatically.",
            "risk_noted": "self-modification drift",
            "future_rule": "Keep real patching disabled unless an approved later workflow allows it.",
            "confidence": "high",
            "sensitivity": "safe_project",
            "approved_for_storage": True,
        }

    def _default_empty_record(self) -> dict:
        return {
            "experience_id": "",
            "created_at": "",
            "stage": EXPERIENCE_STAGE,
            "source_stage": "",
            "event_type": "manual_check",
            "title": "",
            "summary": "",
            "lesson": "",
            "risk_noted": "",
            "future_rule": "",
            "confidence": "medium",
            "sensitivity": "safe_project",
            "approved_for_storage": False,
            "blocked_content": [],
            "not_implemented": list(NOT_IMPLEMENTED),
        }

    def _safe_text(self, value: object, limit: int = 500) -> str:
        text = " ".join(str(value or "").split())
        return text[:limit]

    def _normalize_match_text(self, value: object) -> str:
        return " ".join(str(value or "").strip().lower().split())

    def _unique(self, items: list[str]) -> list[str]:
        unique = []
        for item in items:
            if item and item not in unique:
                unique.append(item)
        return unique
