"""
LUCY STAGE 284: Cosmic Microwave Background (CMB) Multipole Power Spectrum & Inflationary Tensor Perturbation Engine
Sovereign Architect & Supreme Operator: Senin (Senin Ali K P)

Provides high-precision computational cosmological modeling for CMB angular power spectra
D_l = l*(l+1)/(2*pi) * C_l, Sachs-Wolfe plateau, Baryon Acoustic Oscillation (BAO) acoustic
peaks (l ~ 220, 540, 800), Silk damping dissipation tail, and primordial inflationary
tensor-to-scalar ratio r and Lyth bound field excursions.
Fully offline, thread-safe, CP1252-safe ASCII reporting.
"""

import math
import time
import threading
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

STAGE: int = 284
STAGE_NAME: str = "CMB Multipole Power Spectrum & Inflationary Tensor Perturbation Engine"
SOVEREIGN_OPERATOR: str = "Senin (Senin Ali K P)"

# Standard Cosmological Baseline Constants (Planck 2018 Parameters)
T_CMB_K: float = 2.7255                           # CMB average temperature in Kelvin
FIRST_ACOUSTIC_PEAK_L: float = 220.0             # l_1 ~ 220 (spatial flatness)
SECOND_ACOUSTIC_PEAK_L: float = 540.0            # l_2 ~ 540 (baryon density)
THIRD_ACOUSTIC_PEAK_L: float = 800.0             # l_3 ~ 800 (cold dark matter)
SILK_DAMPING_SCALE_L: float = 1200.0             # Photon diffusion damping scale


@dataclass
class CMBSpectrumSnapshot:
    """State snapshot of computed CMB multipole power spectrum."""
    l_max: int
    first_peak_d_l: float
    second_peak_d_l: float
    third_peak_d_l: float
    tensor_to_scalar_r: float
    inflation_energy_scale_gev: float
    lyth_bound_delta_phi: float
    cosmology_status: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "l_max": self.l_max,
            "first_peak_d_l": self.first_peak_d_l,
            "second_peak_d_l": self.second_peak_d_l,
            "third_peak_d_l": self.third_peak_d_l,
            "tensor_to_scalar_r": self.tensor_to_scalar_r,
            "inflation_energy_scale_gev": self.inflation_energy_scale_gev,
            "lyth_bound_delta_phi": self.lyth_bound_delta_phi,
            "cosmology_status": self.cosmology_status,
            "timestamp": self.timestamp,
        }


