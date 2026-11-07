"""
tests/test_stage105_peer_mesh_sync.py
Stage 105: Sovereign P2P Peer Mesh & Local Sync Unit Tests
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.peer_mesh_sync import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    STAGE,
    MeshNodeInfo,
    MeshSyncReport,
    PeerStatus,
    SovereignPeerMeshSync,
    SyncDeltaPacket,
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

    def get_recent_receipts(self, limit=10):
        return self.receipts[-limit:]


class TestStage105PeerMeshSync(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="lucy_stage105_test_")
        self.temp_path = Path(self.temp_dir)
        self.project_root = Path(__file__).resolve().parent.parent

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_constants_and_metadata(self):
        self.assertEqual(STAGE, 105)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")

    def test_02_node_credentials_initialization(self):
        mesh = SovereignPeerMeshSync(
            project_root=self.project_root,
            data_dir=self.temp_path / "mesh",
            device_name="Test-Workstation",
        )
        self.assertTrue(mesh.node_id.startswith("node_"))
        self.assertEqual(len(mesh.public_key), 64)
        self.assertEqual(mesh.vector_clock, 1)
        self.assertTrue((self.temp_path / "mesh" / "node_credentials.json").exists())

    def test_03_peer_discovery(self):
        mesh = SovereignPeerMeshSync(
            project_root=self.project_root,
            data_dir=self.temp_path / "mesh",
        )
        discovered = mesh.discover_peers(scan_simulated=True)
        self.assertGreater(len(discovered), 0)
        first = discovered[0]
        self.assertIsInstance(first, MeshNodeInfo)
        self.assertEqual(first.creator, "Senin")
        self.assertEqual(first.status, PeerStatus.DISCOVERED)

    def test_04_mutual_cryptographic_handshake(self):
        mesh = SovereignPeerMeshSync(
            project_root=self.project_root,
            data_dir=self.temp_path / "mesh",
        )
        discovered = mesh.discover_peers()
        peer_id = discovered[0].node_id

        res = mesh.authenticate_peer(peer_id)
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "AUTHENTICATED")
        self.assertEqual(mesh.peers[peer_id].status, PeerStatus.AUTHENTICATED)
        self.assertGreater(mesh.vector_clock, 1)

    def test_05_imposter_rejection_and_quarantine(self):
        mesh = SovereignPeerMeshSync(
            project_root=self.project_root,
            data_dir=self.temp_path / "mesh",
        )
        # Register a malicious imposter node
        bad_node = MeshNodeInfo(
            node_id="node_imposter99",
            device_name="Rogue-Cloud-Relay",
            device_type="server",
            creator="UnknownAttacker",
            public_key="0000000000000000000000000000000000000000000000000000000000000000",
            ip_address="10.0.0.99",
            port=42024,
            status=PeerStatus.DISCOVERED,
        )
        mesh.peers["node_imposter99"] = bad_node

        res = mesh.authenticate_peer("node_imposter99")
        self.assertFalse(res["success"])
        self.assertEqual(res["status"], "QUARANTINED")
        self.assertIn("Security boundary violation", res["error"])
        self.assertEqual(mesh.peers["node_imposter99"].status, PeerStatus.QUARANTINED)

    def test_06_delta_sync_and_vector_clock(self):
        ledger = MockReceiptLedger()
        ledger.issue_receipt("TEST_ACTION", "execute", "unit_test", "OK")

        mesh = SovereignPeerMeshSync(
            project_root=self.project_root,
            receipt_ledger=ledger,
            data_dir=self.temp_path / "mesh",
        )
        discovered = mesh.discover_peers()
        peer_id = discovered[0].node_id

        sync_res = mesh.sync_peer_deltas(peer_id)
        self.assertTrue(sync_res["success"])
        self.assertEqual(sync_res["status"], "SYNCED")
        self.assertGreaterEqual(sync_res["items_synced"], 1)
        self.assertEqual(mesh.peers[peer_id].status, PeerStatus.SYNCED)

    def test_07_sync_all_report(self):
        mesh = SovereignPeerMeshSync(
            project_root=self.project_root,
            data_dir=self.temp_path / "mesh",
        )
        report = mesh.sync_all()
        self.assertIsInstance(report, MeshSyncReport)
        self.assertEqual(report.local_node_id, mesh.node_id)
        self.assertGreater(report.peers_count, 0)
        self.assertGreaterEqual(report.authenticated_count, 1)

    def test_08_manual_peer_quarantine(self):
        mesh = SovereignPeerMeshSync(
            project_root=self.project_root,
            data_dir=self.temp_path / "mesh",
        )
        discovered = mesh.discover_peers()
        target_id = discovered[0].node_id

        res = mesh.quarantine_peer(target_id, reason="Suspicious port scan")
        self.assertTrue(res)
        self.assertEqual(mesh.peers[target_id].status, PeerStatus.QUARANTINED)
        self.assertEqual(mesh.peers[target_id].metadata["quarantine_reason"], "Suspicious port scan")

    def test_09_export_node_credentials(self):
        mesh = SovereignPeerMeshSync(
            project_root=self.project_root,
            data_dir=self.temp_path / "mesh",
        )
        creds = mesh.export_node_credentials()
        self.assertEqual(creds["node_id"], mesh.node_id)
        self.assertEqual(creds["creator"], "Senin")
        self.assertEqual(creds["creator_full_name"], "Senin Ali K P")
        self.assertTrue(creds["sovereign_local"])

    def test_10_receipt_ledger_integration(self):
        ledger = MockReceiptLedger()
        mesh = SovereignPeerMeshSync(
            project_root=self.project_root,
            receipt_ledger=ledger,
            data_dir=self.temp_path / "mesh",
        )
        discovered = mesh.discover_peers()
        peer_id = discovered[0].node_id
        mesh.authenticate_peer(peer_id)
        mesh.sync_peer_deltas(peer_id)
        mesh.quarantine_peer(peer_id)

        categories = [r["category"] for r in ledger.receipts]
        self.assertIn("MESH_PEER_DISCOVERY", categories)
        self.assertIn("MESH_HANDSHAKE", categories)
        self.assertIn("MESH_DELTA_SYNC", categories)
        self.assertIn("MESH_PEER_QUARANTINE", categories)

    def test_11_cp1252_mesh_status_table(self):
        mesh = SovereignPeerMeshSync(
            project_root=self.project_root,
            data_dir=self.temp_path / "mesh",
        )
        status_table = mesh.mesh_status()
        self.assertIn("LUCY OS - SOVEREIGN P2P PEER MESH", status_table)
        self.assertIn("STAGE 105: ZERO-CLOUD LOCAL SYNC FABRIC", status_table)
        status_table.encode("cp1252")

        st = mesh.status()
        self.assertEqual(st["stage"], 105)
        self.assertEqual(st["creator"], "Senin")
        self.assertGreater(st["total_peers"], 0)


if __name__ == "__main__":
    unittest.main()
