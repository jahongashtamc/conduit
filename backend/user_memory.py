"""Suhbat xotirasi (Conversational Memory).

Har safar foydalanuvchi vazifa bersa, o'sha muloqot (prompt + agent javobi)
shu yerga yoziladi. Modul undan ikki narsa qiladi:

1. **Uslub profili** — foydalanuvchi qanday yozadi: til (uz/en), rasmiy/ergash,
   qisqa/batafsil, qaysi sohalarda ko'p so'raydi (3d, dizayn, video...).
2. **O'xshash esdaliklar** — yangi vazifa kelganda o'tgan o'xshash suhbatlar
   topiladi va agentga kontekst sifatida beriladi.

Shu ikkalasi `build_style_context()` orqali agent promptlariga qo'shiladi,
shunda agent foydalanuvchiga o'xshab fikrlaydi va javobni uning uslubida beradi.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from collections import Counter
from typing import Any, Dict, List, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conduit.db")

# Soha so'zlari: foydalanuvchi qaysi yo'nalishda ko'p ishlaydi.
DOMAIN_KEYWORDS = {
    "3d": ["3d", "blender", "model", "mesh", "render", "sculpt", "material"],
    "dizayn": ["dizayn", "design", "ui", "ux", "figma", "maket", "layout", "rangi"],
    "video": ["video", "montaj", "timeline", "kadr", "animats", "render", "klip"],
    "rasm": ["rasm", "tekstura", "texture", "rasmlar", "painted", "art"],
    "web": ["sayt", "site", "web", "html", "screenshot", "brauzer", "url"],
    "kod": ["kod", "code", "skript", "script", "python", "test", "bug", "xato"],
    "integratsiya": ["notion", "slack", "api", "webhook", "bot"],
}

_UZ_WORDS = {"va", "uchun", "ber", "qil", "kerak", "shu", "bila", "yana", "qanday", "nima", "juda"}
_EN_WORDS = {"the", "and", "please", "make", "create", "with", "need", "want", "how", "what"}
_INFORMAL = {"hmm", "ok", "bo'ldi", "zo'r", "yaxshi", "shu", "ana", "hey", "salom"}
_FORMAL = {"iltimos", "marhamat", "hurmat", "kereak", "please", "kindly", "regards"}


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.row_factory = sqlite3.Row
    return con


def init_memory_db() -> None:
    with _connect() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS user_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                agent TEXT,
                prompt TEXT NOT NULL,
                response TEXT,
                language TEXT,
                tone TEXT,
                domain TEXT,
                keywords TEXT,
                created_at REAL
            )
            """
        )
        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_ui_created ON user_interactions(created_at)"
        )


def _words(text: str) -> List[str]:
    return [w for w in re.findall(r"[a-zA-Z\u2019'\u02bc]{2,}", (text or "").lower())]


def _detect_language(text: str) -> str:
    words = set(_words(text))
    uz = len(words & _UZ_WORDS)
    en = len(words & _EN_WORDS)
    if uz > en:
        return "uz"
    if en > uz:
        return "en"
    # Apostrophe words like "bo'ladi" lean Uzbek.
    return "uz" if re.search(r"[a-zA-Z]\u2019[a-zA-Z]", text or "") else "en"


def _detect_tone(text: str) -> str:
    words = set(_words(text))
    if len(words & _FORMAL) >= len(words & _INFORMAL):
        return "rasmiy"
    return "ergash"


def _detect_domain(text: str) -> str:
    low = (text or "").lower()
    scores = {name: sum(1 for k in keys if k in low) for name, keys in DOMAIN_KEYWORDS.items()}
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "umumiy"


def _keywords(text: str, limit: int = 8) -> List[str]:
    stop = _UZ_WORDS | _EN_WORDS | _INFORMAL | _FORMAL
    words = [w for w in _words(text) if w not in stop and len(w) > 2]
    return [w for w, _ in Counter(words).most_common(limit)]


