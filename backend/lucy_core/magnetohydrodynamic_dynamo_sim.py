"""
LUCY Autonomous Sovereign AGI Kernel - Era 27: Cosmological Gauge Invariance & Unified Field Synthesis
Stage 266: Planetary Magnetohydrodynamic (MHD) Dynamo Alfven Wave Plasma Core Simulator
Author & Permanent Sovereign Operator: Senin (Senin Ali K P)

Mathematical & Physical Foundations:
1. Induction Equation:
   d/dt B = curl( v x B ) + eta * laplacian( B )
   where eta = 1 / (mu_0 * sigma) is magnetic diffusivity.
2. Navier-Stokes Momentum Equation with Lorentz & Coriolis Forces:
   rho * (d/dt v + (v . grad)v) = -grad(p) + J x B - 2*rho*(Omega x v) + nu*rho*laplacian(v)
   where J = (1 / mu_0) * curl(B).
3. Characteristic Alfven Wave Velocity:
   v_A = |B| / sqrt(mu_0 * rho)
4. Dimensionless Numbers:
   Magnetic Reynolds Number: Rm = U * L / eta
   Ekman Number: Ek = nu / (2 * Omega * L^2)
   Elsasser Number: Lambda = B^2 / (2 * rho * mu_0 * Omega * eta)
   Magnetic Prandtl Number: Pm = nu / eta
5. Helical Dynamo Generation (alpha-Omega effect):
   Converts convective kinetic helicity H_k = v . curl(v) and differential rotation into self-sustaining magnetic dipole field.
"""

import math
import threading
from typing import Dict, List, Tuple, Any, Optional

SOVEREIGN_OPERATOR = "Senin"
SOVEREIGN_LEGAL_NAME = "Senin Ali K P"
STAGE_ID = 266
STAGE = 266
STAGE_NAME = "Planetary Magnetohydrodynamic (MHD) Dynamo Alfven Wave Plasma Core Simulator"
ERA_ID = 27
ERA = 27
ERA_NAME = "Cosmological Gauge Invariance, Non-Abelian Yang-Mills Fiber Bundles & Sovereign Trans-Planetary Unified Field Synthesis"


