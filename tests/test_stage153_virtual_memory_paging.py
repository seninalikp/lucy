r"""
tests/test_stage153_virtual_memory_paging.py
Stage 153 Test Suite: Virtual Memory Management & Page Table Synthesizer
Era 16: Autonomous Microkernel, Bare-Metal HAL & Sovereign Operating System Primitives
"""

import unittest

from backend.lucy_core.virtual_memory_paging import (
    CREATOR,
    ERA,
    OPERATOR,
    PAGE_SIZE_4KB,
    PF_NOT_PRESENT,
    PF_NX_VIOLATION,
    PF_PROTECTION_VIOLATION,
    PF_USER_VIOLATION,
    PTE_NX,
    PTE_PRESENT,
    PTE_USER,
    PTE_WRITABLE,
    STAGE,
    STAGE_NAME,
    PageFaultError,
    PhysicalFrameAllocator,
    TranslationLookasideBuffer,
    VirtualMemoryPagingEngine,
    get_paging_engine,
)


class TestStage153VirtualMemoryPaging(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = VirtualMemoryPagingEngine()

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 153)
        self.assertEqual(ERA, 16)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")
        self.assertEqual(
            STAGE_NAME,
            "Virtual Memory Management & Page Table Synthesizer",
        )
        self.assertEqual(PAGE_SIZE_4KB, 4096)

    def test_02_vaddr_decomposition(self) -> None:
        # Virtual address: 0x00007FFFF0123ABC
        vaddr = 0x00007FFFF0123ABC
        pml4_i, pdpt_i, pd_i, pt_i, offset = self.engine.decompose_vaddr(vaddr)

        # 12-bit offset
        self.assertEqual(offset, 0xABC)
        # All indices must fit in 9 bits (0..511)
        self.assertTrue(0 <= pml4_i < 512)
        self.assertTrue(0 <= pdpt_i < 512)
        self.assertTrue(0 <= pd_i < 512)
        self.assertTrue(0 <= pt_i < 512)

    def test_03_physical_frame_allocator(self) -> None:
        pfa = PhysicalFrameAllocator(total_frames=1024)
        # First 256 frames reserved (up to 1MB)
        f1 = pfa.allocate_frame()
        self.assertEqual(f1, 256 * 4096)  # 0x100000 (1MB)
        self.assertEqual(f1 % 4096, 0)

        f2 = pfa.allocate_frame()
        self.assertEqual(f2, 257 * 4096)

        # Free f1 and re-allocate
        ok = pfa.free_frame(f1)
        self.assertTrue(ok)
        f1_realloc = pfa.allocate_frame()
        self.assertEqual(f1_realloc, f1)

    def test_04_map_and_translate_page(self) -> None:
        vaddr = 0x400000 + 0x123
        paddr = self.engine.map_page(vaddr, flags=PTE_PRESENT | PTE_WRITABLE)
        self.assertTrue(paddr >= 0x100000)

        translated_phys, flags = self.engine.translate(vaddr, is_write=True)
        self.assertEqual(translated_phys, paddr + 0x123)
        self.assertTrue(flags & PTE_PRESENT)
        self.assertTrue(flags & PTE_WRITABLE)

    def test_05_page_fault_not_present(self) -> None:
        unmapped = 0xDEADBEEF000
        with self.assertRaises(PageFaultError) as cm:
            self.engine.translate(unmapped)
        self.assertEqual(cm.exception.reason, PF_NOT_PRESENT)

    def test_06_page_fault_write_protection(self) -> None:
        vaddr = 0x800000
        # Map read-only (no PTE_WRITABLE)
        self.engine.map_page(vaddr, flags=PTE_PRESENT)

        # Reading succeeds
        p, f = self.engine.translate(vaddr, is_write=False)
        self.assertTrue(p > 0)

        # Writing fails
        with self.assertRaises(PageFaultError) as cm:
            self.engine.translate(vaddr, is_write=True)
        self.assertEqual(cm.exception.reason, PF_PROTECTION_VIOLATION)

    def test_07_page_fault_nx_violation(self) -> None:
        vaddr = 0x900000
        # Map with NX bit set
        self.engine.map_page(vaddr, flags=PTE_PRESENT | PTE_WRITABLE | PTE_NX)

        # Execute fails
        with self.assertRaises(PageFaultError) as cm:
            self.engine.translate(vaddr, is_exec=True)
        self.assertEqual(cm.exception.reason, PF_NX_VIOLATION)

    def test_08_tlb_caching_and_invalidation(self) -> None:
        vaddr = 0x500000
        self.engine.map_page(vaddr)

        # First lookup: TLB miss
        init_misses = self.engine.tlb.misses
        init_hits = self.engine.tlb.hits
        self.engine.translate(vaddr)
        self.assertEqual(self.engine.tlb.misses, init_misses + 1)

        # Second lookup: TLB hit
        self.engine.translate(vaddr)
        self.assertEqual(self.engine.tlb.hits, init_hits + 1)

        # Invalidate TLB
        vpn = (vaddr & ~0xFFF) >> 12
        inv = self.engine.tlb.invalidate(vpn)
        self.assertTrue(inv)
        # Next lookup misses again
        self.engine.translate(vaddr)
        self.assertEqual(self.engine.tlb.misses, init_misses + 2)

    def test_09_unmap_page_and_frame_reclaim(self) -> None:
        vaddr = 0x600000
        phys = self.engine.map_page(vaddr)
        self.assertEqual(self.engine.mapped_pages_count, 1)

        ok_unmap = self.engine.unmap_page(vaddr, free_frame=True)
        self.assertTrue(ok_unmap)
        self.assertEqual(self.engine.mapped_pages_count, 0)

        # Translating now raises page fault
        with self.assertRaises(PageFaultError):
            self.engine.translate(vaddr)

    def test_10_ascii_status_presentation(self) -> None:
        self.engine.map_page(0x100000)
        self.engine.map_page(0x200000)
        self.engine.translate(0x100000)

        status = self.engine.format_ascii_status()
        self.assertIn("LUCY STAGE 153", status)
        self.assertIn("Senin", status)
        self.assertIn("Mapped Pages", status)
        self.assertIn("TLB Hit Ratio", status)


if __name__ == "__main__":
    unittest.main()
