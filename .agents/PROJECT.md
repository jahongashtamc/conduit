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
  test_pty_claude.py (websocket client, pytest'ga kirmaydi — 105 passed saqlanadi).
