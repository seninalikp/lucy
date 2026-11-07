"""
Stage 257: Quantum Superconducting Josephson Junction SQUID Flux-State Quantum Magnetometer
Era 26: Cosmic-Scale Holomorphic Field Dynamics, Non-Equilibrium Thermodynamic Entropy Engines & Autonomous Sovereign Multi-Verse Orchestration

Sovereign Human Operator: Senin (Senin Ali K P)

Provides:
- DC & AC Josephson Relations: I = I_c * sin(phi) and d(phi)/dt = (2*e / hbar) * V = 2*pi * V / Phi_0
- Superconducting Magnetic Flux Quantum Invariance: Phi_0 = h / (2*e) = 2.067833848e-15 Wb
- DC SQUID Quantum Interference Modulation: I_c(Phi) = 2 * I_c0 * |cos(pi * Phi / Phi_0)|
- Sub-Femto-Tesla Pico-Tesla Ultra-Sensitive Magnetic Field Flux Sensing: B = Phi / Loop_Area
- RCSJ Overdamped Phase-Slip Dynamics & Flux-to-Voltage Transfer Characteristic
- 100% Offline, Pure Python, Deterministic, Zero Cloud Dependencies
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import math
import threading

STAGE = 257
STAGE_NAME = "Quantum Superconducting Josephson Junction SQUID Flux-State Quantum Magnetometer"
ERA = 26
ERA_NAME = "Cosmic-Scale Holomorphic Field Dynamics, Non-Equilibrium Thermodynamic Entropy Engines & Autonomous Sovereign Multi-Verse Orchestration"

# Fundamental Physical Constants
E_CHARGE: float = 1.602176634e-19       # Coulomb (C)
H_PLANCK: float = 6.62607015e-34        # Joule * second (J*s)
HBAR: float = H_PLANCK / (2.0 * math.pi)  # J*s
FLUX_QUANTUM_PHI0: float = H_PLANCK / (2.0 * E_CHARGE)  # ~2.067833848e-15 Wb (Tesla * m^2)


@dataclass
class SQUIDMeasurement:
    measurement_id: str
    magnetic_field_tesla: float
    flux_webers: float
    flux_quanta_units: float
    voltage_output_volts: float
    critical_current_amps: float


class JosephsonSquidMagnetometerFabric:
    """
    Superconducting Josephson Junction & SQUID Flux-State Magnetometer.
    Precision quantum magnetometer measuring external magnetic fields via flux quantization.
    """

    def __init__(
        self,
        critical_current_junction: float = 1e-6,  # 1 microampere
        loop_area_m2: float = 1e-6,              # 1 mm^2 pickup loop
        shunt_resistance_ohms: float = 10.0,     # 10 ohms
    ):
        self._lock = threading.RLock()
        self.i_c0 = float(critical_current_junction)
        self.loop_area = float(loop_area_m2)
        self.r_shunt = float(shunt_resistance_ohms)

        self.total_flux_measurements: int = 0
        self.total_ac_frequency_evals: int = 0

    def compute_dc_josephson_current(self, phase_rad: float, i_c: Optional[float] = None) -> float:
        """
        DC Josephson relation: I = I_c * sin(phi).
        """
        with self._lock:
            ic_val = i_c if i_c is not None else self.i_c0
            return ic_val * math.sin(phase_rad)

    def compute_ac_josephson_frequency(self, voltage_v: float) -> float:
        """
        AC Josephson frequency: f_J = 2 * e * V / h = V / Phi_0.
        Exact linear voltage-to-frequency converter (~483.5979 GHz/mV).
        """
        with self._lock:
            self.total_ac_frequency_evals += 1
            return abs(voltage_v) / FLUX_QUANTUM_PHI0

    def compute_squid_critical_current(self, flux_webers: float) -> float:
        """
        DC SQUID total critical current modulation with magnetic flux:
        I_c(Phi) = 2 * I_c0 * |cos(pi * Phi / Phi_0)|.
        Periodic with period Phi_0.
        """
        with self._lock:
            phase_arg = (math.pi * flux_webers) / FLUX_QUANTUM_PHI0
            return 2.0 * self.i_c0 * abs(math.cos(phase_arg))

    def flux_to_voltage_readout(
        self,
        flux_webers: float,
        bias_current_amps: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Computes voltage response across SQUID shunted junction:
        V = R * sqrt(I_bias^2 - I_c(Phi)^2) if I_bias > I_c(Phi) else 0.
        """
        with self._lock:
            self.total_flux_measurements += 1
            ic_phi = self.compute_squid_critical_current(flux_webers)
            # Default bias slightly above maximum critical current (2 * I_c0 * 1.1)
            i_bias = bias_current_amps if bias_current_amps is not None else (2.0 * self.i_c0 * 1.1)

            if i_bias > ic_phi:
                v_out = self.r_shunt * math.sqrt(i_bias ** 2 - ic_phi ** 2)
            else:
                v_out = 0.0

            flux_quanta = flux_webers / FLUX_QUANTUM_PHI0
            b_field = flux_webers / self.loop_area

            return {
                "magnetic_field_tesla": b_field,
                "flux_webers": flux_webers,
                "flux_quanta_units": round(flux_quanta, 6),
                "voltage_output_volts": v_out,
                "critical_current_amps": ic_phi,
                "bias_current_amps": i_bias,
            }

    def measure_external_field(self, b_field_tesla: float) -> Dict[str, Any]:
        """
        Simulates measurement of an applied external magnetic field B.
        Phi = B * Area.
        """
        with self._lock:
            flux = b_field_tesla * self.loop_area
            res = self.flux_to_voltage_readout(flux)
            return {
                "applied_b_tesla": b_field_tesla,
                "flux_webers": res["flux_webers"],
                "flux_quanta": res["flux_quanta_units"],
                "voltage_microvolts": round(res["voltage_output_volts"] * 1e6, 4),
                "ic_microamps": round(res["critical_current_amps"] * 1e6, 4),
            }

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "era_name": ERA_NAME,
                "flux_quantum_phi0": FLUX_QUANTUM_PHI0,
                "junction_critical_current": self.i_c0,
                "loop_area_m2": self.loop_area,
                "shunt_resistance_ohms": self.r_shunt,
                "total_flux_measurements": self.total_flux_measurements,
                "total_ac_frequency_evals": self.total_ac_frequency_evals,
            }

    def format_ascii_status(self) -> str:
        with self._lock:
            phi_str = f"{FLUX_QUANTUM_PHI0:.6e} Wb"
            ic_str = f"{self.i_c0 * 1e6:.2f} uA"
            area_str = f"{self.loop_area * 1e6:.2f} mm^2"
            meas_str = f"{self.total_flux_measurements} flux interrogations"
            ac_str = f"{self.total_ac_frequency_evals} AC evaluations"

            lines = [
                "+-------------------------------------------------------------------------+",
                "|      STAGE 257: Quantum Superconducting Josephson SQUID Magnetometer    |",
                "|      Era 26: Cosmic-Scale Holomorphic Field Dynamics                    |",
                "+-------------------------------------------------------------------------+",
                f"| Flux Quantum (Phi_0) : {phi_str:<48} |",
                f"| Critical Current     : {ic_str:<48} |",
                f"| SQUID Loop Area      : {area_str:<48} |",
                f"| Flux Interrogations  : {meas_str:<48} |",
                f"| AC Frequency Audits  : {ac_str:<48} |",
                "+-------------------------------------------------------------------------+",
            ]
            return "\n".join(lines)


# Sovereign Global Singleton
_global_squid_magnetometer: Optional[JosephsonSquidMagnetometerFabric] = None
_squid_lock = threading.RLock()


def get_squid_magnetometer() -> JosephsonSquidMagnetometerFabric:
    global _global_squid_magnetometer
    with _squid_lock:
        if _global_squid_magnetometer is None:
            _global_squid_magnetometer = JosephsonSquidMagnetometerFabric()
        return _global_squid_magnetometer
