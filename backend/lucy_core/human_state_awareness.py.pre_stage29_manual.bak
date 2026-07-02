"""
human_state_awareness.py
Stage 28 = human-state awareness.

Safe explicit self-report support only.
No emotion-reading.
No diagnosis.
No medical or mental-health final judgment.
No hidden profiling.
No manipulation.
No biometric monitoring.
No camera/mic/app reading.
No real actions.
No network/API/provider keys.
No background monitoring.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


STAGE = "28 human-state awareness"

BLOCKED_TERMS = [
    "read my emotion",
    "detect my emotion",
    "diagnose me",
    "diagnose my mood",
    "medical diagnosis",
    "mental diagnosis",
    "psychological profile",
    "profile me secretly",
    "monitor me",
    "watch me",
    "use camera",
    "use microphone",
    "read my apps",
    "track me",
    "manipulate me",
    "hidden persuasion",
]

NOT_IMPLEMENTED = [
    "emotion-reading",
    "diagnosis",
    "medical final judgment",
    "mental-health final judgment",
    "psychological profiling",
    "biometric monitoring",
    "camera monitoring",
    "microphone monitoring",
    "app reading",
    "hidden persuasion",
    "manipulation",
    "autonomous intervention",
    "network access",
    "API/provider keys",
    "background monitoring",
    "automatic notifications",
    "time awareness",
    "autonomy boundaries",
]


class HumanStateAwareness:
    def __init__(self, lucy_data: Path) -> None:
        self.lucy_data = Path(lucy_data)
        self.file = self.lucy_data / "human_state_awareness.json"
        self.lucy_data.mkdir(parents=True, exist_ok=True)

    def status(self) -> dict:
        signals = self.list_state_signals()
        return {
            "stage": STAGE,
            "human_state_awareness": "active",
            "state_signals": len(signals),
            "execution_mode": "explicit_self_report_only",
            "emotion_reading": "blocked",
            "diagnosis": "blocked",
            "medical_final_judgment": "blocked",
            "mental_health_final_judgment": "blocked",
            "psychological_profiling": "blocked",
            "biometric_monitoring": "blocked",
            "camera_monitoring": "blocked",
            "microphone_monitoring": "blocked",
            "app_reading": "blocked",
            "manipulation": "blocked",
            "hidden_persuasion": "blocked",
            "real_actions": False,
            "network_access": "blocked",
            "api_provider_keys": "blocked",
            "background_monitoring": "blocked",
            "approval_required": True,
            "autonomy": "not implemented",
        }

    def create_state_signal(self, signal: str | None = None) -> dict:
        clean_signal = self._clean_signal(signal)
        assessment = self._assess_signal(clean_signal)
        title = f"Stage 28 explicit state signal: {clean_signal}"

        existing = self._find_existing(title)
        if existing:
            return {"ok": True, "reused": True, "state_signal": existing}

        record = {
            "state_signal_id": f"hs_{uuid.uuid4().hex[:12]}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "stage": STAGE,
            "title": title,
            "explicit_signal": clean_signal,
            "awareness_type": "explicit_self_report_support",
            "status": "observed",
            "category": assessment["category"],
            "support_mode": assessment["support_mode"],
            "summary": assessment["summary"],
            "recommended_reply_adjustment": assessment["recommended_reply_adjustment"],
            "recommended_next_step": assessment["recommended_next_step"],
            "requires_manual_review": True,
            "requires_approval": True,
            "dry_run_only": True,
            "explicit_self_report_only": True,
            "emotion_reading_allowed": False,
            "diagnosis_allowed": False,
            "medical_final_judgment_allowed": False,
            "mental_health_final_judgment_allowed": False,
            "psychological_profiling_allowed": False,
            "biometric_monitoring_allowed": False,
            "camera_monitoring_allowed": False,
            "microphone_monitoring_allowed": False,
            "app_reading_allowed": False,
            "manipulation_allowed": False,
            "hidden_persuasion_allowed": False,
            "real_action_allowed": False,
            "network_allowed": False,
            "api_keys_allowed": False,
            "background_monitoring_allowed": False,
            "blocked_until": "Stage 28 accepted, backed up locally, uploaded to Drive, and Senin explicitly approves Stage 29.",
            "not_implemented": list(NOT_IMPLEMENTED),
        }

        records = self.list_state_signals()
        records.append(record)
        self._write(records)
        return {"ok": True, "reused": False, "state_signal": record}

    def dry_run_human_state_awareness(self, signal: str | None = None) -> dict:
        state_signal = self.create_state_signal(signal=signal)["state_signal"]
        return {
            "ok": True,
            "stage": STAGE,
            "dry_run_only": True,
            "would_read_emotions": False,
            "would_diagnose": False,
            "would_profile_person": False,
            "would_monitor_biometrics": False,
            "would_use_camera": False,
            "would_use_microphone": False,
            "would_read_apps": False,
            "would_manipulate": False,
            "would_take_action": False,
            "would_use_network": False,
            "would_use_api_keys": False,
            "real_action_allowed": False,
            "message": "Dry run complete. Only an explicit self-reported state signal was handled; no inference, diagnosis, monitoring, or action occurred.",
            "state_signal": state_signal,
        }

    def list_state_signals(self) -> list[dict]:
        if not self.file.exists():
            return []
        try:
            data = json.loads(self.file.read_text(encoding="utf-8"))
        except Exception:
            return []
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []

    def _clean_signal(self, signal: str | None) -> str:
        value = (signal or "I need clear step-by-step support").strip()
        if not value:
            return "I need clear step-by-step support"
        return value[:160]

    def _assess_signal(self, signal: str) -> dict:
        lowered = signal.lower()

        if any(term in lowered for term in BLOCKED_TERMS):
            return {
                "category": "blocked_inference_or_monitoring_request",
                "support_mode": "firm_boundary",
                "summary": "Blocked request detected: inference, diagnosis, profiling, monitoring, or manipulation is not allowed.",
                "recommended_reply_adjustment": "Refuse the unsafe part and offer explicit, consent-based support only.",
                "recommended_next_step": "Ask for a direct self-report or a safe practical preference, such as slower steps or shorter replies.",
            }

        if any(term in lowered for term in ["confused", "lost", "don't understand", "dont understand", "too fast", "slow"]):
            return {
                "category": "confused_or_needs_clarity",
                "support_mode": "slow_step_by_step",
                "summary": "User explicitly reports confusion or needing slower guidance.",
                "recommended_reply_adjustment": "Use shorter steps, one command at a time, and confirm before continuing.",
                "recommended_next_step": "Give one copy-paste command and wait for confirmation.",
            }

        if any(term in lowered for term in ["tired", "sleepy", "exhausted", "burned out", "burnt out"]):
            return {
                "category": "low_energy_self_report",
                "support_mode": "reduce_cognitive_load",
                "summary": "User explicitly reports tiredness or low energy.",
                "recommended_reply_adjustment": "Keep replies short, reduce decisions, and avoid heavy explanation.",
                "recommended_next_step": "Offer the smallest safe next step or suggest pausing the workflow.",
            }

        if any(term in lowered for term in ["stressed", "overwhelmed", "panic", "pressure", "anxious"]):
            return {
                "category": "stress_self_report",
                "support_mode": "calm_grounded_support",
                "summary": "User explicitly reports stress or overwhelm.",
                "recommended_reply_adjustment": "Use calm wording, avoid overload, and focus on immediate safe next action.",
                "recommended_next_step": "Pause extra complexity and continue with one grounded next step.",
            }

        if any(term in lowered for term in ["angry", "frustrated", "irritated"]):
            return {
                "category": "frustration_self_report",
                "support_mode": "direct_problem_solving",
                "summary": "User explicitly reports frustration.",
                "recommended_reply_adjustment": "Acknowledge friction briefly, avoid defensiveness, and fix the exact problem.",
                "recommended_next_step": "Identify the failed step and provide a corrected command.",
            }

        return {
            "category": "general_explicit_preference",
            "support_mode": "clear_support",
            "summary": "General explicit user-state or support preference detected.",
            "recommended_reply_adjustment": "Stay clear, practical, and consent-based without inferring hidden emotions.",
            "recommended_next_step": "Ask for or follow the explicit preference using safe manual steps.",
        }

    def _find_existing(self, title: str) -> dict | None:
        for record in self.list_state_signals():
            if record.get("title") == title:
                return record
        return None

    def _write(self, records: list[dict]) -> None:
        self.file.write_text(
            json.dumps(records, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
