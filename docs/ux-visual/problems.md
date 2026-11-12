# Muammo klasterlari (severity × reach × centrality bo'yicha)

## C1 — Terminal siqilgan (F1) — P1
**Root cause:** `page.tsx` o'ng ustunda terminal `flex-1`, miya tuguni `flex-[2]`
— terminalga ustunning 1/3 i tushadi (~170px canvas). Terminal agentning asosiy
ish maydoni (L7: primary work area largest) — aksincha eng kichigi.
**Qabul mezoni:** 1440×900 da terminal ko'rsatuvchi maydoni ≥ 300px; foydalanuvchi
terminal/miya nisbatini sudrab o'zgartira oladi (0.25–0.75 oralig'i).
**Yuzalar:** workstation tab.

## C2 — Agent tuguni kartalari siqiq va kesilgan (F2, F5) — P1
**Root cause:** `Window3BrainGraph.tsx:274` `grid-cols-2 sm:grid-cols-3 xl:grid-cols-4`
— 560px ustunda 4 ustun kartalar ~130px ga siqadi, matn kesiladi.
**Qabul mezoni:** kartalarda agent nomi to'liq o'qiladi (truncate yo'q 560px ustunda);
ko'rinayotgan qator to'liq kartalar bilan tugaydi.
**Yuzalar:** workstation tab o'ng ustun.

## C3 — Tipografiya juda kichik (F3) — P2
**Root cause:** `text-[9px]`/`text-[10px]` 130+ joyda ishlatilgan, type scale
intizomsiz (19 kombinatsiya).
**Qabul mezoni:** eng kichik matn 11px; 9px va 10px aralash qiymatlar yo'qoladi.
**Yuzalar:** butun ilova.

## C4 — Brauzer bo'sh holati o'lik zona (F4) — P2
**Root cause:** jonli tab bo'shliganda faqat globus ikonkasi bilan katta qora
panel qoladi; hech qanday amal taklif qilinmaydi.
**Qabul mezoni:** bo'sh holatda URL kiritish + quick action'lar ko'rinadi;
bo'sh holat matni kontrasti ≥ 4.5:1.
**Yuzalar:** Window2Browser jonli tab.

## C5 — Kichik nishonlar (F6) — P2
**Root cause:** `px-2 py-0.5` va `p-1` standart tugma o'lchamlari 15–23px.
**Qabul mezoni:** barcha interaktiv tugmalar ≥ 24px balandlik.
**Yuzalar:** titlebar, terminal, status bar, workspace.

## C6 — Kontrast (F7) — P2
**Root cause:** `text-slate-600`/`text-slate-700` qora fonda matn sifatida.
**Qabul mezoni:** matn kontrasti ≥ 4.5:1; ajratgichlar ≥ 3:1 yoki dekorativ emas.
**Yuzalar:** Window2Browser, DesktopStatusBar.

## Kechiktiriladi
- F8 alignment near-miss'lar (P3) — keyingi pass.
- React Flow watermark (P3).
