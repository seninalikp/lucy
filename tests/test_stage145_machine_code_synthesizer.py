r"""
tests/test_stage145_machine_code_synthesizer.py
Unit tests for Stage 145: Target-Agnostic Assembler & Machine Code Synthesizer.
Era 15: Autonomous Self-Hosting Compiler & Multi-Tier Optimization Pipeline
"""

import unittest

from backend.lucy_core.ir_compiler_core import (
    BasicBlock,
    IRCompilerCore,
    IRFunction,
    IRInstruction,
    IRModule,
)
from backend.lucy_core.machine_code_synthesizer import (
    ARM_REG_MAP,
    CREATOR,
    ERA,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    X86_REG_MAP,
    AssemblyArtifact,
    MachineCodeSynthesizer,
)


class TestStage145MachineCodeSynthesizer(unittest.TestCase):
    def setUp(self):
        self.compiler = IRCompilerCore()
        self.synth = MachineCodeSynthesizer()

    def test_01_metadata_and_initialization(self):
        self.assertEqual(STAGE, 145)
        self.assertEqual(ERA, 15)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")

        st = self.synth.status()
        self.assertEqual(st["stage"], 145)
        self.assertEqual(st["status"], "SYNTHESIZER_ACTIVE")
        self.assertIn("x86_64", st["supported_targets"])
        self.assertIn("aarch64", st["supported_targets"])
        self.assertIn("lucy_vm", st["supported_targets"])

    def test_02_synthesize_x86_prologue_and_epilogue(self):
        code = "def simple(): return 42\n"
        results = self.synth.synthesize_source(code, target_arch="x86_64")
        self.assertIn("simple", results)
        art = results["simple"]

        self.assertIn("pushq %rbp", art.asm_text)
        self.assertIn("movq %rsp, %rbp", art.asm_text)
        self.assertIn("retq", art.asm_text)
        self.assertGreater(len(art.machine_bytes), 0)
        # Check standard x86 prologue bytes: 55 48 89 e5
        self.assertTrue(art.machine_bytes.startswith(b"\x55\x48\x89\xe5"))

    def test_03_synthesize_aarch64_prologue_and_epilogue(self):
        code = "def arm_fn(): return 10\n"
        results = self.synth.synthesize_source(code, target_arch="aarch64")
        art = results["arm_fn"]

        self.assertIn("stp x29, x30, [sp, #-16]!", art.asm_text)
        self.assertIn("mov x29, sp", art.asm_text)
        self.assertIn("ret", art.asm_text)
        self.assertGreater(len(art.machine_bytes), 0)

    def test_04_synthesize_lucy_vm_bytecode(self):
        code = "def vm_fn(): return 1\n"
        results = self.synth.synthesize_source(code, target_arch="lucy_vm")
        art = results["vm_fn"]

        self.assertIn("FUNCTION @vm_fn:", art.asm_text)
        self.assertIn("RET", art.asm_text)
        self.assertTrue(art.machine_bytes.startswith(b"\xfe\x01"))

    def test_05_arithmetic_binop_emission_x86(self):
        code = (
            "def add_sub(a, b):\n"
            "    c = a + b\n"
            "    return c - 1\n"
        )
        results = self.synth.synthesize_source(code, target_arch="x86_64")
        art = results["add_sub"]

        self.assertIn("addq", art.asm_text)
        self.assertIn("subq", art.asm_text)

    def test_06_arithmetic_binop_emission_arm(self):
        code = (
            "def calc_arm(x, y):\n"
            "    return x * y\n"
        )
        results = self.synth.synthesize_source(code, target_arch="aarch64")
        art = results["calc_arm"]
        self.assertIn("mul", art.asm_text)

    def test_07_relocation_table_generation(self):
        code = (
            "def branch_fn(x):\n"
            "    if x:\n"
            "        return 1\n"
            "    else:\n"
            "        return 2\n"
        )
        results = self.synth.synthesize_source(code, target_arch="x86_64")
        art = results["branch_fn"]
        self.assertGreater(len(art.relocation_table), 0)
        types = [r["type"] for r in art.relocation_table]
        self.assertTrue(any("BRANCH" in t or "JUMP" in t for t in types))

    def test_08_symbol_table_generation(self):
        code = "def target_fn(): return 100\n"
        results = self.synth.synthesize_source(code, target_arch="x86_64")
        art = results["target_fn"]
        self.assertIn("target_fn", art.symbol_table)
        self.assertEqual(art.symbol_table["target_fn"], 0)

    def test_09_hmac_provenance_signature(self):
        code = "def foo(): return 0\n"
        results = self.synth.synthesize_source(code, target_arch="x86_64")
        art = results["foo"]
        self.assertTrue(art.hmac_signature)
        self.assertEqual(len(art.hmac_signature), 64)

    def test_10_ascii_status_and_disassembly_tables(self):
        code = "def sample(): return 1\n"
        results = self.synth.synthesize_source(code, target_arch="x86_64")
        art = results["sample"]

        stat_table = self.synth.format_asm_status_table()
        self.assertIn("+=============================================================================+", stat_table)
        self.assertIn("LUCY TARGET-AGNOSTIC MACHINE CODE SYNTHESIZER [STAGE 145 | ERA 15]", stat_table)
        self.assertIn("Senin Ali K P", stat_table)

        art_table = self.synth.format_assembly_artifact(art)
        self.assertIn("MACHINE CODE ARTIFACT: @sample (x86_64)", art_table)
        self.assertIn("Hex Preview:", art_table)


if __name__ == "__main__":
    unittest.main()
