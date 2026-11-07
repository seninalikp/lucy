"""
LUCY STAGE 285: Quantum Zeno & Anti-Zeno Dynamic Measurement Controller
Sovereign Architect & Supreme Operator: Senin (Senin Ali K P)

Provides high-precision computational physics and control dynamics for repeated projective
quantum measurements, short-time quadratic survival probabilities P(tau) ~ 1 - (tau/tau_Z)^2,
Quantum Zeno Effect (QZE) decay inhibition (P -> 1 as tau -> 0), and Quantum Anti-Zeno Effect
(AZE) accelerated dissipation via bath spectral density overlap Gamma_eff(tau) > Gamma_0.
Fully offline, thread-safe, CP1252-safe ASCII reporting.
"""

import math
import time
import threading
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

STAGE: int = 285
STAGE_NAME: str = "Quantum Zeno & Anti-Zeno Dynamic Measurement Controller"
SOVEREIGN_OPERATOR: str = "Senin (Senin Ali K P)"

DEFAULT_ZENO_TIME_S: float = 1.0e-9              # tau_Z ~ 1 ns


@dataclass
class ZenoSimulationMetrics:
    """State metrics of Quantum Zeno / Anti-Zeno measurement control."""
    measurement_interval_tau_s: float
    total_time_s: float
    number_of_measurements: int
    survival_probability: float
    natural_decay_probability: float
    zeno_regime: str                             # "ZENO_INHIBITION", "ANTI_ZENO_ACCELERATION", "NATURAL_DECAY"
    effective_decay_rate_hz: float
    natural_decay_rate_hz: float
    decay_suppression_ratio: float               # Gamma_eff / Gamma_0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "measurement_interval_tau_s": self.measurement_interval_tau_s,
            "total_time_s": self.total_time_s,
            "number_of_measurements": self.number_of_measurements,
            "survival_probability": self.survival_probability,
            "natural_decay_probability": self.natural_decay_probability,
            "zeno_regime": self.zeno_regime,
            "effective_decay_rate_hz": self.effective_decay_rate_hz,
            "natural_decay_rate_hz": self.natural_decay_rate_hz,
            "decay_suppression_ratio": self.decay_suppression_ratio,
            "timestamp": self.timestamp,
        }


