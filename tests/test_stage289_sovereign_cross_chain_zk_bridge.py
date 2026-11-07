"""
Unit Tests for Stage 289: Sovereign Autonomous Decentralized Cross-Chain State Relayer & ZK Merkle Bridge
Sovereign Architect: Senin (Senin Ali K P)
"""

import unittest
import threading
from backend.lucy_core.sovereign_cross_chain_zk_bridge import (
    SovereignCrossChainZKBridgeFabric,
    STAGE,
    STAGE_NAME,
    SOVEREIGN_OPERATOR,
    sha256_hex,
)


class TestStage289SovereignCrossChainZKBridge(unittest.TestCase):

    def setUp(self):
        self.fabric = SovereignCrossChainZKBridgeFabric()

    def test_01_initialization_and_metadata(self):
        st = self.fabric.status()
        self.assertEqual(st["stage"], 289)
        self.assertEqual(st["stage_name"], STAGE_NAME)
        self.assertEqual(st["sovereign_operator"], SOVEREIGN_OPERATOR)
        self.assertEqual(st["chains_count"], 2)
        self.assertEqual(st["spent_nullifiers_count"], 0)
        self.assertEqual(st["settled_receipts_count"], 0)

    def test_02_default_chains_presence(self):
        self.assertIn("LUCY-CORE-01", self.fabric._chains)
        self.assertIn("LUCY-ROLLUP-02", self.fabric._chains)
        self.assertEqual(self.fabric._chains["LUCY-CORE-01"]["current_height"], 0)

    def test_03_custom_chain_registration(self):
        root = sha256_hex("GENESIS-SIDECHAIN-03")
        res = self.fabric.register_chain("SIDECHAIN-03", "Test Sidechain", root)
        self.assertEqual(res["chain_id"], "SIDECHAIN-03")
        self.assertEqual(res["status"], "REGISTERED")
        self.assertEqual(self.fabric.status()["chains_count"], 3)

    def test_04_sequential_header_relay(self):
        # Relay block height 1 on LUCY-CORE-01
        genesis_hash = self.fabric._headers["LUCY-CORE-01"][0].block_hash
        new_state_root = sha256_hex("STATE-ROOT-BLOCK-1")
        res = self.fabric.relay_header(
            chain_id="LUCY-CORE-01",
            height=1,
            prev_hash=genesis_hash,
            state_root=new_state_root,
        )
        self.assertEqual(res["status"], "HEADER_ACCEPTED_AND_RELAYED")
        self.assertEqual(res["height"], 1)
        self.assertEqual(self.fabric._chains["LUCY-CORE-01"]["current_height"], 1)

    def test_05_header_relay_height_gap_failure(self):
        # Height skipping must fail
        genesis_hash = self.fabric._headers["LUCY-CORE-01"][0].block_hash
        res = self.fabric.relay_header(
            chain_id="LUCY-CORE-01",
            height=5, # Skipped 1..4
            prev_hash=genesis_hash,
            state_root=sha256_hex("ROOT"),
        )
        self.assertFalse(res["success"])
        self.assertIn("Invalid height", res["error"])

    def test_06_header_relay_invalid_prev_hash(self):
        # Mismatched parent hash must fail
        res = self.fabric.relay_header(
            chain_id="LUCY-CORE-01",
            height=1,
            prev_hash="f" * 64, # Wrong hash
            state_root=sha256_hex("ROOT"),
        )
        self.assertFalse(res["success"])
        self.assertIn("Invalid prev_hash", res["error"])

    def test_07_cross_chain_transfer_settlement(self):
        res = self.fabric.verify_and_settle_transfer(
            source_chain="LUCY-CORE-01",
            target_chain="LUCY-ROLLUP-02",
            receipt_id="RCP-001",
            payload={"amount": 100, "token": "LUCY"},
            merkle_proof=[sha256_hex("sibling1"), sha256_hex("sibling2")],
            nullifier=sha256_hex("NULLIFIER-RCP-001"),
        )
        self.assertTrue(res["settled"])
        self.assertEqual(res["status"], "CROSS_CHAIN_STATE_SETTLED")
        self.assertEqual(self.fabric.status()["settled_receipts_count"], 1)
        self.assertEqual(self.fabric.status()["spent_nullifiers_count"], 1)

    def test_08_double_spend_nullifier_rejection(self):
        null = sha256_hex("NULLIFIER-REPLAY-ATTACK")
        # First settlement succeeds
        r1 = self.fabric.verify_and_settle_transfer(
            source_chain="LUCY-CORE-01",
            target_chain="LUCY-ROLLUP-02",
            receipt_id="RCP-TX-1",
            payload={"amount": 50},
            merkle_proof=[],
            nullifier=null,
        )
        self.assertTrue(r1["settled"])

        # Second settlement with identical nullifier MUST fail
        r2 = self.fabric.verify_and_settle_transfer(
            source_chain="LUCY-CORE-01",
            target_chain="LUCY-ROLLUP-02",
            receipt_id="RCP-TX-2",
            payload={"amount": 50},
            merkle_proof=[],
            nullifier=null,
        )
        self.assertFalse(r2["success"])
        self.assertIn("already spent", r2["error"])

    def test_09_multithreaded_concurrency(self):
        def worker(idx):
            null = sha256_hex(f"THREAD-NULL-{idx}")
            self.fabric.verify_and_settle_transfer(
                source_chain="LUCY-CORE-01",
                target_chain="LUCY-ROLLUP-02",
                receipt_id=f"RCP-THREAD-{idx}",
                payload={"thread_idx": idx},
                merkle_proof=[],
                nullifier=null,
            )

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        st = self.fabric.status()
        self.assertEqual(st["settled_receipts_count"], 10)
        self.assertEqual(st["spent_nullifiers_count"], 10)

    def test_10_ascii_formatting_and_cp1252_encoding(self):
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 289", tbl)
        self.assertIn("Senin (Senin Ali K P)", tbl)
        self.assertIn("Registered Chains", tbl)
        encoded = tbl.encode("cp1252")
        self.assertIsInstance(encoded, bytes)


if __name__ == "__main__":
    unittest.main()
