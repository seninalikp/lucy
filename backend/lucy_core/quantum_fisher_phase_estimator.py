"""
LUCY STAGE 288: Quantum Optic Mach-Zehnder Non-Linear Phase Estimator & Quantum Fisher Information Engine
Sovereign Architect & Supreme Operator: Senin (Senin Ali K P)

Provides high-precision quantum metrology and parameter estimation: Quantum Fisher Information
(QFI) F_Q = 4*(Delta G)^2, Quantum Cramer-Rao Bound Delta_phi >= 1 / sqrt(nu * F_Q), Standard
Quantum Limit (SQL) 1 / sqrt(N), Heisenberg Limit 1 / N via N00N entangled states
|psi_N> = (|N,0> + |0,N>) / sqrt(2), squeezed vacuum enhancement, and Kerr non-linear
super-Heisenberg interferometry.
Fully offline, thread-safe, CP1252-safe ASCII reporting.
"""

import math
import time
import threading
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

STAGE: int = 288
STAGE_NAME: str = "Quantum Optic Mach-Zehnder Phase Estimator & Quantum Fisher Information Engine"
SOVEREIGN_OPERATOR: str = "Senin (Senin Ali K P)"


@dataclass
class FisherMetrologySnapshot:
    """State snapshot of quantum Fisher metrology and phase sensitivity."""
    state_type: str                              # "COHERENT_SQL", "N00N_HEISENBERG", "SQUEEZED_VACUUM", "NONLINEAR_KERR"
    mean_photon_number: float
    quantum_fisher_info: float
    cramer_rao_bound_radians: float
    standard_quantum_limit: float
    heisenberg_limit: float
    quantum_advantage_ratio: float               # Delta_phi_SQL / Delta_phi_actual
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state_type": self.state_type,
            "mean_photon_number": self.mean_photon_number,
            "quantum_fisher_info": self.quantum_fisher_info,
            "cramer_rao_bound_radians": self.cramer_rao_bound_radians,
            "standard_quantum_limit": self.standard_quantum_limit,
            "heisenberg_limit": self.heisenberg_limit,
            "quantum_advantage_ratio": self.quantum_advantage_ratio,
            "timestamp": self.timestamp,
        }


