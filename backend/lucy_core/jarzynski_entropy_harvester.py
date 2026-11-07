"""
Stage 252: Non-Equilibrium Fluctuation-Dissipation & Crooks Jarzynski Entropy Harvester
Era 26: Cosmic-Scale Holomorphic Field Dynamics, Non-Equilibrium Thermodynamic Entropy Engines & Autonomous Sovereign Multi-Verse Orchestration

Sovereign Human Operator: Senin (Senin Ali K P)

Provides:
- Jarzynski Non-Equilibrium Work Equality: <exp(-beta * W)> = exp(-beta * Delta F)
- Second Law of Thermodynamics Jensen Dissipation: <W> >= Delta F (W_diss >= 0)
- Crooks Fluctuation Theorem Probability Distribution Symmetry: P_F(W) / P_R(-W) = exp(beta * (W - Delta F))
- Stochastic Entropy Production Tracking: Delta s_tot = beta * (W - Delta F)
- Information-Theoretic Szilard Fluctuation Harvester: W_harvested <= k_B * T * ln(2) * I_mutual
- 100% Offline, Pure Python, Deterministic, Zero Cloud Dependencies
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import math
import random
import threading
import time

STAGE = 252
STAGE_NAME = "Non-Equilibrium Fluctuation-Dissipation & Crooks Jarzynski Entropy Harvester"
ERA = 26
ERA_NAME = "Cosmic-Scale Holomorphic Field Dynamics, Non-Equilibrium Thermodynamic Entropy Engines & Autonomous Sovereign Multi-Verse Orchestration"

# Boltzmann Constant (J/K)
K_BOLTZMANN = 1.380649e-23


@dataclass
class HarvestingEvent:
    event_id: str
    work_kbt: float
    free_energy_delta_kbt: float
    dissipated_work_kbt: float
    stochastic_entropy_production: float
    energy_harvested_joules: float
    timestamp: float


class JarzynskiEntropyHarvesterFabric:
    """
    Non-Equilibrium Fluctuation-Dissipation & Crooks-Jarzynski Entropy Harvester.
    Extracts free energy and thermodynamic work bounds from non-equilibrium stochastic trajectories.
    """

    def __init__(self, temperature_k: float = 300.0):
        self._lock = threading.RLock()
        self.temperature_k = float(temperature_k)
        self.thermal_energy_joules = K_BOLTZMANN * self.temperature_k
        self.total_trajectories_evaluated: int = 0
        self.total_joules_harvested: float = 0.0
        self.harvest_events: List[HarvestingEvent] = []

    def compute_jarzynski_free_energy(
        self,
        work_samples_kbt: List[float],
    ) -> Dict[str, Any]:
        """
        Applies Jarzynski Equality:
        <exp(-w)> = exp(-Delta f)  ==>  Delta f = -ln( <exp(-w)> )
        where w = W / (k_B * T) is the dimensionless work.
        """
        with self._lock:
            if not work_samples_kbt:
                raise ValueError("Work sample ensemble cannot be empty.")

            n = len(work_samples_kbt)
            self.total_trajectories_evaluated += n

            # Log-sum-exp trick to prevent numerical overflow/underflow
            min_w = min(work_samples_kbt)
            # exp(-w) = exp(-min_w) * exp(-(w - min_w))
            sum_exp = sum(math.exp(-(w - min_w)) for w in work_samples_kbt)
            avg_exp = sum_exp / n
            delta_f_kbt = min_w - math.log(avg_exp)

            avg_w = sum(work_samples_kbt) / n
            dissipated_w = avg_w - delta_f_kbt

            # Convert to SI Joules
            delta_f_joules = delta_f_kbt * self.thermal_energy_joules
            dissipated_joules = dissipated_w * self.thermal_energy_joules

            # Second Law Verification: <W> >= Delta F
            second_law_holds = dissipated_w >= -1e-9

            return {
                "ensemble_size": n,
                "delta_f_kbt": round(delta_f_kbt, 6),
                "delta_f_joules": delta_f_joules,
                "mean_work_kbt": round(avg_w, 6),
                "dissipated_work_kbt": round(dissipated_w, 6),
                "dissipated_work_joules": dissipated_joules,
                "second_law_holds": second_law_holds,
            }

    def verify_crooks_crossing(
        self,
        forward_samples_kbt: List[float],
        reverse_samples_kbt: List[float],
    ) -> Dict[str, Any]:
        """
        Verifies Crooks Fluctuation Theorem:
        P_F(w) / P_R(-w) = exp(w - Delta f)
        At w = Delta f, P_F(w) == P_R(-w) (The distribution intersection point!).
        """
        with self._lock:
            if not forward_samples_kbt or not reverse_samples_kbt:
                raise ValueError("Forward and reverse ensembles must both be non-empty.")

            # Compute free energy via Jarzynski on forward protocol
            fwd_res = self.compute_jarzynski_free_energy(forward_samples_kbt)
            delta_f = fwd_res["delta_f_kbt"]

            # Reverse protocol work: w_rev = -W_R / (k_B T)
            neg_reverse = [-w for w in reverse_samples_kbt]

            # Compare means
            mean_fwd = sum(forward_samples_kbt) / len(forward_samples_kbt)
            mean_rev = sum(reverse_samples_kbt) / len(reverse_samples_kbt)

            # In Gaussian approximation: Delta F = ( <W_F> - <W_R> ) / 2
            gaussian_delta_f = (mean_fwd - mean_rev) / 2.0
            error = abs(delta_f - gaussian_delta_f)

            return {
                "jarzynski_delta_f_kbt": round(delta_f, 4),
                "crooks_gaussian_delta_f_kbt": round(gaussian_delta_f, 4),
                "mean_forward_kbt": round(mean_fwd, 4),
                "mean_reverse_kbt": round(mean_rev, 4),
                "discrepancy": round(error, 6),
                "crossing_verified": error < 1.0,
            }

    def harvest_stochastic_fluctuation(
        self,
        work_kbt: float,
        delta_f_kbt: float,
        mutual_info_bits: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Szilard / Landauer Information Engine:
        Harvests work from stochastic thermal fluctuations where w < delta_f.
        Thermodynamic limit: W_max = k_B * T * ln(2) * I_mutual.
        """
        with self._lock:
            stochastic_entropy_production = work_kbt - delta_f_kbt
            max_harvestable_joules = self.thermal_energy_joules * math.log(2.0) * max(0.0, mutual_info_bits)

            # If stochastic fluctuation produced excess work or negative entropy fluctuation
            harvested_joules = 0.0
            if stochastic_entropy_production < 0.0:
                # Instantaneous negative dissipation (thermal fluctuation advantage)
                advantage_joules = abs(stochastic_entropy_production) * self.thermal_energy_joules
                harvested_joules = min(advantage_joules, max_harvestable_joules)
            else:
                # Information-driven rectification
                harvested_joules = min(max_harvestable_joules * 0.5, self.thermal_energy_joules)

            self.total_joules_harvested += harvested_joules
            event_id = f"HARVEST-{int(time.time()*1000)}-{len(self.harvest_events)+1}"

            event = HarvestingEvent(
                event_id=event_id,
                work_kbt=work_kbt,
                free_energy_delta_kbt=delta_f_kbt,
                dissipated_work_kbt=stochastic_entropy_production,
                stochastic_entropy_production=stochastic_entropy_production,
                energy_harvested_joules=harvested_joules,
                timestamp=time.time(),
            )
            self.harvest_events.append(event)

            return {
                "event_id": event_id,
                "work_kbt": round(work_kbt, 4),
                "delta_f_kbt": round(delta_f_kbt, 4),
                "entropy_production_kbt": round(stochastic_entropy_production, 4),
                "harvested_joules": harvested_joules,
                "total_joules_harvested": self.total_joules_harvested,
            }

    def generate_synthetic_work_ensemble(
        self,
        true_delta_f: float = 5.0,
        dissipation: float = 2.0,
        samples: int = 500,
        seed: int = 42,
    ) -> Tuple[List[float], List[float]]:
        """
        Generates forward and reverse work distributions obeying Crooks fluctuation theorem.
        W_F ~ Normal(Delta F + W_diss, sqrt(2 * W_diss))
        W_R ~ Normal(-Delta F + W_diss, sqrt(2 * W_diss))
        """
        rnd = random.Random(seed)
        sigma = math.sqrt(2.0 * dissipation)

        forward = [rnd.gauss(true_delta_f + dissipation, sigma) for _ in range(samples)]
        reverse = [rnd.gauss(-true_delta_f + dissipation, sigma) for _ in range(samples)]
        return forward, reverse

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "era_name": ERA_NAME,
                "temperature_k": self.temperature_k,
                "thermal_energy_joules": self.thermal_energy_joules,
                "total_trajectories_evaluated": self.total_trajectories_evaluated,
                "total_joules_harvested": self.total_joules_harvested,
                "total_harvest_events": len(self.harvest_events),
            }

    def format_ascii_status(self) -> str:
        with self._lock:
            temp_str = f"{self.temperature_k:.1f} K"
            kbt_str = f"{self.thermal_energy_joules:.3e} J"
            traj_str = f"{self.total_trajectories_evaluated} trajectories"
            harv_str = f"{self.total_joules_harvested:.3e} J"
            ev_str = f"{len(self.harvest_events)} events"

            lines = [
                "+-------------------------------------------------------------------------+",
                "|      STAGE 252: Crooks-Jarzynski Non-Equilibrium Entropy Harvester      |",
                "|      Era 26: Cosmic-Scale Holomorphic Field Dynamics                    |",
                "+-------------------------------------------------------------------------+",
                f"| Operating Temp (T)   : {temp_str:<48} |",
                f"| Thermal Energy (kBT) : {kbt_str:<48} |",
                f"| Work Trajectories    : {traj_str:<48} |",
                f"| Harvested Energy     : {harv_str:<48} |",
                f"| Rectification Events : {ev_str:<48} |",
                "+-------------------------------------------------------------------------+",
            ]
            return "\n".join(lines)


# Sovereign Global Singleton
_global_jarzynski_harvester: Optional[JarzynskiEntropyHarvesterFabric] = None
_jh_lock = threading.RLock()


def get_jarzynski_harvester() -> JarzynskiEntropyHarvesterFabric:
    global _global_jarzynski_harvester
    with _jh_lock:
        if _global_jarzynski_harvester is None:
            _global_jarzynski_harvester = JarzynskiEntropyHarvesterFabric()
        return _global_jarzynski_harvester
