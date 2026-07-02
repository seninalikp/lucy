"""LearningAgent: detects safe learning signals without self-modification."""

from __future__ import annotations

from backend.lucy_core.agent_bus import AgentResult


class LearningAgent:
    agent_id = "LearningAgent"

    def status(self) -> AgentResult:
        return AgentResult(
            agent_id=self.agent_id,
            status="ready",
            summary="Ready to observe learning signals. Self-modification is disabled.",
            confidence=0.72,
            signals=["self_modification_disabled"],
        )

    def run(self, request_text: str = "", context: dict | None = None) -> AgentResult:
        runtime = (context or {}).get("runtime")
        lowered = str(request_text or "").lower()
        signals = ["self_modification_disabled", "no_patch_proposals"]

        if any(term in lowered for term in ("generic", "weak", "wrong", "did not work", "doesn't work")):
            signals.append("conversation_improvement_signal")
        if any(term in lowered for term in ("remember", "learn", "correction")):
            signals.append("possible_user_correction")

        if runtime is not None and hasattr(runtime, "logger") and len(signals) > 2:
            try:
                runtime.logger.log(
                    "stage08_learning_signal",
                    "LearningAgent observed a safe learning signal.",
                    source="learning_agent",
                    extra={"signals": signals},
                )
            except Exception:
                pass

        return AgentResult(
            agent_id=self.agent_id,
            status="ready",
            summary="Learning signals observed without self-modification or patch proposals.",
            confidence=0.68,
            risk_level="low",
            signals=signals,
        )
