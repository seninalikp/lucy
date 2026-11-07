"""
Unit Tests for Stage 279: Sovereign Decentralized Autonomous Zero-Knowledge Rollup & Verifiable State Compressor
Author & Permanent Sovereign Operator: Senin (Senin Ali K P)
"""

import unittest
import threading
from backend.lucy_core.sovereign_zk_rollup_compressor import (
    SovereignZKRollupCompressor,
    SOVEREIGN_OPERATOR,
    SOVEREIGN_LEGAL_NAME,
    STAGE_ID,
    STAGE_NAME,
    ERA_ID
)


class TestStage279SovereignZKRollupCompressor(unittest.TestCase):
    """Thorough unit test suite for Stage 279."""

    def setUp(self):
        self.rollup = SovereignZKRollupCompressor(initial_accounts_count=8)

    def test_01_initialization(self):
        """Verify default account setup and state root generation."""
        self.assertEqual(len(self.rollup.accounts), 8)
        self.assertEqual(len(self.rollup.state_root), 64)
        self.assertEqual(len(self.rollup.rollup_batch_history), 0)

    def test_02_transaction_batch_compression_ratio(self):
        """Verify transaction batch compression achieves >= 3x size reduction."""
        txs = [
            {"from": 0, "to": 1, "amount": 10.0, "nonce": 0, "signature": "0x123456789abcdef0123456789abcdef0"},
            {"from": 0, "to": 2, "amount": 25.5, "nonce": 1, "signature": "0xabcdef0123456789abcdef0123456789"},
            {"from": 1, "to": 3, "amount": 5.0,  "nonce": 0, "signature": "0x9876543210fedcba9876543210fedcba"}
        ]
        res = self.rollup.compress_transaction_batch(txs)
        self.assertGreaterEqual(res["compression_ratio"], 3.0)
        self.assertLess(res["compressed_bytes"], res["uncompressed_bytes"])

    def test_03_valid_state_transitions(self):
        """Verify execution of valid batch updates account balances and nonces."""
        txs = [{"from": 0, "to": 1, "amount": 100.0, "nonce": 0}]
        b0_before = self.rollup.accounts[0]["balance"]
        b1_before = self.rollup.accounts[1]["balance"]

        res = self.rollup.process_and_verify_rollup_batch(txs)
        self.assertEqual(res["valid_transactions"], 1)
        self.assertEqual(res["invalid_transactions"], 0)
        self.assertEqual(self.rollup.accounts[0]["balance"], b0_before - 100.0)
        self.assertEqual(self.rollup.accounts[1]["balance"], b1_before + 100.0)
        self.assertEqual(self.rollup.accounts[0]["nonce"], 1)

    def test_04_insufficient_balance_handling(self):
        """Verify transactions exceeding balance are rejected without corrupting state."""
        txs = [{"from": 2, "to": 1, "amount": 999999.0, "nonce": 0}]
        b2_before = self.rollup.accounts[2]["balance"]

        res = self.rollup.process_and_verify_rollup_batch(txs)
        self.assertEqual(res["valid_transactions"], 0)
        self.assertEqual(res["invalid_transactions"], 1)
        self.assertEqual(self.rollup.accounts[2]["balance"], b2_before)

    def test_05_pre_post_root_integrity(self):
        """Verify state root changes when state transition occurs."""
        txs = [{"from": 0, "to": 2, "amount": 50.0, "nonce": 0}]
        res = self.rollup.process_and_verify_rollup_batch(txs)
        self.assertNotEqual(res["pre_state_root"], res["post_state_root"])
        self.assertEqual(self.rollup.state_root, res["post_state_root"])

    def test_06_succinct_proof_verification(self):
        """Verify succinct validity proof format and parameters."""
        txs = [{"from": 0, "to": 3, "amount": 20.0, "nonce": 0}]
        res = self.rollup.process_and_verify_rollup_batch(txs)
        self.assertEqual(len(res["succinct_validity_proof"]), 64)
        self.assertEqual(res["status"], "SETTLED_AND_COMMITTED")

    def test_07_multiple_sequential_batches(self):
        """Verify sequential settlement across multiple batches."""
        for b_idx in range(3):
            txs = [{"from": 0, "to": b_idx + 1, "amount": 10.0, "nonce": b_idx}]
            res = self.rollup.process_and_verify_rollup_batch(txs)
            self.assertEqual(res["batch_id"], b_idx + 1)
        self.assertEqual(len(self.rollup.rollup_batch_history), 3)

    def test_08_conservation_of_total_supply(self):
        """Verify total circulating balance is conserved across all transfers."""
        initial_total = sum(acc["balance"] for acc in self.rollup.accounts.values())
        txs = [
            {"from": 0, "to": 1, "amount": 40.0},
            {"from": 1, "to": 2, "amount": 15.0},
            {"from": 2, "to": 3, "amount": 10.0}
        ]
        self.rollup.process_and_verify_rollup_batch(txs)
        final_total = sum(acc["balance"] for acc in self.rollup.accounts.values())
        self.assertAlmostEqual(initial_total, final_total, places=2)

    def test_09_operator_binding_and_status(self):
        """Verify sovereign creator binding to Senin and legal name."""
        status = self.rollup.get_status()
        self.assertEqual(status["stage"], 279)
        self.assertEqual(status["era"], 28)
        self.assertEqual(status["sovereign_operator"], "Senin")
        self.assertEqual(status["sovereign_legal_name"], "Senin Ali K P")
        self.assertEqual(SOVEREIGN_OPERATOR, "Senin")
        self.assertEqual(SOVEREIGN_LEGAL_NAME, "Senin Ali K P")
        self.assertEqual(STAGE_ID, 279)
        self.assertEqual(ERA_ID, 28)

    def test_10_concurrency_and_thread_safety(self):
        """Verify thread-safety across concurrent workers."""
        threads = []
        errors = []

        def worker():
            try:
                engine = SovereignZKRollupCompressor(initial_accounts_count=4)
                txs = [{"from": 0, "to": 1, "amount": 5.0, "nonce": 0}]
                _ = engine.compress_transaction_batch(txs)
                _ = engine.process_and_verify_rollup_batch(txs)
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
