"""
Unit Tests for Stage 259: Autonomous Sovereign Multi-Agent Constitutional Game-Theoretic Shapley-Nash Equilibrium Engine
Era 26: Cosmic-Scale Holomorphic Field Dynamics, Non-Equilibrium Thermodynamic Entropy Engines & Autonomous Sovereign Multi-Verse Orchestration

Sovereign Human Operator: Senin (Senin Ali K P)
"""

import unittest
from backend.lucy_core.constitutional_shapley_nash_engine import (
    ConstitutionalShapleyNashEngineFabric,
    get_shapley_nash_engine,
    SOVEREIGN_OPERATOR,
    STAGE,
    ERA,
)


class TestStage259ConstitutionalShapleyNashEngine(unittest.TestCase):

    def setUp(self):
        self.fabric = ConstitutionalShapleyNashEngineFabric(sovereign_name="Senin")

    def test_01_singleton_and_initialization(self):
        singleton = get_shapley_nash_engine()
        self.assertIsNotNone(singleton)
        self.assertEqual(STAGE, 259)
        self.assertEqual(ERA, 26)
        self.assertEqual(self.fabric.sovereign, "Senin")
        self.assertEqual(SOVEREIGN_OPERATOR, "Senin")

    def test_02_shapley_axiomatic_efficiency(self):
        # 3 players: v(A)=2, v(B)=3, v(C)=1, v(AB)=7, v(AC)=5, v(BC)=6, v(ABC)=12
        agents = ["A", "B", "C"]
        def v(s):
            vals = {
                frozenset(): 0.0,
                frozenset(["A"]): 2.0,
                frozenset(["B"]): 3.0,
                frozenset(["C"]): 1.0,
                frozenset(["A", "B"]): 7.0,
                frozenset(["A", "C"]): 5.0,
                frozenset(["B", "C"]): 6.0,
                frozenset(["A", "B", "C"]): 12.0,
            }
            return vals.get(frozenset(s), 0.0)

        shapley = self.fabric.compute_shapley_values(agents, v)
        # Axiom 1: Sum of phi_i must equal v(ABC) = 12.0
        tot = sum(shapley.values())
        self.assertAlmostEqual(tot, 12.0, places=4)

    def test_03_shapley_symmetry_axiom(self):
        # Players A and B are completely symmetric in value contributions
        agents = ["A", "B", "C"]
        def v_sym(s):
            fs = frozenset(s)
            if len(fs) == 0: return 0.0
            if fs == frozenset(["A"]) or fs == frozenset(["B"]): return 3.0
            if fs == frozenset(["C"]): return 1.0
            if fs == frozenset(["A", "C"]) or fs == frozenset(["B", "C"]): return 6.0
            if fs == frozenset(["A", "B"]): return 8.0
            if fs == frozenset(["A", "B", "C"]): return 12.0
            return 0.0

        shapley = self.fabric.compute_shapley_values(agents, v_sym)
        self.assertAlmostEqual(shapley["A"], shapley["B"], places=5)

    def test_04_shapley_null_player_axiom(self):
        # Player C contributes 0 marginal value to every coalition
        agents = ["A", "B", "C"]
        def v_dummy(s):
            sub = frozenset(s) - {"C"}
            if len(sub) == 0: return 0.0
            if sub == frozenset(["A"]): return 5.0
            if sub == frozenset(["B"]): return 5.0
            if sub == frozenset(["A", "B"]): return 10.0
            return 0.0

        shapley = self.fabric.compute_shapley_values(agents, v_dummy)
        self.assertAlmostEqual(shapley["C"], 0.0, places=5)
        self.assertAlmostEqual(shapley["A"], 5.0, places=5)
        self.assertAlmostEqual(shapley["B"], 5.0, places=5)

    def test_05_three_player_majority_game(self):
        # Majority game: any coalition of size >= 2 gets 1.0, singletons get 0.0
        agents = ["P1", "P2", "P3"]
        def v_maj(s):
            return 1.0 if len(s) >= 2 else 0.0

        shapley = self.fabric.compute_shapley_values(agents, v_maj)
        for a in agents:
            self.assertAlmostEqual(shapley[a], 1.0 / 3.0, places=4)

    def test_06_core_stability_verification(self):
        agents = ["A", "B"]
        def v(s):
            if len(s) == 2: return 10.0
            if "A" in s: return 4.0
            if "B" in s: return 3.0
            return 0.0

        # Allocation in Core: A=6, B=4 (sum=10, 6 >= 4, 4 >= 3)
        res_stable = self.fabric.verify_core_stability(agents, {"A": 6.0, "B": 4.0}, v)
        self.assertTrue(res_stable["is_in_core"])

        # Allocation not in Core: A=3, B=7 (A receives 3 < v(A)=4)
        res_unstable = self.fabric.verify_core_stability(agents, {"A": 3.0, "B": 7.0}, v)
        self.assertFalse(res_unstable["is_in_core"])

    def test_07_constitutional_sovereign_guarantee(self):
        # Allocation where sovereign player Senin received only 20%
        initial_alloc = {"Senin": 20.0, "Agent_Alpha": 50.0, "Agent_Beta": 30.0}
        guaranteed = self.fabric.enforce_constitutional_sovereign_guarantee(initial_alloc, minimum_sovereign_share=0.50)

        # Senin must receive at least 50% (50.0 out of 100.0)
        self.assertEqual(guaranteed["Senin"], 50.0)
        self.assertAlmostEqual(sum(guaranteed.values()), 100.0)
        self.assertLess(guaranteed["Agent_Alpha"], 50.0)

    def test_08_prisoners_dilemma_nash_equilibrium(self):
        # Prisoner's Dilemma
        players = ["P1", "P2"]
        actions = {"P1": ["Cooperate", "Defect"], "P2": ["Cooperate", "Defect"]}
        # (C, C): (3, 3); (C, D): (0, 5); (D, C): (5, 0); (D, D): (1, 1)
        payoffs = {
            ("Cooperate", "Cooperate"): {"P1": 3.0, "P2": 3.0},
            ("Cooperate", "Defect"): {"P1": 0.0, "P2": 5.0},
            ("Defect", "Cooperate"): {"P1": 5.0, "P2": 0.0},
            ("Defect", "Defect"): {"P1": 1.0, "P2": 1.0},
        }

        psne = self.fabric.find_pure_strategy_nash_equilibria(players, actions, payoffs)
        self.assertEqual(len(psne), 1)
        self.assertEqual(psne[0]["strategy"], {"P1": "Defect", "P2": "Defect"})
        self.assertEqual(psne[0]["payoffs"], {"P1": 1.0, "P2": 1.0})

    def test_09_coordination_game_multiple_nash_equilibria(self):
        # Stag Hunt coordination game: (Stag, Stag) and (Hare, Hare) are both Nash equilibria
        players = ["P1", "P2"]
        actions = {"P1": ["Stag", "Hare"], "P2": ["Stag", "Hare"]}
        payoffs = {
            ("Stag", "Stag"): {"P1": 5.0, "P2": 5.0},
            ("Stag", "Hare"): {"P1": 0.0, "P2": 3.0},
            ("Hare", "Stag"): {"P1": 3.0, "P2": 0.0},
            ("Hare", "Hare"): {"P1": 3.0, "P2": 3.0},
        }

        psne = self.fabric.find_pure_strategy_nash_equilibria(players, actions, payoffs)
        self.assertEqual(len(psne), 2)
        strategies = [e["strategy"] for e in psne]
        self.assertIn({"P1": "Stag", "P2": "Stag"}, strategies)
        self.assertIn({"P1": "Hare", "P2": "Hare"}, strategies)

    def test_10_ascii_status_and_metrics(self):
        self.fabric.compute_shapley_values(["A", "B"], lambda s: 10.0 if len(s) == 2 else 0.0)

        ascii_table = self.fabric.format_ascii_status()
        self.assertIn("STAGE 259: Constitutional Shapley-Nash Game Engine", ascii_table)
        self.assertIn("Sovereign: Senin", ascii_table)
        self.assertIn("Cooperative Shapley", ascii_table)

        # CP1252 verification
        ascii_table.encode("cp1252")

        metrics = self.fabric.get_metrics()
        self.assertEqual(metrics["stage"], 259)
        self.assertEqual(metrics["era"], 26)
        self.assertEqual(metrics["sovereign_operator"], "Senin")
        self.assertGreater(metrics["total_shapley_computations"], 0)


if __name__ == "__main__":
    unittest.main()
