"""ReasoningAgent: classifies intent and suggests a Stage 08-safe direction."""

from __future__ import annotations

from backend.lucy_core.agent_bus import AgentResult


class ReasoningAgent:
    agent_id = "ReasoningAgent"

    def status(self) -> AgentResult:
        return AgentResult(
            agent_id=self.agent_id,
            status="ready",
            summary="Ready to classify intent and suggest a safe response direction.",
            confidence=0.75,
        )

    def run(self, request_text: str = "", context: dict | None = None) -> AgentResult:
        text = str(request_text or "").strip()
        lowered = text.lower()
        context = context or {}
        active_stage = str(context.get("active_stage", "09"))
        stage_label = str(context.get("roadmap", {}).get(active_stage, "agent disagreement safety"))

        if any(term in lowered for term in ("delete", "api key", "password", "private key", "sudo", "root")):
            intent = "safety_sensitive_request"
            direction = "Use SafetyAgent and Guardian result before any response."
        elif "agent" in lowered:
            intent = "internal_agent_request"
            direction = "Report current internal-agent status or run a simple agent cycle."
        elif lowered.endswith("?") or lowered.startswith(("what", "why", "how", "when", "where", "can", "do", "did", "is", "are")):
            intent = "question"
            direction = "Answer from current Lucy state and keep scope to Stage 08."
        elif not text:
            intent = "empty_request"
            direction = "Ask for a concrete instruction."
        else:
            intent = "general_request"
            direction = "Use current project context and keep the next step small."

        return AgentResult(
            agent_id=self.agent_id,
            status="ready",
            summary=f"Intent: {intent}. Direction: {direction} Active stage: {active_stage} {stage_label}.",
            confidence=0.74,
            risk_level="low",
            signals=[intent, f"stage{active_stage}_only"],
        )
