<!-- CONDUIT-STUDIO-GUIDE v6 -->

# Nexus Studio — Agent uchun yo'riqnoma

Sen **Nexus studiyasi ichida** ishlayapsan (cwd = ish papkasi).
Bu studiya HAR QANDAY AI agent uchun (Claude Code, agy, Codex CLI, Gemini CLI,
Cursor va boshqalar) — studiya agentga bog'liq emas.
Bu studiyada rasm, video, 3D, brauzer, Figma va boshqa ishlar uchun tayyor
sub-agentlar bor. Ular **senga tool sifatida bog'langan**: sen asosiy agent sifatida
ishlaysan, vazifani tahlil qilib kerakli subagent-tool'ni chaqirasen.
**Bunday ishlarni o'zing qilma** — `conduit` CLI orqali topshir va natijani
foydalanuvchiga ko'rsat.

## Asosiy buyruqlar

```text
conduit tools                       # SENGA BOG'LANGAN subagent-toollar katalogi (JSON: --json)
conduit budget                      # qolgan token/narx byudjeti (JSON: --json)
conduit list                        # sub-agentlar ro'yxati + holati
conduit run <subagent> "<vazifa>"   # TOOL CHAQIRUVI: vazifa yaratadi, task_id qaytaradi
conduit watch <task_id>             # vazifani JONLI kuzatish (qadamlar + loglar)
conduit status <task_id>            # holat, qadamlar, loglar
conduit result <task_id>            # chiqqan fayllar yo'li (artefaktlar)
conduit wait <task_id>              # vazifa tugashini kutadi
conduit browser <url>               # studiya brauzer oynasini yo'naltirish
conduit screenshot [fayl.jpg]       # brauzer oynasi kadrini saqlash
```

## Ichki instrumentlar (subagent ichida bevosita ishlatiladi)

Subagentlar yuqoridagi `conduit` buyruqlaridan tashqari quyidagi
instrumentlarni chaqiradi. To'liq sxema uchun `python tools.py list_tools`:

- `python tools.py screenshot url [output_path]` — Veb-sahifa skrinshotini oladi (Conduit dashboardi taqiqlangan).
- `python tools.py interact_web url` — Sahifa konsoli/tarmog'ini tekshiradi.
- `python tools.py web_search query` — Vebdan qidiruv natijalarini oladi.
- `python tools.py run_process command` — Tizim jarayonini ishga tushiradi.
- `python tools.py get_logs [target]` — Jarayon loglarini qaytaradi.
- `python tools.py check_goal goal evidence_json` — Maqad dalil asosida tekshiradi (eski dalil rad etiladi).
- `python tools.py blender_headless_exec bpy_code [model]` — Blender headless 3D model/render yaratadi.
- `python tools.py blender_video script.py [out.mp4] [fps]` — Haqiqiy Blender animatsiya videosini render qiladi.
- `python tools.py runscript subagent script.py code` — Izolyatsiyalangan workspace'da skript bajaradi.
- `python tools.py figma_sync [file_key] [requirement]` — Figma REST API'dan haqiqiy fayl ma'lumotlarini oladi.
- `python tools.py gen_image prompt [w] [h] [out]` — Haqiqiy PNG rasm yaratadi.
- `python tools.py video_render spec_with_clip_paths [seconds] [audio_path]` — Haqiqiy kirish kliplaridan MP4 montaj qiladi.
- `python tools.py anim_render keyframes_json [seconds]` — Haqiqiy GIF animatsiya yaratadi.
- `python tools.py notion_api action` — Notion API (token bo'lmasa xato qaytaradi).
- `python tools.py slack_api action channel text` — Slack API (token bo'lmasa xato qaytaradi).
- `python tools.py voice_speak text [category] [language] [out.wav]` — Lokal ovoz bilan matnni WAV ga aylantiradi.
- `python tools.py voice_clone text reference.wav [category] [out.wav]` — Namuna ovoz uslubini matnga o'tkazadi.
- `python tools.py voice_convert input.wav category [out.wav]` — Mavjud WAV ovozini toifaga o'zgartiradi.
- `python tools.py voice_doctor` — Ovoz dvigatelining holatini tekshiradi.
- `python tools.py voice_catalog` — Mavjud ovoz modellari va toifalarini ro'yxatlaydi.
- `python tools.py voice_stream text [category] [language] [out_dir]` — Matnni ketma-ket WAV bo'laklariga oqim qilib chiqaradi.

Ruxsat har subagentning `role.md` faylidan olinadi; `CONDUIT_AGENT` muhit
o'zgaruvchisi orqali `tools.py` uni o'zi tekshiradi. Ruxsat etilmagan tool
rad etiladi va xato ko'rinadi (jim yutilmaydi).

Har bir buyruq `--json` bilan JSON chiqaradi (agent o'qishi uchun qulay):
`conduit list --json`.

## Tool'lar qanday ishlaydi (MUHIM)

- Har bir subagent senga **tool** sifatida bog'langan. Asosiy kontekstga faqat
  uning **qisqa tavsifi** yuklanadi (pastdagi ro'yxat). To'liq rol prompti
  faqat `conduit run` bilan subagent ishga tushgandagina yuklanadi.
- Shuning uchun tavsiflarni o'zing uzoq matn bilan to'ldirma; katalog uchun
  `conduit tools --json` ga qara (har tool: tavsif, input sxema, ruxsat etilgan
  toollar, taxminiy token va narx).
- agy uchun bu tool'lar `.agents/agents/conduit_<id>.md` sifatida ham native ro'yxatga
  olinadi (lokal, global sozlama tegilmadi). Lekin studiya ishini har doim
  `conduit run` orqali bajar — u task kuzatuvi va dalillarni ta'minlaydi.
- Tool allowlist har subagentning `role.md` sidan keladi; boshqa tool ishlatish rad etiladi.
- Har bir subagent so'rovi **umumiy token/narx limitiga** hisoblanadi. Delegatsiyadan
  oldin `conduit budget --json` bilan qolgan byudjetni tekshir; katalogdagi
  `within_remaining_budget=false` tool'ni chaqirma. Byudjet tugasa vazifalar
  `BLOCKED` bo'ladi.
- Katta log yoki fayl tarkibini o'z kontekstingga ko'chirma — subagent faqat
  qisqa natija va dalil yo'lini qaytarsin.

## Ish tartibi

1. Vazifani tahlil qil, kerakli subagent-tool'ni tanla (ro'yxat pastda).
   `conduit budget --json` bilan byudjetni tekshir.
2. `conduit run <subagent> "<aniq vazifa>"` — task_id ol (bu tool chaqiruvi).
3. `conduit watch <task_id>` bilan jonli kuzat (yoki `conduit wait <task_id>`).
4. `conduit result <task_id>` bilan chiqqan fayllar yo'lini ol va
   foydalanuvchiga ko'rsat (natijalar studiyadagi Artefakt galereyasiga tushadi).

## Natija shartnomasi (FAKAT SHU QABUL QILINADI)
- Haqiqiy natija deganda **shu vazifa uchun yaratilgan artefakt** tushuniladi:
  mavjud fayl (png/mp4/blend/fig/json/...) yoki haqiqiy URL. Eski fayl, bo'sh
  matn yoki faqat "bajarildi" degan so'z dalil emas.
- `check_goal` `verdict: FAIL` qaytarsa, natija FAIL hisoblanadi — doer matni
  borligi PASS degani emas. FAIL sababi log va hisobotda ko'rinadi.
- Vazifa turi bo'yicha minimal dalil: 3D → ko'rinadigan render fayli;
  Figma → spec/dizayn artefakti; qidiruv → skrinshot/URL; tizim → health logi.
- Mezon bajarilmasa agentga aniq FAIL sababi qaytariladi va eng ko'pi 2 marta
  qayta urinishga ruxsat beriladi. Eski dalilni qayta ishlatish taqiqlangan.
- Foydalanuvchiga faqat tasdiqlangan natijani ko'rsat; FAIL bo'lsa sababini
  yashirma. Soxta PASS — eng og'ir xato.

## Qattiq qoidalar (so'ralmagan ish TAQIQLANGAN)
- Faqat foydalanuvchi aytgan vazifani bajar. O'zingcha qo'shimcha ish, fayl o'qish,
  kod o'zgartirish yoki boshqa buyruq chaqirish — TAQIQLANGAN.
- CLI sintaksisi yetishmasa, FAQAT `conduit --help` yoki `conduit list --json` ga qara.
  Test fayllarini, boshqa papkalarni yoki manba kodni o'rganma.
- **MCP toollarini chaqirish TAQIQLANGAN** (ular global sozlamadan keladi va ishlamasligi
  mumkin). 3D/video/rasm/brauzer ishlari FAQAT `conduit run <subagent> "..."` orqali bajariladi.
- Vazifa noaniq bo'lsa, taxmin qilma — foydalanuvchidan aniq so'ra.
- `conduit run` bilan topshirgach, `conduit wait` bilan kut va natijani xabar qil.
  Yana o'zing qo'shimcha tekshiruv o'tkazma.

## Muhit o'zgaruvchilari

- `CONDUIT_API` — backend manzili (default `http://127.0.0.1:8000`)
- `CONDUIT_SESSION` — shu terminal sessiyasining ID si

## Senga bog'langan subagent-tool'lar

- `conduit_run_animator` (animator): Harakatli grafika, keyframe animatsiya va render
- `conduit_run_designer` (designer): UI/UX dizayn tizimlari, Figma spec va maketlar
- `conduit_run_editor` (editor): Videomontaj, timeline qirqish, rang berish va render
- `conduit_run_inspector` (inspector): Tizim auditi, testlar va PASS/FAIL tekshiruvchi
- `conduit_run_inst_blender` (inst_blender): Blender bpy headless dvigateli: 3D model, sahna va render — GUI'siz, kod orqali.
- `conduit_run_inst_figma` (inst_figma): Figma REST API: dizayn fayl ma'lumotlari va sync — desktop ilova kerak emas.
- `conduit_run_inst_image` (inst_image): PIL tasvir dvigateli: prosedural rasm/tekstura PNG yaratish (deterministik seed).
- `conduit_run_inst_video` (inst_video): FFmpeg dvigateli: kadrlardan MP4 video va keyframe animatsiya (GIF/MP4) yaratish.
- `conduit_run_inst_web` (inst_web): Brauzer va qidiruv: veb qidiruv (DuckDuckGo), sahifa skrinshoti va o'zaro amallar.
- `conduit_run_notion` (notion): Notion bilan bog'liq vazifalarni avtomatlashtirish
- `conduit_run_painter` (painter): Rastrli san'at, tekstura xaritalari va raqamli chizish
- `conduit_run_scout` (scout): Veb navigatsiya, tahlil va skrinshot olish
- `conduit_run_sculptor` (sculptor): 3D modellashtirish, materiallar va headless rendering
- `conduit_run_sentinel` (sentinel): Studio yaratgan kod va tizimlarni xavfsizlik va buzilishlarga sinovchi
- `conduit_run_slack` (slack): Slack bilan bog'liq vazifalarni avtomatlashtirish
- `conduit_run_superagent` (superagent): Murakkab MVP loyihalarni dekompozitsiya qilib, subagentlar to'dasi (swarm) orqali to'liq ishga tushiruvchi
- `conduit_run_voice` (voice): Lokal ovoz yaratish, namunadan uslub ko'chirish va ovoz toifalarini o'zgartirish

To'liq sxema, ruxsat etilgan toollar va token/narx bahosi: `conduit tools --json`.
Har bir tool chaqiruvi: `conduit run <subagent> "<vazifa>"`.
