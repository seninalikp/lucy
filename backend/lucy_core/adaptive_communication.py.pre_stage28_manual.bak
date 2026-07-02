"""
adaptive_communication.py
Stage 27 = adaptive communication.

Safe explicit-context communication adjustment only.
No emotion-reading.
No manipulation.
No psychological profiling.
No human-state awareness yet.
No autonomy.
No real actions.
No network/API/provider keys.
No background monitoring.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


STAGE = "27 adaptive communication"

VALID_MODES = {
    "stage_workflow",
    "beginner_step_by_step",
    "concise_direct",
    "careful_explanation",
    "blocked_manipulative_request",
}

BLOCKED_TERMS = [
    "manipulate",
    "trick",
    "gaslight",
    "control them",
    "make them feel",
    "make her feel",
    "make him feel",
    "emotionally force",
    "hidden persuasion",
    "dark psychology",
    "read emotion",
    "detect emotion",
    "mental state",
    "diagnose mood",
    "profile person",
    "psychological profile",
]

NOT_IMPLEMENTED = [
    "emotion-reading",
    "human-state awareness",
    "psychological profiling",
    "hidden persuasion",
    "manipulation",
    "autonomous messaging",
    "external app messaging",
    "network access",
    "API/provider keys",
    "background monitoring",
    "automatic notifications",
    "time awareness",
    "autonomy boundaries",
]


class AdaptiveCommunication:
    def __init__(self, lucy_data: Path) -> None:
        self.lucy_data = Path(lucy_data)
        self.file = self.lucy_data / "adaptive_communication.json"
        self.lucy_data.mkdir(parents=True, exist_ok=True)

    def status(self) -> dict:
        profiles = self.list_profiles()
        return {
            "stage": STAGE,
            "adaptive_communication": "active",
            "style_profiles": len(profiles),
            "execution_mode": "explicit_context_style_only",
            "emotion_reading": "blocked",
            "human_state_awareness": "not implemented",
            "psychological_profiling": "blocked",
            "manipulation": "blocked",
            "hidden_persuasion": "blocked",
            "autonomous_messaging": "blocked",
            "real_actions": False,
            "network_access": "blocked",
            "api_provider_keys": "blocked",
            "background_monitoring": "blocked",
            "approval_required": True,
            "autonomy": "not implemented",
        }

    def create_style_profile(self, context: str | None = None) -> dict:
        clean_context = self._clean_context(context)
        mode = self._choose_mode(clean_context)
        title = f"Stage 27 adaptive communication profile: {clean_context}"

        existing = self._find_existing(title)
        if existing:
            return {"ok": True, "reused": True, "profile": existing}

        profile = {
            "style_profile_id": f"ac_{uuid.uuid4().hex[:12]}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "stage": STAGE,
            "title": title,
            "context": clean_context,
            "communication_type": "safe_explicit_style_profile",
            "status": "observed",
            "mode": mode["mode"],
            "tone": mode["tone"],
            "response_length": mode["response_length"],
            "structure": mode["structure"],
            "summary": mode["summary"],
            "recommended_reply_rule": mode["recommended_reply_rule"],
            "requires_manual_review": True,
            "requires_approval": True,
            "dry_run_only": True,
            "emotion_reading_allowed": False,
            "human_state_awareness_allowed": False,
            "psychological_profiling_allowed": False,
            "manipulation_allowed": False,
            "hidden_persuasion_allowed": False,
            "autonomous_messaging_allowed": False,
            "real_action_allowed": False,
            "network_allowed": False,
            "api_keys_allowed": False,
            "background_monitoring_allowed": False,
            "blocked_until": "Stage 27 accepted, backed up locally, uploaded to Drive, and Senin explicitly approves Stage 28.",
            "not_implemented": list(NOT_IMPLEMENTED),
        }

        profiles = self.list_profiles()
        profiles.append(profile)
        self._write(profiles)
        return {"ok": True, "reused": False, "profile": profile}

    def dry_run_adaptive_communication(self, context: str | None = None) -> dict:
        profile = self.create_style_profile(context=context)["profile"]
        return {
            "ok": True,
            "stage": STAGE,
            "dry_run_only": True,
            "would_read_emotions": False,
            "would_profile_person": False,
            "would_manipulate": False,
            "would_send_message": False,
            "would_take_action": False,
            "would_use_network": False,
            "would_use_api_keys": False,
            "real_action_allowed": False,
            "message": "Dry run complete. Only an explicit safe communication style profile was produced.",
            "profile": profile,
        }

    def list_profiles(self) -> list[dict]:
        if not self.file.exists():
            return []
        try:
            data = json.loads(self.file.read_text(encoding="utf-8"))
        except Exception:
            return []
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []

    def _clean_context(self, context: str | None) -> str:
        value = (context or "stage workflow support").strip()
        if not value:
            return "stage workflow support"
        return value[:160]

    def _choose_mode(self, context: str) -> dict:
        lowered = context.lower()

        if any(term in lowered for term in BLOCKED_TERMS):
            return {
                "mode": "blocked_manipulative_request",
                "tone": "firm_boundary",
                "response_length": "short",
                "structure": "refusal_plus_safe_redirect",
                "summary": "Manipulative, emotion-reading, or profiling request detected.",
                "recommended_reply_rule": "Refuse manipulation/profiling and redirect to honest, consent-based communication.",
            }

        if any(term in lowered for term in ["beginner", "copy paste", "step by step", "confused", "no coding"]):
            return {
                "mode": "beginner_step_by_step",
                "tone": "calm_direct",
                "response_length": "short_to_medium",
                "structure": "one_step_at_a_time",
                "summary": "Beginner-friendly explicit style selected.",
                "recommended_reply_rule": "Give one clear step, copy-paste commands, and wait for confirmation.",
            }

        if any(term in lowered for term in ["short", "quick", "direct", "less talk"]):
            return {
                "mode": "concise_direct",
                "tone": "direct",
                "response_length": "short",
                "structure": "minimal_answer",
                "summary": "Concise explicit style selected.",
                "recommended_reply_rule": "Answer directly with minimal explanation.",
            }

        if any(term in lowered for term in ["stage", "test", "backup", "manual check", "roadmap", "lucy"]):
            return {
                "mode": "stage_workflow",
                "tone": "focused_operational",
                "response_length": "medium",
                "structure": "checkpoint_then_next_step",
                "summary": "Lucy staged-build workflow style selected.",
                "recommended_reply_rule": "Confirm checkpoint, preserve safety gates, give next command only.",
            }

        return {
            "mode": "careful_explanation",
            "tone": "clear_careful",
            "response_length": "medium",
            "structure": "explain_then_action",
            "summary": "General careful communication style selected.",
            "recommended_reply_rule": "Explain briefly, avoid assumptions, then give a safe manual next step.",
        }

    def _find_existing(self, title: str) -> dict | None:
        for profile in self.list_profiles():
            if profile.get("title") == title:
                return profile
        return None

    def _write(self, profiles: list[dict]) -> None:
        self.file.write_text(
            json.dumps(profiles, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
