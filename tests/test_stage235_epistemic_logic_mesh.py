"""
tests/test_stage235_epistemic_logic_mesh.py
Unit tests for Stage 235: Decentralized Multi-Agent Epistemic Logic & Dynamic Common Knowledge Mesh
Era 24: Trans-Dimensional Cognitive Resonance, Neuromorphic Spiking Fabrics & Autonomous Sovereign AGI Singularity
"""

import unittest
from backend.lucy_core.epistemic_logic_mesh import (
    STAGE,
    STAGE_NAME,
    ERA,
    EpistemicFormula,
    FormulaType,
    KripkeModel,
    EpistemicLogicMeshFabric
)


class TestStage235EpistemicLogicMesh(unittest.TestCase):

    def test_01_formula_construction_and_printing(self):
        """Test EpistemicFormula AST operators and stringification."""
        p = EpistemicFormula.atom("p")
        q = EpistemicFormula.atom("q")
        np = EpistemicFormula.neg(p)
        pandq = EpistemicFormula.conj(p, q)
        porq = EpistemicFormula.disj(p, q)
        pimpq = EpistemicFormula.impl(p, q)

        k_a = EpistemicFormula.knows("alice", p)
        e_g = EpistemicFormula.everyone(("alice", "bob"), p)
        c_g = EpistemicFormula.common(("alice", "bob"), p)
        d_g = EpistemicFormula.distributed(("alice", "bob"), p)

        self.assertEqual(p.to_string(), "p")
        self.assertEqual(np.to_string(), "~(p)")
        self.assertEqual(pandq.to_string(), "(p & q)")
        self.assertEqual(porq.to_string(), "(p | q)")
        self.assertEqual(pimpq.to_string(), "(p -> q)")
        self.assertEqual(k_a.to_string(), "K_alice(p)")
        self.assertEqual(e_g.to_string(), "E_{alice,bob}(p)")
        self.assertEqual(c_g.to_string(), "C_{alice,bob}(p)")
        self.assertEqual(d_g.to_string(), "D_{alice,bob}(p)")

    def test_02_kripke_frame_reflexive_and_symmetric_closure(self):
        """Test KripkeModel automatically maintains reflexive and transitive equivalence relations."""
        model = KripkeModel(agents=["agent_1"])
        model.add_world("w1", {"p": True})
        model.add_world("w2", {"p": False})
        model.add_world("w3", {"p": True})

        # By default, (w1, w1), (w2, w2), (w3, w3) are in relations
        rel = model.relations["agent_1"]
        self.assertIn(("w1", "w1"), rel)
        self.assertIn(("w2", "w2"), rel)

        # Set indistinguishable w1 ~ w2 and w2 ~ w3
        model.set_indistinguishable("agent_1", "w1", "w2")
        model.set_indistinguishable("agent_1", "w2", "w3")

        # Must have transitively closed: w1 ~ w3 and w3 ~ w1
        self.assertIn(("w1", "w3"), rel)
        self.assertIn(("w3", "w1"), rel)
        self.assertIn(("w2", "w1"), rel)

    def test_03_modal_s5_evaluation_single_agent(self):
        """Test single-agent knowledge evaluation under S5 accessibility."""
        model = KripkeModel(agents=["alice"])
        model.add_world("w_heads", {"coin_is_heads": True, "light_on": True})
        model.add_world("w_tails", {"coin_is_heads": False, "light_on": True})

        # Alice doesn't know if coin is heads (w_heads ~ w_tails)
        model.set_indistinguishable("alice", "w_heads", "w_tails")

        k_coin = EpistemicFormula.knows("alice", EpistemicFormula.atom("coin_is_heads"))
        k_light = EpistemicFormula.knows("alice", EpistemicFormula.atom("light_on"))

        # In w_heads: coin is heads, but Alice does NOT know it
        self.assertFalse(model.evaluate(k_coin, "w_heads"))
        # In w_heads: light is on in both w_heads and w_tails, so Alice KNOWS light is on
        self.assertTrue(model.evaluate(k_light, "w_heads"))

    def test_04_axiom_t_and_axiom_4_s5_properties(self):
        """Test S5 Axiom T (Knowledge Truth: K_i p -> p) and Axiom 4 (Positive Introspection: K_i p -> K_i K_i p)."""
        model = KripkeModel(agents=["bob"])
        model.add_world("w1", {"safe": True})
        model.add_world("w2", {"safe": True})

        p = EpistemicFormula.atom("safe")
        k_bob_p = EpistemicFormula.knows("bob", p)
        # Axiom T: K_bob(safe) -> safe
        axiom_t = EpistemicFormula.impl(k_bob_p, p)
        # Axiom 4: K_bob(safe) -> K_bob(K_bob(safe))
        k_k_bob_p = EpistemicFormula.knows("bob", k_bob_p)
        axiom_4 = EpistemicFormula.impl(k_bob_p, k_k_bob_p)

        self.assertTrue(model.is_valid(axiom_t))
        self.assertTrue(model.is_valid(axiom_4))

    def test_05_dynamic_epistemic_public_announcement(self):
        """Test Public Announcement Logic [phi!] filters invalid worlds."""
        model = KripkeModel(agents=["alice"])
        model.add_world("w1", {"val": True})
        model.add_world("w2", {"val": False})
        model.add_world("w3", {"val": True})
        model.set_indistinguishable("alice", "w1", "w2")

        self.assertEqual(len(model.worlds), 3)
        # Publicly announce val is True
        announcement = EpistemicFormula.atom("val")
        updated_model = model.public_announcement(announcement)

        self.assertEqual(len(updated_model.worlds), 2)
        self.assertIn("w1", updated_model.worlds)
        self.assertNotIn("w2", updated_model.worlds)
        self.assertIn("w3", updated_model.worlds)

    def test_06_everyone_knows_vs_common_knowledge(self):
        """Test distinction between E_G(p) and C_G(p)."""
        # Graph: w1 -alice- w2 -bob- w3
        # p is true in w1 and w2, false in w3
        model = KripkeModel(agents=["alice", "bob"])
        model.add_world("w1", {"p": True})
        model.add_world("w2", {"p": True})
        model.add_world("w3", {"p": False})

        model.set_indistinguishable("alice", "w1", "w2")
        model.set_indistinguishable("bob", "w2", "w3")

        p = EpistemicFormula.atom("p")
        eg_p = EpistemicFormula.everyone(("alice", "bob"), p)
        cg_p = EpistemicFormula.common(("alice", "bob"), p)

        # In w1:
        # Alice's reach: {w1, w2} -> in both, p is True -> Alice knows p!
        # Bob's reach from w1: {w1} (since w1 is not indistinguishable to w2 for Bob) -> Bob knows p!
        # Therefore, Everyone knows p in w1!
        self.assertTrue(model.evaluate(eg_p, "w1"))

        # However, w3 is reachable from w1 via (w1 ~_alice w2 ~_bob w3).
        # In w3, p is False. Therefore, p is NOT Common Knowledge in w1!
        self.assertFalse(model.evaluate(cg_p, "w1"))

    def test_07_distributed_knowledge_pooling(self):
        """Test Distributed Knowledge D_G(p) pooling private observations."""
        # 3 worlds: w1=(1,0), w2=(1,1), w3=(0,0)
        # Alice knows x, Bob knows y.
        model = KripkeModel(agents=["alice", "bob"])
        model.add_world("w1", {"x": True, "y": False, "secret": True})
        model.add_world("w2", {"x": True, "y": True, "secret": False})
        model.add_world("w3", {"x": False, "y": False, "secret": False})

        # Alice cannot distinguish worlds with same x
        model.set_indistinguishable("alice", "w1", "w2")  # both have x=True
        # Bob cannot distinguish worlds with same y
        model.set_indistinguishable("bob", "w1", "w3")    # both have y=False

        sec = EpistemicFormula.atom("secret")
        # In w1, Alice doesn't know secret (w2 has secret=False)
        self.assertFalse(model.evaluate(EpistemicFormula.knows("alice", sec), "w1"))
        # In w1, Bob doesn't know secret (w3 has secret=False)
        self.assertFalse(model.evaluate(EpistemicFormula.knows("bob", sec), "w1"))

        # But together, their intersection from w1 is {w1, w2} cap {w1, w3} = {w1}!
        # Therefore, Distributed Knowledge knows secret!
        dk_sec = EpistemicFormula.distributed(("alice", "bob"), sec)
        self.assertTrue(model.evaluate(dk_sec, "w1"))

    def test_08_muddy_children_puzzle_convergence(self):
        """Test full Muddy Children puzzle step-by-step convergence."""
        fabric = EpistemicLogicMeshFabric()
        # 3 children, child 1 and child 2 are muddy, child 3 is clean (target: "110")
        fabric.setup_muddy_children_scenario(n_children=3, n_muddy=2)
        self.assertEqual(len(fabric.model.worlds), 8)
        self.assertEqual(fabric.current_world, "110")

        # Step 1: Father announces at least one is muddy
        r1 = fabric.step_muddy_children_round()
        self.assertEqual(r1["round"], 1)
        # World "000" is eliminated -> 7 worlds remain
        self.assertEqual(r1["remaining_worlds"], 7)
        self.assertNotIn("000", fabric.model.worlds)

        # Neither child 1 nor child 2 knows yet (because each sees 1 muddy child, so they might be clean)
        self.assertFalse(fabric.query_agent_knowledge("child_1", "muddy_1"))
        self.assertFalse(fabric.query_agent_knowledge("child_2", "muddy_2"))

        # Step 2: Children announce they don't know
        r2 = fabric.step_muddy_children_round()
        self.assertEqual(r2["round"], 2)

        # Now, since both saw that the other didn't know on round 1, they deduce they are also muddy!
        # Now child 1 and child 2 MUST know they are muddy!
        self.assertTrue(fabric.query_agent_knowledge("child_1", "muddy_1"))
        self.assertTrue(fabric.query_agent_knowledge("child_2", "muddy_2"))
        # Child 3 also knows child 3 is NOT muddy
        self.assertFalse(fabric.query_agent_knowledge("child_3", "muddy_3"))

    def test_09_epistemic_dissonance_and_contradiction(self):
        """Test detection of epistemic dissonance when public announcements conflict."""
        fabric = EpistemicLogicMeshFabric()
        fabric.setup_muddy_children_scenario(n_children=2, n_muddy=1)

        # Force contradiction: announce p AND ~p
        contra = EpistemicFormula.conj(EpistemicFormula.atom("muddy_1"), EpistemicFormula.neg(EpistemicFormula.atom("muddy_1")))
        fabric.model = fabric.model.public_announcement(contra)

        self.assertTrue(fabric.detect_epistemic_dissonance())
        self.assertEqual(len(fabric.model.worlds), 0)

    def test_10_fabric_status_and_ascii_table(self):
        """Test EpistemicLogicMeshFabric status dictionary and ASCII formatted table."""
        fabric = EpistemicLogicMeshFabric()
        st = fabric.status()
        self.assertEqual(st["stage"], 235)
        self.assertEqual(st["era"], 24)
        self.assertIn("active_agents", st)

        tbl = fabric.format_ascii_status()
        self.assertIn("STAGE 235", tbl)
        self.assertIn("Active Agents", tbl)
        self.assertIn("Possible Worlds", tbl)
        self.assertTrue(tbl.startswith("+--"))
        self.assertTrue(tbl.endswith("--+"))


if __name__ == "__main__":
    unittest.main()
