"""
Unit Tests for Stage 286: Topological Majorana Zero-Mode Braiding & Parity-Protected Qubit Gate
Sovereign Architect: Senin (Senin Ali K P)
"""

import unittest
import threading
from backend.lucy_core.majorana_zero_mode_gate import (
    MajoranaZeroModeGateFabric,
    STAGE,
    STAGE_NAME,
    SOVEREIGN_OPERATOR,
)


class TestStage286MajoranaZeroModeGate(unittest.TestCase):

    def setUp(self):
        self.fabric = MajoranaZeroModeGateFabric()

    def test_01_initialization_and_metadata(self):
        st = self.fabric.status()
        self.assertEqual(st["stage"], 286)
        self.assertEqual(st["stage_name"], STAGE_NAME)
        self.assertEqual(st["sovereign_operator"], SOVEREIGN_OPERATOR)
        self.assertEqual(st["total_majoranas"], 4)
        self.assertEqual(st["braid_count"], 0)
        self.assertEqual(st["fermion_parity"], 1)

    def test_02_reset_chain_and_qubit_count(self):
        res = self.fabric.reset_chain(n_majoranas=8)
        self.assertEqual(res["total_majoranas"], 8)
        self.assertEqual(res["logical_qubits"], 2)
        self.assertEqual(res["initial_parity"], 1)

    def test_03_single_braid_transformation(self):
        # B(0,1): gamma_0 -> gamma_1, gamma_1 -> -gamma_0
        self.fabric.reset_chain(4)
        res = self.fabric.apply_braid(0, 1)
        self.assertTrue(res["fault_tolerant"])
        mapping = res["current_mapping"]
        self.assertEqual(mapping[0], (1, 1))
        self.assertEqual(mapping[1], (0, -1))

    def test_04_double_braid_phase_shift(self):
        # B(0,1)^2: gamma_0 -> -gamma_0, gamma_1 -> -gamma_1
        self.fabric.reset_chain(4)
        self.fabric.apply_braid(0, 1)
        res = self.fabric.apply_braid(0, 1)
        mapping = res["current_mapping"]
        self.assertEqual(mapping[0], (0, -1))
        self.assertEqual(mapping[1], (1, -1))

    def test_05_non_abelian_braid_non_commutativity(self):
        # B(0,1) * B(1,2) != B(1,2) * B(0,1)
        fab1 = MajoranaZeroModeGateFabric()
        fab1.apply_braid(0, 1)
        res1 = fab1.apply_braid(1, 2)

        fab2 = MajoranaZeroModeGateFabric()
        fab2.apply_braid(1, 2)
        res2 = fab2.apply_braid(0, 1)

        self.assertNotEqual(res1["current_mapping"], res2["current_mapping"])

    def test_06_clifford_phase_gate(self):
        res = self.fabric.synthesize_clifford_gate("S")
        self.assertEqual(res["gate_name"], "S")
        self.assertTrue(res["fault_tolerant"])
        self.assertEqual(res["total_braids"], 1)

    def test_07_clifford_hadamard_gate(self):
        self.fabric.reset_chain(4)
        res = self.fabric.synthesize_clifford_gate("H")
        self.assertEqual(res["gate_name"], "H")
        self.assertEqual(res["total_braids"], 3)

    def test_08_parity_measurement_logical_states(self):
        self.fabric.reset_chain(4)
        m0 = self.fabric.measure_fermion_parity()
        self.assertEqual(m0["parity_eigenvalue"], 1)
        self.assertEqual(m0["logical_state"], "|0_L>")
        self.assertTrue(m0["quasi_particle_poisoning_protected"])

    def test_09_multithreaded_concurrency(self):
        def worker(idx):
            self.fabric.apply_braid(idx % 3, (idx % 3) + 1)
            self.fabric.measure_fermion_parity()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        st = self.fabric.status()
        self.assertEqual(st["braid_count"], 10)
        self.assertEqual(st["evaluations_count"], 10)

    def test_10_ascii_formatting_and_cp1252_encoding(self):
        self.fabric.synthesize_clifford_gate("S")
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 286", tbl)
        self.assertIn("Senin (Senin Ali K P)", tbl)
        self.assertIn("Majorana Modes", tbl)
        encoded = tbl.encode("cp1252")
        self.assertIsInstance(encoded, bytes)


if __name__ == "__main__":
    unittest.main()
