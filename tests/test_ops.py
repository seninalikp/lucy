import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.ops import SafeOps


class SafeOpsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "run_lucy_core.py").write_text("print('lucy')", encoding="utf-8")
        core = self.root / "backend" / "lucy_core"
        core.mkdir(parents=True)
        (core / "lucy_runtime.py").write_text("runtime = True", encoding="utf-8")
        (core / "router.py").write_text("router = True", encoding="utf-8")
        self.ops = SafeOps(self.root, self.root / "data" / "lucy")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_scan_project(self) -> None:
        report = self.ops.scan_project()
        self.assertIn("report_path", report)
        self.assertEqual(len(report["checks"]), 3)

    def test_backup_project(self) -> None:
        result = self.ops.backup_project()
        self.assertTrue(result["created"])
        self.assertTrue(Path(result["path"]).exists())


if __name__ == "__main__":
    unittest.main()
