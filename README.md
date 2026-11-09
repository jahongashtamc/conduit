# Conduit — AI Agentlar Uchun Ilovalar Dashboardi va Subagent Boshqaruv Tizimi

Conduit professional ilovalar (Blender, After Effects, DaVinci, Premiere, Maya, Figma) va brauzer agentlarini yagona markazdan boshqaruvchi ekotizimdir.

## 🚀 O'rnatish va Talablar

- **Python**: 3.10+ (tizimda Python 3.14 o'rnatilgan)
- **Node.js**: v18+ (tizimda Node.js v24 o'rnatilgan)

### Backendni sozlash:
```bash
cd backend
python -m pip install -r requirements.txt
python main.py
# Backend http://localhost:8000 da ishga tushadi
```

### Frontendni sozlash:
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
