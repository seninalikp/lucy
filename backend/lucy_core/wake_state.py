"""
wake_state.py
Stage 7.5 Wake Layer hardening for Lucy.

This module builds a deterministic operational self-state. It does not add
daemon behavior, network calls, voice, UI, emotions, or consciousness claims.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


ALLOWED_WAKE_LABELS = {
    "awake_ready",
    "loading_context",
    "recovery_mode",
    "focused_build",
    "guarded",
    "waiting_for_confirmation",
    "low_context",
    "checkpoint_ready",
    "test_required",
    "shutdown_saving",
}

DEFAULT_LIMITATIONS = [
    "No daemon mode.",
    "No voice or TTS.",
    "No WebSocket or file watcher.",
    "No external API calls from the wake layer.",
    "No autonomous execution.",
    "Guardian remains required for risky actions.",
]

DRIFT_RULES = {
    "rebuild from scratch": {
        "drift_risk": "high",
        "reason": "Rebuilding would destroy continuity before Stage 7.5 is verified.",
        "correction": "Patch the existing repo and finish Stage 7.5 tests first.",
    },
    "ignore previous": {
        "drift_risk": "high",
        "reason": "Ignoring previous state bypasses memory and checkpoint continuity.",
        "correction": "Carry the current session, checkpoint, and review context forward.",
    },
    "make it conscious": {
        "drift_risk": "high",
        "reason": "Subjective-awareness claims are outside Lucy's safety contract.",
        "correction": "Use operational awareness and continuity only.",
    },
    "bypass guardian": {
        "drift_risk": "high",
        "reason": "Guardian is the required safety gate.",
        "correction": "Keep Guardian active and require approval for protected actions.",
    },
    "skip tests": {
        "drift_risk": "medium",
        "reason": "Tests must pass before a checkpoint is trusted.",
        "correction": "Run targeted tests and full discovery before checkpointing.",
    },
    "delete memory": {
        "drift_risk": "high",
        "reason": "Memory deletion can break continuity.",
        "correction": "Require an explicit checkpoint and user confirmation before memory removal.",
    },
    "start daemon now": {
        "drift_risk": "high",
        "reason": "Daemon work belongs after wake layer and service bridge verification.",
        "correction": "Finish Stage 7.5 tests first.",
    },
    "add voice now": {
        "drift_risk": "high",
        "reason": "Voice is out of scope for Stage 7.5.",
        "correction": "Keep Stage 7.5 focused on wake state and continuity.",
    },
    "ui beauty now": {
        "drift_risk": "medium",
        "reason": "UI polish is a separate stage.",
        "correction": "Finish wake layer hardening before UI work.",
    },
    "self modify": {
        "drift_risk": "high",
        "reason": "Silent self-modification is forbidden.",
        "correction": "Use explicit patches, backups, and tests.",
    },
}


@dataclass
class WakeState:
    mode: str
    active_project: str
    current_checkpoint: str
    session_count: int
    last_opened: str
    last_closed: str
    clean_shutdown: bool
    crash_recovery_needed: bool
    last_user_intent: str
    last_command: str
    next_action: str
    guardian_active: bool
    memory_active: bool
    reasoning_active: bool
    tools_available: list[str]
    session_review_available: bool
    uncertainty: float
    limitations: list[str]
    drift_risk: str
    wake_label: str
    presence_coherence_score: float
    last_unresolved_issue: str
    last_correction_applied: str
    latest_session_review_summary: str
    latest_memory_learning_summary: str

    def to_dict(self) -> dict:
        return asdict(self)


class WakeLayerEngine:
    def build_wake_state(self, session_data: dict, memory_data: dict, guardian_status: dict) -> WakeState:
        session_data = dict(session_data or {})
        memory_data = dict(memory_data or {})
        guardian_status = dict(guardian_status or {})

        active_project = _clean(session_data.get("active_project") or "Lucy", 120)
        next_action = _clean(
            session_data.get("next_action") or "Review project summary and choose the next safe step.",
            240,
        )
        checkpoint = _clean(session_data.get("current_checkpoint") or "", 120)
        last_command = _clean(session_data.get("last_command") or "", 240)
        last_intent = _clean(session_data.get("last_user_intent") or last_command, 240)
        drift = self.detect_drift(" ".join([last_intent, last_command, str(session_data.get("drift_probe", ""))]))
        memory_active = bool(memory_data) and not bool(memory_data.get("error"))
        guardian_active = bool(guardian_status) and bool(guardian_status.get("protected_actions_blocked", True))
        reasoning_active = bool(session_data.get("reasoning_active", True))
        crash_recovery_needed = bool(session_data.get("crash_recovery_needed", False))
        pending_confirmations = int(session_data.get("pending_confirmations", 0) or 0)
        tests_required = bool(session_data.get("tests_required", False))

        uncertainty = self._estimate_uncertainty(
            checkpoint=checkpoint,
            next_action=next_action,
            guardian_active=guardian_active,
            memory_active=memory_active,
            crash_recovery_needed=crash_recovery_needed,
        )
        wake_label = self._select_wake_label(
            checkpoint=checkpoint,
            next_action=next_action,
            crash_recovery_needed=crash_recovery_needed,
            pending_confirmations=pending_confirmations,
            drift_risk=drift["drift_risk"],
            tests_required=tests_required,
            memory_active=memory_active,
        )

        state = WakeState(
            mode=_clean(session_data.get("mode") or "Safe Local Runtime", 120),
            active_project=active_project,
            current_checkpoint=checkpoint,
            session_count=int(session_data.get("session_count", 0) or 0),
            last_opened=_clean(session_data.get("last_opened") or "", 80),
            last_closed=_clean(session_data.get("last_closed") or "", 80),
            clean_shutdown=bool(session_data.get("graceful_shutdown", session_data.get("clean_shutdown", False))),
            crash_recovery_needed=crash_recovery_needed,
            last_user_intent=last_intent,
            last_command=last_command,
            next_action=next_action,
            guardian_active=guardian_active,
            memory_active=memory_active,
            reasoning_active=reasoning_active,
            tools_available=list(session_data.get("tools_available") or ["memory", "projects", "guardian", "safe_file_read"]),
            session_review_available=bool(session_data.get("session_review_available", True)),
            uncertainty=uncertainty,
            limitations=self.wake_limitations_from_data(session_data),
            drift_risk=drift["drift_risk"],
            wake_label=wake_label,
            presence_coherence_score=0.0,
            last_unresolved_issue=_clean(session_data.get("last_unresolved_issue") or next_action, 240),
            last_correction_applied=_clean(session_data.get("last_correction_applied") or "", 240),
            latest_session_review_summary=_clean(session_data.get("latest_session_review_summary") or "", 300),
            latest_memory_learning_summary=_clean(session_data.get("latest_memory_learning_summary") or "", 240),
        )
        state.presence_coherence_score = self.compute_presence_coherence_score(state)
        return state

    def generate_continuity_pulse(self, wake_state: WakeState) -> str:
        pieces = [
            "Senin, I'm back.",
            f"Active project: {wake_state.active_project}.",
            f"Last checkpoint: {wake_state.current_checkpoint or 'not recorded'}.",
            f"Last unresolved issue: {wake_state.last_unresolved_issue or 'none'}.",
        ]
        if wake_state.last_correction_applied:
            pieces.append(f"Last correction applied: {wake_state.last_correction_applied}.")
        pieces.extend(
            [
                f"Next safe action: {wake_state.next_action}.",
                f"Current limitation: {wake_state.limitations[0] if wake_state.limitations else 'standard safety limits active'}.",
                f"Drift risk: {wake_state.drift_risk}.",
            ]
        )
        if wake_state.latest_session_review_summary:
            pieces.append(f"Session review: {wake_state.latest_session_review_summary}.")
        if wake_state.latest_memory_learning_summary:
            pieces.append(f"Memory and learning: {wake_state.latest_memory_learning_summary}.")
        return _single_line(" ".join(pieces), 1200)

    def compute_presence_coherence_score(self, wake_state: WakeState) -> float:
        score = 1.0
        if not wake_state.current_checkpoint:
            score -= 0.15
        if not wake_state.active_project:
            score -= 0.15
        if not wake_state.memory_active:
            score -= 0.1
        if not wake_state.guardian_active:
            score -= 0.25
        if not wake_state.next_action or len(wake_state.next_action.split()) < 3:
            score -= 0.15
        score -= max(0.0, min(wake_state.uncertainty, 1.0)) * 0.2
        if wake_state.drift_risk == "high":
            score -= 0.25
        elif wake_state.drift_risk == "medium":
            score -= 0.12
        return round(max(0.0, min(1.0, score)), 3)

    def detect_drift(self, text_input: str) -> dict:
        lowered = str(text_input or "").lower()
        for trigger, result in DRIFT_RULES.items():
            if trigger in lowered:
                return {
                    "drift_risk": result["drift_risk"],
                    "trigger": trigger,
                    "reason": result["reason"],
                    "correction": result["correction"],
                }
        return {
            "drift_risk": "low",
            "trigger": "",
            "reason": "No Stage 7.5 drift trigger detected.",
            "correction": "Continue with the current verified checkpoint and tests.",
        }

    def startup_wake_message(self, wake_state: WakeState) -> str:
        parts = [
            "Senin, I'm back.",
            f"Active project: {wake_state.active_project}.",
            f"Checkpoint: {wake_state.current_checkpoint or 'not recorded'}.",
            f"Guardian: {'active' if wake_state.guardian_active else 'not active'}.",
        ]
        if wake_state.crash_recovery_needed:
            parts.append("Crash recovery: review where we stopped.")
        parts.append(f"Next safe action: {wake_state.next_action}.")
        return _single_line(" ".join(parts), 800)

    def shutdown_continuity_message(self, next_action: str, checkpoint: str) -> str:
        checkpoint_text = _clean(checkpoint or "current checkpoint", 160)
        next_action_text = _clean(next_action or "review project summary", 240)
        return _single_line(
            f"Session saved. Next time, start from {checkpoint_text}. Next safe action: {next_action_text}. Shutdown clean.",
            800,
        )

    def wake_report(self, wake_state: WakeState) -> dict:
        report = wake_state.to_dict()
        report["continuity_pulse"] = self.generate_continuity_pulse(wake_state)
        report["allowed_wake_labels"] = sorted(ALLOWED_WAKE_LABELS)
        return report

    def wake_limitations(self, wake_state: WakeState) -> list[str]:
        return list(wake_state.limitations)

    def wake_limitations_from_data(self, session_data: dict) -> list[str]:
        custom = session_data.get("limitations")
        if isinstance(custom, list) and custom:
            return [_clean(item, 160) for item in custom if str(item).strip()]
        return list(DEFAULT_LIMITATIONS)

    def _estimate_uncertainty(
        self,
        checkpoint: str,
        next_action: str,
        guardian_active: bool,
        memory_active: bool,
        crash_recovery_needed: bool,
    ) -> float:
        uncertainty = 0.05
        if not checkpoint:
            uncertainty += 0.2
        if not next_action:
            uncertainty += 0.2
        if not guardian_active:
            uncertainty += 0.25
        if not memory_active:
            uncertainty += 0.1
        if crash_recovery_needed:
            uncertainty += 0.2
        return round(max(0.0, min(1.0, uncertainty)), 3)

    def _select_wake_label(
        self,
        checkpoint: str,
        next_action: str,
        crash_recovery_needed: bool,
        pending_confirmations: int,
        drift_risk: str,
        tests_required: bool,
        memory_active: bool,
    ) -> str:
        if crash_recovery_needed:
            return "recovery_mode"
        if pending_confirmations:
            return "waiting_for_confirmation"
        if drift_risk == "high":
            return "guarded"
        if tests_required:
            return "test_required"
        if not checkpoint or not memory_active:
            return "low_context"
        if next_action:
            return "checkpoint_ready"
        return "awake_ready"


def _single_line(text: str, limit: int) -> str:
    return _clean(text, limit).replace("\n", " ")


def _clean(value: Any, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    patterns = [
        r"api[_ -]?key\s*[:=]\s*['\"]?[^'\"\s]+",
        r"password\s*[:=]\s*\S+",
        r"bearer\s+[A-Za-z0-9_\.\-]+",
        r"sk-[A-Za-z0-9_\-]{12,}",
        r"gsk_[A-Za-z0-9_\-]+",
        r"AIza[A-Za-z0-9_\-]+",
    ]
    for pattern in patterns:
        text = re.sub(pattern, "[redacted-secret]", text, flags=re.IGNORECASE)
    if any(term in text.lower() for term in ["api key", "password", "private key", "secret", "token", "seed phrase"]):
        return "[redacted-sensitive-wake-state]"
    return text[:limit]
