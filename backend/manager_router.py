import re
from typing import Dict, Any, Tuple

def route_task(prompt: str, requested_agent: str = None) -> Tuple[str, str]:
    """
    Manager vazifani tahlil qiladi va tegishli subagentga yo'naltiradi.
    Manager o'zi ish bajarmaydi, faqat delegatsiya qiladi.
    
    Qaytaradi: (target_agent_id, routing_reason)
    """
    if requested_agent and requested_agent.lower() != "auto":
        return requested_agent.lower(), f"Foydalanuvchi to'g'ridan-to'g'ri '{requested_agent}' subagentini tanladi."

    p_lower = prompt.lower()

    # Ko'p bosqichli vazifalar (qidirish + tekshirish) -> Bosh Agent (Miya + Yurak)
    has_search = any(k in p_lower for k in ["qidir", "search", "google", "yig'ib", "topib"])
    has_test = any(k in p_lower for k in ["tekshir", "audit", "sinov", "verify"])
    if (has_search and has_test) or "miya" in p_lower or "bosh agent" in p_lower:
        return "brain", "Vazifada bir nechta bosqich (qidirish + audit) aniqlandi -> Bosh Agent (Miya + Yurak) ga topshirildi."

    # Browser / Web / Search -> Scout
    if any(k in p_lower for k in [
        "brauzer", "browser", "web", "sayt", "url", "qidir", "search", "google",
        "internet", "html", "scrape", "screenshot", "sahifa", "navigate", "http"
    ]):
        return "scout", "Vazifada veb/brauzer harakatlari aniqlandi -> Scout agentiga yo'naltirildi."

    # Test / Audit / Health / Verify -> Inspector
    if any(k in p_lower for k in [
        "test", "audit", "tekshir", "sinov", "inspector", "health", "probe",
        "verify", "pass", "fail", "status", "xato", "diagnostika"
    ]):
        return "inspector", "Vazifada tizim tekshiruvi va sinov talab etildi -> Inspector agentiga yo'naltirildi."

    # 3D / Blender -> Sculptor
    if any(k in p_lower for k in ["blender", "3d", "model", "render", "mesh", "sculpt"]):
        return "sculptor", "3D modellashtirish vazifasi -> Sculptor subagenti (Faza 4)."

    # After Effects -> Animator
    if any(k in p_lower for k in ["animat", "after effects", "vfx", "motion"]):
        return "animator", "Harakatli grafika vazifasi -> Animator subagenti (Faza 4)."

    # Video Editing -> Editor
    if any(k in p_lower for k in ["davinci", "premiere", "video", "montaj", "clip"]):
        return "editor", "Videomontaj vazifasi -> Editor subagenti (Faza 4)."

    # Photoshop -> Painter
    if any(k in p_lower for k in ["photoshop", "rasm", "tekstura", "paint", "art"]):
        return "painter", "Rastrli grafika vazifasi -> Painter subagenti (Faza 4)."

    # Figma -> Designer
    if any(k in p_lower for k in ["figma", "dizayn", "design", "ui", "ux", "maket"]):
        return "designer", "Dizayn vazifasi -> Designer subagenti (Faza 4)."

    # Default fallback to Scout for general research
    return "scout", "Umumiy tahlil va tadqiqot vazifasi -> Standart bo'yicha Scout subagentiga yo'naltirildi."

KNOWN_UNLISTED_APPS = {
    "notion": {
        "id": "notion",
        "name": "Notion",
        "category": "Productivity",
        "official_source": "https://www.notion.so/desktop"
    },
    "unreal": {
        "id": "unreal",
        "name": "Unreal Engine",
        "category": "3D & Game Engine",
        "official_source": "https://www.unrealengine.com"
    },
    "cinema4d": {
        "id": "cinema4d",
        "name": "Cinema 4D",
        "category": "3D & Motion",
        "official_source": "https://www.maxon.net"
    },
    "vscode": {
        "id": "vscode",
        "name": "Visual Studio Code",
        "category": "Development",
        "official_source": "https://code.visualstudio.com"
    },
    "slack": {
        "id": "slack",
        "name": "Slack",
        "category": "Communication",
        "official_source": "https://slack.com"
    },
    "telegram": {
        "id": "telegram",
        "name": "Telegram",
        "category": "Communication",
        "official_source": "https://desktop.telegram.org"
    },
    "godot": {
        "id": "godot",
        "name": "Godot Engine",
        "category": "Game Engine",
        "official_source": "https://godotengine.org"
    }
}

def detect_unlisted_app(prompt: str):
    """Vazifada ro'yxatda yo'q ilova talab qilinganini aniqlaydi."""
    p_lower = prompt.lower()
    for app_id, meta in KNOWN_UNLISTED_APPS.items():
        if app_id in p_lower or meta["name"].lower() in p_lower:
            from apps_manager import get_apps_status
            existing = [a.get("id") for a in get_apps_status()]
            if app_id not in existing:
                return meta
    return None

