"""
Minimal Stage 08 internal agent bus.
Registers Lucy's internal specialists and runs them without granting autonomy.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class AgentResult:
    agent_id: str
    status: str
    summary: str
    confidence: float = 0.0
    risk_level: str = "low"
    signals: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class AgentBus:
    def __init__(self) -> None:
        self._agents: dict[str, Any] = {}

    def register(self, agent: Any) -> None:
        agent_id = str(getattr(agent, "agent_id", "")).strip()
        if not agent_id:
            raise ValueError("Agent must expose agent_id.")
        self._agents[agent_id] = agent

    def list_agents(self) -> list[str]:
        return list(self._agents.keys())

    def get_agent(self, agent_id: str) -> Any | None:
        return self._agents.get(agent_id)

    def run_all(self, request_text: str = "", context: dict | None = None) -> list[dict]:
        context = context or {}
        results = []
        for agent_id in self.list_agents():
            agent = self._agents[agent_id]
            try:
                result = agent.run(request_text=request_text, context=context)
            except Exception as exc:
                result = AgentResult(
                    agent_id=agent_id,
                    status="error",
                    summary="Agent failed safely.",
                    confidence=0.0,
                    risk_level="unknown",
                    errors=[str(exc)],
                )
            results.append(self._normalize_result(agent_id, result))
        return results

    def _normalize_result(self, agent_id: str, result: Any) -> dict:
        if isinstance(result, AgentResult):
            data = result.to_dict()
        elif isinstance(result, dict):
            data = dict(result)
        else:
            data = {
                "agent_id": agent_id,
                "status": "error",
                "summary": "Agent returned an unsupported result.",
                "confidence": 0.0,
                "risk_level": "unknown",
                "signals": [],
                "errors": [f"Unsupported result type: {type(result).__name__}"],
            }

        data.setdefault("agent_id", agent_id)
        data.setdefault("status", "unknown")
        data.setdefault("summary", "")
        data.setdefault("confidence", 0.0)
        data.setdefault("risk_level", "unknown")
        data.setdefault("signals", [])
        data.setdefault("errors", [])
        return data
