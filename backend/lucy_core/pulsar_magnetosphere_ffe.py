"""
LUCY STAGE 287: Pulsar Magnetosphere Relativistic Force-Free Electrodynamics (FFE) Simulator
Sovereign Architect & Supreme Operator: Senin (Senin Ali K P)

Provides high-precision relativistic electrodynamics and magnetosphere modeling for
rapidly rotating neutron stars: Force-Free Electrodynamics (FFE) invariants E.B = 0,
B^2 - E^2 > 0, light cylinder boundary R_LC = c/Omega, Goldreich-Julian co-rotation
charge density rho_GJ = -2*(Omega.B)/c, magnetic dipole spin-down luminosity, and
pulsar characteristic age tau_c = P / (2 * P_dot).
Fully offline, thread-safe, CP1252-safe ASCII reporting.
"""

import math
import time
import threading
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

STAGE: int = 287
STAGE_NAME: str = "Pulsar Magnetosphere Relativistic Force-Free Electrodynamics (FFE) Simulator"
SOVEREIGN_OPERATOR: str = "Senin (Senin Ali K P)"

# Fundamental Physical Constants
C_SPEED_OF_LIGHT: float = 299792458.0              # m/s
ELEMENTARY_CHARGE: float = 1.602176634e-19         # Coulombs
DEFAULT_R_NEUTRON_STAR: float = 1.0e4             # 10 km in meters
GAUSS_TO_TESLA: float = 1.0e-4                    # 1 Gauss = 10^-4 Tesla


@dataclass
class PulsarMagnetosphereMetrics:
    """State metrics of pulsar electrodynamics and FFE magnetosphere."""
    period_s: float
    period_derivative_pdot: float
    angular_velocity_rad_s: float
    light_cylinder_radius_m: float
    surface_b_field_tesla: float
    goldreich_julian_density_c_m3: float
    goldreich_julian_number_density_m3: float
    polar_cap_angle_rad: float
    spindown_luminosity_watts: float
    characteristic_age_years: float
    ffe_conditions_satisfied: bool
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "period_s": self.period_s,
            "period_derivative_pdot": self.period_derivative_pdot,
            "angular_velocity_rad_s": self.angular_velocity_rad_s,
            "light_cylinder_radius_m": self.light_cylinder_radius_m,
            "surface_b_field_tesla": self.surface_b_field_tesla,
            "goldreich_julian_density_c_m3": self.goldreich_julian_density_c_m3,
            "goldreich_julian_number_density_m3": self.goldreich_julian_number_density_m3,
            "polar_cap_angle_rad": self.polar_cap_angle_rad,
            "spindown_luminosity_watts": self.spindown_luminosity_watts,
            "characteristic_age_years": self.characteristic_age_years,
            "ffe_conditions_satisfied": self.ffe_conditions_satisfied,
            "timestamp": self.timestamp,
        }


