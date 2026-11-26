# FFmpeg Video Instrument Checker

PASS faqat quyidagi 4 shart **hammasi** bajarilganda beriladi:

1. `success: true` qaytgan
2. `video_path` dagi MP4 diskda mavjud va `bytes > 0`
3. `frames > 0` (video haqiqiy kadrlardan iborat)
4. `inputs` ro'yxatida barcha so'ralgan kliplar bor

## Yakuniy tekshiruv buyrug'i

```bash
python tools.py check_goal "<vazifa matni>" "{\"artefakt\": \"<yo'l>\", \"bytes\": <son>}"
```

`check_goal` `verdict: FAIL` qaytarsa — natija FAIL, hatto doer "bajarildi" degan bo'lsa ham.

## Dalil yangiligi

Faqat **shu vazifa** uchun yaratilgan artefakt dalil bo'ladi. Eski fayl (o'zgarish
vaqti vazifa boshlanishidan oldin) — dalil emas, FAIL.

## Hisobot formati

Oxirgi qator aynan:

```
VERDICT: PASS <artefakt yo'li> <hajm> <qo'shimcha dalil>
```
yoki
```
VERDICT: FAIL <qaysi shart bajarilmadi>
```
