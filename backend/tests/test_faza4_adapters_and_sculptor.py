import os
import sys
import time
from unittest.mock import patch
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import main
import app_adapter
import security_guard
import tools

client = TestClient(main.app)

def test_adapter_app_metadata_and_formats():
    adapters = app_adapter.get_all_adapters_status()
    assert len(adapters) > 0
    blender_adapter = next((a for a in adapters if a["id"] == "blender"), None)
    assert blender_adapter is not None
    assert ".blend" in blender_adapter["supported_formats"]
    assert ".obj" in blender_adapter["supported_formats"]
    assert "{exe}" in blender_adapter["run_template"]

    figma_adapter = next((a for a in adapters if a["id"] == "figma"), None)
    assert figma_adapter is not None
    assert ".fig" in figma_adapter["supported_formats"]

def test_blender_headless_preview_settings():
    script = app_adapter.build_blender_headless_script("import bpy\n")
    assert "cycles.samples = 16" in script
    assert "cycles.use_denoising = True" in script
    assert "resolution_percentage = 50" in script
    with patch.dict(os.environ, {"NEXUS_BLENDER_SAMPLES": "8", "NEXUS_BLENDER_SCALE": "80"}):
        custom = app_adapter.build_blender_headless_script("import bpy\n")
    assert "cycles.samples = 8" in custom
    assert "resolution_percentage = 80" in custom


def test_promote_blender_artifact_replaces_stale_file(tmp_path):
    stale = tmp_path / "render_snapshot.png"
    stale.write_bytes(b"OLD")
    os.utime(stale, (1, 1))
    fresh = tmp_path / "render_snapshot.png0001.png"
    fresh.write_bytes(b"NEW")
    now = time.time()
    os.utime(fresh, (now, now))

    result = app_adapter.promote_blender_artifact(str(stale), now - 1)

    assert result == str(stale.resolve())
    assert stale.read_bytes() == b"NEW"


def test_promote_blender_artifact_rejects_stale_file(tmp_path):
    stale = tmp_path / "render_snapshot.png"
    stale.write_bytes(b"OLD")
    os.utime(stale, (1, 1))

    result = app_adapter.promote_blender_artifact(str(stale), time.time())

    assert result is None
    assert stale.read_bytes() == b"OLD"


def test_blender_headless_execution():
    bpy_code = "import bpy\nbpy.ops.mesh.primitive_cube_add(size=2.0)\n"
    res = app_adapter.execute_blender_headless(bpy_code, model_name="test_cube", output_filename="test_cube_render.png")
    assert res["success"] is True
    assert res["tool"] == "blender_headless_exec"
    assert os.path.exists(res["output_render"])
    assert res["execution_time_seconds"] >= 0
    assert res["web_preview_url"] is not None

def test_run_isolated_script():
    code = "import math\nprint(f'Cube diagonal: {math.sqrt(3):.3f}')\n"
    res = app_adapter.run_isolated_script("sculptor", "diagonal_calc.py", code)
    assert res["success"] is True
    assert res["returncode"] == 0
    assert "Cube diagonal: 1.732" in res["stdout"]
    assert os.path.exists(res["script_path"])

def test_run_isolated_script_security_block():
    bad_code = "import os\nos.system('rmdir /s /q c:\\')"
    res = app_adapter.run_isolated_script("sculptor", "danger.py", bad_code)
    assert res["success"] is False
    assert "Xavfsizlik chegarasi buzildi" in res["error"]

def test_figma_adapter_info_needs_config():
    with patch.dict(os.environ, {"FIGMA_TOKEN": "", "FIGMA_ACCESS_TOKEN": ""}):
        info = app_adapter.get_figma_project_info("realkey123", "Login ekrani ranglari")
    assert info["success"] is False
    assert info["status"] == "needs_config"
    assert "tokens" not in info


def test_figma_adapter_reads_real_rest_data():
    fake = {
        "name": "Login Design",
        "document": {
            "type": "CANVAS", "name": "Login", "children": [{
                "type": "COMPONENT", "name": "PrimaryButton",
                "fills": [{"type": "SOLID", "color": {"r": 0.145, "g": 0.388, "b": 0.922}}],
                "style": {"fontFamily": "Inter"},
            }]
        },
        "components": {"1:2": {"name": "PrimaryButton"}},
    }
    with patch.dict(os.environ, {"FIGMA_TOKEN": "unit-token"}), \
         patch.object(app_adapter, "_figma_get_json", return_value=fake) as mock_get:
        info = app_adapter.get_figma_project_info("realkey123", "Login ekrani ranglari, tugmasi va shrifti")
    assert info["success"] is True
    assert info["file_name"] == "Login Design"
    assert "#2563EB" in info["tokens"]["colors"]
    assert "PrimaryButton" in info["components"]
    assert "Inter" in info["tokens"]["font_families"]
    assert mock_get.call_args.args[0].endswith("/v1/files/realkey123")

def test_tools_py_faza4_commands():
    # 1. Blender headless
    shot = tools.tool_blender_headless("import bpy\n", "cli_test_model")
    assert shot["success"] is True
    assert os.path.exists(shot["output_render"])

    # 2. runScript
    s_res = tools.tool_run_script("sculptor", "cli_script.py", "print('CLI Tool OK')")
    assert s_res["success"] is True
    assert "CLI Tool OK" in s_res["stdout"]

    # 3. figma_sync: haqiqiy token/key bo'lmasa halol needs_config qaytadi
    with patch.dict(os.environ, {"FIGMA_TOKEN": "", "FIGMA_ACCESS_TOKEN": ""}):
        f_res = tools.tool_figma_sync(requirement="Login dizayn")
    assert f_res["success"] is False
    assert f_res["status"] == "needs_config"

def test_adapter_rest_endpoints():
    # GET /api/adapter/apps
    r1 = client.get("/api/adapter/apps")
    assert r1.status_code == 200
    apps_data = r1.json()
    assert isinstance(apps_data, list)
    assert any(a["id"] == "blender" for a in apps_data)

    # POST /api/adapter/blender
    r2 = client.post("/api/adapter/blender", json={"code": "import bpy", "model_name": "api_test_model"})
    assert r2.status_code == 200
    assert r2.json()["success"] is True

    # GET /api/figma/file/... — token bo'lmasa soxta ma'lumot qaytarmaydi
    with patch.dict(os.environ, {"FIGMA_TOKEN": "", "FIGMA_ACCESS_TOKEN": ""}):
        r3 = client.get("/api/figma/file/realkey123")
    assert r3.status_code == 200
    assert r3.json()["success"] is False
    assert r3.json()["status"] == "needs_config"

def test_sculptor_subagent_active_and_permissions():
    tools_sculptor = security_guard.get_allowed_tools("sculptor")
    assert "blender_headless_exec" in tools_sculptor
    assert "runscript" in tools_sculptor
    assert security_guard.verify_tool_access("sculptor", "blender_headless_exec") is True
