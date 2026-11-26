import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools as conduit_tools  # noqa: E402

from voice.tools_adapter import voice_tool  # noqa: E402


def test_voice_tools_registered_in_conduit_catalog():
    names = {spec[0] for spec in conduit_tools.TOOL_SPECS}
    expected = {"voice_speak", "voice_clone", "voice_convert", "voice_doctor", "voice_catalog"}
    assert expected <= names
    assert conduit_tools.canonical_tool_name("speak") == "voice_speak"
    assert conduit_tools.canonical_tool_name("clone_voice") == "voice_clone"


def test_voice_doctor_adapter():
    result = voice_tool("voice_doctor", [])
    assert result["success"] is True
    assert result["report"]["ok"] is True


def test_voice_catalog_adapter():
    result = voice_tool("voice_catalog", [])
    assert result["success"] is True
    assert len(result["categories"]) >= 8
    assert result["capabilities"]["neural_clone"] is False


def test_cli_tool_call_from_backend(tmp_path):
    out = tmp_path / "cli.wav"
    proc = subprocess.run(
        [sys.executable, str(BACKEND / "tools.py"), "voice_speak",
         "Salom dunyo", "boy", "auto", str(out)],
        cwd=str(ROOT), capture_output=True, text=True, timeout=300,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["success"] is True
    assert payload["backend"] == "onnx"
    assert out.is_file() and out.stat().st_size > 10000
