# Web Instrument Checker

PASS faqat quyidagi 3 shart **hammasi** bajarilganda beriladi:

1. `success: true` qaytgan
2. `screenshot_path` dagi fayl diskda mavjud va hajmi 0 dan katta
3. Qidiruvda `results` ro'yxati bo'sh emas (kamida 1 natija)

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
