r"""
tests/test_stage113_ast_polyglot_engine.py
Comprehensive test suite for Stage 113: Polyglot AST Engine
Era 12: The Autonomous Cognitive Matrix & Distributed IPC Fabric
"""

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.ast_polyglot_engine import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    STAGE,
    PolyglotASTEngine,
    PolyglotFileReport,
    PolyglotSymbol,
    PolyglotWorkspaceSummary,
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


class TestStage113PolyglotASTEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.data_dir = self.root / "data" / "polyglot"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.receipt_ledger = MockReceiptLedger()

        self.engine = PolyglotASTEngine(
            project_root=self.root,
            data_dir=self.data_dir,
            receipt_ledger=self.receipt_ledger,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_01_initialization(self) -> None:
        st = self.engine.status()
        self.assertEqual(st["stage"], 113)
        self.assertEqual(st["era"], 12)
        self.assertEqual(st["creator"], CREATOR_NAME)
        self.assertEqual(st["creator_full_name"], CREATOR_FULL_NAME)

    def test_02_detect_language(self) -> None:
        self.assertEqual(self.engine.detect_language("server.py"), "python")
        self.assertEqual(self.engine.detect_language("app.tsx"), "typescript")
        self.assertEqual(self.engine.detect_language("index.js"), "javascript")
        self.assertEqual(self.engine.detect_language("main.go"), "go")
        self.assertEqual(self.engine.detect_language("lib.rs"), "rust")
        self.assertEqual(self.engine.detect_language("kernel.cpp"), "cpp")
        self.assertEqual(self.engine.detect_language("header.hpp"), "cpp")
        self.assertIsNone(self.engine.detect_language("data.xyz"))

    def test_03_parse_python_ast(self) -> None:
        py_code = '''"""Module docstring."""
import os
from sys import argv

class EngineCore:
    """Core runtime engine."""
    def start(self, mode: str) -> bool:
        return True

async def fetch_telemetry():
    pass
'''
        rep = self.engine.parse_python(py_code, "core.py")
        self.assertTrue(rep.syntax_valid)
        self.assertEqual(rep.language, "python")
        self.assertGreaterEqual(len(rep.symbols), 3)

        sym_names = {s.name for s in rep.symbols}
        self.assertIn("EngineCore", sym_names)
        self.assertIn("EngineCore.start", sym_names)
        self.assertIn("fetch_telemetry", sym_names)

        # Check docstring extraction
        cls_sym = next(s for s in rep.symbols if s.name == "EngineCore")
        self.assertEqual(cls_sym.docstring, "Core runtime engine.")
        self.assertTrue(cls_sym.is_exported)

    def test_04_parse_python_syntax_error(self) -> None:
        bad_code = "def broken_syntax(x: int\n   print('missing paren')"
        rep = self.engine.parse_python(bad_code, "bad.py")
        self.assertFalse(rep.syntax_valid)
        self.assertIn("SyntaxError", rep.error_message)

    def test_05_parse_typescript(self) -> None:
        ts_code = """
import { useState } from 'react';
import axios from 'axios';

export interface UserConfig {
    host: string;
    port: number;
}

export type AuthState = "IDLE" | "AUTHENTICATED";

export class GatewayClient {
    connect(): void {}
}

export const executeQuery = async () => {};

function privateHelper() {}
"""
        rep = self.engine.parse_javascript(ts_code, "gateway.ts", is_ts=True)
        self.assertTrue(rep.syntax_valid)
        self.assertEqual(rep.language, "typescript")

        sym_dict = {s.name: s.kind for s in rep.symbols}
        self.assertEqual(sym_dict.get("UserConfig"), "interface")
        self.assertEqual(sym_dict.get("AuthState"), "type")
        self.assertEqual(sym_dict.get("GatewayClient"), "class")
        self.assertEqual(sym_dict.get("executeQuery"), "function")
        self.assertEqual(sym_dict.get("privateHelper"), "function")

        # Check imports
        mod_names = [i.module for i in rep.imports]
        self.assertIn("react", mod_names)
        self.assertIn("axios", mod_names)

    def test_06_parse_go(self) -> None:
        go_code = """
package main

import (
    "fmt"
    "net/http"
)

type ServerConfig struct {
    Port int
}

type Handler interface {
    Serve()
}

func (c *ServerConfig) Validate() bool {
    return c.Port > 0
}

func Run() {
    fmt.Println("Running")
}
"""
        rep = self.engine.parse_go(go_code, "main.go")
        self.assertTrue(rep.syntax_valid)
        self.assertEqual(rep.language, "go")

        sym_dict = {s.name: s.kind for s in rep.symbols}
        self.assertEqual(sym_dict.get("ServerConfig"), "struct")
        self.assertEqual(sym_dict.get("Handler"), "interface")
        self.assertEqual(sym_dict.get("Validate"), "method")
        self.assertEqual(sym_dict.get("Run"), "function")

    def test_07_parse_rust(self) -> None:
        rs_code = """
use std::sync::Arc;

pub struct KernelNode {
    pub id: u64,
}

pub enum NodeStatus {
    Active,
    Idle,
}

pub trait Orchestrator {
    fn dispatch(&self);
}

pub async fn launch_runtime() -> bool {
    true
}
"""
        rep = self.engine.parse_rust(rs_code, "kernel.rs")
        self.assertTrue(rep.syntax_valid)
        self.assertEqual(rep.language, "rust")

        sym_dict = {s.name: s.kind for s in rep.symbols}
        self.assertEqual(sym_dict.get("KernelNode"), "struct")
        self.assertEqual(sym_dict.get("NodeStatus"), "enum")
        self.assertEqual(sym_dict.get("Orchestrator"), "trait")
        self.assertEqual(sym_dict.get("launch_runtime"), "function")

    def test_08_parse_cpp(self) -> None:
        cpp_code = """
#include <iostream>
#include "bridge.h"

namespace LucyCompute {
    class Accelerator {
    public:
        void compute();
    };

    struct BufferDescriptor {
        int size;
    };
}
"""
        rep = self.engine.parse_cpp(cpp_code, "accelerator.cpp")
        self.assertTrue(rep.syntax_valid)
        self.assertEqual(rep.language, "cpp")

        sym_dict = {s.name: s.kind for s in rep.symbols}
        self.assertEqual(sym_dict.get("LucyCompute"), "namespace")
        self.assertEqual(sym_dict.get("Accelerator"), "class")
        self.assertEqual(sym_dict.get("BufferDescriptor"), "struct")

    def test_09_workspace_scan_and_indexing(self) -> None:
        # Create polyglot files in workspace
        (self.root / "py_mod").mkdir(parents=True)
        (self.root / "py_mod" / "agent.py").write_text("class AutonomousAgent:\n    pass\n", encoding="utf-8")

        (self.root / "ts_ui").mkdir(parents=True)
        (self.root / "ts_ui" / "view.ts").write_text("export interface DashboardProps {}\n", encoding="utf-8")

        (self.root / "native_go").mkdir(parents=True)
        (self.root / "native_go" / "daemon.go").write_text("package daemon\ntype Supervisor struct {}\n", encoding="utf-8")

        summary = self.engine.scan_workspace(self.root)
        self.assertIsInstance(summary, PolyglotWorkspaceSummary)
        self.assertGreaterEqual(summary.total_files, 3)
        self.assertGreaterEqual(summary.total_symbols, 3)

        self.assertIn("python", summary.language_breakdown)
        self.assertIn("typescript", summary.language_breakdown)
        self.assertIn("go", summary.language_breakdown)

    def test_10_symbol_lookup(self) -> None:
        (self.root / "sym_test.py").write_text("class BicentennialMatrix:\n    def activate(self): pass\n", encoding="utf-8")
        self.engine.scan_workspace(self.root)

        res = self.engine.find_symbol("BicentennialMatrix")
        self.assertGreaterEqual(len(res), 1)
        self.assertEqual(res[0].name, "BicentennialMatrix")
        self.assertEqual(res[0].kind, "class")

    def test_11_cross_language_bridge_detection(self) -> None:
        (self.root / "bridge.py").write_text(
            "import ctypes\nimport subprocess\nsubprocess.run(['node', 'script.js'])\n",
            encoding="utf-8",
        )
        summary = self.engine.scan_workspace(self.root)
        self.assertGreaterEqual(len(summary.cross_language_bridges), 2)
        bridge_types = [b["bridge_type"] for b in summary.cross_language_bridges]
        self.assertTrue(any("FFI" in b for b in bridge_types))
        self.assertTrue(any("Process IPC" in b for b in bridge_types))

    def test_12_persistence_and_reload(self) -> None:
        (self.root / "file1.py").write_text("class TestClassA: pass\n", encoding="utf-8")
        self.engine.scan_workspace(self.root)

        # Create new engine pointing to same directory
        engine2 = PolyglotASTEngine(
            project_root=self.root,
            data_dir=self.data_dir,
        )
        self.assertIsNotNone(engine2._last_summary)
        self.assertGreaterEqual(engine2._last_summary.total_files, 1)

    def test_13_receipt_ledger_integration(self) -> None:
        (self.root / "receipt_file.py").write_text("def receipt_func(): pass\n", encoding="utf-8")
        self.engine.scan_workspace(self.root)
        self.engine.find_symbol("receipt_func")

        cats = [r["action_category"] for r in self.receipt_ledger.receipts]
        self.assertIn("POLYGLOT_AST_SCAN", cats)
        self.assertIn("POLYGLOT_SYMBOL_RESOLVED", cats)

    def test_14_ascii_summary_table_formatting(self) -> None:
        (self.root / "test.py").write_text("class Sample: pass\n", encoding="utf-8")
        self.engine.scan_workspace(self.root)
        tbl = self.engine.format_polyglot_summary_table()

        self.assertIn("LUCY OS - POLYGLOT AST ENGINE", tbl)
        self.assertIn("Language Dialect", tbl)
        self.assertIn(CREATOR_NAME, tbl)
        self.assertIn(CREATOR_FULL_NAME, tbl)
        self.assertTrue(tbl.startswith("+--"))


if __name__ == "__main__":
    unittest.main()
