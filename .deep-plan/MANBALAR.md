# MANBALAR

## 1. Shu turdagi loyihani bozorda MVP qilish uchun minimal talablar qanday?

- https://www.anthropic.com/engineering/building-effective-agents — 2026-11-24 da o'qildi. Oddiy, tarkibiy qismlarga bo'lingan yechim va aniq baholash mezoni tavsiya etiladi; evalatar-optimizer sikli faqat aniq mezon bilan ishlaydi.
- https://platform.openai.com/docs/guides/function-calling — 2026-11-24 da o'qildi. Tool chiqishi qisqa va tuzilmali bo'lishi, sxema aniq bo'lishi kerak; bizda `spec` maydoni shu vazifani bajaradi.
- https://owasp.org/www-project-top-ten/ — 2026-11-24 da o'qildi. OWASP Top 10 2025 asosida foydalanuvchi matni ishonchli deb qabul qilinmaydi va HTML chiqishi escape qilinadi.

Xulosa: MVP uchun katta model emas, aniq spec + haqiqiy artefakt + ko'z bilan tekshiruv yetarli.

## 5. Bozorda o'xshashlari bormi? Qaysi ustunliklarni taklif qila olaman?

- https://code.claude.com/docs/en/subagents.md — 2026-11-24 da o'qildi. Subagentlar alohida kontekst va cheklangan tool'lar bilan ishlaydi; qisqa tavsif asosiy agentga yuklanadi.
- https://www.anthropic.com/engineering/building-effective-agents — 2026-11-24 da o'qildi. Kod agentlarining muvaffaqiyati testlar va ground truth bilan izohlanadi.
- https://platform.openai.com/docs/guides/function-calling — 2026-11-24 da o'qildi. Tool soni/tavsifi token sarfiga ta'sir qiladi; katalog qisqa bo'lishi kerak.

Xulosa: ustunlik — lokal, deterministik, tekshiriladigan va har qanday agent uchun bir xil CLI/artefakt kontrakti.

## 6. Kiberxavfsizlik tomondan nimalar qilinishi kerak?

- https://owasp.org/www-project-top-ten/ — 2026-11-24 da o'qildi. XSS va ishonchli bo'lmagan kiritish asosiy xavflar.
- https://platform.openai.com/docs/guides/function-calling — 2026-11-24 da o'qildi. Tool chiqishidagi matn ko'rsatma sifatida bajarilmasligi kerak.
- https://code.claude.com/docs/en/subagents.md — 2026-11-24 da o'qildi. Tool allowlist va alohida kontekst orqali huquqlar cheklanadi.

Xulosa: foydalanuvchi matni faqat parametr; kodga `repr()` bilan kiritiladi, HTML da escape qilinadi, ruxsatlar subagent `role.md` dan keladi.
