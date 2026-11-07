"""
workflow_learner.py
Stage 56 = Behavioral Correction & Workflow Habit Learner.

Makes Lucy genuinely adaptive to Senin's corrections and operational habits:
1. Correction Detector: Recognizes when Senin corrects Lucy ("no, don't...",
   "stop doing...", "wrong, use X instead of Y") and records a permanent
   Behavioral Guardrail Rule injected into all future prompts.
2. Habit / Sequence Detector: Observes command sequences and allows 1-command
   macro creation (`macro <name> = <cmd1> ; <cmd2>`) so repetitive workflows
   become single-word triggers.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STAGE = "56 behavioral correction and workflow learner"

CORRECTION_PATTERNS = [
    r"^(?:no[,.\s]+|wrong[,.\s]+|stop\s+)(?:don't|do\s+not|never)\s+([^.!?\n]{6,180})",
    r"\b(?:don't\s+ever|never\s+again|stop\s+giving\s+me|stop\s+using|do\s+not\s+ever)\s+([^.!?\n]{5,180})",
    r"\b(?:instead\s+of\s+[^,]+,\s*(?:always\s+)?use\s+[^.!?\n]{4,140})",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkflowHabitLearner:
    def __init__(self, lucy_data: Path) -> None:
        self.lucy_data = Path(lucy_data)
        self.file = self.lucy_data / "workflow_adaptation.json"
        self.lucy_data.mkdir(parents=True, exist_ok=True)
        self._ensure_file()

    def _default_data(self) -> dict[str, Any]:
        return {
            "version": "1.0.0",
            "correction_rules": [
                "Never output truncated code or placeholder comments when writing implementation files.",
                "Never claim a file or task was modified without executing the underlying tool.",
            ],
            "macros": {
                "morning": ["brief me", "workspace pulse"],
                "checkup": ["health", "workspace pulse", "schedules"],
            },
            "recent_command_chain": [],
            "updated_at": _now(),
        }

    def _ensure_file(self) -> None:
        if not self.file.exists():
            self._write(self._default_data())

    def _read(self) -> dict[str, Any]:
        try:
            data = json.loads(self.file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                default = self._default_data()
                for k, v in default.items():
                    data.setdefault(k, v)
                return data
        except Exception:
            pass
        return self._default_data()

    def _write(self, data: dict[str, Any]) -> None:
        data["updated_at"] = _now()
        self.file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def observe_for_corrections(self, user_text: str) -> dict[str, Any]:
        raw = str(user_text or "").strip()
        learned: list[str] = []
        data = self._read()
        rules = data.setdefault("correction_rules", [])

        for pattern in CORRECTION_PATTERNS:
            m = re.search(pattern, raw, re.IGNORECASE)
            if m:
                rule_text = f"User Correction Guardrail: {raw[:180]}"
                if rule_text not in rules:
                    rules.append(rule_text)
                    data["correction_rules"] = rules[-30:]
                    learned.append(rule_text)

        if learned:
            self._write(data)
        return {"correction_detected": bool(learned), "rules_added": learned}

    def save_macro(self, name: str, steps: list[str]) -> dict[str, Any]:
        clean_name = name.strip().lower()
        clean_steps = [s.strip() for s in steps if s.strip()]
        if not clean_name or not clean_steps:
            return {"ok": False, "reason": "Macro name and steps required."}
        data = self._read()
        data.setdefault("macros", {})[clean_name] = clean_steps
        self._write(data)
        return {"ok": True, "macro": clean_name, "steps": clean_steps}

    def get_macro(self, name: str) -> list[str] | None:
        data = self._read()
        return data.get("macros", {}).get(name.strip().lower())

    def prompt_guardrails_block(self) -> str:
        data = self._read()
        rules = data.get("correction_rules", [])[-8:]
        if not rules:
            return ""
        formatted = "\n".join(f"- {r}" for r in rules)
        return f"[Enforced Behavioral Corrections (Stage 56)]:\n{formatted}"

    def status(self) -> dict[str, Any]:
        data = self._read()
        return {
            "stage": STAGE,
            "workflow_learner": "active",
            "correction_rules_count": len(data.get("correction_rules", [])),
            "macros": data.get("macros", {}),
        }
