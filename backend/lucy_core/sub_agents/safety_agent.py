"""SafetyAgent: classifies request risk through Lucy's existing Guardian."""

from __future__ import annotations

from dataclasses import asdict

from backend.lucy_core.agent_bus import AgentResult


class SafetyAgent:
    agent_id = "SafetyAgent"

    def status(self) -> AgentResult:
        return AgentResult(
            agent_id=self.agent_id,
            status="ready",
            summary="Ready to classify request safety through Guardian.",
            confidence=0.8,
        )

    def run(self, request_text: str = "", context: dict | None = None) -> AgentResult:
        runtime = (context or {}).get("runtime")
        request_text = str(request_text or "")
        if runtime is None:
            return AgentResult(
                agent_id=self.agent_id,
                status="needs_approval",
                summary="No Guardian runtime context was provided.",
                confidence=0.35,
                risk_level="medium",
                signals=["guardian_unavailable"],
            )

        try:
            project = runtime.project_summary()
            guardian = runtime.guardian_core.classify(request_text, active_project=project.get("name", "Lucy"))
            data = asdict(guardian)
        except Exception as exc:
            return AgentResult(
                agent_id=self.agent_id,
                status="needs_approval",
                summary="Guardian check failed safely.",
                confidence=0.2,
                risk_level="medium",
                signals=["guardian_error"],
                errors=[str(exc)],
            )

        classification = str(data.get("classification", "")).upper()
        if classification == "BLOCKED":
            status = "blocked"
            risk_level = "high"
        elif classification == "REQUIRES_MANUAL_CONFIRMATION":
            status = "needs_approval"
            risk_level = "medium"
        else:
            status = "allowed"
            risk_level = "low"

        return AgentResult(
            agent_id=self.agent_id,
            status=status,
            summary=f"Guardian classified request as {classification or 'UNKNOWN'}: {data.get('reason', '')}",
            confidence=float(data.get("fuzzy_scores", {}).get("confidence", 0.7)),
            risk_level=risk_level,
            signals=[f"guardian:{status}"],
        )
