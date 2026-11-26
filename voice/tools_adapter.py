"""Conduit CLI/backend tool'larining ovoz plaginiga bog'lanishi.

``backend/tools.py`` shu module orqali 5 ta yangi tool'ni e'lon qiladi va bajaradi.
Natija har doim JSON-serializable dict bo'ladi (mavjud tool shartnomasi bilan bir xil).
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from .engine import VoiceEngine


VOICE_TOOL_SPECS = (
    ("voice_speak", ("voice_speak", "speak", "tts"), "text [category] [language] [out.wav]", "Lokal ovoz bilan matnni WAV ga aylantiradi."),
    ("voice_clone", ("voice_clone", "clone_voice"), "text reference.wav [category] [out.wav]", "Namuna ovoz uslubini matnga o'tkazadi."),
    ("voice_convert", ("voice_convert", "convert_voice"), "input.wav category [out.wav]", "Mavjud WAV ovozini toifaga o'zgartiradi."),
    ("voice_doctor", ("voice_doctor", "voice_check"), "", "Ovoz dvigatelining holatini tekshiradi."),
    ("voice_catalog", ("voice_catalog", "voices"), "", "Mavjud ovoz modellari va toifalarini ro'yxatlaydi."),
    ("voice_stream", ("voice_stream", "stream_voice"), "text [category] [language] [out_dir]", "Matnni ketma-ket WAV bo'laklariga oqim qilib chiqaradi."),
)


def _engine() -> VoiceEngine:
    return VoiceEngine()


def _payload(args: list[str]) -> dict[str, Any]:
    if args and args[0].strip().startswith("{"):
        try:
            data = json.loads(args[0])
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON noto'g'ri: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("JSON obyekt bo'lishi shart")
        return data
    return {}


def voice_catalog(_args: list[str] | None = None) -> dict[str, Any]:
    engine = _engine()
    return {
        "success": True,
        "tool": "voice_catalog",
        "models": engine.list_models(),
        "categories": engine.list_categories(),
        "capabilities": {
            "tts_uz": True,
            "tts_en_ru_via_sapi": True,
            "clone_from_reference_file": True,
            "clone_mode": "stylized",
            "neural_clone": False,
            "microphone_required": False,
        },
    }


def voice_doctor(_args: list[str] | None = None) -> dict[str, Any]:
    report = _engine().doctor()
    return {"success": bool(report["ok"]), "tool": "voice_doctor", "report": report}


def voice_speak(args: list[str]) -> dict[str, Any]:
    data = _payload(args)
    text = str(data.get("text", args[0] if args else "")).strip()
    category = str(data.get("category", args[1] if len(args) > 1 else "neutral"))
    language = str(data.get("language", args[2] if len(args) > 2 else "auto"))
    out = data.get("out") or data.get("out_path") or (args[3] if len(args) > 3 else None)
    if not text:
        return {"success": False, "tool": "voice_speak", "error": "Matn bo'sh"}
    try:
        result = _engine().synthesize(
            text, category=category, language=language,
            out_path=Path(str(out)) if out else None,
        )
        return {"success": True, "tool": "voice_speak", **result.as_dict()}
    except Exception as exc:
        return {"success": False, "tool": "voice_speak", "error": f"{type(exc).__name__}: {exc}"}


def voice_clone(args: list[str]) -> dict[str, Any]:
    data = _payload(args)
    text = str(data.get("text", args[0] if args else "")).strip()
    reference = str(data.get("reference") or data.get("reference_wav") or (args[1] if len(args) > 1 else ""))
    category = str(data.get("category", args[2] if len(args) > 2 else "neutral"))
    out = data.get("out") or data.get("out_path") or (args[3] if len(args) > 3 else None)
    if not text or not reference:
        return {"success": False, "tool": "voice_clone", "error": "text va reference shart"}
    if not Path(reference).is_file():
        return {"success": False, "tool": "voice_clone", "error": f"Namuna fayl yo'q: {reference}"}
    consent = data.get("consent") is True or str(data.get("consent", "")).lower() == "true"
    consent_id = data.get("consent_id") or data.get("consent-id")
    if not consent or not consent_id:
        return {
            "success": False, "tool": "voice_clone",
            "error": "CONSENT_REQUIRED: klonlash uchun consent=true va consent_id shart.",
            "error_code": "CONSENT_REQUIRED", "retryable": False,
        }
    try:
        result = _engine().clone(
            text, reference, category=category,
            out_path=Path(str(out)) if out else None,
            consent=True, consent_id=str(consent_id),
        )
        return {"success": True, "tool": "voice_clone", **result.as_dict()}
    except Exception as exc:
        return {"success": False, "tool": "voice_clone", "error": f"{type(exc).__name__}: {exc}"}


def voice_convert(args: list[str]) -> dict[str, Any]:
    data = _payload(args)
    source = str(data.get("input") or data.get("input_wav") or (args[0] if args else ""))
    category = str(data.get("category", args[1] if len(args) > 1 else ""))
    out = data.get("out") or data.get("out_path") or (args[2] if len(args) > 2 else None)
    if not source or not category:
        return {"success": False, "tool": "voice_convert", "error": "input va category shart"}
    if not Path(source).is_file():
        return {"success": False, "tool": "voice_convert", "error": f"WAV fayl yo'q: {source}"}
    try:
        result = _engine().convert(
            source, category, out_path=Path(str(out)) if out else None
        )
        return {"success": True, "tool": "voice_convert", **result.as_dict()}
    except Exception as exc:
        return {"success": False, "tool": "voice_convert", "error": f"{type(exc).__name__}: {exc}"}


def voice_stream(args: list[str]) -> dict[str, Any]:
    """Ketma-ket WAV bo'laklari + haqiqiy vaqt metrikalari."""
    import time
    data = _payload(args)
    text = str(data.get("text", args[0] if args else "")).strip()
    category = str(data.get("category", args[1] if len(args) > 1 else "neutral"))
    language = str(data.get("language", args[2] if len(args) > 2 else "auto"))
    out_dir = data.get("out_dir") or (args[3] if len(args) > 3 else None)
    if not text:
        return {"success": False, "tool": "voice_stream", "error": "Matn bo'sh"}
    started = time.perf_counter()
    first_chunk_ms: int | None = None
    paths: list[str] = []
    try:
        engine = _engine()
        target = (
            Path(str(out_dir)) if out_dir
            else engine.output_dir / f"stream_{uuid.uuid4().hex[:10]}"
        )
        target.mkdir(parents=True, exist_ok=True)
        for index, chunk in enumerate(engine.stream(text, category, language)):
            if first_chunk_ms is None:
                first_chunk_ms = int((time.perf_counter() - started) * 1000)
            path = target / f"chunk_{index:04d}.wav"
            path.write_bytes(chunk)
            paths.append(str(path))
        return {
            "success": True, "tool": "voice_stream", "chunks": len(paths),
            "chunk_paths": paths, "out_dir": str(target),
            "first_chunk_ms": first_chunk_ms,
            "total_ms": int((time.perf_counter() - started) * 1000),
            "synthetic": True,
        }
    except Exception as exc:
        return {"success": False, "tool": "voice_stream", "error": f"{type(exc).__name__}: {exc}"}


def voice_tool(name: str, args: list[str]) -> dict[str, Any]:
    handlers = {
        "voice_speak": voice_speak,
        "voice_clone": voice_clone,
        "voice_convert": voice_convert,
        "voice_doctor": voice_doctor,
        "voice_catalog": voice_catalog,
        "voice_stream": voice_stream,
    }
    handler = handlers.get(name)
    if handler is None:
        return {"success": False, "tool": name, "error": f"Noma'lum ovoz tool'i: {name}"}
    return handler(args)
