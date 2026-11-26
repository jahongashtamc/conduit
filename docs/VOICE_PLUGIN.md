# Conduit Voice plagi

AI agentlar uchun lokal ovoz yaratish va ovoz o'zgartirish. Bulut API yo'q,
kalit yo'q, tarmoq chaqiruvi yo'q.

## Imkoniyatlar

| Operatsiya | Buyruq | Dvigatel |
|---|---|---|
| O'zbek matnidan nutq | `python -m voice speak "Salom dunyo" --category qiz` | MMS VITS ONNX (CPU) |
| Lotin o'zbek → Kirill | avtomatik, alohida buyruq yo'q | `voice/text.py` |
| ru/en nutq | `python -m voice speak "Hello" --language en` | Windows SAPI (Zira/Irina) |
| Namunadan ovoz uslubi | `python -m voice clone "Salom" namuna.wav --consent --consent-id ID` | F0 + spektr o'lchov + DSP |
| Toifaga o'tkazish | `python -m voice convert namuna.wav boy` | pitch/formant/tilt/breath/speed |
| Oqim (stream) | `python -m voice stream "Matn..." --chunk-ms 250` | gap bo'yicha ketma-ket WAV bo'laklari |
| Lokal HTTP API | `python -m voice serve --port 8765` | `/api/voice/{speak,clone,stream,catalog,doctor}` |
| Diagnostika | `python -m voice doctor` | sha256, deps, SAPI, mikrofon, ffmpeg |

Toifalar: `male`, `female`, `neutral`, `boy`, `girl`, `child`, `teen`, `deep`,
`elderly` (aliaslar: `erkak`, `ayol`, `qiz`, `bola`, `qari`, `past`, ...).

## To'g'rilik chegarasi (halol)

- Neural ovoz klonlash modeli yo'q: XTTS/Chatterbox CPML 1.0 (notijorat), Python
  3.9–3.12 va torch talab qiladi; mavjud GPU GTX 1080 Ti (sm_61) CUDA 13 tomonidan
  qo'llab-quvvatlanmaydi. Shuning uchun klonlash `clone_mode: "stylized"`,
  `synthetic: true`, `neural_clone: false` deb belgilanadi.
- Klonlash namunadan F0 (FFT cho'qqisi) va spektral muvozanatni o'lchab, keyin
  WSOLA time-stretch + resample pitch + formant masshtabi + FFT spectral tilt
  bilan bajariladi. Bu uslub o'tkazishdir, shaxsning ovozini biometrik tiklash emas.
- Piper katalogida o'zbek ovozi yo'q (183 ovoz, 54 til, `uz` kaliti 0 ta).
- O'zbek modellari kirill yozuvga mo'ljallangan; Lotin matn avtomatik tarjima
  qilinadi. Boshqa tillar faqat SAPI ovozlari bor bo'lsa ishlaydi.
- Mikrofon yo'q bo'lgan tizimda "ovozni mikrofondan yozib olish" ishlamaydi;
  klonlash uchun tayyor WAV fayl talab qilinadi. `voice_doctor` buni ko'rsatadi.

## Modellar

| ID | Manba | Litsenziya | sha256 (onnx/model.onnx) |
|---|---|---|---|
| `uz_male_mms` | [davron112/mms-tts-uzb-cyrl-onnx](https://huggingface.co/davron112/mms-tts-uzb-cyrl-onnx) | CC-BY-NC-4.0 | `13800c7f9d6abce31c7471e5677576a9cbd97e895825d42e0a716d28172d0a68` |
| `uz_female_mms` | [davron112/mms-tts-uzbek-girl-cyrl-onnx](https://huggingface.co/davron112/mms-tts-uzbek-girl-cyrl-onnx) | CC-BY-4.0 | `b26e607c4be29c6adf59eeb59a368be210a0352c53b7204af531cdb8d55ecd69` |

Modellar `voice/models/<male|female>/` ichida. Barcha fayllarning sha256 qiymati
`voice/models.json` da va `voice_doctor` har safar tekshiradi. Yuqoridagi upstream:
[facebook/mms-tts-uzb-script_cyrillic](https://huggingface.co/facebook/mms-tts-uzb-script_cyrillic)
va [MuzaffarSharofitdinov/mms-tts-uzbek-girl-voice_cyrillic](https://huggingface.co/MuzaffarSharofitdinov/mms-tts-uzbek-girl-voice_cyrillic).

O'rnatilgan paketlar: `onnxruntime==1.32.0`, `numpy`, `tokenizers==0.23.3`
(tokenizer faqat yuklab olishda ishlatildi; ish vaqtida vocab to'g'ridan-to'g'ri
`tokenizer.json` dan o'qiladi).

## Conduit tool'lari

```text
python backend/tools.py voice_catalog
python backend/tools.py voice_doctor
python backend/tools.py voice_speak "Salom dunyo" qiz auto voice/output/a.wav
python backend/tools.py voice_clone "Salom" voice/output/namuna.wav girl
python backend/tools.py voice_convert voice/output/namuna.wav boy
python backend/tools.py voice_stream "Bir, ikki, uch."
```

JSON shaklida chaqirish (matnda bo'shliq/tirnoq bo'lsa qulay):

```text
python backend/tools.py voice_speak '{"text":"Salom dunyo","category":"qiz","language":"auto"}'
python backend/tools.py voice_clone '{"text":"Salom","reference":"voice/output/namuna.wav","consent":true,"consent_id":"approved_001"}'
```

Subagent: `conduit run voice "<vazifa>"` → `conduit wait` → `conduit result`.

## Xavfsizlik (2026-11-25 tuzatishlar)

- `voice_clone` faqat `consent=true` va `consent_id` bilan bajariladi. Roziliksiz
  `CONSENT_REQUIRED` xatosi qaytariladi (CLI, tool va HTTP bir xil).
- Namuna va chiqish yo'llari `Path.home()` ichida cheklanadi; symlink va
  `..` bilan chiqish rad etiladi.
- Jim (RMS < 1e-4) WAV na namuna, na natija sifatida qabul qilinadi — soxta
  "muvaffaqiyat" oldi olinadi.
- ONNX modelining sha256 qiymati ish vaqtida ham tekshiriladi (`doctor` bilan
  birga), mos kelmasa `MODEL_HASH_MISMATCH`.
- HTTP `/api/voice/clone` roziliksiz 400 qaytaradi; `/api/voice/stream` endi
  bitta to'g'ri WAV sarlavhasi bilan ma'lumot yuboradi (oldin har chunkning
  sarlavhasi qo'shilib ketgan edi).
- Natijada `device` (`cpu`/`cuda:0`) va `synthetic: true` maydonlari bor.

## Test

```text
python -m pytest voice/tests -q
python -m voice doctor
```

Manbalar o'qilgan sana: 2026-11-24.
