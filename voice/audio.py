"""Faqat numpy + stdlib bilan ishlaydigan WAV va ovoz DSP funksiyalari.

Bu yerda sun'iy "ovoz effekti" emas, hisoblanadigan signal o'zgartirishlar bor:
chastotani siljitish (resample + OLA), spektral qiyalik (FFT gain),
formant masshtabi va F0 baholash (autokorrelyatsiya).
"""

from __future__ import annotations

import math
import wave
from pathlib import Path
from typing import Iterable

import numpy as np


class VoiceAudioError(ValueError):
    """Audio fayli yoki DSP parametri noto'g'ri."""


def safe_path(path: str | Path, root: str | Path | None = None,
              *, must_exist: bool = False) -> Path:
    """Fayl yo'lini ruxsat etilgan ildiz bilan cheklaydi.

    Sub-agentlardan keladigan namuna/chiqish yo'li tashqi faylni o'qish yoki
    tizim fayli ustiga yozish uchun ishlatilmasligi kerak. Symlink ham rad
    etiladi (commonpath faqat matnni tekshiradi, symlink uni aylanib o'tadi).
    """
    base = Path(root or Path.home()).resolve()
    raw = Path(path).expanduser()
    candidate = (raw if raw.is_absolute() else base / raw).resolve()
    if candidate.is_symlink() or raw.is_symlink():
        raise VoiceAudioError(f"Symlink yo'l taqiqlangan: {raw}")
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise VoiceAudioError(f"Yo'l ruxsat etilgan papkadan tashqarida: {raw}") from exc
    if must_exist and not candidate.is_file():
        raise VoiceAudioError(f"Fayl topilmadi: {candidate}")
    return candidate


def audio_energy(samples: np.ndarray) -> tuple[float, float]:
    """RMS va peak. Jim/sifatsiz namunani rad etish uchun ishlatiladi."""
    x = np.nan_to_num(np.asarray(samples, dtype=np.float32))
    if x.size == 0:
        return 0.0, 0.0
    return float(np.sqrt(np.mean(x * x))), float(np.max(np.abs(x)))


def read_wav(path: str | Path, *, root: str | Path | None = None) -> tuple[np.ndarray, int]:
    """WAV faylini mono float32 [-1, 1] massiv va namuna chastotasi sifatida o'qiydi.

    Jim (RMS < 1e-4) fayl rad etiladi — aks holda soxta 'muvaffaqiyatli'
    klonlash/convert natijasi olinadi.
    """
    p = safe_path(path, root, must_exist=True)
    with wave.open(str(p), "rb") as wf:
        sr = wf.getframerate()
        channels = wf.getnchannels()
        width = wf.getsampwidth()
        count = wf.getnframes()
        raw = wf.readframes(count)
    if sr <= 0 or count == 0:
        raise VoiceAudioError(f"WAV fayl bo'sh yoki noto'g'ri: {p}")
    if width == 1:
        data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    elif width == 2:
        data = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    elif width == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        packed = (b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)).astype(np.int32)
        packed = np.where(packed >= 1 << 23, packed - (1 << 24), packed)
        data = packed.astype(np.float32) / float(1 << 23)
    elif width == 4:
        data = np.frombuffer(raw, dtype="<i4").astype(np.float32) / float(1 << 31)
    else:
        raise VoiceAudioError(f"Qo'llab-quvvatlanmaydigan WAV sampwidth: {width}")
    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)
    data = np.ascontiguousarray(data, dtype=np.float32)
    rms, peak = audio_energy(data)
    if rms < 1e-4 or peak < 1e-3:
        raise VoiceAudioError(
            f"WAV jim yoki energy yo'q: rms={rms:.6f}, peak={peak:.6f} ({p})"
        )
    return data, sr


def wav_bytes(samples: np.ndarray, sample_rate: int) -> bytes:
    """float32 signaldan 16-bit PCM WAV baytlarini yaratadi (streaming uchun)."""
    import io

    arr = np.nan_to_num(np.asarray(samples, dtype=np.float32), nan=0.0, posinf=1.0, neginf=-1.0)
    arr = np.clip(arr, -1.0, 1.0)
    pcm = (arr * 32767.0).astype("<i2")
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(int(sample_rate))
        wf.writeframes(pcm.tobytes())
    return buffer.getvalue()


def write_wav(path: str | Path, samples: np.ndarray, sample_rate: int,
              *, root: str | Path | None = None) -> Path:
    """float32 signaldan 16-bit PCM WAV yozadi."""
    p = safe_path(path, root)
    rms, _peak = audio_energy(samples)
    if rms < 1e-4:
        raise VoiceAudioError("Chiqish jim bo'ladi — WAV yozilmadi")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(wav_bytes(samples, sample_rate))
    return p


