r"""
tests/test_stage167_crdt_replicated_types.py
Stage 167 Test Suite: Conflict-Free Replicated Data Types (CRDTs) Synthesizer
Era 17: Distributed Consensus, Mesh Virtualization & High-Availability Primitives
"""

import unittest

from backend.lucy_core.crdt_replicated_types import (
    CREATOR,
    ERA,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    GSet,
    LWWRegister,
    ORSet,
    PNCounter,
    SovereignCRDTSynthesizer,
    TwoPhaseSet,
    get_crdt_synthesizer,
)


class TestStage167CRDTReplicatedTypes(unittest.TestCase):
    def setUp(self) -> None:
        self.synth = SovereignCRDTSynthesizer()

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 167)
        self.assertEqual(ERA, 17)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")
        self.assertEqual(
            STAGE_NAME,
            "Conflict-Free Replicated Data Types (CRDTs) Synthesizer",
        )

    def test_02_pn_counter_operations(self) -> None:
        c1 = PNCounter("node_1")
        c2 = PNCounter("node_2")

        c1.increment(10)
        c1.decrement(2)  # c1 = 8

        c2.increment(5)
        c2.decrement(1)  # c2 = 4

        c1.merge(c2)
        c2.merge(c1)

        self.assertEqual(c1.value, 12)
        self.assertEqual(c2.value, 12)

    def test_03_pn_counter_semilattice_laws(self) -> None:
        c1 = PNCounter("node_1")
        c2 = PNCounter("node_2")
        c1.increment(7)
        c2.increment(3)

        # Commutativity: merge(A, B) == merge(B, A)
        c_ab = PNCounter("c_ab")
        c_ab.merge(c1)
        c_ab.merge(c2)

        c_ba = PNCounter("c_ba")
        c_ba.merge(c2)
        c_ba.merge(c1)

        self.assertEqual(c_ab.value, c_ba.value)

        # Idempotency: merge(A, A) == A
        c_idem = PNCounter("c_idem")
        c_idem.merge(c1)
        c_idem.merge(c1)
        self.assertEqual(c_idem.value, c1.value)

    def test_04_gset_monotonicity(self) -> None:
        g1 = GSet()
        g2 = GSet()
        g1.add("x")
        g2.add("y")

        g1.merge(g2)
        self.assertIn("x", g1)
        self.assertIn("y", g1)

    def test_05_two_phase_set_tombstones(self) -> None:
        tp = TwoPhaseSet()
        tp.add("item_1")
        self.assertIn("item_1", tp.elements())

        tp.remove("item_1")
        self.assertNotIn("item_1", tp.elements())

        # Attempting to re-add in 2P-Set fails because remove tombstone persists
        tp.add("item_1")
        self.assertNotIn("item_1", tp.elements())

    def test_06_lww_register_convergence(self) -> None:
        r1 = LWWRegister("rep_a", "OLD_VAL")
        r1.timestamp = 100.0

        r2 = LWWRegister("rep_b", "NEW_VAL")
        r2.timestamp = 200.0

        r1.merge(r2)
        self.assertEqual(r1.value, "NEW_VAL")
        self.assertEqual(r1.timestamp, 200.0)

    def test_07_or_set_add_and_remove(self) -> None:
        ors = ORSet()
        ors.add("item_a")
        self.assertIn("item_a", ors.read())

        ors.remove("item_a")
        self.assertNotIn("item_a", ors.read())

    def test_08_or_set_readdition_add_wins(self) -> None:
        ors = ORSet()
        ors.add("task_1")
        self.assertIn("task_1", ors.read())

        # Remove
        ors.remove("task_1")
        self.assertNotIn("task_1", ors.read())

        # Re-add with new tag (Add-Wins)
        ors.add("task_1")
        self.assertIn("task_1", ors.read())

    def test_09_synthesizer_mesh_sync(self) -> None:
        # Mutate replicas independently
        self.synth.counters["rep_0"].increment(5)
        self.synth.counters["rep_1"].increment(3)
        self.synth.counters["rep_2"].decrement(1)

        self.synth.sets["rep_0"].add("shared_doc_1")
        self.synth.sets["rep_1"].add("shared_doc_2")

        import time
        self.synth.registers["rep_2"].set("LEADER_ELECTION_V2", timestamp=time.time() + 100.0)

        # Synchronize mesh
        self.synth.synchronize_mesh()

        # All replicas converged
        self.assertEqual(self.synth.counters["rep_0"].value, 7)
        self.assertEqual(self.synth.counters["rep_1"].value, 7)
        self.assertEqual(self.synth.counters["rep_2"].value, 7)

        expected_docs = {"shared_doc_1", "shared_doc_2"}
        self.assertEqual(self.synth.sets["rep_0"].read(), expected_docs)
        self.assertEqual(self.synth.sets["rep_1"].read(), expected_docs)

        self.assertEqual(self.synth.registers["rep_0"].value, "LEADER_ELECTION_V2")
        self.assertEqual(self.synth.registers["rep_1"].value, "LEADER_ELECTION_V2")

    def test_10_ascii_status_and_singleton(self) -> None:
        ascii_out = self.synth.format_ascii_status()
        self.assertIn("LUCY STAGE 167: CONFLICT-FREE REPLICATED DATA TYPES", ascii_out)
        self.assertIn("Senin", ascii_out)
        self.assertIn("Senin Ali K P", ascii_out)
        self.assertIn("Convergence", ascii_out)

        s1 = get_crdt_synthesizer()
        s2 = get_crdt_synthesizer()
        self.assertIs(s1, s2)


if __name__ == "__main__":
    unittest.main()