class QuantumFisherPhaseEstimatorFabric:
    """
    Stage 288: Autonomous Quantum Fisher Information & Mach-Zehnder Phase Estimator.
    Evaluates quantum precision bounds and simulated interferometer fringes.
    """

    def __init__(self, sovereign_operator: str = SOVEREIGN_OPERATOR) -> None:
        self.sovereign_operator: str = sovereign_operator
        self._lock: threading.RLock = threading.RLock()
        self._evaluations_count: int = 0
        self._history: List[FisherMetrologySnapshot] = []
        self._last_snapshot: Optional[FisherMetrologySnapshot] = None

    def calculate_quantum_fisher_info(
        self,
        mean_photons: float = 100.0,
        state_type: str = "N00N",
        squeezing_r: float = 1.0,
        kerr_chi: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Calculates Quantum Fisher Information (QFI) F_Q and minimum achievable phase uncertainty.
        - Coherent: F_Q = N -> Delta_phi = 1 / sqrt(N) (Standard Quantum Limit)
        - N00N state: F_Q = N^2 -> Delta_phi = 1 / N (Heisenberg Limit)
        - Squeezed: F_Q = N * exp(2*r) -> Delta_phi = exp(-r) / sqrt(N)
        - Non-linear Kerr: F_Q = N^4 * chi^2 -> Super-Heisenberg Delta_phi ~ 1 / N^2
        """
        with self._lock:
            n = max(1.0, float(mean_photons))
            st = state_type.strip().upper()
            r_sq = max(0.0, float(squeezing_r))
            chi = max(1e-4, float(kerr_chi))

            sql = 1.0 / math.sqrt(n)
            hl = 1.0 / n

            if st in ("N00N", "HEISENBERG", "ENTANGLED"):
                mode = "N00N_HEISENBERG"
                f_q = n**2
                delta_phi = 1.0 / math.sqrt(f_q)
            elif st in ("SQUEEZED", "SQUEEZED_VACUUM"):
                mode = "SQUEEZED_VACUUM"
                f_q = n * math.exp(2.0 * r_sq)
                delta_phi = 1.0 / math.sqrt(f_q)
            elif st in ("KERR", "NONLINEAR", "SUPER_HEISENBERG"):
                mode = "NONLINEAR_KERR"
                f_q = (n**4) * (chi**2)
                delta_phi = 1.0 / math.sqrt(f_q)
            else:
                mode = "COHERENT_SQL"
                f_q = n
                delta_phi = sql

            advantage = sql / delta_phi if delta_phi > 0 else 1.0

            snapshot = FisherMetrologySnapshot(
                state_type=mode,
                mean_photon_number=n,
                quantum_fisher_info=f_q,
                cramer_rao_bound_radians=delta_phi,
                standard_quantum_limit=sql,
                heisenberg_limit=hl,
                quantum_advantage_ratio=advantage,
            )

            self._evaluations_count += 1
            self._last_snapshot = snapshot
            self._history.append(snapshot)
            if len(self._history) > 100:
                self._history.pop(0)

            return snapshot.to_dict()

    def simulate_mach_zehnder_fringes(
        self,
        true_phase_rad: float = 0.5,
        n_photons: int = 10,
        state_type: str = "N00N",
        points: int = 40,
    ) -> Dict[str, Any]:
        """
        Simulates Mach-Zehnder interference fringes:
        - Coherent/Classical: Transmission T(phi) = cos^2(phi / 2) (period 2*pi)
        - N00N State: Parity / Transmission T(phi) = cos^2(N * phi / 2) (super-resolved period 2*pi / N)
        """
        with self._lock:
            n = max(1, int(n_photons))
            phi_true = float(true_phase_rad)
            st = state_type.strip().upper()
            is_noon = st in ("N00N", "HEISENBERG", "ENTANGLED")

            fringe_curve: List[Dict[str, float]] = []
            steps = max(10, min(points, 100))

            # Sweep from -pi to +pi
            for i in range(steps + 1):
                phi = -math.pi + (2.0 * math.pi * float(i) / float(steps))
                if is_noon:
                    # Super-resolution: N times faster oscillation
                    transmission = (math.cos(float(n) * phi / 2.0))**2
                else:
                    transmission = (math.cos(phi / 2.0))**2

                fringe_curve.append({
                    "phase_rad": phi,
                    "normalized_transmission": transmission,
                })

            # Evaluate at true phase
            transmission_at_true = (math.cos(float(n) * phi_true / 2.0))**2 if is_noon else (math.cos(phi_true / 2.0))**2

            return {
                "state_type": "N00N_SUPER_RESOLUTION" if is_noon else "CLASSICAL_MACH_ZEHNDER",
                "photon_number_n": n,
                "true_phase_rad": phi_true,
                "fringe_finesse_multiplier": float(n) if is_noon else 1.0,
                "transmission_at_true_phase": transmission_at_true,
                "total_fringe_points": len(fringe_curve),
                "fringes": fringe_curve,
            }

    def format_ascii_status(self) -> str:
        """CP1252-safe ASCII table representation."""
        with self._lock:
            last = self._last_snapshot
            mode = last.state_type if last else "N00N_HEISENBERG"
            n = last.mean_photon_number if last else 100.0
            fq = last.quantum_fisher_info if last else 10000.0
            qcrb = last.cramer_rao_bound_radians if last else 0.01
            sql = last.standard_quantum_limit if last else 0.1
            adv = last.quantum_advantage_ratio if last else 10.0

            lines = [
                "+====================================================================+",
                "|       STAGE 288: QUANTUM FISHER INFORMATION & METROLOGY FABRIC     |",
                "+====================================================================+",
                f"| Sovereign Operator  : {self.sovereign_operator:<44} |",
                f"| Evaluations Count   : {self._evaluations_count:<44} |",
                f"| Quantum State Mode  : {mode:<44} |",
                f"| Mean Photons (N)    : {n:<44.2f} |",
                f"| Quantum Fisher Info : {fq:<44.3e} |",
                f"| Cramer-Rao Bound    : {qcrb:<44.4e} rad |",
                f"| Shot-Noise SQL      : {sql:<44.4e} rad |",
                f"| Quantum Advantage   : {adv:<44.2f}x|",
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
                "last_snapshot": self._last_snapshot.to_dict() if self._last_snapshot else None,
            }
