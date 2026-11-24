# LOYIHA

## 1. MVP talablari nima?

Asosiy muammo tezlik emas, natija sifati: agent ish qilayotgandek ko'rinadi, lekin dalil eski yoki soxta bo'lsa ham vazifa PASS deb yopiladi. MVP: (1) har vazifa turi uchun obyektiv qabul mezonlari, (2) dalil yangiligi va haqiqiyligini fail-closed tekshirish, (3) mezon bajarilmaganda agentga aniq sabab qaytarib, cheklangan marta qayta ishlash, (4) natijani UI va hisobotda halol ko'rsatish. Minimal ishlaydigan holat: bo'sh/eski dalil bilan `check_goal` FAIL va sabab ko'rinadi; yangi, haqiqiy artefakt bilan PASS va artefakt yo'li ko'rinadi. Tekshiruv: `pytest backend/tests -q`, real `conduit run` + `conduit result`, `doctor`, `gate.py verify`.

## 2. Foydalanuvchi aynan nimani xohlaydi va qanday ishlashi kerak?

Foydalanuvchi aniq tuzatdi: `sust deganda umuman yomon demoqchi boldim qilayotgan ishlari yomon demoqchiman`, keyin `@deep-plan umumiy hammasi` deb butun jarayonni so'radi. Demak u render tezligini emas, AI agent bajarayotgan ishlarning umumiy sifatini nazarda tutgan. U bitta vazifani ko'rsatmadi, shuning uchun taxmin qilmay mavjud kod, loglar va testlar bo'yicha keng audit qilish kerak. Kutilayotgan oqim: vazifa beriladi → asosiy agent uni subagentga topshiradi → subagent haqiqiy artefakt yaratadi → qabul mezoni obyektiv tekshiradi → FAIL bo'lsa aniq sabab bilan qayta ishlanadi → UI va hisobotda faqat tasdiqlangan natija ko'rinadi.

## 3. Qismlar, oqim va eng kichik ishlaydigan qism

Oqim: `subagents/*/role.md` (vazifa/tool e'lonlari) → `backend/security_guard.py` (ruxsat) → `backend/tool_registry.py` (katalog) → `backend/engine/cli_runner.py` (agent ko'rsatmasi, retry va dalil yig'ish) → `backend/tools.py` (tool bajaruvchi va `check_goal`) → `backend/main.py` (WS/API) → frontend (Tasklar, jonli sahna, galereya). Eng kichik ishlaydigan qism: bitta vazifa uchun obyektiv mezon ro'yxati va uning fail-closed tekshiruvi. Bu ishlamagunicha UI bezaklari, tool katalogi kengaytirishlari va tezlik optimallashtirishlari foydasiz; foydalanuvchi aytgan "yomon ish" aynan shu yerda qoladi.

## 4. Har funksiya uchun eng qisqa to'g'ri yechim

Yangi framework, yangi MCP server yoki global konfiguratsiya kerak emas. Mavjud `tools.py`, `cli_runner.py`, `security_guard.py`, `tool_registry.py` va testlardan foydalanamiz. `check_goal` va `validate_evidence_against_goal` ichida kalit so'zlarga emas, artefakt mavjudligi, yangiligi, turi va o'lchamiga qaraymiz. `cli_runner` FAIL sababini agentga qaytarib, eng ko'pi 2 marta qayta urinadi; har urinish loglanadi. Agent yo'riqnomasiga qisqa "natija shartnomasi" qo'shilingan bo'ladi: nima yaratish kerak, qanday dalil qoldirish kerak, FAIL nima degani.

## 5. O'xshash mahsulotlar va ustunliklar

Claude Code subagentlari alohida kontekst, maxsus system prompt va cheklangan tool to'plami bilan ishlaydi; asosiy agent qisqa tavsifga qarab delegatsiya qiladi. OpenAI function calling'da tool tavsifi va sxemasi model kontekstiga kiradi, shuning uchun aniq tavsif va cheklangan son muhim. Anthropic "building effective agents" maqolasida evaluator-optimizer sikli va obyektiv ground truth asosiy sifat mexanizmi ekani aytiladi. Ustunlik: Conduit bu mexanizmlarni bitta `conduit` CLI orqali agy, claude, codex va opencode uchun universal qiladi. **TAKLIF** (foydalanuvchi tasdiqlamaguncha qo'shilmaydi): UI'da vazifa sifat balli va FAIL sabablari alohida ko'rinish.

## 6. Kiberxavfsizlik

Agent nomi faqat `cli_runner` tomonidan o'rnatilgan `CONDUIT_AGENT` orqali qabul qilinadi; yo'q bo'lsa tool rad etiladi. Tool chiqishi modelga ma'lumot sifatida qaytadi, lekin buyruq sifatida bajarilmaydi. Fayl yo'llari workspace ichida tekshiriladi, maxfiy kalitlar loglanmaydi, global foydalanuvchi config/auth/MCP sozlamalariga tegilmadi. Qayta urinishlar soni va vaqti cheklangan: sifat uchun degan bahona bilan cheksiz token sarflash yoki o'z-o'zini qayta chaqirish yo'q. OWASP Top 10 2025 asosiy xavfsizlik yo'nalishi sifatida olinadi; kiritilgan matn ishonchsiz deb hisoblanadi.

## 7. Tayyorlik mezonlari

`pytest backend/tests -q` yashil, shu jumladan bo'sh/eski/soxta dalil uchun FAIL va haqiqiy dalil uchun PASS testlari. Real vazifa terminal agent orqali bajarilib, Tasklar va jonli sahnda ko'rinadi, `conduit result` artefakt va sabablarni qaytaradi. `check_goal` hech qachon eski faylni yangi dalil deb qabul qilmaydi. FAIL sababi agentga va UI'ga aniq yetib boradi. `compileall`, `doctor`, `tsc`, `build`, `lint` 0; `gate.py verify OK`; o'zgarishlar faqat rejadagi fayllar. Tekshirilmagan narsalar hisobotda "tekshirilmadi" deb yoziladi.
