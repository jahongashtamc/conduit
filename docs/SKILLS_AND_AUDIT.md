# GitHub skilllari va chuqur audit (2026-11-22)

## 1. O'rnatilgan skilllar (faqat lokal)

Manbalar rasmiy/GitHub repolardan `git clone --depth 1` bilan vaqtinchalik papkaga olinib,
kerakli `SKILL.md` papkalari **loyiha ichiga** ko'chirildi:

| Skill ID | Manba | Litsenziya | Maqsad |
|---|---|---|---|
| `systematic-debugging` | `obra/superpowers` | MIT | Root cause bo'yicha 4 fazali debug |
| `verification-before-completion` | `obra/superpowers` | MIT | Dalilsiz "tayyor" deyishni taqiqlash |
| `code-review-and-quality` | `addyosmani/agent-skills` | MIT | 5 o'qli code review |
| `security-and-hardening` | `addyosmani/agent-skills` | MIT | Xavfsizlik/ssrf/secret/input audit |
| `observability-and-instrumentation` | `addyosmani/agent-skills` | MIT | Log/metrik/tracing nazorati |
| `karpathy-guidelines` | `multica-ai/andrej-karpathy-skills` | MIT | Soddalik va jarroh o'zgartirish |
| `webapp-testing` | `anthropics/skills` | per-skill LICENSE.txt | Playwright bilan UI test |

Joylashuv: `conduit/.opencode/skills/`. OpenCode ularni faqat quyidagi lokal config
orqali topadi (ishchi papka ildizida): `opencode.json` → `"skills": ["./conduit/.opencode/skills"]`.
**Global `~/.config/opencode`, `~/.claude`, `~/.gemini` sozlamalariga tegilmadi.**

Lazim bo'lgan skilllar haqiqatan yuklandi (`systematic-debugging`, `verification-before-completion`,
`code-review-and-quality`, `security-and-hardening`, `observability-and-instrumentation`,
`karpathy-guidelines`, `webapp-testing`) va audit jarayonida qo'llanildi.

Manbalar:
- https://github.com/obra/superpowers
- https://github.com/addyosmani/agent-skills
- https://github.com/anthropics/skills
- https://github.com/multica-ai/andrej-karpathy-skills
- OpenCode skills discovery: https://opencode.ai/docs/skills/

## 2. DeepSearch + DeepX ishlatildi

**DeepSearch** (`POST /api/tools/deepsearch`):
- mavzu: `FastAPI async background task error handling and Playwright UI testing best practices`
- natija: `success=true`, `5 candidate`, hisobot:
  `research/fastapi_async_background_task_error_handling_and_playwright_ui_testing_best_practices.md`

**DeepX to'liq pipeline** (`POST /api/tasks`, `execution_mode=deepx`):
- `task_9d421f37`
- 5 ta citation (jumladan lokal `app_adapter.py`, `database.py`, `terminal_session.py`, `tool_registry.py`),
  4 ta thinking step (`problem_framing`, `architecture`, `security_audit`, `mvp_synthesis`),
  2 bosqichli swarm (`designer` → `inspector`).
- Loglarda `[SWARM Self-Healing] inspector xatolikka uchradi. Avtonom davolash ishga tushirilmoqda...` —
  ya'ni xato yuz berganda tizim uni yutmay, loglab davolashni boshlagan.
- Yakuniy holat: **PASS**, evidence: `DEEPX MVP YAKUNLANDI (Vaqt: 1156.51s). DeepSearch: 5 ta manba.
  Fikrlash chuqurligi: 4 bosqich. Loyiha: mvp_task_9d4 (4 ta modul). Sentinel Xavfsizlik Balli:
  100/100 (Sertifikatlangan).`

## 3. Audit topilmalari va dalillar

| # | Tekshiruv | Natija / dalil |
|---|---|---|
| 1 | Jim yutilgan xatolar | AST skani: **25 → 3**. Qolgan 3: ikkitasi test cleanup, bittasi oddiy polling pauzasi (izohlangan). 22 ta `except: pass` loglangan (`LOGGER.debug`/`warning`). |
| 2 | TODO / placeholder | `REAL_TODO_COUNT = 0` (TODO/FIXME/XXX/implement later bo'yicha skan). |
| 3 | UI accessibility (Playwright) | 1600×1000 va 1280×800: `imgs=0/no_alt=0`, `buttons=86/no_name=0`, `inputs=2/no_label=0`. |
| 4 | UI barqarorligi | `overflow_x=0, overflow_y=0, console_errors=0` (ikki viewport). |
| 5 | Maxfiy kalitlar | `SECRET_LIKE_HITS=4` — hammasi redaction test fixture'lari (`inspector_executor.py:80,82`, `tests/test_security.py:49,51`), haqiqiy kalit yo'q. |
| 6 | Dependency audit | `npm audit --omit=dev`: 2 zaiflik — `postcss` high va `next` moderate; tuzatish **faqat major upgrade** (Next 16.4.6) bilan. Majburiy `audit fix --force` qo'llanmadi; sabab: katta versiya sakrashi vaUI regressiya xavfi. Ko'rib chiqish sanasi: 2026-12-22. |
| 7 | Testlar | `pytest`: **123 passed, 2 skipped** (5 ta Windows proactor ResourceWarning — xato emas). Yangi `test_no_silent_except.py` auditni doimiy eshikka aylantiradi, `test_deepx_report_name.py` fayl nomi chegarasini himoya qiladi. |
| 9 | DeepX fayl nomi (commit paytida topildi) | 222 belgili hisobot nomi Windows `MAX_PATH` ga sig'madi va `git add` xato berdi. `deepx.py` da slug 75 belgiga qisqartirilib, mavzu hash'i qo'shildi; eski fayl `research/deepx_audit_nexus_studio.md` ga o'zgartirildi. |
| 8 | Build/health | `compileall 0`, `doctor 0 FAIL`, `tsc 0`, `lint 0`, `next build 0`. |

## 4. Tuzatishlar (surgical)

- `backend/app_adapter.py`, `database.py`, `main.py`, `subagent_creator.py`, `terminal_session.py`,
  `tools.py`, `user_memory.py`, `engine/cli_runner.py`, `engine/heavy_engine.py`:
  faqat jim `except: pass` bloklariga `LOGGER.debug`/`warning` qo'shildi; funksional xatti-harakat o'zgarmadi.
- `main.py:1446` dagi polling pauzasi izoh bilan qoldirildi (bu xato emas).
- Test/xizmat xatolari endi ko'rinadi — "xato yuz berdi, lekin hech qayerda yo'q" holati bartaraf etildi.

## 5. Qolgan kamchilik (halol)

`postcss`/`next` zaifliklari major upgrade talab qiladi. Bu o'zgarish ushbu vazifa doirasiga kirmaydi
(Karpathy: surgical changes) va majburiy avtomatik tuzatish xavfli. Keyingi qadam: alohida
`next@16` migratsiyasi + to'liq UI regression testlari.
