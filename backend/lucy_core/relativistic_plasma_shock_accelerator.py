"""
LUCY Autonomous Sovereign AGI Kernel - Era 28: Quantum Chromodynamic Confinement & Spacetime Geometry
Stage 274: Relativistic Plasma Shock Magnetosonic Wave Accelerator & Fermi Cosmic-Ray Compressor
Author & Permanent Sovereign Operator: Senin (Senin Ali K P)

Mathematical & Plasma Physics Foundations:
1. Relativistic MHD Shock Jump Conditions (Rankine-Hugoniot):
   Compression ratio: r = rho_downstream / rho_upstream = u_upstream / u_downstream
   Magnetic compression: B_perp_2 = r * B_perp_1
   For non-relativistic strong shock: r_max = (gamma + 1)/(gamma - 1) = 4 (for gamma=5/3)
   For ultra-relativistic strong shock: r_max = 7 (for gamma=4/3).
2. Diffusive Shock Acceleration (First-Order Fermi Acceleration):
   Average fractional energy gain per round-trip crossing:
   < Delta E / E > = (4/3) * (u_1 - u_2) / c
   Escape probability per cycle: P_esc = 4 * u_2 / c
   Universal power-law differential energy spectrum:
   N(E) ~ E^-p, where p = (r + 2) / (r - 1).
3. Hillas Criterion for Maximum Particle Acceleration:
   E_max = Z * e * B * R_shock * beta_shock
   determines the upper cosmic-ray cutoff energy in TeV/PeV/EeV regimes.
"""

import math
import threading
from typing import Dict, List, Tuple, Any, Optional

SOVEREIGN_OPERATOR = "Senin"
SOVEREIGN_LEGAL_NAME = "Senin Ali K P"
STAGE_ID = 274
STAGE = 274
STAGE_NAME = "Relativistic Plasma Shock Magnetosonic Wave Accelerator & Fermi Cosmic-Ray Compressor"
ERA_ID = 28
ERA = 28
ERA_NAME = "Quantum Chromodynamic Confinement, Non-Commutative Spacetime Geometry & Sovereign Astro-Topological Singularity Synthesis"

SPEED_OF_LIGHT_M_S = 299792458.0
ELEMENTARY_CHARGE_C = 1.602176634e-19


