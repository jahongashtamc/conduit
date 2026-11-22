"""Agent subprocesslari uchun izolyatsiyalangan konfiguratsiya.

Maqsad: Conduit chaqirgan agent global MCP serverlarni yuklamasin.
Foydalanuvchining asl ~/.gemini konfiguratsiyasiga HECH QANDAY o'zgartirish kiritilmaydi:
faqat auth fayllari vaqtinchalik HOME ichiga nusxalanadi, mcp_config bo'sh yoziladi.
Maxfiy kalitlar loglarga chiqarilmaydi.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from typing import Dict

_AUTH_FILES = ("oauth_creds.json", "google_accounts.json", "installation_id")
_CONFIG_FILES = ("config.json",)


def isolated_home(enabled: bool) -> Dict[str, str]:
    """Izolyatsiyalangan HOME/USERPROFILE qaytaradi (yoqilmagan bo'lsa bo'sh dict)."""
    if not enabled:
        return {}
    root = os.path.join(tempfile.gettempdir(), "nexus-agent-home")
    cfg = os.path.join(root, ".gemini", "config")
    os.makedirs(cfg, exist_ok=True)
    with open(os.path.join(cfg, "mcp_config.json"), "w", encoding="utf-8") as fh:
        json.dump({"mcpServers": {}}, fh)
    real_home = os.path.expanduser("~")
    for name in _AUTH_FILES + _CONFIG_FILES:
        if os.path.isfile(os.path.join(cfg, name)):
            continue
        for src in (
            os.path.join(real_home, ".gemini", name),
            os.path.join(real_home, ".gemini", "config", name),
        ):
            if os.path.isfile(src):
                shutil.copyfile(src, os.path.join(cfg, name))
                break
    return {"USERPROFILE": root, "HOME": root}
