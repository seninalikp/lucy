"""
test_stage47_operator_toolkit.py
Stage 47 = Real-World Safe Windows OS Tool Suite (Operator Toolkit).

Verifies:
1. Toolkit reports Stage 47 and active status.
2. Pure standard library Windows telemetry returns real RAM, CPU cores, disk space, and battery metrics.
3. Process inspector safely parses running tasks by name and PID.
4. Workspace file search by pattern and extension.
5. Content grep locates keywords inside text files.
6. Port socket prober safely assesses ports (11434, 5820, etc.).
7. Sandbox cache hygiene auditor and safe dry-run/deletion.
8. LucyRuntime Stage 47 integration.
9. CommandRouter Stage 47 command routing and formatting.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.operator_toolkit import OperatorToolkit, STAGE
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class Stage47OperatorToolkitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.lucy_data = self.root / "data" / "lucy"
        self.lucy_data.mkdir(parents=True, exist_ok=True)
        self.toolkit = OperatorToolkit(project_root=self.root, lucy_data=self.lucy_data)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_01_initial_status(self) -> None:
        status = self.toolkit.status()
        self.assertEqual(status["stage"], STAGE)
        self.assertEqual(status["operator_toolkit"], "active")
        self.assertIn("cores", status["os_summary"])
        self.assertIn("MB", status["ram_summary"])
        self.assertIn("free", status["disk_summary"])

    def test_02_system_telemetry_fields(self) -> None:
        telemetry = self.toolkit.get_system_telemetry()
        self.assertEqual(telemetry["stage"], STAGE)
        
        # OS
        self.assertIn("Windows", telemetry["os"]["system"])
        self.assertGreaterEqual(telemetry["os"]["cpu_cores"], 1)

        # RAM
        self.assertGreater(telemetry["ram"]["total_mb"], 1000)
        self.assertGreater(telemetry["ram"]["available_mb"], 100)
        self.assertIn("memory_load_percent", telemetry["ram"])

        # Disk
        self.assertGreater(telemetry["disk"]["total_gb"], 10)
        self.assertGreater(telemetry["disk"]["free_gb"], 1)

        # Power
        self.assertIn("ac_line_status", telemetry["power"])

    def test_03_process_inspector_search(self) -> None:
        # Search for current python process
        procs = self.toolkit.inspect_processes(query="python", limit=10)
        self.assertIsInstance(procs, list)
        if procs:
            p = procs[0]
            self.assertIn("python", p["name"].lower())
            self.assertTrue(p["pid"].isdigit())
            self.assertIn("memory", p)

    def test_04_workspace_file_search(self) -> None:
        # Create test directory structure
        test_dir = self.root / "test_workspace"
        test_dir.mkdir(parents=True, exist_ok=True)
        (test_dir / "my_custom_tool.py").write_text("print('hello')", encoding="utf-8")
        (test_dir / "notes.txt").write_text("sample notes", encoding="utf-8")

        results = self.toolkit.search_workspace(pattern="my_custom", root_path=test_dir)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "my_custom_tool.py")

        ext_results = self.toolkit.search_workspace(extension="txt", root_path=test_dir)
        self.assertEqual(len(ext_results), 1)
        self.assertEqual(ext_results[0]["name"], "notes.txt")

    def test_05_workspace_content_grep(self) -> None:
        test_dir = self.root / "test_workspace"
        test_dir.mkdir(parents=True, exist_ok=True)
        (test_dir / "alpha.py").write_text("def unique_search_target_func(): pass", encoding="utf-8")
        (test_dir / "beta.py").write_text("def other(): pass", encoding="utf-8")

        results = self.toolkit.search_workspace(
            pattern="unique_search_target_func",
            search_content=True,
            root_path=test_dir,
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "alpha.py")
        self.assertTrue(results[0]["matched_content"])

    def test_06_port_socket_prober(self) -> None:
        # Probe dummy ports
        res = self.toolkit.probe_network_ports(ports=[59998, 59999])
        self.assertEqual(res["stage"], STAGE)
        self.assertEqual(res["total_probed"], 2)
        self.assertIn("59998", res["ports"])
        self.assertFalse(res["ports"]["59998"]["open"])

    def test_07_sandbox_cache_hygiene(self) -> None:
        staging = self.lucy_data / "sandbox" / "staging"
        (staging / "mock_tool.py").write_text("code = 123", encoding="utf-8")
        (staging / "mock_tool.pyc").write_text("bytecode", encoding="utf-8")

        # Dry run does not delete
        dry = self.toolkit.clean_sandbox_cache(dry_run=True)
        self.assertEqual(dry["files_found"], 2)
        self.assertTrue((staging / "mock_tool.py").exists())

        # Real cleanup deletes
        real = self.toolkit.clean_sandbox_cache(dry_run=False)
        self.assertEqual(real["files_found"], 2)
        self.assertFalse((staging / "mock_tool.py").exists())


class Stage47RuntimeAndRouterIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "data" / "lucy").mkdir(parents=True, exist_ok=True)
        (self.root / "logs").mkdir(parents=True, exist_ok=True)
        self.runtime = LucyRuntime(project_root=self.root)
        self.router = CommandRouter(self.runtime)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_08_runtime_methods(self) -> None:
        telem = self.runtime.system_telemetry()
        self.assertEqual(telem["stage"], STAGE)
        self.assertIn("ram", telem)

        ports = self.runtime.probe_network_ports()
        self.assertIn("ports", ports)

        procs = self.runtime.inspect_processes("python", limit=5)
        self.assertIsInstance(procs, list)

    def test_09_router_commands(self) -> None:
        # 1. Telemetry command
        res1 = self.router.handle("system telemetry")
        self.assertIn("Windows Hardware & System Telemetry:", res1.message)
        self.assertIn("RAM:", res1.message)
        self.assertIn("Disk C:", res1.message)

        # 2. Inspect processes command
        res2 = self.router.handle("inspect processes python")
        self.assertIn("Process Inspector", res2.message)

        # 3. Probe ports command
        res3 = self.router.handle("probe ports")
        self.assertIn("Operator Network Socket Probes", res3.message)

        # 4. Clean cache command
        res4 = self.router.handle("clean sandbox")
        self.assertIn("Sandbox Staging Cache Cleanup:", res4.message)


if __name__ == "__main__":
    unittest.main()
