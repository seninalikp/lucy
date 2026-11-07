r"""
backend/lucy_core/energy_budget_governor.py
Stage 227: Autonomous Hardware Energy Budget Governor & Thermal-Joule Throttle Fabric
Era 23: Universal Multi-Verse State Synthesis, Sub-Atomic Hyper-Computing & Sovereign Holographic Swarm Intelligence

100% offline, sovereign hardware energy budget governor and thermal-joule throttle fabric:
1. Dynamic Voltage and Frequency Scaling (DVFS) & Power Modeling:
   - Simulates CMOS dynamic and static leakage power: P = C * V^2 * f * alpha + I_leak * V.
   - Operating power profiles: TURBO, NOMINAL_BALANCED, CONSERVATIVE, CRITICAL_EMERGENCY.
2. Thermodynamic Junction Temperature & Thermal Throttle Governor:
   - Continuous thermal dissipation physics: dT/dt = (P_in - (T - T_ambient)/R_th) / C_th.
   - Autonomous emergency throttling when junction temperature approaches thermal ceiling (T_crit).
3. Joule Accounting & Subsystem Workload Power Attribution:
   - Cumulative energy consumption tracking in Joules (J) and Watt-hours (Wh).
   - Task-level power attribution and efficiency indexing (FLOPS per Watt / tasks per Joule).
4. Thread-safe execution fabric and CP1252-safe ASCII table formatting.
"""

from __future__ import annotations

import collections
import copy
import enum
import hashlib
import math
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union

STAGE: int = 227
STAGE_NAME: str = "Autonomous Hardware Energy Budget Governor & Thermal-Joule Throttle Fabric"
ERA: int = 23
ERA_NAME: str = "Universal Multi-Verse State Synthesis, Sub-Atomic Hyper-Computing & Sovereign Holographic Swarm Intelligence"


class PowerProfile(enum.Enum):
    TURBO = "TURBO"
    NOMINAL_BALANCED = "NOMINAL_BALANCED"
    CONSERVATIVE = "CONSERVATIVE"
    CRITICAL_EMERGENCY = "CRITICAL_EMERGENCY"


@dataclass
class DVFSState:
    frequency_ghz: float
    voltage_v: float
    relative_clock_ratio: float


PROFILE_DVFS_MAP: Dict[PowerProfile, DVFSState] = {
    PowerProfile.TURBO: DVFSState(frequency_ghz=4.5, voltage_v=1.35, relative_clock_ratio=1.0),
    PowerProfile.NOMINAL_BALANCED: DVFSState(frequency_ghz=3.2, voltage_v=1.10, relative_clock_ratio=0.71),
    PowerProfile.CONSERVATIVE: DVFSState(frequency_ghz=2.0, voltage_v=0.90, relative_clock_ratio=0.44),
    PowerProfile.CRITICAL_EMERGENCY: DVFSState(frequency_ghz=0.8, voltage_v=0.75, relative_clock_ratio=0.18),
}


@dataclass
class EnergyReceipt:
    receipt_id: str
    task_id: str
    joules_consumed: float
    duration_s: float
    average_power_w: float
    peak_temp_c: float
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "task_id": self.task_id,
            "joules_consumed": round(self.joules_consumed, 4),
            "duration_s": round(self.duration_s, 4),
            "average_power_w": round(self.average_power_w, 2),
            "peak_temp_c": round(self.peak_temp_c, 2),
            "timestamp": self.timestamp,
        }


