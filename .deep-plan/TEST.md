# TEST

Har bo'limda haqiqiy terminal chiqishi keltirildi (2026-11-23).

## 1. Ishga tushirish / build
- `python -m compileall -q backend` → `COMPILE=0`.
- `python conduit.py doctor` → `DOCTOR=0`, `Zarur hamma narsa tayyor — MVP ishlatishga mumkin.` (backend API 200; ixtiyoriy CLI/tokenlar WARN).
- `npx tsc --noEmit` → `TSC=0`; `npm run lint` → `LINT=0` (faqat info darajasidagi react-hooks ogohlantirish); `npm run build` → `BUILD=0`.
- `GET /api/health` → `200`; `GET /` (frontend) → `200`.
Natija: O'TDI

## 2. Asosiy funksiyalar
- `python tools.py list_tools` → 15 ta instrument: `screenshot, interact_web, web_search, run_process, get_logs, check_goal, blender_headless_exec, blender_video, runscript, figma_sync, gen_image, video_render, anim_render, notion_api, slack_api`.
- `python conduit.py tools --json` → `CLI=0 TOOLS=16 BUDGET_OK=True` (16 subagent-tool, tavsif 334 token; chegara 15000).
- `python conduit.py budget --json` → `BUDGET_CLI=0`.
- Agent yo'riqnomasi qayta generatsiya qilindi: `DOC_MARKER <!-- CONDUIT-STUDIO-GUIDE v5 -->`; `AGENTS.md:36` → `python tools.py web_search query`, `AGENTS.md:44` → `python tools.py gen_image prompt [w] [h] [out]`.
Natija: O'TDI

## 3. Chegara va xato holatlari
- `CONDUIT_AGENT=scout python tools.py gen_image 'deneme'` → `success: false`, `XAVFSIZLIK TO'SIG'I: 'scout' subagenti ruxsat etilmagan 'gen_image' toolini chaqirishga urindi!`, `DENIED_EXIT=2`.
- `CONDUIT_AGENT=scout python tools.py get_logs` → `success: true`, `tool: get_logs`.
- Bo'sh evidence: `tool_check_goal("Create a 3D model", "{}")` → `verdict: FAIL`, `Dalil taqdim etilmadi`.
- Eski dalil: `verify_stale_evidence.py` (old `latest.png`, `captured_at` 2 soat oldin) → `verdict: FAIL`, `Dalil eski: yaratilgan vaqti joriy vazifa boshlanishidan oldin.`
- `validate_evidence_against_goal(... "render model scene", "")` → `False`, `3D vazifa uchun ko'rinadigan artefakt ... topilmadi`; haqiqiy `.png` yo'li bilan → `True`.
Natija: O'TDI

## 4. Xavfsizlik
- Ruxsat darvozasi `tools.py` ichida, `security_guard.verify_tool_access` orqali; `cli_runner` matn skaneri faqat qo'shimcha himoya. `CONDUIT_AGENT` faqat shu chaqiruv subprocess'iga uzatiladi, global config/auth/MCP o'zgartirilmadi.
- Maxfiy kalitlar loglanmadi; `sk-...` gumonlari faqat mavjud redaction test fixture'lari.
Natija: O'TDI

## 5. Regressiya
- Maqsadli: `pytest tests/test_tool_gate_hardening.py tests/test_cli_runner.py tests/test_tool_coverage.py tests/test_model_error_and_evidence.py -q` → `26 passed, 2 skipped in 8.04s`, EXIT=0.
- To'liq: `python -m pytest tests -q --no-header` → `158 passed, 2 skipped, 4 warnings in 272.76s (0:04:32)`, `PYTEST=0`.
Natija: O'TDI

## 6. Qo'lda ko'rish / jonlilik
- Backend qayta ishga tushirildi (`uvicorn main:app --port 8000`), `/api/health` 200; frontend `npm run start` bilan 3000-portda 200.
- `conduit tools --json` va `conduit budget --json` jonli backend bilan ishladi (yuqoridagi chiqish).
Natija: O'TDI

## 7. Tekshirilmaganlar
- 7 ta ixtiyoriy CLI o'rnatilmagan (global o'rnatish qilinmadi); Notion/Slack/GitHub tokenlari sozlanmagan.
- Ushbu o'zgartirish doirasida to'liq 3D/Blender vazifasi oxirigacha qayta yurgizilmadi; dalil va ruxsat darvozalari unit + CLI darajasida tekshirildi.
- Boshqa agentlarning uzoq TUI oqimlari sinab ko'rilmadi.
Natija: TEKSHIRILMADI (sabablari yuqorida)
