"""
Unit Tests for Stage 299: Sovereign Post-Quantum Lattice Cryptography & Ring-LWE Fabric
Sovereign Architect: Senin (Senin Ali K P)
"""

import math
import threading
import unittest
from backend.lucy_core.sovereign_post_quantum_lattice_cryptography import (
    SovereignPostQuantumLatticeCryptographyFabric,
    STAGE,
    STAGE_NAME,
    SOVEREIGN_OPERATOR,
)


class TestStage299SovereignPostQuantumLatticeCryptography(unittest.TestCase):

    def setUp(self):
        # Use n=16 for fast unit tests while maintaining full power-of-2 negacyclic ring
        self.fabric = SovereignPostQuantumLatticeCryptographyFabric(degree_n=16, modulus_q=3329, eta=2)

    def test_01_initialization_and_metadata(self):
        st = self.fabric.status()
        self.assertEqual(st["stage"], 299)
        self.assertEqual(st["stage_name"], STAGE_NAME)
        self.assertEqual(st["sovereign_operator"], SOVEREIGN_OPERATOR)
        self.assertEqual(st["polynomial_degree_n"], 16)
        self.assertEqual(st["prime_modulus_q"], 3329)
        self.assertEqual(st["binomial_parameter_eta"], 2)
        self.assertEqual(st["status"], "OPERATIONAL")

    def test_02_polynomial_negacyclic_convolution_algebra(self):
        # Multiply (X) * (X^{n-1}) = X^n = -1 = q - 1 mod q
        p1 = [0] * 16
        p1[1] = 1 # X
        p2 = [0] * 16
        p2[15] = 1 # X^15
        prod = self.fabric.poly_mul_negacyclic(p1, p2)
        # Degree 16 wraps to constant term with -1 mod 3329 = 3328
        self.assertEqual(prod[0], 3328)
        self.assertTrue(all(c == 0 for c in prod[1:]))

    def test_03_poly_add_and_sub(self):
        p1 = [10] * 16
        p2 = [5] * 16
        added = self.fabric.poly_add(p1, p2)
        subbed = self.fabric.poly_sub(p1, p2)
        self.assertEqual(added[0], 15)
        self.assertEqual(subbed[0], 5)

    def test_04_keypair_generation_deterministic(self):
        kp1 = self.fabric.generate_keypair("TestSeed_123")
        kp2 = self.fabric.generate_keypair("TestSeed_123")
        self.assertEqual(kp1.fingerprint_sha256, kp2.fingerprint_sha256)
        self.assertEqual(kp1.public_key_a, kp2.public_key_a)
        self.assertEqual(kp1.public_key_b, kp2.public_key_b)
        self.assertEqual(len(kp1.public_key_a), 16)

    def test_05_small_error_sampling_bounds(self):
        kp = self.fabric.generate_keypair("SeedBounds")
        # Check coefficients of secret s are within [-eta, eta] mod q
        eta = self.fabric.eta
        q = self.fabric.q
        for coeff in kp.secret_key_s:
            # Either coeff <= eta or coeff >= q - eta
            self.assertTrue(coeff <= eta or coeff >= q - eta)

    def test_06_ring_lwe_encryption_and_decryption(self):
        kp = self.fabric.generate_keypair("Alice_Keys")
        msg = [1, 0, 1, 1, 0, 0, 1, 0]
        ctxt = self.fabric.encrypt_bit_message(kp, msg, seed="Bob_Ephemeral")
        decrypted = self.fabric.decrypt_bit_message(kp, ctxt)
        self.assertEqual(decrypted, msg)

    def test_07_full_zeros_and_ones_transmission(self):
        kp = self.fabric.generate_keypair("Transmission_Keys")
        all_ones = [1] * 16
        ctxt_ones = self.fabric.encrypt_bit_message(kp, all_ones, seed="Ephemeral_1")
        dec_ones = self.fabric.decrypt_bit_message(kp, ctxt_ones)
        self.assertEqual(dec_ones, all_ones)

        all_zeros = [0] * 16
        ctxt_zeros = self.fabric.encrypt_bit_message(kp, all_zeros, seed="Ephemeral_2")
        dec_zeros = self.fabric.decrypt_bit_message(kp, ctxt_zeros)
        self.assertEqual(dec_zeros, all_zeros)

    def test_08_invalid_degree_raises(self):
        # Degree must be power of 2
        with self.assertRaises(ValueError):
            SovereignPostQuantumLatticeCryptographyFabric(degree_n=15)
        with self.assertRaises(ValueError):
            SovereignPostQuantumLatticeCryptographyFabric(degree_n=4)

    def test_09_multithreaded_concurrency(self):
        results = []

        def worker():
            kp = self.fabric.generate_keypair("ConcurrentSeed")
            results.append(kp.fingerprint_sha256)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), 10)
        self.assertEqual(len(set(results)), 1) # All identical for same seed

    def test_10_invalid_modulus_raises(self):
        with self.assertRaises(ValueError):
            SovereignPostQuantumLatticeCryptographyFabric(modulus_q=5)


if __name__ == "__main__":
    unittest.main()
