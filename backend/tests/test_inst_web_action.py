"""`inst_web` so'ralgan amalni bajarishi shart — o'rnini bosuvchi emas.

Topilgan nuqson (2026-11-26): `conduit run inst_web "... skrinshot ol"` har
doim `interact_web` (konsol/tarmoq tekshiruvi) chaqirardi va PASS berardi.
Skrinshot so'ralgan bo'lsa ham fayl YARATILMASDAN vazifa PASS bo'lardi —
talab bajarilmagan, ya'ni soxta PASS. Endi vazifa matni skrinshot so'rasa,
`tool_screenshot` chaqiriladi va fayl yo'li dalil sifatida qaytariladi.
"""
from __future__ import annotations

import inspect
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine import cli_runner  # noqa: E402


@pytest.mark.parametrize(
    "goal",
    [
        "https://example.com sahifasining skrinshotini ol",
        "take a screenshot of example.com",
        "shu sahifadan surat ol",
        "ekran rasmi kerak",
        "rasmga ol shu sahifani",
    ],
)
def test_goal_wants_screenshot_detects_requests(goal):
    assert cli_runner._goal_wants_screenshot(goal.lower()) is True, goal


@pytest.mark.parametrize(
    "goal",
    [
        "https://example.com konsol xatolarini tekshir",
        "https://example.com sahifasini och",
        "qizil kub 3D modelini yarat",
        "python uchun test yoz",
    ],
)
def test_goal_wants_screenshot_ignores_other_tasks(goal):
    assert cli_runner._goal_wants_screenshot(goal.lower()) is False, goal


def test_inst_web_branch_calls_screenshot_not_only_interact():
    """Shoxda `tool_screenshot` chaqiruvi mavjud bo'lishi shart."""
    src = inspect.getsource(cli_runner)
    start = src.find('inst == "inst_web"')
    assert start != -1, "inst_web branch topilmadi"
    end = src.find('elif inst == "inst_figma"', start)
    assert end != -1
    branch = src[start:end]

    assert "tool_screenshot" in branch, (
        "inst_web skrinshot so'ralganda screenshot chaqirmaydi — vazifa "
        "talabi bajarilmasdan PASS bo'ladi"
    )
    assert "_goal_wants_screenshot" in branch, "so'ralgan amal ajratilmagan"

