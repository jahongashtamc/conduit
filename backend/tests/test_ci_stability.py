"""CI barqarorligi: osilib qolish va baza to'qnashuvi regressiyalari.

Ikkala nuqson ham 2026-11-27 da o'lchandi (CI run 45984826851): Windows job
to'liq to'plamda 13.5 daqiqa jim qoldi, keyin 24% da `F` + 24 ta `E` va
GitHub jobni o'ldirdi. Bir xil kod oldingi run'da 65 soniyada o'tgan edi —
ya'ni sabab kod emas, chegaralanmagan kutish va baza to'qnashuvi.

Bu fayl ikkala ildiz sababni ushlab turadi.
"""
from __future__ import annotations

import configparser
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_every_test_has_a_hard_timeout():
    """`pytest.ini` da global timeout bo'lishi shart.

    Busiz bitta osilgan test butun CI job'ini GitHub'ning 6 soatlik
    chegarasigacha ushlab turadi — bu aynan sodir bo'lgan.
    """
    ini_path = os.path.join(os.path.dirname(__file__), "..", "pytest.ini")
    assert os.path.isfile(ini_path), "backend/pytest.ini yo'q"

    cfg = configparser.ConfigParser()
    cfg.read(ini_path, encoding="utf-8")
    raw = cfg.get("pytest", "timeout", fallback="")
    assert raw.strip(), "pytest.ini da `timeout` berilmagan"

    value = float(raw)
    assert 5 <= value <= 600, f"timeout chegarasi shubhali: {value}"


def test_timeout_plugin_is_declared_in_requirements():
    """CI `pip install -r requirements.txt` qiladi — plugin o'sha yerda bo'lsin."""
    req = os.path.join(os.path.dirname(__file__), "..", "requirements.txt")
    text = open(req, encoding="utf-8").read().lower()
    assert "pytest-timeout" in text, (
        "pytest-timeout requirements.txt da yo'q — CI'da timeout sozlamasi "
        "jimgina e'tiborsiz qoladi (`unknown option: --timeout`)"
    )


def test_deepsearch_has_a_total_search_deadline():
    """Butun qidiruv `asyncio.wait_for` bilan chegaralangan bo'lishi shart.

    Avval `asyncio.gather` umumiy deadline'siz edi: bitta manba DNS/connect
    bosqichida osilsa, butun pipeline cheksiz kutardi.
    """
    import inspect

    from engine import deepsearch

    src = inspect.getsource(deepsearch.DeepSearchEngine.search_candidates_for_topic)
    assert "asyncio.wait_for" in src, (
        "search_candidates_for_topic umumiy deadline'siz — manba osilsa "
        "pipeline cheksiz kutadi"
    )
    assert deepsearch.SEARCH_DEADLINE > 0
    # Fazalar ajratilgan bo'lishi shart: connect 5s, read 12s.
    timeout = deepsearch.TIMEOUT
    assert isinstance(timeout, __import__("httpx").Timeout), (
        "TIMEOUT oddiy son — connect/read fazalari ajratilmagan"
    )


def test_live_backend_uses_its_own_database(live_backend):
    """Test-server alohida baza faylida ishlaydi (lock bo'lmasin).

    Avval test jarayoni va uvicorn bir xil `conduit.db` ga yozardi; Windows'da
    bu `database is locked` berib, keyingi 24 ta testni ERROR qilardi.
    """
    import database

    assert hasattr(live_backend, "db_path"), "live_backend.db_path yo'q"
    assert live_backend.db_path != database.DB_PATH, (
        "test-server asosiy baza bilan bir xil faylda ishlayapti — "
        "Windows'da lock beradi"
    )
    assert os.path.isfile(live_backend.db_path), (
        f"server bazasi yaratilmagan: {live_backend.db_path}"
    )


def test_database_path_is_configurable():
    """`CONDUIT_DB_PATH` muhit o'zgaruvchisi yo'lni almashtira oladi."""
    import importlib

    import database

    original = database.DB_PATH
    custom = os.path.join(os.path.dirname(__file__), "..", "..", "_probe_db_path.db")
    os.environ["CONDUIT_DB_PATH"] = custom
    try:
        reloaded = importlib.reload(database)
        assert os.path.abspath(reloaded.DB_PATH) == os.path.abspath(custom)
    finally:
        os.environ.pop("CONDUIT_DB_PATH", None)
        importlib.reload(database)
        assert database.DB_PATH == original, "DB_PATH tiklanmadi"


def test_server_health_endpoint_is_reachable(live_backend):
    """Fixture haqiqatan tirik server beradi (skip emas, PASS)."""
    import json
    import urllib.request

    with urllib.request.urlopen(f"{live_backend}/api/health", timeout=10) as resp:
        payload = json.load(resp)
    assert payload["status"] == "ok"


def test_module_runner_script_exists_and_is_runnable():
    """CI modul-bo'yicha yurgizish skriptiga tayanadi — u mavjud bo'lsin.

    Nega: bitta jarayonda yurgizilganda bitta osilgan test butun job'ni
    30 daqiqagacha ushlab turadi (o'lchangan: run 46009755859).
    """
    import subprocess

    script = os.path.join(os.path.dirname(__file__), "..", "scripts", "run_tests_by_module.py")
    assert os.path.isfile(script), f"skript yo'q: {script}"

    proc = subprocess.run(
        [sys.executable, script, "--help"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr[-400:]
    assert "--timeout" in proc.stdout


def test_ci_workflow_uses_the_module_runner():
    """CI to'liq to'plamni modul bo'yicha yurgizishi shart."""
    workflow = os.path.join(
        os.path.dirname(__file__), "..", "..", ".github", "workflows", "ci.yml"
    )
    text = open(workflow, encoding="utf-8").read()
    assert "run_tests_by_module.py" in text, (
        "CI hali ham `pytest -q` bilan bitta jarayonda yurgizadi — bitta "
        "osilgan test butun job'ni bloklaydi"
    )
