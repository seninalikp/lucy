r"""
tests/test_stage151_microkernel_scheduler.py
Stage 151 Test Suite: Sovereign Microkernel Architecture & TCB Scheduler
Era 16: Autonomous Microkernel, Bare-Metal HAL & Sovereign Operating System Primitives
"""

import unittest

from backend.lucy_core.microkernel_scheduler import (
    CREATOR,
    ERA,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    MicrokernelScheduler,
    TaskControlBlock,
    TaskPriority,
    TaskState,
    get_microkernel_scheduler,
)


class TestStage151MicrokernelScheduler(unittest.TestCase):
    def setUp(self) -> None:
        self.sched = MicrokernelScheduler()

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 151)
        self.assertEqual(ERA, 16)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")
        self.assertEqual(
            STAGE_NAME,
            "Sovereign Microkernel Architecture & TCB Scheduler",
        )

    def test_02_idle_task_initialization(self) -> None:
        self.assertIn(0, self.sched.all_tasks)
        idle = self.sched.all_tasks[0]
        self.assertEqual(idle.name, "system_idle")
        self.assertEqual(idle.priority, TaskPriority.IDLE)
        self.assertEqual(idle.state, TaskState.READY)

    def test_03_task_creation_and_tcb(self) -> None:
        tcb = self.sched.create_task("worker_alpha", priority=TaskPriority.HIGH, quantum=15)
        self.assertEqual(tcb.task_id, 1)
        self.assertEqual(tcb.name, "worker_alpha")
        self.assertEqual(tcb.priority, TaskPriority.HIGH)
        self.assertEqual(tcb.quantum_remaining, 15)
        self.assertEqual(tcb.state, TaskState.READY)
        self.assertTrue(tcb.stack_base > 0)
        self.assertEqual(tcb.registers.rsp, tcb.stack_base + tcb.stack_size)

    def test_04_schedule_tick_dispatch(self) -> None:
        tcb = self.sched.create_task("calc_task", priority=TaskPriority.NORMAL, quantum=5)
        running = self.sched.schedule_tick()
        self.assertEqual(running.task_id, tcb.task_id)
        self.assertEqual(running.state, TaskState.RUNNING)
        self.assertEqual(running.quantum_remaining, 4)
        self.assertEqual(running.total_cpu_ticks, 1)

    def test_05_priority_preemption(self) -> None:
        # Start low priority task
        low = self.sched.create_task("low_prio", priority=TaskPriority.NORMAL, quantum=10)
        cur = self.sched.schedule_tick()
        self.assertEqual(cur.task_id, low.task_id)

        # Enqueue high priority task
        high = self.sched.create_task("high_prio", priority=TaskPriority.REALTIME, quantum=10)
        # Next tick should preempt low_prio
        next_run = self.sched.schedule_tick()
        self.assertEqual(next_run.task_id, high.task_id)
        self.assertEqual(low.state, TaskState.READY)

    def test_06_round_robin_quantum_exhaustion(self) -> None:
        t1 = self.sched.create_task("rr1", priority=TaskPriority.NORMAL, quantum=2)
        t2 = self.sched.create_task("rr2", priority=TaskPriority.NORMAL, quantum=2)

        # Tick 1: t1 runs (quantum: 2 -> 1)
        r1 = self.sched.schedule_tick()
        self.assertEqual(r1.task_id, t1.task_id)
        self.assertEqual(t1.quantum_remaining, 1)

        # Tick 2: t1 runs (quantum: 1 -> 0, moves to back of queue)
        r2 = self.sched.schedule_tick()
        self.assertEqual(r2.task_id, t1.task_id)

        # Tick 3: t2 runs (t1 was rotated to back)
        r3 = self.sched.schedule_tick()
        self.assertEqual(r3.task_id, t2.task_id)

    def test_07_sleep_and_wakeup_queue(self) -> None:
        t = self.sched.create_task("sleeper", priority=TaskPriority.HIGH, quantum=10)
        self.sched.schedule_tick()  # sleeper starts running

        self.sched.sleep_task(t.task_id, ticks=3)
        self.assertEqual(t.state, TaskState.SLEEPING)

        # For 2 ticks, sleeper should remain sleeping
        self.sched.schedule_tick()
        self.assertEqual(t.state, TaskState.SLEEPING)
        self.sched.schedule_tick()
        self.assertEqual(t.state, TaskState.SLEEPING)

        # On 3rd tick, sleeper wakes up and becomes READY
        self.sched.schedule_tick()
        self.assertIn(t.state, (TaskState.READY, TaskState.RUNNING))

    def test_08_block_and_unblock(self) -> None:
        t = self.sched.create_task("blocker", priority=TaskPriority.HIGH)
        self.sched.schedule_tick()

        ok_block = self.sched.block_task(t.task_id, reason="waiting on IPC")
        self.assertTrue(ok_block)
        self.assertEqual(t.state, TaskState.BLOCKED)

        # Running tick should fall back to idle (or other tasks)
        idle_or_other = self.sched.schedule_tick()
        self.assertNotEqual(idle_or_other.task_id, t.task_id)

        ok_unblock = self.sched.unblock_task(t.task_id)
        self.assertTrue(ok_unblock)
        self.assertEqual(t.state, TaskState.READY)

    def test_09_voluntary_yield_and_termination(self) -> None:
        t1 = self.sched.create_task("yielder", priority=TaskPriority.NORMAL, quantum=20)
        t2 = self.sched.create_task("other", priority=TaskPriority.NORMAL, quantum=20)
        self.sched.schedule_tick()

        # t1 yields
        ok_yield = self.sched.yield_task(t1.task_id)
        self.assertTrue(ok_yield)

        # Terminate t1
        ok_term = self.sched.terminate_task(t1.task_id, exit_code=0)
        self.assertTrue(ok_term)
        self.assertEqual(t1.state, TaskState.TERMINATED)

    def test_10_ascii_presentation_and_simulation(self) -> None:
        self.sched.create_task("sim_task1", priority=TaskPriority.NORMAL)
        self.sched.create_task("sim_task2", priority=TaskPriority.HIGH)

        res = self.sched.run_simulation(ticks=15)
        self.assertEqual(res["current_tick"], 15)
        self.assertTrue(res["context_switches"] >= 1)

        status = self.sched.format_ascii_status()
        self.assertIn("LUCY STAGE 151", status)
        self.assertIn("Senin", status)
        self.assertIn("sim_task1", status)
        self.assertIn("sim_task2", status)


if __name__ == "__main__":
    unittest.main()
