# REJA

## 1. Sifat mezonlari xaritasi va zaif joylarni tasdiqlash

Nima qilinadi va qaysi fayllar: `backend/tools.py`, `backend/engine/cli_runner.py`, `subagents/*/role.md`, `backend/tests/*` ni o'qib, har vazifa turi uchun "haqiqiy dalil nima" mezonlarini `.deep-plan/DEBUG.md` va test nomlarida qayd etish. Eski dalil PASS, kalit so'z validator va ruxsat zaifliklarini qayta hujjatlashtirish.

Tugash sharti: kamida 3 ta aniq zaiflik dalil bilan yozilgan; har biri uchun qaysi test yoki buyruq uni fosh qilishi ko'rsatilgan; foydalanuvchining "yomon ish" shikoyati bitta o'zgarishga emas, butun zanjirga bog'lab tushuntirilgan.

Eng sodda variant: yangi fayl yaratmay, mavjud DEBUG.md ga 3 bo'lim qo'shish va mos test nomlarini ro'yxatlash.

## 2. Fail-closed dalil va obyektiv qabul mezonlari

Nima qilinadi va qaysi fayllar: `backend/tools.py::tool_check_goal`, `backend/engine/cli_runner.py::validate_evidence_against_goal` va ularga tegishli testlar. Bo'sh, eski yoki faqat matndan iborat dalil FAIL bo'lishi; artefakt yo'li, mtime, bayt hajmi va tur asosida tekshirish; FAIL sababi natijada aniq ko'rinishi.

Tugash sharti: eski `latest.png` bilan FAIL, yangi yaratilgan PNG bilan PASS, bo'sh dalil bilan FAIL; barcha sabablar ingliz/uzbek tilida tushunarli. `pytest backend/tests -q` yashil.

Eng sodda variant: mavjud `_fresh_evidence_issue` va `_evidence_artifacts` funksiyalarini kengaytirish, yangi kutubxona qo'shmaslik.

## 3. Cheklangan evaluator-optimizer qayta urinishi

Nima qilinadi va qaysi fayllar: `backend/engine/cli_runner.py` da FAIL sababini agentga qaytarish, eng ko'pi 2 marta qayta urinish, har urinishni `backend/database.py` loglari orqali ko'rinadigan qilish; testlarda chegara va xato holatlari.

Tugash sharti: mezon bajarilmaganda agent aniq sabab oladi; qayta urinishlar soni 2 dan oshmaydi; loglarda har urinish ko'rinadi; hech qanday cheksiz sikl yoki yashirin xato yutish yo'q.

Eng sodda variant: mavjud agent loop ichida bitta qo'shimcha xabar va hisoblagich; yangi orkestrator yo'q.

## 4. Agent yo'riqnomasi, UI halolligi va yakuniy tekshiruv

Nima qilinadi va qaysi fayllar: `backend/terminal_session.py` orqali AGENTS/CLAUDE/GEMINI ga "natija shartnomasi" qo'shish; `frontend` da FAIL sababini ko'rsatish (agar mavjud tuzilma bunga imkon bersa, aks holda hisobot darajasida qoldirish); `.deep-plan/TEST.md`, `DECISIONS.md`, `.agents/time-log.md` yangilash.

Tugash sharti: yaratilgan yo'riqnomada dalil va FAIL shartlari bor; UI yoki hisobotda PASS/FAIL sababi aniq; `doctor`, `compileall`, `tsc`, `build`, `gate.py verify` 0/OK; git toza va faqat rejadagi faylar o'zgargan.

Eng sodda variant: yo'riqnomaga 6-8 qatorlik shartnoma qo'shish; UI o'zgarishi faqat sabab matnini ko'rsatish bilan cheklanadi.

TASDIQ: HA
