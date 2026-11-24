import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database
import report_generator
from engine import cli_runner, deepx, kernel


def test_swarm_stage_timeout_returns_honest_fail(monkeypatch):
    async def stuck(**kwargs):
        await asyncio.sleep(2)
        return {"status": "PASS", "evidence": "kechikkan PASS"}

    monkeypatch.setattr(kernel, "_swarm_stage_timeout", lambda: 0.05)
    monkeypatch.setattr(cli_runner, "run_agent_loop", stuck)

    started = time.monotonic()
    result = asyncio.run(kernel.ConduitKernel()._run_stage_attempt(
        "test_timeout_task", "inspector", "audit", 1
    ))
    elapsed = time.monotonic() - started

    assert result["status"] == "FAIL"
    assert "tugamadi" in result["evidence"]
    assert elapsed < 1.5, f"bosqich vaqt chegidan oshib ketdi: {elapsed:.2f}s"


def test_deepsearch_mode_and_query_relevance():
    assert kernel.KernelMode.DEEPSEARCH.value == "deepsearch"
    score = kernel.ConduitKernel._candidate_relevance
    good = score("React query", {"name": "react-query", "repo": "tanstack/query", "description": "React data fetching"})
    bad = score("React query", {"name": "@improbable-eng/grpc-web", "repo": "improbable-eng/grpc-web", "description": "gRPC web client", "stars": 9000})
    assert good > bad, (good, bad)


def test_deepsearch_report_is_written(tmp_path, monkeypatch):
    original = deepx.DeepXAnalyzer

    class TmpAnalyzer(original):
        def __init__(self):
            super().__init__(str(tmp_path))

    monkeypatch.setattr(deepx, "DeepXAnalyzer", TmpAnalyzer)
    citations = [{
        "source_title": "react-query",
        "source_uri": "https://github.com/TanStack/query",
        "relevance_score": 0.9,
    }]
    path = kernel.ConduitKernel._write_deepsearch_report("React query", citations)
    assert os.path.isfile(path), path
    content = open(path, encoding="utf-8").read()
    assert "React query" in content
    assert "react-query" in content


def test_report_finds_existing_task_by_string_id():
    task_id = "test_report_four_" + str(int(time.time() * 1000))
    database.create_task(task_id, "Hisobot testi", "Vazifa matni", "scout")
    try:
        md = report_generator.generate_task_markdown_report(task_id)
        assert "topilmadi" not in md.lower()
        assert task_id in md
        assert "Vazifa matni" in md
    finally:
        database.purge_test_tasks((task_id,))
