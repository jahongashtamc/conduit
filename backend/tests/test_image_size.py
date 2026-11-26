"""parse_image_size: vazifa matnidan o'lcham ajratish."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app_adapter  # noqa: E402
import pytest  # noqa: E402

CASES = [
    ("sariq yulduz 640x480 png yarat", (640, 480)),
    ("800x600 o'lchamda qizil kub", (800, 600)),
    ("1024*768 shar", (1024, 768)),
    ("2048×1536 katta rasm", (2048, 1536)),
    ("oddiy tavsif", (512, 512)),
    ("64x64 kichik", (64, 64)),
    # Chegaradan tashqari — default qaytadi
    ("10000x10000 juda katta", (512, 512)),
    ("10x10 juda kichik", (512, 512)),
]


@pytest.mark.parametrize("goal,expected", CASES)
def test_parse_image_size(goal, expected):
    assert app_adapter.parse_image_size(goal) == expected


def test_dimensions_are_not_swapped():
    assert app_adapter.parse_image_size("640x480") == (640, 480)
    assert app_adapter.parse_image_size("480x640") == (480, 640)


def test_tool_gen_image_honours_requested_size(tmp_path):
    import tools

    out = tmp_path / "sized.png"
    res = tools.tool_gen_image("sariq yulduz", 640, 480, output_path=str(out))
    assert res["success"] is True
    from PIL import Image

    assert Image.open(out).size == (640, 480)


def test_no_caller_hardcodes_512():
    """`cli_runner` da o'lcham qattiq kodlanmasligi shart.

    Nuqson: `painter` va `inst_image` ikkalasi ham `tool_gen_image(goal, 512,
    512)` deb chaqirardi, vazifa matnidagi o'lcham esa butunlay yo'qolardi.
    """
    import pathlib

    src = pathlib.Path(__file__).resolve().parents[1] / "engine" / "cli_runner.py"
    text = src.read_text(encoding="utf-8")
    hardcoded = [
        line.strip()
        for line in text.splitlines()
        if "tool_gen_image(" in line and "512" in line
    ]
    assert not hardcoded, f"qattiq kodlangan o'lcham qoldi: {hardcoded}"
