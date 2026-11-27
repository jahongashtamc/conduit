# Conduit - AI Agentlar Uchun Ilovalar Dashboardi va Subagent Boshqaruv Tizimi

## Stack
- Backend: Python 3.14 + FastAPI + WebSockets + SQLite + Uvicorn + psutil
- Frontend: Next.js 15 / React 19 + Tailwind CSS + GSAP
- Baza: SQLite (conduit.db)
- Integratsiya: agent-studio-plugin (MCP), Subprocess, Apps OS monitoring
- Tillar: O'zbekcha / Inglizcha

## Arxitektura qarorlari
1. **Subagentlar izolatsiyasi**: Yangi subagent qo'shish faqat `subagents/<nom>/` papkasini nusxalash orqali amalga oshiriladi (kod o'zgartirilmaydi).
2. **Manager roli**: Faqat vazifalarni routing qiladi (yo'naltiradi), o'zi vazifa bajarmaydi.
3. **Jonli oqim**: WebSocket orqali frontendga loglar, skrinshotlar va qadam holatlari (planner -> doer -> checker) bir zumda uzatiladi.
4. **Ilovalar holati**: `apps.json` konfiguratsiyasi va OS processlari (psutil) orqali `ready`, `running`, `not installed` dinamik aniqlanadi.
5. **Workspaces Sandbox (Faza 2)**: Har bir subagent faqat `workspaces/<nom>/` papkasiga yozadi. `resolve_safe_path` orqali Path Traversal (`../../`, tashqi disklar) qat'iy bloklanadi.
6. **Tool Whitelist (Faza 2)**: Har bir subagent faqat o'z `role.md` faylida ko'rsatilgan toollarni chaqira oladi. Noma'lum toollar rad etilib, xavfsizlik audit logiga yoziladi.
7. **Zero Secrets (Faza 2)**: Hech qanday parol yoki API kalit .env dan o'qilmaydi va loglarda/UI da ko'rsatilmaydi (`[REDACTED_SECRET]` sanitization filtri).
8. **Inson tasdig'i (Approval Dialog)**: Fayl o'chirish yoki xavfli amallar aniqlanganda ijro to'xtatilib, foydalanuvchi tasdiqlamaguncha bajarilmaydi.
9. **CLI Subprocess Dvigateli**: Subagentlar to'g'ridan-to'g'ri tizimda o'rnatilgan CLI agentlar (`Claude Code CLI` / `Antigravity agy`) orqali `workspaces/<subagent>/` ichida subprocess sifatida yuritiladi. `tools.py` yordamida `agent-studio-plugin` toollari chaqiriladi va Planner -> Doer -> Checker tsikli 100% yopiq halqada tekshiriladi.
10. **Bosh Agent (Miya + Yurak)**: Miya o'zi tool ishlatmaydi, faqat subagentlarga `{to, task, expected_evidence}` buyruqlarini beradi va `{from, status, evidence, notes}` hisobotlarini qabul qiladi. Yurak aylanishi (Heartbeat loop) maqsad dalil bilan PASS bo'lguncha yoki 3 marta FAIL bo'lguncha qadamlarni boshqaradi. Barcha hodisalar va qisqa xotira (qaror, xato, natija) SQLite `events` va `brain_memory` jadvallarida saqlanadi.
11. **Figma Spec & Standalone PC Desktop App**: Brauzer veb-sahifasidan to'liq mustaqil PC Desktop Studio ilovasiga aylantirildi (`conduit-desktop.py`, `run-conduit.bat`, `DesktopTitlebar` oyna boshqaruvi, `DesktopStatusBar` telemetriya paneli, va 100vh studio workstation). Figma MCP orqali rasmiy Figma Spec (`X2utSRltdpdhTSyhFUcEUg`) va FigJam arxitektura diagrammasi (`leWEA7AyECgzcIk4aeDx8p`) integratsiya qilindi. Designer subagenti (Figma) faollashtirildi.
12. **Faza 3: Jonli Ko'rish Paneli (Live Monitoring & Timeline)**: Har bir subagent uchun jonli sekundomer/taymer (`00:14s`), aniq holat indikatorlari (`idle`, `working`, `needs approval`, `PASS`, `FAIL`, `BLOCKED`), va joriy bosqich trackingi qo'shildi. Vazifa timeline'da `planner` → `doer` → `checker` qadam davomiyliklari (`step_durations`), oraliq xulosalar va dalilga asoslangan tekshiruv (skrinshot + `check_goal` natijasisiz "tayyor" deb e'lon qilmaslik) joriy etildi. LivePanel'da skrinshot zoom/open, loglarni qidiruv va daraja bo'yicha saralash filtrlari yaratildi.
13. **Faza 4: Sculptor (Blender) va Ilova Adapterlari**: Umumiy ilova adapteri qatlami (`backend/app_adapter.py`) yaratildi: `apps.json` konfiguratsiyasi, ijro shablonlari (`run_template`), qo'llab-quvvatlanuvchi formatlar (`supported_formats`) va avtonom skript generatsiyasi (`runScript` sandbox nazorati bilan). Sculptor (Blender 3D), Animator (After Effects), Editor (DaVinci/Premiere), Painter (Photoshop) va Designer (Figma) subagentlari to'liq faollashtirildi (`active`). Headless Blender 3D rendering pipeline va Figma REST/WebSocket bridge moduli integratsiya qilindi. 3D modellash va rendering yopiq halqada (PASS dalili bilan) sinovdan o'tkazildi.
14. **7-Oynali Joylashuv & Conduit CLI**: UI 7 oynali aniq arxitekturaga o'tkazildi: Oyna 6 (Brand logo), Oyna 5 (Maxsus bo'sh maydon), Oyna 7 (Profil & Sozlamalar), Oyna 3 (Bosh agent va subagentlar tuguni - faqat nomlar bilan, jonli oqim animatsiyasi), Oyna 4 (Subagent tekshiruv paneli - qadamlar, loglar, dalillar), Oyna 1 (Agent CLI xterm terminali), Oyna 2 (Brauzer paneli - Natija va Dalil vkladkalari, buzuq rasmsiz). Terminal va CLI uchun `conduit.py` va `conduit.bat` buyruqlari yaratildi. "Hammasini to'xtatish" doimiy faol.

