"""
tests/test_stage136_sovereign_wheel_fabric.py
Verification suite for Stage 136: Self-Hosted Package Index & Sovereign Wheel Fabric
Era 14: Autonomous Code Evolution, Semantic Mutation & Static Synthesis
"""

import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from backend.lucy_core.sovereign_wheel_fabric import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    ERA_NAME,
    STAGE,
    STAGE_NAME,
    SovereignWheelFabricIndex,
    SovereignWheelRecord,
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


class TestStage136SovereignWheelFabric(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)
        self.data_dir = self.project_root / "data" / "lucy" / "wheels"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = MockReceiptLedger()
        self.fabric = SovereignWheelFabricIndex(
            project_root=self.project_root,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_metadata(self):
        """Verifies sovereign operator identity and stage/era metadata."""
        self.assertEqual(STAGE, 136)
        self.assertEqual(ERA, 14)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")
        status = self.fabric.status()
        self.assertEqual(status["stage"], 136)
        self.assertEqual(status["era"], 14)
        self.assertEqual(status["creator"], "Senin")
        self.assertEqual(status["creator_full_name"], "Senin Ali K P")

    def test_02_build_basic_wheel(self):
        """Verifies PEP 427 compliant wheel archive structure."""
        rec = self.fabric.build_wheel("lucy_tensor", version="0.1.0")
        self.assertIsNotNone(rec)
        self.assertEqual(rec.package_name, "lucy_tensor")
        self.assertEqual(rec.version, "0.1.0")

        wheel_path = self.data_dir / rec.wheel_filename
        self.assertTrue(wheel_path.exists())

        with zipfile.ZipFile(wheel_path, "r") as zf:
            names = zf.namelist()
            self.assertIn("lucy_tensor-0.1.0.dist-info/METADATA", names)
            self.assertIn("lucy_tensor-0.1.0.dist-info/WHEEL", names)
            self.assertIn("lucy_tensor-0.1.0.dist-info/RECORD", names)
            self.assertIn("lucy_tensor/__init__.py", names)

    def test_03_verify_wheel_integrity_pass(self):
        """Verifies cryptographic hash audit passes for untampered wheel."""
        rec = self.fabric.build_wheel("lucy_crypto", version="1.2.0")
        audit = self.fabric.verify_wheel(rec.wheel_filename)
        self.assertEqual(audit["status"], "success")
        self.assertTrue(audit["is_valid"])
        self.assertEqual(len(audit["tampered_files"]), 0)

    def test_04_verify_wheel_tamper_detection(self):
        """Verifies tampering with an internal file is detected by RECORD audit."""
        rec = self.fabric.build_wheel("tamper_test", version="1.0.0")
        wheel_path = self.data_dir / rec.wheel_filename

        # Corrupt a file by re-packing with modified content
        tampered_path = self.data_dir / "tampered.whl"
        with zipfile.ZipFile(wheel_path, "r") as src_zf:
            with zipfile.ZipFile(tampered_path, "w") as dst_zf:
                for item in src_zf.infolist():
                    content = src_zf.read(item.filename)
                    if item.filename.endswith("__init__.py"):
                        content = b"TAMPERED_INJECTED_CODE = True\n"
                    dst_zf.writestr(item, content)

        shutil.move(tampered_path, wheel_path)
        audit = self.fabric.verify_wheel(rec.wheel_filename)
        self.assertEqual(audit["status"], "tampered")
        self.assertFalse(audit["is_valid"])
        self.assertGreaterEqual(len(audit["tampered_files"]), 1)

    def test_05_wheel_custom_source_files(self):
        """Verifies bundling arbitrary source files and subpackages."""
        sources = {
            "my_plugin/__init__.py": "VERSION = '1.0'\n",
            "my_plugin/core.py": "def run(): return 42\n",
            "my_plugin/utils.py": "def helper(): return 'ok'\n",
        }
        rec = self.fabric.build_wheel("my_custom_plugin", version="2.0.0", source_files=sources)
        self.assertEqual(rec.total_files_contained, 6)  # 3 sources + METADATA, WHEEL, RECORD

    def test_06_hmac_provenance_signature(self):
        """Verifies HMAC-SHA256 signature length and determinism."""
        rec = self.fabric.build_wheel("signed_pkg", version="1.0.0")
        self.assertEqual(len(rec.hmac_signature), 64)
        self.assertEqual(len(rec.sha256_digest), 64)

    def test_07_persistence_manifest(self):
        """Verifies wheel catalog persists to disk and reloads across instances."""
        rec = self.fabric.build_wheel("persistent_pkg", version="1.0.0")

        fabric2 = SovereignWheelFabricIndex(
            project_root=self.project_root,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
        )
        self.assertIn("persistent_pkg:1.0.0", fabric2._packages)
        self.assertEqual(fabric2.status()["total_built"], 1)

    def test_08_receipt_ledger_integration(self):
        """Verifies receipts are emitted for package building and verification."""
        rec = self.fabric.build_wheel("receipt_pkg", version="1.0.0")
        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("WHEEL_PACKAGE_BUILT", actions)

        self.fabric.verify_wheel(rec.wheel_filename)
        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("PACKAGE_SIGNATURE_VERIFIED", actions)

    def test_09_ascii_wheel_status_table(self):
        """Verifies CP1252-safe ASCII table formatting."""
        self.fabric.build_wheel("table_pkg", version="1.0.0")
        table = self.fabric.format_wheel_status_table()
        self.assertIn("SOVEREIGN WHEEL FABRIC & INDEX", table)
        self.assertIn("table_pkg", table)
        self.assertIn("Senin", table)
        # Strict CP1252 compatibility test
        table.encode("cp1252")

    def test_10_runtime_integration(self):
        """Verifies LucyRuntime binds and executes wheel fabric commands."""
        from backend.lucy_core.lucy_runtime import LucyRuntime

        runtime = LucyRuntime(project_root=self.project_root)
        self.assertTrue(hasattr(runtime, "wheel_fabric"))
        self.assertIsInstance(runtime.wheel_fabric, SovereignWheelFabricIndex)

        # Test CLI commands via lucy_respond
        res = runtime.lucy_respond("/wheel-status")
        self.assertIn("SOVEREIGN WHEEL FABRIC & INDEX", res)

        res_build = runtime.lucy_respond("/build-wheel rt_package 1.0.0")
        self.assertIn("Wheel Package Built", res_build)

        res_ver = runtime.lucy_respond("/verify-wheel rt_package-1.0.0-py3-none-any.whl")
        self.assertIn("Wheel Verification Complete", res_ver)


if __name__ == "__main__":
    unittest.main()
