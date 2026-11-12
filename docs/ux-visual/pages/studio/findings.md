# Studio — UX Visual topilmalari (1440×900, 2026)

## Verdict (asosiy workstation tab)
Uch ustunli ish stoli struktura jihatdan to'g'ri (L1 page-scroll=0), lekin
**zichlik noto'g'ri taqsimlangan**: tipografiya 9–14px orasida 19 kombinatsiya,
ko'p matn 9–10px (o'qish qiyin), terminal atigi 170px balandlikda siqilgan,
markaziy brauzer paneli bo'sh holatda viewport'ning ~21%ini o'lgan joy egallaydi,
agent kartalari 4 ustunda kesilib qolgan.

## Topilmalar jadvali

| ID | Daraja | Element | Muammo | Norm | Dalil | Sev. |
|----|--------|---------|--------|------|-------|------|
| F1 | Terminal | `Window1Terminal` xterm maydoni | **544×170px** — faqat 8–9 qator ko'rinadi; flex-1:flex-[2] nisbati terminalga ustunning 1/3 ini beradi | L1, D1 | term_measure.js: xterm h=170, rightCol h=824 | **P1** |
| F2 | Agent kartalari | `Window3BrainGraph` grid-cols-4 | 560px ustunda 4 ustun → kartalar ~130px, nomlar kesilgan ("Blender Instr…"), 2-qator o'rtadan kesilgan | D1, C4 | look_at_image + audit | **P1** |
| F3 | Tipografiya | butun ilova | 19 ta size/weight kombinatsiya; 9px va 10px asosiy matn (63+ element) — 13–14px normadan past | D1, H3 | layout-audit type | **P2** |
| F4 | Brauzer bo'sh holati | `Window2Browser` jonli tab | `flex-1 min-h-[240px]` qora panel faqat globus ikonkasi — viewport'ning 21% i o'lik zona, eng prominent element bo'sh panel | D2, H1 | deadSpace 21% + look_at_image | **P2** |
| F5 | Kesilgan kartalar | Window3BrainGraph scrollH 573 vs clientH 499 | karta o'rtadan kesilib ko'rinadi — "buzilgan" taassurot | L5, I8 | audit scrollers + look_at_image | P2 |
| F6 | Kichik nishonlar | STD/EEPX/SUPER/DEEPX (20px), "Yangi vazifa" (19px), "conduit list" (19px), SFX ON (15px), terminal input (16px) | < 24px minimal | I4 | audit smallTargets (15 ta) | **P2** |
| F7 | Kontrast | "subagent sahifa ochmagan" 2.72:1, ajratgichlar 1.41:1, "Jonli" 3.68:1 | 4.5:1 dan past | A1 | audit lowContrast | P2 |
| F8 | Alignment | 11 ta yaqin-o'tkazib yuborgan chet (10/12, 12/15, 141/144...) | panellar chetlari mos kelmaydi | H6, L4 | audit nearMissEdges | P3 |

## Yaxshi holatda qoladigan joylar
- Sahifa scrolli yo'q (L1 ✅) — barcha scroll panel ichida
- Uch ustunli layout mantiqan to'g'ri guruhlangan (L7 ✅)
- Memory va Apps tablari tartibli, kartalar tekis (H5 ✅)
- Miya grafigi o'qiladigan, ataylab qilingan ko'rinish
- Terminal status indikatori (ulangan/uzilgan) aniq va tushunarli (C3 ✅)
