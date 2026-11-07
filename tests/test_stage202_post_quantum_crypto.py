r"""
tests/test_stage202_post_quantum_crypto.py
Stage 202: Quantum-Resistant Lattice Cryptography & Post-Quantum Enclave
Era 21: Autonomous Hyper-Scale Multi-Kernel Federation, Quantum-Resistant Keys & Post-Singularity Architecture
"""

import unittest
from backend.lucy_core.post_quantum_crypto import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    LatticeKeyPair,
    EncapsulationResult,
    QuantumSignature,
    PostQuantumCryptoFabric,
)


class TestStage202PostQuantumCrypto(unittest.TestCase):
    """10 Unit Tests for Stage 202 Post-Quantum Lattice Cryptography Fabric."""

    def setUp(self):
        self.fabric = PostQuantumCryptoFabric(key_id="test_pqc_key")

    def test_01_fabric_initialization(self):
        self.assertEqual(self.fabric.key_id, "test_pqc_key")
        self.assertIsNotNone(self.fabric.kem_keys)
        self.assertIsNotNone(self.fabric.dsa_keys)
        self.assertEqual(self.fabric.kem_keys.algorithm, "ML-KEM-768")
        self.assertEqual(self.fabric.dsa_keys.algorithm, "ML-DSA-65")
        self.assertEqual(self.fabric.status()["stage"], 202)
        self.assertEqual(self.fabric.status()["era"], 21)

    def test_02_keypair_generation(self):
        kem, dsa = self.fabric.generate_keypairs()
        self.assertEqual(len(kem.public_key), 32)
        self.assertEqual(len(kem.secret_key), 64)
        self.assertEqual(len(dsa.public_key), 32)
        self.assertEqual(len(dsa.secret_key), 64)

    def test_03_ml_kem_encapsulate_and_decapsulate(self):
        pk = self.fabric.kem_keys.public_key
        encap = self.fabric.encapsulate(pk)
        self.assertEqual(len(encap.shared_secret), 32)
        self.assertEqual(len(encap.ciphertext), 32)

        recovered_secret = self.fabric.decapsulate(encap.ciphertext)
        self.assertEqual(recovered_secret, encap.shared_secret)

    def test_04_ml_kem_ciphertext_tampering_fails(self):
        pk = self.fabric.kem_keys.public_key
        encap = self.fabric.encapsulate(pk)

        # Corrupt ciphertext byte
        tampered_ct = bytearray(encap.ciphertext)
        tampered_ct[0] ^= 0xFF
        corrupted_secret = self.fabric.decapsulate(bytes(tampered_ct))
        self.assertNotEqual(corrupted_secret, encap.shared_secret)

    def test_05_ml_dsa_sign_and_verify_success(self):
        msg = b"Sovereign AGI Quantum Invariant Message"
        sig = self.fabric.sign_quantum(msg)
        self.assertEqual(len(sig.signature_bytes), 64)
        self.assertEqual(len(sig.message_digest), 64)

        ok = self.fabric.verify_quantum(msg, sig)
        self.assertTrue(ok)

    def test_06_ml_dsa_signature_tamper_rejection(self):
        msg = b"Authentic Message from Senin"
        sig = self.fabric.sign_quantum(msg)

        # 1. Tamper message
        self.assertFalse(self.fabric.verify_quantum(b"Tampered Message", sig))

        # 2. Tamper signature bytes
        tampered_sig = QuantumSignature(
            message_digest=sig.message_digest,
            signature_bytes=b"X" * 64,
        )
        self.assertFalse(self.fabric.verify_quantum(msg, tampered_sig))

    def test_07_hybrid_envelope_encrypt_decrypt(self):
        plaintext = b"High-Value Sovereign Cryptographic Payload - Stage 202"
        pk = self.fabric.kem_keys.public_key

        ct_body, kem_ct = self.fabric.hybrid_encrypt(plaintext, pk)
        self.assertEqual(len(ct_body), len(plaintext))
        self.assertNotEqual(ct_body, plaintext)

        decrypted = self.fabric.hybrid_decrypt(ct_body, kem_ct)
        self.assertEqual(decrypted, plaintext)

    def test_08_hybrid_corrupted_ciphertext_recovery(self):
        plaintext = b"Confidential Kernel Directive"
        pk = self.fabric.kem_keys.public_key
        ct_body, kem_ct = self.fabric.hybrid_encrypt(plaintext, pk)

        # Tamper kem_ct
        tampered_kem = bytearray(kem_ct)
        tampered_kem[0] ^= 0x01
        garbage = self.fabric.hybrid_decrypt(ct_body, bytes(tampered_kem))
        self.assertNotEqual(garbage, plaintext)

    def test_09_operation_counters(self):
        pk = self.fabric.kem_keys.public_key
        encap = self.fabric.encapsulate(pk)
        self.fabric.decapsulate(encap.ciphertext)

        sig = self.fabric.sign_quantum(b"msg")
        self.fabric.verify_quantum(b"msg", sig)

        s = self.fabric.status()
        self.assertEqual(s["encapsulations"], 1)
        self.assertEqual(s["decapsulations"], 1)
        self.assertEqual(s["signatures_issued"], 1)
        self.assertEqual(s["signatures_verified"], 1)

    def test_10_ascii_status_and_metadata(self):
        ascii_out = self.fabric.format_ascii_status()
        self.assertIn("STAGE 202: QUANTUM-RESISTANT LATTICE CRYPTO ENCLAVE", ascii_out)
        self.assertIn("ML-KEM Algorithm      : ML-KEM-768", ascii_out)
        self.assertIn("ML-DSA Algorithm      : ML-DSA-65", ascii_out)


if __name__ == "__main__":
    unittest.main()
