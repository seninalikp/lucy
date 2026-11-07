r"""
tests/test_stage212_interplanetary_dtn_routing.py
Stage 212: Galactic Hyper-Mesh Cross-Ring Topology & Interplanetary Delay-Tolerant Routing (DTN)
Era 22: Autonomous Galactic Hyper-Mesh, Hardware-Accelerated Photonic Emulation & Trans-Universal Reasoning Fabrics
"""

import unittest
from backend.lucy_core.interplanetary_dtn_routing import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    ContactWindow,
    DTNBundle,
    InterplanetaryDTNRoutingFabric,
)


class TestStage212InterplanetaryDTNRouting(unittest.TestCase):
    """10 Unit Tests for Stage 212 Interplanetary DTN Routing Fabric."""

    def setUp(self):
        self.fabric = InterplanetaryDTNRoutingFabric(local_node_id="earth_base_0")

    def test_01_fabric_initialization(self):
        self.assertEqual(STAGE, 212)
        self.assertEqual(ERA, 22)
        self.assertEqual(self.fabric.local_node_id, "earth_base_0")
        self.assertGreaterEqual(len(self.fabric.nodes), 3)
        self.assertEqual(self.fabric.status()["stage"], 212)

    def test_02_register_node(self):
        self.fabric.register_node("orbital_relay_jupiter", location="Jupiter L1", ring_tier=3)
        self.assertIn("orbital_relay_jupiter", self.fabric.nodes)
        self.assertEqual(self.fabric.nodes["orbital_relay_jupiter"]["ring_tier"], 3)

    def test_03_schedule_contact(self):
        cw = self.fabric.schedule_contact("earth_base_0", "node_luna_gateway_1", start_time=100.0, end_time=200.0)
        self.assertTrue(cw.is_active(150.0))
        self.assertFalse(cw.is_active(50.0))
        self.assertFalse(cw.is_active(250.0))

    def test_04_create_bundle(self):
        b = self.fabric.create_bundle("node_luna_gateway_1", {"cmd": "PING_LUNAR_CORE"}, current_time=100.0)
        self.assertIsNotNone(b)
        self.assertEqual(b.source_node, "earth_base_0")
        self.assertEqual(b.destination_node, "node_luna_gateway_1")
        self.assertIn(b.bundle_id, self.fabric.buffers["earth_base_0"])

    def test_05_bundle_ttl_expiration(self):
        b = self.fabric.create_bundle("node_mars_deep_2", "DATA", ttl_seconds=300.0, current_time=1000.0)
        self.assertFalse(b.is_expired(1200.0))
        self.assertTrue(b.is_expired(1400.0))

    def test_06_route_step_single_hop_delivery(self):
        self.fabric.schedule_contact("earth_base_0", "node_luna_gateway_1", start_time=100.0, end_time=200.0)
        b = self.fabric.create_bundle("node_luna_gateway_1", {"msg": "MISSION_TELEMETRY"}, current_time=100.0)

        forwarded = self.fabric.route_step(current_time=150.0)
        self.assertIn(b.bundle_id, forwarded)

        # Verify delivered at target
        luna_bundle = self.fabric.buffers["node_luna_gateway_1"][b.bundle_id]
        self.assertTrue(luna_bundle.delivered)
        self.assertTrue(luna_bundle.custody_acknowledged)
        self.assertEqual(self.fabric.status()["bundles_delivered"], 1)

    def test_07_route_step_multi_hop_forwarding(self):
        # Earth -> Luna (T: 100-200), Luna -> Mars (T: 250-350)
        self.fabric.schedule_contact("earth_base_0", "node_luna_gateway_1", 100.0, 200.0)
        self.fabric.schedule_contact("node_luna_gateway_1", "node_mars_deep_2", 250.0, 350.0)

        b = self.fabric.create_bundle("node_mars_deep_2", {"mission": "AREO_DATA"}, current_time=50.0)

        # Hop 1: Earth -> Luna at T=150
        fwd1 = self.fabric.route_step(current_time=150.0)
        self.assertIn(b.bundle_id, fwd1)
        self.assertFalse(self.fabric.buffers["node_luna_gateway_1"][b.bundle_id].delivered)

        # Hop 2: Luna -> Mars at T=300
        fwd2 = self.fabric.route_step(current_time=300.0)
        self.assertIn(b.bundle_id, fwd2)

        # Reached Mars
        mars_bundle = self.fabric.buffers["node_mars_deep_2"][b.bundle_id]
        self.assertTrue(mars_bundle.delivered)
        self.assertEqual(mars_bundle.hop_history, ["earth_base_0", "node_luna_gateway_1", "node_mars_deep_2"])

    def test_08_custody_transfer_buffer_management(self):
        self.fabric.schedule_contact("earth_base_0", "node_luna_gateway_1", 10.0, 50.0)
        b = self.fabric.create_bundle("node_luna_gateway_1", "CARGO_MANIFEST", current_time=10.0)

        # Before route: present in Earth buffer
        self.assertIn(b.bundle_id, self.fabric.buffers["earth_base_0"])

        # Execute route step
        self.fabric.route_step(current_time=20.0)

        # After route: vacated from Earth buffer, present in Luna buffer
        self.assertNotIn(b.bundle_id, self.fabric.buffers["earth_base_0"])
        self.assertIn(b.bundle_id, self.fabric.buffers["node_luna_gateway_1"])

    def test_09_inactive_contact_window_no_forward(self):
        self.fabric.schedule_contact("earth_base_0", "node_luna_gateway_1", 1000.0, 2000.0)
        b = self.fabric.create_bundle("node_luna_gateway_1", "PACKET", current_time=100.0)

        # Query at T=500 (before contact window)
        fwd = self.fabric.route_step(current_time=500.0)
        self.assertEqual(len(fwd), 0)
        self.assertIn(b.bundle_id, self.fabric.buffers["earth_base_0"])

    def test_10_ascii_status_formatting(self):
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 212: GALACTIC HYPER-MESH INTERPLANETARY DTN ROUTER", tbl)
        self.assertIn("Interplanetary Nodes", tbl)
        self.assertIn("RFC 5050 / RFC 9171 Store-Carry-Forward DTN", tbl)


if __name__ == "__main__":
    unittest.main()
