# DEBUG

Har topilgan nuqson: alomat -> ildiz sabab -> tuzatish -> regressiya testi.
Barchasi haqiqiy reproduksiya bilan tasdiqlangan (2026-11-27).

---

## XATO 1: Terminalda Ctrl+C umuman ishlamaydi

**Alomat:** `Start-Sleep -Seconds 60` yoki `ping` yozib Ctrl+C bosilsa
terminal osilib qoladi; keyingi buyruq ham bajarilmaydi.

**Qidiruv:** WS qatlami to'g'ri (`\x03` yuboriladi — `framesent` bilan
tasdiqlandi). Filtr ham to'g'ri (`_TERMINAL_RESPONSE_RE` `\x03` ni moslamaydi).
Xom PTY'ni to'g'ridan-to'g'ri sinash (WS'siz) ham ishlamadi.

**Ildiz sabab:** pywinpty 3.1.2 `spawn()` da backend berilmasa avtomatik
tanlaydi va bu mashinada **WinPTY** backend'ga tushadi. O'lchov:
```
PYWINPTY_BACKEND=1 (ConPTY) -> 4/4 Ctrl+C muvaffaqiyatli
PYWINPTY_BACKEND=0 (WinPTY) -> 0/4 (chiqish umuman kelmaydi)
env yo'q (avto)            -> 0/4
```
`sendintr()` ham, xom `\x03` ham WinPTY'da ishlamaydi.

**Tuzatish:** `terminal_session._spawn_pty()` da
`os.environ.setdefault("PYWINPTY_BACKEND", "1")`; Ctrl+C uchun
`pt.sendintr()` ishlatiladi (rasmiy API).

**Regressiya:** `test_pty_backend.py::test_spawn_forces_conpty_backend`,
`::test_ctrl_c_uses_sendintr`. Mutation bilan tasdiqlangan.

---

## XATO 2: `voice_speak` `language="uz"` da ONNX xatosi

**Alomat:** `InvalidArgument: indices element out of data bounds, idx=45
must be within the inclusive range [-45,44]`.

**Qidiruv:** Lug'at 45 token (0..44), `<unk>` yo'q. `language="auto"` ishlaydi,
`"uz"` yiqiladi.

**Ildiz sabab:** IKKI qatlam:
1. `normalize_text()` da `mode == "uz"` hech bir shoxga tushmaydi — lotin
   harflar normalizatsiyasiz qoladi, lug'atda yo'q.
2. `tokenize()` da `vocab.get("<unk>", 45)` — zaxira id **lug'atdan tashqarida**
   (max id = 44).

**Tuzatish:** `"uz"/"uzbek"` `auto` kabi ishlanadi (script aniqlanadi +
transliteratsiya + filtr). Zaxira id endi `vocab.get("|", 0)` — har doim
lug'at ichida. Aniq yozuv rejimi noto'g'ri berilsa (masalan `cyrillic` +
lotin matn), script qayta aniqlanadi (jim bo'sh natija o'rniga).

**Regressiya:** `voice/tests/test_text.py::test_uz_language_produces_cyrillic`,
`::test_token_ids_never_exceed_vocab` (8 kombinatsiya).

---

## XATO 3: `voice_doctor` model hash "MOS EMAS" — sintez esa ishlaydi

**Alomat:** `voice_doctor` 6 ta model fayl uchun `sha256 MOS EMAS`; ammo
`voice_speak` muvaffaqiyatli WAV yaratadi.

**Ildiruv:** ONNX (114 MB) hash **mos**; kichik JSON'lar mos emas.
`git show HEAD:...` blob hash esa **kutilgan** hash bilan bir xil.

**Ildiz sabab:** `core.autocrlf=true` (Windows git) checkout'da LF -> CRLF
o'giradi. `voice/models.json` dagi hash'lar LF uchun hisoblangan.

**Tuzatish:** `.gitattributes` (`*.json text eol=lf`, binarlar `binary`) +
`voice/doctor.py` `_sha256_text_normalized()` — eski checkout'larni ham
to'g'ri baholaydi.

---

## XATO 4: `voice_speak` boshqa mashinada umuman ishlamaydi

**Alomat:** `VoiceDependencyError: onnxruntime o'rnatilmagan`.

**Ildiz sabab:** `onnxruntime` `backend/requirements.txt` da yo'q edi; faqat
bu mashinaning user site-packages'ida bor edi.

**Tuzatish:** `requirements.txt` ga `onnxruntime==1.32.0` qo'shildi
(`docs/VOICE_PLUGIN.md` da allaqachon shu versiya yozilgan).

---

## XATO 5: `/api/clones/{name}` 500 qaytaradi

**Alomat:** Mavjud bo'lmagan klon nomi -> `Internal Server Error`.

**Ildiz sabab:** `clone_manager.get_clone()` topilmasa `CloneError`
**tashlaydi**, endpoint esa `info is None` deb tekshirardi — ya'ni istisno
ushlanmasdan 500 bo'lardi. Qo'shni endpointlar (`refresh`/`delete`) to'g'ri
ushlaydi.

