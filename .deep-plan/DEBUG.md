# DEBUG

## 1. Eski skrinshot yangi dalil deb PASS bo'layotgandi
Alomat: `python tools.py check_goal 'Create a 3D model' '{}'` → `verdict: PASS`, `success: true`, `visual_captured: true`, lekin dalil sifatida oldingi vazifadan qolgan `backend/static/screenshots/latest.png` ko'rsatilgan.
Ildiz sabab: `tools.py::tool_check_goal` bo'sh evidence'da `test_screenshot.png`, `screenshot.png`, `latest.png` fayllariga fallback qilar va ularni mavjud dalil deb hisoblar edi. Fayl yoshi yoki yaratilgan vaqti tekshirilmasdi.
Dalil: fallback kodi (eski 297-310-qatorlar); yuqoridagi bevosita CLI chaqiruvi natijasi: bo'sh `{}` bilan PASS chiqqan.
Tuzatish: fallback butunlay olib tashlandi; bo'sh evidence → `FAIL`; `CONDUIT_TASK_STARTED_AT` bilan `captured_at` va fayl `mtime` solishtiriladi; 5 soniyalik vaqt bardoshi.
Tekshiruv: `verify_stale_evidence.py` → `verdict: FAIL`, `Dalil eski: yaratilgan vaqti joriy vazifa boshlanishidan oldin.`; `test_check_goal_rejects_empty_evidence`, `test_check_goal_rejects_stale_artifact` yashil.

## 2. Tool allowlist faqat matn skanerida edi
Alomat: agent `tools.py` ni chaqirganda ruxsat faqat `cli_runner` chiqish qatorida `python tools.py ...` deb yozilganini tekshirar, to'g'ridan-to'g'ri vosita chaqiruvi esa darvozadan o'tib ketardi. `web_search` ham CLI yordamida yo'q edi.
Ildiz sabab: `tools.py::main` da `security_guard.verify_tool_access` chaqiruvi yo'q; `CONDUIT_AGENT` subprocess'ga uzatilmasdi.
Dalil: eski `main` (856-939-qatorlar), env qurish (532-539-qatorlar), `inst_web/role.md` da `web_search` borligi.
Tuzatish: `cli_runner` `CONDUIT_AGENT`, `CONDUIT_TASK_ID`, `CONDUIT_TASK_STARTED_AT` ni uzatadi; `tools.py::main` kanonik nomga o'tkazib `verify_tool_access` chaqiradi; barcha alias'lar va `web_search` katalogga kiritildi; katalog buyruqlari matn skanerida oq ro'yxatga olindi.
Tekshiruv: `CONDUIT_AGENT=scout python tools.py gen_image 'deneme'` → `success: false`, `XAVFSIZLIK TO'SIG'I`, exit 2; `python tools.py list_tools` → 15 ta tool; `test_tools_main_enforces_agent_allowlist` yashil.

## 3. Sifat darvozasi kalit so'zlarga ishonardi
Alomat: `validate_evidence_against_goal` da `3d`, `render`, `model` so'zlari dalil matnida bo'lsa, hech qanday fayl/artefakt yo'q bo'lsa ham PASS edi.
Ildiz sabab: faqat `e_lower` bo'yicha kalit so'z qidirish; artefakt obyekti talab qilinmasdi.
Dalil: eski 358-383-qatorlar; `validate_evidence_against_goal("Blender'da 3D kub model yarat", "sculptor", "render model scene", "")` → `True`.
Tuzatish: `_evidence_artifacts` fayl/URL kengaytmalarini ajratadi; 3D/Figma/qidiruv vazifalarida tegishli artefakt bo'lmasa FAIL.
Tekshiruv: `test_evidence_validator_requires_artifact_not_keywords` yashil; mavjud Figma/web validator testlari buzilmadi.

## 4. Agent yo'riqnomasi instrumentlarni to'liq ochib bermagan
Alomat: `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` da faqat `conduit` buyruqlari bor, `tools.py` instrumentlari va ularning ro'yxati yo'q edi.
Ildiz sabab: `_studio_guide_md` faqat subagent katalogini ko'rsatar, ichki tool'lar ro'yxatini generatsiya qilmasdi.
Dalil: `_studio_guide_md()` eski matnida `python tools.py list_tools` yoki instrument nomlari yo'q edi; `grep` natijasi bo'sh.
Tuzatish: `_internal_tool_list_for_docs()` qo'shildi, guide marker v5 ga ko'tarildi, 3 hujjat qayta generatsiya qilindi.
Tekshiruv: `AGENTS.md:36` → `python tools.py web_search query`, `AGENTS.md:44` → `python tools.py gen_image prompt [w] [h] [out]`.

## 5. Full suite vaqtinchalik uzilish (tuzatildi)
Alomat: `3 errors during collection` — `test_pty_*` backendga ulana olmadi (`WinError 1225`), collection to'xtadi.
Ildiz sabab: oldingi server restart'laridan keyin 8000-portda backend ishga tushmagan edi; PTY testlari collection paytida jonli backend talab qiladi.
Dalil: `NO_BACKEND` (8000 port), keyin `HEALTH=200` va xato yo'qolgani.
Tuzatish: backend `uvicorn main:app --port 8000` qayta ishga tushirildi, keyin to'liq test qayta ishlatildi.
Tekshiruv: `python -m pytest tests -q --no-header` → `158 passed, 2 skipped, 4 warnings in 272.76s`, `PYTEST=0`.
