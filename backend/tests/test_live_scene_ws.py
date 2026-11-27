"""Jonli sahna (`/ws/task/{task_id}`) — haqiqiy pytest, agent CLI'siz.

Avval bu qamrov `test_live_scene.py` nomli qo'lda skriptda edi: u vazifa
yaratib, agent CLI javobini 180 soniya kutardi. CI'da agent yo'q, shuning
uchun skript umuman ishlamasdi.

Bu yerdagi testlar agent o'rniga `database.update_task_step` bilan holatni
o'zgartiradi — endpoint shartnomasi (snapshot → preview_frame →
task_completed) to'liq tekshiriladi.

REGRESSIYA (2026-11-27): `websocket_task_stream` ichida `receive_text`
timeout'i ikkala yo'lda ham `continue` qilardi, shuning uchun status
tekshiruvi O'LIK KOD edi — mijoz `task_completed` ni hech qachon olmasdi va
test abadiy osilardi. `test_completed_status_closes_the_stream` aynan shu
nuqsonni ushlab turadi.

REGRESSIYA (2026-11-27, ikkinchi): `_task_preview_frame` brauzer holatini
`state().get("open")` bilan tekshirardi, `live_browser` esa kalitni `is_open`
deb saqlaydi. Natijada brauzer kadri BIR MARTA HAM olinmagan.
`test_browser_state_key_matches_live_browser` shu nomuvofiqlikni ushlaydi.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database  # noqa: E402

TASK_ID = "test_live_scene_contract"


def _cleanup(task_id: str) -> None:
    conn = database.get_connection()
    try:
        conn.execute("DELETE FROM logs WHERE task_id = ?", (task_id,))
        conn.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
        conn.commit()
    finally:
        conn.close()


class _ReceiveTimeout(Exception):
    """WS javobi kutish vaqtida kelmadi."""


def _receive_with_timeout(ws, timeout: float = 10.0):
    """`ws.receive_json()` ni qattiq vaqt chegarasi bilan bajaradi.

    TestClient sinxron API: `receive_json` javob kelmasa ABADIY bloklanadi va
    pytest yig'ilishi osilib qoladi (CI'da 6 soatlik timeout). Bu helper
    javobni alohida oqimda kutadi va `None` qaytaradi — test yiqiladi,
    osilib qolmaydi.
    """
    result: dict = {}

    def worker() -> None:
        try:
            result["msg"] = ws.receive_json()
        except _ReceiveTimeout:
            pass
        except Exception as exc:  # noqa: BLE001
            result["error"] = exc

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        return None
    if "error" in result:
        raise result["error"]
    return result.get("msg")


@pytest.fixture
def fresh_task():
    """Toza vazifa qatori: 'working' holatda yaratiladi, oxirida o'chiriladi."""
    _cleanup(TASK_ID)
    database.create_task(TASK_ID, "live scene sinovi", "jonli sahna", "scout")
    yield TASK_ID
    _cleanup(TASK_ID)


@pytest.fixture
def client():
    """Har test uchun yangi TestClient.

    Ilgari module-scope edi va testlar osilib qolardi: TestClient o'z event
    loop'ini saqlaydi, oldingi testning `websocket_connect` konteksti
    yopilgach keyingi ulanish javob kutib qoladi. Har testga yangi mijoz
    berish bu holatni butunlay yo'q qiladi.
    """
    from fastapi.testclient import TestClient

    import main

    return TestClient(main.app)


@pytest.fixture(autouse=True)
def _guard_against_browser_frames(monkeypatch):
    """Preview kadr uchun HAQIQIY brauzer ochilmasin.

    `_task_preview_frame` birinchi navbatda `live_browser` ni tekshiradi.
    CI'da playright brauzeri o'rnatilmagan bo'lsa `frame()` 30 soniya
    kutishi mumkin va butun job osiladi. Bu fixture holatni "yopiq" deb
    qotiradi — testlar faqat artefakt yo'lini tekshiradi.
    """
    try:
        import live_browser

        monkeypatch.setattr(live_browser, "state", lambda: {"is_open": False})
    except ImportError:
        pass


def _flip_status_later(task_id: str, status: str, delay: float = 1.0) -> threading.Thread:
    def worker() -> None:
        time.sleep(delay)
        database.update_task_step(
            task_id, "checker", status, output="test", evidence="test dalil"
        )

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return thread


def test_connect_sends_snapshot_with_task_and_logs(client, fresh_task):
    """Ulanish darhol `snapshot` yuboradi — vazifa va loglar bilan."""
    database.add_log(fresh_task, "scout", "INFO", "birinchi log")

    with client.websocket_connect(f"/ws/task/{fresh_task}") as ws:
        msg = _receive_with_timeout(ws)

    assert msg is not None, "snapshot olinmadi (timeout)"
    assert msg["type"] == "snapshot"
    assert msg["task_id"] == fresh_task
    assert msg["task"]["task_id"] == fresh_task
    assert msg["task"]["status"] == "working"
    assert isinstance(msg["logs"], list)
    assert any("birinchi log" in (l.get("message") or "") for l in msg["logs"])


def test_unknown_task_reports_error_and_closes(client):
    """Mavjud bo'lmagan vazifa: `error` xabari, keyin yopiladi (osilmaydi)."""
    with client.websocket_connect("/ws/task/yoq_bunday_task_xyz") as ws:
        msg = _receive_with_timeout(ws)
        assert msg is not None, "error xabari olinmadi (timeout)"
        assert msg["type"] == "error"
        assert "topilmadi" in msg["message"].lower()


