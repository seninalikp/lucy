import json
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import STAGE34_OPERATIONAL_NEXT_ACTION, STAGE34_SAFE_NEXT_ACTION, LucyRuntime
from backend.lucy_core.router import CommandRouter


class CommandAliasTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.runtime = LucyRuntime(project_root=self.root)
        self.router = CommandRouter(self.runtime)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_safe_status_typo_aliases_route_deterministically(self) -> None:
        cases = {
            "valuation lab status": "Evaluation lab status:",
            "eval lab status": "Evaluation lab status:",
            "growth proposal status": "Growth proposals status:",
            "groth proposal status": "Growth proposals status:",
            "self modal status": "Self-model status:",
            "shadow test status": "Shadow testing status:",
            "first thot status": "First thought status:",
            "run time status": "Runtime status:",
            "agents status": "Internal agents: active.",
            "agents report": "Internal agent report:",
        }
        for command, expected in cases.items():
            with self.subTest(command=command):
                response = self.router.handle(command)
                self.assertFalse(response.should_exit)
                self.assertIn(expected, response.message)

    def test_safe_evaluation_shadow_aliases_route_deterministically(self) -> None:
        cases = {
            "evaluate prposal": "Evaluation unavailable:",
            "evaluate groth proposal": "Evaluation unavailable:",
            "show evaluation": "Evaluations:",
            "show shadow test": "Shadow tests:",
        }
        for command, expected in cases.items():
            with self.subTest(command=command):
                response = self.router.handle(command)
                self.assertFalse(response.should_exit)
                self.assertIn(expected, response.message)

    def test_next_aliases_return_stage33_gate(self) -> None:
        for command in ["what next", "next", "now what", "wht next"]:
            with self.subTest(command=command):
                response = self.router.handle(command)
                self.assertFalse(response.should_exit)
                self.assertIn(STAGE34_OPERATIONAL_NEXT_ACTION, response.message)
                self.assertIn("Stage 35:", response.message)
                self.assertIn("First manual model call stage blocked", response.message)

    def test_ambiguous_short_commands_ask_clarification(self) -> None:
        proposal = self.router.handle("proposal")
        shadow = self.router.handle("shadow")

        self.assertIn("Do you mean growth proposals status", proposal.message)
        self.assertIn("Do you mean shadow testing status", shadow.message)

    def test_old_provider_key_next_action_is_not_reported(self) -> None:
        stale = "Review desktop UI, checkpoint_0101, fallback learning proposals, and NVIDIA key setup after sleep."
        data = json.loads(self.runtime.projects.projects_file.read_text(encoding="utf-8"))
        project = data["projects"]["Lucy"]
        project["next_action"] = stale
        project["tasks"] = [
            {
                "id": "task_stale",
                "text": stale,
                "status": "open",
                "created_at": "2026-06-09T00:00:00+00:00",
                "completed_at": None,
            }
        ]
        self.runtime.projects.projects_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

        output = "\n".join(
            [
                self.router.handle("tell me").message,
                self.router.handle("what next").message,
                self.router.handle("agent report").message,
                self.router.handle("where did we stop").message,
            ]
        )

        self.assertIn(STAGE34_SAFE_NEXT_ACTION, output)
        self.assertNotIn("NVIDIA key setup", output)
        self.assertNotIn("provider key setup", output)
        self.assertNotIn("API key setup", output)

    def test_stage17_provider_and_external_features_are_not_started(self) -> None:
        self.assertFalse(hasattr(self.runtime, "patch_pipeline"))
        self.assertFalse(hasattr(self.runtime, "provider_router"))
        self.assertFalse(hasattr(self.runtime.shadow_testing, "apply_patch"))
        self.assertFalse((self.root / "data" / "lucy" / "providers").exists())


if __name__ == "__main__":
    unittest.main()
