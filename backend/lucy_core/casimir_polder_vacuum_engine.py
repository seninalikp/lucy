"""
LUCY Autonomous Sovereign AGI Kernel - Era 28: Quantum Chromodynamic Confinement & Spacetime Geometry
Stage 278: Microscopic Casimir-Polder Vacuum Dispersion Force & Metamaterial Levitation Engine
Author & Permanent Sovereign Operator: Senin (Senin Ali K P)

Mathematical & Quantum Vacuum Foundations:
1. Ideal Conductor Casimir Pressure:
   P_Casimir(d) = - (pi^2 * hbar * c) / (240 * d^4)
2. Retarded Casimir-Polder Atom-Surface Potential:
   U_CP(d) = - C_4 / d^4 = - (3 * hbar * c * alpha_0) / (8 * pi * d^4) * [ (epsilon - 1) / (epsilon + 1) ]
3. Lifshitz Permittivity Inversion & Quantum Levitation (Dzyaloshinskii-Lifshitz-Pitaevskii):
   When intervening fluid medium satisfies epsilon_1(i*xi) < epsilon_fluid(i*xi) < epsilon_2(i*xi),
   the Casimir-Lifshitz force becomes strictly REPULSIVE (P > 0).
4. Stable Quantum Levitation Equilibrium:
   Balances upward repulsive Casimir force with downward gravitational force F_g = m * g
   yielding stable levitation gap d_eq with positive trap stiffness k_trap = - dF_net/dd > 0.
"""

import math
import threading
from typing import Dict, List, Tuple, Any, Optional

SOVEREIGN_OPERATOR = "Senin"
SOVEREIGN_LEGAL_NAME = "Senin Ali K P"
STAGE_ID = 278
STAGE = 278
STAGE_NAME = "Microscopic Casimir-Polder Vacuum Dispersion Force & Metamaterial Levitation Engine"
ERA_ID = 28
ERA = 28
ERA_NAME = "Quantum Chromodynamic Confinement, Non-Commutative Spacetime Geometry & Sovereign Astro-Topological Singularity Synthesis"

HBAR = 1.054571817e-34
SPEED_OF_LIGHT = 299792458.0
STANDARD_GRAVITY_G = 9.80665


