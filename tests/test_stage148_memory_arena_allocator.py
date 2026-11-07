r"""
tests/test_stage148_memory_arena_allocator.py
Stage 148 Test Suite: Zero-Copy Memory Arena & Memory Pool Allocator
Era 15: Autonomous Self-Hosting Compiler & Multi-Tier Optimization Pipeline
"""

import unittest

from backend.lucy_core.memory_arena_allocator import (
    CANARY_MAGIC,
    CREATOR,
    ERA,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    BumpArena,
    MemoryCorruptionError,
    MemorySlice,
    ObjectPool,
    OutOfMemoryError,
    SovereignMemoryManager,
    StringInterner,
    get_memory_manager,
)


class TestStage148MemoryArenaAllocator(unittest.TestCase):
    def setUp(self) -> None:
        self.mgr = SovereignMemoryManager()

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 148)
        self.assertEqual(ERA, 15)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")
        self.assertEqual(
            STAGE_NAME,
            "Zero-Copy Memory Arena & Memory Pool Allocator",
        )
        self.assertEqual(CANARY_MAGIC, b"\xde\xad\xbe\xef")

    def test_02_bump_arena_allocation(self) -> None:
        arena = BumpArena("test_bump", capacity_bytes=1024, enable_canaries=True)
        s1 = arena.allocate(64, alignment=8)
        self.assertEqual(s1.size, 64)
        self.assertEqual(s1.offset, 0)

        # Second allocation must be placed after s1 + canary (64 + 4 = 68) aligned to 8 -> 72
        s2 = arena.allocate(32, alignment=8)
        self.assertEqual(s2.offset, 72)
        self.assertEqual(s2.size, 32)
        self.assertEqual(arena.allocated_count, 2)

    def test_03_zero_copy_slice_rw(self) -> None:
        arena = BumpArena("slice_test", capacity_bytes=512)
        s = arena.allocate(16)
        payload = b"Hello, Lucy OS!"
        written = s.write(payload)
        self.assertEqual(written, len(payload))

        read_back = s.read(0, len(payload))
        self.assertEqual(read_back, payload)

        # Bounds check
        with self.assertRaises(ValueError):
            s.write(b"x" * 20)

    def test_04_bump_arena_reset(self) -> None:
        arena = BumpArena("reset_test", capacity_bytes=512)
        arena.allocate(100)
        arena.allocate(200)
        self.assertTrue(arena.offset >= 300)

        arena.reset()
        self.assertEqual(arena.offset, 0)
        self.assertEqual(arena.allocated_count, 0)
        self.assertEqual(len(arena.canary_locations), 0)

    def test_05_canary_integrity_sentinel(self) -> None:
        arena = BumpArena("canary_test", capacity_bytes=512, enable_canaries=True)
        s = arena.allocate(32)

        # Integrity should initially pass
        ok, violations = arena.verify_integrity()
        self.assertTrue(ok)
        self.assertEqual(len(violations), 0)

        # Deliberately corrupt canary bytes
        canary_pos = s.canary_offset
        self.assertIsNotNone(canary_pos)
        arena.buffer[canary_pos : canary_pos + 4] = b"\x00\x00\x00\x00"

        ok2, violations2 = arena.verify_integrity()
        self.assertFalse(ok2)
        self.assertEqual(len(violations2), 1)

    def test_06_arena_out_of_memory(self) -> None:
        arena = BumpArena("oom_test", capacity_bytes=100)
        with self.assertRaises(OutOfMemoryError):
            arena.allocate(200)

    def test_07_object_pool_alloc_dealloc(self) -> None:
        pool = ObjectPool("test_pool", slab_chunk_count=10)
        s1 = pool.allocate(48)  # Should map to 64B bucket
        self.assertEqual(pool.active_allocations, 1)

        s1.write(b"Data in pool block")
        self.assertEqual(s1.read(0, 4), b"Data")

        pool.deallocate(s1)
        self.assertEqual(pool.active_allocations, 0)
        self.assertEqual(pool.total_frees, 1)

    def test_08_object_pool_slab_expansion(self) -> None:
        pool = ObjectPool("expansion_pool", slab_chunk_count=4)
        slices = []
        # Allocate 10 blocks of 128B (chunk count is 4, requires 3 slabs)
        for _ in range(10):
            slices.append(pool.allocate(128))

        st = pool.status()
        self.assertEqual(st["buckets"]["128B"]["slabs"], 3)
        self.assertEqual(pool.active_allocations, 10)

        # Deallocate all
        for s in slices:
            pool.deallocate(s)
        self.assertEqual(pool.active_allocations, 0)

    def test_09_string_interner(self) -> None:
        interner = StringInterner()
        id1 = interner.intern("variable_x")
        id2 = interner.intern("variable_y")
        id3 = interner.intern("variable_x")

        self.assertEqual(id1, id3)
        self.assertNotEqual(id1, id2)
        self.assertEqual(interner.resolve(id1), "variable_x")
        self.assertEqual(interner.resolve(id2), "variable_y")
        self.assertEqual(len(interner), 2)

    def test_10_memory_audit_and_ascii_presentation(self) -> None:
        audit = self.mgr.run_memory_audit()
        self.assertTrue(audit["healthy"])
        self.assertTrue(audit["total_capacity_bytes"] > 0)

        status = self.mgr.format_ascii_status()
        self.assertIn("LUCY STAGE 148", status)
        self.assertIn("Senin", status)
        self.assertIn("compiler", status)


if __name__ == "__main__":
    unittest.main()