class QuantumZenoDynamicControllerFabric:
    """
    Stage 285: Autonomous Quantum Zeno & Anti-Zeno Measurement Controller.
    Computes measurement-induced wavefunction collapse intervals and decay engineering.
    """

    def __init__(self, sovereign_operator: str = SOVEREIGN_OPERATOR) -> None:
        self.sovereign_operator: str = sovereign_operator
        self._lock: threading.RLock = threading.RLock()
        self._evaluations_count: int = 0
        self._history: List[ZenoSimulationMetrics] = []
        self._last_metrics: Optional[ZenoSimulationMetrics] = None

    def simulate_zeno_inhibition(
        self,
        measurement_interval_tau_s: float = 1.0e-10,
        total_time_s: float = 1.0e-8,
        zeno_time_s: float = DEFAULT_ZENO_TIME_S,
        natural_decay_rate_hz: float = 1.0e7,
    ) -> Dict[str, Any]:
        """
        Simulates Quantum Zeno decay inhibition.
        Short-time single-step survival: p(tau) = 1 - (tau / tau_Z)^2.
        For N repeated measurements: P_N(t) = [1 - (tau / tau_Z)^2]^N ~ 1 - (t * tau / tau_Z^2).
        """
        with self._lock:
            tau = max(1e-15, float(measurement_interval_tau_s))
            t_tot = max(tau, float(total_time_s))
            tau_z = max(1e-15, float(zeno_time_s))
            gamma_0 = max(1.0, float(natural_decay_rate_hz))

            n_meas = max(1, int(round(t_tot / tau)))

            # Quadratic single-step survival
            step_decay = (tau / tau_z)**2
            step_survival = max(0.0, 1.0 - step_decay)

            # Cumulative survival probability under N measurements
            p_zeno = step_survival**n_meas

            # Natural exponential decay without measurement
            p_natural = math.exp(-gamma_0 * t_tot)

            # Effective decay rate under frequent projective measurements
            gamma_eff = tau / (tau_z**2)
            ratio = gamma_eff / gamma_0

            regime = "ZENO_INHIBITION" if ratio < 1.0 else "NATURAL_DECAY"

            metrics = ZenoSimulationMetrics(
                measurement_interval_tau_s=tau,
                total_time_s=t_tot,
                number_of_measurements=n_meas,
                survival_probability=p_zeno,
                natural_decay_probability=p_natural,
                zeno_regime=regime,
                effective_decay_rate_hz=gamma_eff,
                natural_decay_rate_hz=gamma_0,
                decay_suppression_ratio=ratio,
            )

            self._evaluations_count += 1
            self._last_metrics = metrics
            self._history.append(metrics)
            if len(self._history) > 100:
                self._history.pop(0)

            return metrics.to_dict()

    def simulate_anti_zeno_regime(
        self,
        measurement_interval_tau_s: float = 5.0e-9,
        omega_0: float = 1.0e9,
        bath_cutoff: float = 1.0e10,
        bath_exponent: float = 2.0,
        natural_gamma_0: float = 1.0e7,
    ) -> Dict[str, Any]:
        """
        Simulates structured reservoir spectral overlap:
        G(omega) = alpha * omega^s * exp(-omega / omega_c).
        For super-Ohmic baths (s > 1), measurement broadening overlaps higher density of modes,
        causing Anti-Zeno acceleration: Gamma_eff(tau) > Gamma_0.
        """
        with self._lock:
            tau = max(1e-15, float(measurement_interval_tau_s))
            w0 = float(omega_0)
            wc = float(bath_cutoff)
            s = float(bath_exponent)
            gamma_0 = float(natural_gamma_0)

            # Sinc^2 energy broadening width Delta_omega ~ 2*pi / tau
            delta_w = (2.0 * math.pi) / tau

            # Effective rate modulation factor:
            # When delta_w overlaps peak of super-Ohmic bath at omega ~ s * wc:
            overlap = ((w0 + 0.5 * delta_w) / w0)**(s - 1.0) * math.exp(-0.2 * (delta_w / wc))
            gamma_eff = gamma_0 * max(0.1, overlap)
            ratio = gamma_eff / gamma_0

            regime = "ANTI_ZENO_ACCELERATION" if ratio > 1.05 else ("ZENO_INHIBITION" if ratio < 0.95 else "NATURAL_DECAY")

            return {
                "measurement_interval_tau_s": tau,
                "spectral_broadening_hz": delta_w,
                "natural_decay_rate_hz": gamma_0,
                "effective_decay_rate_hz": gamma_eff,
                "decay_ratio_gamma_eff_over_gamma_0": ratio,
                "regime": regime,
                "bath_super_ohmic": bool(s > 1.0),
            }

    def format_ascii_status(self) -> str:
        """CP1252-safe ASCII table representation."""
        with self._lock:
            last = self._last_metrics
            tau = last.measurement_interval_tau_s if last else 1.0e-10
            n_meas = last.number_of_measurements if last else 100
            p_surv = last.survival_probability if last else 0.99
            p_nat = last.natural_decay_probability if last else 0.90
            regime = last.zeno_regime if last else "ZENO_INHIBITION"
            ratio = last.decay_suppression_ratio if last else 0.01

            lines = [
                "+====================================================================+",
                "|       STAGE 285: QUANTUM ZENO & ANTI-ZENO DYNAMIC CONTROLLER       |",
                "+====================================================================+",
                f"| Sovereign Operator  : {self.sovereign_operator:<44} |",
                f"| Evaluations Count   : {self._evaluations_count:<44} |",
                f"| Measurement Tau (s) : {tau:<44.3e} |",
                f"| Measurement Pulses  : {n_meas:<44} |",
                f"| Survival Prob P(t)  : {p_surv:<44.6f} |",
                f"| Natural Decay P_0   : {p_nat:<44.6f} |",
                f"| Active Zeno Regime  : {regime:<44} |",
                f"| Rate Ratio Gamma/G0 : {ratio:<44.4e} |",
                "+====================================================================+",
            ]
            return "\n".join(lines)

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "sovereign_operator": self.sovereign_operator,
                "evaluations_count": self._evaluations_count,
                "history_length": len(self._history),
                "last_metrics": self._last_metrics.to_dict() if self._last_metrics else None,
            }
