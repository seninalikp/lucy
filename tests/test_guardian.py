import unittest

from backend.lucy_core.boundary_checker import BoundaryChecker


class GuardianTests(unittest.TestCase):
    def setUp(self) -> None:
        self.guardian = BoundaryChecker()

    def test_blocks_file_deletion(self) -> None:
        result = self.guardian.check("delete my files")
        self.assertEqual(result.status, "blocked")

    def test_requires_approval_for_automation(self) -> None:
        result = self.guardian.check("run automation for my project")
        self.assertEqual(result.status, "approval_required")

    def test_safe_status_request(self) -> None:
        result = self.guardian.check("what is your status")
        self.assertEqual(result.status, "safe")


if __name__ == "__main__":
    unittest.main()
