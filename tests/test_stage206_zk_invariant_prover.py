r"""
tests/test_stage206_zk_invariant_prover.py
Stage 206: Autonomous Zero-Knowledge Proof Invariant Generator
Era 21: Autonomous Hyper-Scale Multi-Kernel Federation, Quantum-Resistant Keys & Post-Singularity Architecture
"""

import unittest
from backend.lucy_core.zk_invariant_prover import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    PRIME_FIELD,
    R1CSConstraint,
    ZKProof,
    ZKInvariantProverFabric,
)


class TestStage206ZKInvariantProver(unittest.TestCase):
    """10 Unit Tests for Stage 206 ZK Invariant Prover Fabric."""

    def setUp(self):
        self.fabric = ZKInvariantProverFabric()

    def test_01_fabric_initialization(self):
        self.assertGreaterEqual(len(self.fabric.circuits), 2)
        self.assertEqual(self.fabric.status()["stage"], 206)
        self.assertEqual(self.fabric.status()["era"], 21)
        self.assertEqual(self.fabric.field_prime, PRIME_FIELD)
        self.assertEqual(self.fabric.field_prime.bit_length(), 254)

    def test_02_r1cs_constraint_evaluation_pass(self):
        # 3 * 4 = 12
        constraint = R1CSConstraint(a={"x": 1}, b={"y": 1}, c={"z": 1})
        witness = {"x": 3, "y": 4, "z": 12}
        self.assertTrue(constraint.evaluate(witness, PRIME_FIELD))

    def test_03_r1cs_constraint_evaluation_fail(self):
        constraint = R1CSConstraint(a={"x": 1}, b={"y": 1}, c={"z": 1})
        witness = {"x": 3, "y": 4, "z": 13}
        self.assertFalse(constraint.evaluate(witness, PRIME_FIELD))

    def test_04_multiplier_circuit_proof_generation(self):
        witness = {"w_a": 7, "w_b": 11}
        public_inputs = {"public_c": 77}
        proof = self.fabric.prove_statement("circuit_multiplier", witness, public_inputs)
        self.assertIsNotNone(proof)
        self.assertEqual(proof.circuit_id, "circuit_multiplier")
        self.assertEqual(proof.public_inputs["public_c"], 77)

    def test_05_multiplier_circuit_invalid_witness_fails(self):
        witness = {"w_a": 7, "w_b": 10}  # 7 * 10 = 70 != 77
        public_inputs = {"public_c": 77}
        with self.assertRaises(ValueError):
            self.fabric.prove_statement("circuit_multiplier", witness, public_inputs)

    def test_06_verify_zk_proof_pass(self):
        proof = self.fabric.prove_statement(
            "circuit_multiplier",
            witness={"w_a": 12, "w_b": 12},
            public_inputs={"public_c": 144},
        )
        ok = self.fabric.verify_proof(proof)
        self.assertTrue(ok)
        self.assertEqual(self.fabric._proofs_verified_pass, 1)

    def test_07_verify_zk_proof_challenge_tamper_fails(self):
        proof = self.fabric.prove_statement(
            "circuit_multiplier",
            witness={"w_a": 5, "w_b": 5},
            public_inputs={"public_c": 25},
        )
        # Corrupt challenge
        proof.challenge = "tampered_challenge_000000000000000000000000000000000000000000000000"
        ok = self.fabric.verify_proof(proof)
        self.assertFalse(ok)
        self.assertEqual(self.fabric._proofs_verified_fail, 1)

    def test_08_balance_transfer_circuit_proof_and_verify(self):
        # 500 - 150 = 350
        proof = self.fabric.prove_statement(
            "circuit_balance_transfer",
            witness={"w_before": 500, "w_spent": 150},
            public_inputs={"public_after": 350},
        )
        ok = self.fabric.verify_proof(proof)
        self.assertTrue(ok)

    def test_09_custom_circuit_compilation(self):
        # Quadratic formula step: (x + 2) * (x + 3) = y
        # We model constraint: term1 * term2 = y where term1=x+2, term2=x+3
        custom_constraints = [
            R1CSConstraint(a={"x": 1, "ONE": 2}, b={"x": 1, "ONE": 3}, c={"y": 1})
        ]
        count = self.fabric.compile_circuit("circuit_custom_quad", custom_constraints)
        self.assertEqual(count, 1)

        # For x = 1: (1+2)*(1+3) = 3*4 = 12
        proof = self.fabric.prove_statement(
            "circuit_custom_quad",
            witness={"x": 1},
            public_inputs={"y": 12},
        )
        ok = self.fabric.verify_proof(proof)
        self.assertTrue(ok)

    def test_10_ascii_status_and_metadata(self):
        ascii_out = self.fabric.format_ascii_status()
        self.assertIn("STAGE 206: ZERO-KNOWLEDGE PROOF INVARIANT GENERATOR & GATE", ascii_out)
        self.assertIn("Finite Field Prime    : BN254 (254-bit Curve)", ascii_out)
        self.assertIn("Era 21 (Post-Singularity ZK Privacy)", ascii_out)


if __name__ == "__main__":
    unittest.main()
