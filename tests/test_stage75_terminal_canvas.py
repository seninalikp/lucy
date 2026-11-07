"""
tests/test_stage75_terminal_canvas.py
Unit tests for Stage 75: Terminal ANSI Canvas & Syntax-Highlighted Visual Stream
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.terminal_canvas import (
    TerminalCanvas,
    TerminalSyntaxHighlighter,
    strip_ansi,
    STAGE,
)


class TestStage75TerminalCanvas(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_stage75_test_"))
        self.canvas = TerminalCanvas(colors_enabled=True)
        self.plain_canvas = TerminalCanvas(colors_enabled=False)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_stage_constant(self):
        self.assertEqual(STAGE, 75)

    def test_02_strip_ansi(self):
        colored = "\033[31mError:\033[0m \033[32mSuccess\033[0m"
        stripped = strip_ansi(colored)
        self.assertEqual(stripped, "Error: Success")

    def test_03_python_syntax_highlighting(self):
        code = 'def greet(name: str):\n    # Say hello\n    return f"Hello {name}"\n'
        hl = self.canvas.highlighter.highlight_python(code, line_numbers=True)

        # Ensure line numbers are present
        self.assertIn("1 |", hl)
        self.assertIn("2 |", hl)
        self.assertIn("3 |", hl)

        # Check keyword colored
        self.assertIn("def", hl)
        self.assertIn("return", hl)

        # Check stripped content matches original logic
        stripped = strip_ansi(hl)
        self.assertIn("def greet(name: str):", stripped)
        self.assertIn("# Say hello", stripped)

    def test_04_diff_highlighting(self):
        diff = (
            "--- a/file.py\n"
            "+++ b/file.py\n"
            "@@ -1,3 +1,3 @@\n"
            "-old_line = 1\n"
            "+new_line = 2\n"
            " unchanged = 3\n"
        )
        hl = self.canvas.highlighter.highlight_diff(diff)
        self.assertIn("\033[32m+new_line = 2\033[0m", hl)
        self.assertIn("\033[31m-old_line = 1\033[0m", hl)
        self.assertIn("\033[36m@@ -1,3 +1,3 @@\033[0m", hl)

    def test_05_json_highlighting(self):
        js = '{\n  "status": "active",\n  "count": 42,\n  "enabled": true\n}'
        hl = self.canvas.highlighter.highlight_json(js)
        stripped = strip_ansi(hl)
        self.assertEqual(stripped, js)
        self.assertIn("\033[36m\"status\"\033[0m", hl)

    def test_06_markdown_highlighting(self):
        md = "# Title\n- Bullet item\n```python\nprint(1)\n```"
        hl = self.canvas.highlighter.highlight_markdown(md)
        stripped = strip_ansi(hl)
        self.assertEqual(stripped, md)

    def test_07_disabled_colors_returns_plain_text(self):
        code = "def foo():\n    return 42"
        hl = self.plain_canvas.highlighter.highlight_python(code, line_numbers=False)
        self.assertEqual(hl, code)

    def test_08_render_box_ascii_safe(self):
        title = "Execution Status"
        lines = ["Step 1: Parse code", "Step 2: Execute sandbox", "Status: OK"]
        box = self.canvas.render_box(title, lines, width=50)

        # Must encode to pure ASCII without error
        box.encode("ascii")
        self.assertIn("+", box)
        self.assertIn("-", box)
        self.assertIn("|", box)
        self.assertIn("EXECUTION STATUS", box)
        self.assertIn("Step 1: Parse code", box)

    def test_09_render_progress_bar(self):
        bar_0 = self.canvas.render_progress_bar(0, 100, width=10)
        self.assertEqual(bar_0, "[          ]   0% (0/100)")

        bar_50 = self.canvas.render_progress_bar(5, 10, width=10)
        self.assertEqual(bar_50, "[====>     ]  50% (5/10)")

        bar_100 = self.canvas.render_progress_bar(10, 10, width=10)
        self.assertEqual(bar_100, "[==========] 100% (10/10)")

    def test_10_render_tree(self):
        sub1 = self.test_dir / "backend"
        sub1.mkdir()
        (sub1 / "main.py").write_text("print('main')", encoding="utf-8")
        (self.test_dir / "config.json").write_text("{}", encoding="utf-8")

        tree_str = self.canvas.render_tree(self.test_dir, max_depth=2)
        tree_str.encode("ascii")
        self.assertIn("+-- backend/", tree_str)
        self.assertIn("+-- main.py", tree_str)
        self.assertIn("+-- config.json", tree_str)

    def test_11_view_file(self):
        sample = self.test_dir / "sample.py"
        sample.write_text("x = 10\ny = 20\nprint(x + y)", encoding="utf-8")

        view = self.canvas.view_file(sample, max_lines=10)
        self.assertIn("FILE: sample.py", view)
        self.assertIn("1 |", view)
        self.assertIn("x = 10", strip_ansi(view))


if __name__ == "__main__":
    unittest.main()
