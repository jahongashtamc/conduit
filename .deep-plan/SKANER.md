# SKANER

Avtomatik faktlar `gate.py scan` dan. Pastdagi bo'limlarni agent o'zi kodni o'qib to'ldiradi.

<!-- AUTO:START -->
## Avtomatik faktlar

- Fayllar (skaner qilingan): 10153
- Tillar (fayl soni / qator): .ts 7287/2111624, .py 219/45152, .java 56/13953, .c 41/1375, .html 25/16449, .tsx 24/8817
- Manifest va sozlama fayllari: .gitignore, README.md, backend\requirements.txt, clones\rea\.gitignore, clones\rea\README.md, clones\rea\assets\README.md, clones\rea\docs\README.md, clones\rea\licenses\README.md, clones\rea\native\windows\README.md, clones\rea\package.json, clones\rea\scripts\verify-tools\skills\package.json, clones\rea\scripts\verify\advertised-schemas\requirements.txt, clones\rea\tests\conformance\README.md, clones\rea\tests\conformance\ghidra\README.md, clones\rea\tests\conformance\psp\Makefile, clones\rea\tests\conformance\readiness\electron\package.json, clones\rea\tests\conformance\readiness\javascript-cli\package.json, clones\rea\tests\fixtures\abiword\README.md, clones\rea\tests\fixtures\android\jni-bindings\README.md, clones\rea\tests\fixtures\android\r8-mapping\README.md, clones\rea\tests\fixtures\devicetree-reservations\README.md, clones\rea\tests\fixtures\elf-extended-symbols\README.md, clones\rea\tests\fixtures\elf-gnu-unique\README.md, clones\rea\tests\fixtures\elf-rel-addends\README.md, clones\rea\tests\fixtures\fit-producer\README.md, clones\rea\tests\fixtures\freecad\README.md, clones\rea\tests\fixtures\golden\README.md, clones\rea\tests\fixtures\graphql\README.md, clones\rea\tests\fixtures\inkscape\README.md, clones\rea\tests\fixtures\javascript-endpoint-capture\README.md, clones\rea\tests\fixtures\libreoffice-runs\README.md, clones\rea\tests\fixtures\libreoffice\README.md, clones\rea\tests\fixtures\lz4-distance\README.md, clones\rea\tests\fixtures\native-macos\archive-xml-encoding\README.md, clones\rea\tests\fixtures\native-macos\dyld-inventory\README.md, clones\rea\tests\fixtures\native-macos\lipo-same-cpu\README.md, clones\rea\tests\fixtures\native-macos\load-command-text-values\README.md, clones\rea\tests\fixtures\nativeaot-producer\README.md, clones\rea\tests\fixtures\openapi\README.md, clones\rea\tests\fixtures\pcap\README.md, clones\rea\tests\fixtures\pe-icon-producer\README.md, clones\rea\tests\fixtures\playwright-trace\README.md, clones\rea\tests\fixtures\protobuf-scalars\README.md, clones\rea\tests\fixtures\riscv-initializers\README.md, clones\rea\tests\fixtures\safetensors-producer\README.md, clones\rea\tests\fixtures\wasm\README.md, clones\rea\tests\support\analysis-efficiency\README.md, clones\rea\third_party\README.md, clones\rea\third_party\evmole\README.md, clones\rea\third_party\pwndbg\README.md, clones\rea\third_party\pwntools\README.md, clones\rea\third_party\wabt\README.md, clones\rea\third_party\web-network-captures\README.md, clones\rea\tsconfig.json, clones\rea\website\README.md, clones\rea\website\locales\README.md, clones\rea\website\public\examples\notes-electron\package.json, clones\rea\website\requirements.txt, frontend\package.json, frontend\tsconfig.json
- Kirish nuqtalari (taxminiy): backend\main.py, clones\rea\src\resources\index.ts, clones\rea\tests\conformance\readiness\electron\main.js, clones\rea\tests\conformance\readiness\javascript-cli\index.js, clones\rea\website\public\index.html, clones\rea\website\public\assets\main.js
- Eng katta fayllar: clones\rea\src\ghidra\GhidraProvider.behavior.test.ts (7642), clones\rea\bridge\ghidra\ReaGhidraBridge.java (6825), clones\rea\src\artifacts\ReleaseExposureReader.test.ts (6033), clones\rea\tests\boundary\providers\GdbSessionManagerCoverage.test.ts (4224), clones\rea\src\application\javascript\JavaScriptArtifactPathResolution.test.ts (3869)
- Test fayllari: 4735
- CI (.github/workflows): bor
- Git: oxirgi commit: 3b364c7 Merge remote-tracking branch 'origin/main'; o'zgartirilgan fayllar: 19
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
  - shell=True / os.system: 6 ta, masalan .opencode\skills\webapp-testing\scripts\with_server.py:68, .opencode\skills\webapp-testing\scripts\with_server.py:71, backend\app_adapter.py:139
  - innerHTML / dangerouslySetInnerHTML: 1 ta, masalan frontend\src\components\Window1Terminal.tsx:130