class CMBMultipolePowerSpectrumFabric:
    """
    Stage 284: Autonomous CMB Multipole Power Spectrum & Inflationary Tensor Perturbation Engine.
    Simulates multipoles C_l, D_l = l(l+1)C_l / (2pi), acoustic peaks, and tensor modes.
    """

    def __init__(self, sovereign_operator: str = SOVEREIGN_OPERATOR) -> None:
        self.sovereign_operator: str = sovereign_operator
        self._lock: threading.RLock = threading.RLock()
        self._evaluations_count: int = 0
        self._history: List[CMBSpectrumSnapshot] = []
        self._last_snapshot: Optional[CMBSpectrumSnapshot] = None

    def evaluate_multipole_d_l(
        self,
        ell: int,
        omega_b: float = 0.022,
        omega_c: float = 0.12,
    ) -> float:
        """
        Evaluates the temperature power spectrum D_l = l*(l+1)*C_l / (2*pi) in microKelvin^2 (uK^2).
        Models Sachs-Wolfe plateau, 3 acoustic peaks, and exponential Silk damping.
        """
        l_val = float(max(2, ell))

        # Sachs-Wolfe plateau baseline ~ 1000 uK^2
        sw_plateau = 1000.0 * (l_val / 10.0)**(-0.035)

        # First acoustic peak (l ~ 220, amplitude ~ 5750 uK^2)
        p1 = 4750.0 * math.exp(-0.5 * ((l_val - FIRST_ACOUSTIC_PEAK_L) / 65.0)**2)

        # Second acoustic peak (l ~ 540, amplitude ~ 2500 uK^2, modulation by baryon density)
        baryon_factor = (omega_b / 0.022)
        p2 = (2500.0 / math.sqrt(baryon_factor)) * math.exp(-0.5 * ((l_val - SECOND_ACOUSTIC_PEAK_L) / 90.0)**2)

        # Third acoustic peak (l ~ 800, amplitude ~ 2600 uK^2, modulation by dark matter)
        cdm_factor = (omega_c / 0.12)
        p3 = (2600.0 * math.sqrt(cdm_factor)) * math.exp(-0.5 * ((l_val - THIRD_ACOUSTIC_PEAK_L) / 110.0)**2)

        # Sum undamped power
        raw_d_l = sw_plateau + p1 + p2 + p3

        # Silk photon diffusion damping factor exp(-(l / l_D)^1.2)
        silk_damping = math.exp(-((l_val / SILK_DAMPING_SCALE_L)**1.2))

        return raw_d_l * silk_damping

    def compute_multipole_spectrum(
        self,
        l_max: int = 1500,
        omega_b: float = 0.022,
        omega_c: float = 0.12,
    ) -> Dict[str, Any]:
        """
        Computes the complete CMB multipole power spectrum from l=2 to l=l_max.
        """
        with self._lock:
            max_l = max(50, min(int(l_max), 2500))
            spectrum: List[Dict[str, float]] = []

            step_size = max(1, max_l // 150)
            for l_int in range(2, max_l + 1, step_size):
                d_l = self.evaluate_multipole_d_l(l_int, omega_b, omega_c)
                # C_l = 2*pi * D_l / (l * (l+1))
                c_l = (2.0 * math.pi * d_l) / (float(l_int) * float(l_int + 1))
                spectrum.append({
                    "multipole_l": float(l_int),
                    "d_l_microkelvin2": d_l,
                    "c_l": c_l,
                })

            d_p1 = self.evaluate_multipole_d_l(int(FIRST_ACOUSTIC_PEAK_L), omega_b, omega_c)
            d_p2 = self.evaluate_multipole_d_l(int(SECOND_ACOUSTIC_PEAK_L), omega_b, omega_c)
            d_p3 = self.evaluate_multipole_d_l(int(THIRD_ACOUSTIC_PEAK_L), omega_b, omega_c)

            return {
                "l_max": max_l,
                "first_peak_l": FIRST_ACOUSTIC_PEAK_L,
                "first_peak_d_l": d_p1,
                "second_peak_l": SECOND_ACOUSTIC_PEAK_L,
                "second_peak_d_l": d_p2,
                "third_peak_l": THIRD_ACOUSTIC_PEAK_L,
                "third_peak_d_l": d_p3,
                "total_points": len(spectrum),
                "spectrum": spectrum,
            }

    def compute_inflation_tensor_ratio(
        self,
        tensor_to_scalar_r: float = 0.03,
        e_folds: float = 60.0,
    ) -> Dict[str, Any]:
        """
        Computes primordial inflationary tensor perturbation parameters:
        r = A_t / A_s
        Inflation energy scale V^(1/4) ~ 1.04e16 GeV * (r / 0.01)^(1/4)
        Lyth field excursion bound Delta_phi / M_Pl >= sqrt(r / 8) * Delta_N
        """
        with self._lock:
            r_val = max(1e-6, min(float(tensor_to_scalar_r), 0.5))
            n_efolds = max(10.0, float(e_folds))

            # Inflation scale in GeV
            energy_scale_gev = 1.04e16 * ((r_val / 0.01)**0.25)

            # Lyth bound Delta_phi / M_Pl
            delta_phi = math.sqrt(r_val / 8.0) * n_efolds

            snapshot = CMBSpectrumSnapshot(
                l_max=1500,
                first_peak_d_l=self.evaluate_multipole_d_l(int(FIRST_ACOUSTIC_PEAK_L)),
                second_peak_d_l=self.evaluate_multipole_d_l(int(SECOND_ACOUSTIC_PEAK_L)),
                third_peak_d_l=self.evaluate_multipole_d_l(int(THIRD_ACOUSTIC_PEAK_L)),
                tensor_to_scalar_r=r_val,
                inflation_energy_scale_gev=energy_scale_gev,
                lyth_bound_delta_phi=delta_phi,
                cosmology_status="SPATIALLY_FLAT_LAMBDA_CDM",
            )

            self._evaluations_count += 1
            self._last_snapshot = snapshot
            self._history.append(snapshot)
            if len(self._history) > 100:
                self._history.pop(0)

            return {
                "tensor_to_scalar_r": r_val,
                "e_folds": n_efolds,
                "inflation_energy_scale_gev": energy_scale_gev,
                "lyth_bound_delta_phi_planck": delta_phi,
                "is_large_field_inflation": bool(delta_phi > 1.0),
                "primordial_gw_detectable": bool(r_val > 0.001),
            }

    def format_ascii_status(self) -> str:
        """CP1252-safe ASCII table representation."""
        with self._lock:
            last = self._last_snapshot
            p1 = last.first_peak_d_l if last else 5750.0
            r_val = last.tensor_to_scalar_r if last else 0.03
            escale = last.inflation_energy_scale_gev if last else 1.37e16
            lyth = last.lyth_bound_delta_phi if last else 3.67

            lines = [
                "+====================================================================+",
                "|       STAGE 284: CMB POWER SPECTRUM & INFLATIONARY TENSOR FABRIC   |",
                "+====================================================================+",
                f"| Sovereign Operator  : {self.sovereign_operator:<44} |",
                f"| Evaluations Count   : {self._evaluations_count:<44} |",
                f"| Peak 1 (l=220) D_l  : {p1:<44.2f} uK^2 |",
                f"| Tensor-to-Scalar (r): {r_val:<44.4f} |",
                f"| Inflation Scale     : {escale:<44.3e} GeV|",
                f"| Lyth Excursion      : {lyth:<44.3f} M_Pl |",
                f"| Cosmology Model     : {'FLAT_LAMBDA_CDM_CONCORDANCE':<44} |",
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
                "last_snapshot": self._last_snapshot.to_dict() if self._last_snapshot else None,
            }
