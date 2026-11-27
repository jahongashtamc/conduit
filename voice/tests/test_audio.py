import numpy as np
import pytest

from voice.audio import (
    analyze_voice,
    estimate_f0,
    formant_scale,
    pitch_shift,
    read_wav,
    spectral_balance_db,
    spectral_tilt,
    time_stretch,
    wav_bytes,
    write_wav,
)
from voice.profiles import apply_params, get_category


SR = 16000


def sine(freq=200.0, seconds=2.0, sr=SR):
    t = np.arange(int(sr * seconds)) / sr
    return (0.5 * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def test_wav_roundtrip(tmp_path):
    path = tmp_path / "a.wav"
    write_wav(path, sine(), SR, root=tmp_path)
    samples, sr = read_wav(path, root=tmp_path)
    assert sr == SR
    assert len(samples) > SR
    assert np.max(np.abs(samples)) > 0.1
    assert wav_bytes(samples, sr)[:4] == b"RIFF"


def test_estimate_f0_on_sine():
    assert abs(estimate_f0(sine(200), SR) - 200) < 5


@pytest.mark.parametrize(("semitones", "factor"), [(12, 2.0), (-12, 0.5)])
def test_pitch_shift_direction(semitones, factor):
    shifted = pitch_shift(sine(200), SR, semitones)
    measured = estimate_f0(shifted, SR)
    assert abs(measured - 200 * factor) < 12


def test_time_stretch_changes_length_not_pitch():
    original = sine(200)
    stretched = time_stretch(original, 0.75)
    assert len(stretched) > len(original) * 1.2
    assert abs(estimate_f0(stretched, SR) - 200) < 12


def test_formant_scale_keeps_pitch():
    shifted = formant_scale(sine(200), SR, 1.1)
    assert abs(estimate_f0(shifted, SR) - 200) < 12


def test_spectral_tilt_changes_balance():
    original = sine(200) + 0.02 * np.random.default_rng(3).standard_normal(SR * 2)
    before = spectral_balance_db(original.astype(np.float32), SR)
    brighter = spectral_tilt(original.astype(np.float32), SR, 0.5)
    after = spectral_balance_db(brighter, SR)
    assert after > before


def test_analyze_voice_fields():
    report = analyze_voice(sine(200), SR)
    assert report["sample_rate"] == SR
    assert report["duration_s"] > 1.9
    assert report["rms"] > 0.1


def test_category_conversion_changes_f0(tmp_path):
    source = tmp_path / "source.wav"
    write_wav(source, sine(200, seconds=1.5), SR, root=tmp_path)
    base, sr = read_wav(source, root=tmp_path)
    _, boy = get_category("boy")
    _, deep = get_category("deep")
    boy_audio = apply_params(base, sr, boy)
    deep_audio = apply_params(base, sr, deep)
    assert estimate_f0(boy_audio, sr) > estimate_f0(base, sr)
    assert estimate_f0(deep_audio, sr) < estimate_f0(base, sr)