def test_completed_status_closes_the_stream(client, fresh_task):
    """PASS holatiga o'tish `task_completed` yuboradi va oqimni yopadi.

    Bu test 2026-11-27 regressiyasini ushlaydi: status tekshiruvi o'lik kod
    bo'lsa, `receive_json` hech qachon qaytmaydi (CI'da timeout).
    """
    flip = _flip_status_later(fresh_task, "PASS", delay=1.0)

    received: list[dict] = []
    with client.websocket_connect(f"/ws/task/{fresh_task}") as ws:
        received.append(_receive_with_timeout(ws))  # snapshot
        received.append(_receive_with_timeout(ws))  # task_completed

    flip.join(timeout=5)

    assert None not in received, (
        "WS xabari kelmadi (timeout) — status tekshiruvi o'lik kod bo'lishi mumkin: "
        "`websocket_task_stream` `receive_text` timeout'idan keyin `continue` qilsa, "
        "`task_completed` hech qachon yuborilmaydi."
    )
    types = [m["type"] for m in received]
    assert types[0] == "snapshot"
    assert "task_completed" in types, f"task_completed kelmadi: {types}"

    done = next(m for m in received if m["type"] == "task_completed")
    assert done["status"] == "PASS"
    assert done["task_id"] == fresh_task
    # Frontend shu maydonlarga tayanadi (ovoz/bildirishnoma).
    assert done["target_agent"] == "scout"
    assert done["evidence"] == "test dalil"
    assert "step_durations" in done


@pytest.mark.parametrize("final_status", ["FAIL", "BLOCKED"])
def test_other_terminal_statuses_also_complete(client, final_status):
    """FAIL va BLOCKED ham yakuniy holat — oqim yopilishi shart."""
    _cleanup(TASK_ID)
    database.create_task(TASK_ID, "terminal holat", "sinov", "scout")
    try:
        flip = _flip_status_later(TASK_ID, final_status, delay=1.0)
        with client.websocket_connect(f"/ws/task/{TASK_ID}") as ws:
            _receive_with_timeout(ws)  # snapshot
            done = _receive_with_timeout(ws)
        flip.join(timeout=5)

        assert done is not None, "task_completed kelmadi (timeout)"
        assert done["type"] == "task_completed"
        assert done["status"] == final_status
    finally:
        _cleanup(TASK_ID)


def test_ping_gets_pong_without_closing(client, fresh_task):
    """`ping` → `pong`; oqim ochiq qoladi (heartbeat shartnomasi)."""
    with client.websocket_connect(f"/ws/task/{fresh_task}") as ws:
        _receive_with_timeout(ws)  # snapshot
        ws.send_text("ping")
        reply = ws.receive_text()
        assert reply == "pong"
        # Oqim hali tirik: yana ping yuborish mumkin.
        ws.send_text("ping")
        assert ws.receive_text() == "pong"


def test_running_task_emits_preview_frame_from_workspace_image(client, fresh_task):
    """Ishlayotgan vazifa workspace'idagi yangi rasmni preview kadr qilib yuboradi."""
    import workspace_manager

    ws_dir = workspace_manager.get_agent_workspace("scout")
    os.makedirs(ws_dir, exist_ok=True)
    image_path = os.path.join(ws_dir, "live_scene_probe.png")
    # Haqiqiy 8x8 PNG — to'liq, PIL o'qiy oladigan baytlar. Qo'lda yozilgan
    # minimal sarlavha "broken data stream" beradi (IDAT noto'g'ri).
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000080000000808020000004b6d29dc"
        "0000001449444154789c6314a938c1800d3061151db412000d5b016449fc729d"
        "0000000049454e44ae426082"
    )
    with open(image_path, "wb") as f:
        f.write(png)
    try:
        # `_task_preview_frame` yarim yozilgan fayllarni (mtime < 0.6s)
        # o'tkazib yuboradi — progressiv render himoyasi. Test shuni kutishi
        # shart, aks holda kadr kelmaydi va receive abadiy osiladi.
        time.sleep(0.8)

        with client.websocket_connect(f"/ws/task/{fresh_task}") as ws:
            _receive_with_timeout(ws)  # snapshot
            msg = _receive_with_timeout(ws)

        assert msg is not None, "preview_frame olinmadi (timeout)"
        assert msg["type"] == "preview_frame", f"kutilgan preview_frame, olindi: {msg['type']}"
        assert msg["frame"]["source"] == "artifact"
        assert msg["frame"]["data"].startswith("data:image/")
    finally:
        try:
            os.remove(image_path)
        except OSError:
            pass


def test_browser_state_key_matches_live_browser():
    """`_task_preview_frame` `live_browser.state()` kalitini to'g'ri o'qiydi.

    Regressiya: kod `state().get("open")` so'rardi, `live_browser._state` esa
    `is_open` kalitini saqlaydi — shart hech qachon bajarilmasdi va brauzer
    kadri olinmasdi. Kalit nomi o'zgarsa, bu test darhol yiqiladi.
    """
    import inspect

    import live_browser
    import main

    state_keys = set(live_browser.state().keys())
    assert "is_open" in state_keys, (
        f"live_browser.state() kalitlari o'zgardi: {sorted(state_keys)}. "
        "`_task_preview_frame` shu kalitga tayanadi."
    )

    src = inspect.getsource(main._task_preview_frame)
    assert 'get("is_open")' in src, (
        "_task_preview_frame brauzer holatini `is_open` bilan tekshirishi shart"
    )
    assert 'get("open")' not in src, (
        "_task_preview_frame yana mavjud bo'lmagan `open` kalitini so'rayapti — "
        "brauzer kadri hech qachon olinmaydi"
    )