**Tuzatish:** `try/except clone_manager.CloneError -> HTTPException(404)`.

---

## XATO 6: `/api/sentinel/audit` HAR DOIM 500

**Alomat:** `NameError: name 'ConduitKernel' is not defined`.

**Ildiz sabab:** `ConduitKernel` modul boshida import qilinmagan; boshqa
ikkinchi joylarda (`main.py:1081`) lokal import ishlatiladi, bu endpointda esa
yo'q edi.

**Tuzatish:** lokal `from engine.kernel import ConduitKernel`.

**Tekshiruv:** `POST /api/sentinel/audit?task_id=...` -> 200, score 100.

---

## XATO 7: `/api/engine/select` noma'lum dvigatelga JIM 200

**Alomat:** `{"engine": "nope_engine"}` -> 200; foydalanuvchi tanlov saqlangan
deb o'ylaydi, aslida hech narsa o'zgarmagan.

**Ildiz sabab:** `if req.engine in cfg["engines"]` — boshqa holat uchun `else`
yo'q.

**Tuzatish:** 404 + mavjud dvigatellar ro'yxati.

---

## XATO 8: `browser/navigate` "not-a-url" ni qabul qiladi

**Alomat:** `{"url": "not-a-url"}` -> 200 va `https://not-a-url` ga
navigatsiya urinishi.

**Ildiz sabab:** `normalize_navigation_url` host label'ini tekshiradi, lekin
**TLD** talab qilmaydi — bitta nuqtasiz matn ham "to'g'ri host".

**Tuzatish:** tashqi domenlar uchun kamida 2 ta label va `[A-Za-z]{2,63}`
TLD talab qilinadi (localhost/IP bundan mustasno).

**Regressiya:** `test_browser_navigation_api.py::test_invalid_hosts_rejected`.

---

## XATO 9: `inst_*` tez instrument agentlar router orqali tanlanmaydi

**Alomat:** "qizil doira 640x480 rasm yarat" so'rovi `painter` rol-agentiga
ketadi (2-6 daqiqa), holbuki `inst_image` buni 0.6s da bajaradi. Blender
so'rovi `sculptor`ga ketadi (LLM sikli).

**Ildiz sabab:** `manager_router.route_task()` da `inst_*` uchun hech qanday
shox yo'q — ular faqat aniq nom bilan chaqirilardi.

**Tuzatish:** aniq, LLM plannersiz bajariladigan so'rovlar uchun tez yo'l
(`rasm yarat` -> inst_image, `blender/3d` -> inst_blender, `mp4/montaj` ->
inst_video). Muhim: murakkab so'rovlar (qidiruv+audit, AE animatsiya, Figma
dizayn) eski yo'lda qoladi.

**Regressiya:** `test_manager_router_agent_ids.py` (7 yangi test) +
`test_backend.py::test_manager_task_routing` yangilandi.

---

## XATO 10: `_agent_busy` marker bermaydigan CLI'larda abadiy qoladi

**Alomat:** claude/codex/opencode agentidan keyin foydalanuvchi xabar
yubora olmaydi — "Agent hali javob yozayapti" ogohlantirishi qaytadi.

**Ildiz sabab:** `_agent_busy` faqat agy'ning `"Generating"` /
`"ready for input"` matnlarida yangilanadi.

**Tuzatish:** (a) PowerShell prompti qaytsa bandlik tozalanadi; (b)
`AGENT_BUSY_MAX_SECONDS=180` sukunatdan keyin holat eskirgan hisoblanadi;
(c) `_agent_last_output_at` sessiya boshida/`shutdown`da yangilanadi.

**Regressiya:** `test_terminal_busy.py` (3 yangi test).

---

## XATO 11: Windows kodlash sinfi (oldin tuzatilgan, takrorlanmasin)

`subprocess.run(text=True)` cp1251 bilan dekodlaydi; Node UTF-8, PowerShell
cp866 yozadi. Kirill yo'llar mojibake bo'lib, fayl diskda bor bo'lsa ham
`os.path.exists` False. Tuzatish: `encoding="utf-8"` + bola muhiti
(`PYTHONIOENCODING`). Regressiya: `test_utf8_subprocess.py` (6 test).

---

XATO TOPILMADI: quyidagi 10 ta tekshiruv o'tkazildi va hech birida nuqson chiqmadi — PTY resize (140x40), 200 qatorli chiqish (200/200 noyob qator), scrollback replay (WS qayta ulanish), eski dalil FAIL, klipsiz video_render FAIL, Figma/Notion/Slack token yo'q FAIL, shell inyeksiya rad etilishi, UI konsol xatolari 0, UI gorizontal overflow 0, gen_image o'lchami 640x480, Blender render ko'z bilan mos. Barchasi `_probe_terminal.py`, `_probe_tools.py`, `_probe_ui.py` va qo'lda ko'rish bilan tasdiqlangan.

