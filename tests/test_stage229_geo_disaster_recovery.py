r"""
tests/test_stage229_geo_disaster_recovery.py
Stage 229 Unit Tests: Autonomous Planetary Geo-Distributed Disaster Recovery & State Relocator
"""

import threading
import unittest

from backend.lucy_core.geo_disaster_recovery import (
    GeoDisasterRecoveryFabric,
    GeoRegionNode,
    RegionHealth,
    STAGE,
    STAGE_NAME,
)


class TestStage229GeoDisasterRecovery(unittest.TestCase):
    def setUp(self):
        self.fabric = GeoDisasterRecoveryFabric()

    def test_01_initialization_and_metadata(self):
        s = self.fabric.status()
        self.assertEqual(s["stage"], 229)
        self.assertEqual(s["stage_name"], STAGE_NAME)
        self.assertEqual(s["total_regions"], 5)
        self.assertEqual(s["online_regions"], 5)
        self.assertTrue(s["has_quorum"])
        self.assertEqual(s["current_epoch"], 1)
        self.assertEqual(s["primary_region"], "EARTH_EU_FRANKFURT")

    def test_02_state_replication_across_quorum(self):
        seq = self.fabric.replicate_state({"mission_directive": "deep_space_survey"})
        self.assertEqual(seq, 1)
        for node in self.fabric.regions.values():
            self.assertEqual(node.state_payload["mission_directive"], "deep_space_survey")
            self.assertEqual(node.last_replicated_seq, 1)

    def test_03_autonomous_failover_on_primary_disaster(self):
        old_primary = self.fabric.primary_region_id
        # Kill primary
        self.fabric.trigger_disaster(old_primary, RegionHealth.OFFLINE_DISASTER)
        # Primary must have relocated to a healthy survivor!
        new_primary = self.fabric.primary_region_id
        self.assertNotEqual(new_primary, old_primary)
        self.assertTrue(self.fabric.regions[new_primary].is_primary)
        self.assertFalse(self.fabric.regions[old_primary].is_primary)
        self.assertEqual(self.fabric.current_epoch, 2)
        self.assertEqual(len(self.fabric.failover_history), 1)

    def test_04_zero_data_loss_preservation_after_failover(self):
        self.fabric.replicate_state({"quantum_key": "0xABCDEF123456"})
        old_primary = self.fabric.primary_region_id
        self.fabric.trigger_disaster(old_primary)
        new_primary = self.fabric.primary_region_id
        # Newly elected primary holds intact state
        self.assertEqual(
            self.fabric.regions[new_primary].state_payload["quantum_key"],
            "0xABCDEF123456",
        )

    def test_05_recovering_offline_region_and_catchup(self):
        # Kill one region
        self.fabric.trigger_disaster("EARTH_APAC_SINGAPORE")
        self.assertEqual(self.fabric.regions["EARTH_APAC_SINGAPORE"].health, RegionHealth.OFFLINE_DISASTER)

        # Mutate state on survivors
        self.fabric.replicate_state({"target_coordinate": [12.5, -45.2]})

        # Restore offline region
        self.fabric.restore_region("EARTH_APAC_SINGAPORE")
        self.assertEqual(self.fabric.regions["EARTH_APAC_SINGAPORE"].health, RegionHealth.ONLINE_HEALTHY)
        self.assertEqual(
            self.fabric.regions["EARTH_APAC_SINGAPORE"].state_payload["target_coordinate"],
            [12.5, -45.2],
        )

    def test_06_quorum_loss_prevention(self):
        # Kill 3 of 5 nodes -> remaining 2 is less than quorum (3)
        self.fabric.trigger_disaster("EARTH_APAC_SINGAPORE")
        self.fabric.trigger_disaster("LUNAR_GATEWAY_ORBIT")
        self.fabric.trigger_disaster("ORBITAL_STATION_ALPHA")
        s = self.fabric.status()
        self.assertFalse(s["has_quorum"])
        # Attempting replication without quorum must raise RuntimeError
        with self.assertRaises(RuntimeError):
            self.fabric.replicate_state({"illegal_write": True})

    def test_07_explicit_candidate_relocation(self):
        new_prim = self.fabric.relocate_primary(candidate_region_id="EARTH_US_VIRGINIA")
        self.assertEqual(new_prim, "EARTH_US_VIRGINIA")
        self.assertEqual(self.fabric.primary_region_id, "EARTH_US_VIRGINIA")

    def test_08_reject_unhealthy_candidate_relocation(self):
        self.fabric.trigger_disaster("LUNAR_GATEWAY_ORBIT")
        with self.assertRaises(ValueError):
            self.fabric.relocate_primary(candidate_region_id="LUNAR_GATEWAY_ORBIT")

    def test_09_cp1252_safe_ascii_table(self):
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 229", tbl)
        self.assertIn("PLANETARY GEO-DISTRIBUTED", tbl)
        tbl.encode("cp1252")
        self.assertTrue(tbl.startswith("+--"))

    def test_10_multithreaded_concurrency(self):
        def worker(wid: int):
            for i in range(4):
                try:
                    self.fabric.replicate_state({f"sync_{wid}_{i}": True})
                except RuntimeError:
                    pass
            _ = self.fabric.status()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertGreater(self.fabric.replication_seq, 0)


if __name__ == "__main__":
    unittest.main()
