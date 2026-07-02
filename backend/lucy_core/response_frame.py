"""
response_frame.py
Internal structured response frame for Lucy Stage 6.

User-facing output can stay simple while the runtime keeps route, context, and
safety metadata clear.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
import re


SECRET_PATTERNS = [
    r"api[_ -]?key\s*[:=]\s*['\"]?[^'\"\s]+",
    r"password\s*[:=]\s*\S+",
    r"sk-[A-Za-z0-9_\-]{12,}",
    r"gsk_[A-Za-z0-9_\-]+",
    r"AIza[A-Za-z0-9_\-]+",
]


@dataclass
class ResponseFrame:
    route: str
    user_intent: str
    visible_answer: str
    context_summary: dict[str, Any] = field(default_factory=dict)
    safety_status: dict[str, Any] = field(default_factory=dict)
    uncertainty: str = ""
    next_action: str = ""
    memory_update_recommendation: str = ""
    tool_recommendation: str = ""
    requires_confirmation: bool = False
    blocked_reason: str = ""
    hidden_reasoning_output: bool = False
    route_decision: dict[str, Any] = field(default_factory=dict)
    context_used: list[str] = field(default_factory=list)
    answer: str = ""
    tool_action_recommendation: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def build_response_frame(
    user_intent: str,
    route_decision: dict[str, Any],
    context_used: list[str] | None = None,
    context_summary: dict[str, Any] | None = None,
    safety_status: dict[str, Any] | None = None,
    answer: str = "",
    visible_answer: str = "",
    uncertainty: str = "",
    next_action: str = "",
    memory_update_recommendation: str = "",
    tool_action_recommendation: str = "",
    tool_recommendation: str = "",
    requires_confirmation: bool | None = None,
    blocked_reason: str = "",
) -> dict:
    route = route_decision.get("decision", "UNKNOWN")
    final_answer = _visible_answer_for_route(route, visible_answer or answer, blocked_reason, uncertainty)
    final_tool_recommendation = tool_recommendation or tool_action_recommendation
    return ResponseFrame(
        route=route,
        user_intent=_safe_text(user_intent, 300),
        visible_answer=final_answer,
        context_summary=context_summary or {},
        safety_status=safety_status or {},
        uncertainty=uncertainty,
        next_action=next_action or _next_action_for_route(route),
        memory_update_recommendation=memory_update_recommendation or "No automatic memory update.",
        tool_recommendation=final_tool_recommendation or "No automatic tool action.",
        requires_confirmation=(
            bool(requires_confirmation)
            if requires_confirmation is not None
            else bool(route_decision.get("requires_confirmation") or route_decision.get("tool_required"))
        ),
        blocked_reason=blocked_reason,
        hidden_reasoning_output=False,
        route_decision=route_decision,
        context_used=context_used or [],
        answer=final_answer,
        tool_action_recommendation=final_tool_recommendation or "No automatic tool action.",
    ).to_dict()


def _visible_answer_for_route(route: str, answer: str, blocked_reason: str, uncertainty: str) -> str:
    if route == "BLOCKED_BY_GUARDIAN":
        return f"Blocked by Guardian: {blocked_reason or 'protected action'}."
    if route == "CLARIFICATION_REQUIRED":
        return uncertainty or "I need one clearer question before I can route this safely."
    if answer:
        return answer
    return "Route preview only. Lucy did not execute tools, read files, or call APIs."


def _safe_text(value: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(value)).strip()
    for pattern in SECRET_PATTERNS:
        text = re.sub(pattern, "[redacted-secret]", text, flags=re.IGNORECASE)
    if any(word in text.lower() for word in ["api key", "password", "private key", "secret", "token"]):
        return "[redacted-sensitive-input]"
    return text[:limit]


def _next_action_for_route(route: str) -> str:
    if route == "CLARIFICATION_REQUIRED":
        return "Ask one specific clarification question."
    if route == "BLOCKED_BY_GUARDIAN":
        return "Stop and do not proceed with the protected action."
    if route == "SAFE_FILE_READ_CONTEXT":
        return "Use Stage 5 safe file commands only after approved-folder checks."
    if route == "REASONING_MODE_RECOMMENDED":
        return "Use local structured planning with safe summaries."
    return "Handle locally using the selected route."
