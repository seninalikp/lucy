r"""
tests/test_stage114_agent_pipeline_fusion.py
Comprehensive test suite for Stage 114: Parallel Pipeline Fusion
Era 12: The Autonomous Cognitive Matrix & Distributed IPC Fabric
"""

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.agent_pipeline_fusion import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    STAGE,
    AgentPipelineFusionEngine,
    PipelineDAG,
    PipelineResult,
    PipelineStep,
    StepStatus,
)


class MockReceiptLedger:
    def __init__(self) -> None:
        self.receipts = []

    def record_receipt(self, action_category: str, operation: str, target: str, verified_outcome: str):
        rcpt = {
            "action_category": action_category,
            "operation": operation,
            "target": target,
            "verified_outcome": verified_outcome,
        }
        self.receipts.append(rcpt)
        return rcpt


class TestStage114AgentPipelineFusion(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.data_dir = self.root / "data" / "pipeline"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.receipt_ledger = MockReceiptLedger()

        self.engine = AgentPipelineFusionEngine(
            project_root=self.root,
            data_dir=self.data_dir,
            receipt_ledger=self.receipt_ledger,
            max_workers=4,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_01_initialization(self) -> None:
        st = self.engine.status()
        self.assertEqual(st["stage"], 114)
        self.assertEqual(st["era"], 12)
        self.assertEqual(st["creator"], CREATOR_NAME)
        self.assertEqual(st["creator_full_name"], CREATOR_FULL_NAME)
        self.assertEqual(st["total_executed"], 0)

    def test_02_linear_dag_layers(self) -> None:
        dag = PipelineDAG(pipeline_id="linear", name="linear_test")
        dag.add_step("s1", "agent1")
        dag.add_step("s2", "agent2", dependencies=["s1"])
        dag.add_step("s3", "agent3", dependencies=["s2"])

        layers = dag.validate_and_compute_layers()
        self.assertEqual(layers, [["s1"], ["s2"], ["s3"]])

    def test_03_fan_out_fan_in_dag(self) -> None:
        dag = PipelineDAG(pipeline_id="diamond", name="diamond_test")
        dag.add_step("start", "starter")
        dag.add_step("branch_a", "worker_a", dependencies=["start"])
        dag.add_step("branch_b", "worker_b", dependencies=["start"])
        dag.add_step("join", "joiner", dependencies=["branch_a", "branch_b"])

        layers = dag.validate_and_compute_layers()
        self.assertEqual(len(layers), 3)
        self.assertEqual(layers[0], ["start"])
        self.assertCountEqual(layers[1], ["branch_a", "branch_b"])
        self.assertEqual(layers[2], ["join"])

    def test_04_cycle_detection(self) -> None:
        dag = PipelineDAG(pipeline_id="cyclic", name="cyclic_test")
        dag.add_step("a", "agent_a", dependencies=["b"])
        dag.add_step("b", "agent_b", dependencies=["a"])

        with self.assertRaises(ValueError) as ctx:
            dag.validate_and_compute_layers()
        self.assertIn("Circular dependency detected", str(ctx.exception))

    def test_05_missing_dependency(self) -> None:
        dag = PipelineDAG(pipeline_id="broken", name="broken_test")
        dag.add_step("a", "agent_a", dependencies=["ghost_step"])

        with self.assertRaises(ValueError) as ctx:
            dag.validate_and_compute_layers()
        self.assertIn("depends on non-existent step", str(ctx.exception))

    def test_06_execute_successful_pipeline(self) -> None:
        dag = PipelineDAG(pipeline_id="exec_test", name="math_fusion")
        dag.add_step("init", "init", handler=lambda ctx: 10)
        dag.add_step("double", "calc", dependencies=["init"], handler=lambda ctx: ctx["step_init_output"] * 2)
        dag.add_step("square", "calc", dependencies=["init"], handler=lambda ctx: ctx["step_init_output"] ** 2)
        dag.add_step("sum", "reduce", dependencies=["double", "square"], handler=lambda ctx: ctx["step_double_output"] + ctx["step_square_output"])

        res = self.engine.execute_pipeline(dag)
        self.assertTrue(res.success)
        self.assertEqual(res.completed_steps, 4)
        self.assertEqual(res.failed_steps, 0)
        self.assertEqual(res.skipped_steps, 0)
        self.assertEqual(res.step_results["sum"], 120)  # 20 + 100

    def test_07_step_failure_and_skip(self) -> None:
        dag = PipelineDAG(pipeline_id="fail_test", name="failure_flow")
        dag.add_step("step1", "starter", handler=lambda ctx: "ok")
        def buggy(ctx):
            raise RuntimeError("Database connection timed out")
        dag.add_step("step2", "buggy", dependencies=["step1"], handler=buggy)
        dag.add_step("step3", "dependent", dependencies=["step2"], handler=lambda ctx: "never_reached")

        res = self.engine.execute_pipeline(dag)
        self.assertFalse(res.success)
        self.assertEqual(res.completed_steps, 1)
        self.assertEqual(res.failed_steps, 1)
        self.assertEqual(res.skipped_steps, 1)
        self.assertIn("step2", res.error)

    def test_08_retry_policy(self) -> None:
        attempts = {"count": 0}
        def flaky_handler(ctx):
            attempts["count"] += 1
            if attempts["count"] < 2:
                raise ValueError("Transient glitch")
            return "recovered_value"

        dag = PipelineDAG(pipeline_id="retry_test", name="flaky_flow")
        dag.add_step("flaky", "resilient_agent", handler=flaky_handler, retry_count=3)

        res = self.engine.execute_pipeline(dag)
        self.assertTrue(res.success)
        self.assertEqual(res.step_results["flaky"], "recovered_value")
        self.assertEqual(attempts["count"], 2)

    def test_09_code_refactor_template(self) -> None:
        dag = self.engine.create_refactor_fusion_pipeline("runtime_core.py")
        self.assertEqual(dag.name, "code_refactor_fusion")
        self.assertEqual(len(dag.steps), 6)

        res = self.engine.execute_pipeline(dag)
        self.assertTrue(res.success)
        self.assertEqual(res.completed_steps, 6)
        self.assertEqual(res.layers_executed, 4)
        self.assertIn("Consensus achieved", res.step_results["final_fusion"])

    def test_10_workspace_audit_template(self) -> None:
        dag = self.engine.create_workspace_audit_pipeline()
        self.assertEqual(dag.name, "workspace_audit_fusion")
        self.assertEqual(len(dag.steps), 5)

        res = self.engine.execute_pipeline(dag)
        self.assertTrue(res.success)
        self.assertEqual(res.completed_steps, 5)
        self.assertEqual(res.layers_executed, 3)
        self.assertIn("Workspace health attestation", res.step_results["healing_proposal"])

    def test_11_receipt_ledger_integration(self) -> None:
        dag = self.engine.create_workspace_audit_pipeline()
        self.engine.execute_pipeline(dag)

        cats = [r["action_category"] for r in self.receipt_ledger.receipts]
        self.assertIn("PIPELINE_FUSION_START", cats)
        self.assertIn("PIPELINE_STEP_COMPLETE", cats)
        self.assertIn("PIPELINE_FUSION_FINISH", cats)

    def test_12_persistence_and_reload(self) -> None:
        dag = self.engine.create_workspace_audit_pipeline()
        self.engine.execute_pipeline(dag)

        # Create new engine instance
        engine2 = AgentPipelineFusionEngine(
            project_root=self.root,
            data_dir=self.data_dir,
        )
        self.assertEqual(engine2._total_executed, 1)
        self.assertEqual(engine2._successful_executed, 1)

    def test_13_ascii_table_formatting(self) -> None:
        dag = self.engine.create_refactor_fusion_pipeline("test.py")
        self.engine.execute_pipeline(dag)

        tbl = self.engine.format_pipeline_status_table()
        self.assertIn("LUCY OS - PARALLEL PIPELINE FUSION", tbl)
        self.assertIn("Total Fused Pipelines Executed", tbl)
        self.assertIn(CREATOR_NAME, tbl)
        self.assertTrue(tbl.startswith("+--"))

        dag_vis = self.engine.format_dag_visualization(dag)
        self.assertIn("[Pipeline DAG Visualization]", dag_vis)
        self.assertIn("L0", dag_vis)


if __name__ == "__main__":
    unittest.main()
