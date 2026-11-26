import pytest

from voice.audio import analyze_voice, read_wav
from voice.engine import VoiceEngine


@pytest.fixture(scope="module")
def engine():
    return VoiceEngine()


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


def test_stream_emits_valid_wav_chunks(engine):
    chunks = list(engine.stream("Birinchi gap. Ikkinchi gap.", category="boy", chunk_ms=200))
    assert len(chunks) >= 3
    assert all(chunk[:4] == b"RIFF" for chunk in chunks)
    assert all(chunk[8:12] == b"WAVE" for chunk in chunks)
    assert sum(len(chunk) for chunk in chunks) > 10000
