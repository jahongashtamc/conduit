import os

import pytest

from voice.audio import analyze_voice, read_wav
from voice.engine import VoiceEngine

# ONNX modellari (114 MB × 2) git'da saqlanmaydi: ular `voice/models/downloads.json`
# dagi sha256 bo'yicha yuklab olinadi. Toza checkout'da (CI) fayl yo'q, shuning
# uchun model talab qiladigan testlar SKIP bo'lishi shart — yiqilishi emas.
# O'lchangan: CI run 46019392258 da 9 ta test shu sababdan yiqilgan.
_MODEL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models"
)
_HAS_MALE = os.path.isfile(os.path.join(_MODEL_DIR, "male", "onnx", "model.onnx"))
_HAS_FEMALE = os.path.isfile(os.path.join(_MODEL_DIR, "female", "onnx", "model.onnx"))

requires_models = pytest.mark.skipif(
    not (_HAS_MALE and _HAS_FEMALE),
    reason="ONNX modellari yuklanmagan (voice/models/downloads.json bo'yicha oling)",
)


@pytest.fixture(scope="module")
def engine():
    return VoiceEngine()


@requires_models
def test_doctor_reports_real_state(engine):
    report = engine.doctor()
    assert report["ok"] is True
    assert report["can_synthesize_uz"] is True
    assert report["neural_clone"] is False
    assert report["clone_mode"] == "stylized"
    assert any(check["name"].startswith("model:") for check in report["checks"])


def test_catalog(engine):
    models = engine.list_models()
    assert {item["id"] for item in models} == {"uz_male_mms", "uz_female_mms"}
    ids = {item["id"] for item in engine.list_categories()}
    assert {"boy", "girl", "child", "elderly"} <= ids


@requires_models
def test_real_uzbek_synthesis(engine, tmp_path):
    out = tmp_path / "salom.wav"
    result = engine.synthesize("Salom dunyo! Bu haqiqiy sinov.", category="girl", out_path=out)
    assert result.success
    assert result.backend == "onnx"
    assert result.model == "uz_female_mms"
    assert result.sample_rate == 16000
    assert out.is_file() and out.stat().st_size > 10000
    samples, sr = read_wav(out)
    assert analyze_voice(samples, sr)["rms"] > 0.01


@requires_models
def test_clone_is_honestly_marked(engine, tmp_path):
    source = tmp_path / "namuna.wav"
    engine.synthesize("Bu namuna ovoz.", category="male", out_path=source)
    out = tmp_path / "klon.wav"
    result = engine.clone(
        "Salom", source, category="boy", out_path=out,
        consent=True, consent_id="test_consent_001",
    )
    assert result.success
    assert result.clone_mode == "stylized"
    assert result.neural_clone is False
    assert result.synthetic is True
    assert out.is_file() and out.stat().st_size > 5000


@requires_models
def test_stream_emits_valid_wav_chunks(engine):
    chunks = list(engine.stream("Birinchi gap. Ikkinchi gap.", category="boy", chunk_ms=200))
    assert len(chunks) >= 3
    assert all(chunk[:4] == b"RIFF" for chunk in chunks)
    assert all(chunk[8:12] == b"WAVE" for chunk in chunks)
    assert sum(len(chunk) for chunk in chunks) > 10000
