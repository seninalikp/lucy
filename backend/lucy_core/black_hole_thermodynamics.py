"""
LUCY STAGE 281: Black Hole Holographic Thermodynamics & Bekenstein-Hawking Entropy Engine
Sovereign Architect & Supreme Operator: Senin (Senin Ali K P)

Provides high-precision computational physics and relativistic thermodynamics for
Schwarzschild and Kerr black holes, holographic Bekenstein-Hawking entropy, Hawking
radiation temperature, evaporation timescales, and unitary Page curve entropy dynamics.
Fully offline, thread-safe, CP1252-safe ASCII reporting.
"""

import math
import time
import threading
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

STAGE: int = 281
STAGE_NAME: str = "Black Hole Holographic Thermodynamics & Bekenstein-Hawking Entropy Engine"
SOVEREIGN_OPERATOR: str = "Senin (Senin Ali K P)"

# Fundamental Physical Constants (CODATA 2018 / SI Units)
C_SPEED_OF_LIGHT: float = 299792458.0              # m/s
G_GRAVITATIONAL_CONST: float = 6.67430e-11        # m^3 / (kg * s^2)
HBAR_PLANCK_REDUCED: float = 1.054571817e-34      # J * s
KB_BOLTZMANN: float = 1.380649e-23                # J / K
PLANCK_LENGTH: float = math.sqrt((HBAR_PLANCK_REDUCED * G_GRAVITATIONAL_CONST) / (C_SPEED_OF_LIGHT**3)) # ~1.616255e-35 m
SOLAR_MASS_KG: float = 1.98847e30                 # kg


@dataclass
class BlackHoleMetrics:
    """Thermodynamic and geometric metric state of a black hole."""
    mass_kg: float
    mass_solar: float
    spin_parameter: float                         # Dimensionless Kerr spin a* in [0, 1)
    schwarzschild_radius_m: float
    horizon_radius_m: float
    horizon_area_m2: float
    planck_area_units: float                      # A / (4 * lp^2) = Dimensionless entropy
    bekenstein_hawking_entropy_jk: float          # S_BH in J/K
    dimensionless_entropy: float                  # S_BH / k_B
    hawking_temperature_k: float                  # T_H in Kelvin
    surface_gravity_ms2: float                    # kappa in m/s^2
    hawking_luminosity_w: float                   # P_H in Watts
    evaporation_lifetime_s: float                 # t_evap in seconds
    page_time_s: float                            # t_Page in seconds
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mass_kg": self.mass_kg,
            "mass_solar": self.mass_solar,
            "spin_parameter": self.spin_parameter,
            "schwarzschild_radius_m": self.schwarzschild_radius_m,
            "horizon_radius_m": self.horizon_radius_m,
            "horizon_area_m2": self.horizon_area_m2,
            "planck_area_units": self.planck_area_units,
            "bekenstein_hawking_entropy_jk": self.bekenstein_hawking_entropy_jk,
            "dimensionless_entropy": self.dimensionless_entropy,
            "hawking_temperature_k": self.hawking_temperature_k,
            "surface_gravity_ms2": self.surface_gravity_ms2,
            "hawking_luminosity_w": self.hawking_luminosity_w,
            "evaporation_lifetime_s": self.evaporation_lifetime_s,
            "page_time_s": self.page_time_s,
            "timestamp": self.timestamp,
        }