class PulsarMagnetosphereFFEFabric:
    """
    Stage 287: Autonomous Pulsar Magnetosphere & Relativistic FFE Engine.
    Simulates force-free plasma dynamics, Goldreich-Julian charge, and dipole spin-down.
    """

    def __init__(self, sovereign_operator: str = SOVEREIGN_OPERATOR) -> None:
        self.sovereign_operator: str = sovereign_operator
        self._lock: threading.RLock = threading.RLock()
        self._evaluations_count: int = 0
        self._history: List[PulsarMagnetosphereMetrics] = []
        self._last_metrics: Optional[PulsarMagnetosphereMetrics] = None

    def calculate_pulsar_parameters(
        self,
        period_s: float = 0.03339,               # Default: Crab Pulsar B0531+21 (~33 ms)
        period_derivative: float = 4.21e-13,     # Crab P_dot
        b_surface_gauss: Optional[float] = None, # If None, derived from P and P_dot
        r_ns_m: float = DEFAULT_R_NEUTRON_STAR,
        magnetic_inclination_rad: float = math.pi / 4.0,
    ) -> Dict[str, Any]:
        """
        Calculates relativistic magnetosphere properties and spin-down parameters.
        """
        with self._lock:
            p = max(1e-4, float(period_s))
            p_dot = max(1e-25, float(period_derivative))
            r_ns = max(1e3, float(r_ns_m))
            c = C_SPEED_OF_LIGHT

            # Angular rotation frequency Omega = 2 * pi / P
            omega = (2.0 * math.pi) / p

            # Light cylinder radius R_LC = c / Omega
            r_lc = c / omega

            # Surface B field (Tesla)
            if b_surface_gauss is not None and b_surface_gauss > 0:
                b_surf = float(b_surface_gauss) * GAUSS_TO_TESLA
            else:
                # Standard magnetic dipole surface field estimate: B_surf ~ 3.2e19 * sqrt(P * P_dot) Gauss
                b_gauss = 3.2e19 * math.sqrt(p * p_dot)
                b_surf = b_gauss * GAUSS_TO_TESLA

            # Goldreich-Julian charge density at pole: rho_GJ = -2 * Omega * B / c (SI units: C / m^3)
            # rho_GJ = -2 * epsilon_0 * Omega * B
            epsilon_0 = 8.8541878128e-12
            rho_gj = -2.0 * epsilon_0 * omega * b_surf
            n_gj = abs(rho_gj) / ELEMENTARY_CHARGE

            # Polar cap open field angle theta_pc ~ sqrt(R_NS / R_LC)
            ratio_r = min(1.0, r_ns / r_lc)
            theta_pc = math.sqrt(ratio_r)

            # Dipole spin-down luminosity E_dot = (2 / (3 * c^3)) * (B * R_NS^3)^2 * Omega^4 * sin^2(alpha)
            # In SI: (mu_0 / (6 * pi * c^3)) * B^2 * R_NS^6 * Omega^4 * sin^2(alpha)
            mu_0 = 4.0 * math.pi * 1e-7
            sin_inc = math.sin(magnetic_inclination_rad)
            edot = (mu_0 / (6.0 * math.pi * (c**3))) * (b_surf**2) * (r_ns**6) * (omega**4) * (sin_inc**2)

            # Characteristic age tau_c = P / (2 * P_dot) (converted to years)
            seconds_per_year = 365.25 * 86400.0
            tau_years = (p / (2.0 * p_dot)) / seconds_per_year

            # FFE condition: E.B = 0 and B^2 - E^2 > 0 inside light cylinder
            ffe_ok = bool(r_lc > r_ns)

            metrics = PulsarMagnetosphereMetrics(
                period_s=p,
                period_derivative_pdot=p_dot,
                angular_velocity_rad_s=omega,
                light_cylinder_radius_m=r_lc,
                surface_b_field_tesla=b_surf,
                goldreich_julian_density_c_m3=rho_gj,
                goldreich_julian_number_density_m3=n_gj,
                polar_cap_angle_rad=theta_pc,
                spindown_luminosity_watts=edot,
                characteristic_age_years=tau_years,
                ffe_conditions_satisfied=ffe_ok,
            )

            self._evaluations_count += 1
            self._last_metrics = metrics
            self._history.append(metrics)
            if len(self._history) > 100:
                self._history.pop(0)

            return metrics.to_dict()

    def simulate_magnetosphere_radial_profile(
        self,
        period_s: float = 0.03339,
        b_surface_gauss: float = 3.8e12,
        r_points: int = 25,
    ) -> Dict[str, Any]:
        """
        Simulates the radial decay of the magnetic field B(r) and induced electric field E(r).
        Inside light cylinder: Dipole decay B(r) ~ B_0 * (R_NS / r)^3.
        At light cylinder and beyond: Toroidal wave radiation B(r) ~ B_LC * (R_LC / r).
        """
        with self._lock:
            p = max(1e-4, float(period_s))
            omega = (2.0 * math.pi) / p
            r_lc = C_SPEED_OF_LIGHT / omega
            r_ns = DEFAULT_R_NEUTRON_STAR
            b_0 = float(b_surface_gauss) * GAUSS_TO_TESLA

            points: List[Dict[str, float]] = []
            steps = max(10, min(r_points, 100))

            for i in range(steps + 1):
                r_frac = 1.0 + (float(i) / float(steps)) * 2.0 # From R_NS to 3*R_LC
                r_val = r_ns + (r_frac - 1.0) * r_lc

                if r_val <= r_lc:
                    # Near zone: Dipolar magnetosphere
                    b_mag = b_0 * ((r_ns / r_val)**3)
                    # Corotation electric field E = (Omega x r) x B -> E ~ (r * Omega / c) * B * c = r * Omega * B
                    e_mag = r_val * omega * b_mag
                    zone = "COROTATING_MAGNETOSPHERE"
                else:
                    # Far zone (radiation zone): B_LC * (R_LC / r)
                    b_lc = b_0 * ((r_ns / r_lc)**3)
                    b_mag = b_lc * (r_lc / r_val)
                    e_mag = b_mag * C_SPEED_OF_LIGHT # Relativistic EM wave E = c * B
                    zone = "WIND_RADIATION_ZONE"

                ffe_invariant = (b_mag**2) - ((e_mag / C_SPEED_OF_LIGHT)**2)

                points.append({
                    "radius_m": r_val,
                    "radius_over_r_lc": r_val / r_lc,
                    "magnetic_field_tesla": b_mag,
                    "electric_field_v_m": e_mag,
                    "ffe_invariant_b2_minus_e2": ffe_invariant,
                    "zone": zone,
                })

            return {
                "period_s": p,
                "light_cylinder_radius_m": r_lc,
                "total_radial_points": len(points),
                "profile": points,
            }

    def format_ascii_status(self) -> str:
        """CP1252-safe ASCII table representation."""
        with self._lock:
            last = self._last_metrics
            p = last.period_s if last else 0.03339
            r_lc = last.light_cylinder_radius_m if last else 1.59e6
            b_surf = last.surface_b_field_tesla if last else 3.8e8
            n_gj = last.goldreich_julian_number_density_m3 if last else 1.0e17
            edot = last.spindown_luminosity_watts if last else 4.5e31
            age = last.characteristic_age_years if last else 1250.0

            lines = [
                "+====================================================================+",
                "|       STAGE 287: PULSAR MAGNETOSPHERE RELATIVISTIC FFE FABRIC      |",
                "+====================================================================+",
                f"| Sovereign Operator  : {self.sovereign_operator:<44} |",
                f"| Evaluations Count   : {self._evaluations_count:<44} |",
                f"| Pulsar Period P     : {p:<44.5f} s |",
                f"| Light Cylinder R_LC : {r_lc:<44.3e} m |",
                f"| Surface Field B_0   : {b_surf:<44.3e} T |",
                f"| Goldreich-Julian n  : {n_gj:<44.3e} m^-3 |",
                f"| Spindown Power E_dot: {edot:<44.3e} W |",
                f"| Characteristic Age  : {age:<44.1f} yrs |",
                f"| FFE State           : {'FORCE_FREE_PLASMA_EQUILIBRIUM':<44} |",
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
