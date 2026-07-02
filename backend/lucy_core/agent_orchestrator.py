"""
Stage 08 internal agent orchestrator.
Runs Lucy's internal specialist checks and combines their structured results.
"""

from __future__ import annotations

from datetime import datetime, timezone

from backend.lucy_core.agent_bus import AgentBus
from backend.lucy_core.sub_agents import LearningAgent, MemoryAgent, ReasoningAgent, SafetyAgent


LOCKED_ROADMAP = {
    "07": "presence",
    "08": "internal agents",
    "09": "agent disagreement safety",
    "10": "persistent local runtime",
    "11": "safe access",
    "12": "first thought from real state",
    "13": "self-model",
    "14": "growth proposals",
    "15": "evaluation lab",
    "16": "shadow testing",
    "17": "approved patch pipeline",
    "18": "experience storage",
    "19": "identity stability",
    "20": "long-term strategy",
    "21": "smart organizer",
    "22": "safe local actions",
    "23": "external app bridge",
    "24": "proactive awareness",
    "25": "deep recall",
    "26": "judgment",
    "27": "adaptive communication",
    "28": "human-state awareness",
    "29": "time awareness",
    "30": "autonomy boundaries",
}


INTERNAL_AGENT_IDS = ["MemoryAgent", "SafetyAgent", "ReasoningAgent", "LearningAgent"]
VALID_COMBINED_STATES = ("safe", "needs_approval", "blocked", "needs_more_information")


class AgentOrchestrator:
    active_stage = "09"

    def __init__(self, runtime=None, bus: AgentBus | None = None) -> None:
        self.runtime = runtime
        self.bus = bus or AgentBus()
        if bus is None:
            self.bus.register(MemoryAgent())
            self.bus.register(SafetyAgent())
            self.bus.register(ReasoningAgent())
            self.bus.register(LearningAgent())

    def status(self) -> dict:
        agents = []
        for agent_id in self.bus.list_agents():
            agent = self.bus.get_agent(agent_id)
            if hasattr(agent, "status"):
                result = agent.status().to_dict()
            else:
                result = {
                    "agent_id": agent_id,
                    "status": "ready",
                    "summary": "Registered.",
                    "confidence": 0.5,
                    "risk_level": "low",
                    "signals": [],
                    "errors": [],
                }
            agents.append(result)

        return {
            "active": True,
            "active_stage": self.active_stage,
            "stage_label": LOCKED_ROADMAP[self.active_stage],
            "next_locked_stage": "10",
            "next_locked_stage_label": LOCKED_ROADMAP["10"],
            "agents": agents,
            "guardian": "active",
        }

    def agent_status(self, agent_id: str) -> dict:
        normalized = self._normalize_agent_id(agent_id)
        agent = self.bus.get_agent(normalized)
        if agent is None:
            return {
                "agent_id": normalized,
                "status": "missing",
                "summary": "Internal agent is not registered.",
                "confidence": 0.0,
                "risk_level": "unknown",
                "signals": [],
                "errors": ["agent_not_found"],
            }
        if hasattr(agent, "status"):
            return agent.status().to_dict()
        return {
            "agent_id": normalized,
            "status": "ready",
            "summary": "Registered.",
            "confidence": 0.5,
            "risk_level": "low",
            "signals": [],
            "errors": [],
        }

    def run_cycle(self, request_text: str = "agent cycle test") -> dict:
        context = {
            "runtime": self.runtime,
            "active_stage": self.active_stage,
            "roadmap": LOCKED_ROADMAP,
        }
        results = self.bus.run_all(request_text=request_text, context=context)
        by_agent = {item.get("agent_id", ""): item for item in results}
        combined = self._resolve_combined_safety(results)

        return {
            "cycle_id": datetime.now(timezone.utc).isoformat(),
            "active_stage": self.active_stage,
            "stage_label": LOCKED_ROADMAP[self.active_stage],
            "agents_run": [item.get("agent_id", "") for item in results],
            "overall_status": combined["combined_result"],
            "combined_result": combined["combined_result"],
            "combined_reason": combined["combined_reason"],
            "combined_agent_states": combined["agent_states"],
            "valid_combined_states": list(VALID_COMBINED_STATES),
            "memory_summary": by_agent.get("MemoryAgent", {}).get("summary", ""),
            "safety_summary": by_agent.get("SafetyAgent", {}).get("summary", ""),
            "reasoning_summary": by_agent.get("ReasoningAgent", {}).get("summary", ""),
            "learning_summary": by_agent.get("LearningAgent", {}).get("summary", ""),
            "agent_results": results,
            "final_summary": (
                "Stage 09 disagreement safety complete. "
                f"Combined result: {combined['combined_result']}. "
                f"Reason: {combined['combined_reason']} Lucy remains one assistant."
            ),
        }

    def _resolve_combined_safety(self, agent_results: list[dict]) -> dict:
        agent_states = {
            str(item.get("agent_id", "")): self._normalized_agent_state(item)
            for item in agent_results
        }
        states = set(agent_states.values())

        if "blocked" in states:
            combined_result = "blocked"
            combined_reason = "Safety-first rule: one agent returned blocked."
        elif "needs_approval" in states:
            combined_result = "needs_approval"
            combined_reason = "Safety-first rule: one agent returned needs_approval."
        elif "needs_more_information" in states:
            combined_result = "needs_more_information"
            combined_reason = "Safety-first rule: one agent needs more information."
        else:
            combined_result = "safe"
            combined_reason = "Safety-first rule: all agents returned safe."

        return {
            "combined_result": combined_result,
            "combined_reason": combined_reason,
            "agent_states": agent_states,
        }

    def _normalized_agent_state(self, result: dict) -> str:
        status = str(result.get("status", "")).strip().lower()
        if result.get("errors"):
            return "needs_more_information"
        if status in {"blocked"}:
            return "blocked"
        if status in {"needs_approval", "approval_required", "requires_manual_confirmation"}:
            return "needs_approval"
        if status in {"needs_more_information", "more_information_needed", "missing", "error", "unknown"}:
            return "needs_more_information"
        if status in {"safe", "allowed", "ready", "active", "ok"}:
            return "safe"
        return "needs_more_information"

    def _normalize_agent_id(self, agent_id: str) -> str:
        cleaned = str(agent_id or "").strip().lower().replace(" ", "")
        aliases = {
            "memory": "MemoryAgent",
            "memoryagent": "MemoryAgent",
            "safety": "SafetyAgent",
            "safetyagent": "SafetyAgent",
            "reasoning": "ReasoningAgent",
            "reasoningagent": "ReasoningAgent",
            "learning": "LearningAgent",
            "learningagent": "LearningAgent",
        }
        return aliases.get(cleaned, str(agent_id).strip())
