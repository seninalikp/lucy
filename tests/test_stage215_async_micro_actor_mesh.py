r"""
tests/test_stage215_async_micro_actor_mesh.py
Stage 215: Autonomous Asynchronous Actor Mesh & Sovereign Micro-Actor Scheduler
Era 22: Autonomous Galactic Hyper-Mesh, Hardware-Accelerated Photonic Emulation & Trans-Universal Reasoning Fabrics
"""

import unittest
from backend.lucy_core.async_micro_actor_mesh import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    ActorMessage,
    ActorStatus,
    AsyncMicroActorMeshFabric,
    MicroActor,
    SupervisorPolicy,
)


class TestStage215AsyncMicroActorMesh(unittest.TestCase):
    """10 Unit Tests for Stage 215 Async Micro-Actor Mesh Fabric."""

    def setUp(self):
        self.fabric = AsyncMicroActorMeshFabric()

    def test_01_fabric_initialization(self):
        self.assertEqual(STAGE, 215)
        self.assertEqual(ERA, 22)
        self.assertEqual(len(self.fabric.actors), 0)
        self.assertEqual(len(self.fabric.dead_letters), 0)
        self.assertEqual(self.fabric.supervisor_policy, SupervisorPolicy.ONE_FOR_ONE)
        self.assertEqual(self.fabric.status()["stage"], 215)

    def test_02_spawn_actor_default_behavior(self):
        actor = self.fabric.spawn_actor("actor_test_1", initial_state={"count": 0})
        self.assertIsNotNone(actor)
        self.assertEqual(actor.status, ActorStatus.ACTIVE)
        self.assertEqual(actor.state["count"], 0)
        self.assertEqual(len(actor.mailbox), 0)

    def test_03_send_message_and_mailbox_fifo(self):
        self.fabric.spawn_actor("worker_alpha")
        m1 = self.fabric.send_message("worker_alpha", "INCREMENT", "count")
        m2 = self.fabric.send_message("worker_alpha", "INCREMENT", "count")

        mailbox = self.fabric.actors["worker_alpha"].mailbox
        self.assertEqual(len(mailbox), 2)
        self.assertEqual(mailbox[0].message_id, m1.message_id)
        self.assertEqual(mailbox[1].message_id, m2.message_id)

    def test_04_step_scheduler_state_mutation(self):
        self.fabric.spawn_actor("accumulator_0")
        self.fabric.send_message("accumulator_0", "SET", {"k": "power", "v": 9000})
        self.fabric.send_message("accumulator_0", "GET", "power")

        results = self.fabric.step_scheduler()
        self.assertIn("accumulator_0", results)
        self.assertEqual(self.fabric.actors["accumulator_0"].state["power"], 9000)
        self.assertEqual(results["accumulator_0"][-1], 9000)

    def test_05_send_to_nonexistent_actor_dead_letter(self):
        msg = self.fabric.send_message("non_existent_node", "PING", {})
        self.assertEqual(len(self.fabric.dead_letters), 1)
        self.assertEqual(self.fabric.dead_letters[0].message_id, msg.message_id)

    def test_06_custom_actor_behavior(self):
        def multiplier(state, msg):
            factor = msg.payload
            state["val"] = state.get("val", 1) * factor
            return state["val"]

        self.fabric.spawn_actor("mult_actor", behavior_fn=multiplier, initial_state={"val": 5})
        self.fabric.send_message("mult_actor", "MUL", 3)
        self.fabric.send_message("mult_actor", "MUL", 2)

        res = self.fabric.step_scheduler()
        self.assertEqual(res["mult_actor"], [15, 30])
        self.assertEqual(self.fabric.actors["mult_actor"].state["val"], 30)

    def test_07_one_for_one_supervision_restart(self):
        def crashing_actor(state, msg):
            if msg.action == "CRASH":
                raise RuntimeError("Intentional Actor Crash")
            return "OK"

        self.fabric.spawn_actor("crash_worker", behavior_fn=crashing_actor)
        self.fabric.send_message("crash_worker", "CRASH", {})

        self.fabric.step_scheduler()
        # Supervised restart
        actor = self.fabric.actors["crash_worker"]
        self.assertEqual(actor.status, ActorStatus.ACTIVE)
        self.assertEqual(actor.restart_count, 1)
        self.assertEqual(self.fabric.status()["total_restarts"], 1)

    def test_08_all_for_one_supervision_policy(self):
        mesh = AsyncMicroActorMeshFabric(supervisor_policy=SupervisorPolicy.ALL_FOR_ONE)

        def unstable(state, msg):
            raise ValueError("All-For-One Trigger")

        mesh.spawn_actor("stable_1")
        mesh.spawn_actor("stable_2")
        mesh.spawn_actor("faulty", behavior_fn=unstable)

        mesh.send_message("faulty", "FAIL", {})
        mesh.step_scheduler()

        # Both stable actors and faulty should have restart_count incremented
        self.assertEqual(mesh.actors["stable_1"].restart_count, 1)
        self.assertEqual(mesh.actors["stable_2"].restart_count, 1)
        self.assertEqual(mesh.actors["faulty"].restart_count, 1)

    def test_09_max_messages_per_actor_fairness(self):
        self.fabric.spawn_actor("heavy_actor")
        for i in range(15):
            self.fabric.send_message("heavy_actor", "INCREMENT", "ticks")

        # Step with max_messages_per_actor = 5
        self.fabric.step_scheduler(max_messages_per_actor=5)
        actor = self.fabric.actors["heavy_actor"]
        self.assertEqual(actor.processed_messages, 5)
        self.assertEqual(len(actor.mailbox), 10)

    def test_10_ascii_status_formatting(self):
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 215: ASYNCHRONOUS MICRO-ACTOR MESH & SCHEDULER", tbl)
        self.assertIn("Supervision Policy", tbl)
        self.assertIn("Share-Nothing Autonomous Micro-Actors", tbl)


if __name__ == "__main__":
    unittest.main()
