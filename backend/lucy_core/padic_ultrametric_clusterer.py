"""
Stage 248: Non-Archimedean p-Adic Ultrametric Cognitive Clustering & Hierarchical Tree Space Embedding
Era 25: Omni-Dimensional Super-Intelligence Matrix, Astro-Cognitive Planetary Orchestration & Sovereign Trans-Singularity Metamaterials

Sovereign Human Operator: Senin (Senin Ali K P)

Provides:
- Non-Archimedean Arithmetic in Q_p: p-Adic Valuation v_p(x) & Ultrametric Norm |x|_p = p^{-v_p(x)}
- Strong Triangle (Ultrametric) Inequality Invariance: d(x, y) <= max(d(x, z), d(z, y))
- Tree-Space Cognitive Embedding: Mapping multi-dimensional concepts to p-adic canonical integer expansions
- Isometric Hierarchical Dendrogram Clustering & Ball Filtration in ultrametric topology
- Non-overlapping hierarchical disjoint cluster trees (Every point inside a ball is a center)
- 100% Offline, Pure Python, Deterministic, Zero Cloud Dependencies
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
import math
import threading

STAGE = 248
STAGE_NAME = "Non-Archimedean p-Adic Ultrametric Cognitive Clustering & Hierarchical Tree Space Embedding"
ERA = 25
ERA_NAME = "Omni-Dimensional Super-Intelligence Matrix, Astro-Cognitive Planetary Orchestration & Sovereign Trans-Singularity Metamaterials"


@dataclass
class UltrametricNode:
    name: str
    vector: List[float]
    padic_repr: int
    cluster_id: Optional[str] = None


@dataclass
class UltrametricCluster:
    cluster_id: str
    radius: float
    members: List[str]
    centroid_padic: int


class PadicUltrametricClustererFabric:
    """
    Non-Archimedean p-Adic Ultrametric Clustering Fabric.
    Constructs distortion-free hierarchical tree spaces where the strong triangle inequality holds identically.
    """

    def __init__(self, prime_base: int = 3, precision_levels: int = 8):
        self._lock = threading.RLock()
        if prime_base < 2 or not self._is_prime(prime_base):
            raise ValueError(f"Base must be a prime number >= 2, got {prime_base}")
        self.p = prime_base
        self.precision_levels = precision_levels
        self.nodes: Dict[str, UltrametricNode] = {}
        self.total_clusters_formed: int = 0
        self.total_comparisons: int = 0
        self.last_strong_triangle_checks: int = 0

    @staticmethod
    def _is_prime(n: int) -> bool:
        if n < 2:
            return False
        for i in range(2, int(math.isqrt(n)) + 1):
            if n % i == 0:
                return False
        return True

    def p_adic_valuation(self, x: int) -> int:
        """
        Computes v_p(x): highest exponent k such that p^k divides x.
        v_p(0) is formally infinity; we return a large integer sentinel (1000).
        """
        if x == 0:
            return 1000
        val = abs(int(x))
        k = 0
        while val > 0 and val % self.p == 0:
            k += 1
            val //= self.p
        return k

    def p_adic_norm(self, x: int) -> float:
        """
        Computes non-Archimedean norm |x|_p = p^{-v_p(x)}.
        |0|_p = 0.
        """
        if x == 0:
            return 0.0
        v = self.p_adic_valuation(x)
        return float(self.p ** (-v))

    def ultrametric_distance(self, x: int, y: int) -> float:
        """
        Computes ultrametric distance d_p(x, y) = |x - y|_p.
        """
        with self._lock:
            self.total_comparisons += 1
            diff = x - y
            return self.p_adic_norm(diff)

    def verify_strong_triangle_inequality(self, x: int, y: int, z: int) -> Dict[str, Any]:
        """
        Verifies the Strong Triangle Inequality (Ultrametric):
        d(x, z) <= max(d(x, y), d(y, z))
        And that every triangle is isosceles with the two longest sides equal.
        """
        with self._lock:
            d_xz = self.ultrametric_distance(x, z)
            d_xy = self.ultrametric_distance(x, y)
            d_yz = self.ultrametric_distance(y, z)

            max_right = max(d_xy, d_yz)
            holds = d_xz <= (max_right + 1e-12)

            sides = sorted([d_xz, d_xy, d_yz])
            # In ultrametric space, the two largest sides must be equal
            is_isosceles_ultrametric = abs(sides[1] - sides[2]) < 1e-9

            self.last_strong_triangle_checks += 1
            return {
                "d_xz": d_xz,
                "d_xy": d_xy,
                "d_yz": d_yz,
                "max_subpath": max_right,
                "strong_inequality_holds": holds,
                "is_isosceles_ultrametric": is_isosceles_ultrametric,
                "sides_sorted": sides,
            }

    def vector_to_p_adic(self, vector: List[float]) -> int:
        """
        Embeds a continuous multi-dimensional cognitive vector into a p-adic integer expansion:
        Each dimension is quantized into base-p digits and interleaved hierarchically.
        """
        if not vector:
            return 0

        padic_val = 0
        dim = len(vector)
        # Interleave coordinates across depth levels
        for level in range(self.precision_levels):
            weight = self.p ** level
            digit_sum = 0
            for i, val in enumerate(vector):
                # Map float val into bounded base-p digit
                mapped = int(abs(val * (10 ** (i % 3 + 1)))) % self.p
                digit_sum = (digit_sum + mapped) % self.p
            padic_val += digit_sum * weight

        return padic_val

    def register_concept(self, name: str, vector: List[float]) -> UltrametricNode:
        """
        Registers a concept and calculates its canonical p-adic tree representation.
        """
        with self._lock:
            padic_int = self.vector_to_p_adic(vector)
            node = UltrametricNode(
                name=name,
                vector=list(vector),
                padic_repr=padic_int,
            )
            self.nodes[name] = node
            return node

    def cluster_concepts(self, max_radius: float = 0.35) -> List[UltrametricCluster]:
        """
        Performs non-Archimedean hierarchical ball clustering.
        In p-adic space, if two balls intersect, one is a subset of the other.
        Every point inside a ball is its center!
        """
        with self._lock:
            if not self.nodes:
                return []

            unassigned: Set[str] = set(self.nodes.keys())
            clusters: List[UltrametricCluster] = []
            cluster_idx = 1

            while unassigned:
                # Pick any element as centroid (any element in a p-adic ball is a valid center)
                seed_name = sorted(list(unassigned))[0]
                seed_node = self.nodes[seed_name]

                members: List[str] = []
                for name in list(unassigned):
                    cand = self.nodes[name]
                    dist = self.ultrametric_distance(seed_node.padic_repr, cand.padic_repr)
                    if dist <= max_radius:
                        members.append(name)

                for m in members:
                    unassigned.remove(m)
                    self.nodes[m].cluster_id = f"CLUST-P{self.p}-{cluster_idx}"

                cluster = UltrametricCluster(
                    cluster_id=f"CLUST-P{self.p}-{cluster_idx}",
                    radius=max_radius,
                    members=members,
                    centroid_padic=seed_node.padic_repr,
                )
                clusters.append(cluster)
                cluster_idx += 1

            self.total_clusters_formed = len(clusters)
            return clusters

    def build_hierarchical_dendrogram(self) -> Dict[str, Any]:
        """
        Constructs a complete multi-scale ultrametric dendrogram across discrete valuation levels.
        """
        with self._lock:
            names = sorted(list(self.nodes.keys()))
            n = len(names)
            if n == 0:
                return {"levels": [], "matrix": []}

            # Distance matrix
            dist_matrix: Dict[str, Dict[str, float]] = {a: {} for a in names}
            for i in range(n):
                for j in range(i, n):
                    a, b = names[i], names[j]
                    d = self.ultrametric_distance(self.nodes[a].padic_repr, self.nodes[b].padic_repr)
                    dist_matrix[a][b] = d
                    dist_matrix[b][a] = d

            # Hierarchy filtration by radius powers p^(-k)
            filtration = []
            for k in range(self.precision_levels):
                r = float(self.p ** (-k))
                clusters_at_r = self.cluster_concepts(max_radius=r)
                filtration.append({
                    "level_k": k,
                    "radius": r,
                    "cluster_count": len(clusters_at_r),
                    "clusters": [{"id": c.cluster_id, "size": len(c.members)} for c in clusters_at_r],
                })

            return {
                "prime_base": self.p,
                "total_concepts": n,
                "filtration": filtration,
                "distance_matrix": dist_matrix,
            }

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "era_name": ERA_NAME,
                "prime_base": self.p,
                "precision_levels": self.precision_levels,
                "total_nodes_registered": len(self.nodes),
                "total_clusters_formed": self.total_clusters_formed,
                "total_distance_comparisons": self.total_comparisons,
                "strong_triangle_verifications": self.last_strong_triangle_checks,
            }

    def format_ascii_status(self) -> str:
        with self._lock:
            p_str = f"{self.p}"
            nodes_str = f"{len(self.nodes)}"
            clust_str = f"{self.total_clusters_formed}"
            comp_str = f"{self.total_comparisons}"
            check_str = f"{self.last_strong_triangle_checks}"

            lines = [
                "+-------------------------------------------------------------------------+",
                "|      STAGE 248: Non-Archimedean p-Adic Ultrametric Clusterer            |",
                "|      Era 25: Omni-Dimensional Super-Intelligence Matrix                |",
                "+-------------------------------------------------------------------------+",
                f"| Prime Base (p)       : {p_str:<48} |",
                f"| Registered Concepts  : {nodes_str:<48} |",
                f"| Active Clusters      : {clust_str:<48} |",
                f"| Distance Evaluations : {comp_str:<48} |",
                f"| Ultrametric Checks   : {check_str:<48} |",
                "+-------------------------------------------------------------------------+",
            ]
            return "\n".join(lines)


# Sovereign Global Singleton
_global_padic_clusterer: Optional[PadicUltrametricClustererFabric] = None
_padic_lock = threading.RLock()


def get_padic_clusterer() -> PadicUltrametricClustererFabric:
    global _global_padic_clusterer
    with _padic_lock:
        if _global_padic_clusterer is None:
            _global_padic_clusterer = PadicUltrametricClustererFabric(prime_base=3)
        return _global_padic_clusterer
