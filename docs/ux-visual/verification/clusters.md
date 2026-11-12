# Verifikatsiya — C1–C6 (1440×900)

| Mezon | Oldin | Keyin | Holat |
|---|---|---|---|
| C1: terminal ko'rsatish maydoni ≥ 300px | 170px | **357px** (default 55%) | ✅ |
| C1: splitter drag | — | +80px drag → 510px (clamp 25–75% ishlaydi) | ✅ |
| C1: PTY resize uzatiladi | — | xterm 21 qator fit bo'ldi, WS resize yuboriladi | ✅ |
| C2: agent kartalari to'liq o'qiladi | ~130px, kesilgan | **242px, clipped=false** | ✅ |
| C3: 9px/10px matn yo'q | 63+ element | **0** (sub-11px: {}) | ✅ |
| C4: bo'sh holatda URL input + quick actions | yo'q | URL input + Ochish + 3 quick action | ✅ |
| C5: barcha tugmalar ≥ 24px | 15 ta kichik | **0** | ✅ |
| C6: "subagent sahifa ochmagan" ≥ 4.5:1 | 2.72 | slate-400 (≈7:1) | ✅ |
| C6: status bar ajratgichlari | 1.41 | slate-600 | ✅ |
| Regressiya: page scroll | 0 | 0 | ✅ |
| Regressiya: `npm run build` | — | exit 0 | ✅ |
| Regressiya: tsc --noEmit | — | 0 xato | ✅ |

Vizual tasdiq: `look_at_image` 1440x900-after.png — terminal kengaygani, kartalar
2 ustunli va to'liq o'qiladigan, matn o'qishli, URL input ko'rinadani tasdiqlandi.

Skrynshotlar: `pages/studio/shots/1440x900-main.png` (oldin) → `1440x900-after.png` (keyin).

## Qoldiq (P3, keyingi pass)
- Agent kartalar ro'yxati konteyner chetida o'rtadan kesiladi (scroll normal,
  lekin gradient fade/go'ralgan mask chiroyli bo'lardi).
- Alignment near-miss'lar (F8).
- React Flow watermark.
