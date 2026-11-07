"""
tests/test_stage236_temporal_chrono_governor.py
Unit tests for Stage 236: Autonomous Temporal Chrono-State Engine & Causality Inversion Governor
Era 24: Trans-Dimensional Cognitive Resonance, Neuromorphic Spiking Fabrics & Autonomous Sovereign AGI Singularity
"""

import unittest
from backend.lucy_core.temporal_chrono_governor import (
    STAGE,
    STAGE_NAME,
    ERA,
    ChronoEvent,
    TemporalChronoGovernorFabric
)


class TestStage236TemporalChronoGovernor(unittest.TestCase):

    def test_01_genesis_timeline_and_event_hash(self):
        """Test genesis root event initialization and SHA-256 invariant hash."""
        gov = TemporalChronoGovernorFabric()
        self.assertIn("prime", gov.timelines)
        self.assertEqual(len(gov.timelines["prime"]), 1)

        root_id = gov.timelines["prime"][0]
        root_evt = gov.events[root_id]
        self.assertEqual(root_evt.event_id, "evt_genesis_0000")
        self.assertEqual(root_evt.logical_tick, 0)
        self.assertEqual(root_evt.state_delta["sovereign_operator"], "Senin (Senin Ali K P)")
        self.assertEqual(len(root_evt.invariant_hash), 64)

    def test_02_commit_sequential_events_vector_clocks(self):
        """Test sequential event commits, vector clock progression, and parent linkage."""
        gov = TemporalChronoGovernorFabric()
        evt1 = gov.commit_event("prime", {"entropy": 0.1, "alpha": 42})
        evt2 = gov.commit_event("prime", {"entropy": 0.2, "beta": 99})

        self.assertEqual(evt1.logical_tick, 1)
        self.assertEqual(evt2.logical_tick, 2)
        self.assertEqual(evt1.vector_clock["prime"], 1)
        self.assertEqual(evt2.vector_clock["prime"], 2)

        self.assertIn(evt1.event_id, evt2.causal_parents)
        self.assertIn(evt2.event_id, evt1.causal_children)
        self.assertEqual(gov.timeline_states["prime"]["alpha"], 42)
        self.assertEqual(gov.timeline_states["prime"]["beta"], 99)

    def test_03_fork_timeline_branching(self):
        """Test branching off an existing timeline into an independent timeline."""
        gov = TemporalChronoGovernorFabric()
        e1 = gov.commit_event("prime", {"param": 100})
        gov.fork_timeline("prime", "timeline_experimental")

        self.assertIn("timeline_experimental", gov.timelines)
        self.assertEqual(gov.timeline_tips["timeline_experimental"], e1.event_id)
        self.assertEqual(gov.timeline_states["timeline_experimental"]["param"], 100)

        # Committing to experimental does not alter prime tip
        e_exp = gov.commit_event("timeline_experimental", {"param": 999})
        self.assertEqual(gov.timeline_states["timeline_experimental"]["param"], 999)
        self.assertEqual(gov.timeline_states["prime"]["param"], 100)
        self.assertNotEqual(gov.timeline_tips["prime"], gov.timeline_tips["timeline_experimental"])

    def test_04_forward_light_cone_reachability(self):
        """Test forward light cone captures all transitive descendants."""
        gov = TemporalChronoGovernorFabric()
        e1 = gov.commit_event("prime", {"k": 1})
        e2 = gov.commit_event("prime", {"k": 2})
        e3 = gov.commit_event("prime", {"k": 3})

        cone_e1 = gov.get_future_light_cone(e1.event_id)
        self.assertIn(e2.event_id, cone_e1)
        self.assertIn(e3.event_id, cone_e1)
        self.assertNotIn(e1.event_id, cone_e1)

        cone_e2 = gov.get_future_light_cone(e2.event_id)
        self.assertIn(e3.event_id, cone_e2)
        self.assertNotIn(e1.event_id, cone_e2)

    def test_05_localized_causality_inversion_rollback(self):
        """Test localized causality inversion rollbacks without touching parallel branches."""
        gov = TemporalChronoGovernorFabric()
        e1 = gov.commit_event("prime", {"step": 1})
        gov.fork_timeline("prime", "parallel_branch")

        e2 = gov.commit_event("prime", {"step": 2})
        e3 = gov.commit_event("prime", {"step": 3})
        e_par = gov.commit_event("parallel_branch", {"step": "parallel_ok"})

        # Invert causality on prime back to e1
        res = gov.invert_causality_and_rollback("prime", e1.event_id)
        self.assertEqual(res["status"], "CAUSALITY_INVERTED")
        self.assertEqual(res["pruned_events_count"], 2)
        self.assertEqual(gov.timeline_tips["prime"], e1.event_id)
        self.assertEqual(gov.timeline_states["prime"]["step"], 1)

        # Verify parallel branch was untouched
        self.assertEqual(gov.timeline_states["parallel_branch"]["step"], "parallel_ok")
        self.assertEqual(gov.inversions_count, 1)

    def test_06_immutable_horizon_paradox_prevention(self):
        """Test that attempts to rollback prior to immutable horizon trigger paradox prevention."""
        gov = TemporalChronoGovernorFabric()
        e1 = gov.commit_event("prime", {"x": 10}) # tick 1
        e2 = gov.commit_event("prime", {"x": 20}) # tick 2
        e3 = gov.commit_event("prime", {"x": 30}) # tick 3

        # Freeze history up to tick 2
        gov.freeze_immutable_horizon(2)
        self.assertEqual(gov.immutable_horizon_tick, 2)

        # Attempting rollback to tick 1 should be blocked
        with self.assertRaises(ValueError) as ctx:
            gov.invert_causality_and_rollback("prime", e1.event_id)

        self.assertIn("Paradox Prevention Triggered", str(ctx.exception))
        self.assertEqual(gov.paradoxes_prevented, 1)

    def test_07_counterfactual_intervention_re_simulation(self):
        """Test counterfactual intervention injects antecedent delta on new divergent timeline."""
        gov = TemporalChronoGovernorFabric()
        e1 = gov.commit_event("prime", {"temperature": 300, "pressure": 1.0})
        e2 = gov.commit_event("prime", {"temperature": 350, "pressure": 1.2})

        # Intervene at tick 1 with counterfactual temperature
        intervened_evt = gov.counterfactual_intervention(
            timeline_id="prime",
            intervention_tick=1,
            intervened_delta={"temperature": 500, "superheated": True},
            new_timeline_id="counterfactual_plasma"
        )

        self.assertIn("counterfactual_plasma", gov.timelines)
        self.assertEqual(gov.timeline_states["counterfactual_plasma"]["temperature"], 500)
        self.assertTrue(gov.timeline_states["counterfactual_plasma"]["superheated"])
        self.assertEqual(gov.timeline_states["prime"]["temperature"], 350)

    def test_08_lowest_common_ancestor_and_3way_reconciliation(self):
        """Test LCA computation and 3-way poset delta reconciliation."""
        gov = TemporalChronoGovernorFabric()
        e_base = gov.commit_event("prime", {"shared_val": "base"})
        gov.fork_timeline("prime", "feature_branch")

        # Prime adds key_a
        gov.commit_event("prime", {"key_a": "val_a"})
        # Feature adds key_b
        gov.commit_event("feature_branch", {"key_b": "val_b"})

        lca = gov.find_lowest_common_ancestor("prime", "feature_branch")
        self.assertEqual(lca, e_base.event_id)

        rec = gov.reconcile_timelines("prime", "feature_branch")
        self.assertIn("key_b", rec["merged_keys"])
        self.assertEqual(gov.timeline_states["prime"]["key_b"], "val_b")
        self.assertEqual(gov.timeline_states["prime"]["key_a"], "val_a")

    def test_09_closed_timelike_curve_cycle_detection(self):
        """Test Closed Timelike Curve (CTC) paradox cycle detection."""
        gov = TemporalChronoGovernorFabric()
        e1 = gov.commit_event("prime", {"a": 1})
        e2 = gov.commit_event("prime", {"a": 2})

        # No CTC initially
        self.assertFalse(gov.detect_closed_timelike_curves())

        # Artificially create a closed loop: e2 -> e1
        gov.events[e2.event_id].causal_children.append(e1.event_id)
        self.assertTrue(gov.detect_closed_timelike_curves())

    def test_10_fabric_status_and_ascii_table(self):
        """Test fabric status dictionary and CP1252-safe ASCII table."""
        gov = TemporalChronoGovernorFabric()
        st = gov.status()
        self.assertEqual(st["stage"], 236)
        self.assertEqual(st["era"], 24)
        self.assertIn("prime", st["active_timelines"])

        tbl = gov.format_ascii_status()
        self.assertIn("STAGE 236", tbl)
        self.assertIn("Active Timelines", tbl)
        self.assertIn("Immutable Horizon", tbl)
        self.assertTrue(tbl.startswith("+--"))
        self.assertTrue(tbl.endswith("--+"))


if __name__ == "__main__":
    unittest.main()
