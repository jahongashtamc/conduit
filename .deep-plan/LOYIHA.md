# LOYIHA

## 1. MVP talablari nima?

Foydalanuvchi aniq 4 ta nuqsanni aytdi: video montaj sifatsiz, deepx/deepsearch ishlamaydi, Figma agenti talabga javob bermaydi, umumiy hisobot topshirib bo'lmaydi. Repro natijalari: `tool_video_render` task matnidan sun'iy gradient yaratadi, kirish klipi/kesim/audio yo'q; `POST /api/kernel/settings active_mode=deepsearch` rad etiladi; `run_deepx_pipeline` 240s dan keyin 2-bosqichda osilib qoladi va yakunda `Sertifikatlangan` deb yozadi; `get_figma_project_info` hardcode ma'lumot qaytaradi; `GET /api/tasks/711/report` `Vazifa topilmadi` deydi. MVP: shu 4 zanjirni kod darajasida tuzatish, haqiqiy artefakt/API/DB tekshiruvi va regressiya testlari.

## 2. Foydalanuvchi aynan nimani xohlayapti va qanday ishlashi kerak?

Foydalanuvchi: `video mantaj qila olish sust deepx va deepsearch rejimlari ishlamayapti figma agenti ham umuman talab ga javob bermaydi umumiy hisobot ni ham topshira olmaydi eng yomoni esa juda yomon ishlayapti`. U shunchaki agentga "yaxshiroq ishla" deb yozishni emas, kod va studiya ishini tuzatishni xohlayapti. Kutilayotgan oqim: berilgan klip/audio bo'lsa haqiqiy montaj MP4 chiqadi; deepx va deepsearch tanlanadi va tugaydi yoki aniq FAIL beradi; Figma agenti haqiqiy token/fayl bo'lsa real ma'lumot oladi, bo'lmasa `needs_config` deydi; hisobot har qanday mavjud vazifa ID si uchun ochiladi.

## 3. Qismlar, oqim va eng kichik ishlaydigan qism

Oqim: `main.py` API/mode/setting → `engine/kernel.py` rejim va swarm → `engine/cli_runner.py` subagent → `tools.py` (video/figma/report dalili) → `app_adapter.py`/FFmpeg/Figma REST → DB va `report_generator.py` → frontend. Eng kichik ishlaydigan qism: bitta real klip bilan montaj MP4; bitta deepsearch so'rovi natijasi; bitta Figma `needs_config` javobi; bitta raqamli vazifa ID si bilan hisobot. Bu to'rttasi ishlamagunicha umumiy xabar yozish foydasiz.

## 4. Har funksiya uchun eng qisqa to'g'ri yechim

Yangi framework yo'q: video uchun mavjud FFmpeg va `shutil.which` ustiga real `concat`/`trim`/`atrim` asosida kesish va birlashtirish; kirish fayl bo'lmasa PASS emas, aniq xato. Deepx uchun `asyncio.wait_for` bilan bosqich chegarasi, bitta self-heal, keyin halol FAIL; deepsearch uchun `KernelMode.DEEPSEARCH` va unga alohida yo'nalish; GitHub 401 bo'lsa manba "mavjud emas" deb ko'rsatiladi. Figma uchun `FIGMA_TOKEN` va fayl kaliti bo'lsa REST API, aks holda hech qanday hardcode ma'lumot yo'q. Hisobot uchun raqamli ID `int` ga o'tkazilib so'raladi.

## 5. O'xshash mahsulotlar va ustunliklar

FFmpeg professional kesish/timeline/audio imkoniyatini beradi; Figma REST haqiqiy fayl va komponent ma'lumotlarini token orqali beradi; GitHub code search autentifikatsiya talab qiladi. Ustunlik: Conduit ularni bitta agent studiyasiga bog'laydi, lekin **TAKLIF** sifatida: qo'shimcha video effektlari yoki bulutli Figma integratsiyasi faqat foydalanuvchi tasdiqlagach qo'shiladi.

## 6. Kiberxavfsizlik

Figma/GitHub tokenlari faqat muhit o'zgaruvchisidan o'qiladi, loglarga yozilmaydi va global config/auth/MCP o'zgartirilmaydi. Video kirish yo'llari workspace ichida tekshiriladi; tashqi URL faqat aniq ruxsat bilan. DeepSearch xato kodlari yutulmaydi, 401/403 holati natijada ko'rinadi. Barcha FAIL sabablari DB log va hisobotda aniq qoladi.

## 7. Tayyorlik mezonlari

Haqiqiy kirish klipi bilan yaratilgan MP4 mavjud va kesimlar soni hisobotda bor; deepx 60s ichida tugaydi yoki aniq FAIL beradi va hech qachon `Sertifikatlangan` deb yolg'on yozmaydi; `deepsearch` rejimi taniladi; Figma token yo'q bo'lsa `needs_config`, bor bo'lsa REST orqali real ma'lumot; `GET /api/tasks/711/report` mavjud vazifa uchun haqiqiy hisobot qaytaradi; `pytest backend/tests -q`, `compileall`, `doctor`, `tsc`, `build`, `gate.py verify` yashil; git toza.
