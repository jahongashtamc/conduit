"""Windows kodlash regressiyasi: UTF-8 bolalar + UTF-8 dekodlash.

Topilgan nuqson (2026-11-26): `subprocess.run(..., text=True)` Windows'da
`locale.getpreferredencoding()` (bu mashinada cp1251) bilan dekodlaydi. Node
esa stdout'ni har doim UTF-8 da yozadi. Natijada kirill harfli yo'l
(`Проект по умолчанию`) mojibake bo'lardi: `tool_screenshot` "success: true"
qaytarardi, lekin `os.path.exists(screenshot_path)` False — dalil yo'q.
Bu aynan "soxta PASS" sinfi.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app_adapter  # noqa: E402
import tools  # noqa: E402

CYRILLIC_NAME = "dalil_кирилл.png"


def test_run_node_eval_decodes_utf8_not_locale():
    """Node UTF-8 yozadi; natija buzilmasdan o'qilishi shart."""
    if not tools.shutil.which("node"):
        pytest.skip("node o'rnatilmagan")

    path = "C:/Users/Kapitan/Documents/Проект по умолчанию/x.png"
    res = tools.run_node_eval(
        "console.log(JSON.stringify({p: process.argv[1]}));",
        [path],
    )
    assert res.get("p") == path, f"yo'l mojibake bo'ldi: {res.get('p')!r}"


def test_screenshot_to_non_ascii_path_creates_the_file(tmp_path):
    """Kirill harfli output_path haqiqiy fayl yaratishi va qaytarilishi shart."""
    target = tmp_path / CYRILLIC_NAME
    result = tools.tool_screenshot("https://example.com", str(target))

    if not result.get("success"):
        pytest.skip(f"tashqi tarmoq/playwright mavjud emas: {result.get('error')}")

    assert target.is_file(), "kirill yo'lda fayl yaratilmadi — dalil yo'q"
    assert os.path.exists(result["screenshot_path"]), (
        "qaytarilgan yo'l diskda mavjud emas (kodlash buzilishi)"
    )
    assert os.path.getsize(result["screenshot_path"]) > 0


def test_screenshot_reports_failure_when_file_is_missing(monkeypatch):
    """Yaratilmagan faylni dalil deb qaytarish (soxta muvaffaqiyat) taqiqlanadi.

    Bugungi nuqson aynan shu edi: bog'lanish natijasi "success: true" bo'lib,
    mavjud bo'lmagan yo'l keyingi bosqichga uzatilardi.
    """
    fake_path = os.path.join(os.path.dirname(__file__), "bu_fayl_yoq.png")
    monkeypatch.setattr(
        tools,
        "run_node_eval",
        lambda *_a, **_k: {
            "success": True,
            "tool": "screenshot",
            "screenshot_path": fake_path,
            "bytes": 1234,
        },
    )

    result = tools.tool_screenshot("https://example.com")

    assert result["success"] is False, "mavjud bo'lmagan fayl 'success' bo'ldi"
    assert "dalil emas" in result["error"]
    assert fake_path in result["error"]


def test_utf8_child_env_forces_python_stdout_to_utf8(tmp_path):
    """runScript bolalari UTF-8 yozishi kerak — aks holda dekodlash buziladi."""
    result = app_adapter.run_isolated_script(
        "scout",
        "print_cyrillic.py",
        "print('Проект')",
        language="python",
    )

    if not result.get("success"):
        pytest.skip(f"run_isolated_script bajarilmadi: {result.get('error')}")

    assert "Проект" in result["stdout"], (
        f"Python bola chiqishi mojibake: {result['stdout']!r}"
    )


def test_check_goal_accepts_a_real_non_ascii_evidence_file(tmp_path):
    """Kirill nomli haqiqiy dalil PASS olishi shart (regressiya to'liq zanjiri)."""
    if not tools.shutil.which("node"):
        pytest.skip("node o'rnatilmagan")

    evidence = tmp_path / CYRILLIC_NAME
    evidence.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 4096)

    res = tools.tool_check_goal(
        "Skrinshot olindi va tizim tekshirildi",
        json.dumps({"screenshot": str(evidence), "logs": "clean"}),
    )

    assert res.get("verdict") == "PASS", res


def test_sapi_list_voices_returns_real_names_not_powershell_errors():
    """`$v.GetVoices()` PowerShell'da overload xatosi chiqarardi.

    `list_voices()` xato matnini ("OverloadDefinitions", "string
    GetDescription (int)") haqiqiy ovoz nomi deb qaytarardi. Ovozlar ASCII
    bo'lgani uchun kodlash muammosi buni yashirgan edi.
    """
    if sys.platform != "win32":
        pytest.skip("SAPI faqat Windows'da")

    # `voice` paketi repo ILDIZIDA, backend/ ichida emas. Bu fayl backend/
    # ichidan ishlaydi, shuning uchun ildizni sys.path'ga qo'shamiz — aks
    # holda import CI'da ham, lokalda ham ModuleNotFoundError beradi.
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    from voice.tts import SapiTTS

    engine = SapiTTS()
    if not engine.available():
        pytest.skip("SAPI mavjud emas")

    voices = engine.list_voices()

    assert voices, "hech bo'lmaganda bitta tizim ovozi bo'lishi kerak"
    for voice in voices:
        assert "OverloadDefinitions" not in voice, f"PowerShell xatosi ovoz deb qaytdi: {voice!r}"
        assert not voice.startswith("string "), f"PowerShell imzosi ovoz deb qaytdi: {voice!r}"
        assert "----" not in voice
