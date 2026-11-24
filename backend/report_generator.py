"""
Conduit Audit & Mission Report Generator
Har bir vazifa yoki butun sessiya uchun professional tahliliy hisobot (Markdown va HTML) tuzadi.
"""

import html
from datetime import datetime
from typing import Any, Union


def _normalize_task_id(task_id: Union[str, int]) -> Any:
    """UI path parametri string keladi, DB tasks.id esa integer."""
    if isinstance(task_id, str):
        raw = task_id.strip()
        if raw.lstrip("-").isdigit():
            return int(raw)
        return raw
    return task_id


def generate_task_markdown_report(task_id: str) -> str:
    import database
    from engine.healer import SelfHealer

    tid = _normalize_task_id(task_id)
    task = database.get_task(tid)
    if not task:
        return f"# Xatolik: Vazifa '{task_id}' topilmadi."

    logs = database.get_logs(tid)
    healing_events = SelfHealer.get_healing_events(tid)

    st_dur = task.get("step_durations", {})
    total_dur = task.get("total_duration", 0)
    status = task.get("status", "Noma'lum")
    agent = task.get("target_agent", "scout")
    prompt = task.get("prompt", "")
    evidence = task.get("evidence", "Dalil yo'q")

    md = []
    md.append(f"# CONDUIT MISSIYA AUDIT HISOBOTI")
    md.append(f"**Vazifa ID:** `{tid}` | **Sana:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md.append(f"**Holat:** `{status}` | **Ijrochi Subagent:** `{agent}`")
    md.append("")
    md.append("---")
    md.append("## 1. Topshiriq Mazmuni va Maqsad")
    md.append(f"> {prompt}")
    md.append("")
    md.append("## 2. Vaqt va Resurs Ko'rsatkichlari")
    md.append(f"- **Jami Davomiylik:** `{total_dur} soniya`")
    if st_dur:
        md.append(f"- **Planner (Miya):** `{st_dur.get('planner', 0)}s`")
        md.append(f"- **Doer (Subagent CLI):** `{st_dur.get('doer', 0)}s`")
        md.append(f"- **Checker (Tekshiruv):** `{st_dur.get('checker', 0)}s`")
    md.append("")
    md.append("## 3. Dalil va Natija")
    md.append(f"**Checker Xulosasi:** {evidence}")
    if task.get("screenshot_url"):
        md.append(f"- **Skrinshot Artefakti:** `{task.get('screenshot_url')}`")
    md.append("")

    if healing_events:
        md.append("## 4. Avtonom O'z-o'zini Tuzatish (Self-Healing)")
        for h in healing_events:
            md.append(f"- **Urinish {h.get('attempt')}:** {h.get('diagnosis')}")
            md.append(f"  - *Strategiya:* {h.get('remedy')}")
        md.append("")

    eepx_traces = database.get_eepx_traces(tid)
    if eepx_traces:
        md.append("## 4.1. EEPX Chuqur Kognitiv Tahlili")
        for tr in eepx_traces:
            md.append(f"- **Faza:** `{tr.get('phase')}` | **Ishonchlilik:** `{tr.get('confidence_score')}`")
            if tr.get("details"):
                for k, v in list(tr["details"].items())[:3]:
                    md.append(f"  - *{k}:* `{str(v)[:70]}`")
        md.append("")

    swarm_stages = database.get_swarm_stages(tid)
    if swarm_stages:
        md.append("## 4.2. Super Agent Swarm Bosqichlari")
        for stg in swarm_stages:
            md.append(f"- **Bosqich {stg.get('stage_index')}:** `{stg.get('stage_title')}` ({stg.get('target_agent')}) — **Holat:** `{stg.get('status')}`")
            if stg.get("output_artifact"):
                md.append(f"  - *Chiquvchi Artefakt:* `{stg.get('output_artifact')}`")
        md.append("")

    deepx_thoughts = database.get_deepx_thoughts(tid)
    if deepx_thoughts:
        md.append("## 4.3. DeepX Uzoq Muddatli Fikrlash (Extended Reasoning)")
        for th in deepx_thoughts:
            md.append(f"- **Qadam {th.get('step_number')}:** `{th.get('thought_title')}` [{th.get('perspective')}] — **Ishonch:** `{th.get('confidence')}`")
            md.append(f"  - *Mazmun:* {th.get('thought_content')}")
        md.append("")

    deepsearch_cits = database.get_deepsearch_citations(tid)
    if deepsearch_cits:
        md.append("## 4.4. DeepSearch Ko'p Manbali Tadqiqot")
        for c in deepsearch_cits:
            md.append(f"- **{c.get('source_title')}:** `{c.get('source_uri')}` (Moslik: `{c.get('relevance_score')}`)")
            md.append(f"  - *Xulosa:* {c.get('summary')}")
        md.append("")

    mvp_bp = database.get_mvp_blueprint(tid)
    if mvp_bp:
        md.append("## 4.5. To'liq MVP Karkasi (Scaffold Blueprint)")
        md.append(f"- **Loyiha Nomi:** `{mvp_bp.get('project_name')}`")
        md.append(f"- **Frontend:** `{mvp_bp.get('frontend_spec', {}).get('framework')}` ({', '.join(mvp_bp.get('frontend_spec', {}).get('pages', []))})")
        md.append(f"- **Backend:** `{mvp_bp.get('backend_spec', {}).get('framework')}` ({len(mvp_bp.get('backend_spec', {}).get('endpoints', []))} endpoints)")
        md.append(f"- **Xavfsizlik:** `{mvp_bp.get('security_spec', {}).get('redteam_status')}`")
        md.append("")

    md.append("## 5. Xavfsizlik va Sandbox Nazorati")
    try:
        import security_guard
        allowed_tools = sorted(security_guard.get_allowed_tools(agent))
    except Exception as exc:
        allowed_tools = []
        md.append(f"- **Tool Whitelist xatosi:** {type(exc).__name__}: {exc}")
    whitelist_text = ", ".join(allowed_tools) if allowed_tools else "o'qilmadi"
    md.append(f"- **Tool Whitelist (role.md):** {whitelist_text}")
    md.append(f"- **Workspace siyosati:** `workspaces/{agent}/` (yo'l ma'lumot uchun; mustaqil audit bu hisobotda yo'q).")
    md.append("- **Secrets:** ushbu hisobot maxfiy kalitlarni skanerlamadi; 'zero-secrets' da'vosi qilinmaydi.")
    md.append("")

    md.append("## 6. So'nggi Ijro Loglari")
    md.append("```text")
    for log in logs[-15:]:
        md.append(f"[{log.get('timestamp')}] [{log.get('level')}] ({log.get('agent_name')}): {log.get('message')}")
    md.append("```")
    md.append("")
    md.append("---")
    md.append("*Ushbu hisobot Conduit Sovereign Autonomous Studio tomonidan avtomatik shakllantirildi.*")

    return "\n".join(md)

def generate_task_html_report(task_id: str) -> str:
    md_content = generate_task_markdown_report(task_id)
    # Simple, high-contrast dark styled HTML document
    lines = md_content.split("\n")
    html_lines = []
    in_code = False

    for line in lines:
        if line.startswith("```"):
            if not in_code:
                html_lines.append("<pre><code>")
                in_code = True
            else:
                html_lines.append("</code></pre>")
                in_code = False
            continue

        # Vazifa matni, loglar va artefakt yo'llari foydalanuvchidan keladi:
        # HTML'ga to'g'ridan-to'g'ri qo'yilsa XSS bo'ladi. Hamma joyga escape qilamiz.
        if in_code:
            html_lines.append(html.escape(line))
            continue

        if line.startswith("# "):
            html_lines.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("> "):
            html_lines.append(f"<blockquote>{html.escape(line[2:])}</blockquote>")
        elif line.startswith("- "):
            html_lines.append(f"<li>{html.escape(line[2:])}</li>")
        elif line.startswith("---"):
            html_lines.append("<hr/>")
        elif line.strip():
            html_lines.append(f"<p>{html.escape(line)}</p>")

    body = "\n".join(html_lines)
    return f"""<!DOCTYPE html>
<html lang="uz">
<head>
  <meta charset="UTF-8">
  <title>Conduit Audit Report - {html.escape(str(task_id))}</title>
  <style>
    body {{
      background: #090d16;
      color: #e2e8f0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
      line-height: 1.6;
      padding: 40px;
      max-width: 900px;
      margin: 0 auto;
    }}
    h1 {{ color: #38bdf8; border-bottom: 2px solid #1e293b; padding-bottom: 10px; font-size: 24px; }}
    h2 {{ color: #818cf8; margin-top: 25px; font-size: 18px; border-bottom: 1px solid #1e293b; padding-bottom: 6px; }}
    code {{ background: #1e293b; padding: 2px 6px; rounded: 4px; color: #38bdf8; font-family: monospace; font-size: 13px; }}
    pre {{ background: #020617; border: 1px solid #1e293b; padding: 15px; border-radius: 8px; overflow-x: auto; color: #94a3b8; font-size: 12px; }}
    blockquote {{ border-left: 4px solid #3b82f6; padding-left: 15px; margin-left: 0; color: #cbd5e1; background: #0f172a; padding: 10px 15px; border-radius: 0 8px 8px 0; }}
    li {{ margin-bottom: 4px; }}
    hr {{ border: 0; border-top: 1px solid #1e293b; margin: 25px 0; }}
  </style>
</head>
<body>
  {body}
</body>
</html>"""
