r"""
tests/test_stage147_aot_native_linker.py
Stage 147 Test Suite: Ahead-Of-Time (AOT) Sovereign Native Linker & PE/ELF Formatter
Era 15: Autonomous Self-Hosting Compiler & Multi-Tier Optimization Pipeline
"""

import os
import struct
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.aot_native_linker import (
    CREATOR,
    ERA,
    OPERATOR,
    RELOC_ABS64,
    RELOC_REL32,
    STAGE,
    STAGE_NAME,
    AOTNativeLinker,
    BinaryArtifact,
    RelocationEntry,
    SectionDefinition,
    get_aot_native_linker,
)
from backend.lucy_core.machine_code_synthesizer import AssemblyArtifact


class TestStage147AOTNativeLinker(unittest.TestCase):
    def setUp(self) -> None:
        self.linker = AOTNativeLinker()

    def test_01_metadata_and_initialization(self) -> None:
        self.assertEqual(STAGE, 147)
        self.assertEqual(ERA, 15)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")
        self.assertEqual(
            STAGE_NAME,
            "Ahead-Of-Time (AOT) Sovereign Native Linker & PE/ELF Formatter",
        )
        self.assertIsNotNone(self.linker.storage_dir)

    def test_02_pe_emission_and_headers(self) -> None:
        # Simple x86_64 code: mov eax, 42; ret
        code = b"\xb8\x2a\x00\x00\x00\xc3"
        data = b"Hello, Sovereign World!\x00"

        artifact = self.linker.link_pe(code_bytes=code, data_bytes=data, target_arch="x86_64")
        self.assertEqual(artifact.format_target, "pe")
        self.assertEqual(artifact.target_arch, "x86_64")

        # Validate PE Header
        val = self.linker.validate_binary_header(artifact.binary_bytes)
        self.assertTrue(val["valid"])
        self.assertEqual(val["format"], "pe")
        self.assertEqual(val["machine"], hex(0x8664))
        self.assertEqual(val["num_sections"], 2)

        # Raw check
        self.assertTrue(artifact.binary_bytes.startswith(b"MZ"))

    def test_03_elf_emission_and_headers(self) -> None:
        code = b"\xb8\x2a\x00\x00\x00\xc3"
        data = b"Lucy OS Native ELF\x00"

        artifact = self.linker.link_elf(code_bytes=code, data_bytes=data, target_arch="x86_64")
        self.assertEqual(artifact.format_target, "elf")
        self.assertEqual(artifact.target_arch, "x86_64")

        # Validate ELF Header
        val = self.linker.validate_binary_header(artifact.binary_bytes)
        self.assertTrue(val["valid"])
        self.assertEqual(val["format"], "elf")
        self.assertEqual(val["type"], 2)  # ET_EXEC
        self.assertEqual(val["machine"], hex(0x3E))

        self.assertTrue(artifact.binary_bytes.startswith(b"\x7fELF"))

    def test_04_sovereign_bin_emission(self) -> None:
        code = b"\x90\x90\xc3"
        data = b"Sovereign Secret Data"

        artifact = self.linker.link_sovereign_bin(code_bytes=code, data_bytes=data, target_arch="x86_64")
        self.assertEqual(artifact.format_target, "sovereign_bin")

        val = self.linker.validate_binary_header(artifact.binary_bytes)
        self.assertTrue(val["valid"])
        self.assertEqual(val["format"], "sovereign_bin")
        self.assertEqual(val["arch"], "x86_64")
        self.assertTrue(artifact.binary_bytes.startswith(b"SOV_BIN\x01"))

    def test_05_relocation_resolution(self) -> None:
        # Buffer containing placeholder call 0x00000000 (e8 00 00 00 00)
        code_buf = bytearray(b"\x90\xe8\x00\x00\x00\x00\xc3")
        code_base_va = 0x140001000

        # Target symbol 'target_func' at 0x140001050
        symbols = {"target_func": 0x140001050}
        relocs = [
            RelocationEntry(
                section_name=".text",
                offset=2,  # offset of 32-bit displacement
                symbol="target_func",
                reloc_type=RELOC_REL32,
            )
        ]

        # Expected displacement: target_va - (site_va + 4)
        # site_va = 0x140001000 + 2 = 0x140001002
        # site_va + 4 = 0x140001006
        # displacement = 0x140001050 - 0x140001006 = 0x4A = 74
        res = self.linker.resolve_relocations(code_buf, relocs, symbols, code_base_va)
        displacement = struct.unpack("<i", res[2:6])[0]
        self.assertEqual(displacement, 74)

        # Test ABS64
        buf64 = bytearray(b"\x48\xb8" + (b"\x00" * 8) + b"\xc3")
        relocs_abs = [
            RelocationEntry(
                section_name=".text",
                offset=2,
                symbol="target_func",
                reloc_type=RELOC_ABS64,
            )
        ]
        res64 = self.linker.resolve_relocations(buf64, relocs_abs, symbols, code_base_va)
        abs_val = struct.unpack("<Q", res64[2:10])[0]
        self.assertEqual(abs_val, 0x140001050)

    def test_06_assembly_artifact_linking(self) -> None:
        # Create an AssemblyArtifact as if synthesized by Stage 145
        asm_art = AssemblyArtifact(
            target_arch="x86_64",
            func_name="compute_core",
            asm_text="mov eax, 100\nret",
            machine_bytes=b"\xb8\x64\x00\x00\x00\xc3",
            relocation_table=[],
            symbol_table={"compute_core": 0},
            hmac_signature="dummy-sig-145",
        )

        pe_bin = self.linker.link_assembly_artifact(asm_art, format_target="pe")
        self.assertEqual(pe_bin.format_target, "pe")
        self.assertTrue(len(pe_bin.binary_bytes) > 512)

        elf_bin = self.linker.link_assembly_artifact(asm_art, format_target="elf")
        self.assertEqual(elf_bin.format_target, "elf")
        self.assertTrue(len(elf_bin.binary_bytes) > 512)

    def test_07_binary_validation(self) -> None:
        invalid = b"\x00" * 10
        val = self.linker.validate_binary_header(invalid)
        self.assertFalse(val["valid"])

        garbage = b"random garbage that is long enough to meet minimum size checks"
        val_garb = self.linker.validate_binary_header(garbage)
        self.assertFalse(val_garb["valid"])

    def test_08_save_to_disk(self) -> None:
        code = b"\xcc\xc3"
        artifact = self.linker.link_sovereign_bin(code_bytes=code)
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "test_bin.sov"
            saved_path = artifact.save(out_file)
            self.assertTrue(saved_path.exists())
            self.assertEqual(saved_path.read_bytes(), artifact.binary_bytes)

    def test_09_alignment_and_padding(self) -> None:
        self.assertEqual(self.linker.align_up(100, 512), 512)
        self.assertEqual(self.linker.align_up(512, 512), 512)
        self.assertEqual(self.linker.align_up(513, 512), 1024)

        data = b"123"
        padded = self.linker.pad_bytes(data, 16)
        self.assertEqual(len(padded), 16)
        self.assertEqual(padded[:3], b"123")

    def test_10_ascii_presentation(self) -> None:
        code = b"\xb8\x01\x00\x00\x00\xc3"
        artifact = self.linker.link_pe(code_bytes=code)

        status = self.linker.format_ascii_status()
        self.assertIn("LUCY STAGE 147", status)
        self.assertIn("Senin", status)

        table = self.linker.format_ascii_artifact_table(artifact)
        self.assertIn("BINARY ARTIFACT:", table)
        self.assertIn(".text", table)
        self.assertIn(".data", table)


if __name__ == "__main__":
    unittest.main()
