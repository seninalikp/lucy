r"""
tests/test_stage164_vector_clock_causality.py
Stage 164 Test Suite: Vector Clock & Lamport Causality Ordering Fabric
Era 17: Distributed Consensus, Mesh Virtualization & High-Availability Primitives
"""

import unittest

from backend.lucy_core.vector_clock_causality import (
    CREATOR,
    ERA,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    CausalBroadcastFabric,
    CausalEvent,
    CausalNode,
    CausalRelation,
    VectorClock,
    get_causal_fabric,
)


class TestStage164VectorClockCausality(unittest.TestCase):
    def setUp(self) -> None:
        self.fabric = CausalBroadcastFabric()

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 164)
        self.assertEqual(ERA, 17)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")
        self.assertEqual(
            STAGE_NAME,
            "Vector Clock & Lamport Causality Ordering Fabric",
        )

    def test_02_vector_clock_tick(self) -> None:
        v = VectorClock()
        self.assertEqual(v.clocks.get("node_a", 0), 0)
        v.tick("node_a")
        self.assertEqual(v.clocks["node_a"], 1)
        v.tick("node_a")
        self.assertEqual(v.clocks["node_a"], 2)

    def test_03_vector_clock_update_merge(self) -> None:
        v1 = VectorClock({"node_a": 2, "node_b": 1})
        v2 = VectorClock({"node_a": 1, "node_b": 3, "node_c": 4})
        v1.update(v2)
        self.assertEqual(v1.clocks["node_a"], 2)
        self.assertEqual(v1.clocks["node_b"], 3)
        self.assertEqual(v1.clocks["node_c"], 4)

    def test_04_causal_relation_before_and_after(self) -> None:
        v1 = VectorClock({"node_a": 1, "node_b": 1})
        v2 = VectorClock({"node_a": 2, "node_b": 1})

        self.assertEqual(v1.compare(v2), CausalRelation.BEFORE)
        self.assertEqual(v2.compare(v1), CausalRelation.AFTER)

        # Equal
        v3 = VectorClock({"node_a": 1, "node_b": 1})
        self.assertEqual(v1.compare(v3), CausalRelation.EQUAL)

    def test_05_causal_relation_concurrent(self) -> None:
        # v1 has higher node_a, v2 has higher node_b -> concurrent (conflict)
        v1 = VectorClock({"node_a": 2, "node_b": 1})
        v2 = VectorClock({"node_a": 1, "node_b": 2})
        self.assertEqual(v1.compare(v2), CausalRelation.CONCURRENT)

    def test_06_causal_event_generation(self) -> None:
        node = CausalNode(node_id="alpha")
        evt = node.create_event("EVENT_INITIALIZE")
        self.assertEqual(evt.sender_id, "alpha")
        self.assertEqual(evt.vclock.clocks["alpha"], 1)
        self.assertEqual(len(node.delivered_events), 1)

    def test_07_causal_delivery_in_order(self) -> None:
        node_a = CausalNode(node_id="alpha")
        node_b = CausalNode(node_id="beta")

        evt1 = node_a.create_event("MSG_1")
        delivered = node_b.receive_event(evt1)
        self.assertTrue(delivered)
        self.assertEqual(node_b.vclock.clocks["alpha"], 1)
        self.assertEqual(len(node_b.delivered_events), 1)

    def test_08_causal_delivery_buffering(self) -> None:
        node_a = CausalNode(node_id="alpha")
        node_b = CausalNode(node_id="beta")

        evt1 = node_a.create_event("MSG_1")  # alpha: 1
        evt2 = node_a.create_event("MSG_2")  # alpha: 2

        # Delivering evt2 FIRST (out-of-order)
        delivered_2 = node_b.receive_event(evt2)
        self.assertFalse(delivered_2)
        self.assertEqual(len(node_b.pending_buffer), 1)
        self.assertEqual(len(node_b.delivered_events), 0)

        # Delivering predecessor evt1 unlocks both evt1 and evt2
        delivered_1 = node_b.receive_event(evt1)
        self.assertTrue(delivered_1)
        self.assertEqual(len(node_b.pending_buffer), 0)
        self.assertEqual(len(node_b.delivered_events), 2)
        self.assertEqual(node_b.delivered_events[0].payload, "MSG_1")
        self.assertEqual(node_b.delivered_events[1].payload, "MSG_2")

    def test_09_broadcast_fabric_conflict_detection(self) -> None:
        # Independent events on alpha and beta
        evt_a = self.fabric.broadcast("alpha", "STATE_A")
        evt_b = self.fabric.broadcast("beta", "STATE_B")

        v_conflict1 = VectorClock({"alpha": 1, "beta": 0})
        v_conflict2 = VectorClock({"alpha": 0, "beta": 1})
        is_conflict = self.fabric.detect_conflict(v_conflict1, v_conflict2)
        self.assertTrue(is_conflict)
        self.assertEqual(self.fabric.concurrent_conflicts_detected, 1)

    def test_10_ascii_status_and_singleton(self) -> None:
        ascii_out = self.fabric.format_ascii_status()
        self.assertIn("LUCY STAGE 164: VECTOR CLOCK & LAMPORT CAUSALITY", ascii_out)
        self.assertIn("Senin", ascii_out)
        self.assertIn("Senin Ali K P", ascii_out)
        self.assertIn("Active Nodes", ascii_out)

        f1 = get_causal_fabric()
        f2 = get_causal_fabric()
        self.assertIs(f1, f2)


if __name__ == "__main__":
    unittest.main()
