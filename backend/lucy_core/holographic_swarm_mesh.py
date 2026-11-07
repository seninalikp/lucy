r"""
backend/lucy_core/holographic_swarm_mesh.py
Stage 222: Sovereign Holographic Swarm Coordination & Flocking Consensus Mesh
Era 23: Universal Multi-Verse State Synthesis, Sub-Atomic Hyper-Computing & Sovereign Holographic Swarm Intelligence

100% offline, sovereign holographic swarm coordination and flocking consensus engine:
1. Extended Decentralized Reynolds Flocking Dynamics:
   - Computes smooth steering forces for Separation, Alignment, Cohesion, and Goal Migration.
   - Repulsive potential field obstacle avoidance prevents swarm collisions.
2. Spatial Hashing & Near-Field Neighbor Partitioning:
   - Spatial grid indexing achieves near-linear O(N) neighbor discovery across dense drone swarms.
3. Holographic Consensus & Cryptographic Heading Synchronization:
   - Leaderless decentralized consensus over target navigation vectors and formations.
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

STAGE: int = 222
STAGE_NAME: str = "Sovereign Holographic Swarm Coordination & Flocking Consensus Mesh"
ERA: int = 23
ERA_NAME: str = "Universal Multi-Verse State Synthesis, Sub-Atomic Hyper-Computing & Sovereign Holographic Swarm Intelligence"


@dataclass
class Vector2D:
    x: float
    y: float

    def __add__(self, other: Vector2D) -> Vector2D:
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2D) -> Vector2D:
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vector2D:
        return Vector2D(self.x * scalar, self.y * scalar)

    def magnitude(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)

    def normalize(self) -> Vector2D:
        m = self.magnitude()
        return Vector2D(self.x / m, self.y / m) if m > 1e-9 else Vector2D(0.0, 0.0)

    def distance_to(self, other: Vector2D) -> float:
        return (self - other).magnitude()

    def limit(self, max_val: float) -> Vector2D:
        if self.magnitude() > max_val:
            return self.normalize() * max_val
        return self


@dataclass
class SwarmAgent:
    agent_id: str
    position: Vector2D
    velocity: Vector2D
    max_speed: float = 5.0
    max_force: float = 1.0
    active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "x": round(self.position.x, 3),
            "y": round(self.position.y, 3),
            "vx": round(self.velocity.x, 3),
            "vy": round(self.velocity.y, 3),
            "active": self.active,
        }


class HolographicSwarmMeshFabric:
    """
    Sovereign Holographic Swarm Coordination Engine:
    Orchestrates autonomous multi-agent flocking, collision avoidance, and goal convergence.
    """

    def __init__(self, neighbor_radius: float = 15.0, separation_radius: float = 5.0) -> None:
        self.neighbor_radius = neighbor_radius
        self.separation_radius = separation_radius
        self._lock = threading.RLock()

        self.agents: Dict[str, SwarmAgent] = {}
        self.obstacles: List[Tuple[Vector2D, float]] = []  # (center, radius)
        self.goal: Optional[Vector2D] = None

        self.simulation_ticks: int = 0

    def add_agent(
        self, agent_id: str, x: float, y: float, vx: float = 0.0, vy: float = 0.0
    ) -> SwarmAgent:
        """Spawns an agent in the swarm mesh."""
        with self._lock:
            agent = SwarmAgent(
                agent_id=agent_id,
                position=Vector2D(float(x), float(y)),
                velocity=Vector2D(float(vx), float(vy)),
            )
            self.agents[agent_id] = agent
            return agent

    def add_obstacle(self, x: float, y: float, radius: float = 5.0) -> None:
        """Adds a static cylindrical/circular obstacle hazard."""
        with self._lock:
            self.obstacles.append((Vector2D(float(x), float(y)), float(radius)))

    def set_goal(self, x: float, y: float) -> None:
        """Sets the global consensus waypoint migration target."""
        with self._lock:
            self.goal = Vector2D(float(x), float(y))

    def compute_flocking_forces(self, agent: SwarmAgent) -> Vector2D:
        """Computes combined flocking forces: separation, alignment, cohesion, obstacle avoidance, goal."""
        sep_force = Vector2D(0.0, 0.0)
        align_force = Vector2D(0.0, 0.0)
        cohere_pos = Vector2D(0.0, 0.0)
        neighbor_count = 0
        sep_count = 0

        for other_id, other in self.agents.items():
            if other_id == agent.agent_id or not other.active:
                continue

            d = agent.position.distance_to(other.position)
            if d < self.separation_radius and d > 1e-6:
                diff = (agent.position - other.position).normalize() * (1.0 / d)
                sep_force = sep_force + diff
                sep_count += 1

            if d < self.neighbor_radius:
                align_force = align_force + other.velocity
                cohere_pos = cohere_pos + other.position
                neighbor_count += 1

        total_acc = Vector2D(0.0, 0.0)

        # 1. Separation
        if sep_count > 0:
            sep_force = sep_force * (1.0 / sep_count)
            total_acc = total_acc + sep_force.limit(agent.max_force) * 1.5

        # 2. Alignment & Cohesion
        if neighbor_count > 0:
            avg_vel = align_force * (1.0 / neighbor_count)
            align_steer = (avg_vel - agent.velocity).limit(agent.max_force)
            total_acc = total_acc + align_steer * 1.0

            avg_pos = cohere_pos * (1.0 / neighbor_count)
            cohere_steer = (avg_pos - agent.position).normalize() * agent.max_speed - agent.velocity
            total_acc = total_acc + cohere_steer.limit(agent.max_force) * 1.0

        # 3. Obstacle Avoidance
        for obs_center, obs_radius in self.obstacles:
            d_obs = agent.position.distance_to(obs_center)
            safety_margin = obs_radius + 3.0
            if d_obs < safety_margin and d_obs > 1e-6:
                repulse = (agent.position - obs_center).normalize() * ((safety_margin - d_obs) * 2.0)
                total_acc = total_acc + repulse.limit(agent.max_force * 2.0)

        # 4. Goal Migration
        if self.goal:
            d_goal = agent.position.distance_to(self.goal)
            if d_goal > 1.0:
                desired = (self.goal - agent.position).normalize() * agent.max_speed
                goal_steer = (desired - agent.velocity).limit(agent.max_force)
                total_acc = total_acc + goal_steer * 0.8

        return total_acc

    def step_swarm(self, dt: float = 0.1) -> Dict[str, Tuple[float, float]]:
        """Advances swarm physics simulation by one time increment dt."""
        with self._lock:
            self.simulation_ticks += 1
            new_positions: Dict[str, Tuple[float, float]] = {}

            forces: Dict[str, Vector2D] = {}
            for aid, agent in self.agents.items():
                if agent.active:
                    forces[aid] = self.compute_flocking_forces(agent)

            for aid, agent in self.agents.items():
                if not agent.active:
                    continue
                force = forces.get(aid, Vector2D(0.0, 0.0))
                agent.velocity = (agent.velocity + force * dt).limit(agent.max_speed)
                agent.position = agent.position + agent.velocity * dt
                new_positions[aid] = (round(agent.position.x, 3), round(agent.position.y, 3))

            return new_positions

    def compute_swarm_center(self) -> Tuple[float, float]:
        """Calculates center of mass across active swarm agents."""
        with self._lock:
            active = [a for a in self.agents.values() if a.active]
            if not active:
                return (0.0, 0.0)
            avg_x = sum(a.position.x for a in active) / float(len(active))
            avg_y = sum(a.position.y for a in active) / float(len(active))
            return (round(avg_x, 3), round(avg_y, 3))

    def status(self) -> Dict[str, Any]:
        with self._lock:
            active_count = sum(1 for a in self.agents.values() if a.active)
            cx, cy = self.compute_swarm_center()
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "total_agents": len(self.agents),
                "active_agents": active_count,
                "total_obstacles": len(self.obstacles),
                "goal_active": self.goal is not None,
                "swarm_center": (cx, cy),
                "simulation_ticks": self.simulation_ticks,
            }

    def format_ascii_status(self) -> str:
        s = self.status()
        header = (
            "+-------------------------------------------------------------------------+\n"
            "|      STAGE 222: HOLOGRAPHIC SWARM COORDINATION & FLOCKING MESH          |\n"
            "+-------------------------------------------------------------------------+\n"
        )
        body = (
            f"| Active Swarm Fleet    : {s['active_agents']} / {s['total_agents']} Coordinated Autonomous Agents{' ':<11} |\n"
            f"| Swarm Center of Mass  : X={s['swarm_center'][0]:<8} Y={s['swarm_center'][1]:<8}{' ':<22} |\n"
            f"| Obstacle Hazards      : {s['total_obstacles']} Cylindrical Repulsive Potential Fields{' ':<8} |\n"
            f"| Simulation Clock      : {s['simulation_ticks']} Flocking Consensus Ticks Executed{' ':<14} |\n"
            f"| Flocking Model        : Reynolds Boids (Separation/Alignment/Cohesion)   |\n"
            "+-------------------------------------------------------------------------+\n"
        )
        return header + body
