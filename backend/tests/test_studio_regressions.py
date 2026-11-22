"""Studio poydevori uchun regression testlar (dalil bilan qotirilgan)."""

import hashlib
import json
import os

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def test_workspace_tools_are_stubs():
    """Workspace yaratuvchi har doim to'liq nusxa emas, stub yozishi shart."""
    import workspace_manager

    ws = workspace_manager.get_agent_workspace("inst_image")
    path = os.path.join(ws, "tools.py")
    assert os.path.isfile(path)
    size = os.path.getsize(path)
    assert size < 2000, f"tools.py {size} bayt — dublikat qaytgan"
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    assert "tools.py" in content and "master" in content.lower()


def test_agent_env_does_not_touch_global_config():
    """Izolyatsiyalangan HOME global MCP config'ga tegmasligi shart."""
    import agent_env

    real = os.path.expanduser("~/.gemini/config/mcp_config.json")
    if not os.path.isfile(real):
        return
    before = hashlib.sha256(open(real, "rb").read()).hexdigest()
    env = agent_env.isolated_home(True)
    after = hashlib.sha256(open(real, "rb").read()).hexdigest()
    assert before == after, "Global mcp_config.json o'zgardi"
    assert env["HOME"] and env["USERPROFILE"]
    isolated = os.path.join(env["HOME"], ".gemini", "config", "mcp_config.json")
    with open(isolated, encoding="utf-8") as fh:
        assert json.load(fh) == {"mcpServers": {}}


def test_agents_have_interactive_command():
    """agents.json dagi interaktiv agentlar terminal uchun aniq buyruqqa ega bo'lishi shart."""
    with open(os.path.join(BASE, "agents.json"), encoding="utf-8") as fh:
        agents = json.load(fh)["agents"]
    assert "interactive_command" in agents["agy"]
    assert "--dangerously-skip-permissions" in agents["agy"]["interactive_command"]
    assert agents["agy"].get("isolated_home") is True
