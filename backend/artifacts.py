"""Artefakt galereyasi API yordamchisi.

workspaces/<agent>/ ichidagi yaratilgan fayllarni (PNG, MP4, GIF, JSON...)
topib, UI galereyasi uchun xavfsiz ro'yxat qaytaradi. Fayl mazmuni faqat
workspace ichidan o'qiladi (path traversal himoyasi).
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

import workspace_manager

ARTIFACT_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".webm", ".json", ".md", ".py"}
MEDIA_MIME = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".webp": "image/webp", ".mp4": "video/mp4",
    ".webm": "video/webm",
}


def list_artifacts(limit: int = 200) -> List[Dict[str, Any]]:
    """Barcha subagent workspace'laridagi artefaktlar, eng yangilari birinchi."""
    root = workspace_manager.WORKSPACES_ROOT
    items: List[Dict[str, Any]] = []
    if not os.path.isdir(root):
        return items
    for agent in sorted(os.listdir(root)):
        agent_dir = os.path.join(root, agent)
        if not os.path.isdir(agent_dir):
            continue
        for dirpath, _dirs, files in os.walk(agent_dir):
            # Framelarni yig'ish papkalari (render oraliq fayllari) tashlab yuboriladi.
            if os.path.basename(dirpath).startswith("_"):
                continue
            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                if ext not in ARTIFACT_EXTS:
                    continue
                full = os.path.join(dirpath, fname)
                try:
                    stat = os.stat(full)
                except OSError:
                    continue
                rel = os.path.relpath(full, root).replace("\\", "/")
                items.append({
                    "agent": agent,
                    "file": fname,
                    "path": rel,
                    "ext": ext,
                    "kind": "media" if ext in MEDIA_MIME else "text",
                    "mime": MEDIA_MIME.get(ext, "text/plain"),
                    "bytes": stat.st_size,
                    "modified": stat.st_mtime,
                })
    items.sort(key=lambda x: -x["modified"])
    return items[:limit]


def safe_artifact_path(rel_path: str) -> str:
    """workspaces/ ichidagi faylning to'liq yo'lini xavfsiz qaytaradi."""
    root = os.path.abspath(workspace_manager.WORKSPACES_ROOT)
    full = os.path.abspath(os.path.join(root, rel_path))
    if not full.startswith(root + os.sep) and full != root:
        raise ValueError("Workspace tashqarisidagi yo'l rad etildi")
    if not os.path.isfile(full):
        raise FileNotFoundError("Fayl topilmadi")
    return full
