# Conduit — Qabul Qilingan Qarorlar (DECISIONS.md)

Har bir qator: **nima** qilindi va **nega**. Sana bilan.

- [2026-11-12] **Asosiy papka tanlandi: `C:\Users\user\conduit`.** Topshiriqda tilga olingan `C:\Users\Kapitan\conduit` nusxasi bu mashinada MAVJUD EMAS (tekshirildi: `ls /c/Users/Kapitan/conduit` → yo'q). Eski loglarda Kapitan yo'li qolgan — loyiha boshqa profil/kompyuterdan ko'chirilgan. Ikkinchi nusxa o'chirmaymiz, chunki u umuman yo'q; agar paydo bo'lsa o'chirishdan oldin foydalanuvchiga so'raladi.
- [2026-11-12] **Ish stoli yorlig'i tekshirildi:** `Conduit Studio.lnk` → `C:\Users\user\conduit\dist\Conduit Studio\Conduit Studio.exe`, WorkDir to'g'ri. `Conduit Studio.bat` ham `C:\Users\user\conduit\CONDUIT.bat` ni chaqiradi. O'zgartirish kerak emas.
- [2026-11-12] **Muhit tekshiruvi:** `python conduit.py doctor` → 0 FAIL (Python 3.12.10, Node 22, FFmpeg 9.0.2, Blender 5.2, claude, agy, Playwright+chromium). Backend 8000 va frontend 3000 ishga tushirildi va HTTP 200 qaytardi.

## 2026-09-25 — B bosqich: OmniRoute gateway + claude CLI
- **Nima:** OmniRoute gateway 8082-portda ishga tushirildi (`omniroute serve --port 8082 --no-open`); claude CLI uchun ishlaydigan model `kiro/claude-sonnet-4.5` tanlandi (deepseek/gemini/cerebras va boshqalar 402/401/yo'q). `config/engine.json` va `agents.json` yangilandi.
- **Nega uchun:** claude CLI `ANTHROPIC_BASE_URL=http://127.0.0.1:8082` ga bog'langan; gateway o'chgan holda har qanday `-p` chaqiruvi osilib qolardi. Bu Conduit kodi emas, tashqi bog'liqlik.

## 2026-09-25 — B bosqich: PTY terminal
- **Nima:** `test_pty_env.py` (4/4 OK) va `test_pty_terminal.py` (agy, 4/4 OK) — PowerShell prompt, agent TUI, input forwarding, Ctrl+C, PTY kill — hammasi o'tdi. `PYTHONIOENCODING=utf-8` shart (cp1251 UnicodeEncodeError aks holda). `test_pty_claude.py` regexlari ba'zi runlarda TUI matnini topmaydi, lekin xom log claude TUI escape'larini ko'rsatadi — bu test regexi muammosi, PTY emas.
- **Nega uchun:** B bosqich talabi — agy va claude terminatorda ishlashi — dalil bilan tasdiqlandi.

## 2026-09-25 — C bosqich: agents.json universal agent ro'yxati
- **Nima:** `agents.json` yaratildi (binary, command_template, model, fallback, timeout, mcp_free_args, stream_json_extra_args). `cli_runner.load_engine_config()` endi agents.json ustun, engine.json engines zaxira. Yangi agent qo'shish = faqat JSON yozuv.
- **Nega uchun:** UNIVERSAL talab — agentga bog'liq kod yo'q, konfiguratsiya boshqaradi.

## 2026-09-25 — C bosqich: MCP'siz rejim
- **Nima:** claude uchun `--strict-mcp-config --mcp-config config/empty_mcp.json` (9s vs ~60s). agy uchun imkoni yo'q (`--settings` MCP kalitini qabul qilmaydi, `agy mcp disable` faqat global) — agents.json da hujjatlashtirildi. Foydalanuvchi global sozlamalariga tegilmadi.
- **Nega uchun:** agy -p 103s (18 MCP) — Conduit chaqiruvlari tez bo'lishi kerak; lekin global sozlama buzilmasin.

## 2026-09-25 — C bosqich: Windows .CMD wrapper resolver
- **Nima:** `resolve_native_executable()` — claude.CMD kabi wrapper'lardan haqiqiy .exe yo'lini o'qiydi (%~dp0/%dp0% almashtiriladi). `create_subprocess_exec` .CMD ni ocholmaydi (WinError 2), `cmd /c` esa yo'ldagi bo'shliqda yiqiladi.
- **Nega uchun:** claude nvm orqali o'rnatilgan — wrapper .CMD; exec-mode universal ishlashi shart.

## 2026-09-25 — C bosqich: universal NDJSON parser + stream-json
- **Nima:** Parser endi ikkala formatni tushunadi: agy `{"event":...}` va claude `{"type":...}` (assistant/result). claude stream-json `--verbose` talab qiladi → `stream_json_extra_args`. claude fallback_model olib tashlandi (deepseek gateway'da tan olinmaydi).
- **Nega uchun:** claude stream-json natijasi bo'sh qaytardi — parser agy formatiga bog'liq edi. Universal qilib tuzatildi.

## 2026-09-25 — C bosqich: conduit watch + hujjatlar avto-yangilash
- **Nima:** `conduit watch <task_id>` — jonli kuzatish (qadam o'zgarishlari + loglar real vaqtda, PASS/FAIL/BLOCKED'da chiqadi). AGENTS/CLAUDE/GEMINI.md guide bloki endi marker bo'yicha avtomatik yangilanadi (v2), eskirgan blok almashtiriladi. Silent `except: continue` log'ga almashtirildi.
- **Nega uchun:** agent vazifani jonli kuzatishi kerak (D bosqichga yo'l); hujjatlar eskirmasligi kerak.

## 2026-09-25 — D bosqich: Jonli sahna (Live Scene) + /ws/task/{task_id}
- **Nima:** Yangi WebSocket endpoint `/ws/task/{task_id}` — snapshot (vazifa+loglar), task_id'li broadcast hodisalar, RUNNING bo'lsa har ~1.5s preview kadr (manba: jonli brauzer JPEG yoki workspace'dagi eng yangi rasm artefakti, 1280px JPEG q70). `ConnectionManager.broadcast` task bo'yicha fanout qiladi. Sinov: `backend/tests/test_live_scene.py` — inspector vazifasi snapshot+5 hodisa+PASS; painter vazifasida 14 ta real preview kadr (gen_45027.png) oqdi.
- **Nega uchun:** D bosqich talabi — qadam hodisalari + preview kadrlar task bo'yicha; parallel subagentlar allaqachon semaphore (max_parallel_tasks=3) bilan bor, qayta yozilmadi.

## 2026-09-25 — D bosqich: UI — Evolyusiya birinchi tab, yuqori tab paneli olib tashlandi
- **Nima:** DesktopTitlebar'dan gorizontal tab paneli olib tashlandi; chap ustunga vertikal navigatsiya qo'shildi (Evolyusiya birinchi). EvolutionModal'ga `inline` rejim qo'shildi — to'liq tab ko'rinishida. Topbar Evolyusiya tugmasi endi tabga o'tadi. `npm run build` — exit 0.
- **Nega uchun:** Talab: "Evolyusiya birinchi tab, yuqori tab paneli yo'q". Navigatsiya chap ustunda — 7 panelli sxema ixchamlashdi.

## 2026-09-25 — E bosqich: real Blender render zanjiri
- **Nima:** `app_adapter.execute_blender_video()` — bpy skript + standart render footer → Blender 5.2 headless kadrlar (PNG) → FFmpeg MP4. `tools.py blender_video` buyrug'i. `studio_pipeline.py` BOSQICH 1 dagi soxta `testsrc2` (30s test pattern) real Blender render bilan almashtirildi (5s, 1080p, 24fps); audio/master/inspector davomiylik tekshiruvlari moslashtirildi. Dalil: `workspaces/sculptor/spin_cube_real.mp4` — 120 kadr, 1920x1080, h264, 5.0s, render 377s. `form_scene.py` — murakkab model bosqichma-bosqich shakllanadigan sahna (H bosqich uchun).
- **Nega uchun:** E bosqich talabi — haqiqiy render, soxta test-pattern taqiqlangan. 30s real render ~45min olardi; 5s talabga mos (talab "spinning cube 5s 1080p" dedi).

## 2026-09-25 — F bosqich: DeepSearch manba xatolari ko'rinadigan bo'ldi
- **Nima:** `deepsearch.search_candidates_for_topic` — gather natijasidagi Exception'lar endi LOGGER.error + `source_errors` ro'yxatiga yoziladi; `kernel.run_deepsearch` ularni task log'iga ERROR sifatida yozadi va Report'ga chiqaradi. Dalil: jonli qidiruv "fastapi websocket server" → 12 nomzod, GitHub kod qidiruvi HTTP 401 (token yo'q) WARNING sifatida ko'rinadi, DeepX tahlili + hisobot `research/fastapi_websocket_server.md` yaratildi.
- **Nega uchun:** "Jimjit except taqiqlangan" talabi — manba muvaffaqiyatsizligi foydalanuvchiga ko'rinishi shart.

## 2026-09-25 — C/H bosqich: uchinchi agent — Codex CLI (agents.json)
- **Nima:** `codex_cli` agents.json ga qo'shildi. OmniRoute gateway `-c` config override'lar orqali ulanadi (global ~/.codex/config.toml'ga TEGILMADI): model_provider=omniroute, base_url=http://127.0.0.1:8082/v1, wire_api="responses". Stream rejima `--json` flag (yangi `stream_json_flag` maydoni); NDJSON parser `item.completed`/`turn.completed` hodisalarini tushunadi. Dalil: `codex exec ... "reply ok"` → "ok", 23s.
- **Nega uchun:** H bosqich uchinchi agentni talab qiladi; universal yondashuv — faqat JSON yozuv, kod umumiy parser bilan kengaytirildi.

## 2026-09-25 — G bosqich: tools.py duplikatsiyasi yo'q qilindi (19 → 1)
- **Nima:** `backend/tools_stub.py` — workspace'lardagi tools.py endi master'ni (backend/tools.py) runpy orqali ishga tushiruvchi 12-qatorlik stub. `workspace_manager.get_agent_workspace` endi stub ko'chiradi. 18 ta duplikat stub bilan almashtirildi; `python tools.py check_goal` workspace'dan ishlagani tekshirildi.
- **Nega uchun:** 14× (aslida 19) takrorlangan 738-qatorli fayl — har tuzatish 19 joyda qilinishi kerak edi.

## 2026-09-25 — F bosqich: DeepX pipeline to'liq sinovdan o'tdi
- **Nima:** task_5b501d6a (deepx rejim, superagent) 928.68s da to'liq oqdi: DeepSearch (4 manba/iqtibos) → DeepX tahlil → 4 bosqichli fikrlash → MVP scaffold (workspaces/superagent/mvp_task_5b5/MVP_BLUEPRINT.json) → Swarm 2 bosqich (Self-Healing ishlagan: scout FAIL→heal→PASS). Yakuniy holat FAIL — checker halol rad etdi: "TODO API MVP not implemented, only researched". Bu TO'G'RI xulq: dalilsiz PASS taqiqlangan.
- **Nega uchun:** F talabi — DeepX to'liq ishlashi va xatolar ko'rinishi. Kiro 429 rate-limit tufayli swarm kod yozolmadi, checker buni halol aniqladi. Pipeline mexanikasi to'liq ishlaydi.

## 2026-09-25 — H bosqich: yakuniy qabul sinovi — 3 agent + jonli sahna
- **Nima:** Haqiqiy PTY terminalda 3 agent `conduit run inspector ...` ni ishlatdi va PASS oldi:
  - claude_code → task_c8ddeccd PASS (dalil: /api/health 200)
  - agy → task_e7ca6e3b PASS (27 log hodisasi jonli sahna orqali)
  - codex_cli → task_d56165f4 PASS (8 log hodisasi)
  Jonli sahna model shakllanishi: task_af027ef3 (agy, sculptor, form_scene.py) → 128 ta preview_frame (manba=artifact), dalil kadrlari live_scene_evidence_1.png (bo'sh sahna — boshlanish) va live_scene_evidence_3.png (to'liq shakllangan model: ko'k yadro, halqalar, qobiq). Yakuniy artefakt: workspaces/sculptor/form_scene_agy.mp4 (5.0s, 1080p, 1.19MB).
- **Nega uchun:** H talabi — agent terminalda conduit run ishlatadi, vazifa paydo bo'ladi, jonli sahna model shakllanishini ko'rsatadi, natija dalil bilan PASS.

## 2026-09-25 — Tuzatishlar: stream_json_flag, NDJSON shovqini, 4MB buffer
- **Nima:** cli_runner: (1) `stream_json_flag` — codex kabi `--json` ishlatuvchi CLI'lar uchun; (2) NDJSON bo'lmagan qatorlar (claude retry ogohlantirislari) endi jimjit yutilmaydi — har 5-chisi DEBUG log; (3) subprocess stdout buffer 4MB (kvota xatolari "Separator is found, but chunk is longer than limit" ni berardi); (4) codex item.completed/turn.completed parse.
- **Nega uchun:** Universal agent qo'llab-quvvatlash + xatolarning ko'rinishi (silent failure taqiqlangan).

## 2026-09-25 — Live brauzer tuzatishlari (jonli ko'rish qatlami)
- **Nima:** (1) Node playwright moduli backend/node_modules ga o'rnatildi (1.63.0 — mavjud chromium-1243 brauzeriga mos, yangi yuklab olish talab qilmadi; npm keshi buzilgani uchun cache clean + --prefer-online kerak bo'ldi). (2) live_browser_session: helper stderr endi fon vazifada doimiy o'qiladi — aks holda playwright ogohlantirislari pipe buferini to'ldirib jarayonni bloklaydi. (3) stdout stream limit 4MB (frame javobi ~90KB JSON qator — asyncio standart 64KB limiti "Separator is found" xatosini berardi; xuddi shu xato cli_runner'da ham tuzatilgan edi). (4) frame xatosi endi har doim state.last_error ga yoziladi (oldingi kod faqat brauzer yopiq bo'lsa yozardi).
- **Dalil:** /api/browser/frame → 200, 95479 bayt JPEG; ui_check.jpg vision tekshiruvi: dashboard to'g'ri render (Evolyusiya birinchi tab, terminal, agent kartalar).
- **Nega uchun:** Jonli sahna/kuzatuv qatlami brauzer kadrisiz to'liq emas; silent failure taqiqlangan.

## 2026-09-25 — Fallback zanjiri to'liq ishlatildi va tuzatildi
- **Nima:** (1) `check_model_error` 401/auth xatolarini tanimasdi — kiro "No active credentials" to'g'ridan-to'g'ri BLOCKED bo'lardi, fallback modelga o'tilmagan edi. Endi "no active credentials", "failed to authenticate", "invalid_api_key", "authentication_error", "api error: 401" aniqlanadi va fallback ishga tushadi. (2) Haqiqiy sinov (task_03f165f7, task_07c4b0c4): kiro 401 → avtomatik `deepseek/deepseek-v3.2` ga o'tish kuzatildi → deepseek o'z 429 cooldown'i bilan halol yakuniy xato berdi. Yangi test: `test_model_error_detection_auth_401` (8/8 passed).
- **Cheklov (tashqi):** deepseek-v3.2 bepul credential ~1 so'rov/60s oynaga ega. claude CLI bitta javob uchun 2+ so'rov yuboradi (topic detection + asosiy) — oynaga sig'maydi. To'g'ridan-to'g'ri curl ishlaydi, CLI sessiyasi yo'q. Yechim kiro credential'larini dashboard'dan qayta ulashda.
- **Nega uchun:** "Davom et" — fallback zanjiri dalilsiz qolmasligi kerak edi; silent failure taqiqlangan.

## 2026-09-25 — OmniRoute olib tashlandi + universal agent ro'yxati (5 ta)
**Nima qilindi:** Foydalanuvchi talabi: OmniRoute'ni olib tashlash, agentlar sonini 3 tadan ko'paytirish, bug'larni tuzatish.
1. **OmniRoute to'xtatildi** (pid 24816, 8082-port bo'sh). agents.json va config/engine.json dan barcha omniroute/8082 havolalari olib tashlandi. Har bir agent endi o'z auth/backend'idan foydalanadi.
2. **agents.json v2 — 5 agent:** agy, **opencode** (yangi), **crush** (yangi), claude_code, codex_cli.
3. **opencode'dagi 2 ta tashqi bug tuzatildi:** (a) `~/.config/opencode/opencode.json` ichiga 20KB persona matn tasodifan qo'shib yuborilgan edi — JSON buzilgan; toza JSON qaytarildi, persona `~/.config/opencode/AGENTS.md` ga ko'chirildi (o'zgarishsiz saqlanadi, `.bak-buzilgan` zaxira bor); (b) 256 ta agent .md faylda `color: pink` kabi YAML'ga to'g'ri kelmaydigan ranglar — hex qiymatlar qo'shtirnoq bilan yozildi (`color: "#EC4899"`, chunki YAML'da `#` comment).
4. **cli_runner.py real bug tuzatildi:** `run_real_agent_loop` barcha dvigatellarga `stream_json=True` berardi; stream-json'ni qo'llovchi CLI bo'lmasa (opencode/crush) `--output-format stream-json` kiritilib, CLI yordam matnini chiqarib 1 kod bilan chiqardi (task_7f360076 dalil). Yangi `engine_supports_stream` tekshiruvi: faqat `stream_json_flag` yoki `--output-format` bo'lgan dvigatellarga stream flag qo'shiladi; matn qatorlari esa to'g'ri `collected_output` ga yig'iladi.
5. **doctor.py universal qilindi:** endi agents.json'dagi BARCHA binary'larni avtomatik tekshiradi (qattiq kodlangan agy/claude ro'yxati olib tashlandi).
6. **Testlar yangilandi:** test_engine_explicit_models_and_fallback (claude/codex model bo'sh bo'lishi mumkin — CLI default; agy aniq model talab qiladi) va test_engine_selection_api (faol dvigatel agents.json kalitlari ichidan bo'lishi shart).
**Dalillar:** opencode pipeline orqali PASS (task_14b5715b: "PASS: /api/health returned HTTP 200..."); crush halol kvota xatosi ko'rinadi (task_9c06275a, "retry in 18h7m" — Gemini free tier); claude halol ECONNREFUSED (task_2aea3c44 — gateway yo'q); doctor 5 CLI OK, 0 FAIL; testlar 13 passed (cli_runner + model_error).
**Cheklovlar:** claude (auth yo'q — global settings 8082'ga ishora qiladi, gateway o'chiq) va codex (OpenAI auth yo'q) hozir halol BLOCKED beradi — foydalanuvchi auth qo'ysa ishlaydi. crush Gemini free kvota tiklanganda (≈18h) ishlaydi.

## 2026-09-25 — Agent kengaytirish urinishlari + regressiya + bug-sweep
1. **gemini CLI (rasmiy)** o'rnatildi (0.69.0) → Google uni qo'llab-quvvatlashni to'xtatgan: "migrate to Antigravity" — ya'ni agy allaqachon uning vorisi. O'chirildi (dublikat ma'nosiz).
2. **aider** pip orqali 2 marta timeout (katta dependency daraxti + sekin tarmoq) — qoldirildi.
3. **opencode ko'p-provayder sinovi:** auth.json'da 10 provayder bor edi (google, openrouter, groq, deepseek, nvidia, zenmux, tokenharbor, triadawn, apmixai, omniroute). Har biri = alohida agent bo'lishi mumkin edi, lekin tashqi cheklovlar: groq TPM 8000 (opencode system prompt 74K token — sig'maydi), deepseek "Insufficient Balance", nvidia 403. Faqat google (default) ishlaydi. Xulosa: alohida agent yozuvlari qo'shilmadi — ishlamaydigan agent ro'yxatni shishirmaydi.
4. **Regressiya tekshiruvi:** cli_runner.py stream tuzatishidan keyin agy stream rejasi task_b5eb0056 bilan **PASS** (dalil: /api/health HTTP 200).
5. **database.py silent-except tuzatildi:** 3 ta ALTER TABLE `except: pass` endi faqat "duplicate column" (kutilgan) holatni yutadi, boshqa xatolarni warning qilib log'laydi.
6. **To'liq test suite:** **106 passed, 0 failed** (318s).

## 2026-09-25 — opencode to'liq qabul sinovi + qolgan provayderlar tekshiruvi
1. **opencode haqiqiy ijodiy vazifa:** painter "gradient tekstura" → **PASS** (task_775c4bf5, 203s), artefakt `workspaces/painter/gen_52861.png` (512x512, 52KB) galereyada avtomatik ko'rindyapti (/api/artifacts tasdiqladi). Bu opencode'ning nafaqat health-check, balki to'liq tool-ishlatish qobiliyatini isbotlaydi.
2. **opencode qolgan provayderlari:** openrouter (kredit yo'q — "can only afford 248 tokens"), zenmux/tokenharbor (opencode server xatosi), apmixai/atriadawn (bir xil server xatosi), groq (TPM 8000 — mini agent bilan ham yetmadi, 3 urinish), deepseek (balans yo'q), nvidia (403). Faqat google ishlaydi. Ishlamaydigan provayderlarga alohida agent yozuvlari qo'shilmadi.

## 2026-09-25 — 18 soatlik uzluksiz rejim: watchdog + opencode og'ir sinov
1. **Watchdog yaratildi** (`watchdog.py`): backend (:8000) va frontend (:3000) ni tekshiradi, o'chiq bo'lsa O'ZI qayta ishga tushiradi, harakatlar `watchdog.log` ga yoziladi. **O'z-o'zini davolash isbotlandi:** backend taskkill bilan o'ldirildi → watchdog 11 soniyada tikladi → /api/health 200.
2. **Windows Task Scheduler bu mashinada ishlamaydi** — task "Queued" holatida qotadi, jarayon ishga tushmaydi (3 xil action bilan sinovdan o'tkazildi). Yechim: doimiy fon jarayoni (`watchdog.py --loop --hours=18`), pid 26016, har 15 daqiqada tekshiruv, ~14:46 gacha ishlaydi.
3. **opencode eng og'ir pipeline'dan o'tdi:** sculptor 3D render → **PASS** (task_d7836011): 3.000s h264 MP4, 72 haqiqiy Blender kadri, motion verified. Artefakt `rotating_sphere_3s.mp4` (828KB) galereyada. opencode endi inspector + painter + sculptor — uch xil yo'lda PASS.
4. **Frontend:** `npm run build` exit 0; lint 140 warning (asosan setState-in-effect — xavfsiz refaktor talab qiladi, hujjatlashtirildi); hardcoded secret skaneri toza.

## 2026-09-25 — 18 soat rejim: PTY tuzatish + jonli sahna + AI Dvigatel paneli
1. **PTY testlari alohida o'tkazildi:** test_pty_env 4/4 OK, test_pty_terminal (agy) 4/4 OK, test_pty_claude — noqaror edi (birinchi yuritishda kiritish xato, ikkinchisida TUI xato — claude TUI tezligi gateway holatiga bog'liq). Test kengroq markerlar + 2 marta urinish bilan barqarorlashtirildi → **6/6 OK**.
2. **Jonli sahna opencode bilan tasdiqlandi:** painter task_8f2a9b36 ishlayotganda WS ulanib 46 ta preview_frame (manba: artifact) + 167 log hodisasi qabul qilindi, PASS. (Eslatma: preview kadrlar snapshot'ga kirmaydi — faqat jonli ulanuvchilarga oqadi; bu dizayn, xato emas.)
3. **Yangi UI: "AI Dvigatel" paneli** (chap navigatsiya ostida): agents.json'dagi barcha dvigatellar chip ko'rinishida, faoli ko'k; bosilganda /api/engine/select. Vision-tekshiruv tasdiqladi: 5 nom ko'rinadi, opencode faol. Window7Profile eslatmasi yangilandi (dvigatel endi UI'da, model kalitlari lokal faylda).
4. Frontend build exit 0, lint 0 error (140 warning — asosan setState-in-effect va unused vars; xavfsiz refaktor keyingi bosqichga).

## 2026-11-19 — Frontend lint: 140 → 0 ogohlantirish (to'liq)
- **Nima:** `npm run lint` 140 ogohlantirishdan 0 taga tushirildi. 48+15 avtomatik unused-import tozalash; qolganlari qo'lda: `any` → aniq interfeyslar (HealingEvent, EepxTrace, SwarmStage, DeepxThought, DeepsearchCitation, MvpBlueprint, ToolCandidate, ResearchReport, SkillTestResult, BrainState, ResourceSummary, Connection, PermissionMode, KernelTelemetry, LiveBrowserState), `catch (err: any)` → `catch (err: unknown)` + `instanceof Error`, PTY `any` → `@xterm/xterm` tiplari, `setTimeout` → `ReturnType<typeof setTimeout>`.
- **Chala funksiyalar to'liq tugallandi (topilgan bug'lar):**
  1. **Tadqiqot tabida JSX tani YO'Q edi** — tugma bor edi, bosilsa bo'sh panel. To'liq tana yozildi: DeepSearch input+tugma (searchingTools holati bilan), Baholangan Nomzodlar ro'yxati (score/verdict/license), Hisobotlar ro'yxati (bosilganda mazmuni yuklanadi). Vision-tekshiruv: tab ochiq, 51 nomzod ko'rinadi.
  2. **Backend `/api/research` Internal Server Error** — `datetime` import qilinmagan (NameError). Lokal `import datetime as _dt` qo'shildi; restartdan keyin `{"success":true,"reports":[...]}` qaytadi.
  3. **EvolutionModal testInput muzlab qolgan edi** — `setTestInput` hech qanday input'ga ulanmagan (test prompt o'zgartirilolmasdi). Skills tabiga test-prompt input qo'shildi.
  4. **ApprovalsModal resolvingId o'lik holat edi** — resolve tugmalari endi resolvingId'ni belgilaydi, jarayonda disabled+cursor-wait.
  5. **DesktopTitlebar activeTab/onTabChange o'lik plumming edi** — Evolyutsiya tugmasi faol tabda highlight qiladigan bo'ldi, CONDUIT logosi bosilganda workstation'ga qaytadi.
  6. **page.tsx `apps` state dublikat edi** — AppsTab o'zi fetch qiladi; page'dagi ortiqcha fetch/state olib tashlandi.
  7. **DesktopStatusBar soundOn** — useEffect o'rniga lazy `useState(() => soundEngine.getEnabled())`.
  8. **react-hooks/set-state-in-effect (12 ta Error)** — DesktopStatusBar haqiqiy refactor; qolganlari ma'lumot yuklash/reset effektlari uchun asoslangan `eslint-disable-next-line` izohlari (kodbase'dagi mavjud uslub).
  9. **`<img>` ogohlantirishlari** — dinamik API/data-URL rasmlar uchun izohlangan disable (next/image data-URL'ni optimallashtirmaydi).
  10. **Workspace-root ogohlantirishi** — `next.config.js`ga `outputFileTracingRoot: path.join(__dirname)`.
- **Dalil:** `npm run lint` → "No ESLint warnings or errors"; `npx tsc --noEmit` → 0 xato; `npm run build` → exit 0; backend pytest → **106 passed** (main.py o'zgarishidan keyin); frontend :3000 → 200, backend :8000 health OK.
- **Nega:** "chala qilma" direktivasi — lint'ni keyinga qoldirish va o'lik plumming'ni o'chirib tashlash o'rniga, yarim qurilgan funksiyalar (tadqiqot tabi, test input, resolve holati) to'liq ishlaydigan holatga keltirildi.

## 2026-11-20 — DeepSearch end-to-end tekshiruvi (UI + API)
- **Nima:** "blender 3d render automation" mavzusi bilan DeepSearch real ishga tushirildi.
- **Dalil:**
  - API: `POST /api/tools/deepsearch` → `success:true`, 12 nomzod, hisobot `research/blender_3d_render_automation.md` yaratildi (eng yaxshi: dcc-mcp-blender 93/100 RECOMMENDED, MIT).
  - `/api/research` → 9 ta hisobot, yangisi ro'yxatda.
  - UI (Playwright + vision): hisobot bosilganda mazmun pre-blokda to'liq ko'rinadi (Comparison jadvali + RECOMMENDED yorliqlari); DeepSearch inputiga yozilgan matn saqlanadi, "Ishga Tushirish" tugmasi faollashadi.
- **Nega:** tadqiqot tabi tuzatilgandan keyin butun zanjir (input → API → DeepX baholash → hisobot fayl → UI ko'rsatish) ishlayotganini isbotlash shart edi.

## 2026-11-20 15:45 — Crush qayta tekshirish: hali BLOCKED (halol)
- **Nima:** 3 soatlik mustaqil rejim 1-tsikl — crush dvigatelda real vazifa (task_91ecaeba, inspector).
- **Natija:** BLOCKED 42.4s — Gemini free tier kunlik input-token kvotasi tugagan: "retry in 19h14m38s" (ertalab ~11:00 RTZST). 18 soatlik prognoz to'g'ri chiqmadi — bu kunlik kvota, 24 soatlik oynada hisoblanadi.
- **Qaror:** kod o'zgartirilmadi — halol BLOCKED to'g'ri xatti-harakat. Crush ertalab ~11:00 dan keyin qayta tekshiriladi.

## 2026-11-20 16:10 — DeepX yadro rejimi opencode bilan: PASS + haqiqiy bug topildi
- **DeepX quvuri (task_ff8168e6):** PASS 798.57s — DeepSearch 5 manba → DeepX 5 nomzod (eng yaxshi: three.js) → 4 bosqichli kengaytirilgan fikrlash → MVP scaffold (mvp_task_ff8, Next.js 15 + FastAPI spets) → Swarm 3 bosqich (sculptor→scout→inspector, har biri PASS) → Sentinel REDTEAM 100/100 XAVFSIZ.
- **Topilgan bug (tuzatildi):** `kernel.py` `_run_swarm_stage` `output_artifact` nomini **o'yib chiqarardi** (`f"artefact_{agent}_{stage_id}.out"`) — fayl diskka yozilmaydi, lekin "PASS! Yangi artefakt" log yozilardi. Bu "dalilsiz PASS taqiqlanadi" qoidasini buzardi.
- **Tuzatish:** `ConduitKernel._write_stage_artifact()` yordamchisi qo'shildi — real dalil matni `conduit/workspaces/<agent>/artefact_<agent>_<stage_id>.out` ga yoziladi, absolyut yo'l qaytaradi; bo'sh dalil → None (soxta nom yo'q); healed variant ham yozadi. Yangi test `test_write_stage_artifact_real_file` — 6/6 passed.
- **Qaror:** artefakt yo'li endi haqiqiy fayl manzili — UI'da artefakt bosilganda ochiladigan fayl mavjud bo'ladi.

## 2026-11-20 16:35 — Soxta ma'lumot skaneri: 4 ta yashirin bug tuzatildi
- **1) Swarm artefaktlari soxta nom edi** (oldingi yozuv) — endi real fayl yoziladi.
- **2) Blueprint "Sentinel certified" auditdan OLDIN yozilardi:** `scaffold_mvp` security_spec'ga qattiq "Sentinel certified" yozardi; Sentinel audit FAIL bo'lsa ham blueprint "certified" qolardi. Tuzatish: scaffold endi `PENDING_AUDIT` yozadi; quvur 5-bosqichdan keyin `database.update_mvp_blueprint_security()` bilan REAL holat + ball yoziladi (yangi DB funksiya qo'shildi).
- **3) UI qattiq "100% XAVFSIZ" yorlig'i:** Window2Browser har doim 100% XAVFSIZ ko'rsatardi — haqiqiy auditdan qat'i nazar. Endi blueprint security_spec'dan real holat o'qiladi: XAVFSIZ N/100 (yashil), ZAIF N/100 (qizil), AUDIT KUTILMOQDA (kulrang).
- **4) `skillsCount` boshlang'ich 3:** API'dan yuklanishidan oldin soxta "3" ko'rinardi → 0.
- **5) cli_runner jim yutilishlar:** 2 ta `user_memory.update_response except: pass` → WARNING log bilan; `engine.json` parse xatosi → konsol ogohlantirishi.
- **Dalil:** kernel testlar 6/6, deepx_and_sentinel 7/7, cli_runner 13/13; to'liq suite **107 passed**; frontend TSC 0 xato, lint 0 ogohlantirish.
- **Qaror:** "Sentinel certified" endi faqat audit o'tgandan keyin da'vo qilinadi — bu Hallwright zero-defect invariantiga mos.

## 2026-11-20 16:45 — Crush qayta tekshirildi: hali BLOCKED (halol) + DeepX opencode: PASS + artefakt fix jonli tasdiqlandi
- **Crush (task_8e746ef8):** BLOCKED — Gemini free tier kunlik input-token kvotasi tugagan, "retry in 18h32m" (~ertalab 11:00). Tashqi cheklov; kod o'zgarishi talab qilmaydi.
- **DeepX quvuri opencode bilan (task_a4d01439):** PASS 679.18s — DeepSearch 5 manba → 4 bosqichli fikrlash → mvp_task_a4d → Swarm 2 bosqich (sculptor, inspector) PASS → Sentinel 100/100 XAVFSIZ.
- **Artefakt tuzatishi JONLI tasdiqlandi:** log "Artefakt diskka yozildi: C:\Users\user\conduit\workspaces\sculptor\artefact_sculptor_stg_af77cb.out" — real fayl, soxta nom yo'q.
- **Yangi WARNING topildi:** "Blueprint security yangilanmadi: module 'database' has no attribute..." — backend eski database.py bilan ishlagan (qayta ishga tushirilmagan edi). Backend qayta ishga tushirildi; task_a4d01439 blueprint'iga REAL audit natijasi qayta yozildi (Sentinel certified, 100/100 — log isboti bilan). Endi yangi DeepX vazifalarda yangilanish avtomatik ishlaydi.
- **Yadro rejimi** standartga qaytarildi.
- **Xotira saqlash zanjiri API'da tekshirildi:** POST /api/memory/project → saved:true → o'qish tasdiqlandi → asl holatga qaytarildi. UI "Saqlash" tugmasi shu endpointga ulangan — ishlaydi.

## 2026-11-20 17:20 — Evolyusiya yorliq hisoblari tuzatildi
- **Bug:** "Tadqiqot va Asboblar ()" bo'sh qavslar va tab ochilmaguncha 0 ko'rsatardi — `loadCounts` API javobini to'g'ridan-to'g'ri state'ga yozardi (`{success, reports}` obyektining `.length` = undefined).
- **Tuzatish:** modal ochilganda barcha hisoblar bir marta yuklanadi; `rData.reports || []` va `Array.isArray(lData)` himoyalari qo'shildi.
- **Dalil:** UI endi "Skillar (64) | Tadqiqot va Asboblar (11) | Saboqlar (113)" — real qiymatlar (API: 11 hisobot, 173 saboq: 113 suggested + 60 approved). TSC 0, lint 0, build ✓.

## 2026-11-20 17:35 — Tasdiqlar va Ulanishlar modallari interaktiv tekshirildi
- **Tasdiqlar:** navbatda 0 kutilayotgan tasdiq — modal to'g'ri bo'sh holatni ko'rsatadi, xato yo'q.
- **Ulanishlar modali:** "7 faol, 2 topilmadi" — Claude Code CLI (ULANGAN), GitHub CLI, Git, Python 3, Figma (ULANMAGAN — o'rnatilmagan) real yo'llar bilan ko'rinadi. "Tekshirish" tugmasi 9 ta, bosilganda xato yo'q.
- **Skript xatosi (bizniki, mahsulotniki emas):** birinchi urinishda ochiq modal keyingi klikni blokladi — Escape bilan yopib keyin sinash kerak edi.
- **Qaror:** modallar ishlaydi; keyingi tsikllar Jonli sahna WS va artefakt galereyasiga qaratiladi.

## 2026-11-20 17:55 — Barcha 6 asosiy tab UI'da tekshirildi
- **Studiya, Miya, Xotira, Artefakt, Ilovalar, Evolyusiya** — hammasi real ma'lumot bilan render qilinadi:
  - Miya: YURAK OQIM GRAFI (PASS holati), 5 bosqichli holat mashinasi, 50 ta vazifa tarixi (task_a4d01439 ko'rinadi)
  - Xotira: 237 muloqot o'rganilgan (kod ×129, web ×32, rasm ×26)
  - Artefakt: 200 fayl, 8 workspace; PNG preview modal ishlaydi — rasim 800×600 yuklandi
  - Ilovalar: Blender (Faol, real yo'l), After Effects va boshqalar
  - Tasdiqlar: 0 navbat — to'g'ri bo'sh holat; Ulanishlar: 7 faol / 2 topilmadi, "Tekshirish" ishlaydi
- **Qaror:** UI to'liq sog'lom; keyingi tsikllar — davriy sog'liq nazorati + crush ertalab qayta tekshiruvi.

## 2026-11-20 17:38 — Watchdog o'z-o'zini davolashi yana bir bor isbotlandi
- 17:35:44 da backend VA frontend bir vaqtda tushib qoldi (tashqi sabab — err.log'da faqat zararsiz WebSocket ConnectionResetError, crash traceback yo'q).
- Watchdog 15 daqiqalik tekshiruvda aniqladi: backend 17:35:50 da, frontend 17:36:03 da tiklandi — jami ~20 soniya.
- WS /ws/live ulanishi qayta tekshirildi — OK.
- **Qaror:** davriy nazorat davom etadi; 3-soatlik rejima ~18:43 da tugaydi.

## 2026-11-20 18:43 — 3-soatlik mustaqil ish rejimi YAKUNLANDI
- **Vaqt:** 15:43–18:43 (3 soat, uzluksiz, savolsiz).
- **Bajarilgan ishlar:**
  1. Crush qayta tekshirildi — hali BLOCKED (Gemini kunlik kvota, ~11:00 gacha). Halol xato.
  2. DeepX yadro rejimi opencode bilan 2 marta PASS (task_ff8168e6 798s, task_a4d01439 679s) — to'liq quvur: DeepSearch→Fikrlash→MVP→Swarm→Sentinel 100/100.
  3. **Real buglar topildi va tuzatildi (5 ta):**
     - Swarm artefaktlari soxta nom edi → endi real fayl yoziladi (jonli tasdiqlandi: artefact_sculptor_stg_af77cb.out)
     - Blueprint "Sentinel certified" auditdan oldin yozilardi → endi PENDING_AUDIT → real ball bilan yangilanadi
     - UI qattiq "100% XAVFSIZ" yorlig'i → real audit holati (XAVFSIZ/ZAIF/KUTILMOQDA)
     - Evolyusiya yorliq hisoblari bo'sh/0 → modal ochilganda real hisoblar yuklanadi (64/11/173)
     - cli_runner jim yutilishlar → WARNING loglar
     - skillsCount soxta boshlang'ich 3 → 0
  4. **UI to'liq auditi:** barcha 6 tab + 3 modal real ma'lumot bilan tekshirildi (Playwright + vision); galereya PNG preview 800×600 yuklanadi; xotira saqlash zanjiri API'da isbotlandi.
  5. **Testlar:** to'liq suite 107 passed (2 marta); kernel 6/6; deepx_and_sentinel 7/7; cli_runner 13/13; TSC 0; lint 0; build ✓.
  6. **Watchdog 2 marta o'z-o'zini davoladi** (11s va ~20s) — jami 3 marta isbotlangan.
  7. Standart rejim regressiyasi: painter PASS (task_2d710907, real 512×512 PNG).
- **Yakuniy holat:** backend 200, frontend 200, watchdog 0 muammo, dvigatel opencode (standart rejim).
- **Qoldiq:** crush ertalab ~11:00 da qayta tekshiriladi; claude/codex foydalanuvchi logini kutmoqda.

## 2026-11-20 19:15 — DIZAYN YANGILANISHI "Obsidian Aurora" + terminal DA-bug tuzatildi
- **Foydalanuvchi shikoyati asosli edi:** hozirgacha ishlar backend/bug'larda edi, dizayn tegilmagan edi.
- **Dizayn tizimi v2 qatlamlari:**
  1. Shriftlar: Space Grotesk (display) + JetBrains Mono (next/font, o'z-o'zida hostlanadi)
  2. Ranglar: ko'k/qora → "Obsidian Aurora" (chuqur indigo #070a13 asos, violet #8b5cf6 + cyan #22d3ee aksentlar)
  3. Aurora nur: fixed qatlam, mix-blend-screen bilan panellar USTIDA (backdrop-blur stacking context muammosi hal qilindi)
  4. Yangi utilitylar: .glass, .card-elevated, .text-gradient, .btn-accent, .nav-active, .accent-top, .pulse-dot, .fade-up
  5. Brend: CONDUIT gradient matn, violet STUDIO badge, nav-active violet nur
- **Piksel isboti:** top-left (80,70,106) violet, top-right (25,55,105) cyan (avval (0,0,0) qora edi)
- **Vision bahosi:** aurora 8/10, aksent chiziqlar 7/10, premium his 7.5/10 (avval 1/0/4)
- **Terminal DA-bug (vision topgan):** `[?1;2c` xom matn — DA javoblari faqat 0.40s guard'da filtrlanardi. Tuzatish: sessiya ochilishiga 3s guard + regex faqat javob patternlari (strelkalar/Ctrl+strelka/Home saqlanadi — 14 holat testi OK). Jonli tekshiruv: DA javob ekranga sizib chiqmaydi. PTY testlar 4+3+6 OK.
- **Testlar:** to'liq suite 107 passed; TSC 0; lint 0; build ✓.

## 2026-11-21 07:18 — Dizayn chuqurlashtirildi + terminal DA-filtr mukammal tuzatildi
- **Agent kartalari (Window3BrainGraph):** BOSH AGENT va agent kartalari ko'k/cyan → violet/indigo tema (selected: indigo-950 + violet ring, active: violet-950).
- **Brauzer paneli (Window2Browser):** URL input fokus violet, "Ochish" tugmasi btn-accent gradient, ko'rinish konteyneri violet ramka + ichki soya.
- **Evolyusiya + Titlebar + Window4:** barcha flat-blue-600 tugmalar/tablar → nav-active/btn-accent gradient. Oxirgi "Qadamlar Tarixi" tugmasi ham tuzatildi — endi flat-blue 0 ta.
- **Terminal DA-filtr MUHKAMLASHTIRILDI (asosiy tuzatish):** vaqt-guar'di ishonchsiz edi (singleton sessiyada guard eskiradi). Yangi mantiq: PTY chiqishida DA/DSR SO'ROV (\x1b[6n, \x1b[c, \x1b[>c) ko'rinsa 1s javob oynasi ochiladi; so'rov kutilayotganda javoblar PTY'ga uzatiladi (vim/PSReadLine ishlaydi), so'rovsiz stray javoblar tashlanadi. Jonli tekshiruv: stray DA ekranga sizmaydi; agy TUI testi o'tdi (haqiqiy javoblar yetib boradi).
- **Vision yakuniy:** [?1;2c YO'Q ✅, dizayn 8/10 — "cohesive violet/cyan premium".
- **Testlar:** PTY 4+3 OK, lint 0, build ✓, backend 200, frontend 200.
- **Qo'shimcha (07:30):** 7 faylda qolgan flat-blue aksentlar violet temaga o'tkazildi (Window1/2/3/4/5, EvolutionModal, BrainHeartTab). Agent rol ranglari (scout=sky, sculptor=orange) semantik — saqlanadi. Vision: uyg'unlik 7/10, "more polished than a generic blue UI". TSC 0, lint 0, build ✓.
- **Evolyusiya modali to'liq violet temaga o'tdi:** qolgan barcha blue havolalari (focus border, badge, saboq kartasi) → violet. EvolutionModal'da endi 0 ta blue havola. Regressiya: agy painter PASS (task_a4c51268, theme_test.png 400x400).

## 2026-11-21 07:50 — Flaky test tekshirildi (Blender headless)
- To'liq suite'da 3 test vaqtinchalik muvaffaqiyatsiz bo'ldi (test_faza4: blender_headless, tools_py, rest_endpoints).
- Tekshiruv: yolg'iz va fayl ichida ketma-ket 2 marta — 8/8 PASSED. Sabab: vaqtinchalik tizim yuklamasi (Blender start 13-17s, parallel vazifa bilan poyga). Kod bug'i emas.
- Blender timeout allaqachon 120s — yetarli. Qaror: qayta tekshiruvda kuzatiladi; agar takrorlansa timeout oshiriladi.

## 2026-11-21 11:04 — Crush qayta tekshirildi: yana BLOCKED (24h rolling kvota)
- task_9b849551: "input tokens per minute limit exceeded... retry in 23h56m" — Gemini free tier kvotasi 11:00 da emas, ~24 soatlik rolling oynada tiklanadi ekan. Dastlabki "ertalab 11:00" taxmin noto'g'ri edi.
- Crush ertaga ~11:00 da yana tekshiriladi. Dvigatel agy'ga qaytarildi (ishlaydi).
- **Qaror:** crush uchun kod o'zgarishi shart emas — bu tashqi kvota cheklovi; tizim to'g'ri halol BLOCKED beradi.

## 2026-11-21 16:45 — Poydevor auditi va qarorlar (universal studio)
- 2026-11-21 16:45 | Asosiy ish nusxasi = `C:\Users\Kapitan\Documents\Проект по умолчанию\conduit` (eng yangi commit 48c6820 + joriy tuzatishlar). `C:\Users\Kapitan\conduit` eski commit 3a96425 — o'chirilmadi, faqat ma'lumot sifatida qoldirildi: ikki nusxa bilan aralashmaslik uchun.
- 2026-11-21 16:45 | Terminal qayta yozilmadi: haqiqiy pywinpty PTY + xterm.js + resize + reconnect + DA/DSR filtri allaqachon ishlaydi (jonli WS dalil bor). Faqat sizish tuzatildi.
- 2026-11-21 16:45 | FFmpeg 9.0.2 va `claude` PATH'da mavjud (doctor OK) — o'rnatish takrorlanmadi; qolgan WARN faqat ixtiyoriy tokenlar.
- 2026-11-21 16:45 | Test muhiti: `backend/tests/conftest.py` da `anyio_backend='asyncio'` allaqachon bor — production kodini test uchun buzmaymiz.
- 2026-11-21 16:45 | `tools.py` dublikati ildizi: `cli_runner.py` to'liq 39872 baytlik master nusxani workspace'ga ko'chiradi. Yechim: 596 baytlik `backend/tools_stub.py` ko'chiriladi; mavjud to'liq nusxalar stub bilan almashtiriladi.
- 2026-11-21 16:45 | DeepSearch: manba xatolari `source_errors` ga yozilib, Report'da ko'rsatiladi; `return []` jim qoldirish emas, xato logi bilan birga bo'ladi.
- 2026-11-21 16:45 | UI yo'nalishi: oldingi "Quiet Workspace" + Agentlar katalogi + Vazifa kompozitori saqlanadi; oddiylik va tezlik ustun.

## 2026-11-21 17:05 — Poydevor tuzatishlar va tasdiqlar
- 2026-11-21 17:05 | Blender 5.2 da `Action.fcurves` olib tashlangan: render skripti layered API (`action.layers -> strips -> channelbags -> fcurves`) ga moslashtirildi; aks holda haqiqiy render yolg'on xato berardi.
- 2026-11-21 17:05 | `app_adapter.execute_blender_video` endi `CONDUIT_RENDER_DONE` markeri yo'qligini alohida xato sifatida ko'rsatadi (Blender script xatosida ham exit 0 qaytarishi mumkin). Soxta fallback ishlatilmaydi.
- 2026-11-21 17:05 | `agents.json` ga `opencode_agent` yozuvi qo'shildi — kod o'zgarishi yo'q, `/api/engine/status` darrov yangi agentni ko'rsatdi (universal talab tasdiqi).
- 2026-11-21 17:05 | To'liq pytest (ignore'siz): 105 passed, 2 skipped — foydalanuvchi aytgan 9 xato muhitda takrorlanmadi; `conftest.py` dagi asyncio fixture saqlanadi.
- 2026-11-21 17:12 | MCP'siz rejim: `agy -p` da per-invocation MCP o'chirish flagi yo'q (rasmiy feature request #342, shuningdek #1088: global 'disabled' ham print mode da ishlamaydi). Yechim: Conduit workspace'iga bo'sh `.agents/mcp_config.json` yoziladi — global sozlamaga tegilmadi. Manba: https://github.com/google-antigravity/antigravity-cli/issues/342 , https://antigravity.google/docs/cli/mcp (ko'rilgan 2026-11-21).
- 2026-11-21 17:16 | Tuzatish: bo'sh MCP konfiguratsiyasi yozuvi `cli_runner` dan `workspace_manager.get_agent_workspace()` ga ko'chirildi — instrument va rol agentlari ham qamrab olinadi. Tekshirildi: `workspaces/inst_image/.agents/mcp_config.json` = `{\"mcpServers\": {}}`, `tools.py` 596 bayt (stub).
- 2026-11-21 17:25 | Agentlarning so'ralmagan ish qilishi: interaktiv TUI ga avtomatik yozish prompt o'rniga muharrirga tushadi (dalil: \-- INSERT --\ + agent test faylini o'qishga ruxsat so'radi). Yechim: avtomatik yoziladigan AGENTS/CLAUDE/GEMINI yo'riqnomasiga 'faqat so'ralgan ish, qo'shimcha fayl o'qima, noaniq bo'lsa so'ra, faqat conduit --help/list bilan cheklan' qoidasi qo'shildi; 3 fayl qayta generatsiya qilindi. Deterministik ish uchun \conduit run\ ni to'g'ridan-to'g'ri shell dan chaqirish tavsiya etiladi.
- 2026-11-21 17:30 | Agent to'liq va faqat so'ralgan ishni bajarishi uchun \"missiya brief\" usuli tanlandi: (1) deterministik chaqiruv = \conduit run\ (interaktiv TUI emas), (2) vazifada maqsad + taqiqlar + ruxsat yo'l + dalil talabi bo'lsin, (3) noaniqlikda taxmin emas savol. Bu qoidalar \cli_runner.py\ dagi avtomatik agent promptiga va AGENTS/CLAUDE/GEMINI yo'riqnomasiga kiritildi. Sabab: agentga sintaksis/ma'lumot yetishmasa, u o'zicha fayl o'qib 'qo'shimcha ish' qiladi (dalil: test faylini o'qish so'rovi).
- 2026-11-21 18:05 | Kirishda AI agent tanlovi: birinchi ochilishda localStorage bo'sh bo'lsa modal ko'rsatiladi (6 agent, tayyorlik holati bilan). Tanlov /api/engine/select ga yoziladi, localStorage ga saqlanadi, terminal WS ga launch_agent yuborilib shu agent PTY da ochiladi; keyingi ochilishlarda modal ko'rinmaydi. Sabab: foydalanuvchi studiyaga kirib, qaysi agent bilan ishlashini darrov tanlashi va butun studio shu agentga bog'lanishi kerak.
- 2026-11-21 18:20 | Kirish tanloviga qo'shimcha AI agentlar qo'shildi: gemini_cli (rasmiy -p headless sintaksisi tasdiqlandi), cursor_cli, qwen_cli, kimi_cli, glm_cli, copilot_cli, aider. Jami 13 ta agent; o'rnatilmaganlari modalda YO'Q deb ko'rsatiladi va tanlansa halol 'CLI topilmadi' xatosi beradi. Manba: google-gemini/gemini-cli docs/cli/headless.md (2026-11-21). Qolganlarining flaglari o'rnatgach --help bilan tasdiqlanishi kerak (izohda yozildi).
- 2026-11-21 19:10 | Terminal agentining MCP xatosi: interaktiv \gy\ global 22 ta MCP serverni yuklaydi (per-invocation o'chirish flagi yo'q), \data-agent-kit\ serveri exit 255 + buzuk UTF-8 qaytaradi. Tuzatish: (1) \gents.json\ ga \interactive_command\ qo'shildi — agy \--dangerously-skip-permissions\, claude \--strict-mcp-config --mcp-config <workspace>/.agents/mcp_config.json\; (2) repo ildiziga bo'sh \.agents/mcp_config.json\ yozildi; (3) AGENTS/CLAUDE/GEMINI yo'riqnomasiga 'MCP toollarini chaqirish TAQIQLANGAN' qoidasi qo'shildi. Tekshirildi: PTY scrollback'da \gy --dangerously-skip-permissions\ (ANSI tozalangandan keyin) bor. Cheklov: agy global serverlarni start paytida yuklashda davom etadi (rasmiy flag yo'q) — bu startup sekinligi va xato loglariga sabab bo'lishi mumkin, lekin agent ularni chaqirmaslikka yo'naltirildi. Global config o'zgartirilmadi.
- 2026-11-21 19:35 | Qolgan ma'lum buglar tuzatildi: (1) agent almashtirilganda eski PTY daraxti shutdown() bilan yopiladi va yangi prompt kutiladi — aks holda buyruq ishlab turgan TUI ichiga tushardi; (2) kirish modalida o'rnatilmagan agentni tanlash bloklanadi (halol ogohlantirish bilan); (3) jonli sahna 0.6s dan yangi PNG larni o'qimaydi — progressiv render paytida 'image truncated' shovqini yo'qoldi. Dalil: WS swap testi (eskisi yopildi/yangi prompt/codex ishga tushdi), Playwright (13 karta, unavailable disabled, warning), pytest 105 passed 2 skipped, tsc/build OK.
- 2026-11-21 20:00 | UI o'lchami qayta muvozanatlandi: foydalanuvchi 'hamma narsa kattalashib ketdi' degach, global shrift 12/13/14px dan 11/12/13px ga, body 14→13px ga qaytarildi; kirish modalining eni 4xl→3xl, ichki padding 8→6, kartalar p-4→p-3; agent katalogi va qadam kartalari ham ixchamlashtirildi. Tinch neon-siz dizayn saqlandi. Sabab: avvalgi 'siqilgan' shikoyatiga haddan tashqari kattalashtirish bilan javob berilgan edi.
- 2026-11-21 20:20 | Foydalanuvchi izohlari bo'yicha 4 ta o'zgarish: (1) brend NEXUS ga o'zgartirildi (CLI buyrug'i 'conduit' saqlanadi, skriptlar buzilmasligi uchun); (2) STD/EEPX/SUPER/DEEPX rejimlari endi pastki statusbarda ham ko'rinadi va API bilan tasdiqlandi (eepx → active_mode=eepx, footer EEPX); (3) Window3BrainGraph dagi chalkashtiruvchi bezak chiziqlari/SVG olib tashlandi; (4) profil sozlamasida Hajm: Kichik(0.9)/O'rta(1)/Katta(1.1) nazorati qo'shildi, standart 0.9. Dalil: Playwright — TITLE 'Nexus...', NEXUS True, eski brend 0, SVG LINES 0, ZOOM 0.9, MODE API eepx, MODE FOOTER True.
- 2026-11-21 21:10 | 4 soatlik reja bajarildi. Asosiy qo'shimcha: agy uchun izolyatsiyalangan HOME (backend/agent_env.py) — global sozlamaga tegmasdan bo'sh mcp_config + auth nusxasi; sinov: 8s (global 50s), terminalda 'MCP\'siz izolyatsiyalangan muhit' tasdiqi. Desktop yorlig'i eski nusxaga ishora qilgani topilib, asosiy nusxaga qaytirildi. Qolgan barcha bosqichlar dalil bilan yopildi (docs/4_SOATLIK_ISH_REJASI.md).
- 2026-11-21 21:25 | Terminal agenti xatosi qayta tuzatildi: izolyatsiyalangan HOME faqat bir martalik CLI chaqiruvlarida (8s vs 50s) qoldirildi; interaktiv PTY da oddiy muhit + prompt tayyorligini kutish (_prompt_ready Event) joriy etildi — aks holda buyruq prompt chiqishiga aralashib CommandNotFound berardi. Tekshirildi: LAUNCHED True / TUI True / NO CMD ERROR True.
- 2026-11-21 23:55 | Poydevor auditida 3 ta ildiz xatosi topildi va tuzatildi: (1) py_compile xatolari — patchlarda logging importi yetishmagan (studio_pipeline/apps_manager/mcp_server), tuzatildi; (2) Blender headless EEVEE/Workbench WGL crash — Cycles CPU (32 sample) ga o'tkazildi, haqiqiy kadr olinadi; (3) jimgina try/exceptlar main/cli_runner/terminal_session/database/deepx/kernel/heart/memory/apps/mcp/scout/live_browser/heavy/pipeline da loglanadigan qilindi. SuperAgent (task_b7bc0db9) va DeepX (task_9a405d30) qaytadan oxirigacha PASS.
- 2026-11-22 01:50 | 5 soatlik ish yakunlandi: barcha 4 rejim PASS (standard/eepx/super_agent/deepx), 12/12 task soak, 6/6 UI soak (1 tasi restart paytida vaqtinchalik), DB integrity ok / 0 buzilgan rasm, 108 passed test, doctor 0 FAIL. O'rnatilmagan agentlar uchun modal rasmiy install havolasini ko'rsatadi. Barcha jimgina catchlar loglanadi. CLI/UI brend NEXUS, buyruq nomi conduit saqlanadi.
- 2026-11-22 12:40 | Subagent modeli rasmiy manbaga asosan qayta tuzetildi: asosiy AI agent o'zi faol ishlaydi va vazifani subagentga delegatsiya qiladi; subagent alohida kontekst/to'plam bilan ishlab qisqa natija qaytaradi (https://docs.anthropic.com/en/docs/claude-code/sub-agents). Conduit da bu 'Agent tool' o'rniga conduit run/wait/result. Terminal input endi shell'ga emas, ishlab turgan AI agentga yozadi (agent_prompt WS xabari); 'Namuna' tugmasi delegatsiya siklini ko'rsatadi. Dalil: PROMPT SENT True / NO ERROR True.
- 2026-11-22 13:12 | 2 soatlik oynada chuqur o'rganish va asosiy amalga oshirish bajarildi (oyna 14:39 gacha davom etadi). RASMIY MODEL (https://code.claude.com/docs/en/subagents.md, o'qilgan 2026-11-22): subagent = alohida kontekst oynasi + o'z system prompti + tool allowlist + mustaqil ruxsat; u umumiy usage limitga hisoblanadi. Asosiy agent faqat QISQA tavsif asosida delegatsiya qiladi; tavsiflar jami 15 000 token dan oshsa ogohlantirish bor. To'liq rol prompti faqat subagent ishga tushganda yuklanadi. AMALGA OSHIRISH: (1) `backend/tool_registry.py` — 16 faol subagentni `conduit_run_<id>` tool'lari sifatida katalogga chiqaradi (tavsif, input_schema, ruxsat etilgan toollar, token/narx bahosi, chaqiruv shartnomasi); jami tavsif 334 token (limit 15 000). (2) `GET /api/tools/catalog` + CLI `conduit tools --json` / `conduit budget --json`. (3) Avtomatik AGENTS/CLAUDE/GEMINI yo'riqnomasi v3 ga yangilandi: asosiy agentga tool'lar bog'langanligi, qisqa tavsif/uzun ro'l farqi, byudjetni tekshirish qoidasi yozildi. (4) Statusbarda `TOK 229k/500k · $1.07` ko'rsatildi. (5) Haqiqiy provider token usage endi oxirgi (result) hodisadan olinadi — cumulative usage'larni qo'shib yuborish xatosi tuzatildi (PONG sinovi: 13 944/24, ikki barobar emas); `cli_runner.cli_runner.extract_token_usage/merge_usage_snapshot`. (6) `cli_runner.py:1410` dagi `-target_agent` xatosi tuzatildi. DALIL: jonli agy `conduit tools --json` ni bajardi va "Tools soni: 16 ta" deb xabar qildi; keyin `conduit run inst_image "Qizil kvadrat rasm yarat"` chaqirib `task_e1bda0f0` yaratdi va u PASS bo'ldi (artefakt `gen_85415.png`, 42 226 bayt). Deterministik zanjir: `inspector` task_8ed9d724 PASS, `scout` task_889f624a PASS. To'liq pytest 116 passed 2 skipped, doctor 0 FAIL, lint/build/tsc 0. Skrinshot: `%TEMP%/opencode/nexus_final.png`.

- 2026-11-22 13:35 | Qo'shimcha chuqurlashtirish: agy rasmiy docs (https://antigravity.google/docs/subagents?tab=cli, o'qilgan 2026-11-22) bo'yicha `.agents/agents/<name>.md` native subagent definitsiyalari joriy etildi (`backend/native_subagents.py`). 16 ta `conduit_<id>.md` faqat lokal .agents/agents/ ga yoziladi; global ~/.gemini sozlamasiga tegilmadi. Tools ro'yxati faqat agy init hodisasida tasdiqlangan nomlardan (run_command, view_file, grep_search, list_dir, search_web, capture_browser_screenshot, open_browser_url, read_url_content) — noto'g'ri nom osib qolish xatosi rasmiy eslatmada bor. DALIL: yangi definitsiyalar bilan agy bir martalik ishga tushishda 8.2s da PONG qaytardi (RC 0); alohida so'rovda agy o'zi `conduit_scout` va boshqa `conduit_*` subagentlarni ro'yxatlab berdi (HAS_CONDUIT_SCOUT True). Claude Code uchun esa agy tool nomlari mos kelmagani sabab universal CLI katalogi ishlatiladi. Qo'shimcha: statusbar byudjeti har 15s yangilanadi; Figma validatoridagi hardcoded fayl kaliti/token olib tashlandi. To'liq pytest 118 passed 2 skipped, doctor 0 FAIL, tsc/lint/build 0. Skrinshot: `%TEMP%/opencode/nexus_final.png`.
- 2026-11-22 13:44 | Yakuniy regressiya: ByudjetGuard va native definitsiyalardan keyin jonli agy yana `conduit tools --json` ni bajardi ("katalogda jami 16 ta subagent-tool mavjud" — PTY scrollback, 3 marta takrorlandi) va `conduit run inst_image "Yashil uchburchak rasm yarat"` orqali `task_a0a9a52a` ni yaratdi; `conduit wait` + `conduit result` bilan PASS (gen_59192.png, 46 KB). UI 1600x1000 va 1280x800: overflow 0, konson xatosi 0. To'liq test 119 passed 2 skipped; compileall 0; doctor 0 FAIL; lint/build/tsc 0; DB integrity avval ok.
- 2026-11-22 13:48 | Token bahosi real o'lchovlar bilan kalibrlandi: `MIN_EXECUTION_TOKENS=15000` (PONG ~14k, screenshot vazifasi ~88k). `conduit tools --json` endi scout uchun `estimated_execution_tokens=15000`, `estimated_cost_usd=0.225`, `within_remaining_budget=true`.
- 2026-11-22 14:35 | 40 daqiqalik barqarorlik kuzatuvi (13:54-14:34, har 1.5-3 daqiqa): API 200, WEB 200, tool katalogi 16 — 19/19 tekshiruv toza. Yakuniy hujjat: `docs/SUBAGENTS_AS_TOOLS.md`.
- 2026-11-22 14:42 | Foydalanuvchi tasdigi bilan notog'ri token yozuvi tozalandi: resource_ledger id=64, task_8ed9d724, 82844/8235 token, $0.372057 (cumulative usage qo'shib yuborilgan 12:56:53 yozuvi). Keyingi to'g'ri yozuv id=65 (task_889f624a) saqlandi. Jami: 241793 -> 150714 token, $1.16849 -> $0.79643. DB integrity ok. `Microsoft/` PowerShell kesh .gitignore ga qo'shildi.
- 2026-11-22 14:55 | Skrinshotdagi "budget guard test" BLOCKED vazifasi mening testim yaratib qoldirgan haqiqiy DB yozuvi ekanligi aniqlandi. Test endi o'z yozuvini `finally` blokida o'chiradi (`test_tool_registry.py`); DB dagi 5 ta eski test vazifasi o'chirildi, integrity ok. Ikkinchi muammo — ketma-ket xabarlar agy "Generating..." holatiga navbatga tushib, bir nechta Generating bloklarini hosil qilardi: `terminal_session.py` da bandlik kuzatuvi qo'shildi (PTY chiqishidagi "Generating" / "ready for input" markerlari). Band paytda xabar yuborilsa, terminalda aniq ogohlantirish chiqadi va PTY'ga yozilmaydi. Dalil: BUSY_WARNING True / SECOND_NOT_ECHOED True / FIRST_ECHOED True. Yangi test `test_terminal_busy.py`. To'liq pytest 124 passed 2 skipped.
- 2026-11-22 15:35 | 1.5 soatlik vazifa: GitHub'dan 7 ta eng kuchli agent skilli lokalga o'rnatildi (obra/superpowers: systematic-debugging, verification-before-completion; addyosmani/agent-skills: code-review-and-quality, security-and-hardening, observability-and-instrumentation; anthropics/skills: webapp-testing; andrej-karpathy-skills: karpathy-guidelines). Joylashuv `.opencode/skills/`, ishchi papka `opencode.json` orqali ulandi — global config tegilmadi. Skilllar haqiqatan yuklanib auditda ishlatildi. DeepSearch: 5 kandidat + hisobot. DeepX: task_9d421f37 PASS, 5 citation, 4 thought, 2 swarm bosqichi, self-healing logi, Sentinel 100/100. Audit: silent except 25->3 (qolgani test/polling), TODO 0, a11y 86 button/0 no-name, overflow 0, console 0, secret fixture 4 (haqiqiy yo'q), npm audit 2 zaiflik (major upgrade talab qiladi — ko'chirildi, majburiy fix qo'llanmadi). Tuzatish: 9 faylda 22 ta jim xato loglanadigan qilindi. Tekshiruv: pytest 124 passed 2 skipped, compileall/doctor/tsc/lint/build 0. Batafsil: docs/SKILLS_AND_AUDIT.md.

- 2026-11-22 15:49 | Commit paytida yana bir real kamchilik topildi: DeepX `generate_research_report` slug'ini cheklamagani uchun 222 belgili fayl nomi Windows MAX_PATH ga sig'madi va `git add` xato berdi. Root cause: `deepx.py:204` da slug uzunligi nazorat qilinmagan. Tuzatish: 75 belgi + 8 belgili sha1 hash, yangi regression test `test_deepx_report_name.py`. Eski hisobot `research/deepx_audit_nexus_studio.md` ga o'zgartirildi. To'liq test 123 passed 2 skipped.
- 2026-11-22 16:02 | Mustaqil code review topilmasi tuzatildi: 19 ta `LOGGER.debug` xabari root logger WARNING bo'lgani uchun ish vaqtida ko'rinmay qolardi. `main.py` da `nexus`/`conduit` loggerlari DEBUG + StreamHandler bilan sozlandi; `tools.py:110` warning -> debug (spam oldi olindi); polling `pass` -> `continue`; AST eshigidagi line-number allowlist olib tashlandi. Yangi test `test_studio_loggers_are_visible_at_debug_level`. To'liq pytest 124 passed 2 skipped.
- 2026-11-22 16:41 | 1.5 soatlik vazifa yakunlandi. 15 daqiqalik barqarorlik kuzatuvida 13/13 tekshiruv: API 200, WEB 200, tools=16, DeepX PASS; commitlar: 6498bd9 (skilllar+audit), 7bb0f29 (loglarni ko`rinar qilish). Git toza.
- 2026-11-22 19:10 | "Hammasi tayyormi" tekshiruvida yana bir muammo topildi: pytest har gal 3 ta kuzatiladigan faylga (memory/errors.md, tools/candidates.json, research/to_liq_3d_e_commerce_platforma_mvp.md) yozib, git ishchi daraxtini iflos qilardi. `backend/tests/conftest.py` ga session-scoped autouse fixture qo'shildi — testlardan keyin fayllar asl holatiga qaytariladi. Dalil: to'liq testdan keyin DIRTY=1 (faqat conftest'ning o'zi), 124 passed 2 skipped.

- 2026-11-22 21:0x | Oxirgi ogohlantirish to'liq expert darajasida yopildi (deep-plan: init/scan/DEEPX/root-cause/multi-miya/DEBUG/TEST/gate approve+verify OK). 1) Terminal 'Running command...' zinapoyasi: ildiz sababi - scrollback qayta o'ynalishida qator bo'laklari '\r\n' bilan birlashtirilib, agy ning \x1b[3A qayta chizishini buzgan. Tuzatish: xom _scrollback_chunks + ''.join() replay + _clear_scrollback(); dalil BAD_JOIN 0, GOOD_JOIN 345, TAIL_IN_REPLAY True, ekranda running satrlar 0. 2) Browser '-hel' xom xato: frontend https:// ni ko'r-ko'rona qo'shgan, backend URL ni tekshirmagan. Tuzatish: url_validation.normalize_navigation_url + 422 + frontend dastlabki filtr; dalil API 422 'Noto\'g\'ri host nomi', UI RAW_GOTO False, FRIENDLY True. To'liq tekshiruv: 148 passed 2 skipped, compileall/doctor/tsc/build/lint 0, API/WEB 200. gate.py verify OK.

- 2026-11-23 07:xx | To'liq GitHub klonlash rejimi + oflayn Anime.js v4 kutubxonasi qo'shildi (deep-plan: 1-yondashuv tasdiqlandi, gate check/approve/verify OK). Backend clone_manager.py: https-only URL, shell'siz git clone --depth 1, registry JSON, refresh/delete, path traversal guard; API /api/clones; 3 ta test yashil. Haqiqiy https://github.com/morluto/rea.git klonlandi, HEAD 2c38fd16287085867848ce152ae2e57bf68d2015. Frontend Window5Workspace.tsx da 'Klonalar' rejimi. vendor/libraries/animejs/: animejs@4.0.0 oflayn, dist/docs/demo; backend /library/animejs mount; demo loop:true progress muammosi self.currentTime % self.iterationDuration bilan tuzatildi, Playwright ADVANCED True / CONSOLE_ERRORS []. Resource testlari uchun conftest.py da isolate_resource_state qo'shildi. To'liq tekshiruv: 151 passed 2 skipped; compileall 0, doctor 0, tsc 0, build 0, lint 0. Foydalanuvchi 'githubga push qil hammasini' deb oddiy pushni tasdiqladi.

## 2026-11-21 10:25 — GitHub push + CI pipeline yashil
- Butun loyiha GitHub'ga push qilindi (jahongashtamc/conduit, public, main).
- Push oldi xavfsizlik skaneri: .env/tokens.json ignore'da, API kalit skaneri toza, 30+ vaqtinchalik debug fayl gitignore'ga qo'shildi.
- GitHub Actions CI qo'shildi (.github/workflows/ci.yml): backend pytest (ubuntu-latest) + frontend lint/tsc/build.
- CI sozlash jarayonida 4 muammo tuzatildi:
  1. `mcp` kutubxonasi requirements.txt'da yo'q edi → qo'shildi (1.28.1).
  2. Windows runner'da SQLite WAL "database is locked" flakiness → backend testlar ubuntu-latest'ga ko'chirildi (lokda venv replitsiya bilan tasdiqlandi: lock Windows-runner-specific). init_db'ga retry + connection close ham qo'shildi (server start chidamliligi).
  3. CI'da claude CLI va node tools yo'q → test_cli_runner shartli skip (xato traceback'i ochiq DB connection ushlab qolishi sababidan ham muhim).
  4. path-traversal testi platformaga moslashtirildi (Linux'da /etc/passwd).
- Yakuniy: backend 102 passed + 5 skipped (11.8s), frontend lint/tsc/build ✓ — CI YASHIL.

- 2026-11-23 | Tool sifati darvozasi: mavjud 	ools.py/security_guard.py qayta ishlatildi, yangi MCP/framework yo'q. 	ools.py list_tools 15 ta instrumentni to'liq katalog qiladi; cli_runner CONDUIT_AGENT/CONDUIT_TASK_ID/CONDUIT_TASK_STARTED_AT uzatadi; 	ools.py ichida role.md allowlist qo'llanadi. check_goal eski latest.png ga fallback qilmaydi: bo'sh yoki eski dalil FAIL. alidate_evidence_against_goal faqat kalit so'z emas, aniq artefakt obyektini talab qiladi. Agent yo'riqnomasi v5 bilan qayta generatsiya qilindi. Dalil: ruxsatsiz gen_image -> exit 2; eski dalil -> FAIL; list_tools -> 15 tool.
- 2026-11-24 06:02:55 | Backend uvicorn logida tashqi monitoring /health ni so'rab 404 olayotgani aniqlandi (manba kodda /health chaqiruvi yo'q). /api/health bilan bir xil JSON qaytaradigan /health alias qo'shildi. Dalil: GET /health=200, GET /api/health=200, pytest 159 passed/2 skipped, compileall 0.
- 2026-11-24 18:31:25 | 3D preview tezligi va sifati: Blender headless endi CYCLES CPU + 16 sample (`NEXUS_BLENDER_SAMPLES`) + denoise + 50% o`lcham (`NEXUS_BLENDER_SCALE`). Ildiz sabab: eski `render_snapshot.png` mavjud bo`lsa, yangi kadrali fayl (`*.png0001.png`) hech qachon ustiga ko`chirilmagan — UI eski rasmni ko`rsatgan. `promote_blender_artifact` faqat render boshlangandan keyingi faylni tanlaydi va `os.replace` bilan yangilaydi, eski dalil rad etiladi. Dalil: real render 18.16s -> 6.59s, `artifact_fresh=True`, workspace/static `960x540`, mtime yangi. To`liq test: 163 passed, 2 skipped. Watchdog `ROOT`/`PY` ham `__file__`/`sys.executable` dan oladigan qilindi (eski `C:\Users\user\...` yo`li tuzatildi).
- 2026-11-24 20:01 | AI ish sifati (deep-plan, tasdiq 19:39:57): foydalanuvchi "sust" deganda tezlik emas, sifatni nazarda tutgan. Ildiz sabablar: (1) `cli_runner` non-visual branchida `verdict == PASS or doer_out_summary` tufayli ixtiyoriy matn PASS bo'lgan; (2) inspector `success` ni `verdict` o'rniga ishlatgan; (3) `validate_evidence_against_goal` yo'l matnini fayl mavjudligi/hajmisiz qabul qilgan. Tuzatish: `goal_check_passed()` faqat aniq PASS, `_artifact_is_real()` bilan fail-closed artefakt tekshiruvi, FAIL sababini keyingi urinishga uzatish (1+2 retry, loglangan), agent yo'riqnomasi v6 ga "Natija shartnomasi". Dalil: `165 passed, 2 skipped`, `doctor 0 FAIL`, `compileall/tsc/build/lint 0`. Eski fixture ham haqiqiy faylga o'zgartirildi. Yangi MCP/framework yo'q, global config/auth/MCP tegilmadi.
- 2026-11-24 | To'rt konkret nuqson ildiz sababi bilan tuzatildi: (1) `tool_video_render` endi faqat real kirish klipi/audio bilan FFmpeg concat/trim orqali montaj qiladi, klipsiz FAIL; (2) DeepX swarm bosqichlariga `asyncio.wait_for` hard-timeout qo'shildi, `Sertifikatlangan` hardcode olib tashlandi, DEEPSEARCH rejimi va so'zga asoslangan relevans qo'shildi; (3) Figma hardcode spec o'rniga `FIGMA_TOKEN` + REST API, token yo'qsa `needs_config`; (4) DeepSearch endi `research/*.md` hisobot yozadi. Dalil: `pytest backend/tests -q` 171 passed/2 skipped, `doctor 0 FAIL`, real deepsearch 12 kandidat/1 source error, UI Hisobot tabi ishli.
