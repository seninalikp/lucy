"""
test_server_api.py
Automated verification tests for backend/server.py REST endpoints including Stages 54-59.
"""

from __future__ import annotations

import unittest
from backend.server import app


class TestServerAPI(unittest.TestCase):
    def setUp(self) -> None:
        self.client = app.test_client()
        self.client.testing = True

    def test_spine_endpoints(self) -> None:
        res = self.client.get("/api/spine")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("lucy", data)

    def test_executive_brief_endpoint(self) -> None:
        res = self.client.get("/api/executive-brief")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("brief_text", data)
        self.assertIn("stage", data)

    def test_workspace_pulse_endpoint(self) -> None:
        res = self.client.get("/api/workspace-pulse")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("recent_files", data)
        self.assertIn("git", data)

    def test_memory_graph_endpoint(self) -> None:
        res = self.client.get("/api/memory-graph")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("active_nodes", data)
        self.assertIn("memory_graph", data)

    def test_execution_receipts_endpoint(self) -> None:
        res = self.client.get("/api/execution-receipts")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("total_historical_receipts", data)
        self.assertIn("execution_receipt_ledger", data)

    def test_lora_status_endpoint(self) -> None:
        res = self.client.get("/api/lora/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("stage", data)

    def test_training_queue_endpoint(self) -> None:
        res = self.client.get("/api/training-queue")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("verified_samples_count", data)
        self.assertIn("training_queue", data)

    def test_natural_actions_endpoint(self) -> None:
        res = self.client.get("/api/natural-actions")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("capabilities", data)

    def test_chat_endpoint(self) -> None:
        res = self.client.post("/api/chat", json={"message": "status"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("reply", data)


if __name__ == "__main__":
    unittest.main()
