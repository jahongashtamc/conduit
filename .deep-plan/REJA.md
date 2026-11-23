# REJA

## 1. Tool katalogi va yordam chiqishini to'liq qilish

Nima qilinadi va qaysi fayllar: `backend/tool_registry.py` va `backend/security_guard.py` asosida `backend/tools.py` ga `list_tools` buyrug'i va `--json` chiqishi, barcha e'lon qilingan tool nomlari (screenshot, run_process, check_goal, blender_headless_exec, runscript, figma_sync, gen_image, video_render, anim_render, notion_api, slack_api, web_search va boshqalar) bilan to'ldiriladi; `backend/tests/test_tool_coverage.py` kengaytiriladi.
Tugash sharti: `python tools.py --help` va `python tools.py list_tools --json` 0 xato bilan barcha tool'larni ko'rsatadi; test ro'yxatdagi har bir tool CLI'da mavjudligini tasdiqlaydi.
Eng sodda variant: yangi modul yaratmay, mavjud `tools.py` va `tool_registry.py` funksiyalarini bog'lash.

## 2. Bajaruvchi tomonda ruxsat va agent identifikatori

Nima qilinadi va qaysi fayllar: `backend/engine/cli_runner.py` subprocess env'iga `CONDUIT_AGENT` va `CONDUIT_TASK_ID` qo'shadi; `backend/tools.py::main` har bir tool chaqiruvidan oldin `security_guard.verify_tool_access` bilan tekshiradi; `web_search` katalog va xato xabarlariga qo'shadi.
Tugash sharti: ruxsatsiz agent tool chaqiruvi aniq "permission denied" bilan rad etiladi; ruxsat etilgani bajariladi; `backend/tests/test_security.py`/yangi test yashil.
Eng sodda variant: bitta `enforce_tool_access(tool_name)` funksiyasi, barcha chaqiruvlar oldida chaqiriladi.

## 3. Dalil sifatini qat'iy tekshirish

Nima qilinadi va qaysi fayllar: `backend/tools.py::tool_check_goal` eski screenshot'ga fallback qilishni to'xtatadi; faqat joriy vazifa uchun yaratilgan, mavjud va haqiqiy faylni qabul qiladi; `backend/engine/cli_runner.py::validate_evidence_against_goal` kalit so'z o'rniga aniq dalil obyektlarini tekshiradi; `backend/tests/test_cli_runner.py` va yangi regression testlar.
Tugash sharti: eski `latest.png` bilan `verdict: FAIL`, yangi yaratilgan PNG bilan `verdict: PASS`, bo'sh dalil FAIL; mavjud `success:true` kontrakti buzilmaydi.
Eng sodda variant: dalil yoshini `mtime` va vazifa boshlang'ich vaqti bilan solishtirish, turini tasdiqlash.

## 4. Agent yo'riqnomasi, testlar va yakuniy tekshiruv

Nima qilinadi va qaysi fayllar: `backend/terminal_session.py::_studio_guide_md` va `backend/tool_registry.py` orqali asosiy agentga tool katalogi va delegatsiya qoidalari qo'shadi; `.deep-plan/TEST.md`, `.deep-plan/DEBUG.md`, `.deep-plan/PROGRESS.md`, `DECISIONS.md`, `.agents/time-log.md` yangilanadi.
Tugash sharti: yo'riqnomada `python tools.py --help` / `conduit tools` havolasi bor; `pytest backend/tests -q`, `compileall`, `doctor`, `tsc`, `lint`, `build` yashil; `gate.py verify OK`; faqat ko'zlangan fayllar o'zgargan.
Eng sodda variant: mavjud yo'riqnoma matniga katalog qatorlari va namuna qo'shish.

TASDIQ: HA
