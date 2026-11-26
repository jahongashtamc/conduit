# Animator Checker

PASS shartlari (hammasi bajarilishi shart):

1. `anim_render` chiqishida `success: true`.
2. `animation_path` fayli diskda mavjud va hajmi 0 dan katta:
   ```bash
   python -c "import os; p=r'<animation_path>'; print(os.path.isfile(p), os.path.getsize(p))"
   ```
3. `frames >= 12` (kamida 1 sekund @ 12fps) — 1-2 kadr animatsiya emas.
4. `keyframes >= 2` — bitta rangdan animatsiya bo'lmaydi.
5. Fayl kengaytmasi `.gif` yoki `.mp4`.

Yakuniy tekshiruv:

```bash
python tools.py check_goal "<vazifa>" "{\"animation_path\": \"<path>\", \"frames\": <son>, \"bytes\": <son>}"
```

Animatsiya harakatlanishini isbotlash uchun kamida ikki xil kadr bo'lishi kerak:
`keyframes` maydoni 2 dan kichik bo'lsa FAIL.
