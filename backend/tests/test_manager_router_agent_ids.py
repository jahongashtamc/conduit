"""Manager agent ID validatsiyasi: yangi subagent darrov ko'rinishi kerak.

Ildiz sabab: `known_agent_ids` @lru_cache bilan keshlangandi. Backend ishga
tushgandan keyin qo'shilgan `voice` papkasi "noma'lum subagent" xatosini berdi.
"""

from __future__ import annotations

import json
import os
import sys

# Boshqa testlar kabi backend/ ichidan ishga tushiriladi (CI `working-directory:
# backend`), shuning uchun paket yo'li (`backend.manager_router`) emas — modul
# yo'li ishlatiladi. Aks holda pytest collection bosqichida yiqiladi va BUTUN
# to'plam bajarilmay qoladi.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import manager_router  # noqa: E402


def test_new_subagent_folder_is_recognized_without_restart(tmp_path, monkeypatch):
    monkeypatch.setattr(manager_router, "_PROJECT_ROOT", str(tmp_path))
    subagents = tmp_path / "subagents"
    (subagents / "voice").mkdir(parents=True)
    (subagents / "voice" / "app.json").write_text(
        json.dumps({"id": "voice", "name": "Voice"}), encoding="utf-8"
    )
    ids = manager_router.known_agent_ids()
    assert "voice" in ids
    assert manager_router.validate_agent_id("voice") == "voice"

    # Ikkinchi chaqiruvda ham yangi papka ko'rinadi (kesh yo'q).
    (subagents / "brand_new_agent").mkdir()
    assert "brand_new_agent" in manager_router.known_agent_ids()


def test_manifest_id_is_used_instead_of_folder_name(tmp_path, monkeypatch):
    monkeypatch.setattr(manager_router, "_PROJECT_ROOT", str(tmp_path))
    folder = tmp_path / "subagents" / "folder_name"
    folder.mkdir(parents=True)
    (folder / "app.json").write_text(
        json.dumps({"id": "custom_id", "name": "Custom"}), encoding="utf-8"
    )
    ids = manager_router.known_agent_ids()
    assert "custom_id" in ids
    assert "folder_name" not in ids


def test_unknown_agent_raises_with_helpful_list(tmp_path, monkeypatch):
    monkeypatch.setattr(manager_router, "_PROJECT_ROOT", str(tmp_path))
    (tmp_path / "subagents").mkdir()
    try:
        manager_router.validate_agent_id("does_not_exist")
    except ValueError as exc:
        assert "Noma'lum subagent" in str(exc)
        assert "Mavjud agentlar" in str(exc)
    else:
        raise AssertionError("Noma'lum agent rad etilmadi")


# --- Instrument (tez yo'l) routing regressiyasi (2026-11-27) ---
# Topilgan nuqson: `inst_*` agentlar router orqali HECH QACHON tanlanmasdi.
# "qizil doira rasm yarat" so'rovi 2-6 daqiqalik `painter` rol-agentiga
# ketardi, holbuki `inst_image` buni 0.6s da bajaradi.

def test_simple_image_request_routes_to_fast_instrument():
    agent, reason = manager_router.route_task("qizil doira 640x480 rasm yarat")
    assert agent == "inst_image", f"kutilgan inst_image, olindi {agent}: {reason}"


def test_blender_request_routes_to_fast_instrument():
    agent, reason = manager_router.route_task("sariq yulduz 3D modelini yaratib render qil")
    assert agent == "inst_blender", f"kutilgan inst_blender, olindi {agent}: {reason}"


def test_video_assembly_routes_to_fast_instrument():
    agent, reason = manager_router.route_task("klip.mp4 dan video montaj qil")
    assert agent == "inst_video", f"kutilgan inst_video, olindi {agent}: {reason}"


def test_web_task_still_routes_to_scout():
    agent, _ = manager_router.route_task("Google qidiruvidan Conduit haqida ma'lumot top")
    assert agent == "scout"


def test_inspector_task_still_routes_to_inspector():
    agent, _ = manager_router.route_task("Tizim testlarini ishga tushir va audit qil")
    assert agent == "inspector"


def test_explicit_agent_overrides_auto_routing():
    agent, reason = manager_router.route_task("rasm yarat", requested_agent="painter")
    assert agent == "painter"
    assert "to'g'ridan-to'g'ri" in reason


def test_image_and_blender_both_mentioned_goes_to_blender():
    """Aralash so'rovda 3D ustun — rasm yo'li noto'g'ri bo'lmasligi kerak."""
    agent, _ = manager_router.route_task("blenderda qizil sharni render qil")
    assert agent == "inst_blender"
