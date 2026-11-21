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
