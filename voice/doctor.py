"""O'rnatish va ishga tushirish diagnostikasi (halol dalillar bilan)."""

from __future__ import annotations

import ctypes
import hashlib
import importlib.util
import shutil
import sys
from pathlib import Path
from typing import Any

from .tts import PACKAGE_DIR, load_registry, SapiTTS


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text_normalized(path: Path) -> str:
    """Matn fayli uchun CRLF'ga chidamli sha256.

    `voice/models.json` dagi hash'lar LF shakli uchun hisoblangan. Windows'da
    `core.autocrlf=true` checkout faylni CRLF ga o'giradi va hash mos
    kelmaydi — fayl buzilmagan bo'lsa ham doctor "MOS EMAS" derdi.
    `.gitattributes` bilan LF majburlanadi; bu funksiya eski checkout'larni
    ham to'g'ri baholaydi.
    """
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def check_models() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    registry = load_registry()
    for model in registry["models"]:
        for relative, expected in model["files"].items():
            path = PACKAGE_DIR / model["dir"] / relative
            if not path.is_file():
                results.append({
                    "name": f"model:{model['id']}:{relative}",
                    "ok": False,
                    "detail": f"{path.relative_to(PACKAGE_DIR)} — fayl yo'q",
                })
                continue
            actual = _sha256(path)
            if actual == expected:
                ok, note = True, "sha256 mos"
            else:
                # Matn fayllari CRLF bilan kelishi mumkin — normallashtirib qayta tekshiramiz.
                normalized = _sha256_text_normalized(path)
                if normalized == expected:
                    ok, note = True, "sha256 mos (CRLF normallashtirildi)"
                else:
                    ok, note = False, "sha256 MOS EMAS"
            results.append({
                "name": f"model:{model['id']}:{relative}",
                "ok": ok,
                "detail": f"{path.relative_to(PACKAGE_DIR)} — {note}",
            })
    return results


def check_dependencies() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for name in ("numpy", "onnxruntime"):
        found = importlib.util.find_spec(name) is not None
        out.append({
            "name": f"python:{name}",
            "ok": found,
            "detail": f"{name} {'topildi' if found else 'topilmadi'}",
        })
    out.append({
        "name": "python:version",
        "ok": sys.version_info >= (3, 10),
        "detail": f"Python {sys.version.split()[0]}",
    })
    return out


def check_sapi() -> list[dict[str, Any]]:
    if sys.platform != "win32":
        return [{"name": "sapi", "ok": False, "detail": "Windows emas"}]
    try:
        voices = SapiTTS().list_voices()
    except Exception as exc:
        return [{"name": "sapi", "ok": False, "detail": f"{type(exc).__name__}: {exc}"}]
    return [{
        "name": "sapi",
        "ok": bool(voices),
        "detail": "SAPI ovozlari: " + (", ".join(voices) if voices else "topilmadi"),
    }]


def check_microphone() -> list[dict[str, Any]]:
    if sys.platform != "win32":
        return [{"name": "microphone", "ok": False, "detail": "Windows emas"}]
    try:
        count = ctypes.windll.winmm.waveInGetNumDevs()
        return [{
            "name": "microphone",
            "ok": int(count) > 0,
            "detail": f"Tizimda {int(count)} ta mikrofon/qurilma",
        }]
    except Exception as exc:
        return [{"name": "microphone", "ok": False, "detail": f"{type(exc).__name__}: {exc}"}]


def check_ffmpeg() -> list[dict[str, Any]]:
    path = shutil.which("ffmpeg")
    return [{
        "name": "ffmpeg",
        "ok": path is not None,
        "detail": path or "ffmpeg PATH da topilmadi",
    }]


def doctor() -> dict[str, Any]:
    checks = (
        check_dependencies()
        + check_models()
        + check_sapi()
        + check_microphone()
        + check_ffmpeg()
    )
    model_hashes_ok = all(c["ok"] for c in checks if c["name"].startswith("model:"))
    dep_ok = all(c["ok"] for c in checks if c["name"].startswith("python:"))
    sapi_ok = any(c["ok"] for c in checks if c["name"] == "sapi")
    mic_ok = any(c["ok"] for c in checks if c["name"] == "microphone")
    return {
        "ok": model_hashes_ok and dep_ok,
        "can_synthesize_uz": model_hashes_ok and dep_ok,
        "can_clone_from_file": model_hashes_ok and dep_ok,
        "can_record_microphone": mic_ok,
        "can_synthesize_ru_en": sapi_ok,
        "neural_clone": False,
        "clone_mode": "stylized",
        "checks": checks,
        "notes": [
            "Neural ovoz klonlash modeli yo'q (XTTS/Chatterbox litsenziya va Python talablari mos kelmaydi).",
            "Klonlash namunadan F0/spektr o'lchab, haqiqiy DSP bilan uslub o'tkazish orqali bajariladi.",
        ],
    }
