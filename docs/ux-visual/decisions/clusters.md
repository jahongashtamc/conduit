# Qarorlar (C1–C6)

Har bir klaster uchun A (minimal) / B (qayta tuzish) / C (konventsiya) ko'rib
chiqildi. Qisqacha:

## C1 Terminal — **B tanlandi: sudraladigan ajratgich + flex nisbati**
- A: faqat flex-[1]→flex-[2] almashtirish — yaxshi, lekin foydalanuvchiga qolgan
  nisbatni o'zgartirish imkonsiz (terminal yoki miya doim jabr qilinadi).
- **B: terminal flex-[3] default + terminal/miya orasiga draggable splitter
  (0.25–0.75 clamp). ResizeObserver allaqachon fit qiladi — PTY resize
  websocket orqali avtomatik uzatiladi.** Terminal asosiy ish maydoni —
  foydalanuvchi nazorati eng to'g'ri yechim (VS Code panel modeli).
- C: terminalni alohida to'liq balandlikka chiqarish — miya tuguni yo'qoladi,
  ma'lumot yo'qotiladi. Rad.
- Effort: ~60 satr. Risk: past (mavjud ResizeObserver fit qiladi).

## C2 Agent kartalari — **A: grid-cols-2 + kartalar ichki zichligi**
- 560px ustunda 2 ustun → ~270px karta, nomlar to'liq o'qiladi.
- C (tab'ga ko'chirish) rad — kontekst uzoqlashadi.

## C3 Tipografiya — **A: global minimum 11px**
- `text-[9px]`→`text-[11px]`, `text-[10px]`→`text-[11px]` (130+ joy, sed bilan).
- Ierarxiya weight/color orqali saqlanadi; scale {11,12,14} ga qisqaradi.
- Risk: ba'zi zich joylarda o'ralish (wrap) — skrinshot bilan tekshiriladi.

## C4 Brauzer bo'sh holati — **B: URL input + quick actions**
- Bo'sh panelga `POST /api/browser/navigate` ga ulangan URL kiritish qatori va
  2 ta quick action (screenshot, conduit list) qo'shiladi — bo'sh joy amalga aylanadi.
- A (faqat ikonka kichraytirish) rad — muammoni hal qilmaydi.

## C5 Nishonlar — **A: `py-0.5`→`py-1`, `p-1`→`p-1.5` eng kichik tugmalarda**
- Faqat audited elementlar: titlebar rejim tugmalari, "Yangi vazifa", terminal
  chips, SFX, terminal input (h-7).

## C6 Kontrast — **A: slate-600→slate-400 matn, slate-700 ajratgich→slate-600**
- Faqat matn sifatida ishlatilgan joylar; dekorativ borderlar qoladi.

## Test rejasi
1. `npm run build` — 0 xato.
2. agent-browser bilan 1440×900 qayta o'lchov: terminal ≥ 300px, 9/10px matn yo'q,
   bo'sh holatda URL input ko'rinadi, tugmalar ≥ 24px.
3. Yangi skrinshot + look_at_image taqqoslash.
4. Terminal splitter drag testi.
