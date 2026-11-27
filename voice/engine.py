"""Ovoz plaginining asosiy API'si: sintez, klonlash, toifalar, stream, doctor."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator

import numpy as np

from .audio import analyze_voice, read_wav, safe_path, wav_bytes, write_wav
from .doctor import doctor as run_doctor
from .profiles import (
    apply_params,
    get_category,
    list_categories,
    params_from_profile,
)
from .text import split_segments
from .tts import (
    OnnxTTS,
    SapiTTS,
    load_registry,
    pick_sapi_voice,
    sapi_supported,
)

PACKAGE_DIR = Path(__file__).resolve().parent


@dataclass
class VoiceResult:
    success: bool
    wav_path: str = ""
    sample_rate: int = 0
    duration_s: float = 0.0
    size_bytes: int = 0
    backend: str = ""
    model: str = ""
    category: str = ""
    language: str = ""
    synthetic: bool = True
    clone_mode: str = "none"
    neural_clone: bool = False
    device: str = "cpu"
    warnings: list[str] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)
    text_preview: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "wav_path": self.wav_path,
            "sample_rate": self.sample_rate,
            "duration_s": round(self.duration_s, 3),
            "size_bytes": self.size_bytes,
            "backend": self.backend,
            "model": self.model,
            "category": self.category,
            "language": self.language,
            "synthetic": self.synthetic,
            "clone_mode": self.clone_mode,
            "neural_clone": self.neural_clone,
            "device": self.device,
            "warnings": self.warnings,
            "params": self.params,
            "text_preview": self.text_preview,
        }


class VoiceEngine:
    """Barcha ovoz operatsiyalari uchun yagona kirish nuqtasi."""

    def __init__(self, output_dir: str | Path | None = None,
                 allowed_root: str | Path | None = None) -> None:
        self.output_dir = Path(output_dir) if output_dir else PACKAGE_DIR / "output"
        # `allowed_root` — `safe_path` chegarasi (ixtiyoriy). Standart holatda
        # uy papkasi (avvalgi xatti-harakat). Testlar `tmp_path` beradi, chunki
        # pytest vaqtinchalik papkasi (`/tmp/...`) uy papkasidan tashqarida va
        # `safe_path` uni to'g'ri rad etadi — bu xavfsizlik chegarasi, nuqson
        # emas. O'lchangan: CI run 46019392258 da 3 test shu sababdan yiqilgan.
        self.allowed_root = Path(allowed_root) if allowed_root is not None else Path.home()
        self._onnx: dict[str, OnnxTTS] = {
            "male": OnnxTTS("uz_male_mms"),
            "female": OnnxTTS("uz_female_mms"),
        }
        self._sapi: SapiTTS | None = None

    # -- katalog -----------------------------------------------------------
    def list_models(self) -> list[dict[str, Any]]:
        registry = load_registry()
        return [
            {key: value for key, value in model.items() if key != "files"}
            for model in registry["models"]
        ]

    def list_categories(self) -> list[dict[str, Any]]:
        return list_categories()

    def doctor(self) -> dict[str, Any]:
        return run_doctor()

    # -- sintez ------------------------------------------------------------
    def _resolve_voice(self, category: str, voice: str | None) -> str:
        if voice:
            key = str(voice).strip().lower()
            aliases = {"uz_male_mms": "male", "uz_female_mms": "female",
                       "erkak": "male", "ayol": "female", "qiz": "female"}
            key = aliases.get(key, key)
            if key in self._onnx:
                return key
        return str(get_category(category)[1]["model"])

    def _synthesize_raw(
        self, text: str, language: str, model_key: str, warnings: list[str]
    ) -> tuple[np.ndarray, int, str, str]:
        mode = (language or "auto").lower()
        if sapi_supported(mode):
            if self._sapi is None:
                self._sapi = SapiTTS()
            try:
                voices = self._sapi.list_voices()
            except Exception as exc:
                voices = []
                warnings.append(f"SAPI ovoz ro'yxati olinmadi: {exc}")
            name = pick_sapi_voice(mode, voices)
            if not name:
                warnings.append(f"{mode} uchun SAPI ovozi topilmadi; mavjud: {voices}")
            samples, sr = self._sapi.synthesize(text)
            return samples, sr, "sapi", name or "default"
        samples = self._onnx[model_key].synthesize(text, language=language)
        if mode == "latin":
            warnings.append("Lotin matn o'zbek Kirilliga o'tkazildi.")
        return samples, self._onnx[model_key].sample_rate, "onnx", self._onnx[model_key].info["id"]

    def synthesize(
        self,
        text: str,
        category: str = "neutral",
        language: str = "auto",
        voice: str | None = None,
        strength: float = 1.0,
        out_path: str | Path | None = None,
    ) -> VoiceResult:
        canonical, category_params = get_category(category)
        model_key = self._resolve_voice(canonical, voice)
        warnings: list[str] = []
        samples, sr, backend, model = self._synthesize_raw(
            text, language, model_key, warnings
        )
        params = {
            "category": canonical,
            "pitch": category_params["pitch"],
            "formant": category_params["formant"],
            "tilt": category_params["tilt"],
            "breath": category_params["breath"],
            "speed": category_params["speed"],
            "notes": [],
        }
        samples = apply_params(samples, sr, params, strength=strength)
        path = self._save(samples, sr, out_path)
        return VoiceResult(
            success=True,
            wav_path=str(path), sample_rate=sr,
            duration_s=len(samples) / sr, size_bytes=path.stat().st_size,
            backend=backend, model=model, category=canonical,
            language=language, clone_mode="none",
            device="cpu" if backend == "sapi" else self._onnx[model_key].device,
            warnings=warnings, params=params,
            text_preview=text[:100],
        )

    # -- klonlash ----------------------------------------------------------
    def profile(self, reference_wav: str | Path) -> dict[str, float]:
        samples, sr = read_wav(reference_wav, root=self.allowed_root)
        return analyze_voice(samples, sr)

    def _save(self, samples: np.ndarray, sr: int, out_path: str | Path | None) -> Path:
        path = Path(out_path) if out_path else self.output_dir / f"voice_{uuid.uuid4().hex[:12]}.wav"
        return write_wav(path, samples, sr, root=self.allowed_root)

    def clone(
        self,
        text: str,
        reference_wav: str | Path,
        category: str | None = "neutral",
        strength: float = 1.0,
        language: str = "auto",
        out_path: str | Path | None = None,
        *,
        consent: bool = False,
        consent_id: str | None = None,
    ) -> VoiceResult:
        """Namuna uslubini ko'chirish.

        Roziliksiz klonlash taqiqlangan: boshqa shaxs ovozida soxta audio
        yaratish xavfi. `consent=True` va ro'yxatdan o'tgan `consent_id` shart.
        """
        if not consent:
            raise PermissionError(
                "CONSENT_REQUIRED: klonlash uchun namuna egasining roziligi shart "
                "(consent=True va consent_id berilishi kerak)."
            )
        if not consent_id or not consent_id.strip():
            raise PermissionError("CONSENT_REQUIRED: consent_id bo'sh bo'lishi mumkin emas.")
        profile = self.profile(reference_wav)
        params = params_from_profile(profile, category=category)
        model_key = self._resolve_voice(str(params["category"]), None)
        warnings: list[str] = list(params["notes"])
        samples, sr, backend, model = self._synthesize_raw(
            text, language, model_key, warnings
        )
        samples = apply_params(samples, sr, params, strength=strength)
        warnings.append(
            "Neural klonlash emas: namunadan F0/spektr o'lchanib, uslubiy o'tkazish bajarildi."
        )
        path = self._save(samples, sr, out_path)
        return VoiceResult(
            success=True,
            wav_path=str(path), sample_rate=sr,
            duration_s=len(samples) / sr, size_bytes=path.stat().st_size,
            backend=backend, model=model, category=str(params["category"]),
            language=language, clone_mode="stylized", neural_clone=False,
            device="cpu" if backend == "sapi" else self._onnx[model_key].device,
            warnings=warnings, params=params, text_preview=text[:100],
        )

    def convert(
        self,
        input_wav: str | Path,
        category: str,
        strength: float = 1.0,
        out_path: str | Path | None = None,
    ) -> VoiceResult:
        canonical, category_params = get_category(category)
        samples, sr = read_wav(input_wav, root=self.allowed_root)
        params = {
            "category": canonical,
            "pitch": category_params["pitch"],
            "formant": category_params["formant"],
            "tilt": category_params["tilt"],
            "breath": category_params["breath"],
            "speed": category_params["speed"],
            "notes": [],
        }
        samples = apply_params(samples, sr, params, strength=strength)
        path = self._save(samples, sr, out_path)
        return VoiceResult(
            success=True, wav_path=str(path), sample_rate=sr,
            duration_s=len(samples) / sr, size_bytes=path.stat().st_size,
            backend="dsp", model=Path(input_wav).name, category=canonical,
            language="", clone_mode="category_conversion",
            device="cpu",
            warnings=[], params=params, text_preview="",
        )

    # -- oqim --------------------------------------------------------------
    def stream(
        self,
        text: str,
        category: str = "neutral",
        language: str = "auto",
        chunk_ms: int = 250,
        strength: float = 1.0,
    ) -> Iterator[bytes]:
        """Har bir qism mustaqil WAV sarlavhasi bilan oqib chiqadi.

        Matn gaplarga ajratilib, har bir gap sintez qilinishi zahoti yuboriladi —
        bu ketma-ket ijro etish (streaming playback) uchun yaroqli.
        """
        if chunk_ms < 50:
            raise ValueError("chunk_ms kamida 50 bo'lishi shart")
        canonical, category_params = get_category(category)
        params = {
            "category": canonical,
            "pitch": category_params["pitch"],
            "formant": category_params["formant"],
            "tilt": category_params["tilt"],
            "breath": category_params["breath"],
            "speed": category_params["speed"],
            "notes": [],
        }
        model_key = self._resolve_voice(canonical, None)
        for segment in split_segments(text, language=language):
            samples, sr, _backend, _model = self._synthesize_raw(
                segment, language, model_key, []
            )
            samples = apply_params(samples, sr, params, strength=strength)
            chunk_size = max(1, int(sr * chunk_ms / 1000.0))
            for start in range(0, len(samples), chunk_size):
                yield wav_bytes(samples[start:start + chunk_size], sr)

    def stream_text(
        self, chunks: Iterable[str], category: str = "neutral",
        language: str = "auto", chunk_ms: int = 250,
    ) -> Iterator[bytes]:
        """AI agent ketma-ket yuborgan matn bo'laklarini ovozga aylantiradi."""
        for chunk in chunks:
            yield from self.stream(chunk, category, language, chunk_ms)

