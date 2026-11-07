"""
Unit Tests for Stage 269: Sovereign Decentralized Multi-Tier Zero-Knowledge Succinct zk-SNARK / STARK Verifier
Author & Permanent Sovereign Operator: Senin (Senin Ali K P)
"""

import unittest
import hashlib
import threading
from backend.lucy_core.zero_knowledge_zk_verifier import (
    ZeroKnowledgeZKVerifier,
    SOVEREIGN_OPERATOR,
    SOVEREIGN_LEGAL_NAME,
    STAGE_ID,
    STAGE_NAME,
    ERA_ID
)


class TestStage269ZeroKnowledgeZKVerifier(unittest.TestCase):
    """Thorough unit test suite for Stage 269."""

    def setUp(self):
        self.verifier = ZeroKnowledgeZKVerifier(curve_name="bn254")

    def test_01_initialization(self):
        """Verify initialization and prime field size."""
        self.assertEqual(self.verifier.curve_name, "bn254")
        self.assertEqual(self.verifier.field_p.bit_length(), 254)
        self.assertEqual(len(self.verifier.verified_receipts), 0)

    def test_02_r1cs_satisfied_multiplication(self):
        """Verify R1CS verification of valid multiplication constraint: 3 * 5 = 15."""
        # Witness vector w = [1, x=3, y=5, out=15]
        witness = [1, 3, 5, 15]
        # A = [0, 1, 0, 0] -> selects x
        matrix_a = [[0, 1, 0, 0]]
        # B = [0, 0, 1, 0] -> selects y
        matrix_b = [[0, 0, 1, 0]]
        # C = [0, 0, 0, 1] -> selects out
        matrix_c = [[0, 0, 0, 1]]

        res = self.verifier.verify_r1cs_constraint_system(matrix_a, matrix_b, matrix_c, witness)
        self.assertTrue(res["is_satisfied"])
        self.assertEqual(res["violations_count"], 0)

    def test_03_r1cs_violation_detection(self):
        """Verify R1CS detects invalid computation: 3 * 5 != 16."""
        witness = [1, 3, 5, 16]
        matrix_a = [[0, 1, 0, 0]]
        matrix_b = [[0, 0, 1, 0]]
        matrix_c = [[0, 0, 0, 1]]

        res = self.verifier.verify_r1cs_constraint_system(matrix_a, matrix_b, matrix_c, witness)
        self.assertFalse(res["is_satisfied"])
        self.assertEqual(res["violations_count"], 1)
        self.assertIn(0, res["violated_rows"])

    def test_04_r1cs_modular_arithmetic(self):
        """Verify R1CS calculations wrap modulo field prime p."""
        p = self.verifier.field_p
        # (p - 1) * (p - 1) == 1 (mod p)
        witness = [1, p - 1, 1]
        matrix_a = [[0, 1, 0]]
        matrix_b = [[0, 1, 0]]
        matrix_c = [[0, 0, 1]]

        res = self.verifier.verify_r1cs_constraint_system(matrix_a, matrix_b, matrix_c, witness)
        self.assertTrue(res["is_satisfied"])

    def test_05_sovereign_identity_proof_generation(self):
        """Verify sovereign ZK identity proof generation."""
        proof = self.verifier.generate_sovereign_identity_proof(
            public_challenge="CHALLENGE_BLOCK_270",
            secret_witness="SENIN_SECRET_KEY_999"
        )
        self.assertEqual(proof["proof_type"], "SOVEREIGN_ZK_IDENTITY")
        self.assertEqual(proof["sovereign_operator"], "Senin")
        self.assertEqual(len(proof["commitment_hash"]), 64)
        self.assertEqual(len(proof["fiat_shamir_challenge"]), 64)
        self.assertEqual(len(proof["proof_response"]), 64)

    def test_06_sovereign_identity_proof_verification(self):
        """Verify valid sovereign ZK proof evaluates successfully."""
        witness = "SENIN_MASTER_GENESIS_SECRET"
        salt = "LUCY_SOVEREIGN_ERA27"
        expected_comm = hashlib.sha256(f"{witness}:{salt}".encode("utf-8")).hexdigest()

        proof = self.verifier.generate_sovereign_identity_proof(
            public_challenge="EPOCH_27_DEPLOYMENT",
            secret_witness=witness,
            salt=salt
        )
        res = self.verifier.verify_sovereign_identity_proof(proof, known_valid_commitment=expected_comm)
        self.assertTrue(res["verified"])
        self.assertTrue(res["commitment_matches_sovereign"])
        self.assertTrue(res["fiat_shamir_consistent"])
        self.assertEqual(len(self.verifier.verified_receipts), 1)

    def test_07_tampered_proof_rejection(self):
        """Verify modified challenge or commitment is rejected."""
        witness = "SENIN_SECRET"
        salt = "LUCY_SOVEREIGN_ERA27"
        expected_comm = hashlib.sha256(f"{witness}:{salt}".encode("utf-8")).hexdigest()

        proof = self.verifier.generate_sovereign_identity_proof("CHALLENGE_A", witness, salt)
        # Tamper challenge
        proof["public_challenge"] = "CHALLENGE_TAMPERED"
        res = self.verifier.verify_sovereign_identity_proof(proof, expected_comm)
        self.assertFalse(res["verified"])
        self.assertFalse(res["fiat_shamir_consistent"])

    def test_08_merkle_stark_path_verification(self):
        """Verify STARK Merkle branch authentication."""
        leaf = hashlib.sha256(b"leaf_data_0").hexdigest()
        sibling = hashlib.sha256(b"sibling_data_1").hexdigest()
        # parent = H(leaf || sibling)
        parent = hashlib.sha256(f"{leaf}{sibling}".encode("utf-8")).hexdigest()

        path = [(sibling, 'R')]
        is_valid = self.verifier.verify_merkle_stark_path(leaf, path, parent)
        self.assertTrue(is_valid)

        # Wrong root
        wrong_root = hashlib.sha256(b"corrupt_root").hexdigest()
        is_invalid = self.verifier.verify_merkle_stark_path(leaf, path, wrong_root)
        self.assertFalse(is_invalid)

    def test_09_operator_binding_and_status(self):
        """Verify sovereign creator binding to Senin and legal name."""
        status = self.verifier.get_status()
        self.assertEqual(status["stage"], 269)
        self.assertEqual(status["era"], 27)
        self.assertEqual(status["sovereign_operator"], "Senin")
        self.assertEqual(status["sovereign_legal_name"], "Senin Ali K P")
        self.assertEqual(SOVEREIGN_OPERATOR, "Senin")
        self.assertEqual(SOVEREIGN_LEGAL_NAME, "Senin Ali K P")
        self.assertEqual(STAGE_ID, 269)
        self.assertEqual(ERA_ID, 27)

    def test_10_concurrency_and_thread_safety(self):
        """Verify thread-safety across concurrent workers."""
        threads = []
        errors = []

        def worker():
            try:
                v = ZeroKnowledgeZKVerifier()
                w = "THREAD_SECRET"
                s = "SALT"
                comm = hashlib.sha256(f"{w}:{s}".encode("utf-8")).hexdigest()
                p = v.generate_sovereign_identity_proof("CHALLENGE", w, s)
                res = v.verify_sovereign_identity_proof(p, comm)
                if not res["verified"]:
                    errors.append("Verification failed in thread")
            except Exception as e:
                errors.append(str(e))

        for _ in range(5):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Thread errors: {errors}")


if __name__ == "__main__":
    unittest.main()