def resample(samples: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
    """Chiziqli interpolatsiya bilan namuna chastotasini o'zgartiradi."""
    x = np.asarray(samples, dtype=np.float32)
    if src_rate <= 0 or dst_rate <= 0:
        raise VoiceAudioError("Namuna chastotasi musbat bo'lishi shart")
    if src_rate == dst_rate or len(x) < 2:
        return x.copy()
    new_len = max(2, int(round(len(x) * dst_rate / src_rate)))
    src_pos = np.linspace(0.0, len(x) - 1, new_len, dtype=np.float64)
    idx = np.floor(src_pos).astype(np.int64)
    frac = src_pos - idx
    upper = np.minimum(idx + 1, len(x) - 1)
    return (x[idx] * (1.0 - frac) + x[upper] * frac).astype(np.float32)


def time_stretch(samples: np.ndarray, rate: float) -> np.ndarray:
    """WSOLA: davomiylikni o'zgartiradi, pitch va garmonikalarni saqlaydi.

    Oddiy OLA qo'shni freymlarning fazasini moslashtirmagani uchun ovozda
    sun'iy rezonans paydo bo'ladi. WSOLA esa keyingi freymni oldingi freymning
    qoplash qismiga eng yaqin bo'lgan joydan qidiradi.
    """
    x = np.asarray(samples, dtype=np.float32)
    if rate <= 0:
        raise VoiceAudioError("time_stretch rate > 0 bo'lishi shart")
    if abs(rate - 1.0) < 1e-6 or len(x) < 2048:
        return x.copy()
    win = 1024
    hop_a = win // 4
    hop_s = max(1, int(round(hop_a / rate)))
    search = min(384, hop_a * 2)
    window = np.hanning(win).astype(np.float32)
    out_len = max(64, int(round(len(x) / rate)))
    acc = np.zeros(out_len + win, dtype=np.float32)
    norm = np.zeros(out_len + win, dtype=np.float32)
    prev_start: int | None = None
    target = 0
    out_pos = 0
    overlap_len = win - hop_s
    while target + win <= len(x) and out_pos < out_len:
        start = target
        if prev_start is not None:
            ref = x[prev_start + hop_s: prev_start + win]
            if len(ref) == overlap_len and np.dot(ref, ref) > 1e-9:
                best_score = -1e9
                best_delta = 0
                ref_norm = float(np.sqrt(np.dot(ref, ref)))
                for delta in range(-search, search + 1, 4):
                    cand_start = target + delta
                    if cand_start < 0 or cand_start + win > len(x):
                        continue
                    cand = x[cand_start: cand_start + overlap_len]
                    denom = float(np.sqrt(np.dot(cand, cand)))
                    if denom < 1e-9:
                        continue
                    score = float(np.dot(ref, cand)) / (ref_norm * denom)
                    if score > best_score:
                        best_score = score
                        best_delta = delta
                start = target + best_delta
        frame = x[start:start + win] * window
        end = out_pos + win
        if end > len(acc):
            break
        acc[out_pos:end] += frame
        norm[out_pos:end] += window
        prev_start = start
        target += hop_a
        out_pos += hop_s
    out = np.divide(acc, np.maximum(norm, 1e-6))
    return out[:out_len].astype(np.float32)


def pitch_shift(samples: np.ndarray, sample_rate: int, semitones: float) -> np.ndarray:
    """Chastotani yarim tonlarga siljitadi, davomiylikni taxminan saqlaydi."""
    if not -24.0 <= semitones <= 24.0:
        raise VoiceAudioError("pitch_shift diapazoni -24..24 yarim ton")
    x = np.asarray(samples, dtype=np.float32)
    if abs(semitones) < 1e-6 or len(x) < 64:
        return x.copy()
    factor = 2.0 ** (semitones / 12.0)
    # resample(src, sr, sr/factor) uzaytiradi emas, qisqartiradi -> pitch *factor.
    pitched = resample(x, sample_rate, max(1, int(round(sample_rate / factor))))
    restored_len = time_stretch(pitched, 1.0 / factor)
    return _fit_length(restored_len, len(x))


def formant_scale(samples: np.ndarray, sample_rate: int, scale: float) -> np.ndarray:
    """Vokal trakti hajmini o'zgartiradi (pitch asl holida qoladi)."""
    if not 0.6 <= scale <= 1.8:
        raise VoiceAudioError("formant_scale 0.6..1.8 oralig'ida bo'lishi shart")
    x = np.asarray(samples, dtype=np.float32)
    if abs(scale - 1.0) < 1e-6 or len(x) < 64:
        return x.copy()
    shifted = resample(x, sample_rate, max(1, int(round(sample_rate / scale))))
    pitch_back = pitch_shift(shifted, sample_rate, -12.0 * math.log2(scale))
    duration_back = time_stretch(pitch_back, 1.0 / scale)
    return _fit_length(duration_back, len(x))


def spectral_tilt(samples: np.ndarray, sample_rate: int, alpha: float, pivot_hz: float = 1000.0) -> np.ndarray:
    """Spektral qiyalikni o'zgartiradi: alpha > 0 yorqinroq, < 0 yumshoqroq."""
    if not -1.5 <= alpha <= 1.5:
        raise VoiceAudioError("spectral_tilt alpha -1.5..1.5 oralig'ida bo'lishi shart")
    x = np.asarray(samples, dtype=np.float32)
    if abs(alpha) < 1e-6 or len(x) < 64:
        return x.copy()
    spectrum = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1.0 / sample_rate)
    gain = np.power(np.maximum(freqs, 25.0) / pivot_hz, alpha)
    gain = np.clip(gain, 0.25, 4.0)
    return np.fft.irfft(spectrum * gain, n=len(x)).astype(np.float32)


