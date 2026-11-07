r"""
tests/test_stage196_self_evolving_code_pipeline.py
Stage 196: Self-Evolving Code Synthesis & AST Verification Pipeline
Era 20: The Sovereign Bicentennial AGI Singularity & Autonomous Kernel Transcendence
"""

import unittest
from backend.lucy_core.self_evolving_code_pipeline import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    CodePatch,
    SelfEvolvingCodePipelineFabric,
)


class TestStage196SelfEvolvingCodePipeline(unittest.TestCase):
    """10 Unit Tests for Stage 196 Self-Evolving Code Synthesis & AST Verification Pipeline."""

    def setUp(self):
        self.fabric = SelfEvolvingCodePipelineFabric()

    def test_01_fabric_initialization(self):
        self.assertEqual(self.fabric.sovereign_operator, "Senin")
        self.assertEqual(len(self.fabric.patches), 0)
        self.assertEqual(self.fabric._audits_passed, 0)

    def test_02_safety_audit_clean_code(self):
        clean_code = """
def compute_factor(x: int) -> int:
    base = 100
    multiplier = 2
    return x * base * multiplier
"""
        is_safe, violations = self.fabric.analyze_safety(clean_code)
        self.assertTrue(is_safe)
        self.assertEqual(len(violations), 0)

    def test_03_safety_audit_rejects_eval_and_exec(self):
        unsafe_code = """
def backdoor(user_input):
    return eval(user_input)
"""
        is_safe, violations = self.fabric.analyze_safety(unsafe_code)
        self.assertFalse(is_safe)
        self.assertGreater(len(violations), 0)
        self.assertIn("eval", violations[0])

    def test_04_ast_constant_folding_arithmetic(self):
        code = """
def get_val(x):
    return x + (10 + 20)
"""
        optimized, count = self.fabric.optimize_ast(code)
        self.assertGreaterEqual(count, 1)
        self.assertIn("30", optimized)
        self.assertNotIn("10 + 20", optimized)

    def test_05_ast_constant_folding_dead_if_branch(self):
        code = """
def check_mode():
    if False:
        dead_val = 999
    return 42
"""
        optimized, count = self.fabric.optimize_ast(code)
        self.assertGreaterEqual(count, 1)
        self.assertNotIn("dead_val = 999", optimized)

    def test_06_synthesize_and_verify_success(self):
        code = """
def compute_score(x):
    bonus = 5 + 5
    if False:
        bonus = 0
    return x + bonus
"""
        test_inputs = [
            ((10,), 20),
            ((0,), 10),
            ((-5,), 5),
        ]
        patch = self.fabric.synthesize_and_verify(code, "compute_score", test_inputs)
        self.assertTrue(patch.is_safe)
        self.assertTrue(patch.verification_passed)
        self.assertGreater(patch.transforms_applied, 0)
        self.assertTrue(len(patch.signature) > 0)
        self.assertIn(patch.patch_id, self.fabric.patches)

    def test_07_synthesize_verification_failure_on_incorrect_function(self):
        code = """
def faulty_calc(x):
    return x * 2
"""
        test_inputs = [
            ((10,), 25),  # 10 * 2 = 20 != 25 -> Fails!
        ]
        patch = self.fabric.synthesize_and_verify(code, "faulty_calc", test_inputs)
        self.assertTrue(patch.is_safe)
        self.assertFalse(patch.verification_passed)
        self.assertEqual(patch.signature, "")

    def test_08_cryptographic_patch_signature(self):
        code = """
def add_ten(x):
    offset = 5 + 5
    return x + offset
"""
        patch = self.fabric.synthesize_and_verify(code, "add_ten", [((5,), 15)])
        self.assertTrue(patch.verification_passed)
        self.assertEqual(len(patch.signature), 64)  # SHA-256 hex digest

    def test_09_unified_diff_generation(self):
        code = """
def transform_me():
    val = 100 + 200
    return val
"""
        patch = self.fabric.synthesize_and_verify(code, "transform_me", [((), 300)])
        self.assertTrue(patch.verification_passed)
        self.assertIn("--- original.py", patch.diff)
        self.assertIn("+++ evolved.py", patch.diff)

    def test_10_ascii_status_and_metadata(self):
        s = self.fabric.status()
        self.assertEqual(s["stage"], 196)
        self.assertEqual(s["era"], 20)
        self.assertEqual(s["operator"], "Senin")

        ascii_out = self.fabric.format_ascii_status()
        self.assertIn("STAGE 196: SELF-EVOLVING CODE SYNTHESIS & AST VERIFICATION", ascii_out)
        self.assertIn("Sovereign Operator    : Senin", ascii_out)


if __name__ == "__main__":
    unittest.main()
