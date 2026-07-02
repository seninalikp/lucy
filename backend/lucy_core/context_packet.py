"""
context_packet.py
Safe local context packet builder for Lucy Stage 6 FULL.

Packets contain summaries only. They exclude secrets, raw private files, raw
memory dumps, and hidden reasoning.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any


DEFAULT_CONTEXT_PACKET_MAX_CHARS = 6000

SECRET_PATTERNS = [
    r"api[_ -]?key\s*[:=]\s*['\"]?[^'\"\s]+",
    r"password\s*[:=]\s*\S+",
    r"sk-[A-Za-z0-9_\-]{12,}",
    r"gsk_[A-Za-z0-9_\-]+",
    r"AIza[A-Za-z0-9_\-]+",
    r"-----BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY-----",
]

SECRET_WORDS = {
    "api key",
    "apikey",
    "credential",
    "password",
    "private key",
    "secret",
    "seed phrase",
    "token",
    "wallet",
}


@dataclass
class ContextPacket:
    active_project_name: str = "Lucy"
    current_checkpoint: str = ""
    next_action: str = ""
    last_command_summary: str = ""
    memory_recall_summaries: list[dict[str, Any]] = field(default_factory=list)
    daily_context_summary: dict[str, Any] = field(default_factory=dict)
    safe_file_summary: dict[str, Any] = field(default_factory=dict)
    guardian_status: dict[str, Any] = field(default_factory=dict)
    route_decision: dict[str, Any] = field(default_factory=dict)
    hidden_reasoning_output: bool = False
    max_chars: int = DEFAULT_CONTEXT_PACKET_MAX_CHARS

    def to_dict(self) -> dict:
        return asdict(self)


class ContextPacketBuilder:
    def __init__(self, runtime=None, max_chars: int = DEFAULT_CONTEXT_PACKET_MAX_CHARS) -> None:
        self.runtime = runtime
        self.max_chars = max_chars

    def build(
        self,
        user_text: str,
        route_decision: dict[str, Any],
        safe_file_summary: dict[str, Any] | None = None,
    ) -> dict:
        project = self._project_summary()
        session = self._session_status()
        packet = ContextPacket(
            active_project_name=self._clean(project.get("name", "Lucy"), 80),
            current_checkpoint=self._clean(session.get("current_checkpoint", ""), 120),
            next_action=self._clean(project.get("next_action", ""), 240),
            last_command_summary=self._clean(session.get("last_command", ""), 240),
            memory_recall_summaries=self._memory_summaries(user_text),
            daily_context_summary=self._daily_summary(),
            safe_file_summary=self._safe_file_summary(safe_file_summary or {}),
            guardian_status=self._guardian_summary(),
            route_decision=self._route_summary(route_decision),
            hidden_reasoning_output=False,
            max_chars=self.max_chars,
        ).to_dict()
        return self._cap_packet(packet)

    def _project_summary(self) -> dict:
        if self.runtime is None:
            return {}
        try:
            return self.runtime.project_summary()
        except Exception:
            return {}

    def _session_status(self) -> dict:
        if self.runtime is None:
            return {}
        try:
            return self.runtime.session_state.status()
        except Exception:
            return {}

    def _memory_summaries(self, user_text: str) -> list[dict[str, Any]]:
        if self.runtime is None:
            return []
        try:
            memories = self.runtime.recall(user_text, limit=5)
        except Exception:
            return []
        summaries = []
        for item in memories[:5]:
            summaries.append(
                {
                    "id": self._clean(item.get("id", ""), 40),
                    "type": self._clean(item.get("type") or item.get("category", "general"), 60),
                    "summary": self._clean(item.get("fact", ""), 220),
                }
            )
        return summaries

    def _daily_summary(self) -> dict[str, Any]:
        if self.runtime is None:
            return {}
        try:
            daily = self.runtime.daily_context.brief_context()
        except Exception:
            return {}
        return {
            "date": self._clean(daily.get("date", ""), 40),
            "has_today_log": bool(daily.get("has_today_log")),
            "energy": daily.get("energy"),
            "sleep_status": self._clean(daily.get("sleep_status", ""), 120),
            "main_project_today": self._clean(daily.get("main_project_today", ""), 120),
            "tomorrow_priority": self._clean(daily.get("tomorrow_priority", ""), 220),
            "notes": self._clean(daily.get("notes", ""), 220),
        }

    def _safe_file_summary(self, summary: dict[str, Any]) -> dict[str, Any]:
        if not summary:
            return {}
        allowed = {}
        for key in ["path", "relative_path", "name", "size", "extension", "truncated", "skipped", "match_count"]:
            if key in summary:
                value = summary[key]
                allowed[key] = self._clean(value, 180) if isinstance(value, str) else value
        return allowed

    def _guardian_summary(self) -> dict[str, Any]:
        if self.runtime is None:
            return {}
        try:
            status = self.runtime.guardian_status()
        except Exception:
            return {}
        return {
            "mode": self._clean(status.get("mode", ""), 80),
            "protected_actions_blocked": bool(status.get("protected_actions_blocked", True)),
            "root_access_enabled": bool(status.get("root_access_enabled", False)),
            "autonomy_enabled": bool(status.get("autonomy_enabled", False)),
            "agent_execution_enabled": bool(status.get("agent_execution_enabled", False)),
            "pending_approvals": int(status.get("pending_approvals", 0) or 0),
        }

    def _route_summary(self, decision: dict[str, Any]) -> dict[str, Any]:
        return {
            "decision": self._clean(decision.get("decision", ""), 80),
            "reason": self._clean(decision.get("reason", ""), 240),
            "required_context": [self._clean(item, 80) for item in decision.get("required_context", [])[:8]],
            "guardian_required": bool(decision.get("guardian_required")),
            "tool_required": bool(decision.get("tool_required")),
            "external_api_allowed": bool(decision.get("external_api_allowed", False)),
            "route_confidence": decision.get("route_confidence", decision.get("confidence")),
        }

    def _cap_packet(self, packet: dict) -> dict:
        text = repr(packet)
        if len(text) <= self.max_chars:
            return packet
        packet = dict(packet)
        packet["memory_recall_summaries"] = packet.get("memory_recall_summaries", [])[:2]
        packet["safe_file_summary"] = {"summary": "omitted because context packet reached size limit"}
        packet["packet_truncated"] = True
        return packet

    def _clean(self, value: Any, limit: int) -> str:
        text = re.sub(r"\s+", " ", str(value)).strip()
        lowered = text.lower()
        if any(word in lowered for word in SECRET_WORDS):
            return "[redacted-sensitive-context]"
        for pattern in SECRET_PATTERNS:
            text = re.sub(pattern, "[redacted-secret]", text, flags=re.IGNORECASE)
        return text[:limit]
