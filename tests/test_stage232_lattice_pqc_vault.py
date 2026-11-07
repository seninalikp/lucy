r"""
tests/test_stage232_lattice_pqc_vault.py
Stage 232 Unit Tests: Quantum-Resilient Lattice Post-Quantum Cryptography Vault
"""

import threading
import unittest

from backend.lucy_core.lattice_pqc_vault import (
    LatticePQCVaultFabric,
    N_DEGREE,
    PQCKeyPair,
    Q_MODULUS,
    poly_add,
    poly_mul_mod_ring,
    poly_sub,
    sample_small_poly,
    STAGE,
    STAGE_NAME,
)


class TestStage232LatticePQCVault(unittest.TestCase):
    def setUp(self):
        self.fabric = LatticePQCVaultFabric()

    def test_01_initialization_and_metadata(self):
        s = self.fabric.status()
        self.assertEqual(s["stage"], 232)
        self.assertEqual(s["stage_name"], STAGE_NAME)
        self.assertEqual(s["polynomial_degree"], N_DEGREE)
        self.assertEqual(s["modulus"], Q_MODULUS)
        self.assertIn("sovereign_master_pqc_key", s["stored_keypairs"])

    def test_02_polynomial_ring_arithmetic(self):
        p1 = [1, 2, 0, 0] + [0] * (N_DEGREE - 4)
        p2 = [3, 4, 0, 0] + [0] * (N_DEGREE - 4)
        sum_p = poly_add(p1, p2)
        self.assertEqual(sum_p[0], 4)
        self.assertEqual(sum_p[1], 6)

        sub_p = poly_sub(p2, p1)
        self.assertEqual(sub_p[0], 2)
        self.assertEqual(sub_p[1], 2)

        # (1 + 2X) * (3 + 4X) = 3 + 10X + 8X^2
        mul_p = poly_mul_mod_ring(p1, p2)
        self.assertEqual(mul_p[0], 3)
        self.assertEqual(mul_p[1], 10)
        self.assertEqual(mul_p[2], 8)

    def test_03_centered_binomial_sampling(self):
        poly = sample_small_poly("test_seed_123", eta=2)
        self.assertEqual(len(poly), N_DEGREE)
        # All coefficients must be small in magnitude mod Q
        for c in poly:
            self.assertTrue(c <= 2 or c >= (Q_MODULUS - 2))

    def test_04_keypair_generation(self):
        kp = self.fabric.generate_keypair("satellite_uplink_key")
        self.assertEqual(kp.key_id, "satellite_uplink_key")
        self.assertEqual(len(kp.public_key_t), N_DEGREE)
        self.assertEqual(len(kp.secret_key_s), N_DEGREE)
        d = kp.to_dict()
        self.assertEqual(d["key_id"], "satellite_uplink_key")
        self.assertIn("pk_fingerprint", d)

    def test_05_encapsulation_and_decapsulation(self):
        ct, shared_enc = self.fabric.encapsulate("sovereign_master_pqc_key", seed="session_omega_99")
        self.assertEqual(len(ct.u), N_DEGREE)
        self.assertEqual(len(ct.v), N_DEGREE)
        self.assertEqual(len(shared_enc), 64)

        # Decapsulate using secret key
        shared_dec = self.fabric.decapsulate("sovereign_master_pqc_key", ct)
        self.assertEqual(shared_enc, shared_dec)

    def test_06_vault_store_and_retrieve_secret(self):
        secret_msg = "Sovereign AGI Core Operational Authorization: Senin-Omega-77"
        rec = self.fabric.store_encrypted_vault_secret(
            key_id="sovereign_master_pqc_key",
            record_id="auth_token_01",
            secret_text=secret_msg,
        )
        self.assertEqual(rec["record_id"], "auth_token_01")
        self.assertIn("auth_token_01", self.fabric.vault_records)

        # Decrypt secret from vault
        decrypted = self.fabric.retrieve_decrypted_vault_secret("auth_token_01")
        self.assertEqual(decrypted, secret_msg)

    def test_07_lattice_digital_signature(self):
        sig = self.fabric.sign_message("sovereign_master_pqc_key", "Genesis Block Directive #232")
        self.assertEqual(sig["key_id"], "sovereign_master_pqc_key")
        self.assertIn("challenge", sig)
        self.assertIsInstance(sig["z_norm"], int)

    def test_08_unknown_key_handling(self):
        with self.assertRaises(ValueError):
            self.fabric.encapsulate("non_existent_key")
        with self.assertRaises(ValueError):
            self.fabric.sign_message("non_existent_key", "test")

    def test_09_cp1252_safe_ascii_table(self):
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 232", tbl)
        self.assertIn("QUANTUM-RESILIENT LATTICE POST-QUANTUM", tbl)
        tbl.encode("cp1252")
        self.assertTrue(tbl.startswith("+--"))

    def test_10_multithreaded_concurrency(self):
        def worker(wid: int):
            for i in range(3):
                kid = f"w_key_{wid}_{i}"
                self.fabric.generate_keypair(kid)
                ct, sh = self.fabric.encapsulate(kid)
                _ = self.fabric.decapsulate(kid, ct)
            _ = self.fabric.status()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertGreaterEqual(self.fabric.total_encapsulations, 12)


if __name__ == "__main__":
    unittest.main()
