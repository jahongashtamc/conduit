import json
import os
from typing import Tuple

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_SPECIAL_AGENTS = frozenset({
    "brain", "manager", "super_agent", "superagent", "swarm",
    "commander", "auto",
})


def known_agent_ids() -> frozenset:
    """Haqiqiy subagentlar + maxsus rejimlar (katalog bilan bir xil manba).

    Kesh ishlatilmaydi: yangi subagent papkasi qo'shilganda uni darrov ko'rish
    kerak. Papka soni kichik (~20), skan qilish arzon. Eski `lru_cache` tufayli
    ishga tushgandan keyin qo'shilgan `voice` subagenti "noma'lum" bo'lib qolgan.
    """
    ids = set(_SPECIAL_AGENTS)
    subagents_dir = os.path.join(_PROJECT_ROOT, "subagents")
    if not os.path.isdir(subagents_dir):
        return frozenset(ids)
    for name in os.listdir(subagents_dir):
        folder = os.path.join(subagents_dir, name)
        if not os.path.isdir(folder):
            continue
        manifest = os.path.join(folder, "app.json")
        agent_id = name
        if os.path.isfile(manifest):
            try:
                with open(manifest, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                agent_id = str(data.get("id") or data.get("name") or name)
            except (OSError, ValueError) as exc:
                # Noto'g'ri manifest jim yutilmaydi, lekin papka nomi ishlatiladi.
                import logging
                logging.getLogger("nexus.manager_router").warning(
                    "Subagent manifesti o'qilmadi (%s): %s", manifest, exc
                )
        ids.add(agent_id.lower())
    return frozenset(ids)


def validate_agent_id(requested_agent: str = None) -> str:
    """Foydalanuvchi so'ragan agent borligini tasdiqlaydi."""
    if not requested_agent:
        return ""
    agent_id = str(requested_agent).strip().lower()
    if not agent_id or agent_id == "auto":
        return ""
    if agent_id not in known_agent_ids():
        raise ValueError(
            f"Noma'lum subagent: '{requested_agent}'. "
            "Mavjud agentlar: " + ", ".join(sorted(known_agent_ids()))
        )
    return agent_id


def route_task(prompt: str, requested_agent: str = None) -> Tuple[str, str]:
    """
    Manager vazifani tahlil qiladi va tegishli subagentga yo'naltiradi.
    Manager o'zi ish bajarmaydi, faqat delegatsiya qiladi.

    Qaytaradi: (target_agent_id, routing_reason)
    """
    if requested_agent and requested_agent.lower() != "auto":
        return requested_agent.lower(), f"Foydalanuvchi to'g'ridan-to'g'ri '{requested_agent}' subagentini tanladi."

    p_lower = prompt.lower()

    # FAQAT natijasi aniq bo'lgan, LLM plannersiz bajariladigan vazifalar
    # tez instrument agentlariga yo'naltiriladi (0.2-7s vs 110-360s).
    # Avval bu yo'l umuman yo'q edi: `inst_*` agentlar faqat aniq nom bilan
    # chaqirilardi, oddiy "rasm yarat" so'rovi esa 2-6 daqiqalik rol-agentga
    # ketardi. Shart: matnda aniq vosita va aniq obyekt bo'lishi.
    image_hint = any(k in p_lower for k in [
        "rasm yarat", "rasm chiz", "png yarat", "jpg yarat", "surat yarat",
        "gen_image", "tasvir yarat", "image generate",
    ])
    if image_hint and not any(k in p_lower for k in ["blender", "3d", "render", "video", "figma"]):
        return "inst_image", "Aniq rasm yaratish so'rovi -> inst_image (PIL, tez yo'l)."

    blender_hint = any(k in p_lower for k in ["blender", "3d model", "3d render", "sculpt"])
    if blender_hint:
        return "inst_blender", "Blender/bpy so'rovi -> inst_blender (headless, tez yo'l)."

    video_hint = any(k in p_lower for k in ["video yig'", "mp4 yarat", "montaj qil", "gif yarat"])
    if video_hint and any(k in p_lower for k in [".mp4", "klip", "kadr"]):
        return "inst_video", "Video/GIF yig'ish so'rovi -> inst_video (FFmpeg, tez yo'l)."

    # Asboblar qidiruvi va tahlili (Tools Engine / DeepSearch + DeepX)
    if any(k in p_lower for k in [
        "asbob top", "asbob qidir", "asboblar top", "tool top", "tool search", 
        "find tool", "nomzod top", "uchun asbob", "uchun tool"
    ]):
        return "scout", "Vazifada asboblar tadqiqoti (DeepSearch + DeepX) aniqlandi -> Scout agentiga yo'naltirildi."

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