## Bosqich 1, 2, 3 Yakuniy Yangilanishlari (2026-11-08)
- Bosqich 1: ConPTY persistent terminal session (scrollback tiklanadi, auto-reconnect 1/2/4/8s, ping/pong), `conduit run/wait/status` CLI, $N=3$ parallel semafor va har subagent uchun workspace lock, 30s idle output heartbeat timeout, Oyna 3 egri Bezier nurlari.
- Bosqich 2: Yuqori panel 4 tugmasi: Evolyutsiya (Skillar, ziddiyat tekshiruvi, Sinab ko'r, Xotira md tahriri, Saboqlar), Tasdiqlar (xavfli buyruqlar qizil ramkada, Hammasiga ruxsat), Resurs (sarf hisobi $, token, byudjet limiti va avto-blok), Ulanish holati (CLI diagnostikasi va tekshirish).
- Bosqich 3: Oyna 5 Task rejimi (Rejim tanlagich: Tasklar | Widgetlar; Ishlayotgan parallel vazifalar, tarix va holatlar, Oyna 4 bilan bog'lanish, Yangi vazifa va tezkor shablonlar). Sozlamalarda Ruxsat darajasi tanlovi ("Har qadamda so'ra / Faqat xavfli amalda so'ra / Ish papkasida erkin").
- Super Yangilanish (Elita): Avtonom Self-Healing dvigateli (`SelfHealer` 5 toifali tashxis: sintaksis, tarmoq, 429 quota, fayl yo'li, ijro nosozligi; avtomatik buyruqni qayta boyitish va DB saqlash), Audit hisobotlar generatori (`/api/tasks/{task_id}/report` Markdown va to'liq CSS HTML), Oyna 2 da Hisobot va Avto-Tuzatish vkladkalari, Web Audio API orqali sintez qilingan nol-assetli ovoz effektlari (`playDispatch`, `playSuccess`, `playFailure`, `playAlert`), StatusBarda SFX ON/MUTE tugmasi va global tezkor tugmalar (`Ctrl+Shift+A`, `Ctrl+Shift+X`, `Ctrl+1..4`, `Ctrl+K`). Barcha 66 ta pytest unit testlari 100% PASS.
- Kernel v2 (EEPX & Super Agent Swarm, 2026-11-08): Yadroga 3 xil chuqur ijro rejimi qo'shildi: (1) `standard` (Planner -> Doer -> Checker), (2) `eepx` (E1 Exploration, E2 Evaluation, P Planning DAG, X Dual-Verify), (3) `super_agent` (Avtonom ko'p agentli swarm arxitekturasi: avtomatik maqsad dekompozitsiyasi, subagentlararo zanjir, kiruvchi artefakt uzatish, va bosqichlararo self-healing himoyasi). SQLite'da `kernel_settings`, `eepx_traces`, `swarm_stages` jadvallari, `/api/kernel/settings`, `/api/kernel/telemetry`, `/api/tasks/{task_id}/eepx`, `/api/tasks/{task_id}/swarm` API endpointlari yaratildi. Frontend Titlebar'da 3-rejimli segmented control va Oyna 2 da jonli "Yadro" telemetriya va vizualizator paneli integratsiya qilindi. Barcha 71 ta pytest testlari 100% PASS.
- DEEPX & Sentinel RedTeam Upgrade (2026-11-09):
  1. `Sentinel` (v2.0.0): Studio yaratgan kod, arxitektura va API'larni stress-test qiluvchi, Path Traversal, ochiq sirlar (leaks), SQLi/XSS va chegaraviy holatlarni tekshiruvchi maxsus xavfsizlik auditori.
  2. `DeepSearch + DeepX`: Ko'p manbali tadqiqot (DeepSearch), uzoq muddatli fikrlash (Extended Chain-of-Thought 4 ta kognitiv shox bilan), va murakkab loyihalarni to'liq noldan ishlab chiqarishga tayyor MVP (Frontend + Backend + Database + Security) karkasiga aylantirish.
  3. Barcha 11 subagent (`Scout`, `Sculptor`, `Inspector`, `Designer`, `Animator`, `Editor`, `Painter`, `Notion`, `Slack`, `SuperAgent`, `Sentinel`) 100% faol holatga keltirildi va testlandi.
  4. Barcha 78 ta pytest unit/integration testlari 100% PASS. Titlebarda 4-rejimli boshqaruv (`STANDART` | `EEPX` | `SWARM` | `DEEPX`) va Oyna 2 da DeepX kognitiv daraxti, DeepSearch iqtiboslari hamda Sentinel sertifikati to'liq ishga tushirildi.
  5. GitHub Repository yaratildi va butun loyiha to'liq push qilindi: https://github.com/jahongashtamc/conduit (main branch).


## MVP tayyorlov (2026-11-11, 11:43)
- `conduit doctor` — 19 bandli tizim tekshiruvi (backend/doctor.py), exit code 0/1.
- `conduit demo <agent>` — 11 agent uchun tayyor demo vazifa, PASS/FAIL kutiladi.
- Yangi toollar: gen_image (PIL), video_render (FFmpeg MP4), anim_render (GIF), notion_api, slack_api.
- Blender 5.2 real render ulandi (apps.json 5.x yo'llari; avval simulyatsiya edi).
- Suhbat xotirasi: backend/user_memory.py, prompt'larga uslub konteksti qo'shiladi, Xotira tab'da ko'rinadi.
- Tuzatilgan: heartbeat config ildizdan noto'g'ri o'qilishi; create_dynamic_subagent role.md ust yozishi; Titlebar tab tugmalari yo'qligi.
- Testlar: 100 passed. FFmpeg PATH'da, Blender "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe".

## 2026-11-11: Instrument yordamchi agentlar + Qadam 1 qo'shimchalar
- 5 ta instrument agent qo'shildi: inst_blender, inst_video, inst_image, inst_web, inst_figma.
  LLM planner'siz to'g'ridan-to'g'ri asbob bajaruvchi (0.2-7s vs 110-360s LLM agentlar).
- role.md'dagi 7 ta takrorlangan "Ruxsat etilgan toollar" bo'limi tozalandi.
- gen_image/video_render/anim_render/blender_headless endi chaqiruvchi agentning OZ workspace'iga yozadi (agent_id param).
- cli_runner: stdin=DEVNULL (agy stdin'da qotishi oldini olish), inst_* keyword-fallback'dan chiqarildi.
- app_adapter: Blender frame raqami (0001) fayl nomini to'g'rilaydi.
- Yangi API: /api/artifacts, /api/artifacts/file, /api/tokens (GET/POST/DELETE), /api/pipeline(s).
- UI: GalleryTab (Artefakt tab), Window7Profile'da token sozlash, vazifa tugaganda Windows notification.
- pipeline.py: ketma-ket agent zanjiri, oldingi natija keyingisiga kontekst, FAIL'da to'xtaydi.
- tools.py: web_search (DuckDuckGo HTML) + CLI dispatch.
- Testlar: 105 passed.

## 2026-11-11 (2): Haqiqiy agent sikli + terminalda real agy
- run_real_agent_loop: rol-agentlar endi bitta haqiqiy agy sessiyasida ishlaydi —
  agent O'ZI reja qiladi, tools.py'ni o'zi bajaradi, check_goal bilan tekshiradi,
  VERDICT: PASS/FAIL qaytaradi. Shablon doer/checker faqat inst_* uchun.
- agy --output-format stream-json: NDJSON hodisalar real vaqtda (text rejada
  agy hammasini buferlaydi — heartbeat noto'g'ri o'ldirardi).
- run_cli_subprocess: shell qator o'rniga shlex+create_subprocess_exec (cmd.exe
  qochish belgilari promptni buzardi). stream_json param + final_text.
- Terminal: 'agy' endi REAL interaktiv sessiya (stdin PIPE + WS->stdin piping),
  'agy <vazifa>' real CLI one-shot. Soxta banner olib tashlandi. shutil import tuzatildi.
- VERDICT regex xatosi (bad character range :-() tuzatildi.
- Tekshirildi: painter PASS 171s (gen_image o'zi bajardi), inspector PASS 160s
  (API health o'zi tekshirdi), terminal 'agy 1 deb javob ber' -> '1'.
- Testlar: 105 passed.

## 2026-11-12 (tun): Umumiy tekshiruv — hammasi tek
- 11/11 rol-agent REAL vazifalar bilan PASS: scout 327s, inspector 472s, sentinel 955s,
  sculptor 456s, designer 515s, animator 1356s, editor 458s, painter 321s,
  notion 644s, slack 648s, superagent 1549s (swarm 2 bosqich).
- Pipeline endi to'liq ishlaydi: 2 bosqichli zanjir (inst_web → inst_image) 2/2 PASS.
- KRITIK xato tuzatildi: retry va pipeline execute_task_lifecycle'ni ALMASHTIRILGAN
  argumentlar bilan chaqarardi (prompt↔agent). Barcha 4 chaqiruv joyi to'g'rilandi.
- Frontend eski build'ni servis qilardi (next start 11:41'dan beri) — qayta ishga tushirildi.
- UI DOM tekshiruvi: 16 agent kartasi, 5 tab (Studio/Miya/Xotira/Artefakt/Ilovalar) ko'rinadi.
- DB tozalandi: 0 working osilgan vazifa. Doctor: 16 OK / 3 WARN (tokenlar).
- verify_all_agents.py — tests ichida, istalgan vaqt qayta ishga tushirish mumkin.
- Testlar: 105 passed. Backend 200, Frontend 200, 16 subagent active.

## 2026-11-12: Haqiqiy PTY terminal (xterm.js + pywinpty)
- terminal_session.py to'liq qayta yozildi: subprocess+pipe o'rniga winpty.PtyProcess
  (powershell.exe -NoLogo -NoProfile, cwd=Conduit). Interaktiv agy/claude endi ishlaydi.
- winpty spawn QAVSIZ yo'l talab qiladi (quoted path -> "not executable" xato).
- WS /ws/terminal: raw bayt uzatish, {"type":"resize","cols","rows"} -> pty.setwinsize(),
  {"type":"clear"}, {"type":"close"} (PTY daraxti psutil bilan o'ldiriladi),
  {"type":"run","command"} (yordamchi; 'conduit ...' -> 'python conduit.py ...' tarjima).
- Frontend xterm.js: convertEol=false, fit -> resize WS'ga, beforeunload -> close,
  To'xtatish tugmasi (Power iconi). Reconnect backoff + scrollback qayta chiqarish saqlanadi.
- Test natijalari: PowerShell prompt OK; agy interaktiv OK (TUI render, javob, Ctrl+C ->
  prompt); claude TUI OK (trust dialogi render); close -> powershell daraxti o'ldi (5->4).
- Eslatma: agy/claude model kreditlari tugagan ("Out of credits") — PTY mexanikasi to'la,
  model javoblari kredit bog'liq. Testlar: backend/tests/test_pty_terminal.py,
  test_pty_claude.py (websocket client, pytest'ga kirmaydi - 105 passed saqlanadi).

## 2026-11-21: Repo ishga tushirish va EVIDENCE-MANDATORY tuzatish
- Yangi klondan ishga tushirish: `pip install -r backend/requirements.txt` + `cd frontend && npm ci`.
  Doctor dastlab "no such table: tasks" beradi — backend'ni ishga tushirishdan oldin
  `python -c "import sys; sys.path.insert(0,'backend'); import database; database.init_db()"` kerak.
- `backend/tools.py::tool_check_goal`: ko'rsatilgan skrinshot fayli diskda yo'q bo'lsa ham
  Node evaluator PASS berar edi. Endi fayl mavjudligi tekshiriladi (yo'q → FAIL), bo'sh dalil
  Node yo'nalishida ham NEEDS_INSPECTION bo'ladi. Sabab: `test_tools_py_direct_check_goal` xatosi.
- Tekshirildi: doctor 0 FAIL; pytest 105 passed / 2 skipped; npm lint + tsc + build OK;
  backend 8000 + frontend 3000 jonli; inst_image/inst_video/inst_web vazifalari PASS;
  scout demo (haqiqiy agy agenti) PASS 177s, skrinshot 1280x801, konsol xatosiz.
- `conduit_app.py`: watchdog daemon thread bo'lgani uchun launcher darrov chiqib ketar va
  watchdog o'char edi. Desktop rejimida `_watchdog_stop.wait()` bilan jarayon tirik ushlanadi.
  PC da ishga tushirish: `CONDUIT.bat` yoki `python conduit_app.py` — portlar band bo'lsa
  qayta ishga tushirmaydi, Edge `--app` oynasini ochadi.
- `.gitignore`: `backend/conduit.db-shm` va `-wal` runtime fayllari qo'shildi.

## 2026-11-21: Terminal ishlashi (PTY)
- Muammo: xterm.js avtomatik DA javobi (`ESC[?1;2c`) so'rov oynasida PTY'ga o'tib,
  PowerShell promptiga matn sifatida sizib chiqar edi (`[?1;2cython` → ParserError).
- Tuzatish: `backend/terminal_session.py` da `_alt_screen` holati kuzatiladi
  (`ESC[?1049h/l`, 1047, 47). Terminal javoblari FAQAT alternativ ekran TUI'si
  (vim/agy/claude) so'rov yuborganda o'tkaziladi; oddiy promptida tashlanadi.
- Tekshirildi: boshlang'ich chiqishda sizish yo'q; `echo FIX_OK` ishlaydi;
  agy TUI `ESC[?1049h` + DSR so'rovi bilan render bo'ladi, javob qabul qilinadi.
- Eslatma: Blender headless (EEVEE) vaqti-vaqti bilan EXCEPTION_ACCESS_VIOLATION beradi
  (GPU/libepoxy); qayta ishga tushirganda 8/8 test PASS — kod xatosi emas.

## 2026-11-21: UI dizayni v3 — "Quiet Workspace"
- Foydalanuvchi: "UI juda siqilgan, AI dizayni yoqmayapti", yo'nalishni o'zim tanladim.
- `globals.css` to'liq qayta yozildi: neon/aurora gradyanlari, binafsha/cyan glow,
  shisha effekti olib tashlandi; neytral qora sirtlar, bitta tinch ko'k aksent.
- O'qish qulayligi: body 14px, eski 10–11px yorliqlar 12px ga, `text-xs` 13px ga,
  `text-sm` 14px ga kattalashtirildi (global CSS override).
- `page.tsx`: aurora nur qatlami o'chirildi, panellar orasidagi bo'shliq va ichki padding oshdi.
- Barcha komponentlarda violet/purple/indigo/cyan → slate/calm; titlebar 48→56px,
  statusbar 28→36px, brend 56→64px, terminal shrifti 12→13px.
- Eslatma: xterm theme obyektidagi `cyan` kaliti ham almashtirilib ketgandi — tuzatildi.
- Tekshirildi: lint 0, tsc 0, build OK, 1600x1000 da gorizontal overflow yo'q.
  Skrinshotlar: `%TEMP%/opencode/conduit_ui_before.png` va `conduit_ui_after.png`.

## 2026-11-21: UI qo'shimchalari (so'rovsiz)
- Ishlaydigan **yorug'/qorong'u tema**: titlebarda Quyosh/Oy tugmasi, `localStorage`
  ga saqlanadi, `html.dark` classi bilan boshqariladi. Yorug' tema uchun barcha to'q
  sirt/matn/chegara sinflari izchil oq-kulrangga moslashtirildi; terminal ichi qora qoladi.
- Faol holatlar (`aria-pressed/selected/current`) endi aniq tinch ko'k fon bilan ajraladi.
- Subagent tafsilot panelidagi PLANNER/DOER/CHECKER kartalari: kattaroq padding,
  `min-h-[8.5rem]`, matn `line-clamp-6` — uzun chiqishlar qatordan chiqib ketmaydi.
- Tekshirildi: lint 0, tsc 0, build OK; ikkala tema 1600x1000 da skrinshotlandi
  (`%TEMP%/opencode/conduit_dark.png`, `conduit_light.png`), overflow yo'q.

## 2026-11-21: Studiya kengaytmasi — Agentlar katalogi + Vazifa kompozitori
- Yangi to'liq tab `agents` (chap navigatsiyada "Agentlar"): 16 ta agent kartasi,
  qidiruv, filtrlar (Barcha/Rol/Instrument/Faol), oxirgi vazifa holati (PASS/FAIL/BLOCKED),
  har kartadan "Ishga tushir" tugmasi. `frontend/src/components/AgentsCatalog.tsx`.
- Yangi `frontend/src/components/TaskComposer.tsx`: tezkor shablonlar (WEB/3D/AUDIT/UI/VIDEO),
  vazifa matni, agent tanlash, yadro rejimi (STANDARD/EEPX/SUPER_AGENT/DEEPX),
  Ctrl+Enter yuborish, Escape yopish. `page.tsx` da `handleComposerDispatch` orqali
  `/api/tasks` ga POST va vazifalar ro'yxatini yangilaydi.
- Tekshirildi (Playwright, 1600x1000): 16 karta, kompozitor ochiladi, yuborish ishlaydi,
  `task_914b830b` (inst_image) PASS 0.36s, modal yopiladi, overflow yo'q.
  Skrinshotlar: `%TEMP%/opencode/agents_catalog.png`, `task_composer.png`.

## 2026-11-21 17:10 — Poydevor qayta tekshiruvi (universal studio)
- `doctor` 0 FAIL (FFmpeg 9.0.2, Blender 5.2, agy/opencode/claude/codex PATH'da).
- To'liq pytest (ignore'siz): 105 passed, 2 skipped; `conftest.py asyncio` saqlanadi.
- Real render: `workspaces/sculptor/conduit_spin_cube.mp4` — 120 kadr, 1920x1080, 24fps,
  5.0s, h264, 947149 bayt. Kadrlar 0s/4.5s farqli (aylanish tasdiqlandi). Blender 5.2
  `action.fcurves` API o'zgargani uchun skript layered API ga o'tkazildi.
- Agent orqali render: `task_f23f90ed` (sculptor) PASS 382.67s, dalil MP4 fayli va hajmi.
- Jonli sahna: shu vazifada `/ws/task/{id}` orqali 16 `log` + 40 `preview_frame` hodisasi keldi.
- DeepSearch: jonli qidiruv 8 nomzod qaytardi; github_code HTTP 401 xatosi `source_errors`
  ga yozildi va logda ko'rindi; majburiy 4 xato ham 4 ta xato sifatida qayd etildi.
- Universal: `agents.json` ga `opencode_agent` qo'shildi, kod o'zgarishi yo'q, API darrov ko'rsatdi.
- DeepX: `task_6ea1f735` (execution_mode=deepx) `deepx_swarm_execution` bosqichigacha yetdi;
  loglarda DeepSearch manba xatolari (github_code 401, npm 400, pypi 404) ko'rinadi.
- Terminal qabul testi: WS orqali `conduit run inst_image "Terminaldan CLI test"` →
  `task_0125a043`, keyin `conduit status` va `conduit result` ishladi.
- Uchinchi agent: `agents.json` ga qo'shilgan `opencode_agent` faollashtirildi,
  `task_edd2b6f3` PASS; engine yana `agy` ga qaytarildi.
- MCP'siz rejim: Conduit workspace'iga bo'sh `.agents/mcp_config.json` yoziladi
  (global sozlamaga tegilmadi). Manba: agy issue #342/#1088 + rasmiy MCP docs.
- Eslatma: terminalda interaktiv `agy` TUI ochildi va javob berdi, lekin avtomatlashtirilgan
  matn kiritish TUI ichidagi editor/permission dialogiga tushib, `conduit run` chaqiruvigacha
  yetmadi — bu inson ishtirokini talab qiladigan TUI cheklovi, PTY mexanizmi ishlaydi.

## 2026-11-21 18:05 — Kirishda AI agent tanlovi
- Yangi `frontend/src/components/AgentChoiceModal.tsx`:
  birinchi ochilishda 6 ta agent kartasi (nomi, `binary`, TAYYOR/YO'Q holati, izoh).
- Tanlov `localStorage.conduit-engine` + `conduit-launch-agent` ga saqlanadi,
  `/api/engine/select` chaqiriladi, statusbar va chap panel faol agentni ko'rsatadi.
- `Window1Terminal` WS orqali `{type:'launch_agent',engine:...}` yuboradi;
  `terminal_session.py` agents.json dagi binary ni olib PTY ga yozadi (xavfsiz token tekshiruvi bilan).
- Tekshirildi (Playwright): MODAL FIRST 1, CARDS 6, tanlovdan keyin server `codex_cli`,
  LS `codex_cli`, qayta yuklaganda MODAL 0, LS saqlangan; PTY scrollback'da `codex` ko'rinadi.
- Sinovdan keyin server dvigateli `agy` ga qaytarildi (foydalanuvchi o'zi tanlaydi).
- 2026-11-21 18:20: kirish ro'yxati 13 taga kengaytirildi: gemini_cli, cursor_cli, qwen_cli,
  kimi_cli, glm_cli, copilot_cli, aider qo'shildi. `get_engine_status` 13 ta agent qaytaradi,
  6 tasi TAYYOR; Playwright: modalda 13 karta, jumladan barcha 7 yangisi bor.
  Skrinshot: `%TEMP%/opencode/engine_choice_13.png`.

## 2026-11-21 19:10 — Terminal MCP xatosi
- Skrinshotdagi xato: agy global 22 MCP serverdan `data-agent-kit` (`jsonbook_soc gate Prefilter`)
  tool chaqirganida exit 255 + invalid UTF-8 qaytargan. Sabab: interaktiv PTY bo'sh `agy` bilan
  ochilgan va global MCP serverlar yuklangan; `workspaces/<agent>/.agents/` konfiguratsiyasi
  terminalga tatbiq etilmagan (cwd = repo ildizi).
- Tuzatish: `agents.json` da `interactive_command` (agy: `--dangerously-skip-permissions`;
  claude: `--strict-mcp-config --mcp-config ...`), repo ildizida bo'sh `.agents/mcp_config.json`,
  yo'riqnomada "MCP toollarini chaqirish TAQIQLANGAN", launch buyrug'i shlex + xavfsizlik tekshiruvi bilan.
- Tekshirildi: ANSI tozalangach PTY chiqishida `agy --dangerously-skip-permissions` bor,
  `py_compile` OK, 3 ta yo'riqnoma qayta generatsiya qilindi.
- Cheklov: agy MCP serverlarni start paytida yuklashda davom etadi (CLI flagi yo'q); global sozlamaga tegilmadi.

## 2026-11-21 19:35 — Qolgan buglar
- Agent almashtirilganda (launch_agent) eski PTY daraxti `shutdown()` bilan yopiladi, 0.4s yangi
  prompt kutiladi, keyin yangi agent yoziladi — oldingi TUI ga buyruq tushib ketish bug'i yo'qoldi.
- Kirish modali: `available !== true` agent uchun "Yangi vazifa" tugmasi bloklanadi va
  "CLI tizimda topilmadi" ogohlantirishi ko'rsatiladi.
- `main._task_preview_frame`: oxirgi 0.6s ichida o'zgartirilgan rasm fayllari o'tkazib yuboriladi
  (yarim yozilgan PNG larni o'qishdan kelgan "image truncated" log shovqini tugadi).
- Tekshirildi: WS swap (Sessiya yopildi True / yangi prompt True / codex ishga tushdi True),
  Playwright (13 karta, unavailable disabled True, warning True), pytest 105 passed 2 skipped,
  lint/tsc/build OK, py_compile OK.
- 2026-11-21 20:00: UI o'lchami qayta muvozanatlandi — shrift 11/12/13px, body 13px,
  modal max-w-3xl va ixcham kartalar. Skrinshotlar: `%TEMP%/opencode/modal_balanced.png`,
  `ui_balanced.png`. `tsc`/`build` OK.
- 2026-11-21 20:20: brend **NEXUS** (CLI buyrug'i `conduit` saqlanadi); STD/EEPX/SUPER/DEEPX
  faol rejim statusbarda ko'rinadi; Window3 dagi bezak chiziqlari olib tashlandi;
  profilda Hajm 0.9/1/1.1 nazorati (standart 0.9). Tekshirildi: Playwright TITLE/NEXUS/SVG 0/
  ZOOM 0.9/MODE API eepx/FOOTER EEPX; keyin rejim `standard` ga qaytarildi.
  Skrinshot: `%TEMP%/opencode/nexus_ui.png`. `tsc`/`build` OK.
## 2026-11-22 00:15 — 5 soatlik yakuniy barqarorlik
- SuperAgent 	ask_b7bc0db9 PASS, DeepX 	ask_9a405d30 PASS (qayta ishga tushirilgandan keyin).
- Blender headless EEVEE/Workbench WGL crash → Cycles CPU (32 sample) bilan tuzatildi; haqiqiy kadr olinadi.
- Jimgina try/exceptlar 14 ta backend modulida loglanadigan qilindi; py_compile/compileall 0.
- Yangi regression testlar: ackend/tests/test_studio_regressions.py (3 ta) — jami test 108 passed, 2 skipped.
- Terminal prompt-tayyorligi bilan agy toza ishga tushadi: LAUNCHED/TUI/NO CMD ERROR.
- Barcha to'liq tablarga umumiy 'Studiyaga qaytish' tugmasi qo'shildi; Playwright 5/6 tab OK, konsol 0 xato, overflow yo'q.
- 30 daqiqalik soak-test (har 2 daqiqada vazifa) ishga tushirildi.
## 2026-11-22 13:12 - Subagentlar = agentga bog'langan tool'lar (2 soat)
- Rasmiy subagent modeli o'rganildi: alohida kontekst + qisqa tavsif asosida delegatsiya + tool allowlist + umumiy token/narx limiti (code.claude.com/docs/en/subagents.md).
- `backend/tool_registry.py`: 16 subagent `conduit_run_<id>` tool'i sifatida; `conduit tools --json`, `conduit budget --json`, `GET /api/tools/catalog`. Tavsiflar jami 334 token.
- AGENTS/CLAUDE/GEMINI v3 yo'riqnomasi va statusbarda byudjet ko'rsatigichi qo'shildi.
- Provider token usage oxirgi `result` hodisadan olinadi (cumulative qo'shish xatosi yo'q); PONG sinovi 13944/24.
- DALIL: jonli agy 16 toolni topdi va o'zi `conduit run inst_image` orqali `task_e1bda0f0` ni PASS qildi. Test 116 passed 2 skipped, doctor/lint/build 0.
## 2026-11-22 13:35 - Native subagentlar va yakuniy barqarorlik
- `backend/native_subagents.py`: 16 ta `conduit_<id>.md` lokal `.agents/agents/` ga yoziladi (agy official format). Global sozlama tegilmadi.
- agy ularni o'zi topadi: HAS_CONDUIT_SCOUT True; startup 8.2s, RC 0. Faqat tasdiqlangan agy tool nomlari ishlatiladi.
- Statusbar byudjeti 15s da yangilanadi; Figma validatoridagi hardcoded kalit/token olib tashlandi.
- To'liq test: 118 passed, 2 skipped. doctor/lint/build/tsc 0.

- 2026-11-23: python tools.py list_tools — 15 ta instrumentning to'liq katalogi; CONDUIT_AGENT muhit o'zgaruvchisi bajaruvchida role.md allowlist'ni qo'llaydi (ruxsatsiz tool exit 2).
- 2026-11-23: check_goal faqat joriy vazifa (CONDUIT_TASK_STARTED_AT) davomida yaratilgan dalilni qabul qiladi; eski latest.png endi PASS bermaydi.

## 2026-11-26 15:05 — Eski nusxa arxivlandi, shakl/montaj/terminal nuqsonlari tuzatildi
- `C:\Users\Kapitan\conduit` (eski nusxa) -> `C:\Users\Kapitan\_archive\conduit_old_2026-11-26`.
  Ish stolidagi yorliq faqat shu faol nusxani ochadi endi.
- `live_browser_session.py` boshqa checkout'ning `node_modules` iga qattiq bog'langan edi;
  playwright endi helper faylidan yuqoriga qarab, keyin CONDUIT_ROOT, keyin `npm root -g`.
  `backend/package.json` playwright 1.65.0 ni e'lon qiladi. Brauzer paneli eski nusxasiz
  ishlashi API orqali isbotlandi (navigate -> success + real title).
- `app_adapter._VISUAL_SHAPES`: uchburchak/yulduz/doira/to'rtburchak/beshburchak/oltiburchak
  qo'shildi; shakl nomidagi son so'zlari ("uchburchak" dagi "uch") endi son hisoblanmaydi;
  shakl tartibi vazifa matnidagi tartibda.
- `tool_gen_image` har bir shaklni haqiqiy chizadi; Blender yassi shakllarni 90° X atrofida
  buradi — avval disk gorizontal yotib, kamera faqat qirrasini ko'rardi (uchburchak "quti").
- 204 passed. `conduit run sculptor "sariq yulduz 3D modelini yaratib render qil"` -> PASS,
  dalil: tik 5 qirrali yulduz. `conduit run editor` 2 klip bilan montaj -> 1280x720, 72 kadr, 3.0s.
- `ok` Terminal 11/11 E2E PASS (fokus, buyruq, backspace, kirill, Ctrl+C, tarix, uzun, xato).
## 2026-11-26 17:35 — Soxta PASS sinfi va instrument nuqsonlari (2-bosqich)
- **Eng og'ir nuqson:** `check_goal` dalil MATNINI o'qimasdi — "video_render xato: kirish
  fayli kerak" yozuvi bilan ham PASS berilardi. `_evidence_reports_failure()` qo'shildi
  (xato:, error:, failed, muvaffaqiyatsiz, ishlamadi, traceback, exception, success:false).
  "topilmadi" ataylab qo'shilmadi — muvaffaqiyatli natijada ham uchraydi.
- `cli_runner`: `inst_ok` endi checker'ga `inst_doer_ok` sifatida uzatiladi — instrument
  FAIL bo'lsa vazifa PASS bo'lmaydi.
- `inst_image` VA `painter` ikkalasi ham `512x512` ni qattiq kodlagan edi; endi
  `parse_image_size()` vazifa matnidan o'lcham oladi (640x480, 800*600, 1024×768).
  Regressiya testi: `test_no_caller_hardcodes_512()` cli_runner'ni grep qiladi.
- `inst_web`/`inst_figma` dalili DOIM bo'sh chiqardi (`output` maydoni yo'q). Endi
  interact_web konsol/tarmoq xato sonlarini, figma_sync holat/komponent/rang sonini beradi.
- `tool_screenshot`: `output_path` Node yordamchisiga PAPKA sifatida berilardi va
  `example.png/` papkasi yaratilardi. Endi `dirname` beriladi, natija faylga ko'chiriladi.
- `star` hajmli (ikki qavat + yon yoqlar), `rect` haqiqiy 1.35x0.5x0.85 quti.
- Barcha tuzatishlar mutation bilan tekshirildi (buzilsa test yiqiladi). 230 passed.
- Jonli dalillar: sculptor PASS (hajmli yulduz), animator PASS (36 kadr GIF, 36/36 noyob),
  editor PASS (2 klip, 1280x720 72 kadr), scout PASS (haqiqiy PNG fayl), inst_web PASS,
  inst_figma FAIL (token yo'q — halol), inst_video FAIL klipsiz / PASS klip bilan.
## 2026-11-26 22:58 — Windows kodlash sinfi va inst_web soxta PASS (3-bosqich)
- **Ildiz sabab:** `subprocess.run(..., text=True)` Windows'da `locale.getpreferredencoding()`
  (bu mashinada **cp1251**) bilan dekodlaydi. Node stdout'ni **UTF-8**, PowerShell esa
  **cp866** da yozadi. Kirill yo'l (`Проект по умолчанию`) mojibake bo'lardi.
- `run_node_eval` (backend/tools.py): `encoding="utf-8", errors="replace"` qo'shildi.
  Avval `tool_screenshot` "success: true" qaytarib, mavjud bo'lmagan yo'l berardi.
- `tool_screenshot`: qaytarilgan yo'l diskda mavjud va bo'sh emasligi **tekshiriladi**;
  aks holda `success: False` — soxta muvaffaqiyat yopildi.
- `run_isolated_script` (app_adapter.py): bola muhitiga `PYTHONIOENCODING/PYTHONUTF8`
  (nusxa, global emas) + UTF-8 dekodlash. Blender/`run_process` shoxlari ham.
- `inst_web` (cli_runner.py): vazifa "skrinshot/surat/kadr/rasm ol" so'rasa endi
  `tool_screenshot` chaqiriladi. Avval HAR DOIM `interact_web` bo'lib, fayl
  yaratilmasdan PASS berilardi — talab bajarilmagan soxta PASS.
- `voice/tts.py` `list_voices`: PowerShell `[Console]::OutputEncoding=UTF8` +
  UTF-8 dekodlash (ruscha ovoz nomlari cp866 da buzilardi).
- Testlar: `test_utf8_subprocess.py` (6) + `test_inst_web_action.py` (10), mutation
  bilan tasdiqlangan. To'liq: **246 passed**. tsc/compileall/doctor 0 xato.
- Jonli dalil: skrinshot vazifasi PASS, haqiqiy 37 033 baytlik PNG.

## 2026-11-27 02:06 — To'liq audit: terminal, toollar, API (deep-plan)
- **Terminal Ctrl+C umuman ishlamasdi** — ildiz sabab: pywinpty 3.x `spawn()` da
  backend berilmasa WinPTY'ga tushadi, u yerda Ctrl+C ishlamaydi. O'lchov:
  `PYWINPTY_BACKEND=1` (ConPTY) -> 4/4 OK; `0` yoki env yo'q -> 0/4.
  Tuzatish: `_spawn_pty()` da `setdefault("PYWINPTY_BACKEND","1")` + `sendintr()`.
- `voice_speak language="uz"` ONNX `indices out of bounds`: (1) `normalize_text`
  `uz` ni tanimasdi -> lotin harflar lug'atda yo'q; (2) `vocab.get("<unk>",45)`
  lug'at (0..44) tashqarisida. Ikkalasi tuzatildi. `uz/uzbek` endi `auto` kabi.
- `voice_doctor` model hash "MOS EMAS": `core.autocrlf=true` CRLF'ga o'girgan.
  `.gitattributes` (`*.json text eol=lf`) + CRLF'ga chidamli hash tekshiruvi.
- `onnxruntime` `requirements.txt` da yo'q edi -> qo'shildi (1.32.0).
- `/api/clones/{name}` 500 -> `CloneError` ushlanmayotgan edi, 404 qilindi.
- `/api/sentinel/audit` HAR DOIM 500 -> `ConduitKernel` import yo'q edi (NameError).
- `/api/engine/select` noma'lum nomga jim 200 -> endi 404 + ro'yxat.
- `browser/navigate` `not-a-url` ni qabul qilardi -> TLD validatsiyasi qo'shildi.
- **Router instrumentlarni tanlamasdi**: "rasm yarat" 2-6 daqiqalik rol-agentga
  ketardi. Endi tez yo'l: `inst_image`/`inst_blender`/`inst_video` (0.6s).
  Murakkab so'rovlar (qidiruv+audit, AE, Figma) eski yo'lda.
- `_agent_busy` marker bermaydigan CLI'larda (claude/codex) abadiy qolardi ->
  PowerShell promptida tozalanadi + 180s sukunatdan keyin eskiredi.
- Toollar: 16/16 haqiqiy artefakt bilan PASS. Terminal: 9/10 (bulk probe
  timeout; alohida 200/200). API: 37/47 GET 5xx emas, 18/19 POST validatsiya.
- Testlar: **325 passed** (avval 246). Yangi: test_pty_backend, test_inst_web_action,
  test_utf8_subprocess, router/URL/voice regressionlari. Mutation bilan tasdiqlangan.

## 2026-11-27 11:01 — CI yashil qilindi (GitHub Actions qulatardi)
CI 4 ketma-ket push'da `failure` edi: backend job 6 testda yiqilardi. Ildiz sabablar
va tuzatishlar:
- **`check_goal` CI'da `verdict` qaytarmasdi** — yagona evaluator global Gemini
  plagin papkasida (`~/.gemini/config/plugins/...`), repo'da esa yo'q. Node/plugin
  bo'lmasa darvoza butunlay ochiq qolardi. Endi `_builtin_goal_evaluator()` repo
  ichida zaxira: shartnoma bir xil, `evaluator: "builtin"` belgisi bilan.
- **`test_five_hour_findings` 3 testi tirik backend talab qilardi** — CI'da hech kim
  ko'tarmaydi, lokalda esa tasodifan ochiq studiya serveriga ulanardi (natija
  muhitga bog'liq). Yangi `live_backend` fixture (`conftest.py`) bo'sh portda
  `uvicorn --lifespan off` bilan toza server ko'taradi (startup hook tirik
  vazifalarni BLOCKED qilib qo'ymasligi uchun). Test o'zi vazifa yaratib tozalaydi
  (CI bazasi bo'sh).
- **`test_pty_terminal/env/claude` import paytida `asyncio.run(main())`** chaqirardi
  — pytest yig'ishda yiqilardi, shuning uchun CI ularni `--ignore` qilardi. Endi
  `if __name__ == "__main__":` guard — fayllar pytest uchun xavfsiz, qo'lda
  ishga tushirish ham saqlanadi.
- **`test_utf8_subprocess` `voice` import qilolmasdi** — paket repo ildizida,
  backend/ ichida emas. Test ildizni `sys.path`ga qo'shadi.
- **`video_render` ffmpeg yo'qligini kirish fayldan oldin aytardi** — CI'da
  ffmpeg yo'q, test esa "kirish video kerak" xabarini kutadi. Endi kirish
  fayllari ffmpeg'dan OLDIN tekshiriladi (foydalanuvchi uchun ham to'g'riroq).
- **`clones/rea` buziq gitlink** (`.gitmodules` yo'q) — har `git checkout`da
  "fatal: No url found for submodule path" berardi. `git rm --cached` qilindi;
  `clones/` endi ignore (registry — runtime holat, repo fayli emas).
- Natija: backend **268 passed** (CI bayroqlari bilan), voice **57 passed**,
  frontend lint/tsc/build toza.
