"""Soxta PASS himoyasi: dalilda xato bo'lsa check_goal PASS bermaydi."""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest  # noqa: E402
import tools  # noqa: E402


def _check(goal: str, evidence: str) -> dict:
    return tools.tool_check_goal(
        goal, json.dumps({"evidence": evidence, "captured_at": time.time()})
    )


@pytest.mark.parametrize(
    "evidence",
    [
        "Amal: tools.py video_render xato: kamida bitta mavjud kirish video fayli kerak.",
        "Amal: tools.py gen_image xato: Prompt bo'sh",
        "Amal: tools.py run_process xato: buyruq topilmadi",
        "Traceback (most recent call last): ...",
        "muvaffaqiyatsiz yakunlandi",
        "the engine failed to start",
        "Exception: something broke",
    ],
)
def test_error_evidence_never_passes(evidence):
    """Dalil matni nosozlikni ko'rsatsa, PASS berilmaydi.

    Topilgan nuqson: `inst_video` "video_render xato: ... kerak" yozgan holda
    PASS olardi, chunki evaluator faqat fayl mavjudligini ko'rardi.
    """
    res = _check("2 sekundlik MP4 video yarat", evidence)
    assert res["verdict"] == "FAIL", (
        f"xato dalil PASS oldi: {evidence!r} -> {res['verdict']}"
    )
    assert res["issues"], "FAIL sababi ko'rsatilmadi"


def test_success_evidence_still_passes():
    """Ijobiy dalil bloklanmasligi kerak — soxta FAIL bo'lmasin."""
    res = _check(
        "sariq yulduz 640x480 png yarat",
        "Amal: tools.py gen_image\nRasm: C:\\x\\gen_1.png\nO'lcham: 640x480\nHajm: 10024b",
    )
    assert res["verdict"] == "PASS", res.get("issues")


def test_topilmadi_alone_is_not_a_failure():
    """"topilmadi" muvaffaqiyatli natijada ham uchraydi — soxta FAIL bo'lmasin."""
    res = _check(
        "video montaj",
        "Amal: eski montage topilmadi, yangisi yaratildi\nVideo: a.mp4\nKadrlar: 72",
    )
    assert res["verdict"] == "PASS", res.get("issues")


def test_explicit_success_false_blocks_pass():
    res = tools.tool_check_goal(
        "vazifa",
        json.dumps({"evidence": "bajarildi", "success": False, "captured_at": time.time()}),
    )
    assert res["verdict"] == "FAIL"


def test_empty_evidence_never_passes():
    res = tools.tool_check_goal("vazifa", json.dumps({"evidence": ""}))
    assert res["verdict"] == "FAIL"
