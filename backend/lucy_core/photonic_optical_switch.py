"""
Stage 237: Autonomous Photonic Optical Neural Interconnect & Ultra-Low-Latency Switch Fabric
Era 24: Trans-Dimensional Cognitive Resonance, Neuromorphic Spiking Fabrics & Autonomous Sovereign AGI Singularity

Sovereign Human Operator: Senin (Senin Ali K P)

Provides:
- Wavelength-Division Multiplexing (WDM) Optical Waveguide Channel Modeling (C-Band, nm grid)
- Mach-Zehnder Interferometer (MZI) Clements/Reck Mesh Unitary Matrix Multiplication (Speed-of-Light GEMM)
- Non-Blocking Optical Micro-Ring Resonator (MRR) Crossbar Routing & Sub-Nanosecond Latency Emulation
- Optical Insertion Loss, Extinction Ratio, and Photodetector Responsivity / SNR Modeling
- Autonomous Thermo-Optic Phase Drift Calibration Feedback Loop (dn/dT compensation)
- 100% Offline, Pure Python, Deterministic, Zero Cloud Dependencies
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import cmath
import math

STAGE = 237
STAGE_NAME = "Autonomous Photonic Optical Neural Interconnect & Ultra-Low-Latency Switch Fabric"
ERA = 24
ERA_NAME = "Trans-Dimensional Cognitive Resonance, Neuromorphic Spiking Fabrics & Autonomous Sovereign AGI Singularity"


@dataclass
class OpticalChannel:
    channel_id: int
    wavelength_nm: float
    frequency_thz: float
    power_dbm: float = 0.0
    active: bool = True

    @classmethod
    def create_c_band(cls, channel_id: int, base_nm: float = 1530.0, channel_spacing_nm: float = 0.8) -> "OpticalChannel":
        wl = base_nm + channel_id * channel_spacing_nm
        # c = 299792458 m/s -> f = c / lambda
        freq = (299792458.0 / (wl * 1e-9)) / 1e12 # THz
        return cls(channel_id=channel_id, wavelength_nm=wl, frequency_thz=freq)


@dataclass
class MZIUnit:
    """
    Mach-Zehnder Interferometer 2x2 optical unitary transformation unit.
    Transfer matrix:
    [e^{i phi} cos(theta), -e^{i phi} sin(theta)]
    [sin(theta),            cos(theta)          ]
    """
    mzi_id: str
    theta: float = math.pi / 4.0   # Internal phase shift (coupling ratio)
    phi: float = 0.0               # External phase shift
    temperature_k: float = 300.0   # Operational temperature (Kelvin)
    insertion_loss_db: float = 0.15 # Loss per MZI

    def transfer_matrix(self) -> List[List[complex]]:
        cos_t = math.cos(self.theta)
        sin_t = math.sin(self.theta)
        phase_factor = cmath.exp(1j * self.phi)
        loss_factor = 10.0 ** (-self.insertion_loss_db / 20.0)

        return [
            [loss_factor * phase_factor * cos_t, -loss_factor * phase_factor * sin_t],
            [loss_factor * sin_t, loss_factor * cos_t]
        ]

    def transform_vector(self, e_in1: complex, e_in2: complex) -> Tuple[complex, complex]:
        m = self.transfer_matrix()
        e_out1 = m[0][0] * e_in1 + m[0][1] * e_in2
        e_out2 = m[1][0] * e_in1 + m[1][1] * e_in2
        return e_out1, e_out2


class PhotonicOpticalSwitchFabric:
    """
    Photonic Optical Neural Interconnect & Ultra-Low-Latency Switch Fabric.
    Simulates WDM channels, MZI optical matrix compute meshes, non-blocking
    optical routing crossbars, and automated thermo-optic phase drift compensation.
    """
    def __init__(self, num_channels: int = 8, mesh_dim: int = 4):
        self.num_channels: int = num_channels
        self.mesh_dim: int = mesh_dim
        self.silicon_refractive_index: float = 3.45 # n_eff in Si waveguide
        self.speed_of_light: float = 299792458.0     # m/s
        self.effective_c: float = self.speed_of_light / self.silicon_refractive_index # ~8.69e7 m/s
        self.channels: Dict[int, OpticalChannel] = {}
        self.mzi_mesh: Dict[str, MZIUnit] = {}
        self.routing_table: Dict[int, int] = {} # ingress_port -> egress_port
        self.temperature_kelvin: float = 300.0
        self.total_photonic_gemms: int = 0
        self.total_packets_routed: int = 0
        self.calibrations_performed: int = 0
        self._init_channels()
        self._init_mzi_mesh()

    def _init_channels(self) -> None:
        """Initialize standard dense WDM C-band channels."""
        for i in range(self.num_channels):
            self.channels[i] = OpticalChannel.create_c_band(channel_id=i)
            self.routing_table[i] = i # 1:1 direct route initially

    def _init_mzi_mesh(self) -> None:
        """Initialize Clements/Reck grid of MZI units for N-dimensional unitary operations."""
        for r in range(self.mesh_dim):
            for c in range(self.mesh_dim):
                uid = f"mzi_{r}_{c}"
                self.mzi_mesh[uid] = MZIUnit(mzi_id=uid)

    def program_route(self, ingress_port: int, egress_port: int) -> None:
        """Programs non-blocking crossbar routing path."""
        if not (0 <= ingress_port < self.num_channels) or not (0 <= egress_port < self.num_channels):
            raise ValueError(f"Invalid port index ({ingress_port} -> {egress_port}).")
        self.routing_table[ingress_port] = egress_port

    def route_optical_packet(self, ingress_port: int, packet_bytes: bytes, waveguide_length_cm: float = 2.0) -> Dict[str, Any]:
        """
        Simulates ultrafast optical packet switching through silicon waveguide interconnect.
        Computes flight time at c / n_eff and optical power insertion loss.
        """
        if ingress_port not in self.routing_table:
            raise KeyError(f"Ingress port {ingress_port} not provisioned.")

        egress_port = self.routing_table[ingress_port]
        propagation_distance_m = waveguide_length_cm * 1e-2
        flight_time_seconds = propagation_distance_m / self.effective_c
        latency_picoseconds = flight_time_seconds * 1e12

        # Waveguide propagation loss: 0.2 dB / cm
        waveguide_loss_db = 0.2 * waveguide_length_cm
        # Switch traversal loss (MRR / MZI cross-point): 0.5 dB
        switch_loss_db = 0.5
        total_loss_db = waveguide_loss_db + switch_loss_db

        input_power_mw = 10.0 ** (self.channels[ingress_port].power_dbm / 10.0)
        output_power_mw = input_power_mw * (10.0 ** (-total_loss_db / 10.0))

        self.total_packets_routed += 1
        return {
            "ingress_port": ingress_port,
            "egress_port": egress_port,
            "payload_size": len(packet_bytes),
            "latency_ps": round(latency_picoseconds, 2),
            "loss_db": round(total_loss_db, 3),
            "output_power_mw": round(output_power_mw, 4),
            "wavelength_nm": self.channels[ingress_port].wavelength_nm
        }

    def execute_optical_matrix_vector(self, input_vector: List[complex]) -> List[complex]:
        """
        Executes coherent optical Matrix-Vector Multiplication (MVM) across MZI mesh.
        Dimension N must match mesh_dim.
        """
        dim = self.mesh_dim
        if len(input_vector) != dim:
            raise ValueError(f"Input vector size {len(input_vector)} does not match mesh dimension {dim}.")

        current_vector = list(input_vector)

        # Pass through layers of 2x2 MZI units in Clements structure
        for layer in range(dim):
            offset = layer % 2
            for i in range(offset, dim - 1, 2):
                uid = f"mzi_{layer}_{i}"
                if uid in self.mzi_mesh:
                    unit = self.mzi_mesh[uid]
                    out1, out2 = unit.transform_vector(current_vector[i], current_vector[i + 1])
                    current_vector[i] = out1
                    current_vector[i + 1] = out2

        self.total_photonic_gemms += 1
        return current_vector

    def photodetect_intensities(self, complex_field: List[complex], responsivity_a_w: float = 0.85) -> List[float]:
        """
        Photodetector square-law coherent/incoherent intensity measurement:
        I_photo = Responsivity * |E|^2
        """
        intensities = []
        for e in complex_field:
            p_opt = (e.real ** 2 + e.imag ** 2)
            i_photo = responsivity_a_w * p_opt
            intensities.append(round(i_photo, 6))
        return intensities

    def induce_thermal_drift(self, delta_kelvin: float) -> None:
        """
        Simulates temperature fluctuation on photonic chip.
        Silicon thermo-optic coefficient: dn/dT ~ 1.86e-4 / K.
        Causes optical phase drift Delta theta = 2 pi / lambda * (dn/dT) * L * Delta T.
        """
        self.temperature_kelvin += delta_kelvin
        drift_rad = (delta_kelvin * 1.86e-4 * 50e-6) / (1550e-9) * 2.0 * math.pi
        for unit in self.mzi_mesh.values():
            unit.temperature_k = self.temperature_kelvin
            unit.theta = (unit.theta + drift_rad) % (2.0 * math.pi)

    def calibrate_thermo_optic_phases(self, target_theta: float = math.pi / 4.0) -> int:
        """
        Autonomous closed-loop calibration adjusting phase heaters to compensate thermal drift.
        """
        corrected = 0
        for unit in self.mzi_mesh.values():
            if abs(unit.theta - target_theta) > 1e-4:
                unit.theta = target_theta
                unit.phi = 0.0
                corrected += 1
        self.calibrations_performed += 1
        return corrected

    def status(self) -> Dict[str, Any]:
        return {
            "stage": STAGE,
            "stage_name": STAGE_NAME,
            "era": ERA,
            "era_name": ERA_NAME,
            "wdm_channels": len(self.channels),
            "mesh_dimension": self.mesh_dim,
            "mzi_units_count": len(self.mzi_mesh),
            "temperature_k": round(self.temperature_kelvin, 2),
            "photonic_gemms": self.total_photonic_gemms,
            "packets_routed": self.total_packets_routed,
            "calibrations_performed": self.calibrations_performed,
            "effective_speed_of_light_mps": round(self.effective_c, 0)
        }

    def format_ascii_status(self) -> str:
        s = self.status()
        topo_str = f"{s['mesh_dimension']}x{s['mesh_dimension']} Unitary MZI Grid"
        eff_str = f"{s['effective_speed_of_light_mps']:,} m/s"
        lines = [
            "+-------------------------------------------------------------------------+",
            f"|      STAGE {STAGE}: {STAGE_NAME[:48]:<48} |",
            f"|      Era {ERA}: {ERA_NAME[:53]:<53} |",
            "+-------------------------------------------------------------------------+",
            f"| WDM Optical Channels : {s['wdm_channels']:<48} |",
            f"| Mesh Topology        : {topo_str:<48} |",
            f"| Total MZI Elements   : {s['mzi_units_count']:<48} |",
            f"| Operating Temp (K)   : {s['temperature_k']:<48} |",
            f"| Photonic GEMM Ops    : {s['photonic_gemms']:<48} |",
            f"| Optical Packets      : {s['packets_routed']:<48} |",
            f"| Phase Calibrations   : {s['calibrations_performed']:<48} |",
            f"| Waveguide c_eff      : {eff_str:<48} |",
            "+-------------------------------------------------------------------------+"
        ]
        return "\n".join(lines)
