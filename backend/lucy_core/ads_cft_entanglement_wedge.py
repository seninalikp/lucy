"""
Stage 262: Holographic AdS/CFT Conformal Boundary-to-Bulk Dictionary & Ryu-Takayanagi Entanglement Wedge
Era 27: Cosmological Gauge Invariance, Non-Abelian Yang-Mills Fiber Bundles & Sovereign Trans-Planetary Unified Field Synthesis

Sovereign Human Operator: Senin (Senin Ali K P)

Provides:
- AdS_3 / CFT_2 Holographic Duality Poincare Patch Metric: ds^2 = (L^2 / z^2) * (dz^2 - dt^2 + dx^2)
- Brown-Henneaux Conformal Central Charge: c = 3 * L / (2 * G_N)
- Ryu-Takayanagi Holographic Entanglement Entropy Formula: S_A = Area(gamma_A) / (4 * G_N) = (c / 3) * ln(l / epsilon)
- Bulk Minimal Geodesic Profile & Entanglement Wedge Boundary Reconstruction W_E(A)
- Holographic Mutual Information I(A:B) Disentanglement Phase Transition & Subregion-Subregion Duality
- 100% Offline, Pure Python, Deterministic, Zero Cloud Dependencies
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import math
import threading

STAGE = 262
STAGE_NAME = "Holographic AdS/CFT Boundary-to-Bulk Dictionary & Ryu-Takayanagi Entanglement Wedge"
ERA = 27
ERA_NAME = "Cosmological Gauge Invariance, Non-Abelian Yang-Mills Fiber Bundles & Sovereign Trans-Planetary Unified Field Synthesis"


@dataclass
class EntanglementWedgeState:
    subsystem_range: Tuple[float, float]
    subsystem_length: float
    max_bulk_depth_z: float
    entanglement_entropy: float
    central_charge: float
    is_entangled: bool


class AdSCFTEntanglementWedgeFabric:
    """
    AdS/CFT Holographic Dictionary & Ryu-Takayanagi Entanglement Wedge Fabric.
    Reconstructs bulk spatial geometry from boundary conformal quantum entanglement.
    """

    def __init__(
        self,
        ads_radius_l: float = 1.0,
        newton_constant_gn: float = 0.25,
        default_uv_cutoff_eps: float = 1e-3,
    ):
        self._lock = threading.RLock()
        self.L = float(ads_radius_l)
        self.gn = float(newton_constant_gn)
        self.eps = float(default_uv_cutoff_eps)

        # Brown-Henneaux central charge: c = 3 * L / (2 * G_N)
        self.central_charge = (3.0 * self.L) / (2.0 * self.gn)

        self.total_entropy_evaluations: int = 0
        self.total_wedge_reconstructions: int = 0

    def compute_ryu_takayanagi_entropy(
        self,
        subsystem_length: float,
        uv_cutoff: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Computes Ryu-Takayanagi entanglement entropy:
        S_A = (c / 3) * ln(l / eps).
        """
        with self._lock:
            self.total_entropy_evaluations += 1
            l_val = max(1e-9, float(subsystem_length))
            eps_val = uv_cutoff if uv_cutoff is not None else self.eps
            if l_val <= eps_val:
                # Subsystem smaller than UV regulator
                return {
                    "subsystem_length": l_val,
                    "uv_cutoff": eps_val,
                    "entanglement_entropy": 0.0,
                    "central_charge": self.central_charge,
                    "geodesic_length": 0.0,
                }

            # Geodesic length: Area(gamma_A) = 2 * L * ln(l / eps)
            geodesic_len = 2.0 * self.L * math.log(l_val / eps_val)
            s_a = geodesic_len / (4.0 * self.gn)

            return {
                "subsystem_length": round(l_val, 6),
                "uv_cutoff": eps_val,
                "entanglement_entropy": round(s_a, 6),
                "central_charge": round(self.central_charge, 4),
                "geodesic_length": round(geodesic_len, 6),
                "max_bulk_penetration_z": round(l_val / 2.0, 6),
            }

    def compute_bulk_geodesic_coordinates(
        self,
        x_start: float,
        x_end: float,
        num_points: int = 30,
    ) -> List[Tuple[float, float]]:
        """
        Computes the semicircular RT minimal surface into the bulk:
        (x - x_mid)^2 + z^2 = (l / 2)^2.
        """
        with self._lock:
            self.total_wedge_reconstructions += 1
            l_val = abs(x_end - x_start)
            r = l_val / 2.0
            x_mid = (x_start + x_end) / 2.0

            coords = []
            for i in range(num_points + 1):
                # Angle theta from 0 to pi
                theta = (math.pi * i) / num_points
                # Displace slightly from boundary to respect UV cutoff eps
                sin_theta = math.sin(theta)
                z = max(self.eps, r * sin_theta)
                x = x_mid - r * math.cos(theta)
                coords.append((round(x, 4), round(z, 4)))

            return coords

    def is_in_entanglement_wedge(
        self,
        x: float,
        z: float,
        x_start: float,
        x_end: float,
    ) -> bool:
        """
        Checks whether bulk point (x, z) lies within the entanglement wedge W_E(A).
        Condition: point must be under the geodesic dome:
        (x - x_mid)^2 + z^2 <= (l / 2)^2 and z >= 0.
        """
        with self._lock:
            l_val = abs(x_end - x_start)
            r = l_val / 2.0
            x_mid = (x_start + x_end) / 2.0

            dist_sq = (x - x_mid) ** 2 + z ** 2
            return (dist_sq <= r ** 2 + 1e-9) and (z >= 0.0)

    def compute_holographic_mutual_information(
        self,
        l_a: float,
        l_b: float,
        separation_d: float,
    ) -> Dict[str, Any]:
        """
        Computes mutual information I(A: B) = S_A + S_B - S_{A U B}.
        In AdS/CFT, exhibits a sharp Hawking-Page-like entanglement phase transition:
        - When d is small (connected phase): I(A: B) > 0.
        - When d is large (disconnected phase): I(A: B) = 0 identically.
        """
        with self._lock:
            s_a = self.compute_ryu_takayanagi_entropy(l_a)["entanglement_entropy"]
            s_b = self.compute_ryu_takayanagi_entropy(l_b)["entanglement_entropy"]

            # Disconnected geodesic candidate: S_A + S_B
            s_disconnected = s_a + s_b

            # Connected geodesic candidate across A and B:
            # Spans from start of A to end of B (length l_a + d + l_b) + interior gap (length d)
            s_union_connected = (
                self.compute_ryu_takayanagi_entropy(l_a + separation_d + l_b)["entanglement_entropy"]
                + self.compute_ryu_takayanagi_entropy(separation_d)["entanglement_entropy"]
            )

            # Minimal surface picks the configuration with minimal area
            if s_union_connected < s_disconnected:
                s_aub = s_union_connected
                phase = "CONNECTED_ENTANGLED"
                i_ab = s_disconnected - s_aub
            else:
                s_aub = s_disconnected
                phase = "DISCONNECTED_DISENTANGLED"
                i_ab = 0.0

            return {
                "subsystem_a_len": l_a,
                "subsystem_b_len": l_b,
                "separation_d": separation_d,
                "entropy_a": s_a,
                "entropy_b": s_b,
                "entropy_union": round(s_aub, 6),
                "mutual_information": round(max(0.0, i_ab), 6),
                "holographic_phase": phase,
            }

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "era_name": ERA_NAME,
                "ads_radius_l": self.L,
                "newton_constant_gn": self.gn,
                "central_charge": self.central_charge,
                "uv_cutoff_eps": self.eps,
                "total_entropy_evaluations": self.total_entropy_evaluations,
                "total_wedge_reconstructions": self.total_wedge_reconstructions,
            }

    def format_ascii_status(self) -> str:
        with self._lock:
            c_str = f"c = {self.central_charge:.2f} (Brown-Henneaux)"
            met_str = f"L = {self.L:.2f}, G_N = {self.gn:.3f}"
            rt_str = f"{self.total_entropy_evaluations} RT entropy evals"
            wdg_str = f"{self.total_wedge_reconstructions} wedge profiles"

            lines = [
                "+-------------------------------------------------------------------------+",
                "|      STAGE 262: Holographic AdS/CFT Ryu-Takayanagi Entanglement Wedge   |",
                "|      Era 27: Cosmological Gauge Invariance                              |",
                "+-------------------------------------------------------------------------+",
                f"| Conformal Central Charge: {c_str:<48} |",
                f"| Bulk Metric Parameters : {met_str:<48} |",
                f"| Entanglement Entropy   : {rt_str:<48} |",
                f"| Wedge Reconstructions  : {wdg_str:<48} |",
                "+-------------------------------------------------------------------------+",
            ]
            return "\n".join(lines)


# Sovereign Global Singleton
_global_entanglement_wedge_fabric: Optional[AdSCFTEntanglementWedgeFabric] = None
_wedge_lock = threading.RLock()


def get_entanglement_wedge_fabric() -> AdSCFTEntanglementWedgeFabric:
    global _global_entanglement_wedge_fabric
    with _wedge_lock:
        if _global_entanglement_wedge_fabric is None:
            _global_entanglement_wedge_fabric = AdSCFTEntanglementWedgeFabric()
        return _global_entanglement_wedge_fabric
