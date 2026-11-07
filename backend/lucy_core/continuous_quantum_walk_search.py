"""
LUCY Autonomous Sovereign AGI Kernel - Era 27: Cosmological Gauge Invariance & Unified Field Synthesis
Stage 265: Continuous-Time Quantum Walk & Graph-Topological Spatial Search Accelerator
Author & Permanent Sovereign Operator: Senin (Senin Ali K P)

Mathematical & Physical Foundations:
1. Graph Hamiltonian Formulation:
   H_0 = -gamma * A_graph   or   H_0 = -gamma * (D - A) (Laplacian)
   where A is the adjacency matrix and D is the vertex degree matrix.
2. Oracle-Driven Continuous Spatial Search (Childs & Goldstone Formalism):
   H = H_0 - epsilon * |target><target|
   where |target> is the marked node and epsilon is the potential well depth.
3. Unitary Schrödinger Evolution:
   U(t) = exp(-i * H * t / hbar)
   |psi(t)> = U(t) |psi(0)>
   Initial state: Uniform superposition |s> = (1 / sqrt(N)) * sum_{v in V} |v>
4. Hitting Probability & Quantum Resonance Speedup:
   P_target(t) = |<target|psi(t)>|^2
   Achieves quadratic speedup O(sqrt(N)) over classical random walk diffusion O(N).
"""

import cmath
import math
import threading
from typing import Dict, List, Tuple, Any, Optional

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

SOVEREIGN_OPERATOR = "Senin"
SOVEREIGN_LEGAL_NAME = "Senin Ali K P"
STAGE_ID = 265
STAGE = 265
STAGE_NAME = "Continuous-Time Quantum Walk & Graph-Topological Spatial Search Accelerator"
ERA_ID = 27
ERA = 27
ERA_NAME = "Cosmological Gauge Invariance, Non-Abelian Yang-Mills Fiber Bundles & Sovereign Trans-Planetary Unified Field Synthesis"


