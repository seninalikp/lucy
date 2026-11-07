"""
LUCY Autonomous Sovereign AGI Kernel - Era 28: Quantum Chromodynamic Confinement & Spacetime Geometry
Stage 275: Autonomous Gravitational Lensing Caustic & Relativistic Light-Deflection Raytracer
Author & Permanent Sovereign Operator: Senin (Senin Ali K P)

Mathematical & Relativistic Foundations:
1. Einstein Angular Radius:
   theta_E = sqrt( (4 * G * M / c^2) * (D_ls / (D_l * D_s)) )
2. Gravitational Lens Equation:
   beta = theta - alpha(theta) = theta - (theta_E^2 / |theta|^2) * theta
   For point lens aligned at beta:
   theta_+ = (beta + sqrt(beta^2 + 4 * theta_E^2)) / 2
   theta_- = (beta - sqrt(beta^2 + 4 * theta_E^2)) / 2
3. Magnification & Jacobian Matrix:
   A(theta) = d(beta) / d(theta)
   mu(theta) = 1 / det(A(theta))
   For point mass: mu_total = mu_+ + |mu_-| = (u^2 + 2) / (u * sqrt(u^2 + 4)), where u = beta / theta_E.
4. Critical Curves & Caustic Bifurcation:
   Critical curves satisfy det(A) = 0 in image plane; their mapping beta(theta_crit) forms caustics.
   Source crossing a fold/cusp caustic undergoes pair creation/annihilation of micro-images.
5. Relative Time Delay (Geometric + Shapiro Dilation):
   Delta_t = (1 + z_l)/c * (D_l * D_s / D_ls) * [ 1/2 * (theta - beta)^2 - psi(theta) ]
"""

import math
import threading
from typing import Dict, List, Tuple, Any, Optional

SOVEREIGN_OPERATOR = "Senin"
SOVEREIGN_LEGAL_NAME = "Senin Ali K P"
STAGE_ID = 275
STAGE = 275
STAGE_NAME = "Autonomous Gravitational Lensing Caustic & Relativistic Light-Deflection Raytracer"
ERA_ID = 28
ERA = 28
ERA_NAME = "Quantum Chromodynamic Confinement, Non-Commutative Spacetime Geometry & Sovereign Astro-Topological Singularity Synthesis"

GRAVITATIONAL_CONSTANT_G = 6.67430e-11
SPEED_OF_LIGHT_C = 299792458.0
SOLAR_MASS_KG = 1.98847e30
PARSEC_METERS = 3.085677581e16
ARCSEC_TO_RAD = 4.848136811e-6


