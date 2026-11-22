"""Subagentlarni asosiy AI agentga bog'langan tool'lar sifatida taqdim etish.

Rasmiy subagent modeli (Claude Code docs, 2026-11-22):
  * asosiy agent kontekstiga faqat QISQA tavsif yuklanadi;
  * to'liq rol/system prompt faqat subagent ishga tushganda yuklanadi;
  * har subagent o'z tool allowlistiga ega;
  * uning so'rovlari umumiy token/narx limitiga hisoblanadi.

Conduit agent-agnostik bo'lgani uchun "Agent tool" o'rniga universal CLI shartnomasi
ishlatiladi: `conduit tools --json` -> katalog, `conduit run <id> "<task>"` -> chaqiruv.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

try:  # paket sifatida ham, backend papkasidan to'g'ridan-to'g'ri ham ishlaydi
    from . import database, security_guard, subagent_scanner
except ImportError:  # pragma: no cover - uvicorn main:app ushbu yo'ldan yuradi
    import database  # type: ignore
    import security_guard  # type: ignore
    import subagent_scanner  # type: ignore

LOGGER = logging.getLogger("nexus.tool_registry")

CATALOG_VERSION = "1.0"
# Claude Code ogohlantirish chegarasi: barcha tavsiflar jami 15 000 token dan oshmasligi kerak.
DESCRIPTION_TOKEN_WARNING = 15_000
# Narx modeli database.record_resource_usage bilan bir xil (USD / 1M token).
COST_PROMPT_PER_M = 3.0
COST_COMPLETION_PER_M = 15.0
# Tavsif uzunligi (asosiy kontekstga yuklanadigan yagona qism).
MAX_DESCRIPTION_CHARS = 160
# Haqiqiy agy chaqiruvlari o'lchovi asosida minimal ijro bahosi.
MIN_EXECUTION_TOKENS = 15_000


def _tokens_from_text(text: str) -> int:
    """Konservativ token bahosi: o'rtacha 3 belgi = 1 token."""
    return max(1, len(text or "") // 3)


def _short_description(meta: Dict[str, Any], role_text: str) -> str:
    desc = (
        meta.get("role_desc_uz")
        or meta.get("role_desc_en")
        or meta.get("description")
        or ""
    ).strip()
    if not desc and role_text:
        for line in role_text.splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                desc = line.strip()
                break
    if len(desc) > MAX_DESCRIPTION_CHARS:
        desc = desc[: MAX_DESCRIPTION_CHARS - 1].rstrip() + "…"
    return desc or f"{meta.get('id', 'subagent')} vazifalari"


def _role_text(agent_id: str) -> str:
    path = os.path.join(security_guard.SUBAGENTS_DIR, agent_id, "role.md")
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read().strip()
    except OSError as exc:
        LOGGER.warning("Rol prompti o'qilmadi (%s): %s: %s", path, type(exc).__name__, exc)
        return ""


def _budget() -> Dict[str, Any]:
    try:
        summary = database.get_resource_summary()
    except Exception as exc:
        LOGGER.warning("Resurs summary olinmadi: %s: %s", type(exc).__name__, exc)
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}

    used = float(summary.get("total_tokens") or 0)
    max_tokens = float(summary.get("max_tokens") or 0)
    used_cost = float(summary.get("total_cost_usd") or 0)
    max_cost = float(summary.get("max_budget_usd") or 0)
    return {
        "available": True,
        "used_tokens": int(used),
        "max_tokens": int(max_tokens),
        "remaining_tokens": max(0, int(max_tokens - used)) if max_tokens else None,
        "used_cost_usd": round(used_cost, 6),
        "max_budget_usd": round(max_cost, 6),
        "remaining_cost_usd": round(max(0.0, max_cost - used_cost), 6) if max_cost else None,
        "is_blocked": bool(summary.get("is_blocked")),
        "block_reason": summary.get("block_reason"),
        "by_agent": summary.get("by_agent") or {},
    }