<!-- AUTO:END -->


## 1. Tuzilma va asosiy oqim

`subagents/*/role.md` har bir subagent uchun tool ro'yxatini e'lon qiladi; `backend/security_guard.py::get_allowed_tools()` ularni o'qiydi; `backend/tool_registry.py` 16 ta `conduit_run_*` tool'ni katalog qiladi; `backend/engine/cli_runner.py` asosiy agentga ko'rsatma yuboradi va subagent CLI'ni ishga tushiradi; `backend/tools.py` tool chaqiruvlarini bajaradi va `check_goal` orqali dalilni baholaydi; natija `backend/main.py` WS/API orqali frontend'ga yetadi. Muammo: ro'yxatlar alohida yuritiladi, `tools.py` da ruxsat tekshiruvi yo'q, `check_goal` eski faylni yangi dalil deb qabul qiladi.

## 2. Zaif va xavfli joylar

Haqiqiy yugurish bilan tasdiqlandi: `python tools.py check_goal 'Create a 3D model' '{}'` → `verdict: PASS`, `success: true`, `visual_captured: true`, lekin dalil sifatida eski `backend/static/screenshots/latest.png` ko'rsatilgan. `tools.py::tool_check_goal` 297-310-qatorlarda `test_screenshot.png`, `screenshot.png`, `latest.png` ga jim fallback qiladi. `tools.py::main` 856-939-qatorlarda `verify_tool_access` chaqirilmaydi; faqat `cli_runner` 683-698-qatorlarda matndan `python tools.py` qidiradi. `web_search` `inst_web` rolidа bor, lekin CLI yordamida yo'q. Skanerdagi `sk-...` gumonlari test fixture'lari; 42 ta jim except va 6 ta shell=True asosan klonlangan `clones/rea` va eski skriptlarda, yangi o'zgarish ularni ishlatmaydi.

## 3. Test va sifat holati

Oldingi vazifada `pytest backend/tests -q` → `151 passed, 2 skipped`; `compileall`, `doctor`, `tsc`, `lint`, `build` 0; API/WEB 200. Ammo `test_tool_coverage.py` faqat qattiq kodlangan `IMPLEMENTED_TOOLS` to'plamini tekshiradi, CLI'da haqiqatan bajarilishini emas; `test_cli_runner.py:43-60` esa aniq yo'q screenshot FAIL va haqiqiy PNG PASS ekanligini talab qiladi — bu kontrakt saqlanadi. Yangi testlar qo'shilmaguncha sifat holati "yashil, lekin asosiy muammoni qamrab olmaydi".

## 4. Bilmaydigan va tekshirilmagan joylar

16 ta subagentning barchasi bilan real uzoq ish sinab ko'rilmadi; faqat ularning e'lon qilingan tool ro'yxatlari solishtirildi. `check_goal` plugin yo'li `C:\Users\user\agent-studio-plugin\src` mavjud emas, Node fallback ishlatiladi — uning ichki logikasi to'liq o'qilmadi, lekin tashqi natija dalil bilan tasdiqlandi. Boshqa AI CLI'larning native tool chaqiruvlari (agy/codex/opencode) to'liq sinab ko'rilmadi; shuning uchun ruxsat darvozasi ichki `tools.py` ga qo'yiladi. Global auth/MCP sozlamalari o'zgartirilmadi va sinab ko'rilmadi.
