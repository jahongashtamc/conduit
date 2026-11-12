import os
import re
from typing import Set, Tuple, Optional

SUBAGENTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "subagents"))

class ToolNotPermittedError(Exception):
    """Subagent ruxsat etilmagan toolni chaqirmoqchi bo'lganda chiqariladi."""
    pass

class DangerousActionPending(Exception):
    """Xavfli amal uchun inson tasdig'i talab etilganda chiqariladi."""
    pass

SECRET_PATTERNS = [
    (re.compile(r'(api[_-]?key\s*[:=]\s*["\']?)([^"\'\s]{8,})', re.IGNORECASE), r'\1[REDACTED_SECRET]'),
    (re.compile(r'(secret[_-]?key\s*[:=]\s*["\']?)([^"\'\s]{8,})', re.IGNORECASE), r'\1[REDACTED_SECRET]'),
    (re.compile(r'(password\s*[:=]\s*["\']?)([^"\'\s]{4,})', re.IGNORECASE), r'\1[REDACTED_SECRET]'),
    (re.compile(r'(bearer\s+)([a-zA-Z0-9_\-\.]{15,})', re.IGNORECASE), r'\1[REDACTED_SECRET]'),
    (re.compile(r'(token\s*[:=]\s*["\']?)([^"\'\s]{10,})', re.IGNORECASE), r'\1[REDACTED_SECRET]'),
    (re.compile(r'sk-[a-zA-Z0-9]{15,}', re.IGNORECASE), '[REDACTED_SECRET]'),
]

def sanitize_text(text: str) -> str:
    """Barcha maxfiy kalitlar, parollar va tokenlarni [REDACTED_SECRET] bilan almashtiradi."""
    if not text:
        return text
    clean = text
    for pattern, repl in SECRET_PATTERNS:
        clean = pattern.sub(repl, clean)
    return clean

def get_allowed_tools(agent_id: str) -> Set[str]:
    """Subagentning role.md faylidan ruxsat etilgan toollar ro'yxatini ajratib oladi."""
    clean_id = agent_id.strip().lower()
    role_file = os.path.join(SUBAGENTS_DIR, clean_id, "role.md")
    
    if not os.path.exists(role_file):
        return set()

    allowed = set()
    try:
        with open(role_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        in_tools_section = False
        for line in lines:
            line_str = line.strip()
            if line_str.startswith("## Ruxsat etilgan toollar") or line_str.startswith("## Allowed Tools"):
                in_tools_section = True
                continue
            elif line_str.startswith("## ") and in_tools_section:
                in_tools_section = False
                break
            
            if in_tools_section:
                match = re.match(r"^[-*]\s*`?([a-zA-Z0-9_\-]+)`?", line_str)
                if match:
                    allowed.add(match.group(1).lower())
    except Exception as e:
        print(f"Error reading role.md for {agent_id}: {e}")

    return allowed

def verify_tool_access(agent_id: str, tool_name: str) -> bool:
    """
    Subagent uchun ushbu tool role.md da ruxsat etilganini tekshiradi.
    Agar ro'yxatda bo'lmasa, ToolNotPermittedError chiqaradi.
    """
    clean_tool = tool_name.strip().lower()
    allowed = get_allowed_tools(agent_id)
    
    if clean_tool not in allowed:
        raise ToolNotPermittedError(
            f"XAVFSIZLIK TO'SIG'I: '{agent_id}' subagenti ruxsat etilmagan '{clean_tool}' toolini chaqirishga urindi! "
            f"Faqat role.md dagi toollar ruxsat etilgan: {list(allowed)}"
        )
    return True

def inspect_danger_level(action_type: str, details: dict) -> Tuple[bool, Optional[str]]:
    """
    Amalning xavflilik darajasini tekshiradi:
    - Fayl o'chirish (delete_file, rmdir)
    - Workspace tashqarisiga chiqish
    - Tizim buyruqlarini ishga tushirish (exec_command, shell)
    
    Qaytaradi: (is_dangerous: bool, reason: str)
    """
    action = action_type.lower()
    
    # 1. Fayl o'chirish
    if action in ["delete_file", "file_delete", "remove_file", "rmdir"]:
        target = details.get("file_path", details.get("path", "noma'lum"))
        return True, f"Faylni o'chirish amali: '{target}' butunlay o'chiriladi."

    # 2. Tashqi tizim buyruqlari
    if action in ["exec_command", "run_shell", "system_exec", "terminal_command"]:
        cmd = details.get("command", "noma'lum")
        return True, f"Tashqi tizim buyrug'ini bajarish: '{cmd}'"

    # 3. Papkadan tashqariga chiqish urinishi
    path = details.get("file_path", details.get("path", ""))
    if ".." in path or path.startswith("/") or (len(path) > 1 and path[1] == ":"):
        return True, f"Workspace chegarasidan tashqariga chiqish urinishi: '{path}'"

    return False, None

def is_dangerous_action(prompt: str) -> Tuple[bool, Optional[str]]:
    """Prompt matnida xavfli yoki destruktiv buyruqlar borligini tekshiradi."""
    p_lower = prompt.lower()
    dangerous_keywords = [
        ("rm -rf", "Kataloglarni majburiy o'chirish buyrug'i"),
        ("drop database", "Ma'lumotlar bazasini o'chirish"),
        ("format c:", "Diskni formatlash"),
        ("git push --force", "Git tarixini majburiy qayta yozish"),
        ("o'chir", "Fayl yoki resurslarni o'chirish amali"),
        ("delete all", "Ommaviy o'chirish amali"),
        ("wipe", "Ma'lumotlarni tozalash")
    ]
    for kw, reason in dangerous_keywords:
        if kw in p_lower:
            return True, f"Xavfli amal aniqlandi: '{kw}' ({reason})"
    return False, None

# ==================== PERMISSION MODES ====================

PERMISSION_MODES = ["ask_always", "ask_dangerous_only", "free_in_workspace"]
CURRENT_PERMISSION_MODE = "ask_dangerous_only"

def get_permission_mode() -> str:
    global CURRENT_PERMISSION_MODE
    return CURRENT_PERMISSION_MODE

def set_permission_mode(mode: str) -> str:
    global CURRENT_PERMISSION_MODE
    if mode in PERMISSION_MODES:
        CURRENT_PERMISSION_MODE = mode
    return CURRENT_PERMISSION_MODE

def should_require_approval(action_type: str, details: dict, is_in_workspace: bool = False) -> Tuple[bool, Optional[str]]:
    mode = get_permission_mode()
    is_dangerous, reason = inspect_danger_level(action_type, details)

    if mode == "ask_always":
        return True, reason or f"Har bir qadam uchun tasdiq talab etiladi ({action_type})."
    elif mode == "free_in_workspace":
        if is_in_workspace and action_type not in ["file_delete", "delete_file"]:
            return False, None
        return is_dangerous, reason
    else:  # ask_dangerous_only
        return is_dangerous, reason
