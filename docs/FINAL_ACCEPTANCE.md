# NEXUS (Conduit) — Yakuniy qabul hisoboti

Sana: 2026-11-22 · Asosiy nusxa: `C:\Users\Kapitan\Documents\Проект по умолчанию\conduit`

## 1. Muhit
- `python conduit.py doctor` → **0 FAIL** (FFmpeg 9.0.2, Blender 5.2, agy/opencode/claude/codex PATH'da).
- Desktop yorlig'i asosiy nusxaga ishora qiladi (eski nusxa o'zgartirilmadi).
- CLI buyrug'i `conduit` saqlanadi; brend va UI sarlavhalari NEXUS.

## 2. Testlar
- To'liq `pytest` (ignore'siz): **108 passed, 2 skipped**.
- `backend/tests/test_studio_regressions.py` — 3 ta regression test (stub, HOME izolyatsiyasi, interactive_command).
- `lint` 0, `tsc` 0, `next build` OK, `py_compile`/`compileall` OK.

## 3. Universal agent qatlami
- 13 ta agent `agents.json` va kirish modalida (6 tasi TAYYOR).
- `AGENTS.md/CLAUDE.md/GEMINI.md` avto-yaratiladi; `CONDUIT_API`, `CONDUIT_SESSION` o'rnatiladi.
- Bir martalik CLI chaqiruvlari uchun izolyatsiyalangan HOME (MCP'siz): 8s (global: 50s), global config o'zgarmaydi.
- Terminal: `agy --dangerously-skip-permissions` faqat prompt tayyor bo'lganda yoziladi; eski xatolar buferi tozalanadi.
  Dalil: `LAUNCHED True · TUI True · NO CMD ERROR True`, skrinshot `final_terminal.png`.

## 4. Rejimlar
| Rejim | Vazifa | Natija |
|---|---|---|
| standard | task_18499e7c | PASS |
| eepx | task_a163475c | PASS |
| deepx | task_59b5b517 | PASS |
| super_agent | task_b7bc0db9, task_f102fcae | PASS (ikki marta) |

## 5. Jonli sahna va render
- `/ws/task/{id}` snapshot + log + **40 preview_frame**.
- Blender 5.2 headless: Cycles CPU (32 sample), haqiqiy kadr; 120 kadr 1920×1080 5s MP4.
- Galereya: 138 rasm, **0 buzilgan**, haqiqiy render artefakti bor.

## 6. UI
- NEXUS brendi, kirishda agent tanlovi, Hajm 0.9/1/1.1, yorug'/qorong'u tema.
- Barcha to'liq tablarga «Studiyaga qaytish» tugmasi.
- 1600×1000 va 1280×800: overflow yo'q, konsol 0 xato.

## 7. Barqarorlik
- Soak-test: har 2 daqiqada vazifa, 9/9 PASS (davom etmoqda).
- UI soak: har 5 daqiqada konsol/overflow tekshiruvi, 2/2 toza (davom etmoqda).
- DB/artefakt sog'lig'i monitoringi 30 daqiqa (davom etmoqda).

## 8. Qolgan cheklovlar
- 7 ixtiyoriy CLI (Gemini/Cursor/Qwen/Kimi/GLM/Aider va boshqalar) tizimda o'rnatilmagan.
- 10 ixtiyoriy token sozlanmagan.
- `agy` global MCP serverlarni start paytida yuklaydi (per-invocation flag yo'q); bir martalik chaqiruvlarda izolyatsiya qo'llanadi.

## 9. Subagentlar = asosiy agentga bog'langan tool'lar (2026-11-22)
- Rasmiy model: alohida kontekst + qisqa tavsif asosida delegatsiya + tool allowlist + umumiy token/narx limiti.
  Manbalar: https://code.claude.com/docs/en/subagents.md , https://antigravity.google/docs/subagents?tab=cli (o'qilgan 2026-11-22).
- `conduit tools --json`: 16 tool, jami tavsif 334 token (ogohlantirish chegarasi 15 000). Har tool: input sxema,
  ruxsat etilgan toollar, taxminiy token/narx, `within_remaining_budget`.
- `conduit budget --json` va statusbar: qolgan token/narx (15 s da yangilanadi).
- `POST /api/tasks` dagi BudgetGuard: tanlangan tool uchun byudjet yetishmasa vazifa `BLOCKED` qilinadi.
- native: `.agents/agents/conduit_<id>.md` (16 ta) — agy ularni o'zi topadi (`HAS_CONDUIT_SCOUT True`),
  startup 8.2 s / RC 0. Global sozlama o'zgartirilmadi.
- Haqiqiy delegatsiya: jonli agy `conduit tools --json` ni bajardi (16 toolni xabar qildi), so'ngra
  `conduit run inst_image` orqali `task_e1bda0f0` ni yaratdi va PASS oldi (artefakt 42 226 bayt).
- Token hisobi cumulative hodisalarni qo'shmasdan oxirgi `result` dan olinadi (PONG: 13 944/24).
- Test: `119 passed, 2 skipped`; `doctor` 0 FAIL; `tsc`, `lint`, `next build` 0 xato.
- Skrinshot: `%TEMP%/opencode/nexus_final.png`.

## 10. Yakuniy regressiya (13:44)
- Jonli agy 16 toolni qayta topdi va inst_image vazifasini PASS qildi: `task_a0a9a52a` (gen_59192.png).
- UI 1600x1000 / 1280x800: overflow 0, console errors 0.
- 119 passed, 2 skipped; doctor 0 FAIL; compileall/lint/build/tsc 0.

## 11. 40 daqiqalik kuzatuv (13:54-14:34)
- 19/19 tekshiruv: API 200, WEB 200, `GET /api/tools/catalog` = 16 tool. Xizmat qayta ishga tushmadi.

## 12. Terminal navbat muammosi tuzatildi (14:55)
- Ketma-ket xabarlar agy band paytida yuborilsa, ular navbatga tushib bir nechta "Generating..." bloklarini yaratardi.
- Endi bandlik aniqlanadi va xabar rad etiladi: `BUSY_WARNING True`, `SECOND_NOT_ECHOED True`.
- Test yaratgan 5 ta soxta "budget guard test" vazifasi DB dan o'chirildi; test o'zini o'zi tozalaydi.
- 121 passed, 2 skipped.
