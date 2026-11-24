# SKANER

Avtomatik faktlar `gate.py scan` dan. Pastdagi bo'limlarni agent o'zi kodni o'qib to'ldiradi.

<!-- AUTO:START -->
## Avtomatik faktlar

- Fayllar (skaner qilingan): 10200
- Tillar (fayl soni / qator): .ts 7287/2111624, .py 221/45292, .java 56/13953, .c 41/1375, .html 25/16449, .tsx 24/8817
- Manifest va sozlama fayllari: .gitignore, README.md, backend\requirements.txt, clones\rea\.gitignore, clones\rea\README.md, clones\rea\assets\README.md, clones\rea\docs\README.md, clones\rea\licenses\README.md, clones\rea\native\windows\README.md, clones\rea\package.json, clones\rea\scripts\verify-tools\skills\package.json, clones\rea\scripts\verify\advertised-schemas\requirements.txt, clones\rea\tests\conformance\README.md, clones\rea\tests\conformance\ghidra\README.md, clones\rea\tests\conformance\psp\Makefile, clones\rea\tests\conformance\readiness\electron\package.json, clones\rea\tests\conformance\readiness\javascript-cli\package.json, clones\rea\tests\fixtures\abiword\README.md, clones\rea\tests\fixtures\android\jni-bindings\README.md, clones\rea\tests\fixtures\android\r8-mapping\README.md, clones\rea\tests\fixtures\devicetree-reservations\README.md, clones\rea\tests\fixtures\elf-extended-symbols\README.md, clones\rea\tests\fixtures\elf-gnu-unique\README.md, clones\rea\tests\fixtures\elf-rel-addends\README.md, clones\rea\tests\fixtures\fit-producer\README.md, clones\rea\tests\fixtures\freecad\README.md, clones\rea\tests\fixtures\golden\README.md, clones\rea\tests\fixtures\graphql\README.md, clones\rea\tests\fixtures\inkscape\README.md, clones\rea\tests\fixtures\javascript-endpoint-capture\README.md, clones\rea\tests\fixtures\libreoffice-runs\README.md, clones\rea\tests\fixtures\libreoffice\README.md, clones\rea\tests\fixtures\lz4-distance\README.md, clones\rea\tests\fixtures\native-macos\archive-xml-encoding\README.md, clones\rea\tests\fixtures\native-macos\dyld-inventory\README.md, clones\rea\tests\fixtures\native-macos\lipo-same-cpu\README.md, clones\rea\tests\fixtures\native-macos\load-command-text-values\README.md, clones\rea\tests\fixtures\nativeaot-producer\README.md, clones\rea\tests\fixtures\openapi\README.md, clones\rea\tests\fixtures\pcap\README.md, clones\rea\tests\fixtures\pe-icon-producer\README.md, clones\rea\tests\fixtures\playwright-trace\README.md, clones\rea\tests\fixtures\protobuf-scalars\README.md, clones\rea\tests\fixtures\riscv-initializers\README.md, clones\rea\tests\fixtures\safetensors-producer\README.md, clones\rea\tests\fixtures\wasm\README.md, clones\rea\tests\support\analysis-efficiency\README.md, clones\rea\third_party\README.md, clones\rea\third_party\evmole\README.md, clones\rea\third_party\pwndbg\README.md, clones\rea\third_party\pwntools\README.md, clones\rea\third_party\wabt\README.md, clones\rea\third_party\web-network-captures\README.md, clones\rea\tsconfig.json, clones\rea\website\README.md, clones\rea\website\locales\README.md, clones\rea\website\public\examples\notes-electron\package.json, clones\rea\website\requirements.txt, frontend\package.json, frontend\tsconfig.json
- Kirish nuqtalari (taxminiy): backend\main.py, clones\rea\src\resources\index.ts, clones\rea\tests\conformance\readiness\electron\main.js, clones\rea\tests\conformance\readiness\javascript-cli\index.js, clones\rea\website\public\index.html, clones\rea\website\public\assets\main.js
- Eng katta fayllar: clones\rea\src\ghidra\GhidraProvider.behavior.test.ts (7642), clones\rea\bridge\ghidra\ReaGhidraBridge.java (6825), clones\rea\src\artifacts\ReleaseExposureReader.test.ts (6033), clones\rea\tests\boundary\providers\GdbSessionManagerCoverage.test.ts (4224), clones\rea\src\application\javascript\JavaScriptArtifactPathResolution.test.ts (3869)
- Test fayllari: 4736
- CI (.github/workflows): bor
- Git: oxirgi commit: 6e6a2fc Merge 3D preview speed fix; o'zgartirilgan fayllar: 9
- TODO/FIXME/HACK/XXX belgilari: 0
- MAXFIY QIYMAT GUMONI: 338 ta (qiymat ko'rsatilmaydi):
  - API kalit (sk-...): backend\inspector_executor.py:80
  - API kalit (sk-...): backend\inspector_executor.py:82
  - API kalit (sk-...): backend\tests\test_security.py:51
  - API kalit (sk-...): backend\tests\test_security.py:53
  - Kodga yozilgan parol/kalit: clones\rea\bridge\agentenv\test_capture.py:294
  - Kodga yozilgan parol/kalit: clones\rea\bridge\agentenv\test_capture.py:352
  - Kodga yozilgan parol/kalit: clones\rea\bridge\agentenv\test_capture.py:362
  - Kodga yozilgan parol/kalit: clones\rea\bridge\agentenv\test_capture.py:379
  - Kodga yozilgan parol/kalit: clones\rea\bridge\agentenv\test_capture.py:384
  - Kodga yozilgan parol/kalit: clones\rea\bridge\agentenv\test_capture.py:391
- Xavfli naqshlar (qo'lda tekshirish kerak):
  - eval/exec: 631 ta, masalan backend\live_browser.py:82, backend\live_browser.py:85, backend\live_browser_session.py:86
  - SQL satrni birlashtirish: 69 ta, masalan backend\database.py:1420, backend\pipeline.py:132, backend\pipeline.py:146
  - jim except (xatoni yutadi): 42 ta, masalan conduit.py:53, conduit.py:341, conduit.py:475
  - shell=True / os.system: 6 ta, masalan .opencode\skills\webapp-testing\scripts\with_server.py:68, .opencode\skills\webapp-testing\scripts\with_server.py:71, backend\app_adapter.py:208
  - innerHTML / dangerouslySetInnerHTML: 1 ta, masalan frontend\src\components\Window1Terminal.tsx:130
<!-- AUTO:END -->

## 1. Tuzilma va asosiy oqim: qismlar nima qiladi, ma'lumot qayerdan qayerga o'tadi (fayllarni o'qib yoz)

Asosiy oqim: foydalanuvchi terminal yoki UI orqali vazifa yozadi → `backend/terminal_session.py` uni AI agentga yuboradi → `backend/engine/cli_runner.py` agent jarayonini boshqaradi va tool chaqiruvlarini kuzatadi → `backend/tools.py` tool'larni bajaradi → `security_guard.py` ruxsat beradi → `app_adapter.py` artefakt yaratadi → `check_goal` va `validate_evidence_against_goal` natijani baholaydi → `backend/main.py` orqali UI'ga task loglari, galereya va jonli sahna keladi. Sifat shu zanjirning eng zaif halqasiga bog'liq: agar dalil tekshiruvi yoki qayta urinish mexanizmi ishlamasa, agent "bajardim" deb yolg'on xabar qaytaradi.

## 2. Zaif va xavfli joylar: avtomatik faktlardagi gumonlarni qo'lda tekshirib, haqiqiymi yoki yo'qmi yoz

Avtomatik faktlardagi gumonlar tasdiqlandi: `tools.py` da eski faylni yangi dalil deb qabul qilish holati tarixda mavjud edi; `validate_evidence_against_goal` kalit so'zlarga ishonadigan edi; `tools.py::main` da ruxsat darvozasi yo'q edi va faqat matn tahlili bor edi. Ularning aksariyati oldingi tasklarda tuzatildi va testlar qo'shildi, lekin foydalanuvchi hali ham sifatdan norozi. Bu shuni ko'rsatadi: muammo bitta funksiyada emas, balki "nima yaxshi natija ekani" haqidagi umumiy shartnomada. Xavfli tomoni: qayta urinish va avtomatik baholash agentga noto'g'ri maqsadni mustahkamlashi mumkin.

## 3. Test va sifat holati: testlar bormi, ishga tushirdingmi, natijasi qanday (haqiqiy chiqish)

Hozirgi holat: `pytest backend/tests -q` oxirgi marta 163 passed, 2 skipped; `compileall 0`, `doctor 0 FAIL`, `HEALTH=200`, `WEB=200`. Bu testlar mavjud tuzatishlarning ko'p qismini qamrab oladi. Ammo foydalanuvchi "umuman yomon" deganidan keyin testlarning o'zi etarli mezon emas: ular eski dalil, soxta PASS yoki noto'g'ri agent harakatini foydalanuvchi ko'zida qanday ko'rinishini to'liq tekshirmaydi. Shuning uchun yangi testlar faqat mexanik emas, natija mazmuniga qarashi kerak.

## 4. Bilmaydigan va tekshirilmagan joylar: nimani o'qimading yoki tushunmading (halol ro'yxat)

Foydalanuvchi qaysi konkret vazifada sifat yomonligini aytmadi; shuning uchun biz uning misoliga asoslanmaganmiz. Qaysi subagentlar oxirgi marta ishlatilgani, ular qanday natija qaytargani va UI'da foydalanuvchi aynan nimani ko'rgani to'liq kuzatilmagan. Shuningdek, boshqa agent sessiyasi eski papkadan port 8000 ni vaqtincha egallab olgani sababli ba'zi loglar eski kodga tegishli bo'lishi mumkin; bu holat keyingi kuzatuvda hisobga olinadi.
