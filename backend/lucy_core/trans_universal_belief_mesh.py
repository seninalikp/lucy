r"""
backend/lucy_core/trans_universal_belief_mesh.py
Stage 218: Trans-Universal Multi-Agent Recursive Reasoning & Belief Propagation Mesh
Era 22: Autonomous Galactic Hyper-Mesh, Hardware-Accelerated Photonic Emulation & Trans-Universal Reasoning Fabrics

100% offline, sovereign factor-graph belief propagation and recursive probabilistic reasoning mesh:
1. Decentralized Factor Graph Topology:
   - Encapsulates joint probability distributions over discrete multi-agent hypotheses using factor potentials.
2. Loopy Belief Propagation (LBP) Engine:
   - Implements damped sum-product message passing across variable and factor nodes.
   - Computes exact or high-fidelity variational marginal posterior beliefs: b_i(x_i) \propto \prod_{a \in \partial i} \mu_{a \to i}(x_i).
3. Trans-Universal Evidence Synthesis:
   - Aggregates asynchronous probabilistic evidence from multi-planetary nodes to converge on cosmic truth states.
4. Thread-safe execution fabric and CP1252-safe ASCII table formatting.
"""

from __future__ import annotations

import collections
import copy
import math
import threading
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union

STAGE: int = 218
STAGE_NAME: str = "Trans-Universal Multi-Agent Recursive Reasoning & Belief Propagation Mesh"
ERA: int = 22
ERA_NAME: str = "Autonomous Galactic Hyper-Mesh, Hardware-Accelerated Photonic Emulation & Trans-Universal Reasoning Fabrics"


@dataclass
class VariableNode:
    var_id: str
    cardinality: int = 2  # Default binary {0, 1}
    prior: List[float] = field(default_factory=list)

    def __post_init__(self):
        if not self.prior:
            self.prior = [1.0 / float(self.cardinality)] * self.cardinality


@dataclass
class FactorNode:
    factor_id: str
    variables: List[str]
    # potential: mapping from assignment tuple (e.g. (0, 1)) to potential float >= 0.0
    potential_table: Dict[Tuple[int, ...], float]


