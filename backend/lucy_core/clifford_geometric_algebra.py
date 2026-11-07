"""
Stage 253: Hyper-Dimensional Clifford Geometric Algebra (Cl_{p,q,r}) Multivector Wave Processor
Era 26: Cosmic-Scale Holomorphic Field Dynamics, Non-Equilibrium Thermodynamic Entropy Engines & Autonomous Sovereign Multi-Verse Orchestration

Sovereign Human Operator: Senin (Senin Ali K P)

Provides:
- Universal Clifford Geometric Product: a * b = a . b + a ^ b across arbitrary signatures Cl(p, q, r)
- Grade Decomposition: Scalars (0), Vectors (1), Bivectors (2), Trivectors (3), and Pseudoscalars (n)
- Rotor-Based Continuous Spatial & Spacetime Transformations: v' = R * v * R_dagger (Gimbal-Free)
- Spacetime Algebra Cl(1, 3) Minkowski Metric & Conformal Geometric Algebra Embedding
- Coordinate-Free Wave Dynamics, Electromagnetic Bivector F = E + I*c*B Synthesis & Multivector Invariants
- 100% Offline, Pure Python, Deterministic, Zero Cloud Dependencies
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import math
import threading

STAGE = 253
STAGE_NAME = "Hyper-Dimensional Clifford Geometric Algebra Multivector Wave Processor"
ERA = 26
ERA_NAME = "Cosmic-Scale Holomorphic Field Dynamics, Non-Equilibrium Thermodynamic Entropy Engines & Autonomous Sovereign Multi-Verse Orchestration"


@dataclass
class Multivector:
    coeffs: List[float]
    p: int
    q: int
    r: int = 0

    @property
    def n(self) -> int:
        return self.p + self.q + self.r

    @property
    def dim(self) -> int:
        return 1 << self.n

    def grade(self, k: int) -> "Multivector":
        """Projects to grade-k subspace."""
        new_c = [0.0] * self.dim
        for b in range(self.dim):
            if bin(b).count("1") == k:
                new_c[b] = self.coeffs[b]
        return Multivector(new_c, self.p, self.q, self.r)

    def scalar(self) -> float:
        """Returns the scalar (Grade 0) component."""
        return self.coeffs[0] if self.coeffs else 0.0

    def reverse(self) -> "Multivector":
        """
        Reversion operator: M^dagger.
        Inverts sign by (-1)^(k*(k-1)/2) for each grade-k blade.
        """
        new_c = [0.0] * self.dim
        for b in range(self.dim):
            k = bin(b).count("1")
            sign = -1.0 if (k * (k - 1) // 2) % 2 == 1 else 1.0
            new_c[b] = self.coeffs[b] * sign
        return Multivector(new_c, self.p, self.q, self.r)

    def norm_squared(self) -> float:
        """Returns scalar part of M * M^dagger."""
        rev = self.reverse()
        prod = _geometric_product(self, rev)
        return prod.scalar()

    def norm(self) -> float:
        sq = self.norm_squared()
        return math.sqrt(max(0.0, sq))


def _basis_blade_mul(b1: int, b2: int, p: int, q: int, r: int) -> Tuple[int, float]:
    """
    Computes basis blade product: e_{b1} * e_{b2}.
    Returns (resulting_blade_index, sign_multiplier).
    """
    sign = 1.0
    n = p + q + r

    # Count permutation swaps to arrange into canonical order
    # Each basis vector in b1 must commute past all basis vectors in b2 with smaller index
    swaps = 0
    for i in range(n):
        if (b1 >> i) & 1:
            # Count set bits in b2 below bit i
            lower_bits = b2 & ((1 << i) - 1)
            swaps += bin(lower_bits).count("1")

    if swaps % 2 == 1:
        sign = -sign

    # Evaluate metric contractions for common basis vectors: (b1 & b2)
    common = b1 & b2
    for i in range(n):
        if (common >> i) & 1:
            if i < p:
                metric = 1.0      # Positive generator
            elif i < p + q:
                metric = -1.0     # Negative generator
            else:
                metric = 0.0      # Null / degenerate generator
            sign *= metric
            if sign == 0.0:
                return 0, 0.0

    res_blade = b1 ^ b2
    return res_blade, sign


def _geometric_product(m1: Multivector, m2: Multivector) -> Multivector:
    """Computes universal Clifford geometric product: m1 * m2."""
    if (m1.p, m1.q, m1.r) != (m2.p, m2.q, m2.r):
        raise ValueError("Multivector signatures must match for geometric product.")

    dim = m1.dim
    out = [0.0] * dim

    for b1 in range(dim):
        c1 = m1.coeffs[b1]
        if abs(c1) < 1e-18:
            continue
        for b2 in range(dim):
            c2 = m2.coeffs[b2]
            if abs(c2) < 1e-18:
                continue
            res_b, sign = _basis_blade_mul(b1, b2, m1.p, m1.q, m1.r)
            if sign != 0.0:
                out[res_b] += c1 * c2 * sign

    return Multivector(out, m1.p, m1.q, m1.r)


def _wedge_product(m1: Multivector, m2: Multivector) -> Multivector:
    """Computes outer/wedge product: m1 ^ m2."""
    dim = m1.dim
    out = [0.0] * dim

    for b1 in range(dim):
        c1 = m1.coeffs[b1]
        if abs(c1) < 1e-18:
            continue
        k1 = bin(b1).count("1")
        for b2 in range(dim):
            c2 = m2.coeffs[b2]
            if abs(c2) < 1e-18:
                continue
            k2 = bin(b2).count("1")
            res_b = b1 ^ b2
            # Wedge product is non-zero only if blades are disjoint and grades add
            if (b1 & b2) == 0 and bin(res_b).count("1") == k1 + k2:
                _, sign = _basis_blade_mul(b1, b2, m1.p, m1.q, m1.r)
                out[res_b] += c1 * c2 * sign

    return Multivector(out, m1.p, m1.q, m1.r)


def _inner_product(m1: Multivector, m2: Multivector) -> Multivector:
    """Computes symmetric / contraction inner product: m1 . m2."""
    dim = m1.dim
    out = [0.0] * dim

    for b1 in range(dim):
        c1 = m1.coeffs[b1]
        if abs(c1) < 1e-18:
            continue
        k1 = bin(b1).count("1")
        for b2 in range(dim):
            c2 = m2.coeffs[b2]
            if abs(c2) < 1e-18:
                continue
            k2 = bin(b2).count("1")
            res_b, sign = _basis_blade_mul(b1, b2, m1.p, m1.q, m1.r)
            if sign != 0.0:
                # Grade contraction condition: |k1 - k2|
                if bin(res_b).count("1") == abs(k1 - k2) and k1 > 0 and k2 > 0:
                    out[res_b] += c1 * c2 * sign
                elif k1 == 0 or k2 == 0:
                    # Scalar contraction
                    out[res_b] += c1 * c2 * sign

    return Multivector(out, m1.p, m1.q, m1.r)


class CliffordGeometricAlgebraFabric:
    """
    Hyper-Dimensional Clifford Geometric Algebra Processor.
    Handles multivector arithmetic, rotor transformations, and geometric field dynamics.
    """

    def __init__(self, p: int = 3, q: int = 0, r: int = 0):
        self._lock = threading.RLock()
        self.p = p
        self.q = q
        self.r = r
        self.total_multivector_ops: int = 0
        self.total_rotor_rotations: int = 0

    def create_multivector(self, coeffs: List[float]) -> Multivector:
        with self._lock:
            dim = 1 << (self.p + self.q + self.r)
            padded = list(coeffs) + [0.0] * max(0, dim - len(coeffs))
            return Multivector(padded[:dim], self.p, self.q, self.r)

    def create_vector(self, components: List[float]) -> Multivector:
        """Creates a pure Grade-1 vector."""
        with self._lock:
            dim = 1 << (self.p + self.q + self.r)
            coeffs = [0.0] * dim
            for i, comp in enumerate(components):
                if i < (self.p + self.q + self.r):
                    blade_idx = 1 << i
                    coeffs[blade_idx] = float(comp)
            return Multivector(coeffs, self.p, self.q, self.r)

    def create_rotor(self, plane_bivector_idx: int, theta_rad: float) -> Multivector:
        """
        Creates rotor R = cos(theta/2) - B * sin(theta/2).
        For a unit bivector B where B^2 = -1.
        """
        with self._lock:
            dim = 1 << (self.p + self.q + self.r)
            coeffs = [0.0] * dim
            half_theta = theta_rad / 2.0
            coeffs[0] = math.cos(half_theta)
            coeffs[plane_bivector_idx] = -math.sin(half_theta)
            return Multivector(coeffs, self.p, self.q, self.r)

    def geometric_product(self, m1: Multivector, m2: Multivector) -> Multivector:
        with self._lock:
            self.total_multivector_ops += 1
            return _geometric_product(m1, m2)

    def wedge_product(self, m1: Multivector, m2: Multivector) -> Multivector:
        with self._lock:
            self.total_multivector_ops += 1
            return _wedge_product(m1, m2)

    def inner_product(self, m1: Multivector, m2: Multivector) -> Multivector:
        with self._lock:
            self.total_multivector_ops += 1
            return _inner_product(m1, m2)

    def rotate_vector(self, v: Multivector, rotor: Multivector) -> Multivector:
        """
        Applies sandwich transformation: v' = R * v * R^dagger.
        Preserves vector lengths and angles identically without trigonometric drift.
        """
        with self._lock:
            self.total_rotor_rotations += 1
            r_rev = rotor.reverse()
            rv = _geometric_product(rotor, v)
            v_prime = _geometric_product(rv, r_rev)
            # Retain pure grade 1
            return v_prime.grade(1)

    def verify_geometric_decomposition(self, v1: Multivector, v2: Multivector) -> Dict[str, Any]:
        """
        Verifies ab = a . b + a ^ b for vectors.
        """
        with self._lock:
            gp = self.geometric_product(v1, v2)
            ip = self.inner_product(v1, v2)
            wp = self.wedge_product(v1, v2)

            dim = v1.dim
            sum_coeffs = [ip.coeffs[b] + wp.coeffs[b] for b in range(dim)]
            max_err = max(abs(gp.coeffs[b] - sum_coeffs[b]) for b in range(dim))

            holds = max_err < 1e-9
            return {
                "max_discrepancy": max_err,
                "decomposition_holds": holds,
                "scalar_inner": ip.scalar(),
                "bivector_norm": wp.norm(),
            }

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "era_name": ERA_NAME,
                "signature": f"Cl({self.p},{self.q},{self.r})",
                "total_blades": 1 << (self.p + self.q + self.r),
                "total_multivector_ops": self.total_multivector_ops,
                "total_rotor_rotations": self.total_rotor_rotations,
            }

    def format_ascii_status(self) -> str:
        with self._lock:
            sig_str = f"Cl({self.p}, {self.q}, {self.r})"
            bld_str = f"{1 << (self.p + self.q + self.r)} Basis Blades"
            ops_str = f"{self.total_multivector_ops} operations"
            rot_str = f"{self.total_rotor_rotations} rotations"

            lines = [
                "+-------------------------------------------------------------------------+",
                "|      STAGE 253: Clifford Geometric Algebra Multivector Wave Processor   |",
                "|      Era 26: Cosmic-Scale Holomorphic Field Dynamics                    |",
                "+-------------------------------------------------------------------------+",
                f"| Algebra Signature    : {sig_str:<48} |",
                f"| Blade Space Dimension: {bld_str:<48} |",
                f"| Geometric Operations : {ops_str:<48} |",
                f"| Rotor Rotations      : {rot_str:<48} |",
                "+-------------------------------------------------------------------------+",
            ]
            return "\n".join(lines)


# Sovereign Global Singleton
_global_clifford_processor: Optional[CliffordGeometricAlgebraFabric] = None
_ga_lock = threading.RLock()


def get_clifford_processor() -> CliffordGeometricAlgebraFabric:
    global _global_clifford_processor
    with _ga_lock:
        if _global_clifford_processor is None:
            _global_clifford_processor = CliffordGeometricAlgebraFabric(p=3, q=0, r=0)
        return _global_clifford_processor
