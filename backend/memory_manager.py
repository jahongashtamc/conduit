"""
Conduit Xotira Menejeri (Memory Manager).

Xotira fayllari: memory/project.md, memory/decisions.md, memory/errors.md.
Faqat Yurak yozadi. Inson dashboard orqali ko'ra oladi va tahrirlay oladi.
Subagentlar faqat o'z ilovasiga tegishli qismni oladi (kontekst qisqa saqlanadi).
"""

import os
from datetime import datetime
from typing import Dict, List, Optional

MEMORY_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "memory"))
os.makedirs(MEMORY_DIR, exist_ok=True)

BLOCKS = ["project", "decisions", "errors"]

def get_block_path(block_name: str) -> str:
    clean_name = block_name.lower().replace(".md", "").strip()
    return os.path.join(MEMORY_DIR, f"{clean_name}.md")

def read_memory_block(block_name: str) -> str:
    path = get_block_path(block_name)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading {block_name}: {str(e)}"
    return ""

def write_memory_block(block_name: str, content: str) -> bool:
    path = get_block_path(block_name)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception:
        return False

def append_decision(task_id: str, decision: str) -> bool:
    path = get_block_path("decisions")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n- [{timestamp}] [{task_id}] {decision}"
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(entry)
        return True
    except Exception:
        return False

def append_error(task_id: str, error: str, lesson: str = "") -> bool:
    path = get_block_path("errors")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n- [{timestamp}] [{task_id}] Xatolik: {error} | Saboq: {lesson or 'Qayta urinish'}"
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(entry)
        return True
    except Exception:
        return False

def get_all_memory() -> Dict[str, str]:
    """Barcha xotira bloklarini qaytaradi."""
    return {b: read_memory_block(b) for b in BLOCKS}

def get_subagent_context(subagent: str) -> str:
    """Subagent uchun qisqartirilgan va faqat tegishli kontekstni tayyorlaydi."""
    proj = read_memory_block("project")
    # Faqat birinchi 400 ta belgini qisqacha oladi
    clean_proj = "\n".join([line for line in proj.splitlines() if not line.startswith("#")][:6])
    return f"Loyiha konteksti: {clean_proj}\nSubagent: {subagent}"
