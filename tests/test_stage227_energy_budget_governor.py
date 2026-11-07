r"""
tests/test_stage227_energy_budget_governor.py
Stage 227 Unit Tests: Autonomous Hardware Energy Budget Governor & Thermal-Joule Throttle Fabric
"""

import threading
import unittest

from backend.lucy_core.energy_budget_governor import (
    EnergyBudgetGovernorFabric,
    EnergyReceipt,
    PowerProfile,
    PROFILE_DVFS_MAP,
    STAGE,
    STAGE_NAME,
)


class TestStage227EnergyBudgetGovernor(unittest.TestCase):
    def setUp(self):
        self.fabric = EnergyBudgetGovernorFabric(
            ambient_temp_c=25.0,
            thermal_resistance_r_th=0.45,
            thermal_capacitance_c_th=50.0,
            critical_temp_c=80.0,
        )

    def test_01_initialization_and_metadata(self):
        s = self.fabric.status()
        self.assertEqual(s["stage"], 227)
        self.assertEqual(s["stage_name"], STAGE_NAME)
        self.assertEqual(s["current_profile"], "NOMINAL_BALANCED")
        self.assertEqual(s["junction_temp_c"], 25.0)
        self.assertFalse(s["is_throttled"])
        self.assertEqual(s["total_joules"], 0.0)

    def test_02_profile_switching(self):
        self.fabric.set_profile(PowerProfile.TURBO)
        s = self.fabric.status()
        self.assertEqual(s["current_profile"], "TURBO")
        self.assertEqual(s["frequency_ghz"], 4.5)
        self.assertEqual(s["voltage_v"], 1.35)

    def test_03_dvfs_power_scaling(self):
        self.fabric.set_profile(PowerProfile.CONSERVATIVE)
        p_cons = self.fabric._compute_instantaneous_power(activity_factor=0.8)
        self.fabric.set_profile(PowerProfile.TURBO)
        p_turbo = self.fabric._compute_instantaneous_power(activity_factor=0.8)
        # Turbo power draw must be significantly higher than Conservative
        self.assertGreater(p_turbo, p_cons * 2.0)

    def test_04_energy_accumulation_joules(self):
        p = self.fabric.update_thermodynamics(dt=1.0, activity_factor=0.5)
        self.assertAlmostEqual(self.fabric.total_joules, p * 1.0, places=2)
        self.assertGreater(self.fabric.total_joules, 0.0)

    def test_05_thermal_rise_under_load(self):
        initial_temp = self.fabric.junction_temp_c
        self.fabric.set_profile(PowerProfile.TURBO)
        # Advance heavy load for several seconds
        for _ in range(50):
            self.fabric.update_thermodynamics(dt=0.1, activity_factor=1.0)
        self.assertGreater(self.fabric.junction_temp_c, initial_temp)

    def test_06_autonomous_thermal_throttling(self):
        # Force temperature near critical limit
        self.fabric.junction_temp_c = 79.5
        self.fabric.set_profile(PowerProfile.TURBO)
        self.fabric.update_thermodynamics(dt=0.5, activity_factor=1.0)
        # Should breach critical_temp_c (80.0) and trigger emergency throttle
        self.assertTrue(self.fabric.is_throttled)
        self.assertEqual(self.fabric.current_profile, PowerProfile.CRITICAL_EMERGENCY)
        self.assertEqual(self.fabric.throttle_count, 1)

    def test_07_hysteresis_thermal_recovery(self):
        # Trigger throttle
        self.fabric.junction_temp_c = 85.0
        self.fabric.is_throttled = True
        self.fabric.current_profile = PowerProfile.CRITICAL_EMERGENCY

        # Cool junction temp down below hysteresis threshold (80.0 - 10.0 = 70.0)
        self.fabric.junction_temp_c = 68.0
        self.fabric.update_thermodynamics(dt=0.1, activity_factor=0.1)
        self.assertFalse(self.fabric.is_throttled)
        self.assertEqual(self.fabric.current_profile, PowerProfile.NOMINAL_BALANCED)

    def test_08_execute_governed_workload(self):
        receipt = self.fabric.execute_governed_workload("task-quantum-fft", workload_duration_s=0.2)
        self.assertIsInstance(receipt, EnergyReceipt)
        self.assertEqual(receipt.task_id, "task-quantum-fft")
        self.assertGreater(receipt.joules_consumed, 0.0)
        self.assertGreater(receipt.average_power_w, 0.0)
        self.assertEqual(len(self.fabric.task_receipts), 1)

    def test_09_cp1252_safe_ascii_table(self):
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 227", tbl)
        self.assertIn("HARDWARE ENERGY BUDGET", tbl)
        tbl.encode("cp1252")
        self.assertTrue(tbl.startswith("+--"))

    def test_10_multithreaded_concurrency(self):
        def worker(wid: int):
            for i in range(5):
                _ = self.fabric.execute_governed_workload(f"task-{wid}-{i}", workload_duration_s=0.05)
            _ = self.fabric.status()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(self.fabric.task_receipts), 20)


if __name__ == "__main__":
    unittest.main()