class TransUniversalBeliefMeshFabric:
    """
    Sovereign Belief Propagation Reasoning Fabric:
    Performs sum-product message passing over multi-agent factor graphs.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.variables: Dict[str, VariableNode] = {}
        self.factors: Dict[str, FactorNode] = {}

        # Messages: (from_id, to_id) -> List[float]
        self.messages: Dict[Tuple[str, str], List[float]] = {}
        self.inference_runs: int = 0
        self.message_ticks: int = 0

    def add_variable(self, var_id: str, cardinality: int = 2, prior: Optional[List[float]] = None) -> VariableNode:
        """Adds a discrete random variable node."""
        with self._lock:
            card = max(2, cardinality)
            pr = list(prior) if prior else [1.0 / float(card)] * card
            var = VariableNode(var_id=var_id, cardinality=card, prior=pr)
            self.variables[var_id] = var
            return var

    def add_factor(
        self, factor_id: str, variables: List[str], potential_table: Dict[Tuple[int, ...], float]
    ) -> FactorNode:
        """Adds a multi-variable factor constraint / potential."""
        with self._lock:
            factor = FactorNode(factor_id=factor_id, variables=list(variables), potential_table=dict(potential_table))
            self.factors[factor_id] = factor

            # Initialize messages between connected variables and factor
            for v in variables:
                card = self.variables[v].cardinality
                # Variable -> Factor message
                self.messages[(v, factor_id)] = [1.0 / float(card)] * card
                # Factor -> Variable message
                self.messages[(factor_id, v)] = [1.0 / float(card)] * card

            return factor

    def step_belief_propagation(self, damping: float = 0.5) -> float:
        """
        Executes one sum-product message passing round.
        Returns maximum message delta (convergence metric).
        """
        with self._lock:
            self.message_ticks += 1
            max_delta = 0.0
            new_messages: Dict[Tuple[str, str], List[float]] = {}

            # 1. Variable -> Factor messages
            for v_id, var in self.variables.items():
                connected_factors = [f_id for f_id, f in self.factors.items() if v_id in f.variables]
                for target_f in connected_factors:
                    msg = list(var.prior)
                    for other_f in connected_factors:
                        if other_f != target_f:
                            incoming = self.messages.get((other_f, v_id), [1.0] * var.cardinality)
                            for state in range(var.cardinality):
                                msg[state] *= incoming[state]

                    # Normalize
                    s = sum(msg)
                    if s > 0:
                        msg = [m / s for m in msg]

                    # Damping
                    old_msg = self.messages.get((v_id, target_f), msg)
                    damped_msg = [damping * old + (1.0 - damping) * n for old, n in zip(old_msg, msg)]
                    s_d = sum(damped_msg)
                    if s_d > 0:
                        damped_msg = [m / s_d for m in damped_msg]

                    delta = max(abs(a - b) for a, b in zip(old_msg, damped_msg))
                    max_delta = max(max_delta, delta)
                    new_messages[(v_id, target_f)] = damped_msg

            # 2. Factor -> Variable messages
            for f_id, factor in self.factors.items():
                vars_in_factor = factor.variables
                for target_v in vars_in_factor:
                    target_idx = vars_in_factor.index(target_v)
                    target_card = self.variables[target_v].cardinality
                    msg = [0.0] * target_card

                    # Iterate over factor potential table assignments
                    for assignment, pot in factor.potential_table.items():
                        if len(assignment) != len(vars_in_factor):
                            continue
                        target_val = assignment[target_idx]

                        # Multiply by incoming messages from other variables
                        prod = pot
                        for idx, other_v in enumerate(vars_in_factor):
                            if idx != target_idx:
                                val = assignment[idx]
                                in_msg = self.messages.get((other_v, f_id), [1.0] * self.variables[other_v].cardinality)
                                prod *= in_msg[val]

                        msg[target_val] += prod

                    # Normalize
                    s = sum(msg)
                    if s > 0:
                        msg = [m / s for m in msg]

                    old_msg = self.messages.get((f_id, target_v), msg)
                    damped_msg = [damping * old + (1.0 - damping) * n for old, n in zip(old_msg, msg)]
                    s_d = sum(damped_msg)
                    if s_d > 0:
                        damped_msg = [m / s_d for m in damped_msg]

                    delta = max(abs(a - b) for a, b in zip(old_msg, damped_msg))
                    max_delta = max(max_delta, delta)
                    new_messages[(f_id, target_v)] = damped_msg

            self.messages.update(new_messages)
            return max_delta

    def run_inference(self, max_iterations: int = 15, tolerance: float = 1e-4) -> Dict[str, List[float]]:
        """Runs iterative belief propagation until convergence or max_iterations."""
        with self._lock:
            self.inference_runs += 1
            for _ in range(max_iterations):
                delta = self.step_belief_propagation()
                if delta < tolerance:
                    break

            # Compute posterior marginals for each variable
            beliefs: Dict[str, List[float]] = {}
            for v_id, var in self.variables.items():
                b = list(var.prior)
                connected_factors = [f_id for f_id, f in self.factors.items() if v_id in f.variables]
                for f_id in connected_factors:
                    incoming = self.messages.get((f_id, v_id), [1.0] * var.cardinality)
                    for state in range(var.cardinality):
                        b[state] *= incoming[state]

                s = sum(b)
                if s > 0:
                    b = [round(val / s, 6) for val in b]
                beliefs[v_id] = b

            return beliefs

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "variable_count": len(self.variables),
                "factor_count": len(self.factors),
                "total_messages": len(self.messages),
                "inference_runs": self.inference_runs,
                "message_ticks": self.message_ticks,
            }

    def format_ascii_status(self) -> str:
        s = self.status()
        header = (
            "+-------------------------------------------------------------------------+\n"
            "|      STAGE 218: TRANS-UNIVERSAL RECURSIVE BELIEF PROPAGATION MESH       |\n"
            "+-------------------------------------------------------------------------+\n"
        )
        body = (
            f"| Variable Nodes (State): {s['variable_count']} Discrete Random Variables{' ':<21} |\n"
            f"| Factor Constraints    : {s['factor_count']} Multi-Agent Evidence Potentials{' ':<17} |\n"
            f"| Message Channels      : {s['total_messages']} Directed Sum-Product Edge Channels{' ':<12} |\n"
            f"| Inferences Executed   : {s['inference_runs']} Convergence Sweeps Completed{' ':<16} |\n"
            f"| Reasoning Paradigm    : Loopy Damped Sum-Product Belief Propagation     |\n"
            "+-------------------------------------------------------------------------+\n"
        )
        return header + body
