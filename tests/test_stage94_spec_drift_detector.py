"""
tests/test_stage94_spec_drift_detector.py
Stage 94 = Architecture Specification Drift Detector & Realignment Engine

Verifies:
1. STAGE constant is 94.
2. ArchitectureSpecRegistry defines all 8 default architectural invariants.
3. Identity invariant compliance verifies Creator and Operator is Senin (Senin Ali K P).
4. Drift detection flags corrupted identity and realign_spec() autonomously repairs it.
5. CP1252 console encoding validator checks for ASCII borders (+, -, |).
6. Core runtime subsystems audit checks engine lifecycle presence.
7. Router contracts audit verifies stage command registration.
8. Stage cadence audit verifies sequential test continuity.
9. Full audit execution generates scored DriftReport with disk persistence.
10. Execution receipt ledger records receipts for audits and realignments.
11. Terminal summary uses strictly CP1252-compatible ASCII characters.
12. Status reporting returns expected diagnostic dictionary.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.lucy_core.spec_drift_detector import (
    STAGE,
    ArchitectureSpecRegistry,
    DriftItem,
    DriftReport,
    DriftSeverity,
    SpecCategory,
    SpecDriftDetector,
    SpecInvariant,
)


class MockReceiptLedger:
    def __init__(self) -> None:
        self.receipts: List[Dict[str, Any]] = []

    def issue_receipt(
        self,
        action_category: str,
        operation: str,
        target: str,
        verified_outcome: str,
    ) -> Dict[str, Any]:
        rcpt = {
            "action_category": action_category,
            "operation": operation,
            "target": target,
            "verified_outcome": verified_outcome,
        }
        self.receipts.append(rcpt)
        return rcpt


class MockRuntime:
    def __init__(self) -> None:
        self.receipt_ledger = MockReceiptLedger()
        self.workspace_sensor = object()
        self.proactive_briefer = object()
        self.atomic_patcher = object()
        self.mutation_fuzzer = object()
        self.self_healing_patcher = object()
        self.ast_vector_index = object()
        self.spec_drift_detector = object()
        self.worktree_fabric = object()
        self.model_quantizer = object()
        self.causal_dag = object()
        self.host_sandbox = object()
        self.hardware_telemetry = object()
        self.master_seal = object()
        self.kernel_supervisor = object()
        self.execution_profiler = object()
        self.neural_retriever = object()
        self.refactor_engine = object()
        self.peer_mesh = object()
        self.voice_fabric = object()
        self.token_compressor = object()
        self.red_team = object()
        self.ambient_hud = object()
        self.consensus_nexus = object()
        self.workspace_daemon = object()
        self.semantic_cache = object()
        self.polyglot_ast = object()
        self.pipeline_fusion = object()
        self.ipc_bus = object()
        self.local_vector_db = object()
        self.git_ops = object()
        self.thermal_governor = object()
        self.dream_consolidator = object()
        self.era12_seal = object()
        self.knowledge_graph = object()
        self.counterfactual_simulator = object()
        self.goal_decomposer = object()
        self.verification_oracle = object()
        self.concept_miner = object()
        self.context_budgeter = object()
        self.protocol_synthesizer = object()
        self.meta_policy_refiner = object()
        self.mesh_gateway = object()
        self.era13_seal = object()
        self.ast_mutator = object()
        self.test_oracle = object()
        self.constraint_solver = object()
        self.bytecode_inspector = object()
        self.ffi_linker = object()
        self.wheel_fabric = object()


class TestStage94SpecDriftDetector(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        # Create basic directory structure
        (self.root / "data" / "lucy").mkdir(parents=True, exist_ok=True)
        (self.root / "backend" / "lucy_core").mkdir(parents=True, exist_ok=True)
        (self.root / "tests").mkdir(parents=True, exist_ok=True)

        # Baseline personal profile
        profile_data = {
            "user_name": "Senin",
            "full_name": "Senin Ali K P",
            "preferred_name": "Senin",
            "creator": "Senin",
            "role": "AI Systems Builder, Software Developer, and Product Architect",
        }
        (self.root / "data" / "personal_profile.json").write_text(
            json.dumps(profile_data, indent=2), encoding="utf-8"
        )

        # Baseline connector file
        (self.root / "backend" / "lucy_core" / "ollama_connector.py").write_text(
            'DEFAULT_SOVEREIGN_MODEL = "qwen2.5:3b"\n', encoding="utf-8"
        )

        # Baseline router file
        (self.root / "backend" / "lucy_core" / "router.py").write_text(
            '# /fuzz /heal /index-repo /code-search /symbol-tree /spec-audit /drift-report /realign-spec\n',
            encoding="utf-8",
        )

        # Baseline safety files
        (self.root / "backend" / "lucy_core" / "autonomy_boundaries.py").write_text(
            '# autonomy boundaries\n', encoding="utf-8"
        )
        (self.root / "backend" / "lucy_core" / "tool_policy.py").write_text(
            '# tool policy\n', encoding="utf-8"
        )

        # Baseline stage test files
        (self.root / "tests" / "test_stage91_mutation_fuzzer.py").write_text("# s91", encoding="utf-8")
        (self.root / "tests" / "test_stage92_self_healing_patcher.py").write_text("# s92", encoding="utf-8")
        (self.root / "tests" / "test_stage93_ast_vector_index.py").write_text("# s93", encoding="utf-8")

        self.mock_ledger = MockReceiptLedger()
        self.detector = SpecDriftDetector(
            project_root=self.root,
            receipt_ledger=self.mock_ledger,
            data_dir=self.root / "data" / "lucy" / "spec_drift",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_01_stage_constant(self) -> None:
        self.assertEqual(STAGE, 94)

    def test_02_default_invariants_registry(self) -> None:
        invariants = ArchitectureSpecRegistry.get_default_invariants()
        self.assertEqual(len(invariants), 8)
        spec_ids = [inv.spec_id for inv in invariants]
        expected_ids = [f"SPEC-0{i}" for i in range(1, 9)]
        self.assertEqual(spec_ids, expected_ids)

        # Verify critical severities
        ident_inv = next(i for i in invariants if i.spec_id == "SPEC-01")
        self.assertEqual(ident_inv.category, SpecCategory.IDENTITY)
        self.assertEqual(ident_inv.severity, DriftSeverity.CRITICAL)
        self.assertTrue(ident_inv.is_realignable)

    def test_03_identity_compliance(self) -> None:
        inv = next(i for i in self.detector.invariants if i.spec_id == "SPEC-01")
        compliant, details, detected, expected = inv.check_fn(self.root, None)
        self.assertTrue(compliant)
        self.assertIn("Senin", details)
        self.assertIn("Senin Ali K P", details)

    def test_04_identity_drift_detection_and_realignment(self) -> None:
        profile_path = self.root / "data" / "personal_profile.json"
        # Corrupt identity
        corrupted = {
            "user_name": "ForeignOperator",
            "full_name": "Unknown Entity",
            "creator": "Imposter",
        }
        profile_path.write_text(json.dumps(corrupted, indent=2), encoding="utf-8")

        # Run audit - drift must be detected
        report = self.detector.audit()
        self.assertGreater(report.drifted_specs, 0)
        self.assertGreater(report.critical_drifts, 0)
        self.assertLess(report.compliance_score, 100.0)

        # Verify drift item
        drift_item = next(it for it in report.items if it.spec_id == "SPEC-01")
        self.assertEqual(drift_item.severity, "CRITICAL")
        self.assertEqual(drift_item.category, "IDENTITY")
        self.assertTrue(drift_item.is_realignable)

        # Run realignment
        res = self.detector.realign_spec("SPEC-01")
        self.assertIn("SPEC-01", res["realigned_specs"])

        # Check restored profile
        restored = json.loads(profile_path.read_text(encoding="utf-8"))
        self.assertEqual(restored["user_name"], "Senin")
        self.assertEqual(restored["full_name"], "Senin Ali K P")
        self.assertEqual(restored["creator"], "Senin")

    def test_05_encoding_compliance(self) -> None:
        inv = next(i for i in self.detector.invariants if i.spec_id == "SPEC-03")
        compliant, details, detected, expected = inv.check_fn(self.root, None)
        self.assertTrue(compliant)

    def test_06_runtime_subsystems_audit(self) -> None:
        inv = next(i for i in self.detector.invariants if i.spec_id == "SPEC-04")
        mock_rt = MockRuntime()
        compliant, details, detected, expected = inv.check_fn(self.root, mock_rt)
        self.assertTrue(compliant)

        # Test missing engine
        class BrokenRuntime:
            pass

        broken_rt = BrokenRuntime()
        compliant_b, details_b, _, _ = inv.check_fn(self.root, broken_rt)
        self.assertFalse(compliant_b)
        self.assertIn("Missing", details_b)

    def test_07_router_contracts_audit(self) -> None:
        inv = next(i for i in self.detector.invariants if i.spec_id == "SPEC-05")
        compliant, details, _, _ = inv.check_fn(self.root, None)
        self.assertTrue(compliant)

        # Test missing router command
        (self.root / "backend" / "lucy_core" / "router.py").write_text("# empty\n", encoding="utf-8")
        compliant_empty, details_empty, _, _ = inv.check_fn(self.root, None)
        self.assertFalse(compliant_empty)

    def test_08_stage_continuity_audit(self) -> None:
        inv = next(i for i in self.detector.invariants if i.spec_id == "SPEC-06")
        compliant, details, _, _ = inv.check_fn(self.root, None)
        self.assertTrue(compliant)

    def test_09_full_audit_execution_and_persistence(self) -> None:
        mock_rt = MockRuntime()
        report = self.detector.audit(runtime=mock_rt)
        self.assertEqual(report.total_specs, 8)
        self.assertEqual(report.passed_specs, 8)
        self.assertEqual(report.compliance_score, 100.0)
        self.assertEqual(report.drifted_specs, 0)

        # Verify disk persistence
        self.assertTrue(self.detector.report_file.exists())
        saved_data = json.loads(self.detector.report_file.read_text(encoding="utf-8"))
        self.assertEqual(saved_data["compliance_score"], 100.0)

        # Verify reload from disk
        reloaded = self.detector._load_last_report()
        self.assertIsNotNone(reloaded)
        self.assertEqual(reloaded.total_specs, 8)

    def test_10_receipt_ledger_emission(self) -> None:
        mock_rt = MockRuntime()
        self.detector.audit(runtime=mock_rt)
        self.assertGreaterEqual(len(self.mock_ledger.receipts), 1)
        audit_rcpt = self.mock_ledger.receipts[0]
        self.assertEqual(audit_rcpt["action_category"], "SPEC_DRIFT_AUDIT")

        # Test realignment receipt
        self.detector.realign_spec("SPEC-08", runtime=mock_rt)
        self.assertGreaterEqual(len(self.mock_ledger.receipts), 2)

    def test_11_terminal_summary_cp1252_safe(self) -> None:
        mock_rt = MockRuntime()
        report = self.detector.audit(runtime=mock_rt)
        summary = report.format_terminal_summary()

        # Must encode to cp1252 without any UnicodeEncodeError
        encoded = summary.encode("cp1252")
        self.assertTrue(len(encoded) > 0)

        # Must not contain unicode box drawing characters
        for ch in summary:
            self.assertFalse(0x2500 <= ord(ch) <= 0x257F)

        self.assertIn("+----------------------------------------------------------------------+", summary)
        self.assertIn("100% SPECIFICATION CONVERGENCE", summary)

    def test_12_status_dictionary(self) -> None:
        self.detector.audit(runtime=MockRuntime())
        st = self.detector.status()
        self.assertEqual(st["stage"], 94)
        self.assertEqual(st["total_registered_specs"], 8)
        self.assertEqual(st["compliance_score"], 100.0)


if __name__ == "__main__":
    unittest.main()
