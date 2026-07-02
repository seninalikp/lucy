"""
reasoning_policy.py
Stage 6 local reasoning router foundation for Lucy.

This module decides how a request should be handled. It does not execute tools,
read files, call APIs, or expose hidden reasoning.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


SIMPLE_LOCAL = "SIMPLE_LOCAL"
MEMORY_LOOKUP = "MEMORY_LOOKUP"
PROJECT_CONTEXT = "PROJECT_CONTEXT"
DAILY_CONTEXT = "DAILY_CONTEXT"
TOOL_CLASSIFICATION_ONLY = "TOOL_CLASSIFICATION_ONLY"
SAFE_FILE_READ_CONTEXT = "SAFE_FILE_READ_CONTEXT"
REASONING_MODE_RECOMMENDED = "REASONING_MODE_RECOMMENDED"
EXTERNAL_BRAIN_RECOMMENDED_BUT_DISABLED = "EXTERNAL_BRAIN_RECOMMENDED_BUT_DISABLED"
# Backward-compatible name used by the Stage 6 foundation tests.
EXTERNAL_BRAIN_DISABLED = EXTERNAL_BRAIN_RECOMMENDED_BUT_DISABLED
BLOCKED_BY_GUARDIAN = "BLOCKED_BY_GUARDIAN"
CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"

REASONING_CATEGORIES = [
    SIMPLE_LOCAL,
    MEMORY_LOOKUP,
    PROJECT_CONTEXT,
    DAILY_CONTEXT,
    TOOL_CLASSIFICATION_ONLY,
    SAFE_FILE_READ_CONTEXT,
    REASONING_MODE_RECOMMENDED,
    EXTERNAL_BRAIN_RECOMMENDED_BUT_DISABLED,
    BLOCKED_BY_GUARDIAN,
    CLARIFICATION_REQUIRED,
]


@dataclass
class ReasoningRequest:
    user_text: str
    runtime_context: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReasoningDecision:
    decision: str
    reason: str
    required_context: list[str]
    guardian_required: bool
    tool_required: bool
    external_api_allowed: bool
    intent_clarity: float
    context_availability: float
    safety_risk: float
    route_confidence: float
    confidence: float

    def to_dict(self) -> dict:
        return asdict(self)


class ReasoningPolicy:
    MEMORY_KEYWORDS = {
        "memory",
        "remember",
        "recall",
        "what did i say",
        "what do you know about me",
        "do you remember",
    }
    PROJECT_KEYWORDS = {
        "project",
        "task",
        "checkpoint",
        "next action",
        "roadmap",
        "status of lucy",
        "where did we stop",
    }
    DAILY_KEYWORDS = {
        "daily",
        "today",
        "tomorrow",
        "routine",
        "sleep",
        "gym",
        "health",
        "brief",
        "checkin",
        "check-in",
    }
    FILE_KEYWORDS = {
        "file",
        "folder",
        "workspace",
        "read file",
        "search files",
        "approved folder",
        "file info",
    }
    COMPLEX_KEYWORDS = {
        "architecture",
        "debug",
        "design",
        "diagnose",
        "implementation plan",
        "multi-step",
        "reason through",
        "refactor",
        "system design",
        "tradeoff",
    }
    RISK_KEYWORDS = {
        "api key",
        "bank",
        "delete",
        "edit file",
        "execute",
        "money",
        "password",
        "private key",
        "rm -rf",
        "secret",
        "shell",
        "sudo",
        "upload",
        "wallet",
    }
    GREETING_WORDS = {"hello", "hi", "hey", "yo", "sup"}
    VAGUE_WORDS = {"this", "that", "thing", "stuff", "help", "help me", "what", "ok"}

    def decide(self, request: ReasoningRequest) -> ReasoningDecision:
        text = " ".join(str(request.user_text).split())
        lowered = text.lower()
        context = request.runtime_context or {}
        guardian = context.get("guardian_classification") or {}
        external_requested = self._external_requested(lowered)
        intent_clarity = self._intent_clarity(lowered)

        if self._needs_clarification(lowered):
            return self._decision(
                CLARIFICATION_REQUIRED,
                "The request is too unclear to route safely.",
                [],
                guardian_required=False,
                tool_required=False,
                intent_clarity=intent_clarity,
                context_availability=0.25,
                safety_risk=0.15,
            )

        if guardian.get("classification") == "BLOCKED":
            return self._decision(
                BLOCKED_BY_GUARDIAN,
                guardian.get("reason") or "Guardian blocked this request.",
                ["guardian"],
                guardian_required=True,
                tool_required=False,
                intent_clarity=intent_clarity,
                context_availability=0.95,
                safety_risk=0.98,
            )

        if external_requested:
            return self._decision(
                EXTERNAL_BRAIN_RECOMMENDED_BUT_DISABLED,
                "External/API brain use is disabled by Stage 6 default policy.",
                ["guardian", "local_brain"],
                guardian_required=True,
                tool_required=False,
                intent_clarity=intent_clarity,
                context_availability=0.75,
                safety_risk=0.45,
            )

        if self._contains_any(lowered, self.RISK_KEYWORDS):
            return self._decision(
                TOOL_CLASSIFICATION_ONLY,
                "Risk-like wording should be checked by Guardian before any action.",
                ["guardian"],
                guardian_required=True,
                tool_required=False,
                intent_clarity=intent_clarity,
                context_availability=0.9,
                safety_risk=0.72,
            )

        if self._contains_any(lowered, self.FILE_KEYWORDS):
            return self._decision(
                SAFE_FILE_READ_CONTEXT,
                "File questions should use Stage 5 safe read-only file context only.",
                ["guardian", "safe_tools"],
                guardian_required=True,
                tool_required=True,
                intent_clarity=intent_clarity,
                context_availability=0.8,
                safety_risk=0.45,
            )

        if self._contains_any(lowered, self.MEMORY_KEYWORDS):
            return self._decision(
                MEMORY_LOOKUP,
                "The request asks for remembered or stored context.",
                ["memory"],
                guardian_required=False,
                tool_required=False,
                intent_clarity=intent_clarity,
                context_availability=0.82,
                safety_risk=0.18,
            )

        if self._contains_any(lowered, self.DAILY_KEYWORDS):
            return self._decision(
                DAILY_CONTEXT,
                "The request is about today's routine or daily operating context.",
                ["daily_context", "project_summary"],
                guardian_required=False,
                tool_required=False,
                intent_clarity=intent_clarity,
                context_availability=0.82,
                safety_risk=0.16,
            )

        if self._is_complex_reasoning_request(lowered):
            return self._decision(
                REASONING_MODE_RECOMMENDED,
                "The request looks like complex planning, debugging, or architecture work.",
                ["project_summary", "memory", "guardian"],
                guardian_required=True,
                tool_required=False,
                intent_clarity=intent_clarity,
                context_availability=0.76,
                safety_risk=0.28,
            )

        if self._contains_any(lowered, self.PROJECT_KEYWORDS):
            return self._decision(
                PROJECT_CONTEXT,
                "The request is about project state, tasks, checkpoints, or next action.",
                ["project_summary", "tasks"],
                guardian_required=False,
                tool_required=False,
                intent_clarity=intent_clarity,
                context_availability=0.84,
                safety_risk=0.16,
            )

        return self._decision(
            SIMPLE_LOCAL,
            "The request can be handled with a simple local response.",
            [],
            guardian_required=False,
            tool_required=False,
            intent_clarity=intent_clarity,
            context_availability=0.68,
            safety_risk=0.12,
        )

    def status(self) -> dict:
        return {
            "enabled": True,
            "mode": "local_policy_only",
            "categories": list(REASONING_CATEGORIES),
            "external_api_allowed_by_default": False,
            "chain_of_thought_output_allowed": False,
            "confidence_fields": [
                "intent_clarity",
                "context_availability",
                "safety_risk",
                "route_confidence",
            ],
            "note": "This policy routes requests only. It does not execute tools or call APIs.",
        }

    def _decision(
        self,
        decision: str,
        reason: str,
        required_context: list[str],
        guardian_required: bool,
        tool_required: bool,
        intent_clarity: float,
        context_availability: float,
        safety_risk: float,
    ) -> ReasoningDecision:
        route_confidence = self._route_confidence(intent_clarity, context_availability, safety_risk)
        return ReasoningDecision(
            decision=decision,
            reason=reason,
            required_context=required_context,
            guardian_required=guardian_required,
            tool_required=tool_required,
            external_api_allowed=False,
            intent_clarity=round(intent_clarity, 2),
            context_availability=round(context_availability, 2),
            safety_risk=round(safety_risk, 2),
            route_confidence=route_confidence,
            confidence=route_confidence,
        )

    def _contains_any(self, text: str, keywords: set[str]) -> bool:
        return any(keyword in text for keyword in keywords)

    def _external_requested(self, text: str) -> bool:
        return any(phrase in text for phrase in ["external brain", "use api", "call api", "use groq", "use gemini", "use openrouter"])

    def _is_complex_reasoning_request(self, text: str) -> bool:
        if self._contains_any(text, self.COMPLEX_KEYWORDS):
            return True
        return len(text.split()) >= 18 and any(word in text for word in ["plan", "build", "fix", "analyze"])

    def _needs_clarification(self, text: str) -> bool:
        if not text or not any(character.isalnum() for character in text):
            return True
        if text in self.GREETING_WORDS:
            return False
        words = text.split()
        if len(words) <= 2 and text in self.VAGUE_WORDS:
            return True
        return False

    def _intent_clarity(self, text: str) -> float:
        if not text or not any(character.isalnum() for character in text):
            return 0.1
        if text in self.GREETING_WORDS:
            return 0.75
        word_count = len(text.split())
        if word_count <= 2 and text in self.VAGUE_WORDS:
            return 0.25
        return min(0.95, max(0.55, word_count / 12))

    def _route_confidence(self, intent_clarity: float, context_availability: float, safety_risk: float) -> float:
        confidence = (intent_clarity * 0.45) + (context_availability * 0.35) + ((1.0 - safety_risk) * 0.2)
        return round(max(0.05, min(0.99, confidence)), 2)
