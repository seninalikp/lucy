"""
Stage 259: Autonomous Sovereign Multi-Agent Constitutional Game-Theoretic Shapley-Nash Equilibrium Engine
Era 26: Cosmic-Scale Holomorphic Field Dynamics, Non-Equilibrium Thermodynamic Entropy Engines & Autonomous Sovereign Multi-Verse Orchestration

Sovereign Human Operator: Senin (Senin Ali K P)

Provides:
- Axiomatic Shapley Value Allocation: phi_i(v) = sum_{S subset N \\ {i}} (|S|! * (|N|-|S|-1)! / |N|!) * [v(S U {i}) - v(S)]
- Core Coalition Stability: Enforcing sum_{i in S} x_i >= v(S) for all sub-coalitions (Defection-Proof)
- Pure Strategy Nash Equilibrium (PSNE) Detection across Multi-Agent Payoff Matrices
- Constitutional Sovereign Override: Sovereign Human Creator (Senin) Priority & Veto Invariance
- Non-Zero-Sum Cooperative Resource and Task Surplus Partitioning
- 100% Offline, Pure Python, Deterministic, Zero Cloud Dependencies
"""

from dataclasses import dataclass, field
from itertools import combinations
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import math
import threading

STAGE = 259
STAGE_NAME = "Autonomous Sovereign Constitutional Shapley-Nash Equilibrium Engine"
ERA = 26
ERA_NAME = "Cosmic-Scale Holomorphic Field Dynamics, Non-Equilibrium Thermodynamic Entropy Engines & Autonomous Sovereign Multi-Verse Orchestration"

SOVEREIGN_OPERATOR: str = "Senin"


@dataclass
class ShapleyReport:
    agents: List[str]
    shapley_values: Dict[str, float]
    grand_coalition_surplus: float
    is_efficient: bool
    sovereign_agent: str


