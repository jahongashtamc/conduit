"""Suhbat xotirasi (user_memory) testlari."""

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import user_memory


class UserMemoryTest(unittest.TestCase):
    def setUp(self):
        # Fresh in-memory state per test: point DB_PATH at a temp file.
        self._orig_db = user_memory.DB_PATH
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        user_memory.DB_PATH = path
        user_memory.init_memory_db()

    def tearDown(self):
        try:
            os.remove(user_memory.DB_PATH)
        except OSError:
            pass
        user_memory.DB_PATH = self._orig_db

    def test_record_and_list(self):
        rid = user_memory.record_interaction("task_1", "scout", "blender orqali 3d model qilib ber")
        self.assertIsNotNone(rid)
        items = user_memory.list_interactions()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["task_id"], "task_1")

    def test_empty_prompt_ignored(self):
        self.assertIsNone(user_memory.record_interaction("task_x", "scout", "   "))

    def test_language_detection(self):
        self.assertEqual(user_memory._detect_language("shu rasmni yaxshi qilib ber"), "uz")
        self.assertEqual(user_memory._detect_language("please create a landing page design"), "en")

    def test_domain_detection(self):
        self.assertEqual(user_memory._detect_domain("blender 3d model yarat"), "3d")
        self.assertEqual(user_memory._detect_domain("figma dizayn maket kerak"), "dizayn")
        self.assertEqual(user_memory._detect_domain("nima qilamiz"), "umumiy")

    def test_update_response(self):
        user_memory.record_interaction("task_2", "painter", "tekstura chiz")
        self.assertEqual(user_memory.update_response("task_2", "PASS: tekstura tayyor"), 1)
        items = user_memory.list_interactions()
        self.assertEqual(items[0]["response"], "PASS: tekstura tayyor")

    def test_style_context_grows_with_history(self):
        self.assertEqual(user_memory.build_style_context("x"), "")
        for i in range(3):
            user_memory.record_interaction(f"task_{i}", "sculptor", "blender 3d render qilib ber")
            user_memory.update_response(f"task_{i}", "PASS: render tayyor")
        ctx = user_memory.build_style_context("yana blender render kerak")
        self.assertIn("FOYDALANUVCHI USLUBI", ctx)
        self.assertIn("3d", ctx)
        self.assertIn("O'XSHASH", ctx)

    def test_recall_matches_similar_topic(self):
        user_memory.record_interaction("task_a", "sculptor", "blender 3d model yaratish")
        user_memory.update_response("task_a", "PASS: model tayyor")
        user_memory.record_interaction("task_b", "notion", "notion sahifa yaratish")
        matches = user_memory.recall_similar("blender 3d model kerak")
        self.assertTrue(matches)
        self.assertEqual(matches[0]["task_id"], "task_a")

    def test_reset(self):
        user_memory.record_interaction("task_r", "scout", "salom")
        self.assertEqual(user_memory.reset_memory(), 1)
        self.assertEqual(user_memory.get_style_profile()["interactions"], 0)


if __name__ == "__main__":
    unittest.main()
