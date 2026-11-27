"""Xavfsizlik va halollik testlari: rozilik, yo'l, jim audio, soxta PASS.

Bular auditda topilgan haqiqiy kamchiliklarning regressiya testlaridir.
Tuzatishsiz bu testlar yiqiladi.
"""

from __future__ import annotations

import wave

import numpy as np
import pytest

from voice.audio import VoiceAudioError, read_wav, safe_path, wav_bytes, write_wav
from voice.engine import VoiceEngine


def _silent_wav(path, seconds=1.0, sr=16000):
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(b"\x00\x00" * int(seconds * sr))
    return path


def test_silent_reference_wav_rejected(tmp_path):
    silent = _silent_wav(tmp_path / "silent.wav")
    with pytest.raises(VoiceAudioError, match="jim|energy"):
        read_wav(silent, root=tmp_path)


def test_silent_output_not_written(tmp_path):
    with pytest.raises(VoiceAudioError, match="jim"):
        write_wav(tmp_path / "out.wav", np.zeros(1600, dtype=np.float32), 16000,
                  root=tmp_path)
    assert not (tmp_path / "out.wav").exists()


def test_path_traversal_rejected(tmp_path):
    outside = tmp_path.parent / "outside.wav"
    with pytest.raises(VoiceAudioError, match="tashqarida"):
        safe_path("../outside.wav", root=tmp_path)
    with pytest.raises(VoiceAudioError, match="tashqarida"):
        safe_path(outside, root=tmp_path)


def test_clone_requires_consent(tmp_path):
    engine = VoiceEngine(output_dir=tmp_path, allowed_root=tmp_path)
    ref = tmp_path / "ref.wav"
    ref.write_bytes(wav_bytes(np.sin(np.linspace(0, 100, 16000)) * 0.2, 16000))
    with pytest.raises(PermissionError, match="CONSENT_REQUIRED"):
        engine.clone("Salom", ref)
    with pytest.raises(PermissionError, match="CONSENT_REQUIRED"):
        engine.clone("Salom", ref, consent=True, consent_id="")


def test_convert_rejects_silent_source(tmp_path):
    engine = VoiceEngine(output_dir=tmp_path, allowed_root=tmp_path)
    silent = _silent_wav(tmp_path / "silent.wav")
    with pytest.raises(VoiceAudioError, match="jim"):
        engine.convert(silent, "boy")


def test_safe_path_accepts_inside_root(tmp_path):
    assert safe_path("sub/out.wav", root=tmp_path) == tmp_path / "sub" / "out.wav"