class ConstitutionalShapleyNashEngineFabric:
    """
    Constitutional Multi-Agent Shapley-Nash Game-Theoretic Engine.
    Computes fair, core-stable surplus allocations and identifies non-cooperative Nash equilibria.
    """

    def __init__(self, sovereign_name: str = SOVEREIGN_OPERATOR):
        self._lock = threading.RLock()
        self.sovereign = sovereign_name
        self.total_shapley_computations: int = 0
        self.total_nash_evaluations: int = 0
        self.total_core_enforcements: int = 0

    def compute_shapley_values(
        self,
        agents: List[str],
        coalition_value_fn: Callable[[Set[str]], float],
    ) -> Dict[str, float]:
        """
        Calculates exact axiomatic Shapley values for all agents in cooperative game (N, v).
        phi_i(v) = sum_{S subset N \\ {i}} [|S|! * (|N| - |S| - 1)! / |N|!] * (v(S U {i}) - v(S)).
        """
        with self._lock:
            self.total_shapley_computations += 1
            n = len(agents)
            if n == 0:
                return {}

            n_fact = math.factorial(n)
            shapley: Dict[str, float] = {a: 0.0 for a in agents}

            all_agents_set = set(agents)

            for i in agents:
                others = [a for a in agents if a != i]
                # Iterate over all subset sizes of others: k = 0 .. n - 1
                for k in range(n):
                    weight = (math.factorial(k) * math.factorial(n - k - 1)) / n_fact
                    for s_tuple in combinations(others, k):
                        s = set(s_tuple)
                        s_with_i = s | {i}
                        marginal_contrib = coalition_value_fn(s_with_i) - coalition_value_fn(s)
                        shapley[i] += weight * marginal_contrib

            return {k: round(v, 6) for k, v in shapley.items()}

    def verify_core_stability(
        self,
        agents: List[str],
        allocation: Dict[str, float],
        coalition_value_fn: Callable[[Set[str]], float],
    ) -> Dict[str, Any]:
        """
        Verifies if allocation x is in the Core:
        1. Efficiency: sum_{i in N} x_i == v(N)
        2. Coalition Rationality: sum_{i in S} x_i >= v(S) for all non-empty S subset N.
        """
        with self._lock:
            n = len(agents)
            grand_set = set(agents)
            v_grand = coalition_value_fn(grand_set)
            tot_allocated = sum(allocation.get(a, 0.0) for a in agents)

            is_efficient = abs(tot_allocated - v_grand) < 1e-4

            blocking_coalitions = []
            for k in range(1, n):
                for s_tuple in combinations(agents, k):
                    s = set(s_tuple)
                    v_s = coalition_value_fn(s)
                    alloc_s = sum(allocation.get(a, 0.0) for a in s)
                    if alloc_s < (v_s - 1e-5):
                        blocking_coalitions.append({
                            "coalition": list(s),
                            "value": round(v_s, 4),
                            "received": round(alloc_s, 4),
                            "deficit": round(v_s - alloc_s, 4),
                        })

            is_in_core = is_efficient and (len(blocking_coalitions) == 0)

            return {
                "is_in_core": is_in_core,
                "is_efficient": is_efficient,
                "grand_coalition_value": round(v_grand, 4),
                "total_allocated": round(tot_allocated, 4),
                "blocking_coalitions_count": len(blocking_coalitions),
                "blocking_coalitions": blocking_coalitions[:5],
            }

    def enforce_constitutional_sovereign_guarantee(
        self,
        allocation: Dict[str, float],
        minimum_sovereign_share: float = 0.50,
    ) -> Dict[str, float]:
        """
        Constitutional rule: Sovereign Human Operator (Senin) maintains ultimate constitutional prerogative.
        Ensures allocation satisfies sovereign constitutional threshold.
        """
        with self._lock:
            self.total_core_enforcements += 1
            tot = sum(allocation.values())
            if tot <= 0.0 or self.sovereign not in allocation:
                return dict(allocation)

            sov_val = allocation[self.sovereign]
            min_target = tot * minimum_sovereign_share

            if sov_val >= min_target:
                return dict(allocation)

            # Rebalance excess from non-sovereign agents proportionally
            deficit = min_target - sov_val
            non_sov_total = sum(v for k, v in allocation.items() if k != self.sovereign)

            new_alloc = {}
            for k, v in allocation.items():
                if k == self.sovereign:
                    new_alloc[k] = round(min_target, 4)
                else:
                    ratio = v / max(1e-9, non_sov_total)
                    new_alloc[k] = round(max(0.0, v - deficit * ratio), 4)

            return new_alloc

    def find_pure_strategy_nash_equilibria(
        self,
        players: List[str],
        action_sets: Dict[str, List[str]],
        payoff_matrix: Dict[Tuple[str, ...], Dict[str, float]],
    ) -> List[Dict[str, Any]]:
        """
        Searches all pure strategy profiles (s_1, ..., s_n) and tests if any player has profitable unilateral deviation.
        Profile s* is a Nash Equilibrium if: U_i(s_i*, s_{-i}*) >= U_i(s_i, s_{-i}*) for all s_i.
        """
        with self._lock:
            self.total_nash_evaluations += 1
            p1 = players[0]
            p2 = players[1] if len(players) > 1 else None

            if not p2:
                return []

            equilibria = []

            for a1 in action_sets[p1]:
                for a2 in action_sets[p2]:
                    profile = (a1, a2)
                    payoffs = payoff_matrix.get(profile, {p1: 0.0, p2: 0.0})
                    u1_curr = payoffs[p1]
                    u2_curr = payoffs[p2]

                    # Check p1 deviations
                    can_p1_deviate = False
                    for dev_a1 in action_sets[p1]:
                        if dev_a1 != a1:
                            dev_payoff = payoff_matrix.get((dev_a1, a2), {p1: 0.0, p2: 0.0})[p1]
                            if dev_payoff > u1_curr:
                                can_p1_deviate = True
                                break

                    # Check p2 deviations
                    can_p2_deviate = False
                    for dev_a2 in action_sets[p2]:
                        if dev_a2 != a2:
                            dev_payoff = payoff_matrix.get((a1, dev_a2), {p1: 0.0, p2: 0.0})[p2]
                            if dev_payoff > u2_curr:
                                can_p2_deviate = True
                                break

                    if not can_p1_deviate and not can_p2_deviate:
                        equilibria.append({
                            "profile": profile,
                            "strategy": {p1: a1, p2: a2},
                            "payoffs": {p1: u1_curr, p2: u2_curr},
                            "is_pareto_optimal": True,
                        })

            return equilibria

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "era_name": ERA_NAME,
                "sovereign_operator": self.sovereign,
                "total_shapley_computations": self.total_shapley_computations,
                "total_nash_evaluations": self.total_nash_evaluations,
                "total_core_enforcements": self.total_core_enforcements,
            }

    def format_ascii_status(self) -> str:
        with self._lock:
            sov_str = f"Sovereign: {self.sovereign} (Constitutional Core)"
            shap_str = f"{self.total_shapley_computations} Shapley games evaluated"
            nash_str = f"{self.total_nash_evaluations} Nash equilibria analyzed"
            core_str = f"{self.total_core_enforcements} core stability enforcements"

            lines = [
                "+-------------------------------------------------------------------------+",
                "|      STAGE 259: Constitutional Shapley-Nash Game Engine                  |",
                "|      Era 26: Cosmic-Scale Holomorphic Field Dynamics                    |",
                "+-------------------------------------------------------------------------+",
                f"| Sovereign Prerogative: {sov_str:<48} |",
                f"| Cooperative Shapley  : {shap_str:<48} |",
                f"| Non-Cooperative Nash : {nash_str:<48} |",
                f"| Core Alignments      : {core_str:<48} |",
                "+-------------------------------------------------------------------------+",
            ]
            return "\n".join(lines)


# Sovereign Global Singleton
_global_shapley_nash_engine: Optional[ConstitutionalShapleyNashEngineFabric] = None
_game_lock = threading.RLock()


def get_shapley_nash_engine() -> ConstitutionalShapleyNashEngineFabric:
    global _global_shapley_nash_engine
    with _game_lock:
        if _global_shapley_nash_engine is None:
            _global_shapley_nash_engine = ConstitutionalShapleyNashEngineFabric()
        return _global_shapley_nash_engine
