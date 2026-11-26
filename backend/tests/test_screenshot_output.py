"""`tool_screenshot` haqiqiy FAYL yozishi shart — papka emas.

Topilgan nuqson: `output_path` to'g'ridan-to'g'ri Node yordamchisiga berilardi,
u esa ikkinchi argumentni PAPKA deb qabul qiladi. Natijada
`example_screenshot.png/` papkasi yaratilib, ichida haqiqiy rasm qolardi va
`os.path.isfile()` dalili ishlamasdi.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import tools  # noqa: E402


def test_screenshot_writes_a_real_png_file(tmp_path):
    target = tmp_path / "example_screenshot.png"
    result = tools.tool_screenshot("https://example.com", str(target))

    if not result.get("success"):
        pytest.skip(f"tashqi tarmoq/playwright mavjud emas: {result.get('error')}")

    assert target.is_file(), "output_path papka bo'lib qoldi — dalil yo'q"
    assert not target.is_dir()
    assert target.stat().st_size > 1000
    with open(target, "rb") as fh:
        assert fh.read(8) == b"\x89PNG\r\n\x1a\n", "PNG imzosi noto'g'ri"
    assert os.path.abspath(result["screenshot_path"]) == os.path.abspath(str(target))
    assert result["bytes"] == target.stat().st_size


def test_screenshot_rejects_the_dashboard_itself():
    """O'z dashboardini skrinshot qilish taqiqlangan (cheksiz halqa)."""
    result = tools.tool_screenshot("http://localhost:3000")
    assert result["success"] is False
    assert "localhost:3000" in result["error"]