class RelativisticPlasmaShockAccelerator:
    """
    Simulates relativistic plasma shock dynamics, computes Rankine-Hugoniot jump conditions,
    models first-order Fermi diffusive shock acceleration, and evaluates cosmic-ray power-law spectra.
    """

    def __init__(
        self,
        shock_speed_c: float = 0.1,         # 10% of light speed (e.g. Supernova remnant)
        upstream_density_m3: float = 1e7,    # Interstellar medium density
        upstream_b_field_tesla: float = 3e-9,# 30 microGauss
        adiabatic_index: float = 5.0 / 3.0
    ):
        self._lock = threading.RLock()
        self.beta_shock = max(0.001, min(0.999, float(shock_speed_c)))
        self.rho_1 = max(1e-10, float(upstream_density_m3))
        self.b_1 = max(1e-15, float(upstream_b_field_tesla))
        self.gamma_ad = max(1.1, min(2.0, float(adiabatic_index)))
        self.shock_acceleration_events: List[Dict[str, Any]] = []

    def compute_shock_jump_conditions(
        self,
        mach_number: float = 20.0
    ) -> Dict[str, float]:
        """
        Solves Rankine-Hugoniot jump relations for hydro/MHD shock:
        Compression ratio: r = ( (gamma+1)*M^2 ) / ( (gamma-1)*M^2 + 2 )
        Downstream magnetic field: B_2 = r * B_1
        """
        with self._lock:
            m = max(1.01, float(mach_number))
            gamma = self.gamma_ad

            # Standard hydrodynamic / weak-field MHD compression ratio
            num = (gamma + 1.0) * (m ** 2)
            den = (gamma - 1.0) * (m ** 2) + 2.0
            r_comp = num / den

            # Asymptotic limit
            r_max = (gamma + 1.0) / (gamma - 1.0)
            r_comp = min(r_max, max(1.0, r_comp))

            # Downstream quantities
            rho_2 = self.rho_1 * r_comp
            b_2 = self.b_1 * r_comp
            u_1 = self.beta_shock * SPEED_OF_LIGHT_M_S
            u_2 = u_1 / r_comp

            return {
                "mach_number": round(m, 2),
                "compression_ratio_r": round(r_comp, 4),
                "asymptotic_r_max": round(r_max, 4),
                "upstream_density": self.rho_1,
                "downstream_density": round(rho_2, 4),
                "upstream_b_tesla": self.b_1,
                "downstream_b_tesla": b_2,
                "upstream_speed_m_s": round(u_1, 2),
                "downstream_speed_m_s": round(u_2, 2)
            }

    def compute_fermi_acceleration_spectrum(
        self,
        mach_number: float = 20.0,
        initial_energy_gev: float = 1.0,
        num_cycles: int = 50
    ) -> Dict[str, Any]:
        """
        Models first-order Fermi diffusive shock acceleration:
        Energy gain per cycle: Delta_E / E = (4/3) * (u1 - u2) / c
        Spectral index: p = (r + 2) / (r - 1)
        """
        with self._lock:
            jumps = self.compute_shock_jump_conditions(mach_number)
            r = jumps["compression_ratio_r"]

            # Universal power-law index p = (r + 2) / (r - 1)
            spectral_index_p = (r + 2.0) / max(0.01, (r - 1.0))

            # Fractional gain per crossing
            u1 = jumps["upstream_speed_m_s"]
            u2 = jumps["downstream_speed_m_s"]
            delta_e_over_e = (4.0 / 3.0) * (u1 - u2) / SPEED_OF_LIGHT_M_S

            # Energy after N cycles: E_final = E_0 * (1 + delta_e_over_e)^N
            e_final = initial_energy_gev * ((1.0 + delta_e_over_e) ** num_cycles)

            # Escape probability
            p_escape = 4.0 * (u2 / SPEED_OF_LIGHT_M_S)

            record = {
                "mach_number": mach_number,
                "compression_ratio_r": r,
                "spectral_index_p": round(spectral_index_p, 4),
                "energy_gain_fraction_per_cycle": round(delta_e_over_e, 6),
                "escape_probability_per_cycle": round(p_escape, 6),
                "cycles_simulated": num_cycles,
                "initial_energy_gev": initial_energy_gev,
                "final_energy_gev": round(e_final, 4),
                "energy_amplification_factor": round(e_final / max(1e-12, initial_energy_gev), 2)
            }
            self.shock_acceleration_events.append(record)
            return record

    def compute_hillas_maximum_energy(
        self,
        shock_radius_m: float = 3.086e17,  # ~ 10 parsecs
        charge_number_z: int = 1            # Proton (Z=1), Iron (Z=26)
    ) -> Dict[str, float]:
        """
        Calculates maximum reachable cosmic-ray energy via Hillas criterion:
        E_max = Z * e * B_downstream * R_shock * beta_shock
        Expressed in electron-volts (eV) and Peta-electron-volts (PeV, 10^15 eV).
        """
        with self._lock:
            jumps = self.compute_shock_jump_conditions(mach_number=30.0)
            b_downstream = jumps["downstream_b_tesla"]

            # E_max in Joules: Z * e * B * R * beta
            e_max_joules = float(charge_number_z) * ELEMENTARY_CHARGE_C * b_downstream * shock_radius_m * self.beta_shock
            e_max_ev = e_max_joules / ELEMENTARY_CHARGE_C
            e_max_pev = e_max_ev / 1e15

            return {
                "shock_radius_m": shock_radius_m,
                "shock_radius_pc": round(shock_radius_m / 3.086e16, 2),
                "particle_charge_z": charge_number_z,
                "compressed_magnetic_field_tesla": b_downstream,
                "max_energy_ev": e_max_ev,
                "max_energy_pev": round(e_max_pev, 4),
                "cosmic_ray_knee_regime": (0.1 <= e_max_pev <= 10.0)
            }

    def get_status(self) -> Dict[str, Any]:
        """Returns comprehensive status of Stage 274."""
        with self._lock:
            jumps = self.compute_shock_jump_conditions()
            hillas = self.compute_hillas_maximum_energy()
            return {
                "stage": STAGE_ID,
                "stage_name": STAGE_NAME,
                "era": ERA_ID,
                "era_name": ERA_NAME,
                "sovereign_operator": SOVEREIGN_OPERATOR,
                "sovereign_legal_name": SOVEREIGN_LEGAL_NAME,
                "shock_speed_c": self.beta_shock,
                "adiabatic_index": self.gamma_ad,
                "compression_ratio_r": jumps["compression_ratio_r"],
                "asymptotic_spectral_index_p": round((jumps["compression_ratio_r"] + 2.0) / (jumps["compression_ratio_r"] - 1.0), 4),
                "hillas_max_energy_pev": hillas["max_energy_pev"],
                "total_acceleration_events": len(self.shock_acceleration_events)
            }


RelativisticPlasmaShockAcceleratorFabric = RelativisticPlasmaShockAccelerator
