"""
Unit Tests for Stage 249: Universal Multi-Tier Zero-Trust Hardware Attestation & Enclave Secure Boot Orchestrator
Era 25: Omni-Dimensional Super-Intelligence Matrix, Astro-Cognitive Planetary Orchestration & Sovereign Trans-Singularity Metamaterials

Sovereign Human Operator: Senin (Senin Ali K P)
"""

import unittest
from backend.lucy_core.zero_trust_hardware_enclave import (
    ZeroTrustHardwareEnclaveFabric,
    get_hardware_enclave,
    ZERO_PCR_HASH,
    STAGE,
    ERA,
)


class TestStage249ZeroTrustHardwareEnclave(unittest.TestCase):

    def setUp(self):
        self.enclave = ZeroTrustHardwareEnclaveFabric(num_pcrs=8)

    def test_01_singleton_and_initialization(self):
        singleton = get_hardware_enclave()
        self.assertIsNotNone(singleton)
        self.assertEqual(STAGE, 249)
        self.assertEqual(ERA, 25)
        self.assertEqual(self.enclave.num_pcrs, 8)
        self.assertEqual(len(self.enclave.pcrs), 8)
        for pcr in self.enclave.pcrs:
            self.assertEqual(pcr, ZERO_PCR_HASH)

    def test_02_pcr_extend_and_boot_log(self):
        meas = b"LUCY_STAGE249_MICROKERNEL_IMAGE"
        new_hash = self.enclave.extend_pcr(0, "microkernel", meas)
        self.assertNotEqual(new_hash, ZERO_PCR_HASH)
        self.assertEqual(self.enclave.pcrs[0], new_hash)
        self.assertEqual(len(self.enclave.boot_log), 1)

        entry = self.enclave.boot_log[0]
        self.assertEqual(entry.pcr_index, 0)
        self.assertEqual(entry.stage_component, "microkernel")
        self.assertEqual(entry.resulting_pcr_hex, new_hash)

    def test_03_pcr_bounds_check(self):
        with self.assertRaises(IndexError):
            self.enclave.extend_pcr(8, "invalid_index", b"test")
        with self.assertRaises(IndexError):
            self.enclave.extend_pcr(-1, "invalid_index", b"test")

    def test_04_pcr_composite_determinism(self):
        comp1 = self.enclave.get_pcr_composite(0xFF)
        comp2 = self.enclave.get_pcr_composite(0xFF)
        self.assertEqual(comp1, comp2)
        self.assertEqual(len(comp1), 64)

        # Extending a PCR changes composite
        self.enclave.extend_pcr(1, "firmware", b"FW_V1")
        comp3 = self.enclave.get_pcr_composite(0xFF)
        self.assertNotEqual(comp1, comp3)

    def test_05_seal_and_unseal_roundtrip(self):
        secret = b"SOVEREIGN-MASTER-ENCLAVE-SECRET-TOKEN-12345"
        package = self.enclave.seal_data(secret, pcr_mask=0x03)
        self.assertIn("ciphertext_hex", package)
        self.assertIn("tag_hex", package)

        # Unseal with unchanged PCR state
        ok, decrypted, status = self.enclave.unseal_data(package)
        self.assertTrue(ok)
        self.assertEqual(decrypted, secret)
        self.assertEqual(status, "UNSEAL_SUCCESS_AUTHENTIC")

    def test_06_unseal_fails_on_pcr_tamper(self):
        secret = b"VAULT-INTEGRITY-KEY"
        package = self.enclave.seal_data(secret, pcr_mask=0x01)

        # Tamper/extend PCR 0
        self.enclave.extend_pcr(0, "unauthorized_driver", b"MALWARE_PAYLOAD")

        # Unseal should be strictly rejected
        ok, decrypted, status = self.enclave.unseal_data(package)
        self.assertFalse(ok)
        self.assertIsNone(decrypted)
        self.assertIn("PCR State Divergence", status)

    def test_07_unseal_fails_on_ciphertext_tamper(self):
        secret = b"GENESIS_SEED_DATA"
        package = self.enclave.seal_data(secret, pcr_mask=0x01)

        # Tamper ciphertext
        ct_bytes = bytearray(bytes.fromhex(package["ciphertext_hex"]))
        ct_bytes[0] ^= 0xFF
        package["ciphertext_hex"] = bytes(ct_bytes).hex()

        ok, decrypted, status = self.enclave.unseal_data(package)
        self.assertFalse(ok)
        self.assertIsNone(decrypted)
        self.assertIn("Cryptographic integrity tag mismatch", status)

    def test_08_attestation_quote_generation_and_verification(self):
        nonce = "FRESH_NONCE_987654321"
        quote = self.enclave.generate_attestation_quote(nonce)
        self.assertIsNotNone(quote.signature_hex)
        self.assertIn("QUOTE-DICE-", quote.quote_id)

        valid = self.enclave.verify_attestation_quote(quote, expected_nonce=nonce)
        self.assertTrue(valid)

    def test_09_attestation_quote_fails_on_replay_or_altered_nonce(self):
        nonce = "FRESH_NONCE_ORIGINAL"
        quote = self.enclave.generate_attestation_quote(nonce)

        # Altered nonce should fail
        valid = self.enclave.verify_attestation_quote(quote, expected_nonce="REPLAY_ATTACK_NONCE")
        self.assertFalse(valid)

    def test_10_ascii_status_and_metrics(self):
        self.enclave.extend_pcr(2, "secure_bootloader", b"BOOT_V2")
        self.enclave.generate_attestation_quote("AUDIT_NONCE")

        ascii_table = self.enclave.format_ascii_status()
        self.assertIn("STAGE 249: Universal Multi-Tier Zero-Trust Hardware Enclave", ascii_table)
        self.assertIn("PCR Composite (RoT)", ascii_table)
        self.assertIn("Measured Boot Log", ascii_table)

        # CP1252 verification
        ascii_table.encode("cp1252")

        metrics = self.enclave.get_metrics()
        self.assertEqual(metrics["stage"], 249)
        self.assertEqual(metrics["era"], 25)
        self.assertEqual(metrics["num_pcrs"], 8)
        self.assertEqual(metrics["total_attestation_quotes"], 1)


if __name__ == "__main__":
    unittest.main()
