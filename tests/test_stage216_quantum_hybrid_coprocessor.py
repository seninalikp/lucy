r"""
tests/test_stage216_quantum_hybrid_coprocessor.py
Stage 216: Quantum-Classical Hybrid Co-Processor & VQE (Variational Quantum Eigensolver) Emulation
Era 22: Autonomous Galactic Hyper-Mesh, Hardware-Accelerated Photonic Emulation & Trans-Universal Reasoning Fabrics
"""

import math
import unittest
from backend.lucy_core.quantum_hybrid_coprocessor import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    PauliTerm,
    QuantumHybridCoprocessorFabric,
    VQEResult,
)


class TestStage216QuantumHybridCoprocessor(unittest.TestCase):
    """10 Unit Tests for Stage 216 Quantum-Classical Hybrid Co-Processor Fabric."""

    def setUp(self):
        self.fabric = QuantumHybridCoprocessorFabric(default_qubits=2)

    def test_01_fabric_initialization(self):
        self.assertEqual(STAGE, 216)
        self.assertEqual(ERA, 22)
        self.assertEqual(self.fabric.default_qubits, 2)
        self.assertEqual(self.fabric.evaluations_count, 0)
        self.assertEqual(self.fabric.vqe_runs_count, 0)
        self.assertEqual(self.fabric.status()["stage"], 216)

    def test_02_prepare_ansatz_state_normalization(self):
        state = self.fabric.prepare_ansatz(num_qubits=2, parameters=[0.5, 1.2])
        self.assertEqual(len(state), 4)  # 2^2
        # Check total probability sum |c_i|^2 = 1.0
        total_prob = sum(abs(c) ** 2 for c in state)
        self.assertAlmostEqual(total_prob, 1.0, places=4)

    def test_03_apply_ry_zero_rotation_identity(self):
        init_state = [1.0 + 0j, 0j]
        res_state = self.fabric._apply_ry(init_state, qubit=0, num_qubits=1, theta=0.0)
        self.assertAlmostEqual(res_state[0].real, 1.0, places=4)
        self.assertAlmostEqual(res_state[1].real, 0.0, places=4)

    def test_04_apply_ry_pi_rotation_bit_flip(self):
        init_state = [1.0 + 0j, 0j]  # |0>
        # Ry(pi) |0> = |1>
        res_state = self.fabric._apply_ry(init_state, qubit=0, num_qubits=1, theta=math.pi)
        self.assertAlmostEqual(res_state[0].real, 0.0, places=4)
        self.assertAlmostEqual(res_state[1].real, 1.0, places=4)

    def test_05_apply_cnot_entanglement(self):
        # State = (|00> + |10>) / sqrt(2)
        inv_sqrt2 = 1.0 / math.sqrt(2.0)
        init_state = [inv_sqrt2 + 0j, 0j, inv_sqrt2 + 0j, 0j]
        # CNOT on qubit 0 (control), qubit 1 (target) -> (|00> + |11>) / sqrt(2)
        entangled = self.fabric._apply_cnot(init_state, control=0, target=1, num_qubits=2)
        self.assertAlmostEqual(abs(entangled[0]), inv_sqrt2, places=4)  # |00>
        self.assertAlmostEqual(abs(entangled[1]), 0.0, places=4)        # |01>
        self.assertAlmostEqual(abs(entangled[2]), 0.0, places=4)        # |10>
        self.assertAlmostEqual(abs(entangled[3]), inv_sqrt2, places=4)  # |11>

    def test_06_evaluate_pauli_term_identity(self):
        state = self.fabric.prepare_ansatz(num_qubits=2, parameters=[0.3, 0.7])
        term = PauliTerm(coeff=2.5, pauli_string="II")
        val = self.fabric.evaluate_pauli_term(state, num_qubits=2, term=term)
        self.assertAlmostEqual(val, 2.5, places=4)

    def test_07_evaluate_energy_ising_hamiltonian(self):
        # H = 1.0 * ZZ
        hamiltonian = [PauliTerm(coeff=1.0, pauli_string="ZZ")]
        # When theta=0, state is |00>, Z|0> * Z|0> = (+1)*(+1) = +1
        e0 = self.fabric.evaluate_energy(num_qubits=2, hamiltonian=hamiltonian, parameters=[0.0, 0.0])
        self.assertAlmostEqual(e0, 1.0, places=4)

    def test_08_run_vqe_energy_minimization(self):
        # Minimize H = -1.0 * ZZ (ground state has E = -1.0)
        hamiltonian = [PauliTerm(coeff=-1.0, pauli_string="ZZ")]
        result = self.fabric.run_vqe(hamiltonian, num_qubits=2, max_iterations=15, learning_rate=0.2)
        self.assertIsInstance(result, VQEResult)
        # Energy should be <= initial
        self.assertLessEqual(result.ground_state_energy, result.energy_history[0] + 0.01)
        self.assertAlmostEqual(result.ground_state_energy, -1.0, places=2)

    def test_09_vqe_result_structure(self):
        hamiltonian = [PauliTerm(coeff=0.5, pauli_string="ZI")]
        res = self.fabric.run_vqe(hamiltonian, num_qubits=2, max_iterations=5)
        d = res.to_dict()
        self.assertIn("ground_state_energy", d)
        self.assertIn("optimal_parameters", d)
        self.assertIn("energy_history", d)
        self.assertEqual(res.iterations_run, 5)

    def test_10_ascii_status_formatting(self):
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 216: QUANTUM-CLASSICAL HYBRID CO-PROCESSOR (VQE ENGINE)", tbl)
        self.assertIn("Variational Quantum Eigensolver (PQC Ansatz)", tbl)
        self.assertIn("Finite-Difference Gradient Descent", tbl)


if __name__ == "__main__":
    unittest.main()
