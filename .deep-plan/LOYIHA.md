# LOYIHA

## 1. MVP talablari nima?

Asosiy muammo: subagentlar ro'yxati va ularning tool'lari qog'ozda bor, lekin ular to'liq ishga tushmaydi hamda yaratilgan dalil eski fayl bo'lsa ham `check_goal` uni PASS deb qabul qiladi. Shuning uchun MVP: (1) barcha e'lon qilingan tool'lar uchun yagona katalog va CLI yordam chiqishi, (2) `tools.py` ichida haqiqiy ruxsat tekshiruvi, (3) dalil yangiligi va mazmunini qat'iy tekshirish, (4) asosiy agentga to'liq yo'riqnomada shu tool'larni ko'rsatish, (5) regression testlari. Tekshiruvlar: `python tools.py --help`, `python tools.py list_tools --json`, eski screenshot bilan `check_goal` FAIL bo'lishi, yangi yaratilgan dalil bilan PASS bo'lishi, ruxsat etilmagan tool rad etilishi, `pytest`.

## 2. Foydalanuvchi aynan nimani xohlaydi va qanday ishlashi kerak?

Foydalanuvchi: `tollar tolliq qoshilmagan va instrumentlar sabab ai agent qilyapti lekin ishi sifatsizbolyaoti`. Ya'ni tool'lar to'liq qo'shilmagan va instrumentlar tufayli AI agent ish qilayotgandek ko'rinadi, lekin natija sifatsiz. U tez va ishlaydigan natija xohlaydi. Kutilayotgan oqim: asosiy agent `conduit tools`/`python tools.py --help` orqali barcha tool'larni ko'radi, vazifani subagentga `conduit run <subagent> "..."` bilan topshiradi, subagent ruxsat etilgan tool'lardan foydalanadi, `check_goal` faqat shu vazifa uchun yangi yaratilgan dalil bo'lsa PASS beradi, aks holda FAIL va qayta ishlashga majbur qiladi.

## 3. Qismlar, oqim va eng kichik ishlaydigan qism

Oqim: `subagents/*/role.md` (tool e'lonlari) → `backend/security_guard.py::get_allowed_tools()` → `backend/tool_registry.py` (katalog) → `backend/engine/cli_runner.py` (agentga ko'rsatma va subprocess env) → `backend/tools.py` (tool bajaruvchi + ruxsat darvozasi + check_goal) → `backend/main.py` WS/API → frontend. Eng kichik ishlaydigan qism: bitta eski screenshot bilan `check_goal` FAIL, bitta yangi dalil bilan PASS va bitta ruxsatsiz tool rad etilishi. Bu ishlamagunicha UI chiroyliligining ahamiyati yo'q.

## 4. Har funksiya uchun eng qisqa to'g'ri yechim

Yangi framework yoki global MCP server qo'shmaymiz. Mavjud `tools.py` va `security_guard.py` ichida tekshiruv qo'shamiz; `tool_registry.py` orqali katalog chiqaramiz; `cli_runner.py` agent subprocess'iga `CONDUIT_AGENT` va `CONDUIT_TASK_ID` uzatadi; `tools.py` ularni o'qib, `verify_tool_access` chaqiradi. `check_goal` dalil sifatida faqat joriy vazifa boshlanganidan keyin yaratilgan faylni qabul qiladi va fayl mazmuni (taxminan 100 bayt) hamda turini tekshiradi. `validate_evidence_against_goal` kalit so'zlarga emas, aniq dalil obyektlariga asoslanadi.

## 5. O'xshash mahsulotlar va ustunliklar

Claude Code subagentlari alohida kontekst, maxsus system prompt va cheklangan tool to'plami bilan ishlaydi; OpenAI function calling'da tool tavsifi va sxemasi model kontekstiga kiradi, shuning uchun tool soni/tavsifi muhim; OpenCode'da ham tool'lar agentga bog'lanadi. Ustunlik: Conduit bularni bitta katalog va CLI orqali barcha AI agentlar (agy, claude, codex, opencode) uchun universal qiladi. **TAKLIF** (tasdiqlanmaguncha qo'shilmaydi): tool'lar soni va tavsif token byudjetini UI'da ko'rsatish.

## 6. Kiberxavfsizlik

`tools.py` hech qanday agent nomi yoki ruxsat parasini ishonchli deb qabul qilmaydi: faqat `cli_runner` tomonidan o'rnatilgan `CONDUIT_AGENT` env ishlatiladi, u yo'q bo'lsa barcha tool'lar rad etiladi (yoki faqat o'qish uchun xavfsizlari — eng qisqa variantda to'liq rad). Tool chiqishi modelga qaytadi, lekin ichidagi matn buyruq sifatida bajarilmaydi. Screenshot/fayl yo'llari workspace ichida tekshiriladi; global foydalanuvchi konfiguratsiyasi, auth va MCP sozlamalariga tegilmadi. Xatolar yutulmaydi, loglanadi.

## 7. Tayyorlik mezonlari

`python tools.py --help` barcha tool'larni ko'rsatadi; `python tools.py list_tools --json` 0 xato; eski `latest.png` bilan `check_goal` `verdict: FAIL`; yangi yaratilgan PNG bilan `verdict: PASS`; ruxsatsiz agent tool chaqiruvi `permission denied`; `pytest backend/tests -q` yashil, shu jumladan yangi regression testlari; `compileall`, `doctor`, `tsc`, `build`, `lint` 0; `gate.py verify OK`; faqat ko'zlangan fayllar o'zgargan.
