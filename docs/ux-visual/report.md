# UX Visual hisobot — Conduit Studio

**Surf:** workstation (asosiy), Miya, Xotira, Artefakt, Ilovalar — 1440×900.
**Sabab (foydalanuvchi):** "terminal siqilib qolgan, UX'lar juda zich".

## Oldin → Keyin (implementatsiya qilingan klasterlar)

| Klaster | Qaror | Natija (o'lchangan) |
|---|---|---|
| **C1 Terminal siqilgan** (P1) | Terminal default 55% balandlik + terminal↔miya orasiga **sudraladigan ajratgich** (25–75% clamp) | 170px → **357px**; drag +80px → 510px; PTY resize avtomatik |
| **C2 Agent kartalari** (P1) | `grid-cols-4` → `grid-cols-2` (560px ustunda) | karta 130px → **242px**, matn kesilishi yo'q |
| **C3 Tipografiya** (P2) | global `text-[9px]`/`[10px]` → `text-[11px]` (130+ joy) | sub-11px matn **0**; scale {11,12,14} |
| **C4 Brauzer bo'sh holati** (P2) | URL kiritish (`POST /api/browser/navigate`) + 3 quick action | o'lik 21% zona amalga aylandi |
| **C5 Kichik nishonlar** (P2) | `py-0.5`→`py-1`, `p-1`→`p-1.5`, SFX `h-6` | <24px tugma **0** (15→0) |
| **C6 Kontrast** (P2) | slate-600/700 matn → slate-400/600 | 2.72:1 → ≈7:1 |

**Tekshiruv:** tsc 0 xato, `npm run build` exit 0, agent-browser o'lchovlari
(`verification/clusters.md`), oldin/keyin skrinshotlar, look_at_image tasdiği.

## Kechiktirilgan (P3)
- F8 alignment near-miss'lar (11 ta yaqin chet)
- React Flow watermark
- Kartalar ro'yxati konteyner chetida fade

## Yaxshi holatda qolganlar
- Sahifa scrolli yo'q (L1), uch ustunli mantiq (L7), Memory/Apps tablari tartibli,
  Miya grafigi o'qiladigan, terminal status indikatori aniq (C3).

## Tekshirilmaganlar
- 768×1024 va 390×844 breakpoint'lar (desktop ilova 1100×700 min — mobil
  viewport rejasiz); boshqa tillar (EN) matn uzunliklari; uzoq sessiyada
  terminal scrollback to'lib-qolishi.
