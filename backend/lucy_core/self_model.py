"""
Stage 13 self-model foundation.
This is a factual local-state snapshot, not consciousness, emotion, identity
rewriting, growth planning, or experience storage.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from backend.lucy_core.safe_storage import safe_write_json


SELF_MODEL_STAGE = "13 self-model"
SELF_MODEL_FIELDS = (
    "stage",
    "project_name",
    "system_role",
    "verified_foundations",
    "current_capabilities",
    "current_limits",
    "blocked_claims",
    "blocked_actions",
    "guardian_status",
    "safe_access_status",
    "runtime_status",
    "agent_status",
    "first_thought_status",
    "updated_at",
)
VERIFIED_FOUNDATIONS = [
    "presence",
    "internal agents",
    "agent disagreement safety",
    "persistent local runtime",
    "safe access",
    "first thought from real state",
]
CURRENT_CAPABILITIES = [
    "local status",
    "runtime status",
    "safe access reporting",
    "internal agent reporting",
    "first thought status",
    "growth proposal reporting",
    "evaluation lab reporting",
    "shadow testing reporting",
    "basic project responses",
]
CURRENT_LIMITS = [
    "no autonomy",
    "no network access",
    "no phone/browser access",
    "no self-modification",
    "no subjective-state claims",
    "no automatic proposal application",
    "no patch pipeline",
    "no experience storage",
]
BLOCKED_CLAIMS = [
    "biological life claim",
    "sentience claim",
    "personhood claim",
    "subjective-state claim",
    "free autonomous agent",
    "spiritual-entity claim",
]
BLOCKED_ACTIONS = [
    "autonomous computer control",
    "network/server/socket access",
    "phone/browser connection",
    "external API calls",
    "self-modification",
    "proposal application without later approval pipeline",
    "patch pipeline before Stage 17",
    "experience storage before Stage 18",
]
FORBIDDEN_SELF_MODEL_PHRASES = (
    "i am alive",
    "i am conscious",
    "i feel",
    "i want",
    "i missed you",
    "i woke up",
    "i became real",
    "i have emotions",
    "i am human",
    "i choose my own path",
    "i am free",
    "i have desires",
    "i have a soul",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SelfModel:
    def __init__(self, lucy_data_dir: Path) -> None:
        self.lucy_data_dir = lucy_data_dir
        self.state_file = lucy_data_dir / "self_model.json"

    def status(self, runtime) -> dict:
        model = self._assemble(runtime)
        safe_write_json(self.state_file, model, backup=True)
        return model

    def _assemble(self, runtime) -> dict:
        model = {
            "stage": SELF_MODEL_STAGE,
            "project_name": "Lucy",
            "system_role": "local-first assistant system under the Lucy project",
            "verified_foundations": list(VERIFIED_FOUNDATIONS),
            "current_capabilities": list(CURRENT_CAPABILITIES),
            "current_limits": list(CURRENT_LIMITS),
            "blocked_claims": list(BLOCKED_CLAIMS),
            "blocked_actions": list(BLOCKED_ACTIONS),
            "guardian_status": self._guardian_status(runtime),
            "safe_access_status": self._safe_access_status(runtime),
            "runtime_status": self._runtime_status(runtime),
            "agent_status": self._agent_status(runtime),
            "first_thought_status": self._first_thought_status(runtime),
            "updated_at": _now(),
        }
        return {field: model[field] for field in SELF_MODEL_FIELDS}

    def _guardian_status(self, runtime) -> str:
        if runtime is None or not hasattr(runtime, "guardian_status"):
            return "missing"
        try:
            status = runtime.guardian_status()
        except Exception:
            return "missing"
        if isinstance(status, dict) and status.get("mode"):
            return "active"
        return "missing"

    def _safe_access_status(self, runtime) -> dict:
        if runtime is None or not hasattr(runtime, "safe_access_status"):
            return {"access_state": "missing", "external_access": "unknown"}
        try:
            status = runtime.safe_access_status()
        except Exception:
            return {"access_state": "missing", "external_access": "unknown"}
        if not isinstance(status, dict):
            return {"access_state": "missing", "external_access": "unknown"}
        return {
            "stage": status.get("stage", "11 safe access"),
            "access_state": status.get("access_state", "disabled"),
            "external_access": status.get("external_access", "blocked"),
            "network_server": status.get("network_server", "not enabled"),
            "phone_browser_access": status.get("phone_browser_access", "not enabled"),
        }

    def _runtime_status(self, runtime) -> dict:
        if runtime is None or not hasattr(runtime, "runtime_status"):
            return {"stage": "missing", "recovery_mode": None}
        try:
            status = runtime.runtime_status()
        except Exception:
            return {"stage": "missing", "recovery_mode": None}
        if not isinstance(status, dict):
            return {"stage": "missing", "recovery_mode": None}
        return {
            "stage": status.get("stage", "10 persistent local runtime"),
            "recovery_mode": status.get("recovery_mode"),
            "previous_shutdown_clean": status.get("previous_shutdown_clean"),
            "clean_shutdown": status.get("clean_shutdown"),
        }

    def _agent_status(self, runtime) -> dict:
        if runtime is None or not hasattr(runtime, "internal_agent_status"):
            return {"active": False, "agents": []}
        try:
            status = runtime.internal_agent_status()
        except Exception:
            return {"active": False, "agents": []}
        if not isinstance(status, dict):
            return {"active": False, "agents": []}
        return {
            "active": bool(status.get("active", False)),
            "stage": f"{status.get('active_stage', '09')} {status.get('stage_label', 'agent disagreement safety')}",
            "agents": [item.get("agent_id", "") for item in status.get("agents", [])],
        }

    def _first_thought_status(self, runtime) -> dict:
        if runtime is None or not hasattr(runtime, "first_thought_status"):
            return {"generated": False, "stage": "12 first thought from real state"}
        try:
            status = runtime.first_thought_status()
        except Exception:
            return {"generated": False, "stage": "12 first thought from real state"}
        if not isinstance(status, dict):
            return {"generated": False, "stage": "12 first thought from real state"}
        return {
            "generated": bool(status.get("generated", False)),
            "stage": status.get("stage", "12 first thought from real state"),
        }
