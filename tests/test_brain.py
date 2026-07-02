import unittest

from backend.lucy_core.brain import BrainRouter, ResponseChecker


class BrainTests(unittest.TestCase):
    def test_brain_status_is_local_only(self) -> None:
        router = BrainRouter()
        status = router.status()
        self.assertTrue(status["local_fallback"])
        self.assertFalse(status["external_api_enabled"])

    def test_response_checker_blocks_forbidden_claim(self) -> None:
        checker = ResponseChecker()
        response = checker.sanitize("I am conscious.")
        self.assertFalse(response.ok)

    def test_local_brain_answers(self) -> None:
        router = BrainRouter()
        response = router.ask(
            "what now",
            {"name": "Lucy", "next_action": "Run tests", "open_tasks": []},
            [],
        )
        self.assertTrue(response.ok)
        self.assertIn("Active project", response.text)


if __name__ == "__main__":
    unittest.main()