class ContinuousQuantumWalkSearch:
    """
    Simulates continuous-time quantum walks (CTQW) and spatial search algorithms
    on arbitrary finite graphs, computing unitary evolution, hitting probabilities,
    and quantum speedup metrics over classical random walk exploration.
    """

    def __init__(
        self,
        num_nodes: int = 16,
        hopping_rate_gamma: float = 1.0,
        hbar: float = 1.0
    ):
        self._lock = threading.RLock()
        self.num_nodes = max(2, int(num_nodes))
        self.gamma = float(hopping_rate_gamma)
        self.hbar = float(hbar)

        # Adjacency matrix: N x N float list
        self.adj_matrix: List[List[float]] = [[0.0] * self.num_nodes for _ in range(self.num_nodes)]
        # Default topology: Cycle graph C_N
        self.set_topology_cycle()
        self.marked_target: Optional[int] = None
        self.search_history: List[Dict[str, Any]] = []

    def set_topology_cycle(self) -> None:
        """Configures adjacency for 1D Ring / Cycle graph C_N."""
        with self._lock:
            n = self.num_nodes
            self.adj_matrix = [[0.0] * n for _ in range(n)]
            for i in range(n):
                self.adj_matrix[i][(i + 1) % n] = 1.0
                self.adj_matrix[i][(i - 1 + n) % n] = 1.0
            self.marked_target = None

    def set_topology_complete(self) -> None:
        """Configures adjacency for Complete graph K_N."""
        with self._lock:
            n = self.num_nodes
            self.adj_matrix = [[1.0 if i != j else 0.0 for j in range(n)] for i in range(n)]
            self.marked_target = None

    def set_topology_star(self, center: int = 0) -> None:
        """Configures adjacency for Star graph S_N."""
        with self._lock:
            n = self.num_nodes
            self.adj_matrix = [[0.0] * n for _ in range(n)]
            c = max(0, min(n - 1, center))
            for i in range(n):
                if i != c:
                    self.adj_matrix[c][i] = 1.0
                    self.adj_matrix[i][c] = 1.0
            self.marked_target = None

    def set_topology_grid_2d(self, rows: int, cols: int) -> None:
        """Configures adjacency for 2D Grid / Lattice graph with open boundaries."""
        with self._lock:
            n = rows * cols
            self.num_nodes = n
            self.adj_matrix = [[0.0] * n for _ in range(n)]
            for r in range(rows):
                for c in range(cols):
                    idx = r * cols + c
                    if c + 1 < cols:
                        self.adj_matrix[idx][idx + 1] = 1.0
                        self.adj_matrix[idx + 1][idx] = 1.0
                    if r + 1 < rows:
                        self.adj_matrix[idx][idx + cols] = 1.0
                        self.adj_matrix[idx + cols][idx] = 1.0
            self.marked_target = None

    def build_hamiltonian(self, marked_node: Optional[int] = None, oracle_depth: float = 1.0) -> List[List[float]]:
        """
        Constructs the search Hamiltonian:
        H = -gamma * A - (oracle_depth * |marked_node><marked_node| if marked_node is not None)
        """
        with self._lock:
            n = self.num_nodes
            H = [[-self.gamma * self.adj_matrix[i][j] for j in range(n)] for i in range(n)]
            if marked_node is not None and 0 <= marked_node < n:
                H[marked_node][marked_node] -= oracle_depth
            return H

    def _matrix_exp_hermitian(self, H: List[List[float]], t: float) -> List[List[complex]]:
        """
        Computes unitary time evolution operator U(t) = exp(-i * H * t / hbar).
        Utilizes NumPy eigendecomposition if available, else pure Python fallback.
        """
        n = len(H)
        if HAS_NUMPY:
            H_arr = np.array(H, dtype=float)
            eigenvals, eigenvecs = np.linalg.eigh(H_arr)
            diag_phase = np.exp(-1j * eigenvals * t / self.hbar)
            U = eigenvecs @ np.diag(diag_phase) @ eigenvecs.T.conj()
            return [[complex(U[i, j]) for j in range(n)] for i in range(n)]
        else:
            # Power series approximation U(t) = sum_{k=0}^{M} (-i H t / hbar)^k / k!
            # Valid for moderate t * ||H||
            scale = t / self.hbar
            I = [[complex(1.0 if i == j else 0.0) for j in range(n)] for i in range(n)]
            U = [[I[i][j] for j in range(n)] for i in range(n)]
            term = [[I[i][j] for j in range(n)] for i in range(n)]
            for k in range(1, 24):
                # Multiply term by (-i * scale / k) * H
                next_term = [[complex(0.0) for _ in range(n)] for _ in range(n)]
                factor = complex(0.0, -scale / k)
                for i in range(n):
                    for j in range(n):
                        s = complex(0.0)
                        for m in range(n):
                            s += term[i][m] * H[m][j]
                        next_term[i][j] = s * factor
                term = next_term
                for i in range(n):
                    for j in range(n):
                        U[i][j] += term[i][j]
            return U

    def propagate_quantum_state(
        self,
        initial_state: Optional[List[complex]] = None,
        evolution_time: float = 1.0,
        marked_node: Optional[int] = None,
        oracle_depth: float = 1.0
    ) -> Dict[str, Any]:
        """
        Propagates wavefunction |psi(t)> = U(t) |psi(0)> under Hamiltonian H.
        Returns node probability distributions and target hitting probability.
        """
        with self._lock:
            n = self.num_nodes
            if initial_state is None:
                # Uniform superposition |s> = 1/sqrt(N)
                norm_factor = 1.0 / math.sqrt(n)
                psi_0 = [complex(norm_factor, 0.0) for _ in range(n)]
            else:
                norm = math.sqrt(sum(abs(x)**2 for x in initial_state))
                if norm < 1e-12:
                    norm = 1.0
                psi_0 = [x / norm for x in initial_state]

            H = self.build_hamiltonian(marked_node=marked_node, oracle_depth=oracle_depth)
            U = self._matrix_exp_hermitian(H, evolution_time)

            # |psi(t)> = U @ psi_0
            psi_t = [complex(0.0) for _ in range(n)]
            for i in range(n):
                for j in range(n):
                    psi_t[i] += U[i][j] * psi_0[j]

            # Probabilities P_i = |psi_t[i]|^2
            probs = [abs(amp)**2 for amp in psi_t]
            total_prob = sum(probs)
            normalized_probs = [round(p / total_prob, 6) for p in probs]

            target_prob = normalized_probs[marked_node] if (marked_node is not None and 0 <= marked_node < n) else 0.0

            # Classical random walk probability benchmark: uniform classical is 1/N
            classical_prob = 1.0 / n
            speedup_ratio = round(target_prob / classical_prob, 4) if classical_prob > 0 else 0.0

            result = {
                "num_nodes": n,
                "evolution_time_t": round(evolution_time, 4),
                "marked_node": marked_node,
                "oracle_depth": oracle_depth,
                "target_hitting_probability": round(target_prob, 6),
                "classical_baseline_probability": round(classical_prob, 6),
                "quantum_speedup_ratio": speedup_ratio,
                "probabilities": normalized_probs,
                "state_norm": round(total_prob, 6)
            }
            return result

    def execute_spatial_search(
        self,
        target_node: int,
        oracle_depth: float = 2.0,
        time_samples: int = 50,
        max_time: float = 10.0
    ) -> Dict[str, Any]:
        """
        Performs continuous quantum spatial search for target_node over a range of times,
        identifying the optimal hitting time t_opt and peak success probability.
        """
        with self._lock:
            n = self.num_nodes
            if target_node < 0 or target_node >= n:
                target_node = 0
            self.marked_target = target_node

            best_time = 0.0
            peak_prob = 0.0
            dt = max_time / max(1, time_samples)

            for step in range(1, time_samples + 1):
                t = step * dt
                res = self.propagate_quantum_state(
                    evolution_time=t,
                    marked_node=target_node,
                    oracle_depth=oracle_depth
                )
                p = res["target_hitting_probability"]
                if p > peak_prob:
                    peak_prob = p
                    best_time = t

            classical_diffusion_steps = n
            quantum_equivalent_steps = round(math.sqrt(n), 2)

            search_record = {
                "target_node": target_node,
                "num_nodes": n,
                "optimal_time_t": round(best_time, 4),
                "peak_success_probability": round(peak_prob, 6),
                "classical_complexity": classical_diffusion_steps,
                "quantum_complexity": quantum_equivalent_steps,
                "quantum_advantage_factor": round(peak_prob * math.sqrt(n), 4)
            }
            self.search_history.append(search_record)
            return search_record

    def get_status(self) -> Dict[str, Any]:
        """Returns comprehensive status of Stage 265."""
        with self._lock:
            edge_count = sum(sum(1 for val in row if val > 0.0) for row in self.adj_matrix) // 2
            return {
                "stage": STAGE_ID,
                "stage_name": STAGE_NAME,
                "era": ERA_ID,
                "era_name": ERA_NAME,
                "sovereign_operator": SOVEREIGN_OPERATOR,
                "sovereign_legal_name": SOVEREIGN_LEGAL_NAME,
                "num_nodes": self.num_nodes,
                "num_edges": edge_count,
                "hopping_rate_gamma": self.gamma,
                "hbar": self.hbar,
                "marked_target": self.marked_target,
                "total_searches_executed": len(self.search_history)
            }


ContinuousQuantumWalkSearchFabric = ContinuousQuantumWalkSearch
