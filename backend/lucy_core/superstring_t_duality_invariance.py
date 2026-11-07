r"""
LUCY STAGE 298: Superstring Target Space T-Duality & Buscher Transformation Fabric
Sovereign Architect & Supreme Operator: Senin (Senin Ali K P)

Provides high-precision computational string theory target space duality (T-Duality) dynamics.
Implements the universal closed string compactification spectrum on S^1 of radius R:
M^2 = (n / R)^2 + (w * R / alpha')^2 + (2 / alpha') * (N_L + N_R - 2)
with fundamental T-duality invariance under radius inversion R <-> alpha' / R and winding-momentum
exchange n <-> w. Implements Buscher transformation rules for background metric G_munu,
antisymmetric Kalb-Ramond B_munu field, and dilaton field Phi:
Phi' = Phi - (1/2) * ln(G_00).
Fully offline, thread-safe, CP1252-safe ASCII reporting.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import math
import threading
import time

STAGE: int = 298
STAGE_NAME: str = "Superstring Target Space T-Duality & Buscher Transformation Fabric"
SOVEREIGN_OPERATOR: str = "Senin (Senin Ali K P)"

# String scale parameter alpha' (Regge slope) in Planck area units
DEFAULT_ALPHA_PRIME: float = 1.0


@dataclass
class StringMassSpectrumMetrics:
    """Metrics for compactified closed string state."""
    compact_radius_r: float
    dual_radius_r_dual: float                     # R' = alpha' / R
    momentum_number_n: int                        # KK momentum mode
    winding_number_w: int                         # Topological winding mode
    left_oscillator_level_nl: int
    right_oscillator_level_nr: int
    mass_squared: float
    dual_mass_squared: float                      # Mass with (R -> alpha'/R, n <-> w)
    t_duality_mass_difference: float              # |M^2(R, n, w) - M^2(R', w, n)| == 0
    is_t_dual_invariant: bool
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "compact_radius_r": self.compact_radius_r,
            "dual_radius_r_dual": self.dual_radius_r_dual,
            "momentum_number_n": self.momentum_number_n,
            "winding_number_w": self.winding_number_w,
            "left_oscillator_level_nl": self.left_oscillator_level_nl,
            "right_oscillator_level_nr": self.right_oscillator_level_nr,
            "mass_squared": self.mass_squared,
            "dual_mass_squared": self.dual_mass_squared,
            "t_duality_mass_difference": self.t_duality_mass_difference,
            "is_t_dual_invariant": self.is_t_dual_invariant,
            "timestamp": self.timestamp,
        }


class SuperstringTDualityInvarianceFabric:
    """
    Superstring Target Space Duality (T-Duality) Engine.
    Implements Buscher transformations and closed string KK/winding spectra.
    Self-dual radius (string scale): R_self = sqrt(alpha').
    """

    def __init__(self, alpha_prime: float = DEFAULT_ALPHA_PRIME) -> None:
        if alpha_prime <= 0:
            raise ValueError("Regge slope alpha' must be strictly positive.")
        self.alpha_prime: float = alpha_prime
        self.r_self_dual: float = math.sqrt(self.alpha_prime)
        self.operator: str = SOVEREIGN_OPERATOR
        self._lock = threading.RLock()
        self.evaluations_count: int = 0

    def compute_dual_radius(self, radius_r: float) -> float:
        """Computes T-dual radius R' = alpha' / R."""
        if radius_r <= 0:
            raise ValueError("Compactification radius R must be positive.")
        return self.alpha_prime / radius_r

    def compute_string_mass_squared(
        self,
        radius_r: float,
        momentum_n: int,
        winding_w: int,
        nl: int = 1,
        nr: int = 1,
    ) -> float:
        """
        Mass formula for closed bosonic/superstring on a circle of radius R:
        M^2 = (n / R)^2 + (w * R / alpha')^2 + (2 / alpha') * (N_L + N_R - 2)
        Level matching condition requires: N_R - N_L = n * w.
        """
        if radius_r <= 0:
            raise ValueError("Compactification radius R must be positive.")
        kk_term = (float(momentum_n) / radius_r)**2
        winding_term = (float(winding_w) * radius_r / self.alpha_prime)**2
        oscillator_term = (2.0 / self.alpha_prime) * float(nl + nr - 2)
        return kk_term + winding_term + oscillator_term

    def verify_t_duality_invariance(
        self,
        radius_r: float,
        momentum_n: int,
        winding_w: int,
        nl: int = 1,
        nr: int = 1,
    ) -> StringMassSpectrumMetrics:
        """
        Verifies exact spectrum identity:
        M^2(R, n, w) == M^2(alpha'/R, w, n).
        """
        with self._lock:
            self.evaluations_count += 1
            r_dual = self.compute_dual_radius(radius_r)

            m2_orig = self.compute_string_mass_squared(radius_r, momentum_n, winding_w, nl, nr)
            # Under T-duality: R -> R' and n <-> w
            m2_dual = self.compute_string_mass_squared(r_dual, winding_w, momentum_n, nl, nr)

            diff = abs(m2_orig - m2_dual)
            is_inv = diff < 1e-11

            return StringMassSpectrumMetrics(
                compact_radius_r=radius_r,
                dual_radius_r_dual=r_dual,
                momentum_number_n=momentum_n,
                winding_number_w=winding_w,
                left_oscillator_level_nl=nl,
                right_oscillator_level_nr=nr,
                mass_squared=m2_orig,
                dual_mass_squared=m2_dual,
                t_duality_mass_difference=diff,
                is_t_dual_invariant=is_inv,
            )

    def apply_buscher_transform(
        self,
        g_00: float,
        g_0i: float,
        g_ij: float,
        b_0i: float,
        b_ij: float,
        dilaton_phi: float,
    ) -> Dict[str, float]:
        """
        Applies Buscher T-duality transformation along x^0 isometry:
        G'_00 = 1 / G_00
        G'_0i = B_0i / G_00
        G'_ij = G_ij - (G_0i*G_0j - B_0i*B_0j) / G_00
        B'_0i = G_0i / G_00
        B'_ij = B_ij - (G_0i*B_0j - B_0i*G_0j) / G_00
        Phi'  = Phi - (1/2) * ln(G_00)
        """
        with self._lock:
            if g_00 <= 0:
                raise ValueError("Metric component G_00 must be positive.")
            g00_dual = 1.0 / g_00
            g0i_dual = b_0i / g_00
            b0i_dual = g_0i / g_00

            gij_dual = g_ij - (g_0i * g_0i - b_0i * b_0i) / g_00
            bij_dual = b_ij - (g_0i * b_0i - b_0i * g_0i) / g_00
            phi_dual = dilaton_phi - 0.5 * math.log(g_00)

            return {
                "g_00_prime": g00_dual,
                "g_0i_prime": g0i_dual,
                "g_ij_prime": gij_dual,
                "b_0i_prime": b0i_dual,
                "b_ij_prime": bij_dual,
                "dilaton_phi_prime": phi_dual,
            }

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "sovereign_operator": self.operator,
                "alpha_prime": self.alpha_prime,
                "self_dual_radius": self.r_self_dual,
                "evaluations_count": self.evaluations_count,
                "status": "OPERATIONAL",
            }
