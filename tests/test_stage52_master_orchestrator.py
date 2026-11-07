"""
test_stage52_master_orchestrator.py
Stage 52 = Master Orchestrator / Multi-Step Goal DAG Loop.

Verifies:
1. Orchestrator reports Stage 52 and ready status with complete schema.
2. Goal DAG topological sorting and cycle detection exception.
3. Step readiness evaluation and mathematical progress calculation.
4. Pre-built goal template factories (code_tool, night_audit, health_recovery).
5. Successful end-to-end multi-step DAG execution with context propagation.
6. Graceful failure handling and downstream dependency skipping.
7. ASCII progress tree formatting with visual status symbols.
8. Goal checkpoint persistence on disk and execution history logging.
9. Full integration with CommandRouter and LucyRuntime.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.master_orchestrator import (
    DAGStep,
    GoalDAG,
    GoalStatus,
    GoalTemplates,
    MasterOrchestrator,
    StepStatus,
    STAGE,
)
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class MockRuntime:
    """Mock runtime for testing orchestrator step dispatch."""
    def __init__(self) -> None:
        self.actions = []

    def system_telemetry(self) -> dict:
        self.actions.append("telemetry")
        return {"ram": {"memory_load_percent": 35}}

    def scan_workspace_now(self) -> dict:
        self.actions.append("sentinel_scan")
        return {"total_tracked": 120}

    def auto_heal_system(self) -> dict:
        self.actions.append("auto_heal")
        return {"current_health": "HEALTHY"}

    def create_system_backups(self) -> dict:
        self.actions.append("create_backups")
        return {"total_backed_up": 8}


class Stage52MasterOrchestratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.project_root = self.tmp_path / "project"
        self.lucy_data = self.project_root / "data" / "lucy"

        self.project_root.mkdir(parents=True, exist_ok=True)
        self.lucy_data.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        try:
            self.tmp.cleanup()
        except Exception:
            pass

    def test_stage_identity_and_status(self) -> None:
        """1. Orchestrator reports Stage 52 and ready status with complete schema."""
        orch = MasterOrchestrator(
            project_root=self.project_root,
            lucy_data=self.lucy_data,
        )
        status = orch.status()
        self.assertEqual(status["stage"], "52 master orchestrator goal dag loop")
        self.assertEqual(status["status"], "ready")
        self.assertIn("goals_executed", status)
        self.assertIn("templates_available", status)

    def test_goal_dag_topological_sort(self) -> None:
        """2. Goal DAG topological sorting and cycle detection exception."""
        dag = GoalDAG(title="Test Sort DAG")
        dag.add_step(DAGStep("step_c", "Step C", "CUSTOM", dependencies=["step_b"]))
        dag.add_step(DAGStep("step_a", "Step A", "CUSTOM"))
        dag.add_step(DAGStep("step_b", "Step B", "CUSTOM", dependencies=["step_a"]))

        order = dag.topological_sort()
        self.assertEqual(order, ["step_a", "step_b", "step_c"])

        # Cycle detection
        dag_cycle = GoalDAG(title="Cycle DAG")
        dag_cycle.add_step(DAGStep("n1", "Node 1", "CUSTOM", dependencies=["n2"]))
        dag_cycle.add_step(DAGStep("n2", "Node 2", "CUSTOM", dependencies=["n1"]))
        with self.assertRaises(ValueError):
            dag_cycle.topological_sort()

    def test_goal_dag_readiness_and_progress(self) -> None:
        """3. Step readiness evaluation and mathematical progress calculation."""
        dag = GoalDAG(title="Readiness Test")
        dag.add_step(DAGStep("s1", "First", "CUSTOM"))
        dag.add_step(DAGStep("s2", "Second", "CUSTOM", dependencies=["s1"]))

        # Initially s1 is ready, s2 is not
        ready = dag.get_ready_steps()
        self.assertEqual(len(ready), 1)
        self.assertEqual(ready[0].step_id, "s1")

        # Mark s1 complete
        dag.steps["s1"].status = StepStatus.COMPLETED
        ready2 = dag.get_ready_steps()
        self.assertEqual(len(ready2), 1)
        self.assertEqual(ready2[0].step_id, "s2")

        # Progress stats
        prog = dag.progress_summary()
        self.assertEqual(prog["total"], 2)
        self.assertEqual(prog["completed"], 1)
        self.assertEqual(prog["percent"], 50.0)

    def test_goal_templates_instantiation(self) -> None:
        """4. Pre-built goal template factories (code_tool, night_audit, health_recovery)."""
        code_dag = GoalTemplates.code_tool_workflow("Build Tool", "make a disk cleaner")
        self.assertEqual(code_dag.template_name, "code_tool")
        self.assertIn("plan", code_dag.steps)
        self.assertIn("synthesize", code_dag.steps)
        self.assertIn("ast_verify", code_dag.steps)
        self.assertIn("test_execute", code_dag.steps)
        self.assertIn("promote", code_dag.steps)

        audit_dag = GoalTemplates.night_audit_workflow()
        self.assertEqual(audit_dag.template_name, "night_audit")
        self.assertIn("telemetry", audit_dag.steps)
        self.assertIn("sentinel_scan", audit_dag.steps)

        recovery_dag = GoalTemplates.health_recovery_workflow()
        self.assertEqual(recovery_dag.template_name, "health_recovery")
        self.assertIn("probe_health", recovery_dag.steps)
        self.assertIn("auto_heal", recovery_dag.steps)

    def test_dag_execution_success_flow(self) -> None:
        """5. Successful end-to-end multi-step DAG execution with context propagation."""
        mock_rt = MockRuntime()
        orch = MasterOrchestrator(
            project_root=self.project_root,
            lucy_data=self.lucy_data,
            runtime=mock_rt,
        )

        dag = GoalTemplates.night_audit_workflow()
        res = orch.execute_dag(dag)

        self.assertTrue(res["ok"])
        self.assertEqual(res["status"], GoalStatus.COMPLETED)
        self.assertEqual(res["progress"]["completed"], res["progress"]["total"])
        self.assertIn("telemetry", mock_rt.actions)
        self.assertIn("sentinel_scan", mock_rt.actions)
        self.assertIn("auto_heal", mock_rt.actions)

    def test_dag_execution_step_failure_and_skip(self) -> None:
        """6. Graceful failure handling and downstream dependency skipping."""
        orch = MasterOrchestrator(
            project_root=self.project_root,
            lucy_data=self.lucy_data,
        )

        dag = GoalDAG(title="Fail Test DAG")
        dag.add_step(DAGStep("failing_step", "Fails intentionally", "CUSTOM", max_retries=0))
        dag.add_step(DAGStep("dependent_step", "Should be skipped", "CUSTOM", dependencies=["failing_step"]))

        # Force failing step behavior by injecting invalid action
        class FailOrchestrator(MasterOrchestrator):
            def _execute_step(self, step: DAGStep, dag: GoalDAG) -> dict:
                if step.step_id == "failing_step":
                    return {"ok": False, "error": "Simulated hardware fault"}
                return {"ok": True}

        f_orch = FailOrchestrator(project_root=self.project_root, lucy_data=self.lucy_data)
        res = f_orch.execute_dag(dag)

        self.assertFalse(res["ok"])
        self.assertEqual(dag.steps["failing_step"].status, StepStatus.FAILED)
        self.assertEqual(dag.steps["dependent_step"].status, StepStatus.SKIPPED)

    def test_ascii_tree_rendering(self) -> None:
        """7. ASCII progress tree formatting with visual status symbols."""
        dag = GoalDAG(title="Render Test")
        s1 = DAGStep("step1", "Initialize workspace", "CUSTOM")
        s1.status = StepStatus.COMPLETED
        s1.elapsed_ms = 45.2
        dag.add_step(s1)

        tree = dag.render_ascii_tree()
        self.assertIn("Goal: Render Test", tree)
        self.assertIn("[OK]  1. step1", tree)
        self.assertIn("(45.2ms)", tree)

    def test_goal_persistence_and_history(self) -> None:
        """8. Goal checkpoint persistence on disk and execution history logging."""
        orch = MasterOrchestrator(
            project_root=self.project_root,
            lucy_data=self.lucy_data,
        )
        dag = GoalTemplates.health_recovery_workflow()
        res = orch.execute_dag(dag)

        # Check history
        history = orch.list_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["goal_id"], dag.goal_id)

        # Check details from disk
        details = orch.get_goal_details(dag.goal_id)
        self.assertIsNotNone(details)
        self.assertEqual(details["goal_id"], dag.goal_id)
        self.assertEqual(details["status"], GoalStatus.COMPLETED)

    def test_lucy_runtime_and_router_integration(self) -> None:
        """9. Full integration with CommandRouter and LucyRuntime."""
        runtime = LucyRuntime(project_root=Path(r"C:\Users\admin\Desktop\senin\LUCY\lucy"))
        router = CommandRouter(runtime)

        # Orchestrator status via router
        resp_stat = router.handle("/orchestrator status")
        self.assertIn("Master Orchestrator DAG Status:", resp_stat.message)
        self.assertIn("52 master orchestrator goal dag loop", resp_stat.message)

        # Execute goal via router
        resp_goal = router.handle("/goal perform night audit")
        self.assertIn("Master Orchestrator Execution", resp_goal.message)
        self.assertIn("Goal:", resp_goal.message)

        # Goal history via router
        resp_hist = router.handle("/goals")
        self.assertIn("Master Orchestrator Goal History", resp_hist.message)

        # Direct runtime methods
        status_dict = runtime.orchestrator_status()
        self.assertEqual(status_dict["stage"], STAGE)


if __name__ == "__main__":
    unittest.main()
