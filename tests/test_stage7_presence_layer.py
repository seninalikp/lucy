import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.presence import PresenceLayer
from backend.lucy_core.router import CommandRouter


class Stage7PresenceLayerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_presence_report_includes_wake_fields(self) -> None:
        runtime = LucyRuntime(project_root=self.root)
        report = runtime.presence()
        self.assertIn("wake_label", report)
        self.assertIn("continuity_pulse", report)
        self.assertIn("presence_coherence_score", report)
        self.assertIn("drift_risk", report)
        self.assertIn("limitations", report)

    def test_presence_command_executes_without_crash(self) -> None:
        runtime = LucyRuntime(project_root=self.root)
        response = CommandRouter(runtime).handle("presence")
        self.assertFalse(response.should_exit)
        self.assertIn("Presence", response.message)

    def test_presence_layer_does_not_claim_subjective_state(self) -> None:
        report = PresenceLayer().build_report(
            {
                "active_project": "Lucy",
                "wake_label": "checkpoint_ready",
                "next_action": "Run tests.",
                "continuity_pulse": "Active project: Lucy. Next safe action: Run tests.",
                "presence_coherence_score": 0.9,
                "drift_risk": "low",
                "limitations": ["No daemon mode."],
            }
        ).to_dict()
        text = repr(report).lower()
        self.assertNotIn("i " + "feel", text)
        self.assertNotIn("i am " + "alive", text)


if __name__ == "__main__":
    unittest.main()
