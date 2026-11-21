# Conduit — AI Agentlar Uchun Ilovalar Dashboardi va Subagent Boshqaruv Tizimi

![CI](https://github.com/jahongashtamc/conduit/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

Conduit professional ilovalar (Blender, After Effects, DaVinci, Premiere, Maya, Figma) va brauzer agentlarini yagona markazdan boshqaruvchi ekotizimdir.

## ⚡ 3 Qadamda Boshlash (Quickstart)

1. **Ishga tushirish:** ish stolidagi `Conduit AI Studio` yorlig'ini bosing (yoki `CONDUIT.bat`).
2. **Tekshirish:** terminalda `python conduit.py doctor` — hamma narsa tayyorligini ko'rsatadi.
3. **Birinchi vazifa:** `python conduit.py demo scout` — agent brauzer ochadi, skrinshot oladi va PASS qaytaradi.

Har bir agentni sinash:
```bash
python conduit.py demo sculptor   # haqiqiy Blender 3D render
python conduit.py demo painter    # gen_image bilan PNG
python conduit.py demo editor     # FFmpeg bilan MP4 video
python conduit.py demo animator   # keyframe'dan GIF animatsiya
python conduit.py demo designer   # Figma spec sinxronizatsiya
```

## 📦 MVP Holati (nima tayyor)

| Tizim | Holat |
|---|---|
| 16 subagent (`subagents/`), `run/status/wait/list/kill-all` | ✅ |
| Real instrumentlar: screenshot, interact_web, blender (haqiqiy render — 1080p MP4 tekshirilgan), figma, gen_image (PIL), video_render (FFmpeg MP4), anim_render (GIF), notion_api, slack_api | ✅ |
| Jonli brauzer ko'rinishi (Jonli tab, 1.5s yangilanish) | ✅ |
| Studio terminali: haqiqiy PTY (pywinpty), `conduit` CLI terminal ichida ishlaydi | ✅ |
| Suhbat xotirasi (agent foydalanuvchi uslubini o'rganadi) | ✅ |
| DeepSearch (jonli GitHub/npm/PyPI qidiruv) + DeepX (litsenziya/xavfsizlik baholash) | ✅ end-to-end tekshirilgan: task_ff8168e6 — DeepSearch 5 manba → DeepX 5 nomzod → 4 bosqichli fikrlash → MVP scaffold → Swarm 3 bosqich PASS → Sentinel 100/100 (798.57s) |
| DeepX Swarm artefaktlari: haqiqiy fayl yoziladi (`workspaces/<agent>/artefact_*.out`) | ✅ soxta nom bug'i tuzatildi, `test_write_stage_artifact_real_file` |
| Sentinel sertifikati faqat auditdan keyin: blueprint `PENDING_AUDIT` → real ball bilan yangilanadi; UI qattiq "100% XAVFSIZ" o'rniga real holat | ✅ |
| Watchdog: heartbeat timeout, osilgan jarayonlarni yopish | ✅ |
| Watchdog: backend/frontend o'lsa 10s da avtomatik qayta ishga tushirish (desktop_app.py + conduit_app.py) | ✅ |
| Desktop ilova (Edge/Chrome --app, ish stoli yorlig'i) | ✅ |
| Standalone exe: `dist/Conduit Studio/Conduit Studio.exe` (PyInstaller, konsol yashirin) | ✅ |
| Dvigatel: `agy` (Gemini) | ✅ |
| Dvigatel: `opencode` (OpenCode CLI) | ✅ o'z auth'i orqali — inspector PASS (task_14b5715b), painter PASS (task_775c4bf5, gen_52861.png), sculptor PASS (task_d7836011), DeepX quvuri PASS (task_ff8168e6), standart rejim regressiya PASS (task_2d710907, test_qalqon.png) |
| Dvigatel: `crush` (Charm) | ⚠️ sozlangan; Gemini free kunlik token kvotasi tugagan — ertalab ~11:00 RTZST dan keyin ishlaydi (halol "retry in 19h14m" xatosi ko'rinadi, task_91ecaeba) |
| Dvigatel: `claude` (Claude Code CLI) | ⚠️ auth kerak — OmniRoute gateway o'chirildi (foydalanuvchi talabi); login qilingach ishlaydi |
| Dvigatel: `codex` (OpenAI Codex CLI) | ⚠️ OpenAI auth kerak (`codex login`) |
| OmniRoute | ❌ olib tashlandi — har bir agent o'z auth/backend'idan foydalanadi |
| Qabul sinovi (H): 3 agent PTY terminalda `conduit run` → PASS | ✅ claude (task_c8ddeccd), agy (task_e7ca6e3b), codex (task_d56165f4) |
| Jonli sahna model shakllanishi: 128 preview_frame, dalil kadrlari | ✅ task_af027ef3, `live_scene_evidence_*.png`, `form_scene_agy.mp4` (5s 1080p) |
| Universal agent qatlami: `agents.json` — har qanday CLI agent (agy, claude, Codex, Gemini CLI...) bitta JSON yozuv bilan qo'shiladi | ✅ |
| MCP'siz rejim: Conduit chaqiruvlari MCP yuklamaydi (claude `--strict-mcp-config`, ~9s) | ✅ |
| Jonli sahna: `/ws/task/{task_id}` — qadam hodisalari + preview kadrlar | ✅ |
| `conduit watch <task_id>` — vazifani jonli kuzatish | ✅ |
| Haqiqiy Blender video render: `tools.py blender_video` (120 kadr 1080p → MP4 tekshirilgan) | ✅ |
| FFmpeg | ✅ o'rnatilgan (WinGet `Gyan.FFmpeg` 9.0.2), PATH'da |
| Notion/Slack real integratsiya | ⚠️ token kerak (`NOTION_TOKEN`, `SLACK_BOT_TOKEN`) |
| `tools/vendor/` (uchinchi tomon asboblari) | ❌ repo ichida yo'q — `THIRD_PARTY.md` ga qarang |
| Ko'p foydalanuvchi / auth / cloud | ❌ MVP doirasidan tashqari |

## 🚀 O'rnatish va Talablar

- **Python**: 3.10+ (tekshirilgan: 3.12.10)
- **Node.js**: v18+ (tekshirilgan: v22.23.3)
- **pywinpty**: `pip install pywinpty` — terminal PTY uchun **majburiy**. Busiz interaktiv CLI (`agy`, `claude`) osilib qoladi.
- **FFmpeg**: `winget install Gyan.FFmpeg` — `video_render` va `anim_render` uchun. PATH'da bo'lishi shart.

Tekshirish: `python conduit.py doctor` — 0 FAIL bo'lishi kerak.

### Desktop ilova sifatida ishga tushirish (tavsiya etiladi)

Windows'da ish stolidagi **Conduit AI Studio** yorlig'ini bosing, yoki:
```bash
CONDUIT.bat
```

Launcher backend (8000) va frontendni (3000) o'zi ishga tushiradi, tayyor
bo'lishini kutadi va Conduit'ni manzil qatorisiz alohida desktop oynasida
ochadi. To'xtatish uchun `stop_conduit.bat`.

### Standalone exe (app versiyasi)

Ish stolidagi **Conduit Studio** yorlig'i endi to'g'ridan-to'g'ri
`dist/Conduit Studio/Conduit Studio.exe` ni ochadi — Python/Node kerak emas
(dekstop oyna pywebview orqali, servislar o'zi ko'tariladi, yopilsa tozalanadi).

Qayta build qilish:
```bash
python -m PyInstaller --noconfirm --clean --name "Conduit Studio" --console --icon conduit.ico desktop_app.py
```

**Muhim:** `--windowed` ishlatmang — antivirus PyInstaller'ning `runw.exe`
bootloaderini o'chirib tashlayapti. `--console` bilan build qilinadi; qora
konsol oynasi dastur ichida (`_hide_console_window()`) yashiriladi.

Watchdog: ikkala launcher ham har 10s da backend/frontend sog'lig'ini
tekshiradi — xizmat o'lsa avtomatik qayta ishga tushiriladi.

Qo'lda boshqarish:
```bash
python conduit_app.py              # odatdagi ishga tushirish
python conduit_app.py --dev        # Next.js dev server bilan
python conduit_app.py --no-window  # faqat servislar, oyna ochilmaydi
```

### Backendni alohida sozlash:
```bash
cd backend
python -m pip install -r requirements.txt
python main.py
# Backend http://localhost:8000 da ishga tushadi
```

### Frontendni alohida sozlash:
```bash
cd frontend
npm install
npm run dev
# Dashboard http://localhost:3000 da ochiladi
```

---

## 🧩 Yangi Subagent Qo'shish (Faqat papka nusxalash orqali!)

Conduit'da yangi subagent yaratish uchun **birorta qator dastur kodi o'zgartirilmaydi**. Tizim avtomatik ravishda `subagents/` papkasini skan qiladi.

1. `subagents/` papkasi ichida yangi nomli papka yarating, masalan `subagents/writer`:
   ```bash
   cp -r subagents/scout subagents/writer
   ```
2. Fayllarni o'zgartiring:
   - `subagents/writer/role.md` — Subagent nomi, uning roli, vazifasi va ruxsat berilgan toollar.
   - `subagents/writer/app.json` — Bog'langan dastur (masalan VS Code yoki Figma), faollik holati (`active` yoki `later`), ikonka va tavsif.
   - `subagents/writer/inner/planner.md` — Vazifani rejalashtirish ko'rsatmasi.
   - `subagents/writer/inner/doer.md` — Vazifani bajarish qadamlari.
   - `subagents/writer/inner/checker.md` — Natijani tekshirish qoidalari.
3. Backend darhol yangi agentni aniqlaydi va dashboard'da ko'rsatadi!

---

## 🏛️ Arxitektura va Tuzilma

```
conduit/
├── apps.json                  # Boshqariladigan ilovalar ro'yxati va holati
├── subagents/                 # Subagentlar katalogi (modular)
│   ├── scout/                 # Brauzer qidiruv agenti (Faol)
│   │   ├── role.md
│   │   ├── app.json
│   │   └── inner/
│   │       ├── planner.md
│   │       ├── doer.md
│   │       └── checker.md
│   ├── inspector/             # Tizim sinovchisi va auditori (Faol)
│   ├── sculptor/              # Blender 3D agenti (Keyinroq)
│   ├── animator/              # After Effects agenti (Keyinroq)
│   ├── editor/                # DaVinci/Premiere agenti (Keyinroq)
│   ├── painter/               # Photoshop agenti (Keyinroq)
│   └── designer/              # Figma agenti (Keyinroq)
├── backend/                   # FastAPI + SQLite + WebSockets
│   ├── main.py
│   ├── database.py
│   ├── apps_manager.py
│   ├── subagent_engine.py
│   └── tests/
└── frontend/                  # Next.js + React + Tailwind + GSAP
    ├── src/
    │   ├── app/
    │   ├── components/
    │   └── lib/
    └── package.json
```
