"""
presence.py
Minimal Stage 7 presence compatibility layer.

Stage 7.5 extends this report with WakeState summary fields. This is operational
presence only: no emotions, subjective experience, daemon, voice, or UI work.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class PresenceReport:
    mode: str
    active_project: str
    status: str
    next_action: str
    wake_label: str
    continuity_pulse: str
    presence_coherence_score: float
    drift_risk: str
    limitations: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


class PresenceLayer:
    def build_report(self, wake_report: dict) -> PresenceReport:
        return PresenceReport(
            mode="adaptive_operational_presence",
            active_project=str(wake_report.get("active_project") or "Lucy"),
            status=str(wake_report.get("wake_label") or "low_context"),
            next_action=str(wake_report.get("next_action") or "Review project summary."),
            wake_label=str(wake_report.get("wake_label") or "low_context"),
            continuity_pulse=str(wake_report.get("continuity_pulse") or ""),
            presence_coherence_score=float(wake_report.get("presence_coherence_score") or 0.0),
            drift_risk=str(wake_report.get("drift_risk") or "low"),
            limitations=list(wake_report.get("limitations") or []),
        )
