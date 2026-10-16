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

    def test_short_innocent_strings_do_not_trigger_false_positives(self) -> None:
        from backend.lucy_core.guardian import GuardianCore, SAFE
        core = GuardianCore()
        for token in ["", "   ", "move", "run", "key", "status", "hello"]:
            res = core.classify_action(token)
            self.assertEqual(res.classification, SAFE, f"Expected {token!r} to be SAFE, got {res.classification}")
            check_res = self.guardian.check(token)
            self.assertEqual(check_res.status, "safe", f"Expected {token!r} to be safe in boundary checker, got {check_res.status}")


if __name__ == "__main__":
    unittest.main()
