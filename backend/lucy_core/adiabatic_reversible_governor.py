"""
Stage 246: Thermodynamically Reversible Landauer-Zero Computation & Adiabatic Switching Governor
Era 25: Omni-Dimensional Super-Intelligence Matrix, Astro-Cognitive Planetary Orchestration & Sovereign Trans-Singularity Metamaterials

Sovereign Human Operator: Senin (Senin Ali K P)

Provides:
- Landauer Bound Evaluation: E_min = k_B * T * ln(2) per Erased Bit
- Bijective Reversible Logic Primitive Synthesis: Fredkin (CSWAP), Toffoli (CCNOT), and Feynman (CNOT)
- Conservative Bit-Weight Invariance (Zero Information Entropy Destruction)
- Adiabatic Charge-Recovery Switching Energy Dissipation: E_diss = (RC / T_ramp) * C * V^2
- Zero-Heat Reversible Logic Pipeline Execution & Thermodynamic Efficiency Auditing
- 100% Offline, Pure Python, Deterministic, Zero Cloud Dependencies
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import math

STAGE = 246
STAGE_NAME = "Thermodynamically Reversible Landauer-Zero Computation & Adiabatic Switching Governor"
ERA = 25
ERA_NAME = "Omni-Dimensional Super-Intelligence Matrix, Astro-Cognitive Planetary Orchestration & Sovereign Trans-Singularity Metamaterials"

# Boltzmann Constant (J/K)
K_BOLTZMANN = 1.380649e-23


class ReversibleGateType(Enum):
    FEYNMAN_CNOT = "FEYNMAN_CNOT"
    FREDKIN_CSWAP = "FREDKIN_CSWAP"
    TOFFOLI_CCNOT = "TOFFOLI_CCNOT"
    PAULI_X = "PAULI_X"


class AdiabaticReversibleGovernorFabric:
    """
    Thermodynamically Reversible Landauer-Zero Computation & Adiabatic Governor.
    Executes bijective logic transformations that conserve information entropy,
    simulates adiabatic charge recovery, and evaluates heat dissipation against Landauer's limit.
    """
    def __init__(self, temperature_kelvin: float = 300.0):
        self.temperature_kelvin: float = temperature_kelvin
        self.total_reversible_ops: int = 0
        self.total_bits_erased: int = 0
        self.total_dissipated_joules: float = 0.0

    @property
    def landauer_energy_per_bit_joules(self) -> float:
        # E = k_B * T * ln(2)
        return K_BOLTZMANN * self.temperature_kelvin * math.log(2.0)

    def execute_feynman_cnot(self, control: int, target: int) -> Tuple[int, int]:
        """
        Feynman Gate (CNOT):
        (C, T) -> (C, T ^ C)
        Self-inverse and reversible.
        """
        c_out = control & 1
        t_out = (target ^ control) & 1
        self.total_reversible_ops += 1
        return c_out, t_out

    def execute_fredkin_cswap(self, control: int, a: int, b: int) -> Tuple[int, int, int]:
        """
        Fredkin Gate (Controlled-SWAP):
        (C, A, B) -> (C, A if C=0 else B, B if C=0 else A)
        Conservative: Number of 1s in input equals number of 1s in output!
        """
        c = control & 1
        a_in = a & 1
        b_in = b & 1
        if c == 1:
            a_out, b_out = b_in, a_in
        else:
            a_out, b_out = a_in, b_in
        self.total_reversible_ops += 1
        return c, a_out, b_out

    def execute_toffoli_ccnot(self, c1: int, c2: int, target: int) -> Tuple[int, int, int]:
        """
        Toffoli Gate (CCNOT):
        (C1, C2, T) -> (C1, C2, T ^ (C1 & C2))
        Universal for reversible computing.
        """
        c1_out = c1 & 1
        c2_out = c2 & 1
        t_out = (target ^ (c1 & c2)) & 1
        self.total_reversible_ops += 1
        return c1_out, c2_out, t_out

    def compute_adiabatic_switching_dissipation(
        self,
        capacitance_f: float = 1e-15,     # 1 fF gate capacitance
        voltage_v: float = 0.8,            # 0.8 V
        resistance_ohms: float = 1000.0,   # 1 kOhm channel resistance
        ramp_time_seconds: float = 10e-9   # 10 ns adiabatic ramp
    ) -> Dict[str, Any]:
        """
        Calculates energy dissipation under adiabatic slow charging:
        E_adiabatic = (RC / T_ramp) * C * V^2
        Compare to conventional abrupt CMOS: E_cmos = 0.5 * C * V^2.
        """
        rc = resistance_ohms * capacitance_f
        e_cmos = 0.5 * capacitance_f * (voltage_v ** 2)

        if ramp_time_seconds <= rc:
            e_adiabatic = e_cmos
        else:
            e_adiabatic = (rc / ramp_time_seconds) * capacitance_f * (voltage_v ** 2)

        energy_savings_ratio = e_cmos / (e_adiabatic + 1e-30)
        self.total_dissipated_joules += e_adiabatic

        return {
            "capacitance_fF": capacitance_f * 1e15,
            "voltage_v": voltage_v,
            "ramp_time_ns": ramp_time_seconds * 1e9,
            "rc_time_constant_ps": rc * 1e12,
            "conventional_cmos_energy_joules": e_cmos,
            "adiabatic_dissipated_energy_joules": e_adiabatic,
            "energy_reduction_factor": round(energy_savings_ratio, 2),
            "below_landauer_limit": e_adiabatic < self.landauer_energy_per_bit_joules
        }

    def simulate_irreversible_erasure(self, bits_to_erase: int) -> float:
        """
        Simulates irreversible erasure of bits, dissipating Landauer heat:
        Q = N * k_B * T * ln(2).
        """
        if bits_to_erase < 0:
            raise ValueError("Bits to erase must be non-negative.")
        q_dissipated = bits_to_erase * self.landauer_energy_per_bit_joules
        self.total_bits_erased += bits_to_erase
        self.total_dissipated_joules += q_dissipated
        return q_dissipated

    def status(self) -> Dict[str, Any]:
        return {
            "stage": STAGE,
            "stage_name": STAGE_NAME,
            "era": ERA,
            "era_name": ERA_NAME,
            "temperature_k": self.temperature_kelvin,
            "landauer_limit_joules_per_bit": self.landauer_energy_per_bit_joules,
            "landauer_limit_ev": self.landauer_energy_per_bit_joules / 1.602176634e-19,
            "total_reversible_ops": self.total_reversible_ops,
            "total_bits_erased": self.total_bits_erased,
            "total_dissipated_joules": self.total_dissipated_joules
        }

    def format_ascii_status(self) -> str:
        s = self.status()
        l_ev = f"{s['landauer_limit_ev']:.5f} eV / bit"
        l_j = f"{s['landauer_limit_joules_per_bit']:.3e} J"
        temp_str = f"{s['temperature_k']} K"
        diss_str = f"{s['total_dissipated_joules']:.3e} J"
        lines = [
            "+-------------------------------------------------------------------------+",
            f"|      STAGE {STAGE}: {STAGE_NAME[:48]:<48} |",
            f"|      Era {ERA}: {ERA_NAME[:53]:<53} |",
            "+-------------------------------------------------------------------------+",
            f"| Operating Temp (K)   : {temp_str:<48} |",
            f"| Landauer Limit Bound : {l_ev:<48} |",
            f"| Landauer Joules/Bit  : {l_j:<48} |",
            f"| Reversible Logic Ops : {s['total_reversible_ops']:<48} |",
            f"| Bits Erased (Heat)   : {s['total_bits_erased']:<48} |",
            f"| Dissipated Joules    : {diss_str:<48} |",
            "+-------------------------------------------------------------------------+"
        ]
        return "\n".join(lines)
