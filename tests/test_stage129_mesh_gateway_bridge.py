"""
tests/test_stage129_mesh_gateway_bridge.py
Verification suite for Stage 129: Distributed Multi-Node IPC Mesh Gateway
Era 13: Self-Reflective Symbolic Mesh & Cognitive Graph Synthesizer
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.mesh_gateway_bridge import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    ERA_NAME,
    STAGE,
    STAGE_NAME,
    DistributedMeshGatewayBridge,
    MeshNodeDescriptor,
    RPCInvocationPacket,
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


class TestStage129MeshGatewayBridge(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)
        self.data_dir = self.project_root / "data" / "lucy" / "mesh"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = MockReceiptLedger()
        self.bridge = DistributedMeshGatewayBridge(
            project_root=self.project_root,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
            local_node_id="test_master_node",
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_metadata(self):
        """Verifies sovereign operator identity and stage/era metadata."""
        self.assertEqual(STAGE, 129)
        self.assertEqual(ERA, 13)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")
        status = self.bridge.status()
        self.assertEqual(status["stage"], 129)
        self.assertEqual(status["era"], 13)
        self.assertEqual(status["creator"], "Senin")
        self.assertEqual(status["creator_full_name"], "Senin Ali K P")

    def test_02_default_nodes_initialization(self):
        """Verifies initial cluster nodes are seeded with active status."""
        nodes = self.bridge.list_nodes()
        self.assertGreaterEqual(len(nodes), 3)

        master = self.bridge.get_node("test_master_node")
        self.assertIsNotNone(master)
        self.assertEqual(master.role, "controller")
        self.assertEqual(master.status, "ACTIVE")
        self.assertTrue(len(master.signature) > 10)

    def test_03_register_custom_node_with_hmac(self):
        """Verifies custom worker node registration and HMAC-SHA256 signature."""
        node = self.bridge.register_node(
            node_id="worker_gpu_cluster_01",
            endpoint="ipc://localhost/worker_gpu",
            role="worker",
        )
        self.assertEqual(node.node_id, "worker_gpu_cluster_01")
        self.assertEqual(node.role, "worker")
        self.assertTrue(len(node.signature) == 64)  # 256-bit hex string

        fetched = self.bridge.get_node("worker_gpu_cluster_01")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.endpoint, "ipc://localhost/worker_gpu")

    def test_04_dispatch_rpc_to_local_handler(self):
        """Verifies internal RPC dispatch and execution of registered handlers."""
        # Ping handler
        resp_ping = self.bridge.dispatch_rpc(
            target_node="test_master_node",
            procedure="ping",
            parameters={},
        )
        self.assertEqual(resp_ping["status"], "success")
        self.assertTrue(resp_ping["result"]["pong"])

        # Echo handler
        resp_echo = self.bridge.dispatch_rpc(
            target_node="test_master_node",
            procedure="echo",
            parameters={"msg": "hello sovereign mesh"},
        )
        self.assertEqual(resp_echo["status"], "success")
        self.assertEqual(resp_echo["result"]["echoed"]["msg"], "hello sovereign mesh")

    def test_05_dispatch_rpc_to_simulated_remote_node(self):
        """Verifies simulated RPC routing and metrics update on target nodes."""
        node_id = "worker_neural_01"
        resp = self.bridge.dispatch_rpc(
            target_node=node_id,
            procedure="quantize_ast",
            parameters={"model": "deep_lucy_7b", "bits": 4},
        )
        self.assertEqual(resp["status"], "success")
        self.assertEqual(resp["target_node"], node_id)

        node = self.bridge.get_node(node_id)
        self.assertEqual(node.total_rpcs_handled, 1)

    def test_06_unauthorized_node_dropped(self):
        """Verifies RPC to non-existent node is rejected and security receipt recorded."""
        resp = self.bridge.dispatch_rpc(
            target_node="rogue_external_node_666",
            procedure="infiltrate",
            parameters={},
        )
        self.assertEqual(resp["status"], "error")
        self.assertIn("not registered", resp["message"].lower())

        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("UNAUTHORIZED_NODE_DROPPED", actions)

    def test_07_persistence_manifest(self):
        """Verifies cluster topology persists to disk and reloads across instances."""
        self.bridge.register_node("persistent_node_99", "ipc://localhost/p99", "memory")
        self.bridge.dispatch_rpc("persistent_node_99", "store", {"k": "v"})

        bridge2 = DistributedMeshGatewayBridge(
            project_root=self.project_root,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
            local_node_id="test_master_node",
        )
        p_node = bridge2.get_node("persistent_node_99")
        self.assertIsNotNone(p_node)
        self.assertEqual(p_node.total_rpcs_handled, 1)
        self.assertEqual(bridge2.status()["total_rpcs"], 1)

    def test_08_receipt_ledger_integration(self):
        """Verifies execution receipts for node registration and RPC dispatch."""
        self.bridge.register_node("ledger_node_01", "ipc://test", "sensor")
        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("MESH_NODE_REGISTERED", actions)

        self.bridge.dispatch_rpc("ledger_node_01", "ping")
        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("RPC_DISPATCHED", actions)

    def test_09_ascii_mesh_status_table(self):
        """Verifies CP1252-safe ASCII table formatting."""
        table = self.bridge.format_mesh_status_table()
        self.assertIn("DISTRIBUTED IPC MESH GATEWAY", table)
        self.assertIn("test_master_node", table)
        self.assertIn("controller", table)
        self.assertIn("Senin", table)
        # Strict CP1252 compatibility test
        table.encode("cp1252")

    def test_10_runtime_integration(self):
        """Verifies LucyRuntime binds and executes mesh gateway commands."""
        from backend.lucy_core.lucy_runtime import LucyRuntime

        runtime = LucyRuntime(project_root=self.project_root)
        self.assertTrue(hasattr(runtime, "mesh_gateway"))
        self.assertIsInstance(runtime.mesh_gateway, DistributedMeshGatewayBridge)

        # Test CLI commands via lucy_respond
        res = runtime.lucy_respond("/mesh-gateway-status")
        self.assertIn("DISTRIBUTED IPC MESH GATEWAY", res)

        res_reg = runtime.lucy_respond("/register-node worker_rt_01 ipc://localhost/rt worker")
        self.assertIn("Registered Mesh Node", res_reg)

        res_rpc = runtime.lucy_respond("/dispatch-rpc test_master_node ping")
        self.assertIn("RPC Dispatched", res_rpc)


if __name__ == "__main__":
    unittest.main()
