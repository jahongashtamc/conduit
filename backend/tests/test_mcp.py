import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
import mcp_server
from providers.base import MCPAgentProvider

client = TestClient(app)

def test_mcp_list_subagents():
    agents = mcp_server.list_subagents()
    assert isinstance(agents, list)
    assert len(agents) >= 7
    ids = [a["id"] for a in agents]
    assert "scout" in ids
    assert "inspector" in ids
    scout = next(a for a in agents if a["id"] == "scout")
    assert "screenshot" in scout["allowed_tools"]
    assert "interact_web" in scout["allowed_tools"]

def test_mcp_get_subagent_role():
    role_info = mcp_server.get_subagent_role("scout")
    assert role_info["subagent"] == "scout"
    assert "screenshot" in role_info["allowed_tools"]
    assert "interact_web" in role_info["allowed_tools"]
    assert "Scout" in role_info["role_md"]

def test_mcp_run_and_get_task():
    # 1. Dispatch task via MCP tool
    result = mcp_server.run_task("scout", "MCP orqali saytni och va skrinshot ol")
    assert "task_id" in result
    assert result["subagent"] == "scout"
    assert result["status"] == "working"
    task_id = result["task_id"]

    # 2. Get task status via MCP tool
    task_data = mcp_server.get_task(task_id)
    assert task_data["task_id"] == task_id
    assert task_data["subagent"] == "scout"
    assert "steps" in task_data
    assert "logs" in task_data

def test_mcp_agent_provider_interface():
    provider = MCPAgentProvider(agent_name="Antigravity Test Agent")
    assert provider.get_provider_name() == "mcp"
    assert provider.is_connected() is True
    info = provider.get_info()
    assert info["agent_name"] == "Antigravity Test Agent"
    assert "MCP v2.0" in info["protocol"]

def test_agent_status_endpoint():
    res = client.get("/api/agent/status")
    assert res.status_code == 200
    data = res.json()
    assert "is_connected" in data
    assert "agent_name" in data
    assert "mcp_config_sample" in data
