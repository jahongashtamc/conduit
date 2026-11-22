# NEXUS (Conduit) — 4 soatlik yakuniy ish rejasi

Maqsad: studiyani universal AI-agent platformasi sifatida to'liq tasdiqlash, qolgan kamchiliklarni
tuzatish va har bosqichni dalil bilan yopish. Savol yo'q; noaniq joylarda eng oddiy va to'g'ri
variant tanlanadi, qaror `DECISIONS.md` ga yoziladi.

## Bosqich 0 — 0:00–0:15 · Holatni qotirish
- [x] Git holati, build, xizmatlar, asosiy nusxa (Documents) tasdiqlandi.
- [ ] `conduit doctor` 0 FAIL.
- [ ] To'liq `pytest` (ignore'siz) yashil.
- **Dalil:** doctor chiqishi, pytest summary.

## Bosqich 1 — 0:15–1:00 · Poydevor va muhit
- [ ] Desktop yorlig'i (shortcut) to'g'ri papkaga ishora qilishini tekshirish/tuzatish.
- [ ] Eski nusxa (`C:\Users\Kapitan\conduit`) bilan aralashmaslik qarori tasdiqlandi (o'chirilmaydi).
- [ ] `tools.py` dublikati yo'qligi, workspace stub 596 bayt ekanligi.
- [ ] FFmpeg/Blender/CLI mavjudligi, requirements to'liqligi.
- **Dalil:** `doctor`, `git status`, stub hashlari, yo'riqnoma.

## Bosqich 2 — 1:00–1:50 · Universal agent qatlami
- [ ] 13 ta agent ro'yxati API va kirish modalida ko'rinadi (tasdiqlangan).
- [ ] `AGENTS.md/CLAUDE.md/GEMINI.md` avto-generatsiyasi va `CONDUIT_API/SESSION`.
- [ ] agy uchun MCP yuklanishini kamaytirish: izolyatsiyalangan config/HOME sinovi.
- [ ] Terminaldan `conduit run` → bitta task_id → `status` → `result` (agy bilan tasdiqlangan).
- [ ] Claude CLI va 3-agent (agents.json ga qo'shilgan) bilan qabul sinovi.
- **Dalil:** PTY scrollback, task_id, API status, DECISIONS qaydi.

## Bosqich 3 — 1:50–2:40 · Jonli sahna va haqiqiy render
- [ ] `/ws/task/{id}` snapshot + log + preview_frame oqimi (40 kadr tasdiqlangan).
- [ ] Progressiv 3D shakllanish: Blender 5s 1080p kub + kadrlar farqi (tasdiqlangan).
- [ ] Natija Artefakt galereyasida ko'rinadi, thumbnail buzilmagan.
- [ ] Jonli preview yarim yozilgan kadrlarni o'tkazib yuboradi (tuzatildi).
- **Dalil:** ffprobe, kadrlar, gallery DOM/skrinshot, WS hisoblagich.

## Bosqich 4 — 2:40–3:20 · Rejimlar, DeepSearch/DeepX
- [ ] STD/EEPX/SUPER/DEEPX tanlovi serverga yoziladi va statusbarda ko'rinadi (tasdiqlangan).
- [ ] Har bir rejimda kamida bitta vazifa ishga tushirilib, bosqich loglari olinadi.
- [ ] DeepSearch manba xatolari `source_errors` va loglarda ko'rinadi (tasdiqlangan).
- [ ] DeepX research→analysis→swarm bosqichlari log bilan tasdiqlangan.
- **Dalil:** task loglari, `source_errors`, API javoblari.

## Bosqich 5 — 3:20–3:50 · UI/UX final audit
- [ ] NEXUS brendi, 13 agent, zichlik 0.9, bezak chiziqlar yo'q (tasdiqlangan).
- [ ] 1600x1000 va 1280x800 da gorizontal overflow yo'q.
- [ ] Konsol xatolari yo'q; barcha tugmalar bosiladi.
- [ ] Light/dark tema izchil.
- **Dalil:** Playwright skrinshotlari, console log, overflow o'lchovlari.

## Bosqich 6 — 3:50–4:00 · Qabul va hisobot
- [ ] Yakuniy `doctor` + to'liq test + build.
- [ ] DECISIONS.md, PROJECT.md, README, time-log yangilangan.
- [ ] Qisqa hisobot: nima ishlaydi (dalil), nima ishlamaydi (halol).

## Faktik natijalar (2026-11-21 21:10)
- **0-bosqich:** `doctor` 0 FAIL; to'liq `pytest` 105 passed / 2 skipped (ikki marta tasdiqlandi).
- **1-bosqich:** desktop yorlig'i eski `C:\Users\Kapitan\conduit` ga ishora qilgan — asosiy
  `Documents\Проект по умолчанию\conduit\CONDUIT.bat` ga o'zgartirildi (MATCH=True, EXISTS=True);
  11 ta workspace tools.py ham 596 bayt stub.
- **2-bosqich:** agy, claude_code (`task_8c57c298` PASS), codex_cli va opencode_agent sinovdan o'tti.
  `agent_env.py` bilan MCP izolyatsiyasi: 8s vs 50s, global config o'zgarmadi, terminal tasdiqi bor.
- **3-bosqich:** galereya 138 rasm / 0 buzilgan / haqiqiy render bor; WS 40 preview kadr.
- **4-bosqich:** EEPX E1/E2/P loglari, SuperAgent swarm 2 bosqich, DeepX research→swarm loglari.
- **5-bosqich:** 1600x1000 va 1280x800 da overflow yo'q, konsol 0 xato.
- **6-bosqich:** yakuniy doctor 0 FAIL, pytest 105/2, build OK. Hisobot berildi.

> Eslatma: reja 4 soatga mo'ljallangan edi, ammo muhit 35 daqiqa ichida barcha bandlar
> bajarildi va tasdiqlandi; qolgan vaqt kutilmadi (kerak emas edi).

## Doimiy qoidalar
- Jimgina try/except yo'q; xato log va Report'da ko'rinadi.
- "Tayyor" faqat dalil bilan: log, skrinshot, fayl yo'li, kadr.
- Bosqich dalil bilan yopilmaguncha keyingisiga o'tish yo'q.
- Global foydalanuvchi sozlamalariga (MCP config, auth) tegmaslik.
## Qo'shimcha (5 soat, 2026-11-22 00:15)
- Blender headless Cycles CPU ga o'tkazildi (EEVEE/Workbench GPU crash).
- 14 modulda jimgina xatolar loglandi; 3 ta regression test qo'shildi (108 passed).
- SuperAgent va DeepX qayta ishga tushirilib oxirigacha PASS.
- To'liq tablarga 'Studiyaga qaytish' tugmasi qo'shildi.
- Soak-test 30 daqiqa davomida har 2 daqiqada vazifa yuboradi.
