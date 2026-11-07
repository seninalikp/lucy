"""
Unit Tests for Stage 291: Topological Toric Code Quantum Memory & Anyonic Stabilizer Fabric
Sovereign Architect: Senin (Senin Ali K P)
"""

import math
import threading
import unittest
from backend.lucy_core.topological_quantum_memory import (
    TopologicalQuantumMemoryFabric,
    STAGE,
    STAGE_NAME,
    SOVEREIGN_OPERATOR,
)


class TestStage291TopologicalQuantumMemory(unittest.TestCase):

    def setUp(self):
        self.fabric = TopologicalQuantumMemoryFabric(lattice_size=4)

    def test_01_initialization_and_metadata(self):
        st = self.fabric.status()
        self.assertEqual(st["stage"], 291)
        self.assertEqual(st["stage_name"], STAGE_NAME)
        self.assertEqual(st["sovereign_operator"], SOVEREIGN_OPERATOR)
        self.assertEqual(st["lattice_size"], 4)
        self.assertEqual(st["physical_qubits"], 32) # 2 * 4 * 4
        self.assertEqual(st["logical_qubits"], 2)
        self.assertEqual(st["code_distance"], 4)
        self.assertEqual(st["status"], "OPERATIONAL")

    def test_02_clean_ground_state_has_zero_syndromes(self):
        state = self.fabric.evaluate_state()
        self.assertEqual(len(state.star_syndromes), 0)
        self.assertEqual(len(state.plaquette_syndromes), 0)
        self.assertEqual(state.logical_z1_eigenvalue, 1)
        self.assertEqual(state.logical_z2_eigenvalue, 1)
        self.assertEqual(state.active_error_count, 0)

    def test_03_single_qubit_x_error_creates_anyon_pair(self):
        # Single X error on edge creates exactly 2 star syndromes (e-anyons at endpoints)
        self.fabric.inject_pauli_error(1, 1, 0, "X")
        stars = self.fabric.measure_star_syndromes()
        self.assertEqual(len(stars), 2)
        self.assertIn((1, 1), stars)
        self.assertIn((1, 2), stars) # right neighbor of (1, 1, 0)
        # Plaquette syndromes should be completely unaffected
        plaquettes = self.fabric.measure_plaquette_syndromes()
        self.assertEqual(len(plaquettes), 0)

    def test_04_single_qubit_z_error_creates_flux_pair(self):
        # Single Z error on edge creates exactly 2 plaquette syndromes (m-anyons on adjacent faces)
        self.fabric.inject_pauli_error(2, 2, 1, "Z")
        plaquettes = self.fabric.measure_plaquette_syndromes()
        self.assertEqual(len(plaquettes), 2)
        # Star syndromes should be unaffected
        stars = self.fabric.measure_star_syndromes()
        self.assertEqual(len(stars), 0)

    def test_05_closed_error_loop_is_syndrome_free(self):
        # Injecting a contractible closed loop of X errors around plaquette (1, 1)
        # Edges: (1, 1, 0), (2, 1, 0), (1, 1, 1), (1, 2, 1)
        self.fabric.inject_pauli_error(1, 1, 0, "X")
        self.fabric.inject_pauli_error(2, 1, 0, "X")
        self.fabric.inject_pauli_error(1, 1, 1, "X")
        self.fabric.inject_pauli_error(1, 2, 1, "X")
        stars = self.fabric.measure_star_syndromes()
        # A closed loop has no endpoints, so no star defects!
        self.assertEqual(len(stars), 0)

    def test_06_topological_entanglement_entropy(self):
        # gamma = ln(2) for Z2 topological order
        gamma = self.fabric.topological_entanglement_entropy()
        self.assertAlmostEqual(gamma, math.log(2.0), places=6)

    def test_07_logical_qubit_error_detection(self):
        # A non-contractible line of errors flips logical eigenvalue
        self.fabric.inject_pauli_error(0, 0, 1, "X")
        z1, z2 = self.fabric.measure_logical_operators()
        self.assertEqual(z1, -1)
        self.assertEqual(z2, 1)

    def test_08_syndrome_decoding_and_annihilation(self):
        self.fabric.inject_pauli_error(0, 0, 0, "X")
        res = self.fabric.decode_and_correct_syndromes()
        self.assertEqual(res["initial_star_defects"], 2)
        self.assertEqual(res["corrections_applied"], 1)
        self.assertEqual(res["residual_star_defects"], 0)
        self.assertTrue(res["stabilized"])

    def test_09_multithreaded_concurrency(self):
        results = []

        def worker():
            st = self.fabric.evaluate_state()
            results.append(st.num_physical_qubits)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), 10)
        self.assertTrue(all(q == 32 for q in results))

    def test_10_invalid_lattice_size_raises(self):
        with self.assertRaises(ValueError):
            TopologicalQuantumMemoryFabric(lattice_size=1)


if __name__ == "__main__":
    unittest.main()
