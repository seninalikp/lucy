"""
test_stage37_fact_state_verifier.py
Stage 37 = ELIE Absorption & Deterministic Fact/State Verifier.

Verifies:
1. Extraction of claimed file paths from text.
2. Verified claims: If file exists on physical disk, verified=True and badge matches.
3. Hallucination detection: If claimed file does NOT exist on disk, verified=False and hallucination_detected=True.
4. ELIE Security Review: Flags dangerous execution patterns (eval, exec, hardcoded secrets).
5. Router command integration: "fact verifier status", "verify fact <claim>", "elie review <code>".
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter
from backend.lucy_core.fact_state_verifier import FactStateVerifier


class TestStage37FactStateVerifier(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "data" / "lucy").mkdir(parents=True, exist_ok=True)
        (self.root / "logs").mkdir(parents=True, exist_ok=True)
        (self.root / "backend" / "lucy_core").mkdir(parents=True, exist_ok=True)
        # Create a real file on disk for positive verification testing
        (self.root / "backend" / "lucy_core" / "real_scanner.py").write_text("# real file", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _runtime_and_router(self):
        runtime = LucyRuntime(project_root=self.root)
        router = CommandRouter(runtime)
        return runtime, router

    def test_01_fact_verifier_status_command(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("fact verifier status")
        self.assertIn("ELIE Fact/State Verifier status:", response.message)
        self.assertIn("Stage: 37 fact state verifier", response.message)
        self.assertIn("Verification Mode: physical_disk_state_only", response.message)
        self.assertIn("Anti-Hallucination Gate: enforced", response.message)

    def test_02_status_aliases_work(self) -> None:
        _, router = self._runtime_and_router()
        for cmd in ["fact state status", "anti hallucination status", "elie verifier status"]:
            self.assertIn("ELIE Fact/State Verifier status:", router.handle(cmd).message)

    def test_03_positive_verification_file_exists(self) -> None:
        verifier = FactStateVerifier(self.root)
        claim = "I created backend/lucy_core/real_scanner.py successfully."
        res = verifier.verify_claim(claim)
        self.assertTrue(res["verified"])
        self.assertFalse(res["hallucination_detected"])
        self.assertIn("real_scanner.py", res["verified_paths"][0])
        self.assertIn("ELIE: VERIFIED", res["badge"])

    def test_04_negative_verification_hallucination_intercepted(self) -> None:
        verifier = FactStateVerifier(self.root)
        # Claim mentioning a file that does NOT exist
        claim = "I have created backend/lucy_core/fake_nonexistent_tool.py for you."
        res = verifier.verify_claim(claim)
        self.assertFalse(res["verified"])
        self.assertTrue(res["hallucination_detected"])
        self.assertIn("fake_nonexistent_tool.py", res["missing_paths"][0])
        self.assertIn("HALLUCINATION_INTERCEPTED", res["badge"])

    def test_05_router_verify_fact_command(self) -> None:
        _, router = self._runtime_and_router()
        # Verify nonexistent file via router
        resp1 = router.handle('verify fact "I saved the file phantom_module.py on disk"')
        self.assertIn("Hallucination Detected: true", resp1.message)
        self.assertIn("HALLUCINATION_INTERCEPTED", resp1.message)

        # Verify real file via router
        resp2 = router.handle('verify fact "I updated backend/lucy_core/real_scanner.py"')
        self.assertIn("Verified: true", resp2.message)
        self.assertIn("ELIE: VERIFIED", resp2.message)

    def test_06_elie_security_review_flags_eval_and_secrets(self) -> None:
        verifier = FactStateVerifier(self.root)
        dangerous_code = "eval(user_input)\napi_key = 'sk-1234567890abcdef1234567890'"
        report = verifier.elie_security_review(dangerous_code)
        self.assertFalse(report["safe"])
        self.assertIn("SECURITY_FLAGGED", report["badge"])
        self.assertTrue(any("eval" in issue for issue in report["issues"]))
        self.assertTrue(any("credential" in issue for issue in report["issues"]))

    def test_07_elie_security_review_passes_safe_code(self) -> None:
        verifier = FactStateVerifier(self.root)
        safe_code = "def add(a: int, b: int) -> int:\n    return a + b\n"
        report = verifier.elie_security_review(safe_code)
        self.assertTrue(report["safe"])
        self.assertIn("SECURITY_APPROVED", report["badge"])


if __name__ == "__main__":
    unittest.main()
