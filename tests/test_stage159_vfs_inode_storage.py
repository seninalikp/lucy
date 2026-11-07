r"""
tests/test_stage159_vfs_inode_storage.py
Stage 159 Test Suite: Microkernel VFS & Content-Addressable Inode Storage
Era 16: Autonomous Microkernel, Bare-Metal HAL & Sovereign Operating System Primitives
"""

import os
import unittest

from backend.lucy_core.vfs_inode_storage import (
    CREATOR,
    DEFAULT_BLOCK_SIZE,
    ERA,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    CASBlock,
    ContentAddressableStore,
    FileDescriptor,
    Inode,
    InodeType,
    OpenFlags,
    VirtualFileSystem,
    get_vfs,
)


class TestStage159VFSInodeStorage(unittest.TestCase):
    def setUp(self) -> None:
        self.vfs = VirtualFileSystem()

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 159)
        self.assertEqual(ERA, 16)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")
        self.assertEqual(
            STAGE_NAME,
            "Microkernel VFS & Content-Addressable Inode Storage",
        )
        self.assertEqual(DEFAULT_BLOCK_SIZE, 4096)

    def test_02_cas_block_deduplication(self) -> None:
        cas = ContentAddressableStore(block_size=512)
        chunk1 = b"SENIN_LUCY_IDENTICAL_BLOCK_PAYLOAD"
        chunk2 = b"SENIN_LUCY_IDENTICAL_BLOCK_PAYLOAD"

        h1 = cas.put_chunk(chunk1)
        self.assertEqual(len(cas.blocks), 1)
        self.assertEqual(cas.blocks[h1].ref_count, 1)

        h2 = cas.put_chunk(chunk2)
        self.assertEqual(h1, h2)
        self.assertEqual(len(cas.blocks), 1)
        self.assertEqual(cas.blocks[h1].ref_count, 2)
        self.assertEqual(cas.total_dedup_hits, 1)
        self.assertEqual(cas.dedup_bytes_saved, len(chunk1))

        # Releasing one reference
        cas.release_chunk(h1)
        self.assertEqual(cas.blocks[h1].ref_count, 1)
        self.assertEqual(cas.get_chunk(h1), chunk1)

    def test_03_vfs_initialization_and_root(self) -> None:
        root = self.vfs.resolve_path("/")
        self.assertIsNotNone(root)
        self.assertEqual(root.name, "/")
        self.assertEqual(root.itype, InodeType.DIRECTORY)
        self.assertIn("dev", root.children)
        self.assertIn("sys", root.children)
        self.assertIn("tmp", root.children)
        self.assertIn("/", self.vfs.mount_table)
        self.assertIn("/dev", self.vfs.mount_table)

    def test_04_mkdir_and_directory_traversal(self) -> None:
        new_dir = self.vfs.mkdir("/var")
        self.assertEqual(new_dir.name, "var")
        self.assertEqual(new_dir.itype, InodeType.DIRECTORY)

        sub_dir = self.vfs.mkdir("/var/log")
        self.assertEqual(sub_dir.name, "log")

        resolved = self.vfs.resolve_path("/var/log")
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.inode_id, sub_dir.inode_id)

        # Duplicate mkdir raises FileExistsError
        with self.assertRaises(FileExistsError):
            self.vfs.mkdir("/var/log")

        # Nonexistent parent raises FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            self.vfs.mkdir("/nonexistent/folder")

    def test_05_file_creation_and_open_flags(self) -> None:
        # File creation with O_CREAT
        fd = self.vfs.sys_open("/tmp/senin_test.txt", flags=OpenFlags.O_CREAT | OpenFlags.O_WRONLY)
        self.assertGreaterEqual(fd, 3)
        self.assertIn(fd, self.vfs.open_files)

        # Verify inode created
        inode = self.vfs.resolve_path("/tmp/senin_test.txt")
        self.assertIsNotNone(inode)
        self.assertEqual(inode.itype, InodeType.FILE)

        self.vfs.sys_close(fd)
        self.assertNotIn(fd, self.vfs.open_files)

        # Opening non-existent file without O_CREAT raises FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            self.vfs.sys_open("/tmp/ghost_file.bin", flags=OpenFlags.O_RDONLY)

    def test_06_sys_write_and_sys_read(self) -> None:
        fd_w = self.vfs.sys_open("/tmp/data.bin", flags=OpenFlags.O_CREAT | OpenFlags.O_RDWR)
        payload = b"MICROKERNEL_SOVEREIGN_STORAGE_BLOCK_DATA_PAYLOAD"
        written = self.vfs.sys_write(fd_w, payload)
        self.assertEqual(written, len(payload))

        # Seek to beginning
        self.vfs.sys_lseek(fd_w, 0, os.SEEK_SET)
        data = self.vfs.sys_read(fd_w, 1024)
        self.assertEqual(data, payload)
        self.vfs.sys_close(fd_w)

        # Open read-only
        fd_r = self.vfs.sys_open("/tmp/data.bin", flags=OpenFlags.O_RDONLY)
        read_payload = self.vfs.sys_read(fd_r, len(payload))
        self.assertEqual(read_payload, payload)

        # Attempting write on read-only FD raises PermissionError
        with self.assertRaises(PermissionError):
            self.vfs.sys_write(fd_r, b"ILLEGAL_WRITE")
        self.vfs.sys_close(fd_r)

    def test_07_sys_lseek_offsets(self) -> None:
        fd = self.vfs.sys_open("/tmp/seek_test.txt", flags=OpenFlags.O_CREAT | OpenFlags.O_RDWR)
        self.vfs.sys_write(fd, b"0123456789ABCDEF")

        # SEEK_SET
        off = self.vfs.sys_lseek(fd, 5, os.SEEK_SET)
        self.assertEqual(off, 5)
        self.assertEqual(self.vfs.sys_read(fd, 3), b"567")

        # SEEK_CUR
        off = self.vfs.sys_lseek(fd, 2, os.SEEK_CUR)
        self.assertEqual(off, 10)
        self.assertEqual(self.vfs.sys_read(fd, 2), b"AB")

        # SEEK_END
        off = self.vfs.sys_lseek(fd, -4, os.SEEK_END)
        self.assertEqual(off, 12)
        self.assertEqual(self.vfs.sys_read(fd, 4), b"CDEF")

        # Negative offset raises ValueError
        with self.assertRaises(ValueError):
            self.vfs.sys_lseek(fd, -1, os.SEEK_SET)

        self.vfs.sys_close(fd)

    def test_08_sys_unlink_and_cas_cleanup(self) -> None:
        fd = self.vfs.sys_open("/tmp/temp.log", flags=OpenFlags.O_CREAT | OpenFlags.O_WRONLY)
        self.vfs.sys_write(fd, b"TEMPORARY_LOG_RECORDS")
        self.vfs.sys_close(fd)

        inode = self.vfs.resolve_path("/tmp/temp.log")
        self.assertIsNotNone(inode)
        block_hash = inode.block_hashes[0]
        self.assertIn(block_hash, self.vfs.cas.blocks)

        # Unlink file
        ok = self.vfs.sys_unlink("/tmp/temp.log")
        self.assertTrue(ok)
        self.assertIsNone(self.vfs.resolve_path("/tmp/temp.log"))
        # Verify block cleaned up from CAS
        self.assertNotIn(block_hash, self.vfs.cas.blocks)

        # Cannot unlink root
        with self.assertRaises(PermissionError):
            self.vfs.sys_unlink("/")

    def test_09_mount_table_and_devices(self) -> None:
        self.vfs.mount("/mnt/disk1", device="nvme0n1", fs_type="lucyfs")
        self.assertIn("/mnt/disk1", self.vfs.mount_table)
        mnt_info = self.vfs.mount_table["/mnt/disk1"]
        self.assertEqual(mnt_info["device"], "nvme0n1")
        self.assertEqual(mnt_info["fs_type"], "lucyfs")

        # Readdir on root
        entries = self.vfs.sys_readdir("/")
        names = [e["name"] for e in entries]
        self.assertIn("dev", names)
        self.assertIn("sys", names)
        self.assertIn("tmp", names)

    def test_10_ascii_status_and_singleton(self) -> None:
        ascii_out = self.vfs.format_ascii_status()
        self.assertIn("LUCY STAGE 159: MICROKERNEL VFS & CONTENT-ADDRESSABLE INODE STORAGE", ascii_out)
        self.assertIn("Senin", ascii_out)
        self.assertIn("Senin Ali K P", ascii_out)
        self.assertIn("Active Inodes", ascii_out)
        self.assertIn("CAS Unique Blks", ascii_out)

        v1 = get_vfs()
        v2 = get_vfs()
        self.assertIs(v1, v2)


if __name__ == "__main__":
    unittest.main()
