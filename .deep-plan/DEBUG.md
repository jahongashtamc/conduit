# DEBUG

## 1. Video montaj sun'iy gradient ekani

Alomat: foydalanuvchi video montaj yomon deb aytdi; haqiqiy klip/kesish/audio o'rniga rangli gradient chiqar edi.
Ildiz sabab: `backend/tools.py::tool_video_render` kirish klip/audio olmay, task matnidan PIL gradient kadrlari yaratadi; `backend/engine/studio_pipeline.py` dagi haqiqiy media quvuri editor yo'liga ulanmagan.
Dalil: kod 695-782 qatorlarda tasodifiy gradient bor edi; `cli_runner.py:1173-1201` faqat `tool_video_render(task_goal, 3.0)` chaqirardi.
Tuzatish: kirish media bo'yicha FFmpeg trim/setpts/concat/atrim bilan haqiqiy montaj qilindi; kirish fayllari bo'lmasa aniq FAIL qaytariladi.
Tekshiruv: ikki lokal klip bilan real MP4 yaratildi va kirishsiz FAIL testi qo'shildi; `pytest` 171 passed.

## 2. DeepX 2-bosqichda osilib qolishi

Alomat: `repro-deepx-20261124` vazifasi 240 soniyadan keyin timeout berdi, 2-bosqich tugamadi.
Ildiz sabab: inspector/agy tool-call tsiklida qolib, `_execute_swarm_stage_with_healing` da bosqich uchun qattiq timeout yo'q edi; audit FAIL bo'lsa ham yakunda `Sertifikatlangan` yozilardi.
Dalil: DB loglari 240s davomida `[agent] tool bajarilmoqda...` qatorlarini takrorlagan; `kernel.py:924` hardcode matn bor edi.
Tuzatish: `asyncio.wait_for` bilan qattiq chegara, bitta self-heal, keyin halol FAIL va haqiqiy audit natijasi qo'yildi.
Tekshiruv: sekin bosqich mock testi timeoutni tasdiqladi; hardcode matn olib tashlandi; to'liq test yashil.

## 3. DeepSearch rejim va natija sifati

Alomat: foydalanuvchi deepsearch ishlamaydi va natijalar alaqasiz deb aytdi.
Ildiz sabab: `KernelMode` va settings validatsiyasida DEEPSEARCH yo'q edi; GitHub code search 401 qaytaradi, lekin xato yashirinadi; relevance faqat yulduz soniga asoslanadi.
Dalil: `POST /api/kernel/settings active_mode=deepsearch` rad etildi; 8 kandidat faqat local/npm manbalardan, github_code 401 va `grpc-web` tanlangan edi.
Tuzatish: DEEPSEARCH rejimi qo'shildi, source_errors ochiq ko'rsatiladi, so'z mosligi bo'yicha relevance joriy etildi va search-only pipeline yaratildi.
Tekshiruv: rejim, relevance va manba xatosi testlari o'tdi; real `POST /api/tools/deepsearch` 12 kandidat va 1 xato qaytardi.

## 4. Figma agenti hardcode ma'lumot qaytaradi

Alomat: foydalanuvchi Figma agenti talabga javob bermaydi deb aytdi.
Ildiz sabab: `app_adapter.get_figma_project_info` doimiy token/component/spec qaytaradi, `FIGMA_TOKEN` tekshirilmaydi, REST chaqiruvi yo'q edi.
Dalil: `tool_figma_sync` faqat berilgan file_key ni qaytaradi, qolgan ma'lumot hardcode edi; dizaynchi 3D shar bilan soxta preview yaratardi.
Tuzatish: token bo'lsa real Figma REST API chaqiriladi, bo'lmasa `needs_config`; preview faqat haqiqiy API ma'lumotidan yaratiladi.
Tekshiruv: mock REST testi haqiqiy token/componentlarni qaytardi; token yo'q holatda `needs_config` testi o'tdi.

## 5. Umumiy hisobot chiqmaydi

Alomat: foydalanuvchi "umumiy hisobotni ham topshira olmaydi" dedi.
Ildiz sabab: mission report API haqiqiy ID bilan ishlaydi, lekin DeepSearch/DeepX tadqiqot hisoboti faqat to'liq swarm tugaganda yoziladi; swarm osilib qolgani uchun `research/*.md` yaratilmaydi.
Dalil: `GET /api/tasks/test_heal_mission_dbe6e4/report?format=markdown` 200 va 2563 belgi qaytardi; `/api/research` da hisobot yo'q edi; `711` kabi ID mavjud emas edi.
Tuzatish: `run_deepsearch_pipeline` iqtiboslardan haqiqiy `research/*.md` yozadi va `report_path` qaytaradi; isbotlanmagan statik xavfsizlik da'volari olib tashlandi.
Tekshiruv: `test_deepsearch_report_file_created` va `test_report_lookup_works_with_real_string_id` o'tdi; real deepsearch `research/react_query.md` yaratdi.

## 6. Testlar yashil, lekin foydalanuvchi natijasi yomon edi

Alomat: oxirgi to'liq test 165 passed edi, lekin foydalanuvchi 4 ta muammoni aytdi.
Ildiz sabab: testlar mexanik holatni tekshiradi, natija mazmuni — haqiqiy video, real Figma, to'g'ri rejim va hisobot — ni tekshirmaydi.
Dalil: barcha 4 nuqson haqiqiy chaqiruv/kod o'qish bilan repro qilindi; yangi testlar ularni fosh qiladi.
Tuzatish: mazmunni tekshiradigan regression testlar qo'shildi; agent yo'riqnomasi ham natija shartnomasi bilan yangilandi.
Tekshiruv: to'liq `pytest backend/tests -q` 171 passed, 2 skipped; UI Playwright hisobot tab va matn mavjudligini tasdiqladi.
