import os
import sys
import pytest
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

def test_figma_adapter_info():
    info = app_adapter.get_figma_project_info("leWEA7AyECgzcIk4aeDx8p")
    assert info["success"] is True
    assert "tokens" in info
    assert "primary_color" in info["tokens"]
    assert "components" in info
    assert len(info["components"]) > 0

def test_tools_py_faza4_commands():
    # 1. Blender headless
    shot = tools.tool_blender_headless("import bpy\n", "cli_test_model")
    assert shot["success"] is True
    assert os.path.exists(shot["output_render"])

    # 2. runScript
    s_res = tools.tool_run_script("sculptor", "cli_script.py", "print('CLI Tool OK')")
    assert s_res["success"] is True
    assert "CLI Tool OK" in s_res["stdout"]

    # 3. figma_sync
    f_res = tools.tool_figma_sync()
    assert f_res["success"] is True
    assert "tokens" in f_res

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

    # GET /api/figma/file/...
    r3 = client.get("/api/figma/file/leWEA7AyECgzcIk4aeDx8p")
    assert r3.status_code == 200
    assert r3.json()["success"] is True

def test_sculptor_subagent_active_and_permissions():
    tools_sculptor = security_guard.get_allowed_tools("sculptor")
    assert "blender_headless_exec" in tools_sculptor
    assert "runscript" in tools_sculptor
    assert security_guard.verify_tool_access("sculptor", "blender_headless_exec") is True
