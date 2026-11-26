# Animator Planner

Keyframe animatsiyani aniq rejaga aylantir:

1. **Vaqt o'qishi**: animatsiya davomiyligi (sekund). Ko'rsatilmasa — 2 soniya.
2. **Keyframe'lar**: kamida 2 ta nuqta — boshlanish (`t: 0`) va tugash (`t: 1`).
   `t` — 0..1 oralig'idagi nisbiy vaqt.
3. **Ranglar**: har keyframe uchun HEX rang (`#RRGGBB`), o'tish silliq interpolatsiya bo'ladi.
4. **Chiqish**: `animation.gif` (standart) yoki `.mp4`.

Reja oxirida aniq buyruq:

```bash
python tools.py anim_render '[{"t":0,"color":"#101828"},{"t":1,"color":"#38bdf8"}]' 2.0
```

Uch nuqtali misol (qizil → yashil → ko'k):

```bash
python tools.py anim_render '[{"t":0,"color":"#FF0000"},{"t":0.5,"color":"#00FF00"},{"t":1,"color":"#0000FF"}]' 3.0
```

**Diqqat**: JSON bitta qo'shtirnoq ichida, ichki kalitlar ikki qo'shtirnoq bilan.
PowerShell'da bu shakl ishlaydi. JSON buzilgan bo'lsa tool "Keyframe JSON noto'g'ri"
qaytaradi.
