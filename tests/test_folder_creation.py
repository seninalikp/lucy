"""
tests/test_folder_creation.py
Verification test suite for safe folder creation via runtime, router, natural action parser,
and Writer Bot integration.
"""

import os
import shutil
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class TestFolderCreation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = LucyRuntime()
        cls.router = CommandRouter(cls.runtime)
        cls.test_dir_names = [
            "test_unit_folder_1",
            "test_unit_folder_2",
            "test_unit_folder_3",
            "test_unit_folder_an",
            "nested/sub_unit_folder",
        ]

    @classmethod
    def tearDownClass(cls):
        cls.runtime.graceful_shutdown("TestFolderCreation suite finished")

    def tearDown(self):
        for name in self.test_dir_names:
            base = name.split("/")[0]
            if os.path.exists(base):
                shutil.rmtree(base, ignore_errors=True)

    def test_01_runtime_create_folder(self):
        res = self.runtime.create_folder("test_unit_folder_1")
        self.assertTrue(res["ok"])
        self.assertTrue(res["created"])
        self.assertTrue(os.path.isdir("test_unit_folder_1"))

        # Second creation should indicate already existed
        res2 = self.runtime.create_folder("test_unit_folder_1")
        self.assertTrue(res2["ok"])
        self.assertTrue(res2["already_existed"])

    def test_02_router_create_folder_command(self):
        resp = self.router.dispatch("create folder test_unit_folder_2")
        self.assertIn("Created folder: test_unit_folder_2", resp.message)
        self.assertTrue(os.path.isdir("test_unit_folder_2"))

    def test_03_router_mkdir_command(self):
        resp = self.router.dispatch("mkdir test_unit_folder_3")
        self.assertIn("Created folder: test_unit_folder_3", resp.message)
        self.assertTrue(os.path.isdir("test_unit_folder_3"))

    def test_04_nested_folder_creation(self):
        res = self.runtime.create_folder("nested/sub_unit_folder")
        self.assertTrue(res["ok"])
        self.assertTrue(os.path.isdir("nested/sub_unit_folder"))

    def test_05_natural_action_parser_folder_make(self):
        res = self.runtime.natural_action_parser.parse_and_execute(
            "please make a folder called test_unit_folder_1"
        )
        self.assertGreaterEqual(res["actions_executed"], 1)
        self.assertTrue(os.path.isdir("test_unit_folder_1"))

    def test_06_traversal_attack_blocked(self):
        res = self.runtime.create_folder("../../outside_target")
        self.assertFalse(res["ok"])
        self.assertIn("outside", res["error"].lower())

    def test_07_make_an_folder_natural_and_router(self):
        # 1. Natural action parser 'make an folder'
        res_nat = self.runtime.natural_action_parser.parse_and_execute(
            "make an folder called test_unit_folder_an"
        )
        self.assertGreaterEqual(res_nat["actions_executed"], 1)
        self.assertTrue(os.path.isdir("test_unit_folder_an"))

        # 2. Router command 'make an folder'
        if os.path.exists("test_unit_folder_an"):
            shutil.rmtree("test_unit_folder_an", ignore_errors=True)
        resp_router = self.router.dispatch("make an folder test_unit_folder_an")
        self.assertIn("Created folder: test_unit_folder_an", resp_router.message)
        self.assertTrue(os.path.isdir("test_unit_folder_an"))

    def test_08_writer_bot_runtime_methods(self):
        # Ensure writer online method exists and responds
        online = self.runtime.ensure_writer_online(max_wait_seconds=4.0)
        self.assertTrue(online)

        conn_rep = self.runtime.connect_writer_bot()
        self.assertEqual(conn_rep["bot"], "writer")
        self.assertTrue(conn_rep["online"])
        self.assertEqual(conn_rep["status"], "CONNECTED")

        status_rep = self.runtime.writer_status()
        self.assertEqual(status_rep["bot"], "writer")
        self.assertTrue(status_rep["online"])

    def test_09_router_writer_commands(self):
        resp_conn = self.router.dispatch("connect writer bot")
        self.assertIn("Writer Bot Connection:", resp_conn.message)
        self.assertIn("Status: CONNECTED", resp_conn.message)

        resp_stat = self.router.dispatch("writer status")
        self.assertIn("Writer Bot Status: ONLINE", resp_stat.message)


if __name__ == "__main__":
    unittest.main()
