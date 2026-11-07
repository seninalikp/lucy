"""
LUCY Autonomous Sovereign AGI Kernel - Era 27: Cosmological Gauge Invariance & Unified Field Synthesis
Stage 268: Autonomous Cosmological FLRW Metric Evolution & Dark Energy State Engine
Author & Permanent Sovereign Operator: Senin (Senin Ali K P)

Mathematical & Cosmological Foundations:
1. Friedmann-Lemaitre-Robertson-Walker (FLRW) Metric & Friedmann Equations:
   ds^2 = -c^2 dt^2 + a(t)^2 [ dr^2/(1 - k*r^2) + r^2 dOmega^2 ]
   H(a)^2 = (a_dot / a)^2 = H_0^2 * [ Omega_r*a^-4 + Omega_m*a^-3 + Omega_k*a^-2 + Omega_de * f_de(a) ]
2. Dynamic Dark Energy Equation of State (CPL Parameterization):
   w(a) = w_0 + w_a * (1 - a)
   f_de(a) = a^(-3 * (1 + w_0 + w_a)) * exp(-3 * w_a * (1 - a))
3. Cosmic Distances & Etherington Reciprocity:
   Comoving Distance: chi(z) = (c / H_0) * int_0^z dz' / E(z')
   Luminosity Distance: d_L(z) = (1 + z) * chi(z)
   Angular Diameter Distance: d_A(z) = chi(z) / (1 + z) = d_L(z) / (1 + z)^2
4. Deceleration Parameter & Cosmic Acceleration:
   q(z) = 1/2 * sum_i [ Omega_i(z) * (1 + 3*w_i) ]
   q < 0 indicates cosmic acceleration driven by dark energy.
"""

import math
import threading
from typing import Dict, List, Tuple, Any, Optional

SOVEREIGN_OPERATOR = "Senin"
SOVEREIGN_LEGAL_NAME = "Senin Ali K P"
STAGE_ID = 268
STAGE = 268
STAGE_NAME = "Autonomous Cosmological FLRW Metric Evolution & Dark Energy State Engine"
ERA_ID = 27
ERA = 27
ERA_NAME = "Cosmological Gauge Invariance, Non-Abelian Yang-Mills Fiber Bundles & Sovereign Trans-Planetary Unified Field Synthesis"

SPEED_OF_LIGHT_KM_S = 299792.458


