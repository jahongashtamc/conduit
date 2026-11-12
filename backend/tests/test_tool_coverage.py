"""Subagent tool'larining to'liq mosligi testlari.

Har bir subagent role.md'da e'lon qilingan tool haqiqatan tools.py'da
mavjud bo'lishi shart — nomi bor lekin ishlamaydigan tool bo'lsin, bu soxta
imkoniyat bo'ladi.
"""

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tools
import security_guard
import user_memory


AGENTS = [
    "scout", "inspector", "sentinel", "sculptor", "designer",
    "animator", "editor", "painter", "notion", "slack", "superagent",
    "inst_blender", "inst_video", "inst_image", "inst_web", "inst_figma",
]

IMPLEMENTED_TOOLS = {
    "screenshot", "interact_web", "run_process", "get_logs", "check_goal",
    "blender_headless_exec", "runscript", "figma_sync",
    "gen_image", "video_render", "anim_render", "notion_api", "slack_api",
    "web_search",
}


class ToolCoverageTest(unittest.TestCase):
    def test_every_declared_tool_is_implemented(self):
        """role.md'dagi har bir tool tools.py'da mavjud bo'lishi kerak."""
        missing = {}
        for agent in AGENTS:
            allowed = security_guard.get_allowed_tools(agent)
            self.assertTrue(allowed, f"{agent}: role.md tool ro'yxati bo'sh")
            bad = allowed - IMPLEMENTED_TOOLS
            if bad:
                missing[agent] = sorted(bad)
        self.assertEqual(missing, {}, f"Amalga oshirilmagan tool'lar: {missing}")

    def test_role_specific_tools_present(self):
        """Har rolni o'z asosiy instrumenti borligi."""
        expect = {
            "sculptor": "blender_headless_exec",
            "designer": "figma_sync",
            "animator": "anim_render",
            "editor": "video_render",
            "painter": "gen_image",
            "notion": "notion_api",
            "slack": "slack_api",
        }
        for agent, tool in expect.items():
            allowed = security_guard.get_allowed_tools(agent)
            self.assertIn(tool, allowed, f"{agent} uchun {tool} yo'q")

    def test_superagent_has_broad_access(self):
        allowed = security_guard.get_allowed_tools("superagent")
        self.assertIn("screenshot", allowed)
        self.assertIn("gen_image", allowed)
        self.assertIn("video_render", allowed)

    def test_gen_image_creates_real_png(self):
        res = tools.tool_gen_image("test texture pattern", 256, 256)
        self.assertTrue(res["success"], res.get("error"))
        self.assertTrue(os.path.exists(res["image_path"]))
        self.assertGreater(res["bytes"], 1000)
        # Determinizm: bir xil prompt = bir xil fayl hajmi.
        res2 = tools.tool_gen_image("test texture pattern", 256, 256)
        self.assertEqual(res["bytes"], res2["bytes"])

    def test_video_render_creates_real_mp4(self):
        if not tools._ffmpeg_path():
            self.skipTest("FFmpeg o'rnatilmagan")
        res = tools.tool_video_render("test clip", 1.0)
        self.assertTrue(res["success"], res.get("error"))
        self.assertTrue(os.path.exists(res["video_path"]))
        self.assertGreater(res["frames"], 0)

    def test_anim_render_creates_real_gif(self):
        if not tools._ffmpeg_path():
            self.skipTest("FFmpeg o'rnatilmagan")
        res = tools.tool_anim_render('[{"t":0,"color":"#000000"},{"t":1,"color":"#ffffff"}]', 1.0)
        self.assertTrue(res["success"], res.get("error"))
        self.assertTrue(os.path.exists(res["animation_path"]))

    def test_notion_slack_honest_without_token(self):
        with mock.patch.dict(os.environ, {"NOTION_TOKEN": "", "SLACK_BOT_TOKEN": ""}):
            n = tools.tool_notion_api("search")
            self.assertFalse(n["success"])
            self.assertFalse(n["configured"])
            self.assertIn("NOTION_TOKEN", n["error"])
            s = tools.tool_slack_api("post", "#test", "hi")
            self.assertFalse(s["success"])
            self.assertFalse(s["configured"])

    def test_no_duplicate_tools_in_role_md(self):
        for agent in AGENTS:
            allowed = security_guard.get_allowed_tools(agent)
            # get_allowed_tools set qaytaradi, shuning uchun to'g'ridan fayl o'qiymiz.
            path = os.path.join(security_guard.SUBAGENTS_DIR, agent, "role.md")
            src = open(path, encoding="utf-8").read()
            import re
            m = re.search(r"## Ruxsat etilgan toollar(.*?)(?=\n## |\Z)", src, re.S)
            names = re.findall(r"^[-*]\s*`?([a-zA-Z0-9_\-]+)`?", m.group(1), re.M)
            self.assertEqual(len(names), len(set(names)), f"{agent}: takrorlangan tool'lar")


if __name__ == "__main__":
    unittest.main()
