r"""
tests/test_stage138_dead_code_eliminator.py
Unit tests for Stage 138: Dead-Code Eliminator & AST Pruner.
Era 14: Autonomous Code Evolution, Semantic Mutation & Static Synthesis
"""

import ast
import hmac
import hashlib
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.dead_code_eliminator import (
    CREATOR,
    ERA,
    HMAC_SECRET,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    DeadCodeEliminator,
    DeadCodeItem,
    PruningReport,
)


class TestStage138DeadCodeEliminator(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.pruner = DeadCodeEliminator(project_root=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_metadata_and_initialization(self):
        self.assertEqual(STAGE, 138)
        self.assertEqual(ERA, 14)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")

        st = self.pruner.status()
        self.assertEqual(st["stage"], 138)
        self.assertEqual(st["status"], "ACTIVE_PRUNER")
        self.assertEqual(st["total_analyses"], 0)

    def test_02_detect_unused_import(self):
        code = "import sys\nimport os\nprint(os.name)\n"
        items, summary = self.pruner.analyze_code(code)
        unused = [i for i in items if i.item_type == "unused_import"]
        self.assertEqual(len(unused), 1)
        self.assertEqual(unused[0].name, "sys")

    def test_03_detect_unreachable_code_after_return(self):
        code = (
            "def test_func():\n"
            "    x = 10\n"
            "    return x\n"
            "    y = 20\n"
            "    print(y)\n"
        )
        items, summary = self.pruner.analyze_code(code)
        unreachable = [i for i in items if i.item_type == "unreachable_block"]
        self.assertGreaterEqual(len(unreachable), 1)
        self.assertEqual(unreachable[0].line_number, 4)

    def test_04_detect_unreachable_function_with_entrypoints(self):
        code = (
            "def main():\n"
            "    return active_helper()\n"
            "\n"
            "def active_helper():\n"
            "    return 42\n"
            "\n"
            "def orphan_subsystem():\n"
            "    return 999\n"
        )
        items, summary = self.pruner.analyze_code(code, entrypoints=["main"])
        dead_funcs = [i for i in items if i.item_type == "unreachable_function"]
        self.assertEqual(len(dead_funcs), 1)
        self.assertEqual(dead_funcs[0].name, "orphan_subsystem")

    def test_05_prune_code_generates_valid_python(self):
        code = (
            "import math\n"
            "import sys\n"
            "def run():\n"
            "    return 100\n"
            "    print('Never reached')\n"
            "res = run()\n"
        )
        report = self.pruner.prune_code(code)
        self.assertGreater(report.lines_saved, 0)
        self.assertNotIn("import math", report.pruned_source)
        self.assertNotIn("print('Never reached')", report.pruned_source)
        self.assertIn("def run():", report.pruned_source)
        # Verify valid AST parse
        ast.parse(report.pruned_source)

    def test_06_prune_file_with_disk_write(self):
        fpath = Path(self.test_dir) / "sample_module.py"
        content = "import unused_mod\n\ndef worker():\n    return 1\n    x = 2\n"
        fpath.write_text(content, encoding="utf-8")

        rep = self.pruner.prune_file(fpath, in_place=True)
        self.assertGreater(rep.lines_saved, 0)

        updated = fpath.read_text(encoding="utf-8")
        self.assertNotIn("import unused_mod", updated)
        self.assertNotIn("x = 2", updated)
        ast.parse(updated)

    def test_07_hmac_provenance_signature(self):
        code = "def sample():\n    return 'hello'\n"
        report = self.pruner.prune_code(code)
        self.assertTrue(report.hmac_signature)

        expected = hmac.new(HMAC_SECRET, report.pruned_source.encode("utf-8"), hashlib.sha256).hexdigest()
        self.assertEqual(report.hmac_signature, expected)

    def test_08_reachability_graph_generation(self):
        code = (
            "import json\n"
            "def step1():\n"
            "    step2()\n"
            "def step2():\n"
            "    pass\n"
        )
        graph = self.pruner.build_reachability_graph(code)
        self.assertIn("step1", graph["functions"])
        self.assertIn("step2", graph["functions"])
        self.assertIn("step2", graph["calls_adjacency"]["step1"])

    def test_09_syntax_error_handling(self):
        code = "def broken(:\n    pass\n"
        items, summary = self.pruner.analyze_code(code)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].item_type, "syntax_error")

    def test_10_ascii_status_and_report_tables(self):
        code = "import unused_pkg\nprint(1)\n"
        rep = self.pruner.prune_code(code)

        stat_table = self.pruner.format_status_table()
        self.assertIn("+=============================================================================+", stat_table)
        self.assertIn("LUCY DEAD-CODE ELIMINATOR & AST PRUNER [STAGE 138 | ERA 14]", stat_table)
        self.assertIn("Senin Ali K P", stat_table)

        rep_table = self.pruner.format_report_table(rep)
        self.assertIn("PRUNING REPORT:", rep_table)
        self.assertIn("unused_pkg", rep_table)


if __name__ == "__main__":
    unittest.main()
