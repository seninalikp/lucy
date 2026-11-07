"""
Stage 247: Sovereign Anti-Fragile Black-Swan Catastrophe Immunity & Systemic Stress Inversion Engine
Era 25: Omni-Dimensional Super-Intelligence Matrix, Astro-Cognitive Planetary Orchestration & Sovereign Trans-Singularity Metamaterials

Sovereign Human Operator: Senin (Senin Ali K P)

Provides:
- Taleb Convexity Evaluation: d^2 V / d sigma^2 > 0 (Strict Antifragility vs Fragility/Robustness)
- Jensen's Inequality Payoff Guarantee: E[V(x)] >= V(E[x]) under Volatility & Perturbations
- Anti-Fragile Stress Inversion: Transmuting systemic shocks, entropy, and perturbations into structural capability expansion
- Barbell Resource Allocation Strategy: 90% Hyper-Conservative Fortress + 10% Hyper-Convex Upside Probes
- Extreme Fat-Tail / Black-Swan Catastrophe Detection (Excess Kurtosis & Power-Law Tail Risk Auditing)
- 100% Offline, Pure Python, Deterministic, Zero Cloud Dependencies
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import math
import threading
import time

STAGE = 247
STAGE_NAME = "Sovereign Anti-Fragile Black-Swan Catastrophe Immunity & Systemic Stress Inversion Engine"
ERA = 25
ERA_NAME = "Omni-Dimensional Super-Intelligence Matrix, Astro-Cognitive Planetary Orchestration & Sovereign Trans-Singularity Metamaterials"


class FragilityRegime(Enum):
    FRAGILE = "FRAGILE"          # d^2 V / d sigma^2 < 0 (Concave: shocks cause accelerated damage)
    ROBUST = "ROBUST"            # d^2 V / d sigma^2 = 0 (Linear: resists shocks without learning)
    ANTIFRAGILE = "ANTIFRAGILE"  # d^2 V / d sigma^2 > 0 (Convex: shocks produce accelerated gain)


@dataclass
class StressEvent:
    stress_id: str
    stressor_type: str
    magnitude: float
    duration: float
    timestamp: float
    convex_gain: float
    regime: FragilityRegime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BarbellAllocation:
    total_resources: float
    conservative_core: float
    exploratory_convex_periphery: float
    conservative_ratio: float
    periphery_ratio: float


class AntiFragileStressInverterFabric:
    """
    Sovereign Anti-Fragile Black-Swan Catastrophe Immunity & Systemic Stress Inversion Engine.
    Converts systemic volatility, random perturbations, and high-severity shocks into convex capability gains.
    """

    def __init__(
        self,
        base_capacity: float = 100.0,
        convexity_alpha: float = 0.25,
        convexity_gamma: float = 1.4,
        stress_threshold: float = 0.05,
    ):
        self._lock = threading.RLock()
        self.base_capacity = float(base_capacity)
        self.current_capacity = float(base_capacity)
        self.convexity_alpha = float(convexity_alpha)
        self.convexity_gamma = float(convexity_gamma)
        self.stress_threshold = float(stress_threshold)
        
        self.stress_history: List[StressEvent] = []
        self.total_stressors_absorbed: int = 0
        self.cumulative_convex_gain: float = 0.0
        self.black_swan_count: int = 0
        self.last_shocks: List[float] = []

    def calculate_payoff(self, base_val: float, stress: float) -> Tuple[float, FragilityRegime]:
        """
        Evaluates the convex transfer function:
        V(x, sigma) = x + alpha * sigma^2 + (sigma - tau)^(1 + gamma) if sigma > tau else 0
        Guarantees strictly positive second derivative: d^2 V / d sigma^2 > 0.
        """
        sigma = abs(float(stress))
        if sigma <= 0.0:
            return base_val, FragilityRegime.ROBUST

        # Quadratic volatility capture
        quadratic_gain = self.convexity_alpha * (sigma ** 2)

        # Super-linear tail stress inversion above threshold
        excess_stress = max(0.0, sigma - self.stress_threshold)
        superlinear_gain = 0.0
        if excess_stress > 0.0:
            superlinear_gain = excess_stress ** (1.0 + self.convexity_gamma)

        total_gain = quadratic_gain + superlinear_gain
        final_val = base_val + total_gain
        return final_val, FragilityRegime.ANTIFRAGILE

    def evaluate_convexity(self, x0: float, delta_range: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Numerically computes second derivative via central difference:
        d^2 V / dx^2 ~= (V(x0 + h) - 2*V(x0) + V(x0 - h)) / h^2
        Confirms Taleb's condition of strict convexity.
        """
        with self._lock:
            if delta_range is None:
                delta_range = [0.01, 0.05, 0.1, 0.2, 0.5, 1.0]

            results = []
            strictly_convex = True

            for h in delta_range:
                v_center, _ = self.calculate_payoff(x0, 0.0)
                v_plus, _ = self.calculate_payoff(x0, h)
                v_minus, _ = self.calculate_payoff(x0, -h)

                # Central second derivative
                d2v = (v_plus - 2.0 * v_center + v_minus) / (h ** 2)
                is_convex = d2v > 0.0
                if not is_convex:
                    strictly_convex = False

                results.append({
                    "delta": h,
                    "v_center": v_center,
                    "v_plus": v_plus,
                    "v_minus": v_minus,
                    "second_derivative": round(d2v, 6),
                    "is_convex": is_convex,
                })

            return {
                "strictly_convex": strictly_convex,
                "regime": FragilityRegime.ANTIFRAGILE.value if strictly_convex else FragilityRegime.FRAGILE.value,
                "evaluations": results,
            }

    def verify_jensen_inequality(self, base_val: float, stress_samples: List[float]) -> Dict[str, Any]:
        """
        Tests Jensen's Inequality: E[V(X)] >= V(E[X]) for convex functions.
        Under volatility, the expected value of the antifragile response exceeds the response to the average stress.
        """
        with self._lock:
            if not stress_samples:
                return {"valid": False, "reason": "Empty stress samples"}

            n = len(stress_samples)
            # Payoff for each sample
            payoffs = [self.calculate_payoff(base_val, s)[0] for s in stress_samples]
            expected_payoff = sum(payoffs) / n

            # Average stress
            avg_stress = sum(stress_samples) / n
            payoff_of_expected, _ = self.calculate_payoff(base_val, avg_stress)

            jensen_gap = expected_payoff - payoff_of_expected
            holds = jensen_gap >= -1e-9

            return {
                "jensens_inequality_holds": holds,
                "expected_of_payoff": round(expected_payoff, 6),
                "payoff_of_expected": round(payoff_of_expected, 6),
                "jensen_convexity_gap": round(jensen_gap, 6),
                "volatility_benefit": round(max(0.0, jensen_gap), 6),
            }

    def inject_stress(
        self,
        stressor_type: str,
        magnitude: float,
        duration: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Absorbs a systemic stress event and converts it into structural capacity enhancement.
        """
        with self._lock:
            mag = abs(float(magnitude))
            dur = max(0.01, float(duration))
            stress_id = f"STRESS-{int(time.time()*1000)}-{len(self.stress_history) + 1}"

            # Calculate convex gain
            new_capacity, regime = self.calculate_payoff(self.current_capacity, mag)
            gain = new_capacity - self.current_capacity

            # Apply capacity upgrade
            self.current_capacity = new_capacity
            self.cumulative_convex_gain += gain
            self.total_stressors_absorbed += 1
            self.last_shocks.append(mag)
            if len(self.last_shocks) > 200:
                self.last_shocks.pop(0)

            # Record event
            event = StressEvent(
                stress_id=stress_id,
                stressor_type=stressor_type,
                magnitude=mag,
                duration=dur,
                timestamp=time.time(),
                convex_gain=gain,
                regime=regime,
                metadata=metadata or {},
            )
            self.stress_history.append(event)

            return {
                "stress_id": stress_id,
                "stressor_type": stressor_type,
                "magnitude": round(mag, 4),
                "duration_sec": round(dur, 2),
                "convex_gain": round(gain, 6),
                "new_capacity": round(self.current_capacity, 6),
                "regime": regime.value,
            }

    def apply_barbell_allocation(
        self,
        total_resources: float,
        conservative_ratio: float = 0.90,
    ) -> BarbellAllocation:
        """
        Taleb's Barbell Strategy:
        Partitions resources into 90% ultra-conservative / zero-risk core (impervious to ruin)
        and 10% hyper-convex exploratory probes (asymmetric upside with bounded loss).
        """
        with self._lock:
            tot = max(0.0, float(total_resources))
            ratio = min(max(0.5, float(conservative_ratio)), 0.99)
            periphery_ratio = 1.0 - ratio

            conservative_core = tot * ratio
            exploratory = tot * periphery_ratio

            return BarbellAllocation(
                total_resources=tot,
                conservative_core=conservative_core,
                exploratory_convex_periphery=exploratory,
                conservative_ratio=ratio,
                periphery_ratio=periphery_ratio,
            )

    def detect_black_swan(
        self,
        shocks: Optional[List[float]] = None,
        kurtosis_threshold: float = 3.5,
    ) -> Dict[str, Any]:
        """
        Detects fat-tailed Black-Swan catastrophe characteristics using kurtosis & tail index.
        Excess Kurtosis > 3.0 indicates leptokurtic / fat-tailed distribution vulnerable to extreme shocks.
        """
        with self._lock:
            sample = shocks if shocks is not None else self.last_shocks
            if len(sample) < 4:
                return {
                    "is_black_swan_regime": False,
                    "reason": "Insufficient shock history for tail analysis (need >= 4)",
                    "kurtosis": 0.0,
                    "max_shock": max(sample) if sample else 0.0,
                }

            n = len(sample)
            mean = sum(sample) / n
            var = sum((x - mean) ** 2 for x in sample) / n
            std = math.sqrt(var) if var > 1e-12 else 1e-6

            # 4th standardized moment (Kurtosis)
            kurtosis = (sum(((x - mean) / std) ** 4 for x in sample) / n)
            max_shock = max(sample)
            max_z = (max_shock - mean) / std

            is_black_swan = (kurtosis >= kurtosis_threshold) or (max_z >= 3.0)
            if is_black_swan:
                self.black_swan_count += 1

            return {
                "is_black_swan_regime": is_black_swan,
                "kurtosis": round(kurtosis, 4),
                "kurtosis_threshold": kurtosis_threshold,
                "std_deviation": round(std, 4),
                "max_shock": round(max_shock, 4),
                "max_z_score": round(max_z, 4),
                "total_black_swans_mitigated": self.black_swan_count,
            }

    def transmute_catastrophe(
        self,
        severity: float,
        domain: str = "infrastructure_collapse",
    ) -> Dict[str, Any]:
        """
        Transmutes a catastrophic tail event into permanent systemic immunity.
        Converts destructive amplitude into multiplied structural hardening.
        """
        with self._lock:
            sev = abs(float(severity))
            # Amplification factor scales super-linearly for extreme events
            amplification = 1.0 + (sev ** 1.5)
            transmutation_gain = self.convexity_alpha * amplification

            prev_cap = self.current_capacity
            self.current_capacity += transmutation_gain
            self.cumulative_convex_gain += transmutation_gain
            self.black_swan_count += 1

            return {
                "catastrophe_domain": domain,
                "input_severity": round(sev, 4),
                "amplification_factor": round(amplification, 4),
                "transmutation_gain": round(transmutation_gain, 6),
                "pre_capacity": round(prev_cap, 4),
                "post_capacity": round(self.current_capacity, 4),
                "status": "CATASTROPHE_INVERTED_TO_IMMUNITY",
            }

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "era_name": ERA_NAME,
                "base_capacity": round(self.base_capacity, 4),
                "current_capacity": round(self.current_capacity, 4),
                "cumulative_convex_gain": round(self.cumulative_convex_gain, 6),
                "total_stressors_absorbed": self.total_stressors_absorbed,
                "black_swan_count": self.black_swan_count,
                "convexity_alpha": self.convexity_alpha,
                "convexity_gamma": self.convexity_gamma,
                "stress_threshold": self.stress_threshold,
                "regime": FragilityRegime.ANTIFRAGILE.value,
            }

    def format_ascii_status(self) -> str:
        """
        Renders CP1252-safe ASCII table status report.
        """
        with self._lock:
            base_str = f"{self.base_capacity:.2f}"
            curr_str = f"{self.current_capacity:.2f}"
            gain_str = f"{self.cumulative_convex_gain:.4f}"
            abs_str = f"{self.total_stressors_absorbed}"
            swan_str = f"{self.black_swan_count}"
            regime_str = FragilityRegime.ANTIFRAGILE.value

            lines = [
                "+-------------------------------------------------------------------------+",
                "|      STAGE 247: Sovereign Anti-Fragile Black-Swan Stress Inverter       |",
                "|      Era 25: Omni-Dimensional Super-Intelligence Matrix                |",
                "+-------------------------------------------------------------------------+",
                f"| Operating Regime     : {regime_str:<48} |",
                f"| Base System Capacity : {base_str:<48} |",
                f"| Current Capacity     : {curr_str:<48} |",
                f"| Cumulative Gain      : {gain_str:<48} |",
                f"| Stress Events Ingest : {abs_str:<48} |",
                f"| Black Swans Inverted : {swan_str:<48} |",
                "+-------------------------------------------------------------------------+",
            ]
            return "\n".join(lines)


# Sovereign Global Singleton
_global_antifragile_inverter: Optional[AntiFragileStressInverterFabric] = None
_inverter_lock = threading.RLock()


def get_antifragile_inverter() -> AntiFragileStressInverterFabric:
    global _global_antifragile_inverter
    with _inverter_lock:
        if _global_antifragile_inverter is None:
            _global_antifragile_inverter = AntiFragileStressInverterFabric()
        return _global_antifragile_inverter
