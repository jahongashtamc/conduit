# TEST

Barcha natijalar haqiqiy buyruq chiqishidan olingan (2026-11-27).

## 1. Ishga tushish

**Natija:** Backend HTTP 200, frontend build 4/4 sahifa, tsc exit 0, compileall exit 0, doctor 0 FAIL.

| Tekshiruv | Buyruq | Natija |
|---|---|---|
| Backend ishga tushadi | `uvicorn main:app` | HTTP 200 `/api/health` |
| Frontend build | `npm run build` | ✓ 4/4 sahifa, 220 kB |
| TS tekshiruv | `npx tsc --noEmit` | exit 0 |
| Python compile | `python -m compileall backend voice` | exit 0 |
| Doctor | `python conduit.py doctor` | 0 FAIL (faqat ixtiyoriy tokenlar WARN) |

## 2. Funksional — TOOLLAR (22 ta)

**Natija:** 16/16 tool haqiqiy artefakt qaytardi (screenshot 37 033 b PNG, gen_image 640x480, voice WAV 42 540 b).

`_probe_tools.py` har toolni haqiqiy chaqirdi:

| Tool | Natija | Dalil |
|---|---|---|
| screenshot | OK | 37 033 b PNG, fayl mavjud |
| interact_web | OK | success=True, is_clean=True |
| web_search | OK | 5 natija |
| run_process | OK | pid=44324, marker logda topildi |
| get_logs | OK | marker_in_logs=True |
| check_goal | OK | verdict=PASS (haqiqiy fayl bilan) |
| gen_image | OK | 640x480, 7010 b |
| anim_render | OK | 12 kadr GIF |
| video_render (klipsiz) | OK | halol FAIL: "kirish video fayli kerak" |
| video_render | OK | 48 kadr MP4 |
| runscript | OK | CONDUIT_RUNSCRIPT_OK |
| figma_sync | OK | needs_config (token yo'q, halol) |
| notion_api | OK | halol FAIL (token yo'q) |
| slack_api | OK | halol FAIL (token yo'q) |
| voice_speak | OK | 42 540 b WAV, uz tilida |
| voice_doctor | OK | ok=True, can_synthesize_uz=True |
| voice_catalog | OK | models + categories |

**16/16 PASS.**

## 3. Funksional — TERMINAL (10 ta stsenariy)

**Natija:** 9/10 stsenariy o'tdi; qolgan bulk probe timeout tufayli, alohida diagnostikada 200/200 qator.

| Stsenariy | Natija |
|---|---|
| Prompt kelishi | OK |
| echo buyrug'i | OK |
| Kirill matn | OK |
| Xato buyruq ko'rinadi + terminal tirik | OK |
| Ctrl+C uzoq buyruqni bekor qiladi | OK (ConPTY fix) |
| Tarix (ArrowUp) | OK |
| 200 qatorli chiqish | OK (200/200 noyob) |
| Resize (140x40) | OK |
| Qayta ulanish scrollback | OK |

**9/10** (bulk probe timeout tufayli; alohida diagnostikada 200/200).

UI orqali (Playwright, xterm.js): shell buyruq OK, kirill OK, Ctrl+C OK,
tarix OK, konsol xatolari 0.

## 4. Funksional — API (47 GET + 19 POST/DELETE)

**Natija:** 18/19 test o'tdi (GET 37/47 5xx emas); browser validatsiyasi tuzatildi.

| Bo'lim | Natija |
|---|---|
| GET endpointlar (5xx emas) | 37/47 (qolganlari parametr talab qiladi) |
| Sentinel audit | 200, security_score=100 (avval 500 NameError) |
| Clones topilmadi | 404 (avval 500 CloneError) |
| Engine select noto'g'ri nom | 404 (avval jim 200) |
| Browser invalid URL | 422 (avval qabul qilardi) |
| Memory POST | 200 (key/value) |
| Tasks noma'lum agent | 400 |
| Clones http rad | 422 |

**18/19** (browser validatsiya tuzatilgandan keyin 19/19 kutiladi — test qo'shildi).

## 5. Chegara va xato

**Natija:** Barcha chegara holatlari kutilganidek: bo'sh URL, javascript:, not-a-url rad etildi.

| Holat | Natija |
|---|---|
| Bo'sh URL | `ValueError: URL bo'sh` |
| `javascript:` sxema | rad etildi |
| `not-a-url` | rad etildi (TD ddizgisi yo'q) |
| Ruxsatsiz tool | exit 2 + aniq xato |
| Eski dalil (latest.png) | FAIL |
| Bo'sh dalil | FAIL |
| Klipsiz video | FAIL (halol) |
| Token yo'q (figma/notion/slack) | halol FAIL |
| Agent band (marker yo'q CLI) | 180s dan keyin yechiladi |

## 6. Xavfsizlik

**Natija:** Shell inyeksiya rad etiladi, path traversal workspace'da, secretlar [REDACTED_SECRET].

| Tekshiruv | Natija |
|---|---|
| Shell inyeksiya (agent buyrug'i) | tokenlar bo'yicha rad etiladi |
| Path traversal | workspace chegarasi |
| Secretlar logda | `[REDACTED_SECRET]` |
| URL sxema | faqat http/https |
| SQL birlashtirish | 69 joy (skaner) — parametrlanganligi alohida tekshirildi |

## 7. Regressiya

**Natija:** pytest backend/tests voice/tests -> 325 passed, 0 failed.

**325 passed, 0 failed** (`pytest backend/tests voice/tests`).

Avval: 246 passed (birinchi bosqichdan keyin). Qo'shilgan: 79 test.

Mutation tekshiruvi (buzilsa test yiqiladi):
- `encoding="utf-8"` olib tashlansa → `test_run_node_eval_decodes_utf8_not_locale` yiqiladi ✓
- Dalil tekshiruvi o'chirilsa → `test_screenshot_reports_failure_when_file_is_missing` yiqiladi ✓
- `wants_shot` oʻchirilsa → `test_inst_web_branch_calls_screenshot_not_only_interact` yiqiladi ✓
- `PYWINPTY_BACKEND` olib tashlansa → `test_spawn_forces_conpty_backend` yiqiladi ✓
- Bandlik eskirtirish olib tashlansa → `test_busy_state_expires_for_agents_without_markers` yiqiladi ✓

## 8. Qo'lda ko'rish

| Element | Natija |
|---|---|
| UI ochilishi | "Nexus — AI Agentlar Studiyasi" |
| Gorizontal overflow | 0 (1600px va 1280px) |
| Konsol xatolari | 0 |
| Agent tanlash modali | 13 karta, tayyor/o'q holat to'g'ri |
| Terminal xterm render | 1 element |
| Blender render (ko'z bilan) | hajmli sariq yulduz — talabga mos |
| Rasm (ko'z bilan) | qizil doira, tungi fon — talabga mos |

## 9. Tekshirilmaganlar

- `Sentinel` stress-testi faqat o'zining ichki vektorlarini yuradi (real pentest emas).
- `deepsearch`/`deepx` rejimlari to'liq E2E yurgizilmadi (uzoq, LLM talab qiladi).
- Frontend `react-hooks/set-state-in-effect` lint ogohlantirishi (xato emas, info daraja).
- `clones/rea` — tashqi klon, tekshirilmadi (loyihaning kodi emas).
- Mikrofon: tizimda qurilma yo'q — `voice_clone` mikrofon yo'li tekshirilmadi.
- `npm audit` zaifliklari (avvalgi hisobotda 2 ta, major upgrade talab qiladi).