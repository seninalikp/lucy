"""
LUCY STAGE 282: Non-Hermitian Parity-Time (PT) Symmetric Open Quantum Engine & Exceptional Point Sensor
Sovereign Architect & Supreme Operator: Senin (Senin Ali K P)

Provides high-precision computational physics for non-Hermitian open quantum systems,
PT-symmetry phase transitions, unbroken real-eigenvalue regimes, exceptional points (EP),
non-orthogonal coalescence, and ultra-sensitive perturbation sensing scaling as epsilon^(1/N).
Fully offline, thread-safe, CP1252-safe ASCII reporting.
"""

import cmath
import math
import time
import threading
from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple, Optional

STAGE: int = 282
STAGE_NAME: str = "Non-Hermitian Parity-Time Symmetric Open Quantum Engine & Exceptional Point Sensor"
SOVEREIGN_OPERATOR: str = "Senin (Senin Ali K P)"


@dataclass
class PTSpectrumResult:
    """Spectral analysis and phase state of a PT-symmetric system."""
    dimension: int
    omega_0: float
    gain_loss_gamma: float
    coupling_g: float
    eigenvalues: List[complex]
    pt_phase: str                               # "UNBROKEN_REAL", "EXCEPTIONAL_POINT", "BROKEN_COMPLEX"
    ep_distance: float                          # |g - gamma|
    perturbation_sensitivity_gain: float        # Enhancement factor over standard Hermitian linear response
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "omega_0": self.omega_0,
            "gain_loss_gamma": self.gain_loss_gamma,
            "coupling_g": self.coupling_g,
            "eigenvalues": [{"real": ev.real, "imag": ev.imag} for ev in self.eigenvalues],
            "pt_phase": self.pt_phase,
            "ep_distance": self.ep_distance,
            "perturbation_sensitivity_gain": self.perturbation_sensitivity_gain,
            "timestamp": self.timestamp,
        }


