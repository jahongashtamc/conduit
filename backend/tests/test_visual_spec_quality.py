import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import app_adapter
import tools


def test_parse_visual_spec_reads_user_requirement():
    spec = app_adapter.parse_visual_spec(
        '3 ta qizil shar va ko\'k kub yarat, ustiga "NEXUS" yoz, fon qora'
    )
    assert "#DC2626" in spec["colors"]
    assert "#2563EB" in spec["colors"]
    assert "sphere" in spec["shapes"]
    assert "cube" in spec["shapes"]
    assert spec["count"] == 3
    assert spec["text"] == "NEXUS"
    assert spec["background"] == "#0F172A"


def test_build_scene_script_uses_requirement_values():
    script = app_adapter.build_scene_script_from_goal(
        '2 ta yashil shar, matn "NEXUS", metall'
    )
    assert "sphere" in script
    assert "#16A34A" in script
    assert "NEXUS" in script
    assert "METALLIC = 0.85" in script


def test_gen_image_uses_parsed_spec_not_random_grid(tmp_path):
    out = tmp_path / "requirement.png"
    res = tools.tool_gen_image("3 ta qizil shar", 256, 256, output_path=str(out))
    assert res["success"] is True
    assert res["spec"]["count"] == 3
    assert res["spec"]["shapes"] == ["sphere"]
    assert res["spec"]["colors"] == ["#DC2626"]
    assert os.path.getsize(res["image_path"]) > 1000
