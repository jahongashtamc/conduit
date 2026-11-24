# TEST

## 1. Ishga tushirish / build

Natija: O'TDI. `python -m pytest backend/tests -q` → `180 passed, 2 skipped, 4 warnings in 247.73s`, `FULL=0`. `python -m compileall -q backend conduit.py` → `0`. `python conduit.py doctor` → `0 FAIL`, `Zarur hamma narsa tayyor` (faqat ixtiyoriy token WARN). Frontend `npx tsc --noEmit` → `0`, `npm run build` → `0`, `npm run lint` → `0` (2 oldingi ESLint warning). Backend asosiy repodan qayta ishga tushirildi: `/health=200`, `WEB=200`.

## 2. Asosiy funksiyalar

Natija: O'TDI. `python tools.py run_process` + `python tools.py get_logs <pid>` ikki alohida jarayonda ishladi: `REAL_LOG True [stdout] CLI_LOG_OK`. `conduit list --json` → `LIST_JSON_OK True` (ANSI banner yo'q). `conduit status no_such_task --json` → JSON `success:false, http_status:404, error:"Task not found"`. `conduit run no_such_agent test --json` → JSON `success:false, http_status:400` va amaldagi agentlar ro'yxati. Editor vazifasi `task_7ea2f7f7` ikki haqiqiy FFmpeg klipi bilan PASS: `montage.mp4`, 48 kadr, 24 fps, 48840 bayt; preview yangi mtime bilan yangilandi. Figma tokensiz vazifa `task_946afe7d` halol FAIL qaytardi.

## 3. Chegara va xato holatlari

Natija: O'TDI. `no_such_task` va `no_such_agent` xatolari JSON ko'rinishida qaytariladi; noma'lum jarayon uchun `get_logs` `Jarayon topilmadi` bilan `success:false`; klipsiz video FAIL; Figma token/file key bo'lmasa `needs_config`; E2E skriptining noto'g'ri status parsingi tuzatildi (vazifalar aslida PASS edi). `test_no_silent_except` qayta o'tdi: barcha `pass` o'rniga log qo'yildi.

## 4. Xavfsizlik tekshiruvi

Natija: O'TDI. `generate_task_html_report` endi `html.escape()` bilan task matni, loglar va ID ni chiqaradi; `test_html_report_escapes_untrusted_task_text` `<script>` va `<img onerror>` ni qochirilganligini tasdiqladi. Noma'lum agent yaratilishi oldi olindi: 400 va xato xabarida faqat amaldagi agentlar. Global config/auth/MCP o'zgartirilmadi; maxfiy tokenlar loglanmadi.

## 5. Regressiya

Natija: O'TDI. Oldingi 171 passed/2 skipped natijasi 180 passed/2 skipped gacha kengaydi, hech qanday eski test buzilmadi. `test_five_hour_findings.py` va `test_tool_gate_hardening.py` alohida 20 passed berdi. Video, Figma, report va kernel testlari ham o'tdi.

## 6. Qo'lda ko'rish / jonlilik

Natija: O'TDI. Playwright UI audit: `BODY_LEN 5487`, `HAS_REPORT True`, `GAPS={'x':0,'y':0}`, konsol xatosi/ogohlantirishi yo'q. `/api/artifacts` 200 ta artefakt qaytardi; `editor_preview.png` va `latest.png` 101352 bayt, yangi mtime bilan. Oldingi ko'rinishdagi bo'sh chetlar va eski preview muammosi takrorlanmadi.

## 7. Tekshirilmaganlar

Natija: TEKSHIRILMADI (sababi aniq). Haqiqiy Figma tokeni/file keyi va foydalanuvchining shaxsiy video kliplari yo'q; ular mock REST va lokal FFmpeg testsrc klip bilan qoplandi. GitHub code search 401 holati haqiqiy, lekin muallifli token bilan qidiruv sinov qilinmadi. 5 soatlik vaqt oxirigacha faol kuzatuv davom etadi; bu hisobot hozirgacha olingan dalillarni aks ettiradi.
