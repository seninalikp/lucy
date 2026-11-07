"""
test_stage301_open_jarvis_bridge.py
Stage 301 verification test suite for OpenJarvis Sovereign Orchestration Bridge.
Verifies all 5 OpenJarvis primitives and Lucy sovereign command authority.
"""

import sys
import unittest
from pathlib import Path

# Setup project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.lucy_core.open_jarvis_bridge import (
    STAGE,
    SOVEREIGN_POLICY,
    OpenJarvisBridge,
)
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class TestStage301OpenJarvisBridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = LucyRuntime(project_root=PROJECT_ROOT)
        cls.router = CommandRouter(cls.runtime)

    def test_01_sovereign_policy_and_stage(self):
        """Lucy must be the undisputed sovereign orchestrator."""
        status = self.runtime.open_jarvis_status()
        self.assertEqual(status["stage"], STAGE)
        self.assertEqual(status["sovereign_authority"], "LUCY")
        self.assertIn("UNIDIRECTIONAL_AUTHORITY", status["policy"])

    def test_02_intelligence_primitive(self):
        """Intelligence primitive catalog must list primary model."""
        status = self.runtime.open_jarvis_status()
        intel = status["primitives"]["intelligence"]
        self.assertEqual(intel["primary_model"], "lucy:personal")
        self.assertIn("lucy:personal", intel["available_models"])

    def test_03_engine_hardware_telemetry(self):
        """Engine primitive must report hardware specs and loopback latency."""
        status = self.runtime.open_jarvis_status()
        engine = status["primitives"]["engine"]
        self.assertGreaterEqual(engine["cpu_count"], 1)
        self.assertEqual(engine["device_class"], "APU_HYBRID_CPU")

        latency = self.runtime.open_jarvis.engine.benchmark_latency()
        self.assertIn("probe_latency_ms", latency)
        self.assertIn(latency["mode"], ["live_service", "internal_native_engine"])

    def test_04_agent_loops_execution(self):
        """Agent loops must execute deterministically and return verified results."""
        # 1. Native ReAct Loop
        react_res = self.runtime.open_jarvis_execute_agent(
            agent_type="native_react",
            task="Verify local workspace integrity",
        )
        self.assertEqual(react_res["status"], "success")
        self.assertEqual(react_res["agent"], "native_react")
        self.assertEqual(react_res["sovereign_authority"], "LUCY")
        self.assertIn("native_react", react_res["content"])

        # 2. Native OpenHands CodeAct Loop
        openhands_res = self.runtime.open_jarvis_execute_agent(
            agent_type="native_openhands",
            task="Generate unit test assertions",
        )
        self.assertEqual(openhands_res["status"], "success")
        self.assertEqual(openhands_res["agent"], "native_openhands")
        self.assertIn("native_openhands", openhands_res["content"])

        # 3. Deep Research Loop
        research_res = self.runtime.open_jarvis_execute_agent(
            agent_type="deep_research",
            task="Analyze sovereign local architecture",
        )
        self.assertEqual(research_res["status"], "success")
        self.assertIn("deep_research", research_res["content"])

    def test_05_tools_and_mcp_hub(self):
        """Tools and MCP hub operations must succeed."""
        tools_list = self.runtime.open_jarvis.tools.list_available_tools()
        tool_names = [t["name"] for t in tools_list]
        self.assertIn("file_io", tool_names)
        self.assertIn("terminal_exec", tool_names)
        self.assertIn("datetime_calculator", tool_names)
        self.assertIn("mcp_hub", tool_names)

        # Test file_io mkdir
        test_dir = PROJECT_ROOT / "data" / "open_jarvis_test_sandbox"
        res_mkdir = self.runtime.open_jarvis_invoke_tool(
            tool_name="file_io",
            parameters={"operation": "mkdir", "path": str(test_dir)},
        )
        self.assertEqual(res_mkdir["status"], "success")
        self.assertTrue(test_dir.exists())

        # Cleanup test dir
        if test_dir.exists():
            test_dir.rmdir()

        # Test datetime calculation
        res_calc = self.runtime.open_jarvis_invoke_tool(
            tool_name="datetime_calculator",
            parameters={"formula": "now"},
        )
        self.assertEqual(res_calc["status"], "success")

        # Test MCP hub bridge
        res_mcp = self.runtime.open_jarvis_invoke_tool(
            tool_name="mcp_hub",
            parameters={"server_name": "filesystem_mcp", "action": "ping"},
        )
        self.assertEqual(res_mcp["status"], "success")
        self.assertTrue(res_mcp["result"]["connected"])

    def test_06_learning_and_intelligence_per_watt(self):
        """Intelligence Per Watt efficiency metrics must be computed correctly."""
        eff = self.runtime.open_jarvis_profile_efficiency(token_count=200, duration_ms=200.0)
        self.assertIn("throughput_tokens_sec", eff)
        self.assertIn("energy_consumed_joules", eff)
        self.assertIn("efficiency_tokens_per_joule", eff)
        self.assertEqual(eff["compliance"], "OPTIMIZED_LOCAL_APU")

        # Traces file should exist and contain records
        traces_file = self.runtime.open_jarvis.learning.traces_file
        self.assertTrue(traces_file.exists())
        lines = traces_file.read_text(encoding="utf-8").strip().splitlines()
        self.assertGreaterEqual(len(lines), 1)

    def test_07_router_commands(self):
        """Router commands /jarvis, /jarvis-run, and /jarvis-efficiency must respond."""
        # /jarvis
        resp1 = self.router.handle("/jarvis")
        self.assertIn("OPENJARVIS SOVEREIGN ORCHESTRATION BRIDGE", resp1.message)
        self.assertIn("Authority: LUCY", resp1.message)

        # /jarvis-run
        resp2 = self.router.handle("/jarvis-run native_react test task from terminal")
        self.assertIn("OpenJarvis [native_react]", resp2.message)

        # /jarvis-efficiency
        resp3 = self.router.handle("/jarvis-efficiency")
        self.assertIn("OPENJARVIS INTELLIGENCE PER WATT PROFILE", resp3.message)
        self.assertIn("tokens/Joule", resp3.message)


if __name__ == "__main__":
    unittest.main()
