import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine import cli_runner
from manager_router import detect_unlisted_app
from subagent_creator import create_dynamic_subagent, SUBAGENTS_ROOT
import apps_manager

def test_model_error_detection_429():
    """Test 1: Model 429 rate limit error detection"""
    output_sample = "Error: API Error 429: Rate limit reached for model claude-3-5-sonnet. Please wait."
    err_msg = cli_runner.check_model_error(output_sample)
    assert err_msg is not None
    assert "429" in err_msg or "rate limit" in err_msg.lower()

def test_model_error_detection_unrecognized_and_cooldown():
    """Test 2: Unrecognized model and cooldown detection"""
    out1 = "Error 404: unrecognized model 'unknown-ai-model-v9'"
    err_msg1 = cli_runner.check_model_error(out1)
    assert err_msg1 is not None
    assert "Tanilmagan model" in err_msg1 or "unrecognized" in err_msg1.lower()

    out2 = "Provider notice: the endpoint is cooling down for 60 seconds."
    err_msg2 = cli_runner.check_model_error(out2)
    assert err_msg2 is not None
    assert "429" in err_msg2 or "cooling down" in err_msg2.lower()

def test_model_error_detection_auth_401():
    """Test 2b: 401/auth credential xatolari aniqlanishi shart — aks holda
    fallback modelga o'tish ishga tushmaydi (haqiqiy holat: kiro 'No active
    credentials' -> to'g'ridan-to'g'ri BLOCKED, fallback o'tmagan edi)."""
    samples = [
        "Failed to authenticate. API Error: 401 No active credentials for provider: kiro.",
        '{"error":{"type":"authentication_error","code":"invalid_api_key"}}',
        "API Error: 401 invalid_api_key",
    ]
    for sample in samples:
        err_msg = cli_runner.check_model_error(sample)
        assert err_msg is not None, f"Auth xatosi aniqlanmadi: {sample[:60]}"
        assert "Auth xatosi" in err_msg or "401" in err_msg


def test_evidence_validation_rejects_fake_localhost_for_figma():
    """Test 3: Reject fake/mismatched evidence (localhost:3000 for Figma tasks)"""
    # Figma task with web localhost screenshot should be rejected as FALSE PASS
    is_valid, reason = cli_runner.validate_evidence_against_goal(
        goal="Figma dizayn tizimini tuzat va PC app spec yarat",
        subagent="designer",
        evidence="http://localhost:3000 sahifasi tekshirildi",
        screenshot_path="http://localhost:3000/scout_localhost_3000.png"
    )
    assert is_valid is False
    assert "Yolg'on dalil rad etildi" in reason or "Figma" in reason

def test_evidence_validation_accepts_valid_domain_evidence(tmp_path):
    """Test 4: Accept valid evidence matching task goal"""
    google_shot = tmp_path / "scout_google_result.png"
    google_shot.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 128)
    is_valid_web, reason_web = cli_runner.validate_evidence_against_goal(
        goal="Google'dan Conduit haqida qidir, skrinshot ol",
        subagent="scout",
        evidence=f"Google qidiruv natijalari skrinshot olindi {google_shot}",
        screenshot_path=str(google_shot)
    )
    assert is_valid_web is True

    figma_shot = tmp_path / "conduit_figma_artboard.png"
    figma_shot.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 128)
    is_valid_figma, reason_figma = cli_runner.validate_evidence_against_goal(
        goal="Figma dizayn tizimini tekshir",
        subagent="designer",
        evidence=f"figma.com/design/conduit-tokens spec yaratildi {figma_shot}",
        screenshot_path=str(figma_shot)
    )
    assert is_valid_figma is True

def test_detect_unlisted_app():
    """Test 5: Detect unlisted app requirement from prompt"""
    app_info = detect_unlisted_app("Telegram kanalidan eng so'nggi xabarni ol va tekshir")
    assert app_info is not None
    assert app_info["id"] == "telegram"
    assert app_info["name"] == "Telegram"

def test_dynamic_subagent_creation():
    """Test 6: On-demand app addition scaffolds subagents and workspace"""
    res = create_dynamic_subagent("slack", "Slack", "Team Communication")
    assert res is True
    
    subagent_dir = os.path.join(SUBAGENTS_ROOT, "slack")
    assert os.path.exists(os.path.join(subagent_dir, "app.json"))
    assert os.path.exists(os.path.join(subagent_dir, "role.md"))
    assert os.path.exists(os.path.join(subagent_dir, "inner", "planner.md"))

    # Verify registered in apps.json
    all_apps = apps_manager.get_apps_status()
    assert any(a.get("id") == "slack" for a in all_apps)

def test_engine_explicit_models_and_fallback():
    """Test 7: engine.json aniq model va fallback_model ko'rsatishi kerak.

    Model nomining o'zi tekshirilmaydi (provayderga qarab o'zgaradi);
    ikkala maydon ham bo'sh bo'lmasligi muhim.
    """
    cfg = cli_runner.load_engine_config()
    engines = cfg.get("engines", {})
    assert "claude_code" in engines
    # OmniRoute olib tashlangandan keyin claude/codex o'z CLI default
    # modelidan foydalanadi — model bo'sh bo'lishi mumkin (bu ataylab).
    # agy esa aniq model talab qiladi (agy --model flag bilan chaqiriladi).
    assert "agy" in engines
    assert engines["agy"].get("model"), "agy uchun model ko'rsatilmagan"
    # Model ko'rsatilgan dvigatellarda fallback ham ko'rsatilishi shart
    for key, meta in engines.items():
        if meta.get("model") and meta.get("fallback_model"):
            assert meta["model"] != meta["fallback_model"], f"{key}: fallback asosiy modeldan farq qilishi kerak"