def record_interaction(
    task_id: str,
    agent: str,
    prompt: str,
    response: str = "",
) -> Optional[int]:
    """Stores one user<->agent exchange with its extracted style features."""
    if not (prompt or "").strip():
        return None
    init_memory_db()
    try:
        with _connect() as con:
            cur = con.execute(
                """
                INSERT INTO user_interactions
                    (task_id, agent, prompt, response, language, tone, domain, keywords, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    agent,
                    prompt[:2000],
                    (response or "")[:2000],
                    _detect_language(prompt),
                    _detect_tone(prompt),
                    _detect_domain(prompt),
                    json.dumps(_keywords(prompt), ensure_ascii=False),
                    time.time(),
                ),
            )
            return cur.lastrowid
    except Exception:
        return None


def update_response(task_id: str, response: str) -> int:
    """Fills in the agent's answer once the task finishes."""
    if not (response or "").strip():
        return 0
    try:
        with _connect() as con:
            cur = con.execute(
                """
                UPDATE user_interactions
                SET response = ?
                WHERE id = (
                    SELECT id FROM user_interactions
                    WHERE task_id = ? AND (response IS NULL OR response = '')
                    ORDER BY id DESC LIMIT 1
                )
                """,
                (response[:2000], task_id),
            )
            return cur.rowcount
    except Exception:
        return 0


def get_style_profile() -> Dict[str, Any]:
    """Aggregated view of how the user writes and what they ask about."""
    init_memory_db()
    with _connect() as con:
        rows = [dict(r) for r in con.execute(
            "SELECT language, tone, domain, keywords, prompt FROM user_interactions"
        )]
    if not rows:
        return {
            "interactions": 0,
            "language": "uz",
            "tone": "ergash",
            "top_domains": [],
            "frequent_words": [],
            "avg_prompt_words": 0,
        }

    langs = Counter(r["language"] for r in rows)
    tones = Counter(r["tone"] for r in rows)
    domains = Counter(r["domain"] for r in rows)
    words: Counter = Counter()
    for r in rows:
        try:
            words.update(json.loads(r["keywords"] or "[]"))
        except Exception:
            pass
    avg_len = sum(len(_words(r["prompt"])) for r in rows) / len(rows)

    return {
        "interactions": len(rows),
        "language": langs.most_common(1)[0][0],
        "tone": tones.most_common(1)[0][0],
        "top_domains": [{"name": d, "count": c} for d, c in domains.most_common(4)],
        "frequent_words": [w for w, _ in words.most_common(10)],
        "avg_prompt_words": round(avg_len, 1),
    }


def recall_similar(prompt: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Past exchanges whose keywords overlap the new prompt the most."""
    init_memory_db()
    wanted = set(_keywords(prompt, limit=12))
    if not wanted:
        return []
    with _connect() as con:
        rows = [dict(r) for r in con.execute(
            "SELECT task_id, agent, prompt, response, keywords, created_at "
            "FROM user_interactions ORDER BY id DESC LIMIT 200"
        )]
    scored: List[tuple[float, Dict[str, Any]]] = []
    now = time.time()
    for r in rows:
        try:
            kws = set(json.loads(r["keywords"] or "[]"))
        except Exception:
            kws = set()
        overlap = len(wanted & kws)
        if overlap <= 0:
            continue
        # Recent exchanges matter more than old ones.
        age_days = max(0.0, (now - (r["created_at"] or now)) / 86400)
        score = overlap / (1 + age_days / 14)
        scored.append((score, r))
    scored.sort(key=lambda p: -p[0])
    return [r for _, r in scored[:limit]]


def build_style_context(prompt: str) -> str:
    """Compact Uzbek context block injected into agent prompts.

    Returns '' when there is nothing learned yet, so early tasks are unaffected.
    """
    profile = get_style_profile()
    if profile["interactions"] == 0:
        return ""

    lines = [
        "FOYDALANUVCHI USLUBI (o'tgan suhbatlardan o'rganilgan):",
        "- Til: {}; uslub: {}; o'rtacha so'rov uzunligi: {} so'z.".format(
            "o'zbek" if profile["language"] == "uz" else "ingliz",
            profile["tone"],
            profile["avg_prompt_words"],
        ),
    ]
    if profile["top_domains"]:
        doms = ", ".join(f"{d['name']} ({d['count']})" for d in profile["top_domains"])
        lines.append(f"- Ko'p murojaat qiladigan sohalari: {doms}.")
    if profile["frequent_words"]:
        lines.append(f"- Tez ishlatadigan so'zlari: {', '.join(profile['frequent_words'][:6])}.")
    lines.append(
        "- Javobni shu til va uslubda, foydalanuvchiga o'xshab fikrlab ber. "
        "Natijani ham uning odatlangan yo'nalishiga moslab tanla."
    )

    similar = recall_similar(prompt)
    if similar:
        lines.append("O'XSHASH O'TGAN SUHBATLAR:")
        for s in similar:
            resp = (s.get("response") or "").strip()
            tail = f" → natija: {resp[:120]}" if resp else ""
            lines.append(f"- \"{(s['prompt'] or '')[:120]}\"{tail}")

    return "\n".join(lines)


def list_interactions(limit: int = 50) -> List[Dict[str, Any]]:
    init_memory_db()
    with _connect() as con:
        return [dict(r) for r in con.execute(
            "SELECT id, task_id, agent, prompt, response, language, tone, domain, created_at "
            "FROM user_interactions ORDER BY id DESC LIMIT ?", (limit,)
        )]


def reset_memory() -> int:
    init_memory_db()
    with _connect() as con:
        cur = con.execute("DELETE FROM user_interactions")
        return cur.rowcount