class NonHermitianPTSymmetricFabric:
    """
    Stage 282: Autonomous Parity-Time (PT) Symmetric Engine & Exceptional Point Sensor.
    Handles non-Hermitian Hamiltonians, pseudo-Hermitian invariants, and EP2/EP3 sensors.
    """

    def __init__(self, sovereign_operator: str = SOVEREIGN_OPERATOR) -> None:
        self.sovereign_operator: str = sovereign_operator
        self._lock: threading.RLock = threading.RLock()
        self._evaluations_count: int = 0
        self._history: List[PTSpectrumResult] = []
        self._last_result: Optional[PTSpectrumResult] = None

    def solve_dim2_spectrum(
        self,
        gain_loss_gamma: float = 0.5,
        coupling_g: float = 1.0,
        omega_0: float = 0.0,
    ) -> PTSpectrumResult:
        """
        Solves the classic 2x2 PT-symmetric dimer Hamiltonian:
        H = [[omega_0 + i*gamma, g],
             [g, omega_0 - i*gamma]]
        Eigenvalues: lambda_+- = omega_0 +- sqrt(g^2 - gamma^2)
        """
        with self._lock:
            gamma = float(gain_loss_gamma)
            g = float(coupling_g)
            w0 = float(omega_0)

            diff = g**2 - gamma**2
            ep_dist = abs(abs(g) - abs(gamma))

            if ep_dist < 1e-12:
                # Exactly at the Exceptional Point (EP2)
                phase = "EXCEPTIONAL_POINT"
                ev1 = complex(w0, 0.0)
                ev2 = complex(w0, 0.0)
            elif diff > 0.0:
                # Unbroken PT symmetry: purely real eigenvalues
                phase = "UNBROKEN_REAL"
                sq = math.sqrt(diff)
                ev1 = complex(w0 + sq, 0.0)
                ev2 = complex(w0 - sq, 0.0)
            else:
                # Broken PT symmetry: complex conjugate pairs
                phase = "BROKEN_COMPLEX"
                sq_imag = math.sqrt(-diff)
                ev1 = complex(w0, sq_imag)
                ev2 = complex(w0, -sq_imag)

            # Sensitivity boost compared to linear Hermitian shift:
            # At or near EP2: delta_lambda ~ sqrt(epsilon). Gain over epsilon is 1 / sqrt(max(ep_dist, 1e-7))
            sens_gain = 1.0 / math.sqrt(max(ep_dist, 1e-8)) if ep_dist < 1.0 else 1.0

            res = PTSpectrumResult(
                dimension=2,
                omega_0=w0,
                gain_loss_gamma=gamma,
                coupling_g=g,
                eigenvalues=[ev1, ev2],
                pt_phase=phase,
                ep_distance=ep_dist,
                perturbation_sensitivity_gain=sens_gain,
            )

            self._evaluations_count += 1
            self._last_result = res
            self._history.append(res)
            if len(self._history) > 100:
                self._history.pop(0)

            return res

    def evaluate_ep_sensor(
        self,
        perturbation_epsilon: float = 1e-6,
        order: int = 2,
        coupling_g: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Evaluates the exceptional-point perturbation sensor response.
        For order N (EP-N), frequency splitting scales as Delta_lambda = g * (epsilon / g)^(1/N).
        """
        with self._lock:
            eps = max(0.0, float(perturbation_epsilon))
            n = max(2, min(int(order), 4))
            g = max(1e-6, float(coupling_g))

            # Non-Hermitian EP splitting
            delta_ep = g * ((eps / g)**(1.0 / float(n)))

            # Conventional Hermitian linear splitting
            delta_hermitian = eps

            # Amplification ratio
            amplification = delta_ep / delta_hermitian if delta_hermitian > 0.0 else 1.0

            return {
                "order_n": n,
                "perturbation_epsilon": eps,
                "coupling_g": g,
                "ep_eigenvalue_splitting": delta_ep,
                "hermitian_splitting": delta_hermitian,
                "amplification_factor": amplification,
                "sensitivity_order": f"O(eps^(1/{n}))",
            }

    def solve_dim3_spectrum(
        self,
        gain_loss_gamma: float = 0.5,
        coupling_g: float = 1.0,
        omega_0: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Solves 3-site PT-symmetric trimer Hamiltonian:
        H = [[omega_0 + i*gamma, g, 0],
             [g, omega_0, g],
             [0, g, omega_0 - i*gamma]]
        Characteristic polynomial: (lambda - w0) * ((lambda - w0)^2 - (2*g^2 - gamma^2)) = 0
        Roots: lambda_0 = w0, lambda_+- = w0 +- sqrt(2*g^2 - gamma^2)
        EP occurs at gamma = sqrt(2) * g
        """
        with self._lock:
            gamma = float(gain_loss_gamma)
            g = float(coupling_g)
            w0 = float(omega_0)

            crit_gamma = math.sqrt(2.0) * g
            diff = 2.0 * (g**2) - (gamma**2)
            ep_dist = abs(gamma - crit_gamma)

            if ep_dist < 1e-12:
                phase = "EXCEPTIONAL_POINT"
                evs = [complex(w0, 0.0), complex(w0, 0.0), complex(w0, 0.0)]
            elif diff > 0.0:
                phase = "UNBROKEN_REAL"
                sq = math.sqrt(diff)
                evs = [complex(w0, 0.0), complex(w0 + sq, 0.0), complex(w0 - sq, 0.0)]
            else:
                phase = "BROKEN_COMPLEX"
                sq_imag = math.sqrt(-diff)
                evs = [complex(w0, 0.0), complex(w0, sq_imag), complex(w0, -sq_imag)]

            return {
                "dimension": 3,
                "omega_0": w0,
                "gain_loss_gamma": gamma,
                "coupling_g": g,
                "critical_gamma": crit_gamma,
                "pt_phase": phase,
                "ep_distance": ep_dist,
                "eigenvalues": [{"real": e.real, "imag": e.imag} for e in evs],
            }

    def format_ascii_status(self) -> str:
        """CP1252-safe ASCII table status."""
        with self._lock:
            last = self._last_result
            dim = last.dimension if last else 2
            gamma = last.gain_loss_gamma if last else 0.5
            g = last.coupling_g if last else 1.0
            phase = last.pt_phase if last else "UNBROKEN_REAL"
            ep_dist = last.ep_distance if last else 0.5
            gain = last.perturbation_sensitivity_gain if last else 1.4142

            lines = [
                "+====================================================================+",
                "|       STAGE 282: NON-HERMITIAN PT-SYMMETRIC QUANTUM FABRIC        |",
                "+====================================================================+",
                f"| Sovereign Operator  : {self.sovereign_operator:<44} |",
                f"| Evaluations Count   : {self._evaluations_count:<44} |",
                f"| Dimension (N-state) : {dim:<44} |",
                f"| Gain/Loss (gamma)   : {gamma:<44.6f} |",
                f"| Coupling (g)        : {g:<44.6f} |",
                f"| PT Phase State      : {phase:<44} |",
                f"| Distance to EP      : {ep_dist:<44.6e} |",
                f"| Sensor EP Boost     : {gain:<44.2f}x|",
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
                "last_result": self._last_result.to_dict() if self._last_result else None,
            }
