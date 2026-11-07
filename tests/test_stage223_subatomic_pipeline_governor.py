r"""
tests/test_stage223_subatomic_pipeline_governor.py
Stage 223 Unit Tests: Sub-Atomic Micro-Architecture Pipeline Emulation & Speculative Execution Governor
"""

import threading
import unittest

from backend.lucy_core.subatomic_pipeline_governor import (
    BranchPredictor,
    GovernorMode,
    Instruction,
    Opcode,
    SubatomicPipelineGovernorFabric,
    STAGE,
    STAGE_NAME,
)


class TestStage223SubatomicPipelineGovernor(unittest.TestCase):
    def setUp(self):
        self.fabric = SubatomicPipelineGovernorFabric()

    def test_01_initialization_and_metadata(self):
        status = self.fabric.status()
        self.assertEqual(status["stage"], 223)
        self.assertEqual(status["stage_name"], STAGE_NAME)
        self.assertEqual(status["governor_mode"], "STRICT_MITIGATION")
        self.assertEqual(status["cycles"], 0)
        self.assertEqual(status["instructions_retired"], 0)
        self.assertEqual(len(status["registers"]), 8)

    def test_02_instruction_instantiation_and_dict(self):
        inst = Instruction(
            inst_id=1,
            opcode=Opcode.ADD,
            dest_reg="R1",
            src_reg1="R0",
            immediate=42,
        )
        d = inst.to_dict()
        self.assertEqual(d["inst_id"], 1)
        self.assertEqual(d["opcode"], "ADD")
        self.assertEqual(d["dest_reg"], "R1")
        self.assertEqual(d["immediate"], 42)

    def test_03_in_order_arithmetic_execution(self):
        # R1 = 10; R2 = 20; R3 = R1 + R2 (30)
        prog = [
            Instruction(1, Opcode.ADD, dest_reg="R1", immediate=10),
            Instruction(2, Opcode.ADD, dest_reg="R2", immediate=20),
            Instruction(3, Opcode.ADD, dest_reg="R3", src_reg1="R1", src_reg2="R2"),
        ]
        self.fabric.load_program(prog)
        res = self.fabric.run_until_complete(max_cycles=50)
        self.assertEqual(self.fabric.registers["R1"], 10)
        self.assertEqual(self.fabric.registers["R2"], 20)
        self.assertEqual(self.fabric.registers["R3"], 30)
        self.assertEqual(res["instructions_retired"], 3)

    def test_04_memory_store_and_load(self):
        # Store 999 at addr 16, load from 16 to R4
        prog = [
            Instruction(1, Opcode.ADD, dest_reg="R1", immediate=16),
            Instruction(2, Opcode.ADD, dest_reg="R2", immediate=999),
            Instruction(3, Opcode.STORE, src_reg1="R1", src_reg2="R2"),
            Instruction(4, Opcode.LOAD, dest_reg="R4", src_reg1="R1", immediate=0),
        ]
        self.fabric.load_program(prog)
        self.fabric.run_until_complete(max_cycles=50)
        self.assertEqual(self.fabric.memory[16], 999)
        self.assertEqual(self.fabric.registers["R4"], 999)

    def test_05_branch_predictor_state_transitions(self):
        bp = BranchPredictor(table_size=16)
        # Default state is 2 (Weakly Taken)
        self.assertTrue(bp.predict(pc=0))
        # Update with not taken -> transitions 2 -> 1 (Weakly Not Taken)
        bp.update(pc=0, actually_taken=False)
        self.assertFalse(bp.predict(pc=0))
        # Update with not taken -> transitions 1 -> 0 (Strongly Not Taken)
        bp.update(pc=0, actually_taken=False)
        self.assertFalse(bp.predict(pc=0))
        # Update with taken -> transitions 0 -> 1
        bp.update(pc=0, actually_taken=True)
        self.assertFalse(bp.predict(pc=0))
        # Update with taken -> transitions 1 -> 2 (Weakly Taken)
        bp.update(pc=0, actually_taken=True)
        self.assertTrue(bp.predict(pc=0))

    def test_06_correctly_predicted_branch_execution(self):
        # R1 = 5; R2 = 5; BRANCH_EQ R1, R2 to PC=12 (Inst 4)
        prog = [
            Instruction(1, Opcode.ADD, dest_reg="R1", immediate=5),
            Instruction(2, Opcode.ADD, dest_reg="R2", immediate=5),
            Instruction(3, Opcode.BRANCH_EQ, src_reg1="R1", src_reg2="R2", immediate=12),
            Instruction(4, Opcode.ADD, dest_reg="R3", immediate=100),  # target at PC=12
        ]
        self.fabric.load_program(prog)
        self.fabric.run_until_complete(max_cycles=50)
        self.assertEqual(self.fabric.registers["R3"], 100)
        self.assertEqual(self.fabric.branches_mispredicted, 0)

    def test_07_mispredicted_branch_rollback_and_checkpoint_recovery(self):
        # R1 = 5; R2 = 9; Predict taken (default) -> targets PC=16 (Inst 5), but condition fails!
        # Should rollback and fall through to Inst 4 (ADD R3, 77)
        prog = [
            Instruction(1, Opcode.ADD, dest_reg="R1", immediate=5),
            Instruction(2, Opcode.ADD, dest_reg="R2", immediate=9),
            Instruction(3, Opcode.BRANCH_EQ, src_reg1="R1", src_reg2="R2", immediate=16),
            Instruction(4, Opcode.ADD, dest_reg="R3", immediate=77),  # fallthrough at PC=12
            Instruction(5, Opcode.ADD, dest_reg="R4", immediate=99),  # target at PC=16
        ]
        self.fabric.load_program(prog)
        self.fabric.run_until_complete(max_cycles=60)
        self.assertEqual(self.fabric.branches_mispredicted, 1)
        self.assertGreaterEqual(self.fabric.speculative_flushes, 1)
        self.assertEqual(self.fabric.registers["R3"], 77)

    def test_08_speculative_out_of_bounds_hazard_interception(self):
        # Setup speculative load accessing invalid memory 0xFFFF
        # STRICT_MITIGATION should intercept and neutralize the load
        prog = [
            Instruction(1, Opcode.ADD, dest_reg="R1", immediate=0),
            Instruction(2, Opcode.ADD, dest_reg="R2", immediate=1),
            Instruction(3, Opcode.BRANCH_EQ, src_reg1="R1", src_reg2="R2", immediate=12),
            # Speculatively fetched instructions on predicted path (PC=12):
            Instruction(4, Opcode.LOAD, dest_reg="R6", src_reg1="R0", immediate=5000),
        ]
        self.fabric.load_program(prog)
        self.fabric.run_until_complete(max_cycles=40)
        self.assertGreaterEqual(self.fabric.hazards_intercepted, 1)

    def test_09_ascii_formatting_cp1252_safe(self):
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 223", tbl)
        self.assertIn("SUB-ATOMIC MICRO-ARCHITECTURE", tbl)
        # Verify strict CP1252 compatibility
        tbl.encode("cp1252")
        self.assertTrue(tbl.startswith("+--"))

    def test_10_multithreaded_pipeline_concurrency(self):
        def worker(w_id: int):
            for _ in range(5):
                prog = [
                    Instruction(1, Opcode.ADD, dest_reg="R1", immediate=w_id),
                    Instruction(2, Opcode.MUL, dest_reg="R2", src_reg1="R1", immediate=2),
                ]
                self.fabric.load_program(prog)
                self.fabric.run_until_complete(max_cycles=30)
                _ = self.fabric.status()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertGreater(self.fabric.cycles, 0)


if __name__ == "__main__":
    unittest.main()