| Tekshiruv | Natija |
|---|---|
| PTY resize (140x40) | ishlaydi |
| 200 qatorli chiqish | 200/200 noyob qator |
| Scrollback replay | ishlaydi |
| `check_goal` eski dalil | FAIL beradi (to'g'ri) |
| `video_render` klipsiz | halol FAIL (to'g'ri) |
| Figma/Notion/Slack token yo'q | halol FAIL (to'g'ri) |
| Shell inyeksiya (agent buyrug'i) | rad etiladi |
| UI konsol xatolari | 0 |
| UI gorizontal overflow | 0 |
| `gen_image` o'lcham | 640x480 (so'ralgan) |
| Blender render | hajmli yulduz (ko'z bilan mos) |

---

## 2026-11-27 — CI flaky osilish (Windows job 28 daqiqa, 57 ta ERROR)

### Alomat
Run 45984826851 va 45999365515: Windows job to'liq to'plamda 10-13 daqiqa
jim qolib, keyin bitta `F` va 24-32 ta ketma-ket `E`, GitHub jobni o'ldirgan.
Bir xil kod oldingi run'da 65s da o'tgan — ya'ni flaky.

### Gipotezalar va rad etuvchi dalillar
1. **Kod regressiyasi** — rad etildi: `3a4f059` faqat 3 ta `.md` o'zgartirgan.
2. **Playwright yo'q** — qisman haqiqat edi (Windows job'ida brauzer
   o'rnatilmagan), tuzatildi, lekin osilish davom etdi.
3. **Tarmoq (deepsearch)** — haqiqiy: `asyncio.gather` umumiy deadline'siz,
   `httpx timeout=12.0` fazalarni ajratmagan. Tuzatildi (`SEARCH_DEADLINE=35s`).
4. **Baza to'qnashuvi** — HAQIQIY ildiz sabab: har `E` ~34s = `sqlite3.connect(
   timeout=30)`. `live_backend` sessiya-scope bo'lib tirik uvicorn'ni butun
   sessiya ushlab turardi; test jarayoni bilan bir vaqtda SQLite'ga yozish
   Windows'da lock beradi. Tuzatildi: scope `module` + alohida baza fayli
   (`CONDUIT_DB_PATH`).
5. **Timeout himoyasi ishlamayapti** — haqiqiy: `timeout_method = thread`
   subprocess/C-kengaytma ichida osilgan testni to'xtata olmaydi. Olib
   tashlandi; `faulthandler_timeout` (diagnostika) + CI `timeout-minutes`
   (majburiy o'ldirish) qoldirildi.

### Sabab (ildiz)
Ikki jarayon bir xil SQLite fayliga yozishi + chegaralanmagan tarmoq kutishi.
Timeout sozlamasi noto'g'ri metodda bo'lgani uchun osilishni to'xtatmagan,
faqat job limiti ishlagan.

### Tuzatish va regressiya
`tests/test_ci_stability.py` (6): pytest.ini/requirements shartnomasi,
deepsearch deadline, `CONDUIT_DB_PATH`, `live_backend.db_path` izolyatsiyasi.
Mutatsiya bilan tasdiqlangan (deadline olib tashlansa test yiqiladi).
Lokal: 293 passed (160s). CI-simulyatsiya (blender/ffmpeg/claude bloklangan):
290 passed (155s).

---

## 2026-11-27 — `task_completed` duplikati (ovoz/bildirishnoma ikki marta)

### Alomat
Frontend `task_completed` ishlovchisi (`page.tsx`) har hodisada ovoz va
Windows bildirishnomasini chiqaradi. Real vazifa tugaganda ular IKKI marta
ishga tushardi.

### Ildiz sabab
Ikki mustaqil yo'l bor:
1. `cli_runner` vazifa tugaganda `ws_broadcast({"type": "task_completed", ...})`
   chaqiradi. `ConnectionManager.broadcast` uni `/ws/live` ga VA
   `TASK_STREAMS[task_id]` ga (ya'ni `/ws/task/{id}`) uzatadi.
2. `websocket_task_stream` o'z tsiklida holatni tekshirib, terminal holatni
   ko'rganda YANA `task_completed` yuboradi.

`/ws/task/{id}` mijozi ikkalasini ham oladi.

### Tuzatish
`ConnectionManager.broadcast` terminal xabar yuborganda
`TASK_STREAM_COMPLETED` ga `task_id` qo'shadi; endpoint belgi bo'lsa
takrorlamaydi. Oxirgi kuzatuvchi ketganda to'plamdan o'chiriladi (xotira
o'smaydi).

### Regressiya
`test_no_duplicate_task_completed_when_broadcast_already_sent`.
Mutatsiya: `if task_id not in TASK_STREAM_COMPLETED:` -> `if True:` bo'lsa
test yiqiladi va duplikat JSON'ini ko'rsatadi (o'lchangan). Backend 296 passed.