def add_breath(samples: np.ndarray, sample_rate: int, amount: float, seed: int = 7) -> np.ndarray:
    """Shamolli/bolalar ovozi uchun yuqori chastotali nafas shovqini qo'shadi."""
    x = np.asarray(samples, dtype=np.float32)
    if amount <= 0 or len(x) < 64:
        return x.copy()
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(len(x)).astype(np.float32)
    high = noise - np.concatenate(([0.0], noise[:-1]))
    return (x + np.clip(amount, 0.0, 1.0) * 0.05 * high).astype(np.float32)


def normalize_peak(samples: np.ndarray, peak: float = 0.95) -> np.ndarray:
    x = np.asarray(samples, dtype=np.float32)
    top = float(np.max(np.abs(x))) if len(x) else 0.0
    if top < 1e-8:
        return x.copy()
    return (x * (peak / top)).astype(np.float32)


def silence(seconds: float, sample_rate: int) -> np.ndarray:
    return np.zeros(max(0, int(round(seconds * sample_rate))), dtype=np.float32)


def concat_clips(clips: Iterable[np.ndarray], sample_rate: int, gap_ms: int = 120) -> np.ndarray:
    items = [np.asarray(c, dtype=np.float32) for c in clips if len(c)]
    if not items:
        return np.zeros(0, dtype=np.float32)
    gap = silence(gap_ms / 1000.0, sample_rate)
    parts: list[np.ndarray] = []
    for idx, item in enumerate(items):
        if idx:
            parts.append(gap)
        parts.append(item)
    return np.concatenate(parts).astype(np.float32)


def _fit_length(samples: np.ndarray, length: int) -> np.ndarray:
    x = np.asarray(samples, dtype=np.float32)
    if len(x) == length:
        return x
    if len(x) > length:
        return x[:length].copy()
    return np.pad(x, (0, length - len(x))).astype(np.float32)


def estimate_f0(samples: np.ndarray, sample_rate: int, fmin: float = 70.0, fmax: float = 400.0) -> float:
    """FFT cho'qqisi bilan asosiy chastotani (Hz) baholaydi. Ovoz yo'q -> 0.0."""
    x = np.asarray(samples, dtype=np.float32)
    if len(x) < sample_rate // 10:
        return 0.0
    frame = int(sample_rate * 0.25)
    hop = int(sample_rate * 0.125)
    candidates: list[float] = []
    for start in range(0, max(1, len(x) - frame + 1), hop):
        seg = x[start:start + frame]
        seg = seg - np.mean(seg)
        if float(np.sqrt(np.mean(seg ** 2))) < 0.005:
            continue
        n = 1 << (len(seg) - 1).bit_length()
        spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), n=n))
        freqs = np.fft.rfftfreq(n, 1.0 / sample_rate)
        band = (freqs >= fmin) & (freqs <= fmax)
        if not np.any(band):
            continue
        idx = np.where(band)[0][int(np.argmax(spec[band]))]
        peak = float(spec[idx])
        if peak < 1e-4:
            continue
        # kvadratik interpolatsiya bilan aniqroq cho'qqi
        left = spec[idx - 1] if idx > 0 else peak
        right = spec[idx + 1] if idx + 1 < len(spec) else peak
        denom = left - 2.0 * peak + right
        shift = 0.5 * (left - right) / denom if abs(denom) > 1e-12 else 0.0
        shift = float(np.clip(shift, -1.0, 1.0))
        resolved = (idx + shift) * sample_rate / n
        candidates.append(resolved)
    if not candidates:
        return 0.0
    return float(np.median(candidates))


def spectral_balance_db(samples: np.ndarray, sample_rate: int) -> float:
    """2-6 kHz energiyasining 0.2-1 kHz ga nisbatini dB da qaytaradi."""
    x = np.asarray(samples, dtype=np.float32)
    if len(x) < 256:
        return 0.0
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
    freqs = np.fft.rfftfreq(len(x), 1.0 / sample_rate)
    low = float(np.sum(spec[(freqs >= 200) & (freqs < 1000)]))
    high = float(np.sum(spec[(freqs >= 2000) & (freqs <= 6000)]))
    if low <= 1e-12 or high <= 1e-12:
        return 0.0
    return float(10.0 * math.log10(high / low))


def analyze_voice(samples: np.ndarray, sample_rate: int) -> dict[str, float]:
    """Namunadan F0, spektral muvozanat, RMS va davomiylikni hisoblaydi."""
    x = np.asarray(samples, dtype=np.float32)
    return {
        "f0_hz": round(estimate_f0(x, sample_rate), 2),
        "spectral_balance_db": round(spectral_balance_db(x, sample_rate), 2),
        "rms": round(float(np.sqrt(np.mean(x ** 2))) if len(x) else 0.0, 6),
        "duration_s": round(len(x) / sample_rate, 3),
        "sample_rate": int(sample_rate),
    }
