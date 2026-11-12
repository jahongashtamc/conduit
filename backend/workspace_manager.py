import os
import shutil
from pathlib import Path

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKSPACES_ROOT = os.path.join(BASE_DIR, "workspaces")
os.makedirs(WORKSPACES_ROOT, exist_ok=True)

class SecurityViolation(Exception):
    """Xavfsizlik chegarasini buzishga urinishda chaqiriladi."""
    pass

def get_agent_workspace(agent_id: str) -> str:
    """Subagent uchun izolyatsiyalangan workspace papkasi yo'lini qaytaradi va mavjudligini ta'minlaydi."""
    clean_id = agent_id.strip().lower()
    ws_path = os.path.abspath(os.path.join(WORKSPACES_ROOT, clean_id))
    os.makedirs(ws_path, exist_ok=True)
    return ws_path

get_workspace_path = get_agent_workspace

def resolve_safe_path(agent_id: str, target_relative_path: str) -> str:
    """
    Subagent bergan yo'lni tekshiradi.
    Agar yo'l subagentning o'z workspace papkasidan tashqariga chiqsa (Path Traversal),
    darhol SecurityViolation chiqariladi.
    """
    ws_dir = Path(get_agent_workspace(agent_id)).resolve()
    
    # Absolute yoki relative yo'lni workspace ga nisbatan bog'lash
    target = (ws_dir / target_relative_path).resolve()

    # Tekshirish: target yo'li ws_dir ichida bo'lishi shart
    try:
        target.relative_to(ws_dir)
    except ValueError:
        raise SecurityViolation(
            f"XAVFSIZLIK TO'SIg'I: '{agent_id}' subagenti o'z ish joyidan tashqariga ({target}) chiqishga urindi! Rad etildi."
        )

    return str(target)

def write_agent_file(agent_id: str, relative_path: str, content: str) -> str:
    """Faqat subagentning o'z papkasiga xavfsiz yozadi."""
    safe_path = resolve_safe_path(agent_id, relative_path)
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)
    with open(safe_path, "w", encoding="utf-8") as f:
        f.write(content)
    return safe_path

def read_agent_file(agent_id: str, relative_path: str) -> str:
    """Faqat subagentning o'z papkasidan xavfsiz o'qiydi."""
    safe_path = resolve_safe_path(agent_id, relative_path)
    if not os.path.exists(safe_path):
        raise FileNotFoundError(f"Fayl topilmadi: {relative_path}")
    with open(safe_path, "r", encoding="utf-8") as f:
        return f.read()

def delete_agent_file(agent_id: str, relative_path: str) -> bool:
    """Subagent papkasi ichidagi faylni o'chiradi (tasdiq olingandan keyin chaqiriladi)."""
    safe_path = resolve_safe_path(agent_id, relative_path)
    if os.path.exists(safe_path):
        if os.path.isdir(safe_path):
            shutil.rmtree(safe_path)
        else:
            os.remove(safe_path)
        return True
    return False

def list_agent_files(agent_id: str) -> list:
    """Subagent papkasidagi barcha fayllarni qaytaradi."""
    ws_dir = get_agent_workspace(agent_id)
    files = []
    for root, _, filenames in os.walk(ws_dir):
        for f in filenames:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, ws_dir)
            files.append(rel_path)
    return files
