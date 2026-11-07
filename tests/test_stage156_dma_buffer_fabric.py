r"""
tests/test_stage156_dma_buffer_fabric.py
Stage 156 Test Suite: Direct Memory Access (DMA) & Device Buffer Fabric
Era 16: Autonomous Microkernel, Bare-Metal HAL & Sovereign Operating System Primitives
"""

import unittest

from backend.lucy_core.dma_buffer_fabric import (
    CREATOR,
    DMA_PAGE_SIZE,
    ERA,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    DMAChannel,
    DMADescriptor,
    DMADirection,
    DMAStatus,
    MemoryPinningManager,
    SovereignDMABufferFabric,
    get_dma_fabric,
)


class TestStage156DMABufferFabric(unittest.TestCase):
    def setUp(self) -> None:
        self.fabric = SovereignDMABufferFabric()

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 156)
        self.assertEqual(ERA, 16)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")
        self.assertEqual(
            STAGE_NAME,
            "Direct Memory Access (DMA) & Device Buffer Fabric",
        )
        self.assertEqual(DMA_PAGE_SIZE, 4096)

    def test_02_memory_pinning_manager(self) -> None:
        pin_mgr = MemoryPinningManager()
        paddr = 0x200010  # Inside 4KB frame at 0x200000

        self.assertFalse(pin_mgr.is_pinned(paddr))
        cnt1 = pin_mgr.pin_frame(paddr)
        self.assertEqual(cnt1, 1)
        self.assertTrue(pin_mgr.is_pinned(paddr))

        cnt2 = pin_mgr.pin_frame(paddr)
        self.assertEqual(cnt2, 2)

        pin_mgr.unpin_frame(paddr)
        self.assertTrue(pin_mgr.is_pinned(paddr))
        pin_mgr.unpin_frame(paddr)
        self.assertFalse(pin_mgr.is_pinned(paddr))

    def test_03_dma_descriptor_creation(self) -> None:
        desc = DMADescriptor(
            desc_id=1,
            src_paddr=0x1000,
            dst_paddr=0x2000,
            byte_count=512,
            direction=DMADirection.MEMORY_TO_MEMORY,
        )
        self.assertEqual(desc.src_paddr, 0x1000)
        self.assertEqual(desc.dst_paddr, 0x2000)
        self.assertEqual(desc.byte_count, 512)
        self.assertEqual(desc.status, DMAStatus.PENDING)

    def test_04_dma_channel_submission_and_queue(self) -> None:
        chan = DMAChannel(0, "test_chan", ring_size=16)
        d1 = chan.submit_transfer(0x1000, 0x2000, 1024)
        d2 = chan.submit_transfer(0x3000, 0x4000, 2048)
        self.assertEqual(len(chan.descriptors), 2)
        self.assertEqual(chan.status()["pending_count"], 2)

    def test_05_dma_transfer_execution(self) -> None:
        chan = DMAChannel(0, "exec_chan")
        mem = bytearray(65536)
        # Write test pattern into source buffer
        pattern = b"LUCY_SOVEREIGN_DMA_PAYLOAD"
        mem[0x1000 : 0x1000 + len(pattern)] = pattern

        chan.submit_transfer(0x1000, 0x2000, len(pattern))
        executed = chan.execute_pending(mem)
        self.assertEqual(len(executed), 1)
        self.assertEqual(executed[0].status, DMAStatus.COMPLETED)
        self.assertEqual(executed[0].transferred_bytes, len(pattern))

        # Verify destination buffer received data
        self.assertEqual(mem[0x2000 : 0x2000 + len(pattern)], pattern)

    def test_06_dma_direction_modes(self) -> None:
        chan = DMAChannel(1, "modes_chan")
        d1 = chan.submit_transfer(0x100, 0x200, 64, direction=DMADirection.HOST_TO_DEVICE)
        d2 = chan.submit_transfer(0x200, 0x100, 64, direction=DMADirection.DEVICE_TO_HOST)
        self.assertEqual(d1.direction, DMADirection.HOST_TO_DEVICE)
        self.assertEqual(d2.direction, DMADirection.DEVICE_TO_HOST)

    def test_07_dma_fabric_end_to_end(self) -> None:
        src = 0x10000
        dst = 0x20000
        data = b"Microkernel Fabric Zero-Copy Data"
        self.fabric.simulated_ram[src : src + len(data)] = data

        desc = self.fabric.submit_and_execute(channel_id=0, src_paddr=src, dst_paddr=dst, byte_count=len(data))
        self.assertEqual(desc.status, DMAStatus.COMPLETED)
        self.assertEqual(self.fabric.simulated_ram[dst : dst + len(data)], data)
        # Verify unpinned after completion
        self.assertFalse(self.fabric.pinning_mgr.is_pinned(src))

    def test_08_channel_ring_eviction(self) -> None:
        chan = DMAChannel(2, "small_ring", ring_size=4)
        for i in range(10):
            chan.submit_transfer(0x1000 * i, 0x2000 * i, 128)
        self.assertEqual(len(chan.descriptors), 4)

    def test_09_multiple_dma_channels(self) -> None:
        self.assertIn(0, self.fabric.channels)
        self.assertIn(1, self.fabric.channels)
        self.assertIn(2, self.fabric.channels)
        self.assertIn(3, self.fabric.channels)
        self.assertEqual(self.fabric.channels[1].name, "dma_storage_nvme")

    def test_10_ascii_status_presentation(self) -> None:
        self.fabric.submit_and_execute(0, 0x1000, 0x2000, 128)
        status = self.fabric.format_ascii_status()
        self.assertIn("LUCY STAGE 156", status)
        self.assertIn("Senin", status)
        self.assertIn("dma_storage_nvme", status)
        self.assertIn("Total Transmit", status)


if __name__ == "__main__":
    unittest.main()
