"""
tests/test_stage135_ffi_native_linker.py
Verification suite for Stage 135: Polyglot FFI Bridge & Native C ABI Linker
Era 14: Autonomous Code Evolution, Semantic Mutation & Static Synthesis
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.ffi_native_linker import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    ERA_NAME,
    STAGE,
    STAGE_NAME,
    PolyglotFFINativeLinker,
    NativeSymbolBinding,
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


class TestStage135FFINativeLinker(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)
        self.data_dir = self.project_root / "data" / "lucy" / "ffi"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = MockReceiptLedger()
        self.linker = PolyglotFFINativeLinker(
            project_root=self.project_root,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_metadata(self):
        """Verifies sovereign operator identity and stage/era metadata."""
        self.assertEqual(STAGE, 135)
        self.assertEqual(ERA, 14)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")
        status = self.linker.status()
        self.assertEqual(status["stage"], 135)
        self.assertEqual(status["era"], 14)
        self.assertEqual(status["creator"], "Senin")
        self.assertEqual(status["creator_full_name"], "Senin Ali K P")

    def test_02_default_symbols_initialization(self):
        """Verifies standard C runtime symbols are seeded on startup."""
        status = self.linker.status()
        self.assertGreaterEqual(status["total_bindings"], 3)
        self.assertIn("strlen", self.linker._bindings)
        self.assertIn("abs", self.linker._bindings)

    def test_03_link_custom_native_symbol(self):
        """Verifies custom C prototype declaration and binding."""
        binding = self.linker.link_native_symbol(
            symbol_name="sqrt",
            library_name="m",
            restype_name="double",
            argtypes_names=["double"],
            description="Computes square root",
        )
        self.assertEqual(binding.symbol_name, "sqrt")
        self.assertEqual(binding.restype, "double")
        self.assertEqual(binding.argtypes, ["double"])

    def test_04_invoke_native_strlen(self):
        """Verifies invocation of standard strlen through C ABI or fallback."""
        res = self.linker.invoke_native_symbol("strlen", "LucyOS_Kernel")
        self.assertEqual(res, 13)

    def test_05_invoke_native_abs(self):
        """Verifies invocation of standard abs with negative integer."""
        res = self.linker.invoke_native_symbol("abs", -99)
        self.assertEqual(res, 99)

    def test_06_fallback_shim_execution(self):
        """Verifies registration and execution of pure Python fallback shims."""
        self.linker.link_native_symbol("custom_multiplier", "none", "int", ["int", "int"])
        self.linker.register_fallback_shim("custom_multiplier", lambda a, b: a * b)

        res = self.linker.invoke_native_symbol("custom_multiplier", 6, 7)
        self.assertEqual(res, 42)

    def test_07_persistence_manifest(self):
        """Verifies FFI bindings persist to disk and reload across instances."""
        self.linker.link_native_symbol("persistent_func", "libc", "int", ["int"])
        self.linker.register_fallback_shim("persistent_func", lambda x: x + 1)
        self.linker.invoke_native_symbol("persistent_func", 10)

        linker2 = PolyglotFFINativeLinker(
            project_root=self.project_root,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
        )
        self.assertIn("persistent_func", linker2._bindings)
        self.assertEqual(linker2.status()["total_calls"], 1)

    def test_08_receipt_ledger_integration(self):
        """Verifies receipts are recorded for symbol linking and execution."""
        self.linker.link_native_symbol("audit_func", "msvcrt", "int", [])
        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("NATIVE_SYMBOL_LINKED", actions)

        self.linker.invoke_native_symbol("abs", -5)
        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("NATIVE_CALL_EXECUTED", actions)

    def test_09_ascii_ffi_status_table(self):
        """Verifies CP1252-safe ASCII table formatting."""
        table = self.linker.format_ffi_status_table()
        self.assertIn("POLYGLOT FFI NATIVE LINKER", table)
        self.assertIn("strlen", table)
        self.assertIn("abs", table)
        self.assertIn("Senin", table)
        # Strict CP1252 compatibility test
        table.encode("cp1252")

    def test_10_runtime_integration(self):
        """Verifies LucyRuntime binds and executes FFI linker commands."""
        from backend.lucy_core.lucy_runtime import LucyRuntime

        runtime = LucyRuntime(project_root=self.project_root)
        self.assertTrue(hasattr(runtime, "ffi_linker"))
        self.assertIsInstance(runtime.ffi_linker, PolyglotFFINativeLinker)

        # Test CLI commands via lucy_respond
        res = runtime.lucy_respond("/ffi-status")
        self.assertIn("POLYGLOT FFI NATIVE LINKER", res)

        res_link = runtime.lucy_respond("/link-native-symbol msvcrt atoi int str")
        self.assertIn("Linked Native Symbol", res_link)

        res_call = runtime.lucy_respond("/invoke-native abs -42")
        self.assertIn("Result: 42", res_call)


if __name__ == "__main__":
    unittest.main()