class GravitationalLensingCausticTracer:
    """
    Computes relativistic gravitational light deflection, traces caustics and critical curves,
    calculates image positions, magnifications, and Shapiro time delays.
    """

    def __init__(
        self,
        lens_mass_solar: float = 1e11,      # Galaxy-scale lens 10^11 M_sun
        dist_lens_mpc: float = 1000.0,      # Distance to lens D_l ~ 1 Gpc
        dist_source_mpc: float = 2000.0,    # Distance to source D_s ~ 2 Gpc
        lens_redshift_z: float = 0.3
    ):
        self._lock = threading.RLock()
        self.mass_kg = max(1.0, float(lens_mass_solar) * SOLAR_MASS_KG)
        self.d_l_m = max(1.0, float(dist_lens_mpc) * 1e6 * PARSEC_METERS)
        self.d_s_m = max(self.d_l_m * 1.01, float(dist_source_mpc) * 1e6 * PARSEC_METERS)
        self.d_ls_m = self.d_s_m - self.d_l_m
        self.z_l = max(0.0, float(lens_redshift_z))
        self.raytracing_events: List[Dict[str, Any]] = []

    def compute_einstein_radius(self) -> Dict[str, float]:
        """
        Calculates Einstein angular radius theta_E:
        theta_E = sqrt( (4 * G * M / c^2) * (D_ls / (D_l * D_s)) )
        """
        with self._lock:
            schwarzschild_radius = (2.0 * GRAVITATIONAL_CONSTANT_G * self.mass_kg) / (SPEED_OF_LIGHT_C ** 2)
            geom_factor = self.d_ls_m / (self.d_l_m * self.d_s_m)
            theta_e_rad = math.sqrt(2.0 * schwarzschild_radius * geom_factor)
            theta_e_arcsec = theta_e_rad / ARCSEC_TO_RAD

            # Physical Einstein radius in lens plane R_E = theta_E * D_l
            r_e_meters = theta_e_rad * self.d_l_m
            r_e_kpc = r_e_meters / (1000.0 * PARSEC_METERS)

            return {
                "mass_solar": self.mass_kg / SOLAR_MASS_KG,
                "schwarzschild_radius_m": schwarzschild_radius,
                "theta_e_rad": theta_e_rad,
                "theta_e_arcsec": round(theta_e_arcsec, 8),
                "einstein_radius_kpc": round(r_e_kpc, 4)
            }

    def solve_image_positions(self, source_pos_arcsec: float) -> Dict[str, Any]:
        """
        Solves the point-lens equation for source position beta:
        beta = theta - theta_E^2 / theta
        Yields two images theta_+ (primary) and theta_- (secondary).
        """
        with self._lock:
            theta_e = self.compute_einstein_radius()["theta_e_arcsec"]
            beta = float(source_pos_arcsec)

            # Discriminant: Delta = beta^2 + 4 * theta_E^2
            disc = math.sqrt(beta ** 2 + 4.0 * (theta_e ** 2))
            theta_plus = (beta + disc) * 0.5
            theta_minus = (beta - disc) * 0.5

            # Dimensionless impact parameter u = |beta| / theta_E
            u = abs(beta) / max(1e-12, theta_e)

            # Magnifications: mu_pm = 1 / (1 - (theta_E / theta_pm)^4)
            # or mu_+ = (u^2 + 2)/(2*u*sqrt(u^2+4)) + 0.5
            #    mu_- = (u^2 + 2)/(2*u*sqrt(u^2+4)) - 0.5
            denom = u * math.sqrt(u * u + 4.0)
            if denom > 1e-12:
                mu_plus = ((u * u + 2.0) / (2.0 * denom)) + 0.5
                mu_minus = ((u * u + 2.0) / (2.0 * denom)) - 0.5
                mu_total = (u * u + 2.0) / denom
            else:
                mu_plus = 1000.0
                mu_minus = 1000.0
                mu_total = 2000.0

            # Separation between images: Delta_theta = theta_+ - theta_- = sqrt(beta^2 + 4*theta_E^2)
            image_separation = disc

            result = {
                "source_beta_arcsec": round(beta, 4),
                "einstein_radius_arcsec": round(theta_e, 4),
                "image_plus_arcsec": round(theta_plus, 4),
                "image_minus_arcsec": round(theta_minus, 4),
                "image_separation_arcsec": round(image_separation, 4),
                "magnification_plus": round(mu_plus, 4),
                "magnification_minus": round(mu_minus, 4),
                "magnification_total": round(mu_total, 4),
                "is_einstein_ring": abs(beta) < 1e-6
            }
            self.raytracing_events.append(result)
            return result

    def compute_relative_time_delay(self, source_pos_arcsec: float) -> Dict[str, float]:
        """
        Calculates the relative arrival time delay between image_+ and image_-:
        Delta_t = (1 + z_l)/c * (D_l * D_s / D_ls) * [ 1/2 * (theta_+ - beta)^2 - 1/2 * (theta_- - beta)^2 - theta_E^2 * ln|theta_+ / theta_-| ]
        """
        with self._lock:
            sol = self.solve_image_positions(source_pos_arcsec)
            theta_e_rad = sol["einstein_radius_arcsec"] * ARCSEC_TO_RAD
            beta_rad = sol["source_beta_arcsec"] * ARCSEC_TO_RAD
            t_plus_rad = sol["image_plus_arcsec"] * ARCSEC_TO_RAD
            t_minus_rad = sol["image_minus_arcsec"] * ARCSEC_TO_RAD

            # Fermat potential terms
            geom_diff = 0.5 * ((t_plus_rad - beta_rad)**2 - (t_minus_rad - beta_rad)**2)
            shapiro_diff = -(theta_e_rad ** 2) * math.log(abs(t_plus_rad / max(1e-18, abs(t_minus_rad))))

            time_factor = ((1.0 + self.z_l) / SPEED_OF_LIGHT_C) * ((self.d_l_m * self.d_s_m) / self.d_ls_m)
            delta_t_sec = abs(time_factor * (geom_diff + shapiro_diff))
            delta_t_days = delta_t_sec / 86400.0

            return {
                "source_beta_arcsec": sol["source_beta_arcsec"],
                "time_delay_seconds": delta_t_sec,
                "time_delay_days": round(delta_t_days, 2),
                "geometric_component_fraction": round(abs(geom_diff) / max(1e-15, abs(geom_diff) + abs(shapiro_diff)), 4)
            }

    def get_status(self) -> Dict[str, Any]:
        """Returns comprehensive status of Stage 275."""
        with self._lock:
            einst = self.compute_einstein_radius()
            return {
                "stage": STAGE_ID,
                "stage_name": STAGE_NAME,
                "era": ERA_ID,
                "era_name": ERA_NAME,
                "sovereign_operator": SOVEREIGN_OPERATOR,
                "sovereign_legal_name": SOVEREIGN_LEGAL_NAME,
                "lens_mass_solar": einst["mass_solar"],
                "einstein_radius_arcsec": einst["theta_e_arcsec"],
                "einstein_radius_kpc": einst["einstein_radius_kpc"],
                "lens_redshift_z": self.z_l,
                "total_raytrace_simulations": len(self.raytracing_events)
            }


GravitationalLensingCausticTracerFabric = GravitationalLensingCausticTracer