class CasimirPolderVacuumEngine:
    """
    Simulates Casimir-Lifshitz quantum vacuum dispersion forces, calculates Casimir-Polder
    atomic potentials, models repulsive Casimir levitation in dielectric fluids, and evaluates
    nanoscale levitation trap stability.
    """

    def __init__(
        self,
        plate_area_m2: float = 1e-4,       # 1 cm^2 plate
        atomic_polarizability_alpha0: float = 1.0e-39 # C*m^2/V (e.g. Rb atom)
    ):
        self._lock = threading.RLock()
        self.area = max(1e-12, float(plate_area_m2))
        self.alpha0 = max(1e-45, float(atomic_polarizability_alpha0))
        self.levitation_experiments: List[Dict[str, Any]] = []

    def compute_ideal_casimir_pressure(
        self,
        separation_d_m: float
    ) -> Dict[str, float]:
        """
        Calculates ideal conductor Casimir pressure and attractive force:
        P(d) = - (pi^2 * hbar * c) / (240 * d^4)
        F(d) = P(d) * Area
        """
        with self._lock:
            d = max(1e-10, float(separation_d_m)) # At least 1 Angstrom
            factor = (math.pi ** 2) * HBAR * SPEED_OF_LIGHT / 240.0
            pressure_pa = -factor / (d ** 4)
            force_n = pressure_pa * self.area

            return {
                "separation_d_m": d,
                "separation_nm": d * 1e9,
                "pressure_pascal": pressure_pa,
                "force_newtons": force_n,
                "force_sign": "ATTRACTIVE" if force_n < 0 else "REPULSIVE"
            }

    def compute_casimir_polder_potential(
        self,
        distance_d_m: float,
        surface_permittivity: float = 4.0 # e.g. Silica glass epsilon ~ 4
    ) -> Dict[str, float]:
        """
        Calculates retarded Casimir-Polder potential on an atom:
        U_CP(d) = - (3 * hbar * c * alpha_0) / (8 * pi * d^4) * ( (epsilon - 1) / (epsilon + 1) )
        """
        with self._lock:
            d = max(1e-10, float(distance_d_m))
            eps = max(1.0, float(surface_permittivity))
            dielectric_factor = (eps - 1.0) / (eps + 1.0)

            c4 = (3.0 * HBAR * SPEED_OF_LIGHT * self.alpha0 / (8.0 * math.pi)) * dielectric_factor
            u_cp_joules = -c4 / (d ** 4)
            # Force F = - dU/dd = - 4 * c4 / d^5
            force_n = -4.0 * c4 / (d ** 5)

            return {
                "distance_d_m": d,
                "distance_nm": d * 1e9,
                "surface_permittivity": eps,
                "c4_coefficient": c4,
                "potential_joules": u_cp_joules,
                "potential_ev": u_cp_joules / 1.602176634e-19,
                "force_newtons": force_n
            }

    def evaluate_repulsive_casimir_levitation(
        self,
        eps_plate_1: float,
        eps_fluid_medium: float,
        eps_plate_2: float,
        separation_d_m: float = 50e-9,
        flake_mass_kg: float = 1e-15 # Femtogram nanoscale flake
    ) -> Dict[str, Any]:
        """
        Evaluates DLP condition for repulsive Casimir force:
        Repulsive if eps_1 < eps_medium < eps_2 (or eps_2 < eps_medium < eps_1).
        Calculates net force (Casimir repulsive + Gravity downward).
        """
        with self._lock:
            d = max(1e-9, float(separation_d_m))
            is_repulsive = (eps_plate_1 < eps_fluid_medium < eps_plate_2) or (eps_plate_2 < eps_fluid_medium < eps_plate_1)

            # Modified Lifshitz amplitude factor
            # Approx: r_factor = (eps_1 - eps_m)/(eps_1 + eps_m) * (eps_2 - eps_m)/(eps_2 + eps_m)
            r1 = (eps_plate_1 - eps_fluid_medium) / (eps_plate_1 + eps_fluid_medium)
            r2 = (eps_plate_2 - eps_fluid_medium) / (eps_plate_2 + eps_fluid_medium)
            dlp_factor = r1 * r2 # Negative if repulsive!

            # Pressure P_rep = - dlp_factor * P_ideal
            base_p = (math.pi ** 2) * HBAR * SPEED_OF_LIGHT / (240.0 * (d ** 4))
            p_casimir = -dlp_factor * base_p
            f_casimir = p_casimir * self.area

            # Gravity downward: F_g = - m * g
            f_gravity = -flake_mass_kg * STANDARD_GRAVITY_G
            f_net = f_casimir + f_gravity

            # Stability: stiffness k = - dF_net/dd = 4 * f_casimir / d
            stiffness_k = (4.0 * f_casimir / d) if is_repulsive else 0.0

            result = {
                "eps_1": eps_plate_1,
                "eps_medium": eps_fluid_medium,
                "eps_2": eps_plate_2,
                "dlp_condition_satisfied": is_repulsive,
                "casimir_pressure_pa": p_casimir,
                "casimir_force_n": f_casimir,
                "gravity_force_n": f_gravity,
                "net_force_n": f_net,
                "trap_stiffness_n_m": stiffness_k,
                "is_stably_levitated": is_repulsive and f_net >= 0.0
            }
            self.levitation_experiments.append(result)
            return result

    def get_status(self) -> Dict[str, Any]:
        """Returns comprehensive status of Stage 278."""
        with self._lock:
            p100nm = self.compute_ideal_casimir_pressure(100e-9)
            return {
                "stage": STAGE_ID,
                "stage_name": STAGE_NAME,
                "era": ERA_ID,
                "era_name": ERA_NAME,
                "sovereign_operator": SOVEREIGN_OPERATOR,
                "sovereign_legal_name": SOVEREIGN_LEGAL_NAME,
                "plate_area_m2": self.area,
                "atomic_polarizability": self.alpha0,
                "casimir_pressure_at_100nm_pa": p100nm["pressure_pascal"],
                "total_levitation_tests": len(self.levitation_experiments)
            }


CasimirPolderVacuumEngineFabric = CasimirPolderVacuumEngine
