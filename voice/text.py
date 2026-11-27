"""Matnni MMS VITS o'zbek modeli kutadigan shaklga keltirish.

Tokenizer xatti-harakati modelning ``tokenizer.json`` normalizatoridan olingan:
kichik harfga o'tkazish, ruxsat etilgan belgilar qoldirish, har bir belgi oldiga
``|`` qo'yish va oxiriga ``|`` qo'yish. Bu yerda xuddi shuningdek Lotin yozuvidagi
o'zbek matni Kirillga o'tkaziladi — aks holda tokenizer matnni butunlay tashlab
yuboradi va model jim ovoz chiqaradi.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Iterator

ALLOWED_RE = re.compile(r"[^ 0123456|абвгдежзийклмнопрстуфхчшъьэюяёўғқҳ–—]")
BOUNDARY_RE = re.compile(r"(?<=[.!?;\n])\s+")

# Uzun belgilar birinchi: sh -> sh emas, sh -> sh bo'lib qolmasligi uchun.
_LATIN_TO_CYRILLIC: tuple[tuple[str, str], ...] = (
    ("sh", "ш"), ("SH", "ш"), ("ch", "ч"), ("CH", "ч"), ("ng", "нг"),
    ("NG", "нг"), ("o'", "ў"), ("O'", "ў"), ("oʻ", "ў"), ("Oʻ", "ў"),
    ("g'", "ғ"), ("G'", "ғ"), ("gʻ", "ғ"), ("Gʻ", "ғ"),
    ("ye", "е"), ("YE", "е"), ("ya", "я"), ("YA", "я"),
    ("yo", "ё"), ("YO", "ё"), ("yu", "ю"), ("YU", "ю"),
    ("a", "а"), ("b", "б"), ("c", "ц"), ("d", "д"), ("e", "е"),
    ("f", "ф"), ("g", "г"), ("h", "ҳ"), ("i", "и"), ("j", "ж"),
    ("k", "к"), ("l", "л"), ("m", "м"), ("n", "н"), ("o", "о"),
    ("p", "п"), ("q", "қ"), ("r", "р"), ("s", "с"), ("t", "т"),
    ("u", "у"), ("v", "в"), ("x", "х"), ("y", "й"), ("z", "з"),
)

_DIGIT_WORDS = {
    "0": "нол", "1": "бир", "2": "икки", "3": "уч", "4": "тўрт",
    "5": "беш", "6": "олти", "7": "етти", "8": "саккиз", "9": "тўққиз",
}

_CYR_RANGE = re.compile(r"[\u0400-\u04FF]")
_LAT_RANGE = re.compile(r"[A-Za-z]")


def detect_script(text: str) -> str:
    """Matnda qaysi yozuv ustunligini aniqlaydi."""
    cyr = len(_CYR_RANGE.findall(text))
    lat = len(_LAT_RANGE.findall(text))
    if cyr and cyr >= lat:
        return "cyrillic"
    if lat:
        return "latin"
    return "unknown"


def _expand_digits(text: str) -> str:
    return "".join(_DIGIT_WORDS.get(ch, ch) for ch in text)


def to_cyrillic(text: str) -> str:
    """O'zbek Lotin yozuvini model tushunadigan Kirill yozuviga o'tkazadi."""
    lowered = text.lower().replace("’", "'")
    for src, dst in _LATIN_TO_CYRILLIC:
        lowered = lowered.replace(src, dst)
    return lowered


def normalize_text(text: str, language: str = "auto") -> str:
    """Matnni tozalaydi va Kirill o'zbek shakliga keltiradi.

    ``language``: ``auto`` (aniqlaydi), ``uz``, ``latin``, ``cyrillic`` yoki
    ``en``/``ru``. ``en``/``ru`` faqat SAPI zaxira ovozi uchun ishlatiladi va
    bu yerda o'zgarishsiz qaytariladi.

    MUHIM: ``uz`` avval tanilmagan qiymat sifatida o'tkazib yuborilardi —
    lotin harflar model lug'atida yo'q, natijada token id 45 (lug'at 0..44)
    hosil bo'lib ONNX Runtime "indices element out of data bounds" bilan
    yiqilardi. Endi ``uz`` ``auto`` kabi to'liq normalizatsiyadan o'tadi.
    """
    if not isinstance(text, str):
        raise TypeError("text str bo'lishi shart")
    cleaned = unicodedata.normalize("NFC", text).strip()
    if not cleaned:
        return ""
    mode = language.lower().strip()
    if mode in ("auto", "uz", "uzbek", "uzbekistan", "oʻzbek"):
        mode = detect_script(cleaned)
    if mode == "latin":
        cleaned = to_cyrillic(cleaned)
    if mode in ("cyrillic", "latin", "auto", "unknown"):
        filtered = ALLOWED_RE.sub("", _expand_digits(cleaned))
        if not filtered.strip():
            # Aniq yozuv rejimi noto'g'ri berilgan bo'lsa (masalan
            # language="cyrillic" + lotin matn) modelga bo'sh matn ketardi.
            # Script'ni o'zimiz aniqlab qayta urinamiz — jim bo'sh natijadan
            # ko'ra foydalanuvchi niyati bajarilgani yaxshi.
            retry_mode = detect_script(cleaned)
            if retry_mode == "latin":
                cleaned = to_cyrillic(cleaned)
                filtered = ALLOWED_RE.sub("", _expand_digits(cleaned))
        cleaned = filtered
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def tokenize(text: str, tokenizer_path: str | Path, language: str = "auto") -> list[int]:
    """Matnni model vocab'iga mos int64 token id'lari ro'yxatiga aylantiradi.

    Noma'lum belgi uchun zaxira id (``<unk>`` yoki 0) HAR DOIM lug'at
    chegarasida bo'lishi shart. Avval ``vocab.get("<unk>", 45)`` yozilgan edi:
    lug'atda ``<unk>`` bo'lmasa (bu modelda 45 ta token, 0..44) id 45
    qaytarilardi va ONNX Runtime "indices element out of data bounds"
    xatosi bilan yiqilardi.
    """
    normalized = normalize_text(text, language)
    if not normalized:
        return []
    vocab: dict[str, int] = json.loads(Path(tokenizer_path).read_text(encoding="utf-8"))["model"]["vocab"]
    if not vocab:
        return []
    max_id = max(vocab.values())
    unk = vocab.get("<unk>")
    if unk is None or not (0 <= unk <= max_id):
        # Modelning o'z "bo'sh joy/ajratgich" tokeni xavfsiz zaxira.
        unk = vocab.get("|", 0)
    ids: list[int] = []
    for char in normalized:
        ids.append(vocab.get("|", 0))
        ids.append(vocab.get(char, unk))
    ids.append(vocab.get("|", 0))
    return ids


def split_segments(text: str, max_chars: int = 180, language: str = "auto") -> list[str]:
    """Uzun matnni modelga mos qismlarga ajratadi (gap chegarasi bo'yicha)."""
    normalized = normalize_text(text, language)
    if not normalized:
        return []
    raw_parts = [part.strip() for part in BOUNDARY_RE.split(normalized) if part.strip()]
    segments: list[str] = []
    current = ""
    for part in raw_parts:
        if len(part) > max_chars:
            if current:
                segments.append(current)
                current = ""
            words = part.split(" ")
            buffer = ""
            for word in words:
                candidate = f"{buffer} {word}".strip()
                if buffer and len(candidate) > max_chars:
                    segments.append(buffer)
                    buffer = word
                else:
                    buffer = candidate
            if buffer:
                segments.append(buffer)
            continue
        candidate = f"{current} {part}".strip()
        if current and len(candidate) > max_chars:
            segments.append(current)
            current = part
        else:
            current = candidate
    if current:
        segments.append(current)
    return segments


def iter_text_chunks(text: str, chunk_chars: int = 180, language: str = "auto") -> Iterator[str]:
    yield from split_segments(text, chunk_chars, language)
