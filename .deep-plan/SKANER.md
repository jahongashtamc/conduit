# SKANER

Avtomatik faktlar `gate.py scan` dan. Pastdagi bo'limlarni agent o'zi kodni o'qib to'ldiradi.

<!-- AUTO:START -->
## Avtomatik faktlar

- Fayllar (skaner qilingan): 10270
- Tillar (fayl soni / qator): .ts 7287/2111624, .py 224/46322, .java 56/13953, .c 41/1375, .html 25/16449, .tsx 24/8817
- Manifest va sozlama fayllari: .gitignore, README.md, backend\requirements.txt, clones\rea\.gitignore, clones\rea\README.md, clones\rea\assets\README.md, clones\rea\docs\README.md, clones\rea\licenses\README.md, clones\rea\native\windows\README.md, clones\rea\package.json, clones\rea\scripts\verify-tools\skills\package.json, clones\rea\scripts\verify\advertised-schemas\requirements.txt, clones\rea\tests\conformance\README.md, clones\rea\tests\conformance\ghidra\README.md, clones\rea\tests\conformance\psp\Makefile, clones\rea\tests\conformance\readiness\electron\package.json, clones\rea\tests\conformance\readiness\javascript-cli\package.json, clones\rea\tests\fixtures\abiword\README.md, clones\rea\tests\fixtures\android\jni-bindings\README.md, clones\rea\tests\fixtures\android\r8-mapping\README.md, clones\rea\tests\fixtures\devicetree-reservations\README.md, clones\rea\tests\fixtures\elf-extended-symbols\README.md, clones\rea\tests\fixtures\elf-gnu-unique\README.md, clones\rea\tests\fixtures\elf-rel-addends\README.md, clones\rea\tests\fixtures\fit-producer\README.md, clones\rea\tests\fixtures\freecad\README.md, clones\rea\tests\fixtures\golden\README.md, clones\rea\tests\fixtures\graphql\README.md, clones\rea\tests\fixtures\inkscape\README.md, clones\rea\tests\fixtures\javascript-endpoint-capture\README.md, clones\rea\tests\fixtures\libreoffice-runs\README.md, clones\rea\tests\fixtures\libreoffice\README.md, clones\rea\tests\fixtures\lz4-distance\README.md, clones\rea\tests\fixtures\native-macos\archive-xml-encoding\README.md, clones\rea\tests\fixtures\native-macos\dyld-inventory\README.md, clones\rea\tests\fixtures\native-macos\lipo-same-cpu\README.md, clones\rea\tests\fixtures\native-macos\load-command-text-values\README.md, clones\rea\tests\fixtures\nativeaot-producer\README.md, clones\rea\tests\fixtures\openapi\README.md, clones\rea\tests\fixtures\pcap\README.md, clones\rea\tests\fixtures\pe-icon-producer\README.md, clones\rea\tests\fixtures\playwright-trace\README.md, clones\rea\tests\fixtures\protobuf-scalars\README.md, clones\rea\tests\fixtures\riscv-initializers\README.md, clones\rea\tests\fixtures\safetensors-producer\README.md, clones\rea\tests\fixtures\wasm\README.md, clones\rea\tests\support\analysis-efficiency\README.md, clones\rea\third_party\README.md, clones\rea\third_party\evmole\README.md, clones\rea\third_party\pwndbg\README.md, clones\rea\third_party\pwntools\README.md, clones\rea\third_party\wabt\README.md, clones\rea\third_party\web-network-captures\README.md, clones\rea\tsconfig.json, clones\rea\website\README.md, clones\rea\website\locales\README.md, clones\rea\website\public\examples\notes-electron\package.json, clones\rea\website\requirements.txt, frontend\package.json, frontend\tsconfig.json
- Kirish nuqtalari (taxminiy): backend\main.py, clones\rea\src\resources\index.ts, clones\rea\tests\conformance\readiness\electron\main.js, clones\rea\tests\conformance\readiness\javascript-cli\index.js, clones\rea\website\public\index.html, clones\rea\website\public\assets\main.js
- Eng katta fayllar: clones\rea\src\ghidra\GhidraProvider.behavior.test.ts (7642), clones\rea\bridge\ghidra\ReaGhidraBridge.java (6825), clones\rea\src\artifacts\ReleaseExposureReader.test.ts (6033), clones\rea\tests\boundary\providers\GdbSessionManagerCoverage.test.ts (4224), clones\rea\src\application\javascript\JavaScriptArtifactPathResolution.test.ts (3869)
- Test fayllari: 4738
- CI (.github/workflows): bor
- Git: oxirgi commit: a952da7 Merge four reported defect fixes; o'zgartirilgan fayllar: 19
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
  - jim except (xatoni yutadi): 42 ta, masalan conduit.py:54, conduit.py:367, conduit.py:501
  - shell=True / os.system: 6 ta, masalan .opencode\skills\webapp-testing\scripts\with_server.py:68, .opencode\skills\webapp-testing\scripts\with_server.py:71, backend\app_adapter.py:212
  - innerHTML / dangerouslySetInnerHTML: 1 ta, masalan frontend\src\components\Window1Terminal.tsx:130
<!-- AUTO:END -->

## 1. Tuzilma va asosiy oqim

Foydalanuvchi terminal/UI orqali vazifa yuboradi; `conduit.py` uni API ga uzatadi; `backend/main.py` task yaratadi va `kernel.py`/`cli_runner.py` orqali subagent ishga tushadi; `tools.py` va `app_adapter.py` haqiqiy artefakt yaratadi; `database.py` natija va loglarni saqlaydi; frontend ularni ko'rsatadi. Sifat shu zanjirning eng zaif halqasiga bog'liq.

## 2. Zaif va xavfli joylar

Avvalgi auditlarda eski dalil PASS, soxta figma va sun'iy video topilgan va tuzatilgan. Hozirgi xavf: test fixture'lari mahsulot xatosi deb o'qilishi, tashqi API 401 lari yashirinishi va foydalanuvchi ko'rgan muammoning aniq misoli yo'qligi. Shuning uchun faqat real E2E dalil asosida tuzatish kiritiladi.

## 3. Test va sifat holati

Oxirgi to'liq tekshiruv: `pytest backend/tests -q` 171 passed, 2 skipped; `doctor 0 FAIL`; `tsc/build/lint 0`; `gate.py verify OK`. Bu mexanik ko'rsatkichlar yaxshi, lekin foydalanuvchi hali ham real ish sifatidan norozi bo'lgani uchun ular yakuniy dalil hisoblanmaydi.

## 4. Bilmaydigan va tekshirilmagan joylar

E2E skripti natijasi hali kelmadi; qaysi vazifalar haqiqiy artefakt yaratishi va qayerda FAIL sababi noaniq ekani hali tasdiqlanmagan. Bundan tashqari eski papkadagi boshqa agent sessiyasi vaqtincha port 8000 ni egallab olgani uchun ba'zi loglar eski kodga tegishli bo'lishi mumkin; bu hisobga olinadi.
