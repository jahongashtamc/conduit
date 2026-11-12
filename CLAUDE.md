<!-- CONDUIT-STUDIO-GUIDE -->

# Conduit Studio — Agent uchun yo'riqnoma

Sen **Conduit studiyasi ichida** ishlayapsan (cwd = Conduit loyiha papkasi).
Bu studiyada rasm, video, 3D, brauzer, Figma va boshqa ishlar uchun tayyor
sub-agentlar bor. **Bunday ishlarni o'zing qilma** — `conduit` CLI orqali
tegishli sub-agentga topshir va natijani foydalanuvchiga ko'rsat.

## Asosiy buyruqlar

```text
conduit list                        # sub-agentlar va asboblar ro'yxati + holati
conduit run <subagent> "<vazifa>"   # vazifa yaratadi, task_id qaytaradi
conduit status <task_id>            # holat, qadamlar, loglar
conduit result <task_id>            # chiqqan fayllar yo'li (artefaktlar)
conduit wait <task_id>              # vazifa tugashini kutadi
conduit browser <url>               # studiya brauzer oynasini yo'naltirish
conduit screenshot [fayl.jpg]       # brauzer oynasi kadrini saqlash
```

Har bir buyruq `--json` bilan JSON chiqaradi (agent o'qishi uchun qulay):
`conduit list --json`.

## Ish tartibi

1. Vazifani tahlil qil, kerakli sub-agentni tanla (ro'yxat pastda).
2. `conduit run <subagent> "<aniq vazifa>"` — task_id ol.
3. `conduit status <task_id>` bilan kuzat (yoki `conduit wait <task_id>`).
4. `conduit result <task_id>` bilan chiqqan fayllar yo'lini ol va
   foydalanuvchiga ko'rsat (natijalar studiyadagi Artefakt galereyasiga tushadi).

## Muhit o'zgaruvchilari

- `CONDUIT_API` — backend manzili (default `http://127.0.0.1:8000`)
- `CONDUIT_SESSION` — shu terminal sessiyasining ID si

## Mavjud sub-agentlar

| ID | Turi | Tavsif |
|----|------|--------|
| `animator` | role | Harakatli grafika, keyframe animatsiya va render |
| `designer` | role | UI/UX dizayn tizimlari, Figma spec va maketlar |
| `editor` | role | Videomontaj, timeline qirqish, rang berish va render |
| `inspector` | role | Tizim auditi, testlar va PASS/FAIL tekshiruvchi |
| `inst_blender` | instrument | Blender bpy headless dvigateli: 3D model, sahna va render — GUI'siz, k |
| `inst_figma` | instrument | Figma REST API: dizayn fayl ma'lumotlari va sync — desktop ilova kerak |
| `inst_image` | instrument | PIL tasvir dvigateli: prosedural rasm/tekstura PNG yaratish (determini |
| `inst_video` | instrument | FFmpeg dvigateli: kadrlardan MP4 video va keyframe animatsiya (GIF/MP4 |
| `inst_web` | instrument | Brauzer va qidiruv: veb qidiruv (DuckDuckGo), sahifa skrinshoti va o'z |
| `notion` | role | Notion bilan bog'liq vazifalarni avtomatlashtirish |
| `painter` | role | Rastrli san'at, tekstura xaritalari va raqamli chizish |
| `scout` | role | Veb navigatsiya, tahlil va skrinshot olish |
| `sculptor` | role | 3D modellashtirish, materiallar va headless rendering |
| `sentinel` | role | Studio yaratgan kod va tizimlarni xavfsizlik va buzilishlarga sinovchi |
| `slack` | role | Slack bilan bog'liq vazifalarni avtomatlashtirish |
| `superagent` | role | Murakkab MVP loyihalarni dekompozitsiya qilib, subagentlar to'dasi (sw |
