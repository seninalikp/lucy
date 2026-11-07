r"""
tests/test_stage201_multi_kernel_federation.py
Stage 201: Autonomous Multi-Kernel Federation Bus & Cross-Kernel RPC
Era 21: Autonomous Hyper-Scale Multi-Kernel Federation, Quantum-Resistant Keys & Post-Singularity Architecture
"""

import unittest
from backend.lucy_core.multi_kernel_federation import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    KernelIdentity,
    FederationMessage,
    MultiKernelFederationFabric,
)


class TestStage201MultiKernelFederation(unittest.TestCase):
    """10 Unit Tests for Stage 201 Multi-Kernel Federation Fabric."""

    def setUp(self):
        self.fabric = MultiKernelFederationFabric(local_kernel_id="test_kernel_0")

    def test_01_fabric_initialization(self):
        self.assertEqual(self.fabric.local_kernel_id, "test_kernel_0")
        self.assertEqual(len(self.fabric.kernels), 1)
        self.assertIn("test_kernel_0", self.fabric.kernels)
        self.assertEqual(self.fabric.status()["stage"], 201)
        self.assertEqual(self.fabric.status()["era"], 21)

    def test_02_remote_kernel_registration(self):
        peer = self.fabric.register_remote_kernel(
            kernel_id="kernel_satellite_1",
            name="Satellite-Worker-A",
            endpoint="ipc://satellite_1",
            capabilities=["gpu_tensor_node", "vision_embedder"],
        )
        self.assertEqual(peer.kernel_id, "kernel_satellite_1")
        self.assertEqual(len(self.fabric.kernels), 2)
        self.assertTrue(peer.is_active)

    def test_03_create_and_sign_federation_message(self):
        msg = self.fabric.create_message(
            target_id="kernel_satellite_1",
            action="ping",
            payload={"test": 123},
        )
        self.assertEqual(msg.sender_id, "test_kernel_0")
        self.assertEqual(msg.target_id, "kernel_satellite_1")
        self.assertEqual(msg.nonce, 1)
        self.assertEqual(len(msg.signature), 64)

    def test_04_dispatch_inbound_message_ping(self):
        msg = self.fabric.create_message("test_kernel_0", "ping", {})
        ok, res = self.fabric.dispatch_inbound_message(msg)
        self.assertTrue(ok)
        self.assertTrue(res.get("pong"))
        self.assertIn("server_time_ms", res)

    def test_05_dispatch_inbound_message_capabilities(self):
        msg = self.fabric.create_message("test_kernel_0", "capabilities", {})
        ok, res = self.fabric.dispatch_inbound_message(msg)
        self.assertTrue(ok)
        self.assertIn("consensus", res["capabilities"])

    def test_06_dispatch_inbound_signature_rejection(self):
        msg = self.fabric.create_message("test_kernel_0", "ping", {})
        # Tamper payload
        msg.payload["injected"] = "malicious_exploit"
        ok, res = self.fabric.dispatch_inbound_message(msg)
        self.assertFalse(ok)
        self.assertIn("Invalid cryptographic", res["error"])

    def test_07_dispatch_inbound_replay_attack_prevention(self):
        msg = self.fabric.create_message("test_kernel_0", "ping", {})
        ok1, _ = self.fabric.dispatch_inbound_message(msg)
        self.assertTrue(ok1)

        # Replay attack
        ok2, res2 = self.fabric.dispatch_inbound_message(msg)
        self.assertFalse(ok2)
        self.assertIn("Replay attack detected", res2["error"])

    def test_08_custom_rpc_handler_registration(self):
        def square_calc(payload: dict) -> dict:
            val = payload.get("val", 0)
            return {"result": val ** 2}

        self.fabric.register_rpc_handler("square", square_calc)
        msg = self.fabric.create_message("test_kernel_0", "square", {"val": 9})
        ok, res = self.fabric.dispatch_inbound_message(msg)
        self.assertTrue(ok)
        self.assertEqual(res["result"], 81)

    def test_09_discover_kernels_by_capability(self):
        self.fabric.register_remote_kernel(
            "k_gpu", "GPU-Node", "ipc://gpu", ["gpu_tensor_node", "cuda"]
        )
        self.fabric.register_remote_kernel(
            "k_cpu", "CPU-Node", "ipc://cpu", ["cpu_evaluator"]
        )

        gpu_nodes = self.fabric.discover_kernels_with_capability("gpu_tensor_node")
        self.assertEqual(len(gpu_nodes), 1)
        self.assertEqual(gpu_nodes[0].kernel_id, "k_gpu")

        empty_nodes = self.fabric.discover_kernels_with_capability("quantum_qubit")
        self.assertEqual(len(empty_nodes), 0)

    def test_10_ascii_status_and_metadata(self):
        s = self.fabric.status()
        self.assertEqual(s["stage"], 201)
        self.assertEqual(s["era"], 21)

        ascii_out = self.fabric.format_ascii_status()
        self.assertIn("STAGE 201: AUTONOMOUS MULTI-KERNEL FEDERATION BUS & RPC", ascii_out)
        self.assertIn("Era 21 (Post-Bicentennial Hyper-Federation)", ascii_out)


if __name__ == "__main__":
    unittest.main()
