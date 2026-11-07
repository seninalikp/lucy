r"""
tests/test_stage154_ipc_fastring_channels.py
Stage 154 Test Suite: IPC Fast-Ring & Shared Memory Channels
Era 16: Autonomous Microkernel, Bare-Metal HAL & Sovereign Operating System Primitives
"""

import unittest

from backend.lucy_core.ipc_fastring_channels import (
    CREATOR,
    ERA,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    FastRingBuffer,
    IPCEndpointRegistry,
    IPCMessageEnvelope,
    SharedMemoryChannel,
    get_ipc_registry,
)


class TestStage154IPCFastRingChannels(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = IPCEndpointRegistry()

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 154)
        self.assertEqual(ERA, 16)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")
        self.assertEqual(
            STAGE_NAME,
            "IPC Fast-Ring & Shared Memory Channels",
        )

    def test_02_message_envelope_integrity(self) -> None:
        payload = b"Lucy OS Microkernel IPC Message"
        env = IPCMessageEnvelope(
            msg_id=1,
            sender_tid=10,
            receiver_tid=20,
            msg_type="SYNC_CALL",
            payload=payload,
        )
        self.assertTrue(env.verify())
        self.assertEqual(len(env.payload), len(payload))

        # Corrupt payload
        corrupted = IPCMessageEnvelope(
            msg_id=2,
            sender_tid=10,
            receiver_tid=20,
            msg_type="SYNC_CALL",
            payload=payload,
            checksum=0x12345678,
        )
        self.assertFalse(corrupted.verify())

    def test_03_fastring_power_of_two_enforcement(self) -> None:
        # Valid powers of two
        r1 = FastRingBuffer(capacity=64)
        r2 = FastRingBuffer(capacity=128)
        self.assertEqual(r1.capacity, 64)
        self.assertEqual(r2.capacity, 128)

        # Non-powers of two must raise ValueError
        with self.assertRaises(ValueError):
            FastRingBuffer(capacity=50)
        with self.assertRaises(ValueError):
            FastRingBuffer(capacity=100)

    def test_04_fastring_push_pop_fifo(self) -> None:
        ring = FastRingBuffer(capacity=4)
        self.assertTrue(ring.is_empty())

        e1 = IPCMessageEnvelope(1, 1, 2, "MSG", b"first")
        e2 = IPCMessageEnvelope(2, 1, 2, "MSG", b"second")

        ring.push(e1)
        ring.push(e2)
        self.assertEqual(ring.size(), 2)

        out1 = ring.pop()
        self.assertEqual(out1.payload, b"first")
        out2 = ring.pop()
        self.assertEqual(out2.payload, b"second")
        self.assertTrue(ring.is_empty())

    def test_05_fastring_backpressure_drop(self) -> None:
        ring = FastRingBuffer(capacity=2)
        e1 = IPCMessageEnvelope(1, 1, 2, "MSG", b"A")
        e2 = IPCMessageEnvelope(2, 1, 2, "MSG", b"B")
        e3 = IPCMessageEnvelope(3, 1, 2, "MSG", b"C")

        self.assertTrue(ring.push(e1))
        self.assertTrue(ring.push(e2))
        self.assertTrue(ring.is_full())

        # 3rd push fails (backpressure drop)
        self.assertFalse(ring.push(e3))
        self.assertEqual(ring.total_dropped, 1)

    def test_06_shared_memory_channel_bidirectional(self) -> None:
        chan = SharedMemoryChannel("test_bi_channel", capacity=8)
        # Forward send (A -> B)
        mid_fwd = chan.send(sender_tid=1, receiver_tid=2, msg_type="REQ", payload=b"ping", is_forward=True)
        self.assertIsNotNone(mid_fwd)

        # Backward send (B -> A)
        mid_bwd = chan.send(sender_tid=2, receiver_tid=1, msg_type="RESP", payload=b"pong", is_forward=False)
        self.assertIsNotNone(mid_bwd)

        recv_b = chan.receive(is_forward=True)
        self.assertEqual(recv_b.payload, b"ping")

        recv_a = chan.receive(is_forward=False)
        self.assertEqual(recv_a.payload, b"pong")

    def test_07_endpoint_registry_routing(self) -> None:
        # Route to built-in port://vfs
        mid = self.registry.send_to_port("port://vfs", sender_tid=5, msg_type="OPEN", payload=b"/etc/config")
        self.assertIsNotNone(mid)

        env = self.registry.receive_from_port("port://vfs")
        self.assertIsNotNone(env)
        self.assertEqual(env.payload, b"/etc/config")
        self.assertEqual(env.sender_tid, 5)

    def test_08_custom_endpoint_registration(self) -> None:
        ok = self.registry.register_endpoint("port://gpu", owner_tid=99)
        self.assertTrue(ok)
        self.assertEqual(self.registry.endpoints["port://gpu"], 99)

        # Duplicate registration fails
        dup = self.registry.register_endpoint("port://gpu", owner_tid=100)
        self.assertFalse(dup)

    def test_09_high_throughput_burst(self) -> None:
        chan = SharedMemoryChannel("perf_chan", capacity=1024)
        count = 500
        for i in range(count):
            chan.send(sender_tid=1, receiver_tid=2, msg_type="BURST", payload=f"msg_{i}".encode("ascii"))

        popped_count = 0
        for i in range(count):
            msg = chan.receive()
            self.assertIsNotNone(msg)
            self.assertEqual(msg.payload, f"msg_{i}".encode("ascii"))
            popped_count += 1
        self.assertEqual(popped_count, count)

    def test_10_ascii_status_presentation(self) -> None:
        self.registry.send_to_port("port://hal", sender_tid=1, msg_type="RESET", payload=b"probe")
        status = self.registry.format_ascii_status()
        self.assertIn("LUCY STAGE 154", status)
        self.assertIn("Senin", status)
        self.assertIn("port://vfs", status)
        self.assertIn("port://hal", status)


if __name__ == "__main__":
    unittest.main()
