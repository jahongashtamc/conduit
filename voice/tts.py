"""Lokal TTS dvigatellari: MMS VITS ONNX (o'zbek) va Windows SAPI (ru/en zaxira).

Hech qanday bulut API, kalit yoki tarmoq chaqiruvi ishlatilmaydi. ONNX modellari
``voice/models/`` ichida, SAPI esa tizimda o'rnatilgan ovozlardan foydalanadi.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

from .audio import VoiceAudioError, concat_clips, normalize_peak, read_wav
from .text import split_segments, tokenize

PACKAGE_DIR = Path(__file__).resolve().parent


class VoiceDependencyError(RuntimeError):
    """Kerakli kutubxona yoki tizim komponenti yo'q."""


class VoiceBackendError(RuntimeError):
    """TTS dvigateli ishga oshmadi."""


def load_registry() -> dict[str, Any]:
    path = PACKAGE_DIR / "models.json"
    return json.loads(path.read_text(encoding="utf-8"))


def model_info(model_id: str) -> dict[str, Any]:
    for item in load_registry()["models"]:
        if item["id"] == model_id:
            return item
    raise VoiceBackendError(f"Registrda bunday model yo'q: {model_id}")


class OnnxTTS:
    """MMS VITS ONNX modeli bilan o'zbek nutqini sintez qiladi."""

    def __init__(self, model_id: str = "uz_male_mms") -> None:
        self.info = model_info(model_id)
        self._session: Any = None
        self._providers: tuple[str, ...] = ()
        self._sample_rate = int(load_registry()["sample_rate"])

    @property
    def device(self) -> str:
        """Haqiqiy ishlatilayotgan hisoblash qurilmasi."""
        if self._providers and self._providers[0] == "CUDAExecutionProvider":
            return "cuda:0"
        return "cpu"

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    def _get_session(self) -> Any:
        if self._session is None:
            try:
                import onnxruntime as ort
            except ImportError as exc:
                raise VoiceDependencyError(
                    "onnxruntime o'rnatilmagan: python -m pip install onnxruntime==1.32.0"
                ) from exc
            onnx_path = PACKAGE_DIR / self.info["onnx"]
            if not onnx_path.is_file():
                raise VoiceDependencyError(
                    f"ONNX model fayli yo'q: {onnx_path}. Avval modelni yuklab oling."
                )
            # Ish vaqtida hash tekshiruvi: doctor bir marta tekshirgan bo'lsa ham,
            # keyin fayl o'zgarib ketsa, jim ishlatish mumkin emas.
            import hashlib
            expected = self.info.get("files", {}).get("onnx/model.onnx")
            if expected:
                digest = hashlib.sha256()
                with onnx_path.open("rb") as fh:
                    for block in iter(lambda: fh.read(1024 * 1024), b""):
                        digest.update(block)
                if digest.hexdigest() != expected:
                    raise VoiceDependencyError(
                        f"MODEL_HASH_MISMATCH: {onnx_path} sha256 mos emas. "
                        "Modelni qayta yuklab oling."
                    )
            providers = ["CPUExecutionProvider"]
            if ort.get_available_providers() and "CUDAExecutionProvider" in ort.get_available_providers():
                providers.insert(0, "CUDAExecutionProvider")
            self._session = ort.InferenceSession(str(onnx_path), providers=providers)
            self._providers = tuple(providers)
        return self._session

    def synthesize(self, text: str, language: str = "auto") -> np.ndarray:
        segments = split_segments(text, language=language)
        if not segments:
            raise VoiceAudioError("Matn bo'sh yoki model tushunadigan belgilardan iborat emas")
        tokenizer_path = PACKAGE_DIR / self.info["tokenizer"]
        clips: list[np.ndarray] = []
        for segment in segments:
            ids = tokenize(segment, tokenizer_path, language)
            if not ids:
                continue
            arr = np.asarray([ids], dtype=np.int64)
            outputs = self._get_session().run(
                ["waveform"], {"input_ids": arr, "attention_mask": np.ones_like(arr)}
            )
            wave = np.asarray(outputs[0], dtype=np.float32).reshape(-1)
            if len(wave) == 0:
                continue
            clips.append(normalize_peak(wave, 0.92))
        if not clips:
            raise VoiceAudioError("Hech bir matn bo'lagi tokenlarga aylanmadi")
        return concat_clips(clips, self._sample_rate, gap_ms=120)


class SapiTTS:
    """Windows SAPI 5 orqali tizimda mavjud ovozlar bilan nutq yaratadi."""

    def __init__(self, voice_name: str = "", rate: int = 0) -> None:
        self.voice_name = voice_name
        self.rate = int(rate)
        self._sample_rate = 22050

    @staticmethod
    def available() -> bool:
        return sys.platform == "win32"

    def list_voices(self) -> list[str]:
        if not self.available():
            return []
        ps = (
            "$v = New-Object -ComObject SAPI.SpVoice; "
            "foreach ($t in $v.GetVoices()) { Write-Output $t.GetDescription() }"
        )
        try:
            proc = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
                capture_output=True, text=True, timeout=30,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise VoiceBackendError(f"SAPI ovozlarini olish mumkin emas: {exc}") from exc
        if proc.returncode != 0:
            raise VoiceBackendError(f"SAPI xatoligi: {proc.stderr.strip()}")
        return [line.strip() for line in proc.stdout.splitlines() if line.strip()]

    def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        if not self.available():
            raise VoiceDependencyError("SAPI faqat Windows'da mavjud")
        if not text.strip():
            raise VoiceAudioError("SAPI uchun matn bo'sh")
        script = str(PACKAGE_DIR / "sapi_write.ps1")
        with tempfile.TemporaryDirectory(prefix="conduit_voice_") as tmp:
            in_file = Path(tmp) / "text.txt"
            out_file = Path(tmp) / "speech.wav"
            in_file.write_text(text, encoding="utf-8")
            cmd = [
                "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", script, "-InFile", str(in_file), "-OutFile", str(out_file),
                "-Rate", str(self.rate),
            ]
            if self.voice_name:
                cmd += ["-VoiceName", self.voice_name]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            except (OSError, subprocess.SubprocessError) as exc:
                raise VoiceBackendError(f"SAPI sintezi ishlamadi: {exc}") from exc
            if proc.returncode != 0 or not out_file.is_file():
                raise VoiceBackendError(
                    f"SAPI sintezi ishlamadi: {(proc.stderr or proc.stdout).strip()}"
                )
            samples, sr = read_wav(out_file)
        return normalize_peak(samples, 0.92), sr


LANGUAGE_HINTS: dict[str, str] = {
    "en": "English", "english": "English", "ru": "Russian", "russian": "Russian",
}


def pick_sapi_voice(language: str, available: list[str]) -> str:
    hint = LANGUAGE_HINTS.get(language.lower(), "")
    if not hint:
        return ""
    for name in available:
        if hint.lower() in name.lower():
            return name
    return ""


def sapi_supported(language: str) -> bool:
    return language.lower() in LANGUAGE_HINTS
