# Conduit: Loyiha Yo'l Xaritasi (Roadmap)

Conduit — professional ijodiy va hisoblash ilovalari (Blender, After Effects, DaVinci, Premiere, Maya, Figma) hamda `agent-studio-plugin` MCP vositalari ustiga qurilgan AI subagentlarni boshqarish tizimi va boshqaruv paneli (dashboard).

---

## Faza 1: Dashboard skeleti va Scout (brauzer) [BAJARILDI]
- [x] Ilovalar kartalari bosh sahifasi (Blender, After Effects, DaVinci, Premiere, Maya, Figma). Holatlar: `ready`, `not installed`, `running` (`apps.json` va OS monitoring asosida).
- [x] Subagent kartalari:
  - `Scout` (brauzer) - Faol (Active)
  - `Inspector` (tester) - Faol (Active)
  - `Sculptor` (Blender) - Keyinroq (Later)
  - `Animator` (After Effects) - Keyinroq (Later)
  - `Editor` (DaVinci/Premiere) - Keyinroq (Later)
  - `Painter` (Photoshop) - Keyinroq (Later)
  - `Designer` (Figma) - Keyinroq (Later)
- [x] Subagent fayl tizimi tuzilmasi: `subagents/<nom>/role.md`, `app.json`, `inner/` (`planner.md`, `doer.md`, `checker.md`). Yangi subagent qo'shish = papka nusxalash (kod o'zgarmaydi).
- [x] Scout subagenti: brauzer vazifalari, skrinshot va qadamlar bajarilishi.
- [x] Manager arxitekturasi: kelgan topshiriqni tahlil qilib to'g'ri subagentga yo'naltirish (o'zi ijrochi emas).
- [x] FastAPI backend, SQLite ma'lumotlar bazasi, WebSocket jonli yangilanishlar.
- [x] Next.js + Tailwind CSS + GSAP boshqaruv paneli (Dark/Light tema, UZ/EN tillar, Ctrl+K menyu, timeline, jonli panel).

---

## Faza 2: Ish joylari va xavfsizlik [BAJARILDI]
- [x] Har subagent uchun alohida izolyatsiyalangan workspace papkasi: `workspaces/<nom>/`.
- [x] `role.md` ichida ruxsat etilgan toollar oq ro'yxati (whitelist) nazorati. Begona tool chaqirilsa rad etish va xavfsizlik audit logiga yozish.
- [x] Sirli kalitlar himoyasi: API kalitlari va sirlar .env dan o'qilmasligi va UI da hech qachon oshkor bo'lmasligi (`[REDACTED_SECRET]`).
- [x] Xavfli amallar uchun modal tasdiq dialogi (fayl o'chirish, workspace tashqarisiga chiqish, tashqi buyruq). Tasdiqsiz bajarilmaslik.
- [x] Favqulodda "Kill all" tugmasi va dastur yopilganda barcha orqa fon jarayonlarini tozalash.

---

## Faza 3: Jonli ko'rish paneli [BAJARILDI]
- [x] Har subagentning jonli monitoringi: joriy qadam, so'nggi skrinshot, loglar oqimi, ijro vaqti, aniq holat (`idle`, `working`, `needs approval`, `PASS`, `FAIL`).
- [x] Vazifa timeline: `planner` → `doer` → `checker` qadamlari vizualizatsiyasi va oraliq xulosalar.
- [x] Dalilga asoslangan tasdiq: skrinshot + `check_goal` natijasisiz "tayyor" deb e'lon qilmaslik.

---

## Faza 4: Sculptor (Blender) va ilova adapterlari [BAJARILDI]
- [x] Umumiy ilova adapteri + `apps.json` (bajariluvchi yo'l, argumentlar shabloni, formatlar).
- [x] Blender headless boshqaruvi va 3D modellash subagenti (Sculptor).
- [x] Ketma-ket Animator, Editor, Painter modullari integratsiyasi.
- [x] Figma integratsiyasi (alohida REST/WebSocket moduli).
- [x] Avtonom skript generatsiyasi (`runScript`) xavfsiz muhit chegarasida.

---

## Faza 5: Inspector va test rejimi [BAJARILDI]
- [x] Inspector — kod yozuvchidan mustaqil auditor subagent (faqat tekshiradi, o'zi kod yozmaydi).
- [x] Real vaqtda test rejimi va PASS/FAIL baholash tizimi (False-pass to'liq bloklangan).
- [x] Xatolarni qayta ishlash halqasi (maksimal 3 iteratsiya va SelfHealer avto-tuzatish bilan).

---

## Faza 6: Deep UI va Super agent [BAJARILDI]
- [x] Deep UI: ichki agentlar (`planner`/`doer`/`checker`) xotira va EEPX 4-faza kognitiv tahliliga chuqurlashish.
- [x] Qadamma-qadam tarixni orqaga qaytarish va ko'rish (playback/history va checkpointlar).
- [x] Super agent: murakkab ko'p bosqichli topshiriqlarni subagentlarga parallel taqsimlash va Swarm quvuri orqali sintez qilish.

---

## Faza 7: Avtomatlashtirish va uzoq muddatli xotira [BAJARILDI]
- [x] Qayta ishlatiluvchi workflow'lar, Skillar (xavfsizlik skaneri bilan) va Saboqlar evolyutsiyasi.
- [x] Chuqur fikrlash bosqichi: EEPX P-bosqich yo'naltirilgan asiklik grafigi (DAG) orqali vazifani loyihalash.
- [x] Loyiha bo'yicha uzoq muddatli ixcham xotira (`memory/`, SQLite `memory`, `brain_memory` bloklari).
