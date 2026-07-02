"""
deep_recall.py
Stage 25 = deep recall.

This stage searches Lucy's own safe structured records only.
It does not read raw chat logs.
It does not read secrets, .env files, API keys, passwords, tokens, or private keys.
It does not use network/API/provider keys.
It does not access browser, phone, WhatsApp, Instagram, or Chrome.
It does not monitor in the background.
It does not take actions.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


STAGE = "25 deep recall"

SAFE_SOURCE_FILES = [
    "experience_storage.json",
    "identity_stability_checks.json",
    "long_term_strategy.json",
    "smart_organizer.json",
    "safe_local_actions.json",
    "external_app_bridge.json",
    "proactive_awareness.json",
]

BLOCKED_SOURCE_FILES = [
    "raw chat logs",
    "secrets",
    ".env",
    "api keys",
    "passwords",
    "tokens",
    "private keys",
    "wallets",
    "browser data",
    "phone data",
    "WhatsApp data",
    "Instagram data",
    "Chrome data",
]

NOT_IMPLEMENTED = [
    "raw chat log recall",
    "secret recall",
    "whole computer search",
    "browser recall",
    "phone recall",
    "external app recall",
    "network access",
    "API/provider keys",
    "background monitoring",
    "automatic notifications",
    "judgment",
    "adaptive communication",
    "human-state awareness",
    "time awareness",
    "autonomy boundaries",
]


class DeepRecall:
    def __init__(self, lucy_data: Path) -> None:
        self.lucy_data = Path(lucy_data)
        self.file = self.lucy_data / "deep_recall.json"
        self.lucy_data.mkdir(parents=True, exist_ok=True)

    def status(self) -> dict:
        sessions = self.list_recall_sessions()
        return {
            "stage": STAGE,
            "deep_recall": "active",
            "recall_sessions": len(sessions),
            "execution_mode": "manual_structured_recall_only",
            "safe_sources": list(SAFE_SOURCE_FILES),
            "blocked_sources": list(BLOCKED_SOURCE_FILES),
            "raw_chat_logs": "blocked",
            "secrets": "blocked",
            "whole_computer_search": "blocked",
            "network_access": "blocked",
            "api_provider_keys": "blocked",
            "background_monitoring": "blocked",
            "real_actions": False,
            "approval_required": True,
            "autonomy": "not implemented",
        }

    def create_recall_session(self, query: str | None = None) -> dict:
        clean_query = self._clean_query(query)
        title = f"Stage 25 safe deep recall session: {clean_query}"
        existing = self._find_existing(title)
        if existing:
            return {"ok": True, "reused": True, "recall": existing}

        matches = self._collect_matches(clean_query)
        recall = {
            "recall_session_id": f"dr_{uuid.uuid4().hex[:12]}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "stage": STAGE,
            "title": title,
            "query": clean_query,
            "recall_type": "safe_structured_records",
            "status": "observed",
            "summary": self._summary(clean_query, matches),
            "safe_sources_checked": list(SAFE_SOURCE_FILES),
            "blocked_sources": list(BLOCKED_SOURCE_FILES),
            "matches": matches,
            "match_count": len(matches),
            "requires_approval": True,
            "dry_run_only": True,
            "raw_chat_logs_allowed": False,
            "secrets_allowed": False,
            "whole_computer_search_allowed": False,
            "network_allowed": False,
            "api_keys_allowed": False,
            "background_monitoring_allowed": False,
            "real_action_allowed": False,
            "blocked_until": "Stage 25 accepted, backed up locally, uploaded to Drive, and Senin explicitly approves Stage 26.",
            "not_implemented": list(NOT_IMPLEMENTED),
        }

        sessions = self.list_recall_sessions()
        sessions.append(recall)
        self._write(sessions)
        return {"ok": True, "reused": False, "recall": recall}

    def dry_run_deep_recall(self, query: str | None = None) -> dict:
        recall = self.create_recall_session(query=query)["recall"]
        return {
            "ok": True,
            "stage": STAGE,
            "dry_run_only": True,
            "would_read_raw_chat_logs": False,
            "would_read_secrets": False,
            "would_search_whole_computer": False,
            "would_use_network": False,
            "would_take_action": False,
            "real_action_allowed": False,
            "message": "Dry run complete. Only safe structured records were checked.",
            "recall": recall,
        }

    def list_recall_sessions(self) -> list[dict]:
        if not self.file.exists():
            return []
        try:
            data = json.loads(self.file.read_text(encoding="utf-8"))
        except Exception:
            return []
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []

    def _collect_matches(self, query: str) -> list[dict]:
        query_lower = query.lower()
        matches: list[dict] = []

        for filename in SAFE_SOURCE_FILES:
            source = self.lucy_data / filename
            if not source.exists():
                continue

            try:
                data = json.loads(source.read_text(encoding="utf-8"))
            except Exception:
                continue

            records = data if isinstance(data, list) else [data]
            for record in records:
                if not isinstance(record, dict):
                    continue

                record_text = json.dumps(record, ensure_ascii=False).lower()
                if query_lower == "stage status" or query_lower in record_text:
                    matches.append(
                        {
                            "source": filename,
                            "record_id": self._record_id(record),
                            "title": str(record.get("title", record.get("stage", "structured record")))[:160],
                            "stage": str(record.get("stage", ""))[:80],
                            "safe_excerpt": self._safe_excerpt(record),
                        }
                    )

        return matches[:10]

    def _summary(self, query: str, matches: list[dict]) -> str:
        if matches:
            return f"Found {len(matches)} safe structured record match(es) for: {query}."
        return f"No safe structured record matches found for: {query}."

    def _safe_excerpt(self, record: dict) -> str:
        preferred = [
            record.get("summary"),
            record.get("title"),
            record.get("stage"),
            record.get("status"),
        ]
        text = " | ".join(str(item) for item in preferred if item)
        return text[:240]

    def _record_id(self, record: dict) -> str:
        for key in [
            "experience_id",
            "identity_check_id",
            "strategy_id",
            "organizer_item_id",
            "safe_action_id",
            "bridge_id",
            "awareness_scan_id",
            "recall_session_id",
        ]:
            value = record.get(key)
            if value:
                return str(value)
        return "record"

    def _clean_query(self, query: str | None) -> str:
        value = (query or "stage status").strip()
        if not value:
            return "stage status"
        lowered = value.lower()
        for blocked in ["secret", "api key", ".env", "password", "token", "private key", "wallet"]:
            if blocked in lowered:
                return "blocked sensitive query"
        return value[:120]

    def _find_existing(self, title: str) -> dict | None:
        for session in self.list_recall_sessions():
            if session.get("title") == title:
                return session
        return None

    def _write(self, sessions: list[dict]) -> None:
        self.file.write_text(
            json.dumps(sessions, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
