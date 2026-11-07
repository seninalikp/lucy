r"""
tests/test_stage222_holographic_swarm_mesh.py
Stage 222: Sovereign Holographic Swarm Coordination & Flocking Consensus Mesh
Era 23: Universal Multi-Verse State Synthesis, Sub-Atomic Hyper-Computing & Sovereign Holographic Swarm Intelligence
"""

import unittest
from backend.lucy_core.holographic_swarm_mesh import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    HolographicSwarmMeshFabric,
    SwarmAgent,
    Vector2D,
)


class TestStage222HolographicSwarmMesh(unittest.TestCase):
    """10 Unit Tests for Stage 222 Holographic Swarm Mesh Fabric."""

    def setUp(self):
        self.fabric = HolographicSwarmMeshFabric(neighbor_radius=15.0, separation_radius=5.0)

    def test_01_fabric_initialization(self):
        self.assertEqual(STAGE, 222)
        self.assertEqual(ERA, 23)
        self.assertEqual(len(self.fabric.agents), 0)
        self.assertEqual(len(self.fabric.obstacles), 0)
        self.assertIsNone(self.fabric.goal)
        self.assertEqual(self.fabric.status()["stage"], 222)

    def test_02_vector2d_operations(self):
        v1 = Vector2D(3.0, 4.0)
        self.assertAlmostEqual(v1.magnitude(), 5.0, places=4)

        norm = v1.normalize()
        self.assertAlmostEqual(norm.magnitude(), 1.0, places=4)
        self.assertAlmostEqual(norm.x, 0.6, places=4)
        self.assertAlmostEqual(norm.y, 0.8, places=4)

        v2 = Vector2D(1.0, 2.0)
        add = v1 + v2
        self.assertEqual((add.x, add.y), (4.0, 6.0))
        sub = v1 - v2
        self.assertEqual((sub.x, sub.y), (2.0, 2.0))
        mul = v2 * 3.0
        self.assertEqual((mul.x, mul.y), (3.0, 6.0))

    def test_03_add_agent(self):
        agent = self.fabric.add_agent("drone_0", 10.0, 20.0, 1.0, -1.0)
        self.assertEqual(agent.agent_id, "drone_0")
        self.assertEqual((agent.position.x, agent.position.y), (10.0, 20.0))
        self.assertEqual(len(self.fabric.agents), 1)

    def test_04_step_swarm_single_agent(self):
        self.fabric.add_agent("drone_solo", 0.0, 0.0, 2.0, 0.0)
        # 1 step with dt=0.5 -> pos.x becomes 1.0
        pos = self.fabric.step_swarm(dt=0.5)
        self.assertAlmostEqual(pos["drone_solo"][0], 1.0, places=2)
        self.assertAlmostEqual(pos["drone_solo"][1], 0.0, places=2)

    def test_05_separation_repulsion(self):
        # Two agents extremely close at x=0.0 and x=1.0 (separation_radius=5.0)
        a1 = self.fabric.add_agent("left", 0.0, 0.0)
        a2 = self.fabric.add_agent("right", 1.0, 0.0)

        self.fabric.step_swarm(dt=0.2)
        # Left should be pushed left (negative x), right pushed right (positive x)
        self.assertLess(a1.position.x, 0.0)
        self.assertGreater(a2.position.x, 1.0)

    def test_06_goal_seeking_migration(self):
        self.fabric.add_agent("scout", 0.0, 0.0)
        self.fabric.set_goal(100.0, 100.0)

        # Run 10 steps
        for _ in range(10):
            self.fabric.step_swarm(dt=0.2)

        # Agent should have moved towards positive quadrant
        scout = self.fabric.agents["scout"]
        self.assertGreater(scout.position.x, 0.0)
        self.assertGreater(scout.position.y, 0.0)

    def test_07_obstacle_avoidance(self):
        agent = self.fabric.add_agent("traveler", 0.0, 0.0, 2.0, 0.0)
        # Obstacle placed right ahead at (5.0, 0.0)
        self.fabric.add_obstacle(5.0, 0.0, radius=2.0)
        self.fabric.set_goal(20.0, 0.0)

        force = self.fabric.compute_flocking_forces(agent)
        # Should have repulsive force pushing back or away from obstacle
        self.assertNotEqual(force.magnitude(), 0.0)

    def test_08_compute_swarm_center(self):
        self.fabric.add_agent("a1", 10.0, 20.0)
        self.fabric.add_agent("a2", 30.0, 40.0)
        cx, cy = self.fabric.compute_swarm_center()
        self.assertAlmostEqual(cx, 20.0, places=2)
        self.assertAlmostEqual(cy, 30.0, places=2)

    def test_09_inactive_agent_ignored(self):
        a = self.fabric.add_agent("sleeping_drone", 5.0, 5.0, 1.0, 1.0)
        a.active = False
        pos = self.fabric.step_swarm(dt=1.0)
        self.assertNotIn("sleeping_drone", pos)
        self.assertEqual((a.position.x, a.position.y), (5.0, 5.0))

    def test_10_ascii_status_formatting(self):
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 222: HOLOGRAPHIC SWARM COORDINATION & FLOCKING MESH", tbl)
        self.assertIn("Active Swarm Fleet", tbl)
        self.assertIn("Reynolds Boids (Separation/Alignment/Cohesion)", tbl)


if __name__ == "__main__":
    unittest.main()
