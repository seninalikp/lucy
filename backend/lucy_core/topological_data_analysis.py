r"""
backend/lucy_core/topological_data_analysis.py
Stage 226: Self-Supervised Topological Data Analysis (TDA) & Persistent Homology Engine
Era 23: Universal Multi-Verse State Synthesis, Sub-Atomic Hyper-Computing & Sovereign Holographic Swarm Intelligence

100% offline, sovereign topological data analysis (TDA) and persistent homology engine:
1. Vietoris-Rips Complex Construction:
   - Builds filtered simplicial complexes (0-simplices, 1-simplices, 2-simplices) from point cloud metric spaces.
2. Persistent Homology & Topological Invariants:
   - Extracts Betti numbers: beta_0 (connected components) and beta_1 (1-dimensional cycles/cavities).
   - Tracks birth-death filtration intervals and persistence lifespans to distinguish signal from noise.
3. Topological Fingerprinting & Feature Extraction:
   - Produces compact persistence barcodes and computes bottleneck distance between topological manifolds.
4. Thread-safe execution fabric and CP1252-safe ASCII table formatting.
"""

from __future__ import annotations

import collections
import copy
import hashlib
import math
import threading
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union

STAGE: int = 226
STAGE_NAME: str = "Self-Supervised Topological Data Analysis & Persistent Homology Engine"
ERA: int = 23
ERA_NAME: str = "Universal Multi-Verse State Synthesis, Sub-Atomic Hyper-Computing & Sovereign Holographic Swarm Intelligence"


@dataclass
class PersistenceInterval:
    dimension: int  # 0 for H0 (components), 1 for H1 (loops)
    birth: float
    death: float
    feature_id: str

    @property
    def lifespan(self) -> float:
        return self.death - self.birth

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "birth": round(self.birth, 4),
            "death": round(self.death, 4) if self.death != float("inf") else "inf",
            "lifespan": round(self.lifespan, 4) if self.death != float("inf") else "inf",
            "feature_id": self.feature_id,
        }


class DisjointSet:
    """Union-Find disjoint-set data structure with birth tracking for H0 persistent homology."""

    def __init__(self, n: int) -> None:
        self.parent: List[int] = list(range(n))
        self.rank: List[int] = [0] * n
        self.birth: List[float] = [0.0] * n

    def find(self, x: int) -> int:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: int, y: int, current_eps: float) -> Optional[Tuple[int, float]]:
        rx = self.find(x)
        ry = self.find(y)
        if rx == ry:
            return None

        # Elder rule: the older component (earlier birth) survives
        if self.birth[rx] > self.birth[ry]:
            rx, ry = ry, rx
        elif self.birth[rx] == self.birth[ry] and rx > ry:
            rx, ry = ry, rx

        died_birth = self.birth[ry]
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
        return (ry, died_birth)


