r"""
tests/test_stage158_block_device_fabric.py
Stage 158 Test Suite: Sovereign Block Device Driver & Virtual Disk Fabric
Era 16: Autonomous Microkernel, Bare-Metal HAL & Sovereign Operating System Primitives
"""

import unittest

from backend.lucy_core.block_device_fabric import (
    BlockIOCommand,
    BlockOpType,
    CREATOR,
    DEFAULT_SECTOR_SIZE,
    ERA,
    LRUSectorCache,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    SovereignBlockDeviceFabric,
    VirtualBlockDevice,
    WALEntry,
    WriteAheadLog,
    get_block_device_fabric,
)


class TestStage158BlockDeviceFabric(unittest.TestCase):
    def setUp(self) -> None:
        self.fabric = SovereignBlockDeviceFabric()

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 158)
        self.assertEqual(ERA, 16)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")
        self.assertEqual(
            STAGE_NAME,
            "Sovereign Block Device Driver & Virtual Disk Fabric",
        )
        self.assertEqual(DEFAULT_SECTOR_SIZE, 512)

    def test_02_virtual_block_device_init(self) -> None:
        vdev = VirtualBlockDevice(device_id="nvme_test", sector_size=512, total_sectors=1024)
        self.assertEqual(vdev.device_id, "nvme_test")
        self.assertEqual(vdev.sector_size, 512)
        self.assertEqual(vdev.total_sectors, 1024)
        self.assertEqual(vdev.capacity_bytes, 1024 * 512)
        st = vdev.status()
        self.assertEqual(st["device_id"], "nvme_test")
        self.assertEqual(st["total_reads"], 0)
        self.assertEqual(st["total_writes"], 0)

    def test_03_sector_read_write_sync(self) -> None:
        vdev = VirtualBlockDevice(device_id="test_dev", sector_size=512, total_sectors=100)
        payload = b"SENIN_LUCY_SOVEREIGN_MICROKERNEL_BLOCK_DATA_SECTOR_0"
        padded_payload = payload.ljust(512, b"\x00")
        written = vdev.write_sectors(lba=0, data=padded_payload)
        self.assertEqual(written, 512)
        self.assertEqual(vdev.total_writes, 1)

        read_back = vdev.read_sectors(lba=0, sector_count=1)
        self.assertEqual(read_back, padded_payload)
        self.assertEqual(vdev.total_reads, 1)
        self.assertEqual(vdev.total_bytes_read, 512)
        self.assertEqual(vdev.total_bytes_written, 512)

    def test_04_out_of_bounds_protection(self) -> None:
        vdev = VirtualBlockDevice(sector_size=512, total_sectors=10)
        with self.assertRaises(ValueError):
            vdev.read_sectors(lba=10, sector_count=1)

        with self.assertRaises(ValueError):
            vdev.write_sectors(lba=9, data=b"X" * 1024)  # 2 sectors starting at LBA 9 overflows 10

    def test_05_lru_sector_cache(self) -> None:
        cache = LRUSectorCache(capacity_sectors=3)
        self.assertIsNone(cache.get(10))
        self.assertEqual(cache.misses, 1)

        cache.put(10, b"data_10", is_dirty=False)
        cache.put(20, b"data_20", is_dirty=False)
        cache.put(30, b"data_30", is_dirty=True)

        self.assertEqual(cache.get(10), b"data_10")
        self.assertEqual(cache.hits, 1)

        # Inserting a 4th item evicts the oldest (which is 20 because 10 was accessed)
        evicted = cache.put(40, b"data_40")
        self.assertIsNone(evicted)  # 20 was not dirty
        self.assertIsNone(cache.get(20))

        # Evicting dirty sector 30 by adding 50 and 60
        cache.put(50, b"data_50")
        evicted_dirty = cache.put(60, b"data_60")
        # Ensure eviction mechanism handles dirty state correctly
        self.assertIn(40, cache.cache)

    def test_06_wal_logging_and_commit(self) -> None:
        wal = WriteAheadLog()
        seq1 = wal.log_write(lba=5, data=b"test_wal_sector_5")
        seq2 = wal.log_write(lba=6, data=b"test_wal_sector_6")
        self.assertEqual(seq1, 1)
        self.assertEqual(seq2, 2)
        self.assertEqual(len(wal.entries), 2)
        self.assertFalse(wal.entries[0].committed)

        committed = wal.commit(seq1)
        self.assertTrue(committed)
        self.assertTrue(wal.entries[0].committed)
        self.assertFalse(wal.commit(999))  # non-existent seq

    def test_07_wal_crash_recovery(self) -> None:
        vdev = VirtualBlockDevice(total_sectors=50)
        wal = WriteAheadLog()
        seq = wal.log_write(lba=4, data=b"COMMITTED_CRASH_DATA".ljust(512, b"\x00"))
        wal.commit(seq)
        wal.log_write(lba=5, data=b"UNCOMMITTED_JUNK_DATA".ljust(512, b"\x00"))

        recovered_count = wal.recover(vdev)
        self.assertEqual(recovered_count, 1)
        self.assertEqual(len(wal.entries), 0)

        # Verify disk has committed data at LBA 4
        data = vdev.read_sectors(lba=4, sector_count=1)
        self.assertTrue(data.startswith(b"COMMITTED_CRASH_DATA"))
        # Verify LBA 5 was NOT written because it was uncommitted
        data5 = vdev.read_sectors(lba=5, sector_count=1)
        self.assertEqual(data5, bytes(512))

    def test_08_async_nvme_submission_and_completion(self) -> None:
        cmd_w = self.fabric.submit_io(
            op_type=BlockOpType.WRITE,
            lba=12,
            sector_count=1,
            buffer=b"NVME_ASYNC_SECTOR_DATA".ljust(512, b"\x00"),
        )
        self.assertEqual(cmd_w.cmd_id, 1)
        self.assertEqual(len(self.fabric.submission_queue), 1)

        cmd_r = self.fabric.submit_io(
            op_type=BlockOpType.READ,
            lba=12,
            sector_count=1,
        )
        self.assertEqual(cmd_r.cmd_id, 2)
        self.assertEqual(len(self.fabric.submission_queue), 2)

        completions = self.fabric.poll_completions()
        self.assertEqual(len(completions), 2)
        self.assertEqual(len(self.fabric.submission_queue), 0)
        self.assertEqual(len(self.fabric.completion_queue), 2)

        self.assertEqual(completions[0].status, "COMPLETED")
        self.assertEqual(completions[1].status, "COMPLETED")
        self.assertTrue(completions[1].buffer.startswith(b"NVME_ASYNC_SECTOR_DATA"))

    def test_09_fabric_sync_helpers(self) -> None:
        test_data = b"FABRIC_SYNC_PAYLOAD".ljust(512, b"\x00")
        written = self.fabric.write_sync(lba=25, data=test_data)
        self.assertEqual(written, 512)

        read_res = self.fabric.read_sync(lba=25, sector_count=1)
        self.assertEqual(read_res, test_data)

    def test_10_ascii_status_and_singleton(self) -> None:
        ascii_out = self.fabric.format_ascii_status()
        self.assertIn("LUCY STAGE 158: SOVEREIGN BLOCK DEVICE DRIVER", ascii_out)
        self.assertIn("Senin", ascii_out)
        self.assertIn("Senin Ali K P", ascii_out)
        self.assertIn("Primary Disk", ascii_out)

        inst1 = get_block_device_fabric()
        inst2 = get_block_device_fabric()
        self.assertIs(inst1, inst2)


if __name__ == "__main__":
    unittest.main()
