import pytest
import os
import sys
import uuid
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import database
import workspace_manager
from engine.kernel import ConduitKernel, KernelMode

@pytest.fixture(autouse=True)
def setup_test_db():
    database.init_db()
    yield

def test_sentinel_subagent_registered_and_configured():
    """Sentinel subagenti to'liq mavjud va faol ekanligini tekshirish."""
    subagents_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../subagents"))
    sentinel_dir = os.path.join(subagents_dir, "sentinel")
    assert os.path.isdir(sentinel_dir), "Sentinel papkasi mavjud emas"
    assert os.path.isfile(os.path.join(sentinel_dir, "role.md")), "role.md mavjud emas"
    assert os.path.isfile(os.path.join(sentinel_dir, "app.json")), "app.json mavjud emas"
    assert os.path.isdir(os.path.join(sentinel_dir, "inner")), "inner papkasi mavjud emas"
    assert os.path.isfile(os.path.join(sentinel_dir, "inner", "planner.md")), "planner.md mavjud emas"
    assert os.path.isfile(os.path.join(sentinel_dir, "inner", "doer.md")), "doer.md mavjud emas"
    assert os.path.isfile(os.path.join(sentinel_dir, "inner", "checker.md")), "checker.md mavjud emas"

def test_all_11_subagents_have_active_status():
    """Barcha 11 subagent (Scout, Sculptor, Inspector, Designer, Animator, Editor, Painter, Notion, Slack, SuperAgent, Sentinel) faol ekanini tekshirish."""
    import subagent_scanner
    all_subs = subagent_scanner.scan_subagents()
    sub_ids = [s["id"] for s in all_subs]
    expected_subs = [
        "scout", "sculptor", "inspector", "designer", "animator",
        "editor", "painter", "notion", "slack", "superagent", "sentinel"
    ]
    for exp in expected_subs:
        assert exp in sub_ids, f"{exp} subagenti topilmadi"
        sub_obj = next(s for s in all_subs if s["id"] == exp)
        assert sub_obj["status"] == "active", f"{exp} subagenti statusi faol emas"

@pytest.mark.anyio
async def test_deepsearch_citations():
    """DeepSearch lokal kod va xotiradan tegishli faktlarni topib iqtibos (citation) hosil qilishi."""
    kernel = ConduitKernel()
    task_id = f"test_ds_{uuid.uuid4().hex[:6]}"
    database.create_task(task_id, "DeepSearch test", "Murakkab MVP arxitekturasi va xavfsizlik", "superagent")
    
    citations = await kernel.run_deepsearch(task_id, "Clean Architecture va Sentinel")
    assert len(citations) >= 2, "Kamida 2 ta iqtibos topilishi kerak"
    assert all("source_title" in c and "relevance_score" in c for c in citations)
    
    # DB dan o'qish
    db_cits = database.get_deepsearch_citations(task_id)
    assert len(db_cits) == len(citations)

@pytest.mark.anyio
async def test_deep_thinking_reasoning_steps():
    """Uzoq muddatli fikrlash (Extended Reasoning) 4 ta kognitiv bosqichni bajarishi."""
    kernel = ConduitKernel()
    task_id = f"test_dt_{uuid.uuid4().hex[:6]}"
    database.create_task(task_id, "DeepThinking test", "Katta Fintech MVP tizimini loyihalash", "superagent")
    
    thoughts = await kernel.run_deep_thinking(task_id, "Katta Fintech MVP tizimini loyihalash", "context")
    assert len(thoughts) == 4, "4 ta fikrlash qadami bo'lishi kerak"
    perspectives = [t["perspective"] for t in thoughts]
    assert "problem_framing" in perspectives
    assert "architecture" in perspectives
    assert "security_audit" in perspectives
    assert "mvp_synthesis" in perspectives

@pytest.mark.anyio
async def test_mvp_scaffold_blueprint():
    """Murakkab loyihani to'liq MVP darajasiga ko'tarish spetsifikatsiyasi generatsiyasi."""
    kernel = ConduitKernel()
    task_id = f"test_mvp_{uuid.uuid4().hex[:6]}"
    database.create_task(task_id, "MVP Scaffold test", "SaaS AI Video Generator MVP", "superagent")
    
    blueprint = await kernel.scaffold_mvp(task_id, "SaaS AI Video Generator MVP", "ai_video_mvp")
    assert blueprint["project_name"] == "ai_video_mvp"
    assert "frontend_spec" in blueprint
    assert "backend_spec" in blueprint
    assert "database_spec" in blueprint
    assert "security_spec" in blueprint
    
    # DB dan o'qish
    db_bp = database.get_mvp_blueprint(task_id)
    assert db_bp is not None
    assert db_bp["project_name"] == "ai_video_mvp"

@pytest.mark.anyio
async def test_sentinel_stress_test_execution():
    """Sentinel subagenti orqali yaratilgan kodni xavfsizlik va buzilishlarga sinash."""
    kernel = ConduitKernel()
    task_id = f"test_sentinel_{uuid.uuid4().hex[:6]}"
    database.create_task(task_id, "Sentinel Stress Test", "Tekshiruv", "sentinel")
    
    report = await kernel.run_sentinel_stress_test(
        task_id=task_id,
        target_workspace=workspace_manager.get_agent_workspace("superagent"),
        prompt="Tekshiruv"
    )
    assert "audit_passed" in report
    assert "security_score" in report
    assert report["security_score"] >= 90
    assert len(report["checked_vectors"]) >= 4

from unittest.mock import patch

@pytest.mark.anyio
async def test_deepx_full_pipeline_dispatch():
    """DeepX to'liq rejimida task dispatch qilinganda barcha bosqichlar (Search, Think, Scaffold, Swarm, Sentinel) ishlashi."""
    kernel = ConduitKernel()
    task_id = f"test_full_deepx_{uuid.uuid4().hex[:6]}"
    database.create_task(task_id, "Full DeepX MVP Mission", "To'liq 3D E-Commerce Platforma MVP", "superagent", execution_mode="deepx")
    
    with patch("engine.cli_runner.run_agent_loop") as mock_loop:
        mock_loop.return_value = {
            "status": "PASS",
            "evidence": "Swarm stage completed successfully: artefakt.out",
            "output_artifact": "artefakt.out"
        }
        res = await kernel.dispatch_task(
            task_id=task_id,
            target_agent="superagent",
            prompt="To'liq 3D E-Commerce Platforma MVP",
            mode=KernelMode.DEEPX
        )
    assert res["status"] in ["PASS", "FAIL"]
    assert "citations" in res
    assert "thoughts" in res
    assert "blueprint" in res
    assert "sentinel_audit" in res
    assert res["sentinel_audit"]["audit_passed"] is True
