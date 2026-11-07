"""
tests/test_stage110_consensus_nexus.py
Stage 110: Sovereign Consensus Nexus & Era 11 Master Seal Unit Tests
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.consensus_nexus import (
    CANONICAL_ERA11_MODULES,
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    ERA_NAME,
    STAGE,
    Era11SealCertificate,
    LogEntry,
    NodeRole,
    SovereignConsensusNexus,
)


class MockReceiptLedger:
    def __init__(self):
        self.receipts = []

    def issue_receipt(self, action_category, operation, target, verified_outcome):
        rec = {
            "category": action_category,
            "operation": operation,
            "target": target,
            "outcome": verified_outcome,
        }
        self.receipts.append(rec)
        return rec


class TestStage110ConsensusNexus(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="lucy_stage110_test_")
        self.temp_path = Path(self.temp_dir)
        self.project_root = Path(__file__).resolve().parent.parent

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_constants_and_metadata(self):
        self.assertEqual(STAGE, 110)
        self.assertEqual(ERA, 11)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")
        self.assertIn("Sovereign", ERA_NAME)

    def test_02_canonical_era11_modules(self):
        self.assertEqual(len(CANONICAL_ERA11_MODULES), 10)
        stages = [m[0] for m in CANONICAL_ERA11_MODULES]
        self.assertEqual(stages, list(range(101, 111)))

    def test_03_propose_and_commit(self):
        nexus = SovereignConsensusNexus(
            project_root=self.project_root,
            data_dir=self.temp_path / "consensus",
        )
        res = nexus.propose("sync_workspace_state")
        self.assertEqual(res["status"], "COMMITTED")
        self.assertEqual(res["index"], 1)
        self.assertEqual(res["term"], 1)
        self.assertTrue(len(res["entry_hash"]) == 64)

        st = nexus.status()
        self.assertEqual(st["commit_index"], 1)
        self.assertEqual(st["total_entries"], 1)

    def test_04_conflict_arbitration_operator_priority(self):
        nexus = SovereignConsensusNexus(
            project_root=self.project_root,
            data_dir=self.temp_path / "consensus",
        )
        proposals = [
            {"node_id": "sub_agent_alpha", "payload": "execute_unverified_task"},
            {"node_id": "senin_operator_node", "payload": "Senin Ali K P confirmed priority override"},
        ]
        arb = nexus.arbitrate_conflict(proposals)
        self.assertEqual(arb.winner_node, "senin_operator_node")
        self.assertIn("Senin Priority Override", arb.arbitration_reason)

    def test_05_conflict_arbitration_fallback(self):
        nexus = SovereignConsensusNexus(
            project_root=self.project_root,
            data_dir=self.temp_path / "consensus",
        )
        proposals = [
            {"node_id": "worker_1", "payload": "clean_tmp_cache"},
            {"node_id": "worker_2", "payload": "rebuild_vector_index"},
        ]
        arb = nexus.arbitrate_conflict(proposals)
        self.assertEqual(arb.winner_node, "worker_1")

    def test_06_verify_era11_integrity(self):
        nexus = SovereignConsensusNexus(
            project_root=self.project_root,
            data_dir=self.temp_path / "consensus",
        )
        integ = nexus.verify_era11_integrity()
        self.assertEqual(integ["total_modules"], 10)
        self.assertEqual(integ["verified_modules"], 10)
        self.assertTrue(integ["all_verified"])
        self.assertEqual(len(integ["merkle_root"]), 64)

    def test_07_seal_era11_certificate(self):
        nexus = SovereignConsensusNexus(
            project_root=self.project_root,
            data_dir=self.temp_path / "consensus",
        )
        cert = nexus.seal_era11()
        self.assertTrue(cert.seal_id.startswith("SEAL-ERA11-"))
        self.assertEqual(cert.era, 11)
        self.assertEqual(cert.stage_range, "101-110")
        self.assertEqual(cert.total_stages_sealed, 10)
        self.assertEqual(cert.operator, "Senin")
        self.assertEqual(cert.operator_full_name, "Senin Ali K P")
        self.assertEqual(cert.verification_status, "AUTHENTIC_SOVEREIGN_CORE_SEALED")
        self.assertTrue(nexus.status()["is_sealed"])

    def test_08_receipt_ledger_emission(self):
        ledger = MockReceiptLedger()
        nexus = SovereignConsensusNexus(
            project_root=self.project_root,
            data_dir=self.temp_path / "consensus",
            receipt_ledger=ledger,
        )
        nexus.propose("test_action")
        self.assertEqual(len(ledger.receipts), 1)
        self.assertEqual(ledger.receipts[0]["category"], "CONSENSUS_COMMIT_RECEIPT")

        nexus.seal_era11()
        self.assertEqual(len(ledger.receipts), 2)
        self.assertEqual(ledger.receipts[1]["category"], "ERA11_SOVEREIGN_NEXUS_SEAL")

    def test_09_ascii_formatting(self):
        nexus = SovereignConsensusNexus(
            project_root=self.project_root,
            data_dir=self.temp_path / "consensus",
        )
        nexus.propose("sample_commit")
        status_tbl = nexus.format_nexus_status_table()
        self.assertIn("+--------------------------------------------------------------------------------+", status_tbl)
        self.assertIn("LUCY OS - SOVEREIGN CONSENSUS NEXUS CLUSTER STATE", status_tbl)
        self.assertIn("Senin Ali K P", status_tbl)

        cert = nexus.seal_era11()
        summary = cert.format_terminal_summary()
        self.assertIn("+================================================================================+", summary)
        self.assertIn("ERA 11 SOVEREIGN NEXUS MASTER SEAL CERTIFICATE", summary)
        self.assertIn("Senin Ali K P", summary)

    def test_10_status_dictionary(self):
        nexus = SovereignConsensusNexus(
            project_root=self.project_root,
            data_dir=self.temp_path / "consensus",
        )
        st = nexus.status()
        self.assertEqual(st["stage"], 110)
        self.assertEqual(st["era"], 11)
        self.assertEqual(st["creator"], "Senin")
        self.assertEqual(st["creator_full_name"], "Senin Ali K P")
        self.assertEqual(st["node_role"], "LEADER")


if __name__ == "__main__":
    unittest.main()
