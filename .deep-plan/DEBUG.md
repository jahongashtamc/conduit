# DEBUG

## 1. Eski dalil yangi natija deb qabul qilingan

Alomat: foydalanuvchi agent ishini yomon deb baholadi; avvalgi auditda `check_goal` eski `latest.png` bilan ham `verdict: PASS` qaytargani qayd etilgan.
Ildiz sabab: dalil sifatida `test_screenshot.png`, `screenshot.png` va `backend/static/screenshots/latest.png` ga zaxira qarab, ularning shu vazifaga tegishliligi tekshirilmagan.
Dalil: oldingi haqiqiy chaqiruv `python tools.py check_goal 'Create a 3D model' '{}'` natijasida PASS va eski fayl ko'rsatilgan; keyingi tuzatishdan so'ng xuddi shunday holat FAIL bo'ldi.
Tuzatish: faqat `captured_at` yoki fayl mtime asosida vazifa boshlanganidan keyin yaratilgan dalil qabul qilinadi.
Tekshiruv: `backend/tests/test_tool_gate_hardening.py` va real stale-evidence skripti FAIL natijasini ko'rsatdi.

## 2. Kalit so'zga asoslangan sifat bahosi

Alomat: "render model scene" kabi matn bor ekan, 3D vazifa uchun dalil yetarli deb hisoblangan.
Ildiz sabab: `validate_evidence_against_goal` matndagi so'zlarga qarab ishlagan, artefakt obyekti va uning xususiyatlarini talab qilmagan.
Dalil: oldingi test `validate_evidence_against_goal(... 'render model scene', '')` endi False qaytaradi; bu o'zgarishdan oldin u True edi.
Tuzatish: artefakt obyektlari, yo'l, mtime va bayt hajmi tekshiriladi; `goal_check_passed` faqat aniq `verdict == PASS` ni qabul qiladi.
Tekshiruv: yangi hardening testlari va `pytest backend/tests -q` yashil (165 passed, 2 skipped).

## 3. Ruxsat va dalil o'rtasidagi uzilish

Alomat: tool katalogi va ruxsat ro'yxatlari mavjud bo'lsa ham, agent noto'g'ri yoki ruxsat etilmagan tool'ni chaqirishi mumkin edi.
Ildiz sabab: `tools.py::main` ruxsatni bajarish vaqtida tekshirmagan, faqat `cli_runner` matn tahliliga tayanardi.
Dalil: `CONDUIT_AGENT=scout python tools.py gen_image 'deneme'` endi `XAVFSIZLIK TO'SIG'I` bilan exit 2 beradi.
Tuzatish: env orqali agent nomi uzatilib, har chaqiruvda `verify_tool_access` chaqiriladi.
Tekshiruv: ruxsat testi va to'liq backend test to'plami o'tdi.

## 4. Sifat shartnomasi yo'qligi

Alomat: foydalanuvchi "yomon ish" deydi, lekin qaysi mezon buzilganini na agent, na UI aniq aytadi.
Ildiz sabab: `cli_runner.py` da `goal_check.verdict == "PASS" or doer_out_summary` sharti tufayli `check_goal` FAIL bo'lsa ham ixtiyoriy matn bilan PASS chiqariladi; inspector `success` ni `verdict` o'rniga ishlatadi; validator faqat yo'l matnini oladi, fayl mavjudligi/hajmi tekshirilmaydi.
Dalil: kodning mos qatorlari va foydalanuvchi shikoyati; 2026-11-24 19:39:57 da reja tasdiqlandi.
Tuzatish: bitta natija shartnomasi, fail-closed artefakt tekshiruvi, FAIL sababini keyingi urinishga uzatish (1+2 retry), agent yo'riqnomasi v6.
Tekshiruv: `test_goal_check_pass_requires_explicit_verdict`, `test_retry_budget_is_bounded` va to'liq test to'plami yashil; grep yo'riqnomada shartnoma borligini tasdiqladi.

## 5. Qattiq artefakt tekshiruvi eski test fixturasini fosh qildi

Alomat: to'liq test to'plamida `test_kernel_eepx_superagent.py::test_eepx_pipeline_execution` FAIL berdi (`1 failed, 163 passed, 2 skipped`).
Ildiz sabab: test mok-evidensiyasida `workspaces/scout/screenshot.png` degan mavjud bo'lmagan yo'l ishlatilgan; yangi `_artifact_is_real` uni to'g'ri rad etgan, mahsulot xatosi emas.
Dalil: EEPX dual-verify FAIL qaytgan; `tmp_path` bilan haqiqiy PNG yozilgach test yashil bo'ldi.
Tuzatish: fixture haqiqiy fayl yaratadigan qilib o'zgartirildi; `goal_check_passed()` ajratilib faqat aniq PASS ni qabul qiladi.
Tekshiruv: `23 passed` (targeted), keyin to'liq `pytest backend/tests -q` → `165 passed, 2 skipped, 5 warnings`, `PYTEST=0`.
