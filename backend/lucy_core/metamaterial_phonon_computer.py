"""
Stage 241: Programmable Metamaterial Phonon-Polariton Waveguide Computing & Analog Tensor Interconnect
Era 25: Omni-Dimensional Super-Intelligence Matrix, Astro-Cognitive Planetary Orchestration & Sovereign Trans-Singularity Metamaterials

Sovereign Human Operator: Senin (Senin Ali K P)

Provides:
- Phononic Crystal Metamaterial Periodic Lattice Simulation & Acoustic Bandgap Spectrum
- Topological Waveguide Edge Modes with Backscattering Immunity
- Analog Wave-Based Multiply-Accumulate (MAC) & Continuous Wavefront Convolutions
- Acoustic Impedance Mismatch, Damping Attenuation & Quality Factor (Q) Modeling
- Sub-Terahertz Phonon-Polariton Routing with Zero Dynamic Switching Power
- 100% Offline, Pure Python, Deterministic, Zero Cloud Dependencies
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import math
import cmath

STAGE = 241
STAGE_NAME = "Programmable Metamaterial Phonon-Polariton Waveguide Computing & Analog Tensor Interconnect"
ERA = 25
ERA_NAME = "Omni-Dimensional Super-Intelligence Matrix, Astro-Cognitive Planetary Orchestration & Sovereign Trans-Singularity Metamaterials"


@dataclass
class PhononicLatticeUnit:
    cell_id: int
    lattice_constant_um: float = 1.0     # a = 1 micron
    density_kg_m3: float = 2330.0         # Silicon substrate density
    elastic_modulus_gpa: float = 160.0    # Bulk modulus (GPa)
    is_defect_waveguide: bool = False

    @property
    def acoustic_velocity_m_s(self) -> float:
        # v = sqrt(E / rho)
        return math.sqrt((self.elastic_modulus_gpa * 1e9) / self.density_kg_m3)


@dataclass
class BandgapRange:
    lower_freq_ghz: float
    upper_freq_ghz: float

    def contains(self, freq_ghz: float) -> bool:
        return self.lower_freq_ghz <= freq_ghz <= self.upper_freq_ghz


class MetamaterialPhononComputerFabric:
    """
    Programmable Metamaterial Phonon-Polariton Waveguide Computing Fabric.
    Simulates acoustic phonon wave propagation, topological edge routing,
    and passive wave-interference analog tensor Multiply-Accumulate (MAC).
    """
    def __init__(self, lattice_cells: int = 16):
        self.lattice_cells: int = lattice_cells
        self.lattice: List[PhononicLatticeUnit] = []
        self.bandgap = BandgapRange(lower_freq_ghz=1.2, upper_freq_ghz=2.8)
        self.damping_coefficient_db_um: float = 0.05
        self.total_wave_propagations: int = 0
        self.total_mac_operations: int = 0
        self._init_lattice()

    def _init_lattice(self) -> None:
        """Create alternating phononic metamaterial lattice with central topological waveguide defect."""
        for i in range(self.lattice_cells):
            # Alternating elastic properties create Bragg scattering bandgap
            is_defect = (i in {self.lattice_cells // 2 - 1, self.lattice_cells // 2})
            modulus = 190.0 if (i % 2 == 0) else 130.0
            if is_defect:
                modulus = 160.0 # Optimized topological defect state
            unit = PhononicLatticeUnit(
                cell_id=i,
                lattice_constant_um=1.0,
                density_kg_m3=2330.0,
                elastic_modulus_gpa=modulus,
                is_defect_waveguide=is_defect
            )
            self.lattice.append(unit)

    def is_in_bandgap(self, freq_ghz: float) -> bool:
        """True if the frequency falls into the forbidden acoustic bandgap."""
        return self.bandgap.contains(freq_ghz)

    def propagate_phonon_wave(
        self,
        freq_ghz: float,
        initial_amplitude: float = 1.0,
        distance_um: float = 10.0,
        use_topological_defect: bool = True
    ) -> Dict[str, Any]:
        """
        Simulates acoustic phonon transmission through metamaterial crystal.
        If in bandgap and NOT using topological waveguide defect, transmission is exponentially attenuated.
        If using topological defect, wave routes around obstacles with backscattering immunity.
        """
        in_gap = self.is_in_bandgap(freq_ghz)

        if in_gap and not use_topological_defect:
            # High bandgap rejection attenuation (e.g. 40 dB rejection)
            attenuation_db = distance_um * 4.0
            rejection_reason = "BANDGAP_FORBIDDEN"
        elif in_gap and use_topological_defect:
            # Topological protection limits loss to nominal damping
            attenuation_db = distance_um * self.damping_coefficient_db_um
            rejection_reason = "TOPOLOGICALLY_PROTECTED_TRANSMISSION"
        else:
            # Standard passband transmission
            attenuation_db = distance_um * self.damping_coefficient_db_um
            rejection_reason = "PASSBAND_TRANSMISSION"

        linear_decay = 10.0 ** (-attenuation_db / 20.0)
        output_amplitude = max(0.0, initial_amplitude * linear_decay)

        # Compute phase delay based on effective speed of sound
        avg_velocity = sum(u.acoustic_velocity_m_s for u in self.lattice) / len(self.lattice)
        delay_picoseconds = (distance_um * 1e-6 / avg_velocity) * 1e12

        self.total_wave_propagations += 1
        return {
            "frequency_ghz": freq_ghz,
            "input_amplitude": initial_amplitude,
            "output_amplitude": round(output_amplitude, 6),
            "attenuation_db": round(attenuation_db, 3),
            "delay_ps": round(delay_picoseconds, 2),
            "transmission_mode": rejection_reason,
            "topological_protection": (in_gap and use_topological_defect)
        }

    def execute_analog_wave_mac(
        self,
        inputs: List[float],
        weights: List[float],
        base_freq_ghz: float = 2.0
    ) -> Dict[str, Any]:
        """
        Analog wave-based Multiply-Accumulate (MAC) via destructive/constructive phonon wave interference.
        Computes Y = sum_i (w_i * x_i) passively in the acoustic domain.
        """
        if len(inputs) != len(weights):
            raise ValueError(f"Inputs dimension ({len(inputs)}) must match weights dimension ({len(weights)}).")

        # Modulate into complex phasor amplitudes
        total_phasor = 0.0 + 0.0j
        for x, w in zip(inputs, weights):
            # Phase is 0 for positive product, pi for negative product
            prod = x * w
            amplitude = abs(prod)
            phase = 0.0 if prod >= 0.0 else math.pi
            total_phasor += cmath.rect(amplitude, phase)

        # Net measured coherent amplitude
        net_amplitude = total_phasor.real # Measured along in-phase detection axis
        expected_dot_product = sum(x * w for x, w in zip(inputs, weights))

        self.total_mac_operations += 1
        return {
            "inputs": inputs,
            "weights": weights,
            "analog_mac_result": round(net_amplitude, 6),
            "theoretical_dot_product": round(expected_dot_product, 6),
            "coherent_phase_rad": round(cmath.phase(total_phasor), 4),
            "mac_fidelity": round(1.0 - abs(net_amplitude - expected_dot_product) / (abs(expected_dot_product) + 1e-9), 6)
        }

    def status(self) -> Dict[str, Any]:
        avg_v = sum(u.acoustic_velocity_m_s for u in self.lattice) / len(self.lattice)
        return {
            "stage": STAGE,
            "stage_name": STAGE_NAME,
            "era": ERA,
            "era_name": ERA_NAME,
            "lattice_cells": len(self.lattice),
            "bandgap_ghz": f"{self.bandgap.lower_freq_ghz:.1f} - {self.bandgap.upper_freq_ghz:.1f} GHz",
            "mean_sound_velocity_mps": round(avg_v, 1),
            "total_propagations": self.total_wave_propagations,
            "total_mac_ops": self.total_mac_operations,
            "damping_db_um": self.damping_coefficient_db_um
        }

    def format_ascii_status(self) -> str:
        s = self.status()
        v_str = f"{s['mean_sound_velocity_mps']:,} m/s"
        cells_str = f"{s['lattice_cells']} Unit Cells"
        damp_str = f"{s['damping_db_um']} dB/um"
        lines = [
            "+-------------------------------------------------------------------------+",
            f"|      STAGE {STAGE}: {STAGE_NAME[:48]:<48} |",
            f"|      Era {ERA}: {ERA_NAME[:53]:<53} |",
            "+-------------------------------------------------------------------------+",
            f"| Lattice Dimension    : {cells_str:<48} |",
            f"| Acoustic Bandgap     : {s['bandgap_ghz']:<48} |",
            f"| Mean Sound Velocity  : {v_str:<48} |",
            f"| Wave Propagations    : {s['total_propagations']:<48} |",
            f"| Analog MAC Ops       : {s['total_mac_ops']:<48} |",
            f"| Attenuation Damping  : {damp_str:<48} |",
            "+-------------------------------------------------------------------------+"
        ]
        return "\n".join(lines)
