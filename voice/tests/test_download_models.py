"""Model yuklash skripti (`voice/download_models.py`) shartnomasi.

Nega kerak: `voice/models/*/onnx/model.onnx` (114 MB × 2) git'da
saqlanmaydi. Toza checkout'da `voice_speak` ishlamaydi va foydalanuvchi
qayerdan olishni bilmaydi. Skript manbani registrdan o'qib, sha256 bilan
tekshirib yuklaydi — bu testlar uning mantiqini qo'riqlaydi.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys

import pytest

VOICE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(VOICE_DIR)
sys.path.insert(0, REPO_ROOT)

_SCRIPT = os.path.join(VOICE_DIR, "download_models.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("download_models", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def dl():
    return _load_module()


def test_script_exists_and_has_main(dl):
    assert os.path.isfile(_SCRIPT)
    assert callable(dl.main)


def test_registry_has_source_and_hashes_for_every_file(dl):
    """Har model uchun manba va har fayl uchun sha256 bo'lishi shart."""
    registry = dl.load_registry()
    models = registry.get("models") or []
    assert models, "registrda model yo'q"

    for model in models:
        assert model.get("source"), f"{model.get('id')}: `source` yo'q"
        assert model.get("dir"), f"{model.get('id')}: `dir` yo'q"
        files = model.get("files") or {}
        assert files, f"{model.get('id')}: `files` bo'sh"
        for relative, expected in files.items():
            assert len(expected) == 64, (
                f"{model.get('id')}/{relative}: sha256 64 belgi bo'lishi kerak"
            )


def test_huggingface_url_is_built_correctly(dl):
    url = dl.huggingface_url("https://huggingface.co/user/repo", "onnx/model.onnx")
    assert url == "https://huggingface.co/user/repo/resolve/main/onnx/model.onnx"


def test_unknown_source_is_rejected(dl):
    """HuggingFace'dan boshqa manba jimgina qabul qilinmasin."""
    with pytest.raises(SystemExit) as exc:
        dl.huggingface_url("https://evil.example.com/payload", "model.onnx")
    assert "huggingface" in str(exc.value).lower()


def test_crlf_normalized_hash_matches_registry(dl):
    """Windows CRLF checkout'da ham registrdagi hash mos kelishi shart.

    `core.autocrlf=true` JSON fayllarni CRLF qiladi; registrdagi sha256 esa
    LF uchun hisoblangan. Normalizatsiya bo'lmasa `--check` oltita faylni
    xato deb ko'rsatadi (o'lchangan, 2026-11-27).
    """
    registry = dl.load_registry()
    checked = 0
    for model in registry.get("models") or []:
        model_dir = os.path.join(VOICE_DIR, model.get("dir", ""))
        for relative, expected in (model.get("files") or {}).items():
            if not relative.endswith(".json"):
                continue
            path = os.path.join(model_dir, relative)
            if not os.path.isfile(path):
                continue  # CI'da modellar yo'q — bu test faqat joyidagilarni tekshiradi
            ok, note = dl.file_state(dl.Path(path), expected)
            assert ok, f"{model.get('id')}/{relative}: {note}"
            checked += 1
    if checked == 0:
        pytest.skip("model fayllari yuklanmagan (CI)")


def test_missing_file_reports_not_ok(dl, tmp_path):
    ok, note = dl.file_state(tmp_path / "yoq.json", "a" * 64)
    assert ok is False
    assert note == "yo'q"


def test_empty_file_is_rejected(dl, tmp_path):
    empty = tmp_path / "empty.json"
    empty.write_bytes(b"")
    ok, note = dl.file_state(empty, "a" * 64)
    assert ok is False
    assert "bo'sh" in note


def test_wrong_hash_is_rejected(dl, tmp_path):
    wrong = tmp_path / "wrong.json"
    wrong.write_text('{"a": 1}', encoding="utf-8")
    ok, note = dl.file_state(wrong, "0" * 64)
    assert ok is False
    assert "MOS EMAS" in note


def test_text_hash_equals_cli_doctor_normalization(dl, tmp_path):
    """Skript va `voice_doctor` bir xil normalizatsiyani ishlatishi shart."""
    from voice import doctor as doctor_module

    sample = tmp_path / "sample.json"
    sample.write_bytes(b'{"a": 1}\r\n{"b": 2}\r\n')

    expected_normalized = hashlib.sha256(
        b'{"a": 1}\n{"b": 2}\n'
    ).hexdigest()

    ok, _ = dl.file_state(sample, expected_normalized)
    assert ok, "download_models CRLF normalizatsiyasi ishlamadi"

    # doctor ham xuddi shunday hisoblashi kerak
    doctor_hash = doctor_module._sha256_text_normalized(doctor_module.Path(sample))
    assert doctor_hash == expected_normalized, (
        "voice_doctor va download_models turli hash hisoblaydi — ular izchil bo'lishi shart"
    )