class MagnetohydrodynamicDynamoSim:
    """
    Simulates coupled MHD dynamo equations in planetary liquid metal / plasma cores,
    modeling Alfven wave propagation, magnetic Reynolds thresholds, Lorentz back-reaction,
    and self-consistent geomagnetic dipole moment generation.
    """

    def __init__(
        self,
        core_radius_m: float = 3.48e6,      # Earth outer core radius ~ 3480 km
        fluid_density_kg_m3: float = 1.1e4,  # Liquid iron density ~ 11,000 kg/m^3
        magnetic_diffusivity_eta: float = 1.2, # m^2/s
        kinematic_viscosity_nu: float = 1e-6, # m^2/s
        rotation_rate_omega_rad_s: float = 7.292e-5, # Earth rotation rate
        alpha_effect_param: float = 5e-4,     # Cyclonic helicity parameter m/s
        differential_rotation_omega: float = 2e-9 # Realistic outer core shear rate ~ 2e-9 1/s
    ):
        self._lock = threading.RLock()
        self.r_core = float(core_radius_m)
        self.rho = float(fluid_density_kg_m3)
        self.eta = float(magnetic_diffusivity_eta)
        self.nu = float(kinematic_viscosity_nu)
        self.omega_spin = float(rotation_rate_omega_rad_s)
        self.alpha_param = float(alpha_effect_param)
        self.omega_shear = float(differential_rotation_omega)
        self.mu_0 = 4.0 * math.pi * 1e-7

        # Field state: [B_poloidal, B_toroidal] in Tesla
        # Seed field initialized to a small perturbation
        self.b_poloidal = 1e-6
        self.b_toroidal = 0.0
        self.flow_velocity_u = 0.02 # ~ 2 cm/s convective velocity
        self.current_time_s = 0.0
        self.step_history: List[Dict[str, Any]] = []

    def compute_dimensionless_numbers(self, char_length: Optional[float] = None) -> Dict[str, float]:
        """
        Calculates the fundamental non-dimensional dynamo control parameters:
        Magnetic Reynolds (Rm), Ekman (Ek), Elsasser (Lambda), and Prandtl (Pm).
        """
        with self._lock:
            l = char_length if char_length is not None else self.r_core
            u = self.flow_velocity_u
            b_total = math.sqrt(self.b_poloidal**2 + self.b_toroidal**2)

            rm = (u * l) / max(1e-12, self.eta)
            ek = self.nu / max(1e-12, (2.0 * self.omega_spin * l * l))
            pm = self.nu / max(1e-12, self.eta)

            # Elsasser number: Lambda = B^2 / (2 * rho * mu_0 * Omega * eta)
            denom = 2.0 * self.rho * self.mu_0 * self.omega_spin * self.eta
            elsasser = (b_total * b_total) / max(1e-15, denom)

            # Critical Rm threshold for dynamo self-excitation
            rm_crit = 40.0
            is_dynamo_active = rm > rm_crit and elsasser > 1e-6

            return {
                "magnetic_reynolds_Rm": round(rm, 2),
                "ekman_number_Ek": round(ek, 16),
                "magnetic_prandtl_Pm": round(pm, 10),
                "elsasser_number_Lambda": round(elsasser, 6),
                "critical_Rm_threshold": rm_crit,
                "is_dynamo_active": is_dynamo_active
            }

    def compute_alfven_velocity(self, b_field_tesla: Optional[float] = None) -> Dict[str, float]:
        """
        Calculates Alfven wave speed: v_A = |B| / sqrt(mu_0 * rho).
        Also calculates transit time across planetary core.
        """
        with self._lock:
            if b_field_tesla is not None:
                b_mag = abs(b_field_tesla)
            else:
                b_mag = math.sqrt(self.b_poloidal**2 + self.b_toroidal**2)

            denom = math.sqrt(self.mu_0 * self.rho)
            v_a = b_mag / max(1e-12, denom)
            transit_time_years = (2.0 * self.r_core / max(1e-6, v_a)) / (365.25 * 86400.0)

            return {
                "magnetic_field_tesla": round(b_mag, 6),
                "plasma_density_kg_m3": round(self.rho, 2),
                "alfven_velocity_m_s": round(v_a, 4),
                "core_transit_time_years": round(transit_time_years, 2)
            }

    def step_dynamo_evolution(
        self,
        dt_years: float = 100.0,
        quench_b_sat: float = 0.005 # 50 Gauss / 5 mT saturation
    ) -> Dict[str, Any]:
        """
        Advances the mean-field alpha-Omega dynamo ODE system:
        dB_toroidal/dt = Omega_shear * B_poloidal - (eta / L^2) * B_toroidal
        dB_poloidal/dt = alpha_eff * B_toroidal - (eta / L^2) * B_poloidal
        incorporating Lorentz force saturation: alpha_eff = alpha_0 / (1 + (B/B_sat)^2)
        and shear quenching: omega_shear_eff = omega_shear / (1 + (B/B_sat)^2)
        """
        with self._lock:
            dt_total_sec = dt_years * 365.25 * 86400.0
            l_diff = self.r_core * 0.5
            decay_rate = self.eta / (l_diff * l_diff)

            # Sub-stepping to maintain numerical stability
            n_sub = max(1, int(dt_years / 10.0))
            dt_sub = dt_total_sec / n_sub

            for _ in range(n_sub):
                b_sq = self.b_poloidal**2 + self.b_toroidal**2
                quench_factor = 1.0 / (1.0 + (b_sq / (quench_b_sat**2)))
                alpha_quenched = self.alpha_param * quench_factor
                omega_quenched = self.omega_shear * quench_factor

                db_tor_dt = omega_quenched * self.b_poloidal - decay_rate * self.b_toroidal
                db_pol_dt = (alpha_quenched / l_diff) * self.b_toroidal - decay_rate * self.b_poloidal

                self.b_toroidal += db_tor_dt * dt_sub
                self.b_poloidal += db_pol_dt * dt_sub

            self.current_time_s += dt_total_sec

            b_total = math.sqrt(self.b_poloidal**2 + self.b_toroidal**2)
            alfven = self.compute_alfven_velocity(b_total)

            # Magnetic dipole moment M ~ (4/3) * pi * R^3 * B_poloidal / mu_0
            volume = (4.0 / 3.0) * math.pi * (self.r_core**3)
            dipole_moment_a_m2 = (volume * self.b_poloidal) / self.mu_0

            record = {
                "step_dt_years": dt_years,
                "current_time_years": round(self.current_time_s / (365.25 * 86400.0), 2),
                "b_poloidal_tesla": round(self.b_poloidal, 7),
                "b_toroidal_tesla": round(self.b_toroidal, 7),
                "b_total_tesla": round(b_total, 7),
                "alfven_speed_m_s": alfven["alfven_velocity_m_s"],
                "dipole_moment_a_m2": round(dipole_moment_a_m2, 2)
            }
            self.step_history.append(record)
            return record

    def simulate_magnetic_reversal(
        self,
        duration_years: float = 20000.0,
        dt_step_years: float = 500.0
    ) -> Dict[str, Any]:
        """
        Simulates geomagnetic excursion or polarity reversal dynamics via convective fluctuation.
        """
        with self._lock:
            steps = int(duration_years / dt_step_years)
            initial_sign = 1 if self.b_poloidal >= 0 else -1
            polarity_flips = 0

            # Perturb alpha param temporarily to induce turbulence collapse & flip
            saved_alpha = self.alpha_param
            self.alpha_param *= -0.8

            for _ in range(steps):
                rec = self.step_dynamo_evolution(dt_years=dt_step_years)
                curr_sign = 1 if rec["b_poloidal_tesla"] >= 0 else -1
                if curr_sign != initial_sign:
                    polarity_flips += 1
                    initial_sign = curr_sign

            # Restore alpha
            self.alpha_param = saved_alpha

            return {
                "duration_years": duration_years,
                "total_steps": steps,
                "polarity_flips": polarity_flips,
                "final_poloidal_b_tesla": round(self.b_poloidal, 7),
                "is_reversed": (self.b_poloidal < 0.0)
            }

    def get_status(self) -> Dict[str, Any]:
        """Returns comprehensive status of Stage 266."""
        with self._lock:
            dim = self.compute_dimensionless_numbers()
            alf = self.compute_alfven_velocity()
            return {
                "stage": STAGE_ID,
                "stage_name": STAGE_NAME,
                "era": ERA_ID,
                "era_name": ERA_NAME,
                "sovereign_operator": SOVEREIGN_OPERATOR,
                "sovereign_legal_name": SOVEREIGN_LEGAL_NAME,
                "core_radius_km": round(self.r_core / 1000.0, 1),
                "plasma_density": self.rho,
                "b_poloidal_tesla": round(self.b_poloidal, 7),
                "b_toroidal_tesla": round(self.b_toroidal, 7),
                "magnetic_reynolds_Rm": dim["magnetic_reynolds_Rm"],
                "elsasser_number": dim["elsasser_number_Lambda"],
                "alfven_velocity_m_s": alf["alfven_velocity_m_s"],
                "total_evolution_years": round(self.current_time_s / (365.25 * 86400.0), 1),
                "steps_completed": len(self.step_history)
            }


MagnetohydrodynamicDynamoSimFabric = MagnetohydrodynamicDynamoSim
