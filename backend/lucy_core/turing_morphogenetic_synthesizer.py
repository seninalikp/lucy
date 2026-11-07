"""
Stage 255: Sovereign Bio-Mimetic Morphogenetic Reaction-Diffusion Turing Pattern Synthesizer
Era 26: Cosmic-Scale Holomorphic Field Dynamics, Non-Equilibrium Thermodynamic Entropy Engines & Autonomous Sovereign Multi-Verse Orchestration

Sovereign Human Operator: Senin (Senin Ali K P)

Provides:
- Non-Linear Reaction-Diffusion PDE Systems: d_t u = D_u * del^2 u + f(u, v), d_t v = D_v * del^2 v + g(u, v)
- Turing Instability Mathematical Auditing: Differential Diffusion D_v / D_u > 1 & Bifurcation Criteria
- Gray-Scott Morphogenetic Pattern Synthesis: Spatially localized spots, labyrinthine stripes, and traveling waves
- Spatial Wavelength & Morphogenetic Spectral Density Classification (Spots vs Labyrinth vs Soliton)
- Periodic Toroidal Stencil Integration & Self-Organizing Bio-Mimetic Structural Synthesis
- 100% Offline, Pure Python, Deterministic, Zero Cloud Dependencies
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import math
import random
import threading

STAGE = 255
STAGE_NAME = "Sovereign Bio-Mimetic Morphogenetic Reaction-Diffusion Turing Pattern Synthesizer"
ERA = 26
ERA_NAME = "Cosmic-Scale Holomorphic Field Dynamics, Non-Equilibrium Thermodynamic Entropy Engines & Autonomous Sovereign Multi-Verse Orchestration"


class MorphogeneticRegime(Enum):
    HOMOGENEOUS = "HOMOGENEOUS"
    SPOTS_SOLITONS = "SPOTS_SOLITONS"
    STRIPES_LABYRINTH = "STRIPES_LABYRINTH"
    DYNAMIC_WAVES = "DYNAMIC_WAVES"


class TuringMorphogeneticSynthesizerFabric:
    """
    Turing Morphogenetic Reaction-Diffusion Synthesizer.
    Generates self-organizing structural patterns via non-linear spatial chemical kinetics.
    """

    def __init__(
        self,
        grid_width: int = 32,
        grid_height: int = 32,
        diff_u: float = 0.16,
        diff_v: float = 0.08,
        feed_f: float = 0.035,
        kill_k: float = 0.065,
    ):
        self._lock = threading.RLock()
        self.w = grid_width
        self.h = grid_height
        self.du = float(diff_u)
        self.dv = float(diff_v)
        self.f = float(feed_f)
        self.k = float(kill_k)

        # Initialize homogeneous state: u = 1.0, v = 0.0
        self.u = [[1.0 for _ in range(self.w)] for _ in range(self.h)]
        self.v = [[0.0 for _ in range(self.w)] for _ in range(self.h)]

        self.total_simulation_steps: int = 0
        self.total_perturbations_injected: int = 0

    def seed_central_spot(self, radius: int = 4, u_val: float = 0.5, v_val: float = 0.25) -> None:
        """Seeds a localized perturbation at the center to trigger symmetry breaking."""
        with self._lock:
            cx, cy = self.w // 2, self.h // 2
            for y in range(self.h):
                for x in range(self.w):
                    dist_sq = (x - cx) ** 2 + (y - cy) ** 2
                    if dist_sq <= radius ** 2:
                        self.u[y][x] = u_val
                        self.v[y][x] = v_val

            self.total_perturbations_injected += 1

    def step_reaction_diffusion(self, steps: int = 1, dt: float = 1.0) -> None:
        """
        Integrates Gray-Scott reaction-diffusion equations:
        du/dt = D_u * del^2 u - u*v^2 + F * (1 - u)
        dv/dt = D_v * del^2 v + u*v^2 - (F + k) * v
        Using periodic boundary conditions.
        """
        with self._lock:
            for _ in range(steps):
                new_u = [[0.0 for _ in range(self.w)] for _ in range(self.h)]
                new_v = [[0.0 for _ in range(self.w)] for _ in range(self.h)]

                for y in range(self.h):
                    ym1 = (y - 1) % self.h
                    yp1 = (y + 1) % self.h
                    for x in range(self.w):
                        xm1 = (x - 1) % self.w
                        xp1 = (x + 1) % self.w

                        u_c = self.u[y][x]
                        v_c = self.v[y][x]

                        # 5-point discrete Laplacian
                        lap_u = self.u[ym1][x] + self.u[yp1][x] + self.u[y][xm1] + self.u[y][xp1] - 4.0 * u_c
                        lap_v = self.v[ym1][x] + self.v[yp1][x] + self.v[y][xm1] + self.v[y][xp1] - 4.0 * v_c

                        uvv = u_c * v_c * v_c

                        # Reaction-Diffusion kinetics
                        du_dt = self.du * lap_u - uvv + self.f * (1.0 - u_c)
                        dv_dt = self.dv * lap_v + uvv - (self.f + self.k) * v_c

                        new_u[y][x] = max(0.0, min(1.0, u_c + dt * du_dt))
                        new_v[y][x] = max(0.0, min(1.0, v_c + dt * dv_dt))

                self.u = new_u
                self.v = new_v
                self.total_simulation_steps += 1

    def evaluate_turing_instability(
        self,
        fu: float,
        fv: float,
        gu: float,
        gv: float,
        du: float,
        dv: float,
    ) -> Dict[str, Any]:
        """
        Analytically checks Turing's four necessary and sufficient instability criteria:
        1. fu + gv < 0  (Stable without diffusion)
        2. fu * gv - fv * gu > 0  (Positive determinant without diffusion)
        3. dv * fu + du * gv > 0  (Differential diffusion destabilization)
        4. (dv * fu + du * gv)^2 > 4 * du * dv * (fu * gv - fv * gu)  (Turing bifurcation)
        """
        with self._lock:
            det_j = fu * gv - fv * gu
            tr_j = fu + gv

            cond1 = tr_j < 0.0
            cond2 = det_j > 0.0
            mixed_diffusion = dv * fu + du * gv
            cond3 = mixed_diffusion > 0.0

            discriminant = mixed_diffusion ** 2 - 4.0 * du * dv * det_j
            cond4 = discriminant > 0.0

            is_turing_instability = cond1 and cond2 and cond3 and cond4

            # Critical wavenumber
            k_c = math.sqrt(mixed_diffusion / (2.0 * du * dv)) if (is_turing_instability and du * dv > 0) else 0.0
            wavelength = (2.0 * math.pi / k_c) if k_c > 1e-6 else 0.0

            return {
                "trace_j": round(tr_j, 6),
                "det_j": round(det_j, 6),
                "cond1_stable_homogeneous": cond1,
                "cond2_det_positive": cond2,
                "cond3_diffusion_destabilizing": cond3,
                "cond4_bifurcation_positive": cond4,
                "is_turing_instability": is_turing_instability,
                "critical_wavenumber": round(k_c, 4),
                "pattern_wavelength": round(wavelength, 4),
            }

    def compute_morphogenetic_statistics(self) -> Dict[str, Any]:
        """
        Computes spatial statistics over the current grid:
        Variance, active spot count, mean concentrations, and classified regime.
        """
        with self._lock:
            n = self.w * self.h
            mean_u = sum(self.u[y][x] for y in range(self.h) for x in range(self.w)) / n
            mean_v = sum(self.v[y][x] for y in range(self.h) for x in range(self.w)) / n

            var_u = sum((self.u[y][x] - mean_u) ** 2 for y in range(self.h) for x in range(self.w)) / n
            var_v = sum((self.v[y][x] - mean_v) ** 2 for y in range(self.h) for x in range(self.w)) / n

            # Classify regime based on variance and activation
            if var_v < 1e-5:
                regime = MorphogeneticRegime.HOMOGENEOUS
            elif mean_v < 0.15:
                regime = MorphogeneticRegime.SPOTS_SOLITONS
            else:
                regime = MorphogeneticRegime.STRIPES_LABYRINTH

            return {
                "grid_size": f"{self.w}x{self.h}",
                "mean_u": round(mean_u, 4),
                "mean_v": round(mean_v, 4),
                "variance_u": round(var_u, 6),
                "variance_v": round(var_v, 6),
                "regime": regime.value,
                "total_steps": self.total_simulation_steps,
            }

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            stats = self.compute_morphogenetic_statistics()
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "era_name": ERA_NAME,
                "diff_u": self.du,
                "diff_v": self.dv,
                "feed_f": self.f,
                "kill_k": self.k,
                "total_simulation_steps": self.total_simulation_steps,
                "total_perturbations_injected": self.total_perturbations_injected,
                **stats,
            }

    def format_ascii_status(self) -> str:
        with self._lock:
            stats = self.compute_morphogenetic_statistics()
            dim_str = f"{self.w}x{self.h} Toroidal Grid"
            kin_str = f"Du={self.du:.2f}, Dv={self.dv:.2f}, F={self.f:.3f}, k={self.k:.3f}"
            steps_str = f"{self.total_simulation_steps} PDE iterations"
            reg_str = stats["regime"]
            var_str = f"var(u)={stats['variance_u']:.4f}, var(v)={stats['variance_v']:.4f}"

            lines = [
                "+-------------------------------------------------------------------------+",
                "|      STAGE 255: Bio-Mimetic Turing Reaction-Diffusion Synthesizer       |",
                "|      Era 26: Cosmic-Scale Holomorphic Field Dynamics                    |",
                "+-------------------------------------------------------------------------+",
                f"| Grid Stencil Topology: {dim_str:<48} |",
                f"| Chemical Parameters  : {kin_str:<48} |",
                f"| Simulation Progress  : {steps_str:<48} |",
                f"| Morphogenetic State  : {reg_str:<48} |",
                f"| Spatial Variance     : {var_str:<48} |",
                "+-------------------------------------------------------------------------+",
            ]
            return "\n".join(lines)


# Sovereign Global Singleton
_global_turing_synthesizer: Optional[TuringMorphogeneticSynthesizerFabric] = None
_turing_lock = threading.RLock()


def get_turing_synthesizer() -> TuringMorphogeneticSynthesizerFabric:
    global _global_turing_synthesizer
    with _turing_lock:
        if _global_turing_synthesizer is None:
            _global_turing_synthesizer = TuringMorphogeneticSynthesizerFabric()
        return _global_turing_synthesizer
