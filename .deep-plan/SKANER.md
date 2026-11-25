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

`task_goal` → `app_adapter.parse_visual_spec()` → `build_scene_script_from_goal()` / `tools.tool_gen_image()` → `workspaces/*` artefaktlari → `backend/static/screenshots` → UI. Sifat shu zanjirning boshida hal qilinadi: agar talab parametrlari o'qilmasa, keyingi barcha qadamlar chiroyli, lekin noto'g'ri natija ishlab chiqaradi.

## 2. Zaif va xavfli joylar

Eski holatda `cli_runner` kub/sharni hardcoded yaratadi, `tool_gen_image` hash bilan tasodifiy grid chizadi, checker faqat fayl borligini tekshiradi. Bu tasdiqlangan: ochilgan artefaktlar umumiy kub, grid va testsrc edi. Endi barcha vizual yo'nalishlar bir xil spec dan o'qiladi; matn va rang lug'atga asoslanadi.

## 3. Test va sifat holati

`pytest backend/tests -q` → 186 passed, 2 skipped; yangi `test_visual_spec_quality.py` → 3 passed; `compileall 0`, `doctor 0 FAIL`, `tsc/build/lint 0`. Ko'z bilan tekshiruv: 2D `spec_image.png` va 3D `render_snapshot.png` talabga mos (rang, shakl, son, NEXUS yozuvi, tungi fon).

## 4. Bilmaydigan va tekshirilmagan joylar

Yangi tillardagi rang/shakl nomlari lug'atda yo'q; tashqi text-to-image modeli ishlatilmadi (ruxsat yo'q). Foydalanuvchi «yomon» degan eski natijalarning barcha skrinshotlari saqlanmagan; shuning uchun hozirgi tuzatish ochib ko'rilgan uchta asosiy artefaktga asoslangan. Global config/auth/MCP tegmadi.
