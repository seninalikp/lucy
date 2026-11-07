"""
tests/test_stage127_protocol_reverse_synthesizer.py
Verification suite for Stage 127: Protocol Reverse-Engineer & Client Synthesizer
Era 13: Self-Reflective Symbolic Mesh & Cognitive Graph Synthesizer
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.protocol_reverse_synthesizer import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    ERA_NAME,
    STAGE,
    STAGE_NAME,
    ProtocolReverseSynthesizer,
    ProtocolEndpointSpec,
    ProtocolFieldSchema,
)


class MockReceiptLedger:
    def __init__(self):
        self.receipts = []

    def record_receipt(self, action_category: str, operation: str, target: str, verified_outcome: str):
        self.receipts.append({
            "action_category": action_category,
            "operation": operation,
            "target": target,
            "verified_outcome": verified_outcome,
        })


class TestStage127ProtocolReverseSynthesizer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)
        self.data_dir = self.project_root / "data" / "lucy" / "protocols"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = MockReceiptLedger()
        self.synthesizer = ProtocolReverseSynthesizer(
            project_root=self.project_root,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_metadata(self):
        """Verifies sovereign operator identity and stage/era metadata."""
        self.assertEqual(STAGE, 127)
        self.assertEqual(ERA, 13)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")
        status = self.synthesizer.status()
        self.assertEqual(status["stage"], 127)
        self.assertEqual(status["era"], 13)
        self.assertEqual(status["creator"], "Senin")
        self.assertEqual(status["creator_full_name"], "Senin Ali K P")

    def test_02_infer_protocol_from_json_dict(self):
        """Verifies type inference on heterogeneous JSON payload."""
        sample_payload = {
            "node_id": "mesh_node_99",
            "capacity": 4096,
            "load_factor": 0.85,
            "is_active": True,
            "tags": ["core", "edge"],
            "config": {"retries": 3},
        }
        spec = self.synthesizer.infer_protocol(
            name="Cluster Node Register",
            method="POST",
            path="/api/v1/nodes/register",
            raw_payload=sample_payload,
        )
        self.assertIsNotNone(spec)
        self.assertEqual(spec.method, "POST")
        self.assertEqual(spec.path, "/api/v1/nodes/register")
        self.assertEqual(spec.auth_type, "NONE")
        self.assertEqual(len(spec.request_fields), 6)

        field_map = {f.name: f.inferred_type for f in spec.request_fields}
        self.assertEqual(field_map["node_id"], "str")
        self.assertEqual(field_map["capacity"], "int")
        self.assertEqual(field_map["load_factor"], "float")
        self.assertEqual(field_map["is_active"], "bool")
        self.assertEqual(field_map["tags"], "list")
        self.assertEqual(field_map["config"], "dict")

    def test_03_infer_bearer_and_apikey_auth(self):
        """Verifies detection of Bearer and API Key authentication schemes."""
        spec_bearer = self.synthesizer.infer_protocol(
            name="Secure Vault",
            method="GET",
            path="/vault/secrets",
            headers={"Authorization": "Bearer sov_token_xyz123"},
        )
        self.assertEqual(spec_bearer.auth_type, "BEARER")

        spec_apikey = self.synthesizer.infer_protocol(
            name="Telemetry Stream",
            method="GET",
            path="/stream/telemetry",
            headers={"X-API-Key": "apikey_secure_789"},
        )
        self.assertEqual(spec_apikey.auth_type, "API_KEY")

    def test_04_infer_from_curl_command(self):
        """Verifies extraction of method, path, headers, and payload from curl snippet."""
        curl_cmd = (
            "curl -X POST https://cluster.lucy.mesh/api/v2/jobs "
            "-H 'Authorization: Bearer secret999' "
            "-H 'Content-Type: application/json' "
            "-d '{\"job_name\": \"ast_quantization\", \"workers\": 4, \"priority\": 1}'"
        )
        spec = self.synthesizer.infer_from_curl(curl_cmd)
        self.assertIsNotNone(spec)
        self.assertEqual(spec.method, "POST")
        self.assertEqual(spec.path, "/api/v2/jobs")
        self.assertEqual(spec.auth_type, "BEARER")
        self.assertEqual(len(spec.request_fields), 3)

        field_names = {f.name for f in spec.request_fields}
        self.assertIn("job_name", field_names)
        self.assertIn("workers", field_names)
        self.assertIn("priority", field_names)

    def test_05_synthesize_client_code(self):
        """Verifies generated Python client code is syntactically valid and compendious."""
        spec = self.synthesizer.infer_protocol(
            name="Telemetry Dispatcher",
            method="POST",
            path="/api/telemetry/submit",
            raw_payload={"metric": "cpu_load", "value": 78.5},
            headers={"Authorization": "Bearer my_token"},
        )
        code = self.synthesizer.synthesize_client_code(spec.protocol_id)
        self.assertIn("TelemetryDispatcherClient", code)
        self.assertIn("post_api_telemetry_submit", code)
        self.assertIn("Authorization", code)
        self.assertIn("Senin", code)

        # Verify syntactical validity using python built-in compile()
        compiled = compile(code, "<synthesized_client>", "exec")
        self.assertIsNotNone(compiled)

    def test_06_mock_response_generation(self):
        """Verifies mock response data follows the inferred field schema."""
        spec = self.synthesizer.infer_protocol(
            name="User Profile",
            method="GET",
            path="/api/user/profile",
            raw_payload={"username": "operator_senin", "tier": 1},
        )
        mock = self.synthesizer.generate_mock_response(spec.protocol_id)
        self.assertEqual(mock["status"], "success")
        self.assertEqual(mock["protocol_id"], spec.protocol_id)
        self.assertEqual(mock["mock_data"]["username"], "operator_senin")
        self.assertEqual(mock["mock_data"]["tier"], 1)

    def test_07_persistence_manifest(self):
        """Verifies protocol definitions persist to disk and reload across instances."""
        spec = self.synthesizer.infer_protocol(
            name="Persistent Mesh API",
            method="PUT",
            path="/mesh/sync",
            raw_payload={"sync_id": 999},
        )
        # Create second synthesizer instance pointing to same directory
        synth2 = ProtocolReverseSynthesizer(
            project_root=self.project_root,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
        )
        reloaded = synth2.get_protocol(spec.protocol_id)
        self.assertIsNotNone(reloaded)
        self.assertEqual(reloaded.name, "Persistent Mesh API")
        self.assertEqual(reloaded.method, "PUT")

    def test_08_receipt_ledger_integration(self):
        """Verifies receipts emitted to execution ledger for inference and synthesis."""
        spec = self.synthesizer.infer_protocol(
            name="Ledger Test Endpoint",
            method="DELETE",
            path="/items/123",
        )
        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("PROTOCOL_INFERRED", actions)

        self.synthesizer.synthesize_client_code(spec.protocol_id)
        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("CLIENT_SYNTHESIZED", actions)

        self.synthesizer.generate_mock_response(spec.protocol_id)
        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("MOCK_SERVER_INITIALIZED", actions)

    def test_09_ascii_status_table(self):
        """Verifies CP1252-safe ASCII table output."""
        self.synthesizer.infer_protocol(
            name="ASCII Table Endpoint",
            method="GET",
            path="/api/ascii/test",
            raw_payload={"active": True},
        )
        table = self.synthesizer.format_protocol_status_table()
        self.assertIn("PROTOCOL REVERSE-ENGINEER & SYNTHESIZER", table)
        self.assertIn("ASCII Table Endpoint", table)
        self.assertIn("Senin", table)
        # Strict CP1252 compatibility test
        table.encode("cp1252")

    def test_10_runtime_integration(self):
        """Verifies LucyRuntime binds and executes protocol synthesizer commands."""
        from backend.lucy_core.lucy_runtime import LucyRuntime

        runtime = LucyRuntime(project_root=self.project_root)
        self.assertTrue(hasattr(runtime, "protocol_synthesizer"))
        self.assertIsInstance(runtime.protocol_synthesizer, ProtocolReverseSynthesizer)

        # Test CLI commands via lucy_respond
        res = runtime.lucy_respond("/protocol-status")
        self.assertIn("PROTOCOL REVERSE-ENGINEER & SYNTHESIZER", res)

        res_infer = runtime.lucy_respond("/infer-protocol curl -X POST https://api.lucy.net/v1/agent -d '{\"mode\":\"sovereign\"}'")
        self.assertIn("Inferred Protocol", res_infer)

        res_synth = runtime.lucy_respond("/synthesize-client proto_")
        self.assertTrue(len(res_synth) > 0)


if __name__ == "__main__":
    unittest.main()