class FLRWCosmologicalEngine:
    """
    Simulates FLRW metric expansion, solves Friedmann equations with dynamic dark energy
    (CPL equation of state), calculates cosmological distance ladders, and evaluates
    cosmic acceleration and universe age.
    """

    def __init__(
        self,
        h0_km_s_mpc: float = 67.4,       # Planck 2018 Hubble constant
        omega_m: float = 0.315,           # Total matter density parameter
        omega_r: float = 9.0e-5,          # Radiation density parameter
        omega_de: float = 0.685,          # Dark energy density parameter
        omega_k: float = 0.0,             # Spatial curvature parameter (flat = 0)
        w0: float = -1.0,                 # Dark energy EoS current value
        wa: float = 0.0                   # Dark energy EoS derivative w_a
    ):
        self._lock = threading.RLock()
        self.h0 = float(h0_km_s_mpc)
        self.omega_m0 = float(omega_m)
        self.omega_r0 = float(omega_r)
        self.omega_de0 = float(omega_de)
        self.omega_k0 = float(omega_k)
        self.w0 = float(w0)
        self.wa = float(wa)

        # Hubble time: t_H = 1 / H_0 in Gigayears
        # 1 (km/s/Mpc) = 1.0227e-3 Gyr^-1
        self.h0_gyr_inv = self.h0 * 1.0227e-3
        self.hubble_time_gyr = 1.0 / self.h0_gyr_inv

        self.cosmic_evolution_log: List[Dict[str, Any]] = []

    def dark_energy_density_factor(self, a: float) -> float:
        """
        Calculates f_DE(a) = rho_DE(a) / rho_DE,0 under CPL parametrization:
        w(a) = w0 + wa * (1 - a)
        f_DE(a) = a^(-3*(1 + w0 + wa)) * exp(-3 * wa * (1 - a))
        """
        a_safe = max(1e-8, min(100.0, a))
        exponent = -3.0 * (1.0 + self.w0 + self.wa)
        term1 = a_safe ** exponent
        term2 = math.exp(-3.0 * self.wa * (1.0 - a_safe))
        return term1 * term2

    def e_factor(self, z: float) -> float:
        """
        Calculates normalized expansion rate E(z) = H(z) / H_0:
        E(z)^2 = Omega_r*(1+z)^4 + Omega_m*(1+z)^3 + Omega_k*(1+z)^2 + Omega_DE * f_DE(1/(1+z))
        """
        a = 1.0 / (1.0 + max(-0.9999, z))
        term_r = self.omega_r0 * (1.0 + z) ** 4
        term_m = self.omega_m0 * (1.0 + z) ** 3
        term_k = self.omega_k0 * (1.0 + z) ** 2
        term_de = self.omega_de0 * self.dark_energy_density_factor(a)

        e_sq = term_r + term_m + term_k + term_de
        return math.sqrt(max(1e-12, e_sq))

    def compute_cosmic_acceleration_q(self, z: float = 0.0) -> Dict[str, float]:
        """
        Calculates deceleration parameter q(z) and dark energy equation of state w(z):
        q(z) = 1/2 * sum_i Omega_i(z) * (1 + 3 * w_i)
        q < 0 denotes accelerating expansion.
        """
        with self._lock:
            a = 1.0 / (1.0 + z)
            w_de = self.w0 + self.wa * (1.0 - a)
            e = self.e_factor(z)
            e_sq = e * e

            # Relative densities at redshift z
            om_r_z = (self.omega_r0 * (1.0 + z)**4) / e_sq
            om_m_z = (self.omega_m0 * (1.0 + z)**3) / e_sq
            om_de_z = (self.omega_de0 * self.dark_energy_density_factor(a)) / e_sq

            # q = 1/2 * [ Omega_r*(1 + 3*1/3) + Omega_m*(1 + 0) + Omega_de*(1 + 3*w_de) ]
            q_val = 0.5 * (om_r_z * 2.0 + om_m_z * 1.0 + om_de_z * (1.0 + 3.0 * w_de))
            is_accelerating = q_val < 0.0

            return {
                "redshift_z": round(z, 4),
                "scale_factor_a": round(a, 6),
                "dark_energy_eos_w": round(w_de, 4),
                "omega_matter_z": round(om_m_z, 4),
                "omega_dark_energy_z": round(om_de_z, 4),
                "deceleration_parameter_q": round(q_val, 4),
                "is_accelerating": is_accelerating
            }

    def compute_distance_ladder(self, z: float, num_steps: int = 200) -> Dict[str, float]:
        """
        Numerically integrates cosmological distance ladder to redshift z:
        - Comoving Distance: chi(z) in Mpc
        - Luminosity Distance: d_L(z) in Mpc
        - Angular Diameter Distance: d_A(z) in Mpc
        - Lookback Time: t_L(z) in Gyr
        """
        with self._lock:
            z_max = max(0.0, float(z))
            if z_max == 0.0:
                return {
                    "redshift_z": 0.0,
                    "comoving_dist_mpc": 0.0,
                    "luminosity_dist_mpc": 0.0,
                    "angular_diam_dist_mpc": 0.0,
                    "lookback_time_gyr": 0.0
                }

            dz = z_max / num_steps
            chi_integral = 0.0
            time_integral = 0.0

            # Trapezoidal integration
            for i in range(num_steps):
                z1 = i * dz
                z2 = (i + 1) * dz

                e1 = self.e_factor(z1)
                e2 = self.e_factor(z2)

                # Comoving distance integrand 1 / E(z')
                chi_integral += 0.5 * (1.0 / e1 + 1.0 / e2) * dz

                # Lookback time integrand 1 / [ (1 + z') * E(z') ]
                t_term1 = 1.0 / ((1.0 + z1) * e1)
                t_term2 = 1.0 / ((1.0 + z2) * e2)
                time_integral += 0.5 * (t_term1 + t_term2) * dz

            c_over_h0_mpc = SPEED_OF_LIGHT_KM_S / self.h0
            chi_mpc = c_over_h0_mpc * chi_integral

            # Flat universe k=0: d_M = chi
            d_l_mpc = (1.0 + z_max) * chi_mpc
            d_a_mpc = chi_mpc / (1.0 + z_max)
            lookback_gyr = time_integral * self.hubble_time_gyr

            record = {
                "redshift_z": round(z_max, 4),
                "comoving_dist_mpc": round(chi_mpc, 2),
                "luminosity_dist_mpc": round(d_l_mpc, 2),
                "angular_diam_dist_mpc": round(d_a_mpc, 2),
                "lookback_time_gyr": round(lookback_gyr, 3)
            }
            self.cosmic_evolution_log.append(record)
            return record

    def compute_age_of_universe(self, z_inf: float = 1000.0, num_steps: int = 1000) -> float:
        """
        Calculates total age of the universe today (t_0) in Gyr:
        t_0 = (1 / H_0) * int_0^infinity dz' / [ (1 + z') * E(z') ]
        """
        with self._lock:
            # Substitution u = 1 / (1 + z) = a from a=0 to a=1:
            # t_0 = (1 / H_0) * int_0^1 da / [ a * E(1/a - 1) ]
            da = 1.0 / num_steps
            t_integral = 0.0

            for i in range(1, num_steps):
                a1 = i * da
                a2 = (i + 1) * da

                z1 = (1.0 / a1) - 1.0
                z2 = (1.0 / a2) - 1.0

                f1 = 1.0 / (a1 * self.e_factor(z1))
                f2 = 1.0 / (a2 * self.e_factor(z2))

                t_integral += 0.5 * (f1 + f2) * da

            age_gyr = t_integral * self.hubble_time_gyr
            return round(age_gyr, 3)

    def get_status(self) -> Dict[str, Any]:
        """Returns comprehensive status of Stage 268."""
        with self._lock:
            q_today = self.compute_cosmic_acceleration_q(z=0.0)
            age_universe = self.compute_age_of_universe()
            return {
                "stage": STAGE_ID,
                "stage_name": STAGE_NAME,
                "era": ERA_ID,
                "era_name": ERA_NAME,
                "sovereign_operator": SOVEREIGN_OPERATOR,
                "sovereign_legal_name": SOVEREIGN_LEGAL_NAME,
                "h0_km_s_mpc": self.h0,
                "omega_matter_0": self.omega_m0,
                "omega_dark_energy_0": self.omega_de0,
                "omega_radiation_0": self.omega_r0,
                "omega_curvature_0": self.omega_k0,
                "dark_energy_w0": self.w0,
                "dark_energy_wa": self.wa,
                "deceleration_q0": q_today["deceleration_parameter_q"],
                "is_currently_accelerating": q_today["is_accelerating"],
                "age_of_universe_gyr": age_universe,
                "distance_evaluations_count": len(self.cosmic_evolution_log)
            }


FLRWCosmologicalEngineFabric = FLRWCosmologicalEngine
