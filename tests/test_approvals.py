import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.approval_manager import ApprovalManager


class ApprovalManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.approvals = ApprovalManager(Path(self.temp_dir.name))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_and_approve_request(self) -> None:
        request = self.approvals.create_request("run automation", "Automation requires approval.")
        result = self.approvals.review(request["id"][:8], "approved", note="Reviewed.")
        self.assertTrue(result["changed"])
        self.assertEqual(result["approval"]["status"], "approved")
        self.assertEqual(len(self.approvals.list_pending()), 0)

    def test_reject_unknown_request(self) -> None:
        result = self.approvals.review("missing", "rejected")
        self.assertFalse(result["changed"])


if __name__ == "__main__":
    unittest.main()
