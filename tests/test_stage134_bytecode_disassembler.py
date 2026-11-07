"""
tests/test_stage134_bytecode_disassembler.py
Verification suite for Stage 134: Bytecode Decompiler & Disassembly Inspector
Era 14: Autonomous Code Evolution, Semantic Mutation & Static Synthesis
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.bytecode_disassembler import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    ERA_NAME,
    STAGE,
    STAGE_NAME,
    BytecodeDisassemblyInspector,
    BytecodeDisassemblyReport,
    OpcodeInstructionRecord,
)


class MockReceiptLedger:
    def __init__(self):
        self.receipts = []

    def record_receipt(self, action_category: str, operation: str, target: str, verified_outcome: str):
        self.receipts.append({
            "action_category": action_category,
            "operation": operation,
            "target": target,
            "verified_outcome": verified_outcome,
        })


class TestStage134BytecodeDisassembler(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)
        self.data_dir = self.project_root / "data" / "lucy" / "bytecode"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = MockReceiptLedger()
        self.inspector = BytecodeDisassemblyInspector(
            project_root=self.project_root,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_metadata(self):
        """Verifies sovereign operator identity and stage/era metadata."""
        self.assertEqual(STAGE, 134)
        self.assertEqual(ERA, 14)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")
        status = self.inspector.status()
        self.assertEqual(status["stage"], 134)
        self.assertEqual(status["era"], 14)
        self.assertEqual(status["creator"], "Senin")
        self.assertEqual(status["creator_full_name"], "Senin Ali K P")

    def test_02_disassemble_python_code_string(self):
        """Verifies disassembly of raw Python code snippet."""
        code = "def add(a, b):\n    return a + b\n"
        rep = self.inspector.disassemble_code(code, "AddFunction")
        self.assertIsNotNone(rep)
        self.assertGreater(rep.total_instructions, 0)
        self.assertFalse(rep.has_dynamic_eval)
        self.assertIn("RETURN_VALUE", rep.opcode_distribution)

    def test_03_disassemble_callable_function(self):
        """Verifies direct disassembly of Python function object."""
        def sample_kernel(x, y):
            z = x * 2
            return z + y

        rep = self.inspector.disassemble_code(sample_kernel, "SampleKernel")
        self.assertIsNotNone(rep)
        self.assertGreater(rep.total_instructions, 0)
        self.assertEqual(rep.varnames_count, 3)

    def test_04_detect_dynamic_eval_anomaly(self):
        """Verifies detection of dangerous dynamic eval opcodes."""
        dangerous_code = "def execute_input(data):\n    return eval(data)\n"
        rep = self.inspector.disassemble_code(dangerous_code, "DangerousEval")
        self.assertTrue(rep.has_dynamic_eval)

        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("BYTECODE_ANOMALY_FLAGGED", actions)

    def test_05_safe_code_no_eval_anomaly(self):
        """Verifies clean code passes security audit without anomaly flags."""
        clean_code = "def safe_calc(n):\n    return [i * i for i in range(n)]\n"
        rep = self.inspector.disassemble_code(clean_code, "SafeCalc")
        self.assertFalse(rep.has_dynamic_eval)

    def test_06_format_bytecode_dump(self):
        """Verifies human-readable formatted disassembly dump."""
        code = "x = 10\ny = 20\n"
        rep = self.inspector.disassemble_code(code, "Assignment")
        dump = self.inspector.format_bytecode_dump(rep.report_id)
        self.assertIn("Bytecode Disassembly", dump)
        self.assertIn("Offset", dump)
        self.assertIn("Opname", dump)

    def test_07_persistence_manifest(self):
        """Verifies bytecode analysis persists to JSON and reloads across instances."""
        code = "a = 1 + 2\n"
        rep = self.inspector.disassemble_code(code, "PersistTest")

        insp2 = BytecodeDisassemblyInspector(
            project_root=self.project_root,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
        )
        self.assertIn(rep.report_id, insp2._reports)
        self.assertEqual(insp2.status()["total_disassembled"], 1)

    def test_08_receipt_ledger_integration(self):
        """Verifies receipts are recorded for bytecode disassembly."""
        code = "b = 100\n"
        self.inspector.disassemble_code(code, "ReceiptTest")
        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("BYTECODE_DISASSEMBLED", actions)

    def test_09_ascii_bytecode_status_table(self):
        """Verifies CP1252-safe ASCII table formatting."""
        code = "res = True\n"
        self.inspector.disassemble_code(code, "TableTest")
        table = self.inspector.format_bytecode_status_table()
        self.assertIn("BYTECODE DISASSEMBLY INSPECTOR", table)
        self.assertIn("TableTest", table)
        self.assertIn("Senin", table)
        # Strict CP1252 compatibility test
        table.encode("cp1252")

    def test_10_runtime_integration(self):
        """Verifies LucyRuntime binds and executes bytecode disassembler commands."""
        from backend.lucy_core.lucy_runtime import LucyRuntime

        runtime = LucyRuntime(project_root=self.project_root)
        self.assertTrue(hasattr(runtime, "bytecode_inspector"))
        self.assertIsInstance(runtime.bytecode_inspector, BytecodeDisassemblyInspector)

        # Test CLI commands via lucy_respond
        res = runtime.lucy_respond("/bytecode-status")
        self.assertIn("BYTECODE DISASSEMBLY INSPECTOR", res)

        res_dis = runtime.lucy_respond("/disassemble-code a = 1 + 2")
        self.assertIn("Bytecode Disassembled", res_dis)

        res_op = runtime.lucy_respond("/inspect-opcodes x = 10; y = 20; z = x + y")
        self.assertIn("Opcode Frequency Breakdown", res_op)


if __name__ == "__main__":
    unittest.main()
