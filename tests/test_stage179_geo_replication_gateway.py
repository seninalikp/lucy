r"""
tests/test_stage179_geo_replication_gateway.py
Stage 179 Test Suite: Geo-Replication Replication Fabric & Multi-Region Gateway
Era 18: Autonomous Distributed Storage, Geo-Replication & Sharding Primitives
"""

import time
import unittest

from backend.lucy_core.geo_replication_gateway import (
    ConflictPolicy,
    ERA,
    ERA_NAME,
    GeoRecord,
    GeoReplicationFabric,
    GeoSyncPacket,
    RegionalGateway,
    STAGE,
    STAGE_NAME,
    get_geo_replication_fabric,
)


class TestStage179GeoReplicationGateway(unittest.TestCase):
    def setUp(self) -> None:
        self.fabric = GeoReplicationFabric(conflict_policy=ConflictPolicy.LWW)

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 179)
        self.assertEqual(ERA, 18)
        self.assertEqual(
            STAGE_NAME,
            "Geo-Replication Replication Fabric & Multi-Region Gateway",
        )
        self.assertEqual(
            ERA_NAME,
            "Autonomous Distributed Storage, Geo-Replication & Sharding Primitives",
        )
        self.assertEqual(self.fabric.primary_region, "us-east")

    def test_02_regional_gateways_initialization(self) -> None:
        self.assertEqual(len(self.fabric.regions), 3)
        self.assertIn("us-east", self.fabric.regions)
        self.assertIn("eu-central", self.fabric.regions)
        self.assertIn("ap-south", self.fabric.regions)

        self.assertTrue(self.fabric.regions["us-east"].is_active_primary)
        self.assertFalse(self.fabric.regions["eu-central"].is_active_primary)

    def test_03_local_region_write_and_queue(self) -> None:
        rec = self.fabric.write_regional("us-east", "session_user", {"token": "ABC"})
        self.assertEqual(rec.origin_region, "us-east")

        # Immediately available locally in us-east
        self.assertEqual(self.fabric.read_regional("us-east", "session_user"), {"token": "ABC"})
        # Not yet synced to eu-central
        self.assertIsNone(self.fabric.read_regional("eu-central", "session_user"))

        # Outbound queues in us-east should have 1 item for eu-central and ap-south
        gw_us = self.fabric.regions["us-east"]
        self.assertEqual(len(gw_us.outbound_queues["eu-central"]), 1)
        self.assertEqual(len(gw_us.outbound_queues["ap-south"]), 1)

    def test_04_pairwise_asynchronous_sync(self) -> None:
        self.fabric.write_regional("us-east", "config:flag", "ENABLED")
        pkt = self.fabric.sync_region_pair("us-east", "eu-central")

        self.assertEqual(len(pkt.records), 1)
        # Now eu-central has the record
        self.assertEqual(self.fabric.read_regional("eu-central", "config:flag"), "ENABLED")
        # us-east queue for eu-central is drained
        self.assertEqual(len(self.fabric.regions["us-east"].outbound_queues["eu-central"]), 0)

    def test_05_cluster_wide_all_regions_sync(self) -> None:
        self.fabric.write_regional("us-east", "data_us", "val_us")
        self.fabric.write_regional("eu-central", "data_eu", "val_eu")

        total = self.fabric.sync_all_regions()
        self.assertGreaterEqual(total, 2)

        # Both records now exist in all 3 regions
        for rname in ["us-east", "eu-central", "ap-south"]:
            self.assertEqual(self.fabric.read_regional(rname, "data_us"), "val_us")
            self.assertEqual(self.fabric.read_regional(rname, "data_eu"), "val_eu")

    def test_06_lww_conflict_resolution(self) -> None:
        # Step 1: Write initial value in us-east
        self.fabric.write_regional("us-east", "active_theme", "light_theme")
        self.fabric.sync_all_regions()

        # Step 2: Concurrent updates in us-east and eu-central
        # Write newer update in eu-central
        time.sleep(0.005)
        self.fabric.write_regional("eu-central", "active_theme", "dark_matrix")

        # Sync from eu-central to us-east
        self.fabric.sync_region_pair("eu-central", "us-east")

        # LWW: us-east must be updated to dark_matrix because eu-central had newer timestamp
        self.assertEqual(self.fabric.read_regional("us-east", "active_theme"), "dark_matrix")

    def test_07_disaster_recovery_failover(self) -> None:
        self.assertEqual(self.fabric.primary_region, "us-east")

        # Simulate us-east datacenter outage -> Failover to eu-central
        ok = self.fabric.trigger_failover("us-east", "eu-central")
        self.assertTrue(ok)
        self.assertEqual(self.fabric.primary_region, "eu-central")
        self.assertFalse(self.fabric.regions["us-east"].is_healthy)
        self.assertTrue(self.fabric.regions["eu-central"].is_active_primary)

    def test_08_unhealthy_region_write_block(self) -> None:
        self.fabric.trigger_failover("us-east", "eu-central")
        with self.assertRaises(RuntimeError):
            self.fabric.write_regional("us-east", "test_key", "fail")

    def test_09_ascii_formatting_and_status(self) -> None:
        self.fabric.write_regional("us-east", "stat_key", "stat_val")
        st = self.fabric.status()
        self.assertEqual(st["stage"], 179)
        self.assertEqual(st["total_regions"], 3)

        tbl = self.fabric.format_ascii_status()
        self.assertIn("LUCY STAGE 179: GEO-REPLICATION REPLICATION FABRIC & MULTI-REGION GATEWAY", tbl)
        self.assertIn("us-east", tbl)
        self.assertIn("eu-central", tbl)

    def test_10_singleton_accessor(self) -> None:
        g1 = get_geo_replication_fabric()
        g2 = get_geo_replication_fabric()
        self.assertIs(g1, g2)


if __name__ == "__main__":
    unittest.main()
