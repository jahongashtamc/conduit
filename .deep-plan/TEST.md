# TEST

## 1. Ishga tushirish / build

Natija: O'TDI — 2026-11-24 19:53–19:58 da haqiqiy chiqish: `python -m pytest backend/tests -q` → `165 passed, 2 skipped, 5 warnings in 249.20s`, `PYTEST=0`. `python -m compileall -q backend` → `COMPILE=0`. `python conduit.py doctor` → `DOCTOR=0`, `Zarur hamma narsa tayyor`, faqat 3 ixtiyoriy token WARN. Frontend: `npx tsc --noEmit` → `TSC=0`, `npm run build` → `BUILD=0`, `npm run lint` → `LINT=0` (ikki ESLint ogohlantirishi bor, chiqish kodi 0).

## 2. Asosiy funksiyalar

Natija: O'TDI — `validate_evidence_against_goal` endi mavjud bo'lmagan yo'lni rad etadi va haqiqiy fayl bilan PASS qaytaradi (test: `test_evidence_validator_requires_artifact_not_keywords`, `test_evidence_validation_accepts_valid_domain_evidence`). `goal_check_passed` faqat aniq `verdict == PASS` ni qabul qiladi; `success:true` + uzun matn PASS emas (test: `test_goal_check_pass_requires_explicit_verdict`). Non-visual va inspector branch'lari shu helper orqali tekshiradi.

## 3. Chegara va xato holatlari

Natija: O'TDI — bo'sh dalil (`test_check_goal_rejects_empty_evidence`), eski mtime (`test_check_goal_rejects_stale_artifact`), mavjud bo'lmagan artefakt yo'li, Figma uchun localhost skrinshot rad etilishi, va retry chegarasi (`test_retry_budget_is_bounded`) sinovdan o'tkazildi. Har FAIL holatida sabab natijada aniq matn sifatida mavjud.

## 4. Xavfsizlik tekshiruvi

Natija: O'TDI — `CONDUIT_AGENT` env orqali ruxsat darvozasi oldingi bosqichda qo'shilgan va testlangan (`CONDUIT_AGENT=scout python tools.py gen_image` → exit 2). Ushbu o'zgarishda yangi maxfiy qiymat yo'q; `gate.py scan` qayta ishga tushirildi; global config/auth/MCP o'zgartirilmadi. Tool chiqishi buyruq sifatida bajarilmaydi, artefakt faqat ma'lumot sifatida o'qiladi.

## 5. Regressiya

Natija: O'TDI — oldingi 163 ta backend testi saqlanib qoldi; 2 ta test fixture haqiqiy fayl ishlatadigan qilib yangilandi, 3 ta yangi test qo'shildi. To'liq natija: `165 passed, 2 skipped`. EEPX dual-verify testi qattiq artefakt tekshiruviga moslashtirildi (`test_eepx_pipeline_execution` yashil).

## 6. Qo'lda ko'rish / jonlilik

Natija: TEKSHIRILMADI — ushbu bosqichda UI kodi o'zgartirilmadi; FAIL sababi allaqachon `evidence_str = f"FAIL (sabab: {fail_reason})"` orqali natija va loglarga yoziladi. Terminal yo'riqnomasi v6 qayta generatsiya qilindi: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` va 16 ta native subagent definitsiyasida "Natija shartnomasi" borligi `grep` bilan tasdiqlangan. Real brauzer skrinshoti olinmadi; bu halol cheklov.

## 7. Tekshirilmaganlar

Natija: TEKSHIRILMADI — foydalanuvchi konkret "yomon natija" misolini bermagani uchun uning shaxsiy kuzatuvi bilan solishtirib bo'lmadi. 7 ixtiyoriy CLI va Notion/Slack/GitHub tokenlari yo'q. Boshqa agent sessiyasi eski `C:\Users\Kapitan\conduit` dan port 8000 ni vaqtincha egallashi mumkin; foydalanuvchi ruxsatisiz u sessiya o'chirilmadi. Ushbu vazifa doirasida UI dizayni o'zgartirilmadi.
