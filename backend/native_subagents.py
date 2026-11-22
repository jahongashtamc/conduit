"""Conduit subagentlarini agy ga NATIVE subagent sifatida bog'lash.

Rasmiy manbalar (2026-11-22):
  * agy: .agents/agents/<name>.md, YAML frontmatter (name/description/tools/
    subagent/mainAgent/model/commandExecutionPolicy), Markdown body = system prompt.
    https://antigravity.google/docs/subagents?tab=cli
  * Claude Code uchun esa universal CLI katalogi (`conduit tools --json`) ishlatiladi,
    chunki agy tool nomlari Claude Code da tanilmaydi.
    https://code.claude.com/docs/en/subagents.md

Bu faqat PROJEKT ichidagi fayllar yaratadi — global ~/.gemini yoki ~/.claude
sozlamalariga tegilmaydi. Asosiy ish joyi (`conduit run`) o'zgarishsiz qoladi;
native definitsiya agentga subagentni TOPISH va delegation qilish imkonini beradi.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

try:  # paket sifatida ham, backend papkasidan to'g'ridan-to'g'ri ham
    from . import security_guard, subagent_scanner, tool_registry
except ImportError:  # pragma: no cover - uvicorn main:app ushbu yo'ldan yuradi
    import security_guard  # type: ignore
    import subagent_scanner  # type: ignore
    import tool_registry  # type: ignore

LOGGER = logging.getLogger("nexus.native_subagents")

# Faqat agy tomonidan e'lon qilingan (init hodisasida ko'ringan) tool nomlari.
# Noto'g'ri nom subagent processining osib qolishiga olib kelishi rasmiy eslatmada bor.
AGY_VERIFIED_TOOLS: List[str] = [
    "run_command",
    "view_file",
    "grep_search",
    "list_dir",
    "search_web",
    "capture_browser_screenshot",
    "open_browser_url",
    "read_url_content",
]


def _frontmatter(agent_id: str, description: str) -> str:
    tools = "\n".join(f"  - {name}" for name in AGY_VERIFIED_TOOLS)
    return (
        "---\n"
        f"name: conduit_{agent_id}\n"
        f"description: >-\n  {description}\n"
        "  Studiya vazifalarini bajarish uchun conduit run bilan chaqir.\n"
        "tools:\n"
        f"{tools}\n"
        "subagent: true\n"
        "mainAgent: false\n"
        "model: inherit\n"
        "commandExecutionPolicy: sandbox\n"
        "---\n"
    )


def _system_prompt(agent_id: str, role_text: str, description: str) -> str:
    return (
        "# System Prompt\n"
        f"Sen Nexus studiyasining '{agent_id}' subagentisan. {description}\n\n"
        "# Asosiy rol\n"
        f"{role_text or 'Vazifani aniq bajar va dalil keltir.'}\n\n"
        "# Ish tartibi (qat'iy)\n"
        f"1. Studiya ishini haqiqatan bajarish uchun `conduit run {agent_id} \"<vazifa>\"` "
        "buyrug'ini ishga tushir.\n"
        "2. `conduit wait <task_id>` bilan kut, `conduit result <task_id>` bilan dalil ol.\n"
        "3. Asosiy agentga FAQAT qisqa natija va artefakt yo'lini qaytar — katta log yuborma.\n"
        "4. So'ralmagan ish qilma, global sozlamalarga tegma.\n"
    )


def sync_native_subagents(root_dir: str | None = None) -> Dict[str, Any]:
    """Faol subagentlar uchun lokal native definitsiyalarni yozadi."""
    root = root_dir or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    agents_dir = os.path.join(root, ".agents", "agents")
    os.makedirs(agents_dir, exist_ok=True)

    catalog = tool_registry.build_tool_catalog(include_budget=False)
    descriptions = {t["subagent"]: t["description"] for t in catalog.get("tools", [])}
    written: List[str] = []

    for sub in subagent_scanner.scan_subagents():
        agent_id = str(sub.get("id") or "")
        if str(sub.get("status", "")).lower() != "active" or not agent_id:
            continue
        description = descriptions.get(agent_id) or str(sub.get("role_desc_uz") or "")[:160]
        role_path = os.path.join(security_guard.SUBAGENTS_DIR, agent_id, "role.md")
        try:
            with open(role_path, encoding="utf-8", errors="replace") as fh:
                role_text = fh.read().strip()
        except OSError as exc:
            LOGGER.warning("Native subagent roli o'qilmadi (%s): %s: %s", agent_id, type(exc).__name__, exc)
            role_text = ""

        path = os.path.join(agents_dir, f"conduit_{agent_id}.md")
        content = _frontmatter(agent_id, description) + "\n" + _system_prompt(agent_id, role_text, description)
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
            written.append(path)
        except OSError as exc:
            LOGGER.error("Native subagent yozilmadi (%s): %s: %s", path, type(exc).__name__, exc)

    return {"directory": agents_dir, "count": len(written), "files": written}