class BlackHoleThermodynamicsFabric:
    """
    Stage 281: Autonomous Bekenstein-Hawking Holographic Thermodynamics Engine.
    Computes Schwarzschild & Kerr horizons, entropy, Hawking evaporation, and Page curve.
    """

    def __init__(self, sovereign_operator: str = SOVEREIGN_OPERATOR) -> None:
        self.sovereign_operator: str = sovereign_operator
        self._lock: threading.RLock = threading.RLock()
        self._evaluations_count: int = 0
        self._history: List[BlackHoleMetrics] = []
        self._last_metrics: Optional[BlackHoleMetrics] = None

    def _resolve_mass(self, mass_kg: Optional[float] = None, mass_solar: Optional[float] = None) -> float:
        """Resolves mass in kg from either kg or solar mass input."""
        if mass_kg is not None and mass_kg > 0:
            return float(mass_kg)
        if mass_solar is not None and mass_solar > 0:
            return float(mass_solar) * SOLAR_MASS_KG
        # Default to 1 solar mass
        return SOLAR_MASS_KG

    def calculate_schwarzschild(
        self,
        mass_kg: Optional[float] = None,
        mass_solar: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Computes static spherically-symmetric Schwarzschild black hole thermodynamics.
        """
        with self._lock:
            m = self._resolve_mass(mass_kg, mass_solar)
            c = C_SPEED_OF_LIGHT
            g = G_GRAVITATIONAL_CONST
            hbar = HBAR_PLANCK_REDUCED
            kb = KB_BOLTZMANN
            lp2 = PLANCK_LENGTH**2

            # Schwarzschild radius r_s = 2GM / c^2
            r_s = (2.0 * g * m) / (c**2)

            # Horizon area A_H = 4 * pi * r_s^2
            area = 4.0 * math.pi * (r_s**2)

            # Bekenstein-Hawking Entropy S_BH = k_B * c^3 * A / (4 * G * hbar)
            # Dimensionless entropy S / k_B = A / (4 * lp^2)
            s_dim = area / (4.0 * lp2)
            s_bh_jk = s_dim * kb

            # Hawking Temperature T_H = hbar * c^3 / (8 * pi * G * M * k_B)
            t_h = (hbar * (c**3)) / (8.0 * math.pi * g * m * kb)

            # Surface gravity kappa = c^4 / (4 * G * M)
            kappa = (c**4) / (4.0 * g * m)

            # Hawking Radiation Luminosity P = hbar * c^6 / (15360 * pi * G^2 * M^2)
            lum = (hbar * (c**6)) / (15360.0 * math.pi * (g**2) * (m**2))

            # Evaporation lifetime t_evap = 5120 * pi * G^2 * M^3 / (hbar * c^4)
            t_evap = (5120.0 * math.pi * (g**2) * (m**3)) / (hbar * (c**4))

            # Page time t_Page ~ 0.5 * t_evap
            t_page = 0.5 * t_evap

            metrics = BlackHoleMetrics(
                mass_kg=m,
                mass_solar=m / SOLAR_MASS_KG,
                spin_parameter=0.0,
                schwarzschild_radius_m=r_s,
                horizon_radius_m=r_s,
                horizon_area_m2=area,
                planck_area_units=s_dim,
                bekenstein_hawking_entropy_jk=s_bh_jk,
                dimensionless_entropy=s_dim,
                hawking_temperature_k=t_h,
                surface_gravity_ms2=kappa,
                hawking_luminosity_w=lum,
                evaporation_lifetime_s=t_evap,
                page_time_s=t_page,
            )

            self._evaluations_count += 1
            self._last_metrics = metrics
            self._history.append(metrics)
            if len(self._history) > 100:
                self._history.pop(0)

            return metrics.to_dict()

    def calculate_kerr(
        self,
        mass_kg: Optional[float] = None,
        mass_solar: Optional[float] = None,
        spin_param: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Computes rotating Kerr black hole thermodynamics with dimensionless spin a* in [0, 1).
        """
        with self._lock:
            m = self._resolve_mass(mass_kg, mass_solar)
            c = C_SPEED_OF_LIGHT
            g = G_GRAVITATIONAL_CONST
            hbar = HBAR_PLANCK_REDUCED
            kb = KB_BOLTZMANN
            lp2 = PLANCK_LENGTH**2

            # Clamp spin parameter to valid sub-extremal range [0.0, 0.999999]
            a_star = max(0.0, min(float(spin_param), 0.999999))
            gm_c2 = (g * m) / (c**2)
            r_s = 2.0 * gm_c2

            # Outer event horizon radius r_+ = GM/c^2 * (1 + sqrt(1 - a*^2))
            disc = math.sqrt(1.0 - a_star**2)
            r_plus = gm_c2 * (1.0 + disc)

            # Ring singularity radius a = a* * GM/c^2
            a_geom = a_star * gm_c2

            # Kerr Event Horizon Area A = 4 * pi * (r_+^2 + a^2)
            area_kerr = 4.0 * math.pi * (r_plus**2 + a_geom**2)

            s_dim = area_kerr / (4.0 * lp2)
            s_bh_jk = s_dim * kb

            # Kerr Surface Gravity kappa = c^2 * sqrt(1 - a*^2) / (2 * (r_+^2 + a^2) / r_plus)
            # or equivalently: kappa = c^4 * (r_+ - GM/c^2) / (r_+^2 + a^2)
            kappa_kerr = (c**4) * (r_plus - gm_c2) / ((r_plus**2 + a_geom**2) * (c**2 / (g * m))) if m > 0 else 0.0
            # Standard Kerr Hawking temperature: T_H = (hbar * c) / (4 * pi * k_B) * (r_+ - GM/c^2) / (r_+^2 + a^2)
            t_h_kerr = (hbar * c * (r_plus - gm_c2)) / (4.0 * math.pi * kb * (r_plus**2 + a_geom**2))
            t_h_kerr = max(0.0, t_h_kerr)

            # Evaporation timescale approximation (scaled by Kerr horizon area reduction)
            t_evap_base = (5120.0 * math.pi * (g**2) * (m**3)) / (hbar * (c**4))
            area_ratio = area_kerr / (16.0 * math.pi * (gm_c2**2)) if gm_c2 > 0 else 1.0
            t_evap_kerr = t_evap_base * max(0.1, area_ratio)
            t_page = 0.5 * t_evap_kerr

            metrics = BlackHoleMetrics(
                mass_kg=m,
                mass_solar=m / SOLAR_MASS_KG,
                spin_parameter=a_star,
                schwarzschild_radius_m=r_s,
                horizon_radius_m=r_plus,
                horizon_area_m2=area_kerr,
                planck_area_units=s_dim,
                bekenstein_hawking_entropy_jk=s_bh_jk,
                dimensionless_entropy=s_dim,
                hawking_temperature_k=t_h_kerr,
                surface_gravity_ms2=kappa_kerr,
                hawking_luminosity_w=(hbar * (c**6)) / (15360.0 * math.pi * (g**2) * (m**2)),
                evaporation_lifetime_s=t_evap_kerr,
                page_time_s=t_page,
            )

            self._evaluations_count += 1
            self._last_metrics = metrics
            self._history.append(metrics)
            if len(self._history) > 100:
                self._history.pop(0)

            return metrics.to_dict()

    def simulate_page_curve(
        self,
        mass_kg: Optional[float] = None,
        mass_solar: Optional[float] = None,
        steps: int = 50,
    ) -> Dict[str, Any]:
        """
        Simulates the unitary Page curve for black hole evaporation:
        Calculates thermal Hawking radiation entropy vs remaining Bekenstein-Hawking entropy.
        Information returns after Page time t_Page.
        """
        with self._lock:
            base = self.calculate_schwarzschild(mass_kg=mass_kg, mass_solar=mass_solar)
            m0 = base["mass_kg"]
            s0 = base["dimensionless_entropy"]
            t_evap = base["evaporation_lifetime_s"]
            t_page = base["page_time_s"]

            curve_points: List[Dict[str, float]] = []
            steps = max(10, min(steps, 200))

            for i in range(steps + 1):
                tau = float(i) / float(steps) # tau in [0.0, 1.0] of evaporation lifetime
                t_sec = tau * t_evap

                # Mass evolution under standard cubic Hawking evaporation M(t) = M_0 * (1 - t / t_evap)^(1/3)
                rem_factor = max(0.0, 1.0 - tau)
                m_t = m0 * (rem_factor**(1.0 / 3.0)) if rem_factor > 0.0 else 0.0
                
                # Remaining Black Hole Entropy S_BH(t) = S_0 * (M(t)/M0)^2 = S_0 * (1 - tau)^(2/3)
                s_bh_t = s0 * (rem_factor**(2.0 / 3.0)) if rem_factor > 0.0 else 0.0

                # Cumulative coarse-grained Hawking thermal entropy S_thermal(t) ~ S_0 * (4/3) * (1 - (1-tau)^(3/3)...)
                # Monotonically increasing thermal entropy of emitted radiation:
                s_thermal_t = s0 * (1.0 - rem_factor**(2.0 / 3.0))

                # Unitary Page curve S_radiation(t) = min(S_thermal(t), S_BH(t))
                s_rad_unitary = min(s_thermal_t, s_bh_t)

                curve_points.append({
                    "tau_normalized": round(tau, 4),
                    "time_seconds": t_sec,
                    "mass_remaining_kg": m_t,
                    "entropy_bh": s_bh_t,
                    "entropy_thermal": s_thermal_t,
                    "entropy_radiation_page": s_rad_unitary,
                    "is_past_page_time": bool(t_sec >= t_page),
                })

            return {
                "initial_mass_kg": m0,
                "initial_dimensionless_entropy": s0,
                "evaporation_lifetime_s": t_evap,
                "page_time_s": t_page,
                "total_points": len(curve_points),
                "curve": curve_points,
                "unitary_preserved": True,
            }

    def format_ascii_status(self) -> str:
        """CP1252-safe ASCII table representation of current thermodynamics metrics."""
        with self._lock:
            last = self._last_metrics
            mass_solar = last.mass_solar if last else 1.0
            r_s = last.schwarzschild_radius_m if last else 2953.25
            s_dim = last.dimensionless_entropy if last else 1.0e77
            t_h = last.hawking_temperature_k if last else 6.17e-8
            t_evap = last.evaporation_lifetime_s if last else 6.6e74
            spin = last.spin_parameter if last else 0.0

            lines = [
                "+====================================================================+",
                "|       STAGE 281: BLACK HOLE HOLOGRAPHIC THERMODYNAMICS FABRIC       |",
                "+====================================================================+",
                f"| Sovereign Operator  : {self.sovereign_operator:<44} |",
                f"| Evaluations Count   : {self._evaluations_count:<44} |",
                f"| Kerr Spin (a*)      : {spin:<44.4f} |",
                f"| Mass (Solar M_sun)  : {mass_solar:<44.4e} |",
                f"| Horizon Radius (m)  : {r_s:<44.4e} |",
                f"| S_BH / k_B (Planck) : {s_dim:<44.4e} |",
                f"| Hawking Temp T_H (K): {t_h:<44.4e} |",
                f"| Evap Lifetime (s)   : {t_evap:<44.4e} |",
                f"| Page Curve Status   : {'UNITARY_PRESERVED':<44} |",
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
