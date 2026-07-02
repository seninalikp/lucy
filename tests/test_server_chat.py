import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend import server


class ServerChatTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = server.app.test_client()

    def test_chat_endpoint_routes_message(self) -> None:
        fake_router = SimpleNamespace(
            handle=lambda message: SimpleNamespace(
                message=f"Lucy heard: {message}",
                should_exit=False,
            )
        )

        with patch("backend.server.get_lucy_router", return_value=fake_router):
            response = self.client.post("/api/chat", json={"message": "status"})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["reply"], "Lucy heard: status")
        self.assertFalse(data["should_exit"])
        self.assertIn("timestamp", data)

    def test_chat_endpoint_rejects_non_string_message(self) -> None:
        response = self.client.post("/api/chat", json={"message": ["status"]})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "message must be a string")


if __name__ == "__main__":
    unittest.main()