def build_tool_catalog(include_budget: bool = True) -> Dict[str, Any]:
    """Har bir faol subagentni chaqiriladigan tool sifatida qaytaradi."""
    tools: List[Dict[str, Any]] = []
    total_description_tokens = 0
    budget = _budget() if include_budget else None
    remaining_tokens = (budget or {}).get("remaining_tokens")
    remaining_cost = (budget or {}).get("remaining_cost_usd")

    for sub in subagent_scanner.scan_subagents():
        if str(sub.get("status", "")).lower() != "active":
            continue
        agent_id = str(sub.get("id") or "")
        if not agent_id:
            continue

        role_text = _role_text(agent_id)
        description = _short_description(sub, role_text)
        context_tokens = _tokens_from_text(description)
        total_description_tokens += context_tokens
        allowed = sorted(security_guard.get_allowed_tools(agent_id))
        # To'liq rol prompti faqat subagent boshlanganda yuklanadi; u asosiy
        # kontekstga kirmaydi, lekin narx/token rejalashtirish uchun ko'rsatiladi.
        # Real o'lchovlar (agy stream-json): oddiy chaqiruv ~14k token, katta
        # ko'p-tool vazifa ~90k. 15k — eng kichik real chegara sifatida olinadi.
        execution_tokens = max(
            _tokens_from_text(role_text) + context_tokens + 400,
            MIN_EXECUTION_TOKENS,
        )
        estimated_cost = round(
            (context_tokens * COST_PROMPT_PER_M + execution_tokens * COST_COMPLETION_PER_M)
            / 1_000_000,
            6,
        )
        within_budget = True
        if budget and budget.get("available"):
            within_budget = (
                (remaining_tokens is None or remaining_tokens >= execution_tokens)
                and (remaining_cost is None or remaining_cost >= estimated_cost)
            )

        tools.append(
            {
                "name": f"conduit_run_{agent_id}",
                "subagent": agent_id,
                "description": description,
                "use_when": f"{sub.get('target_app', 'General')} bilan bog'liq ish: {description}",
                "type": sub.get("type") or "role",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "Subagentga aniq, o'lchovli vazifa (qisqa va kontekstli)",
                        }
                    },
                    "required": ["task"],
                },
                "invocation": f'conduit run {agent_id} "<task>"',
                "allowed_tools": allowed,
                "context_tokens": context_tokens,
                "estimated_execution_tokens": execution_tokens,
                "estimated_cost_usd": estimated_cost,
                "within_remaining_budget": within_budget,
                "role_prompt_loaded": "faqat subagent ishga tushganda (asosiy kontekstga kirmaydi)",
            }
        )

    catalog: Dict[str, Any] = {
        "version": CATALOG_VERSION,
        "protocol": "conduit-cli",
        "description_limit_tokens": DESCRIPTION_TOKEN_WARNING,
        "total_description_tokens": total_description_tokens,
        "description_budget_ok": total_description_tokens < DESCRIPTION_TOKEN_WARNING,
        "tools": tools,
        "call_contract": [
            "conduit tools --json   # shu katalog",
            "conduit budget --json  # qolgan token/narx",
            'conduit run <subagent> "<task>"  # tool chaqiruvi -> task_id',
            "conduit watch <task_id> | conduit wait <task_id>  # kuzatish",
            "conduit result <task_id>  # dalil va artefaktlar",
        ],
        "rules": [
            "Faqat qisqa tavsif asosiy kontekstga yuklanadi; to'liq rol promptini o'zing kiritma.",
            "Delegatsiyadan oldin `conduit budget --json` ga qara; katalogdagi "
            "`within_remaining_budget=false` bo'lgan tool'ni chaqirma.",
            "Subagent katta log yoki fayl tarkibini qaytarmasligi kerak — faqat qisqa natija va dalil yo'li.",
            "Bitta vazifa uchun bitta aniq subagent tanla; noaniq bo'lsa foydalanuvchidan so'ra.",
        ],
        "budget": budget,
    }
    return catalog


def compact_tool_lines() -> str:
    """AGENTS.md uchun ixcham 'tool -> qisqa tavsif' ro'yxati (DB ga murojaat qilmaydi)."""
    lines: List[str] = []
    for tool in build_tool_catalog(include_budget=False).get("tools", []):
        lines.append(f"- `{tool['name']}` ({tool['subagent']}): {tool['description']}")
    return "\n".join(lines) or "- (faol subagent yo'q)"
