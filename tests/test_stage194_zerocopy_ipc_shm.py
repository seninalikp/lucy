r"""
tests/test_stage194_zerocopy_ipc_shm.py
Stage 194: Autonomous Zero-Copy Inter-Process Shared Memory Ring
Era 20: The Sovereign Bicentennial AGI Singularity & Autonomous Kernel Transcendence
"""

import unittest
from backend.lucy_core.zerocopy_ipc_shm import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    CACHE_LINE_SIZE,
    SlotState,
    SlotDescriptor,
    ZeroCopyIPCShmFabric,
)


class TestStage194ZeroCopyIPCShm(unittest.TestCase):
    """10 Unit Tests for Stage 194 Zero-Copy Inter-Process Shared Memory Ring."""

    def setUp(self):
        self.fabric = ZeroCopyIPCShmFabric(ring_name="test_ring_shm", slot_count=8, slot_size=512)

    def tearDown(self):
        self.fabric.close()

    def test_01_fabric_initialization_defaults(self):
        self.assertEqual(self.fabric.slot_count, 8)
        self.assertEqual(self.fabric.slot_mask, 7)
        self.assertEqual(self.fabric.slot_size % CACHE_LINE_SIZE, 0)
        self.assertEqual(len(self.fabric.slots), 8)
        self.assertEqual(self.fabric._head_sequence, 0)
        self.assertEqual(self.fabric._tail_sequence, 0)

    def test_02_invalid_slot_count_raises(self):
        with self.assertRaises(ValueError):
            ZeroCopyIPCShmFabric(slot_count=7)  # Not a power of 2
        with self.assertRaises(ValueError):
            ZeroCopyIPCShmFabric(slot_count=0)
        with self.assertRaises(ValueError):
            ZeroCopyIPCShmFabric(slot_count=-4)

    def test_03_lease_and_commit_lifecycle(self):
        slot_id, mem_slice = self.fabric.lease_slot()
        self.assertEqual(slot_id, 0)
        self.assertEqual(self.fabric.slots[slot_id].state, SlotState.LEASED)
        self.assertEqual(len(mem_slice), self.fabric.slot_size)

        payload = b"Hello Sovereign AGI Memory"
        desc = self.fabric.commit_slot(slot_id, payload)
        self.assertEqual(desc.state, SlotState.COMMITTED)
        self.assertEqual(desc.payload_size, len(payload))
        self.assertGreater(desc.crc32, 0)

    def test_04_read_and_consume_lifecycle(self):
        payload = b"Bicentennial Singularity Zero-Copy"
        slot_id = self.fabric.write_direct(payload)
        self.assertEqual(slot_id, 0)

        # Peek
        peek_res = self.fabric.peek_next_committed()
        self.assertIsNotNone(peek_res)
        p_id, p_view, p_size = peek_res
        self.assertEqual(p_id, 0)
        self.assertEqual(bytes(p_view), payload)

        # Read & Consume
        c_id, data, crc = self.fabric.read_next_committed()
        self.assertEqual(c_id, 0)
        self.assertEqual(data, payload)
        self.assertEqual(self.fabric.slots[0].state, SlotState.FREE)
        self.assertEqual(self.fabric._tail_sequence, 1)

    def test_05_direct_write_convenience(self):
        msg = b"Direct write payload verification"
        s_id = self.fabric.write_direct(msg)
        self.assertEqual(s_id, 0)

        res = self.fabric.read_next_committed()
        self.assertIsNotNone(res)
        self.assertEqual(res[1], msg)

    def test_06_crc32_corruption_detection(self):
        payload = b"Sensitive Sovereign Instruction"
        slot_id = self.fabric.write_direct(payload)
        slot = self.fabric.slots[slot_id]

        # Artificially tamper with underlying buffer
        self.fabric._memview[slot.offset] = ord(b"X")

        with self.assertRaises(ValueError) as ctx:
            self.fabric.read_next_committed()
        self.assertIn("CRC32 mismatch", str(ctx.exception))

    def test_07_ring_buffer_full_overflow_guard(self):
        # Fill all 8 slots
        for i in range(8):
            self.fabric.lease_slot()

        # 9th lease must raise BufferError
        with self.assertRaises(BufferError):
            self.fabric.lease_slot()

    def test_08_ring_wraparound(self):
        total_cycles = 24  # 3 full passes around 8 slots
        for i in range(total_cycles):
            msg = f"Message cycle {i}".encode("utf-8")
            s_id = self.fabric.write_direct(msg)
            self.assertEqual(s_id, i % 8)

            read_res = self.fabric.read_next_committed()
            self.assertIsNotNone(read_res)
            self.assertEqual(read_res[1], msg)

        self.assertEqual(self.fabric._head_sequence, total_cycles)
        self.assertEqual(self.fabric._tail_sequence, total_cycles)
        self.assertEqual(self.fabric._messages_committed, total_cycles)
        self.assertEqual(self.fabric._messages_consumed, total_cycles)

    def test_09_mmap_backing_mode(self):
        mmap_ring = ZeroCopyIPCShmFabric(
            ring_name="test_mmap_ring",
            slot_count=4,
            slot_size=256,
            use_mmap=True,
        )
        try:
            self.assertTrue(mmap_ring.use_mmap)
            self.assertIsNotNone(mmap_ring._mmap_obj)

            payload = b"Memory mapped direct I/O test"
            s_id = mmap_ring.write_direct(payload)
            self.assertEqual(s_id, 0)

            c_id, data, crc = mmap_ring.read_next_committed()
            self.assertEqual(data, payload)
        finally:
            mmap_ring.close()

    def test_10_ascii_status_and_metadata(self):
        s = self.fabric.status()
        self.assertEqual(s["stage"], 194)
        self.assertEqual(s["era"], 20)
        self.assertTrue(s["cache_line_aligned"])

        ascii_out = self.fabric.format_ascii_status()
        self.assertIn("STAGE 194: AUTONOMOUS ZERO-COPY IPC SHARED MEMORY RING", ascii_out)
        self.assertIn("64-Byte Aligned (Zero False-Sharing)", ascii_out)


if __name__ == "__main__":
    unittest.main()
