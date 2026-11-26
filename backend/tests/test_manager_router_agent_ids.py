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