class EnergyBudgetGovernorFabric:
    """
    Thread-safe autonomous energy budget governor and thermal-joule throttle fabric.
    """

    def __init__(
        self,
        ambient_temp_c: float = 25.0,
        thermal_resistance_r_th: float = 0.45,  # deg C / Watt
        thermal_capacitance_c_th: float = 120.0,  # Joules / deg C
        tdp_watts: float = 125.0,  # Thermal Design Power limit
        critical_temp_c: float = 90.0,  # Throttle threshold
    ) -> None:
        self._lock = threading.RLock()
        self.ambient_temp_c: float = ambient_temp_c
        self.junction_temp_c: float = ambient_temp_c
        self.r_th: float = thermal_resistance_r_th
        self.c_th: float = thermal_capacitance_c_th
        self.tdp_watts: float = tdp_watts
        self.critical_temp_c: float = critical_temp_c

        self.current_profile: PowerProfile = PowerProfile.NOMINAL_BALANCED
        self.is_throttled: bool = False
        self.throttle_count: int = 0

        # Energy consumption ledger
        self.total_joules: float = 0.0
        self.task_receipts: List[EnergyReceipt] = []
        self.last_update_time: float = time.time()

    def set_profile(self, profile: PowerProfile) -> None:
        with self._lock:
            self.current_profile = profile

    def _compute_instantaneous_power(self, activity_factor: float = 0.7) -> float:
        """Computes power draw in Watts given current DVFS state and activity factor."""
        dvfs = PROFILE_DVFS_MAP[self.current_profile]
        # P_dynamic = C * V^2 * f * alpha (with effective capacitance constant k=18.0)
        p_dynamic = 18.0 * (dvfs.voltage_v ** 2) * dvfs.frequency_ghz * activity_factor
        # Static leakage power (exponentially sensitive to temperature)
        temp_ratio = max(1.0, self.junction_temp_c / 25.0)
        p_leakage = 8.0 * dvfs.voltage_v * (temp_ratio ** 1.3)
        return p_dynamic + p_leakage

    def update_thermodynamics(self, dt: float = 0.1, activity_factor: float = 0.7) -> float:
        """
        Advances thermal physics by dt seconds and computes temperature changes.
        Returns the instantaneous power in Watts.
        """
        with self._lock:
            power = self._compute_instantaneous_power(activity_factor=activity_factor)
            # Energy spent in this interval (E = P * dt)
            interval_joules = power * dt
            self.total_joules += interval_joules

            # dT/dt = (Power_in - (T_junction - T_ambient) / R_th) / C_th
            heat_dissipated = (self.junction_temp_c - self.ambient_temp_c) / self.r_th
            dt_temp = (power - heat_dissipated) / self.c_th * dt
            self.junction_temp_c = max(self.ambient_temp_c, self.junction_temp_c + dt_temp)

            # Thermal Throttle Governor Check
            if self.junction_temp_c >= self.critical_temp_c:
                if not self.is_throttled:
                    self.is_throttled = True
                    self.throttle_count += 1
                self.current_profile = PowerProfile.CRITICAL_EMERGENCY
            elif self.is_throttled and self.junction_temp_c < (self.critical_temp_c - 10.0):
                # Hysteresis recovery
                self.is_throttled = False
                self.current_profile = PowerProfile.NOMINAL_BALANCED

            return power

    def execute_governed_workload(
        self,
        task_id: str,
        workload_duration_s: float = 0.5,
        activity_factor: float = 0.8,
    ) -> EnergyReceipt:
        """
        Simulates executing a compute workload while governing temperature and Joules.
        """
        with self._lock:
            dt = 0.05
            steps = max(1, int(workload_duration_s / dt))
            peak_temp = self.junction_temp_c
            joules_before = self.total_joules

            for _ in range(steps):
                self.update_thermodynamics(dt=dt, activity_factor=activity_factor)
                if self.junction_temp_c > peak_temp:
                    peak_temp = self.junction_temp_c

            joules_spent = self.total_joules - joules_before
            avg_power = joules_spent / max(1e-4, workload_duration_s)

            receipt = EnergyReceipt(
                receipt_id=f"receipt-joule-{len(self.task_receipts) + 1:04d}",
                task_id=task_id,
                joules_consumed=joules_spent,
                duration_s=workload_duration_s,
                average_power_w=avg_power,
                peak_temp_c=peak_temp,
                timestamp=time.time(),
            )
            self.task_receipts.append(receipt)
            return receipt

    def status(self) -> Dict[str, Any]:
        with self._lock:
            watt_hours = self.total_joules / 3600.0
            dvfs = PROFILE_DVFS_MAP[self.current_profile]
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "era_name": ERA_NAME,
                "current_profile": self.current_profile.value,
                "frequency_ghz": dvfs.frequency_ghz,
                "voltage_v": dvfs.voltage_v,
                "junction_temp_c": round(self.junction_temp_c, 2),
                "is_throttled": self.is_throttled,
                "throttle_count": self.throttle_count,
                "total_joules": round(self.total_joules, 2),
                "total_watt_hours": round(watt_hours, 6),
                "total_receipts": len(self.task_receipts),
            }

    def format_ascii_status(self) -> str:
        s = self.status()
        header = f"+-------------------------------------------------------------------------+\n|      STAGE {s['stage']}: {s['stage_name'].upper()[:52]:<52} |\n|      Era {s['era']}: {s['era_name'][:56]:<56} |\n+-------------------------------------------------------------------------+"
        body = (
            f"| Power Profile        : {s['current_profile']:<48} |\n"
            f"| Operating Frequency  : {s['frequency_ghz']:.2f} GHz{' ' * 40}|\n"
            f"| Core Voltage         : {s['voltage_v']:.2f} V{' ' * 42}|\n"
            f"| Junction Temperature : {s['junction_temp_c']:.2f} deg C{' ' * 36}|\n"
            f"| Thermal Throttled    : {str(s['is_throttled']):<48} |\n"
            f"| Throttle Events      : {s['throttle_count']:<48} |\n"
            f"| Cumulative Energy    : {s['total_joules']:.2f} Joules ({s['total_watt_hours']:.4f} Wh){' ' * (20 - len(str(s['total_joules'])))}|\n"
            f"| Recorded Receipts    : {s['total_receipts']:<48} |"
        )
        footer = "+-------------------------------------------------------------------------+"
        return f"{header}\n{body}\n{footer}"
