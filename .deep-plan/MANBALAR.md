# MANBALAR

## 1. MVP talablari

- https://ffmpeg.org/ffmpeg-filters.html#concat — 2026-11-24 da o'qildi: concat/trim/setpts/atrim/fade real kesish va timeline uchun rasmiy mexanizm. Xulosa: tasodifiy gradient video montaj emas; kirish media va aniq kesimlar shart.
- https://www.figma.com/developers/api — 2026-11-24 da o'qildi: real fayl/komponent ma'lumoti `GET /v1/files/:key` va token/OAuth2 orqali olinadi. Xulosa: hardcode token/spec foydalanuvchi talabiga javob emas.
- https://www.anthropic.com/engineering/building-effective-agents — 2026-11-24 da o'qildi: evaluator-optimizer aylanishida aniq mezon va muhitdan olingan haqiqiy dalil kerak. Xulosa: test yashiligi o'zi sifat dalili emas.
- https://code.claude.com/docs/en/subagents.md — 2026-11-24 da o'qildi: subagent alohida kontekst va cheklangan tool bilan ishlaydi. Xulosa: agentga faqat matn yozish natijani o'zgartirmaydi, tool va tekshiruv ham tuzatilishi kerak.

## 5. O'xshash mahsulotlar va ustunliklar

- https://ffmpeg.org/ffmpeg-filters.html#concat — 2026-11-24: bir nechta kirish oqimini vaqt bo'yicha birlashtirish standarti.
- https://docs.github.com/en/rest/search/search — 2026-11-24: code search autentifikatsiyasiz 401/403 qaytaradi va natijalar relevance bo'yicha tanlanadi. Xulosa: bizning 401 xatomiz kutilgan, lekin natijani "topildi" deb taqdim etish noto'g'ri.
- https://platform.openai.com/docs/guides/function-calling — 2026-11-24: tool tavsifi va sxemasi aniq bo'lishi, natija modelga qaytishi kerak. Xulosa: rejim/tool nomlari va xato sabablari aniq bo'lmasa agent noto'g'ri yo'l tanlaydi.
- https://www.anthropic.com/engineering/building-effective-agents — 2026-11-24: eng oddiy ishlaydigan yechimdan boshlash va o'lchash tavsiya qilinadi.

## 6. Kiberxavfsizlik

- https://owasp.org/www-project-top-ten/ — 2026-11-24: OWASP Top 10 2025 joriy; kiritilgan ma'lumot, autentifikatsiya va konfiguratsiya xavfsizligi asosiy mezonlar.
- https://docs.github.com/en/rest/search/search — 2026-11-24: search API kalit/log xavfsizligi va rate limit qoidalari bor; kalit hech qachon chiqishga yozilmaydi.
- https://www.figma.com/developers/api — 2026-11-24: access token faqat server tomonida ishlatiladi, mijoz logiga chiqarilmaydi.
- https://platform.openai.com/docs/guides/function-calling — 2026-11-24: tool chiqishi ishonchli ma'lumot sifatida qaytariladi, lekin undagi matn buyruq sifatida bajarilmaydi.