class TopologicalDataAnalysisFabric:
    """
    Thread-safe Vietoris-Rips filtration & persistent homology engine.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.point_clouds: Dict[str, List[List[float]]] = {}
        self.persistence_results: Dict[str, List[PersistenceInterval]] = {}
        self.total_analyses: int = 0

    def add_point_cloud(self, cloud_id: str, points: List[List[float]]) -> None:
        with self._lock:
            if not points:
                raise ValueError("Point cloud cannot be empty.")
            dim = len(points[0])
            if any(len(p) != dim for p in points):
                raise ValueError("All points in cloud must share identical dimensionality.")
            self.point_clouds[cloud_id] = copy.deepcopy(points)

    def _euclidean_distance(self, p1: List[float], p2: List[float]) -> float:
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))

    def compute_vietoris_rips_homology(
        self,
        cloud_id: str,
        max_epsilon: Optional[float] = None,
        num_steps: int = 50,
    ) -> List[PersistenceInterval]:
        """
        Computes 0D and 1D persistent homology using Vietoris-Rips filtration over point cloud.
        """
        with self._lock:
            if cloud_id not in self.point_clouds:
                raise ValueError(f"Point cloud '{cloud_id}' does not exist.")

            points = self.point_clouds[cloud_id]
            n = len(points)
            if n < 2:
                interval = PersistenceInterval(dimension=0, birth=0.0, death=float("inf"), feature_id="h0_0")
                self.persistence_results[cloud_id] = [interval]
                return [interval]

            # 1. Compute pairwise distance matrix & sorted edge list
            edges: List[Tuple[float, int, int]] = []
            max_dist = 0.0
            for i in range(n):
                for j in range(i + 1, n):
                    d = self._euclidean_distance(points[i], points[j])
                    edges.append((d, i, j))
                    if d > max_dist:
                        max_dist = d

            edges.sort(key=lambda x: x[0])
            eps_bound = max_epsilon if max_epsilon is not None else max_dist

            intervals: List[PersistenceInterval] = []

            # 2. H0 Persistent Homology (Connected Components via Elder Rule)
            uf = DisjointSet(n)
            for d, u, v in edges:
                if d > eps_bound:
                    break
                merged = uf.union(u, v, d)
                if merged is not None:
                    died_idx, birth_time = merged
                    intervals.append(
                        PersistenceInterval(
                            dimension=0,
                            birth=birth_time,
                            death=d,
                            feature_id=f"h0_{died_idx}",
                        )
                    )

            # Surviving connected component (infinite persistence)
            intervals.append(
                PersistenceInterval(
                    dimension=0,
                    birth=0.0,
                    death=float("inf"),
                    feature_id="h0_essential",
                )
            )

            # 3. H1 Persistent Homology (1-Cycles / Loops via Triangle Fill Filtration)
            # Find triangles formed by edges: a cycle born at edge (u, v) dies when filled by third vertex w
            adj: Dict[int, Set[int]] = {i: set() for i in range(n)}
            edge_birth: Dict[Tuple[int, int], float] = {}

            active_cycles: List[Tuple[float, Tuple[int, int]]] = []
            for d, u, v in edges:
                if d > eps_bound:
                    break
                edge_key = (min(u, v), max(u, v))
                edge_birth[edge_key] = d

                # Check if u and v share mutual neighbors (forming triangles)
                common_neighbors = adj[u].intersection(adj[v])
                adj[u].add(v)
                adj[v].add(u)

                if common_neighbors:
                    # The triangle fills a 1-cycle
                    for w in common_neighbors:
                        e1 = (min(u, w), max(u, w))
                        e2 = (min(v, w), max(v, w))
                        cycle_birth = min(edge_birth.get(e1, 0.0), edge_birth.get(e2, 0.0))
                        cycle_death = d
                        if cycle_death - cycle_birth > 1e-4:
                            intervals.append(
                                PersistenceInterval(
                                    dimension=1,
                                    birth=cycle_birth,
                                    death=cycle_death,
                                    feature_id=f"h1_{len(intervals)}",
                                )
                            )
                            break

            self.total_analyses += 1
            self.persistence_results[cloud_id] = intervals
            return intervals

    def compute_betti_numbers(self, cloud_id: str, epsilon: float) -> Dict[str, int]:
        """Returns Betti numbers (beta_0, beta_1) at a given filtration threshold."""
        with self._lock:
            if cloud_id not in self.persistence_results:
                self.compute_vietoris_rips_homology(cloud_id)

            intervals = self.persistence_results[cloud_id]
            b0 = sum(1 for it in intervals if it.dimension == 0 and it.birth <= epsilon < it.death)
            b1 = sum(1 for it in intervals if it.dimension == 1 and it.birth <= epsilon < it.death)
            return {"beta_0": b0, "beta_1": b1, "epsilon": round(epsilon, 4)}

    def compute_bottleneck_distance(self, cloud_a_id: str, cloud_b_id: str) -> float:
        """Approximates bottleneck distance between two persistence diagrams."""
        with self._lock:
            int_a = self.persistence_results.get(cloud_a_id) or self.compute_vietoris_rips_homology(cloud_a_id)
            int_b = self.persistence_results.get(cloud_b_id) or self.compute_vietoris_rips_homology(cloud_b_id)

            # Compare lifespan vectors sorted in descending order
            life_a = sorted([it.lifespan for it in int_a if it.death != float("inf")], reverse=True)
            life_b = sorted([it.lifespan for it in int_b if it.death != float("inf")], reverse=True)

            max_len = max(len(life_a), len(life_b))
            while len(life_a) < max_len:
                life_a.append(0.0)
            while len(life_b) < max_len:
                life_b.append(0.0)

            diffs = [abs(a - b) for a, b in zip(life_a, life_b)]
            return round(max(diffs) if diffs else 0.0, 4)

    def generate_circle_sample(self, cloud_id: str, num_points: int = 16, radius: float = 1.0) -> None:
        """Generates a canonical circular point cloud with known topological 1-hole (beta_1 = 1)."""
        points: List[List[float]] = []
        for i in range(num_points):
            theta = 2.0 * math.pi * i / num_points
            points.append([radius * math.cos(theta), radius * math.sin(theta)])
        self.add_point_cloud(cloud_id, points)

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "era_name": ERA_NAME,
                "loaded_clouds": list(self.point_clouds.keys()),
                "total_clouds": len(self.point_clouds),
                "total_analyses": self.total_analyses,
                "analyzed_diagrams": len(self.persistence_results),
            }

    def format_ascii_status(self) -> str:
        s = self.status()
        header = f"+-------------------------------------------------------------------------+\n|      STAGE {s['stage']}: {s['stage_name'].upper()[:52]:<52} |\n|      Era {s['era']}: {s['era_name'][:56]:<56} |\n+-------------------------------------------------------------------------+"
        clouds_str = ", ".join(s["loaded_clouds"])
        if len(clouds_str) > 48:
            clouds_str = clouds_str[:45] + "..."
        body = (
            f"| Total Point Clouds   : {s['total_clouds']:<48} |\n"
            f"| Point Cloud List     : {clouds_str:<48} |\n"
            f"| Total TDA Analyses   : {s['total_analyses']:<48} |\n"
            f"| Analyzed Diagrams    : {s['analyzed_diagrams']:<48} |"
        )
        footer = "+-------------------------------------------------------------------------+"
        return f"{header}\n{body}\n{footer}"
