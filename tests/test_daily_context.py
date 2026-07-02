import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from backend.lucy_core.daily_context import DailyContextEngine


class DailyContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.daily = DailyContextEngine(Path(self.temp_dir.name))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_checkin_creates_structured_today_log(self) -> None:
        result = self.daily.checkin(
            'energy=7 sleep=ok main_project=Lucy completed="router tests; docs" '
            'tomorrow="run health" notes="foundation work"',
            project_context={"name": "Lucy", "next_action": "stabilize"},
        )

        self.assertTrue(result["updated"])
        entry = result["entry"]
        self.assertEqual(entry["energy"], 7)
        self.assertEqual(entry["sleep_status"], "ok")
        self.assertEqual(entry["main_project_today"], "Lucy")
        self.assertEqual(entry["tasks_completed"], ["router tests", "docs"])
        self.assertEqual(entry["tomorrow_priority"], "run health")
        self.assertIn("foundation work", entry["notes"])

    def test_secret_like_daily_context_is_redacted(self) -> None:
        result = self.daily.checkin('notes="my password is test"')

        self.assertEqual(result["redacted_count"], 1)
        self.assertEqual(result["entry"]["notes"], "[redacted-sensitive-daily-context]")

    def test_yesterday_and_weekly_review(self) -> None:
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        self.daily.checkin('completed="wrote memory schema" lesson="keep scope tight"', day=yesterday)

        summary = self.daily.yesterday()
        self.assertTrue(summary["found"])
        self.assertIn("wrote memory schema", summary["entry"]["tasks_completed"])

        weekly = self.daily.weekly_review()
        self.assertGreaterEqual(weekly["days_found"], 1)
        self.assertIn("wrote memory schema", weekly["tasks_completed"])
        self.assertIn("keep scope tight", weekly["lessons_learned"])


if __name__ == "__main__":
    unittest.main()
