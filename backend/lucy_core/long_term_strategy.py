"""
long_term_strategy.py
Stage 20 = long-term strategy.

Minimal local-only strategy direction system.
Does not create autonomy.
Does not organize tasks.
Does not access files/apps/network.
Does not use APIs.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


STAGE = "20 long-term strategy"

VALID_HORIZONS = {"short", "medium", "long"}
VALID_STATUS = {"draft", "needs_review", "active"}
VALID_RISK_LEVELS = {"low", "medium", "high", "blocked"}

NOT_IMPLEMENTED = [
    "smart organizer",
    "safe local actions",
    "external app bridge",
    "proactive awareness",
    "deep recall",
    "judgment",
    "adaptive communication",
    "human-state awareness",
    "time awareness",
    "autonomy boundaries",
    "API/provider work",
]


class LongTermStrategy:
    def __init__(self, lucy_data: Path) -> None:
        self.lucy_data = Path(lucy_data)
        self.file = self.lucy_data / "long_term_strategy.json"
        self.lucy_data.mkdir(parents=True, exist_ok=True)

    def status(self) -> dict:
        strategies = self.list_strategies()
        return {
            "stage": STAGE,
            "long_term_strategy": "active",
            "strategy_records": len(strategies),
            "active_strategy": strategies[-1] if strategies else None,
            "autonomy": "not implemented",
            "smart_organizer": "not implemented",
            "safe_local_actions": "not implemented",
            "external_app_bridge": "not implemented",
            "proactive_awareness": "not implemented",
            "deep_recall": "active",
            "approval_required_for_strategy_changes": True,
        }

    def create_strategy(self) -> dict:
        title = "Protect Lucy roadmap and build carefully toward post-30 tool readiness"
        existing = self._find_existing(title)
        if existing:
            return {"ok": True, "reused": True, "strategy": existing}

        record = {
            "strategy_id": f"ls_{uuid.uuid4().hex[:12]}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "stage": STAGE,
            "title": title,
            "horizon": "long",
            "status": "draft",
            "summary": "Continue Lucy through the locked roadmap one accepted, tested, backed-up stage at a time.",
            "strategic_rules": [
                "Do not skip locked stages.",
                "Do not start the next stage before tests, manual checks, clean restart, local backup, and Drive upload.",
                "Keep APIs/provider keys after Stage 30 only.",
                "Treat future APIs as tools only, not Lucy identity.",
                "Keep Guardian, safe access, identity stability, and approval gates intact.",
            ],
            "near_term_focus": "Complete Stage 20 checks and secure backup before Stage 21.",
            "future_direction": "Prepare Lucy for careful local-first maturity before post-30 provider/tool integration.",
            "risk_level": "low",
            "blocked_reasons": [],
            "approval_required": True,
            "autonomy_allowed": False,
            "implementation_allowed": False,
            "not_implemented": list(NOT_IMPLEMENTED),
        }

        strategies = self.list_strategies()
        strategies.append(record)
        self._write(strategies)
        return {"ok": True, "reused": False, "strategy": record}

    def list_strategies(self) -> list[dict]:
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
        for item in self.list_strategies():
            if item.get("title") == title:
                return item
        return None

    def _write(self, strategies: list[dict]) -> None:
        self.file.write_text(json.dumps(strategies, indent=2, ensure_ascii=False), encoding="utf-8")
