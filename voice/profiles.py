"""Ovoz toifalari va ularning o'lchanadigan akustik parametrlari.

Har bir toifa real DSP parametrlariga ega: yarim ton, formant masshtabi,
spektral qiyalik, nafas shovqini va nutq tezligi. Namuna ovozidan klonlashda
shu parametrlar F0/spektr o'lchovlari bilan aralashtiriladi.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .audio import (
    add_breath,
    formant_scale,
    normalize_peak,
    pitch_shift,
    spectral_tilt,
    time_stretch,
)


class CategoryError(ValueError):
    """Noma'lum ovoz toifasi."""


CategoryParams = dict[str, float | str]

CATEGORIES: dict[str, CategoryParams] = {
    "neutral": {
        "label": "Neutral",
        "model": "male",
        "pitch": 0.0, "formant": 1.0, "tilt": 0.0, "breath": 0.0, "speed": 1.0,
    },
    "male": {
        "label": "Erkak",
        "model": "male",
        "pitch": -2.0, "formant": 0.96, "tilt": -0.06, "breath": 0.0, "speed": 0.97,
    },
    "female": {
        "label": "Ayol",
        "model": "female",
        "pitch": 0.0, "formant": 1.02, "tilt": 0.04, "breath": 0.02, "speed": 1.01,
    },
    "boy": {
        "label": "Bola o'g'il",
        "model": "male",
        "pitch": 5.0, "formant": 0.88, "tilt": 0.08, "breath": 0.10, "speed": 1.05,
    },
    "girl": {
        "label": "Bola qiz",
        "model": "female",
        "pitch": 4.0, "formant": 0.90, "tilt": 0.12, "breath": 0.12, "speed": 1.05,
    },
    "child": {
        "label": "Bola (umumiy)",
        "model": "female",
        "pitch": 6.0, "formant": 0.85, "tilt": 0.15, "breath": 0.15, "speed": 1.08,
    },
    "teen": {
        "label": "O'smir",
        "model": "female",
        "pitch": 2.0, "formant": 0.94, "tilt": 0.06, "breath": 0.06, "speed": 1.03,
    },
    "deep": {
        "label": "Past erkak ovozi",
        "model": "male",
        "pitch": -6.0, "formant": 0.92, "tilt": -0.14, "breath": 0.0, "speed": 0.93,
    },
    "elderly": {
        "label": "Keksa ovoz",
        "model": "male",
        "pitch": -3.0, "formant": 1.03, "tilt": -0.18, "breath": 0.25, "speed": 0.90,
    },
}

ALIASES: dict[str, str] = {
    "erkak": "male", "odam": "male", "man": "male", "m": "male",
    "ayol": "female", "qiz": "girl", "woman": "female", "w": "female",
    "bola": "child", "child": "child", "kid": "child",
    "bola_qiz": "girl", "girl_child": "girl", "boy_child": "boy",
    "yosh": "teen", "teenager": "teen", "qari": "elderly", "old": "elderly",
    "past": "deep", "low": "deep", "oddiy": "neutral", "default": "neutral",
}


def resolve_category(name: str | None) -> str:
    """Kategoriya nomi yoki alias'ini kanonik nomga o'tkazadi."""
    if not name:
        return "neutral"
    key = str(name).strip().lower().replace("-", "_").replace(" ", "_")
    return ALIASES.get(key, key if key in CATEGORIES else "")


def get_category(name: str | None) -> tuple[str, CategoryParams]:
    resolved = resolve_category(name)
    if resolved not in CATEGORIES:
        raise CategoryError(
            f"Noma'lum ovoz toifasi: '{name}'. Mavjud: {', '.join(sorted(CATEGORIES))}"
        )
    return resolved, CATEGORIES[resolved]


def list_categories() -> list[dict[str, Any]]:
    return [
        {"id": key, "label": str(params["label"]), "model": str(params["model"]),
         "pitch_semitones": params["pitch"], "formant_scale": params["formant"],
         "spectral_tilt": params["tilt"], "breath": params["breath"],
         "speed": params["speed"]}
        for key, params in CATEGORIES.items()
    ]


def params_from_profile(profile: dict[str, float], category: str | None = None) -> dict[str, Any]:
    """Klonlanayotgan namunaning o'lchovlaridan DSP parametrlarini chiqaradi."""
    resolved, base = get_category(category or "neutral")
    f0 = float(profile.get("f0_hz", 0.0))
    balance = float(profile.get("spectral_balance_db", 0.0))
    pitch = float(base["pitch"])
    formant = float(base["formant"])
    tilt = float(base["tilt"])
    breath = float(base["breath"])
    notes: list[str] = []
    if f0 >= 70.0:
        base_f0 = 150.0 if resolved in ("male", "deep", "elderly", "neutral") else 200.0
        measured = 12.0 * math.log2(f0 / base_f0)
        pitch = round(0.55 * pitch + 0.45 * measured, 2)
        formant = round(min(1.3, max(0.8, 0.65 * formant + 0.35 * (1.0 + (f0 - base_f0) / base_f0 * 0.2))), 3)
    else:
        notes.append("Namunada asosiy chastota aniqlanmadi; faqat toifa parametrlari ishlatildi.")
    if balance != 0.0:
        measured_tilt = (balance + 8.0) / 12.0
        tilt = round(min(0.4, max(-0.4, 0.6 * tilt + 0.4 * measured_tilt)), 3)
    return {
        "category": resolved,
        "pitch": pitch,
        "formant": formant,
        "tilt": tilt,
        "breath": min(0.6, breath),
        "speed": float(base["speed"]),
        "notes": notes,
    }


def apply_params(samples: np.ndarray, sample_rate: int, params: dict[str, Any], strength: float = 1.0) -> np.ndarray:
    """Parametrlarni haqiqiy signalga qo'llaydi (tartib muhim)."""
    if not 0.0 <= strength <= 2.0:
        raise CategoryError("strength 0..2 oralig'ida bo'lishi shart")
    x = np.asarray(samples, dtype=np.float32).copy()
    if len(x) == 0:
        return x
    scale = max(0.0, min(1.0, strength))
    speed = float(params.get("speed", 1.0))
    if abs(speed - 1.0) > 1e-6:
        x = time_stretch(x, 1.0 / (1.0 + (speed - 1.0) * scale))
    formant = float(params.get("formant", 1.0))
    if abs(formant - 1.0) > 1e-6:
        x = formant_scale(x, sample_rate, 1.0 + (formant - 1.0) * scale)
    pitch = float(params.get("pitch", 0.0))
    if abs(pitch) > 1e-6:
        x = pitch_shift(x, sample_rate, pitch * scale)
    tilt = float(params.get("tilt", 0.0))
    if abs(tilt) > 1e-6:
        x = spectral_tilt(x, sample_rate, tilt * scale)
    breath = float(params.get("breath", 0.0))
    if breath > 0:
        x = add_breath(x, sample_rate, breath * scale)
    return normalize_peak(x)
