"""MemoryAgent: summarizes approved project/session context without secrets."""

from __future__ import annotations

from backend.lucy_core.agent_bus import AgentResult


class MemoryAgent:
    agent_id = "MemoryAgent"

    def status(self) -> AgentResult:
        return AgentResult(
            agent_id=self.agent_id,
            status="ready",
            summary="Ready to summarize approved memory, project, and session context.",
            confidence=0.75,
        )

    def run(self, request_text: str = "", context: dict | None = None) -> AgentResult:
        runtime = (context or {}).get("runtime")
        if runtime is None:
            return AgentResult(
                agent_id=self.agent_id,
                status="ready",
                summary="No runtime context was provided.",
                confidence=0.4,
                signals=["no_runtime_context"],
            )

        try:
            project = runtime.project_summary()
        except Exception:
            project = {"name": "Lucy", "next_action": ""}

        try:
            memory = runtime.memory_audit()
        except Exception:
            memory = {"active": 0}

        try:
            session = runtime.session_status()
        except Exception:
            session = {}

        active_project = project.get("name", "Lucy")
        next_action = project.get("next_action") or session.get("next_action") or "not set"
        active_memories = memory.get("active", 0)
        last_command = session.get("last_command") or "none"
        summary = (
            f"Active project: {active_project}. Next action: {next_action}. "
            f"Approved memories active: {active_memories}. Last command: {last_command}."
        )
        return AgentResult(
            agent_id=self.agent_id,
            status="ready",
            summary=summary,
            confidence=0.78,
            risk_level="low",
            signals=["approved_context_only"],
        )
