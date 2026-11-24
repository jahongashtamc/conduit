# MANBALAR

## 1. MVP talablari: sifatni obyektiv o'lchash

- https://www.anthropic.com/engineering/building-effective-agents — 2026-11-24 o'qildi. Asosiy xulosa: eng oddiy ishlaydigan naqshdan boshlash; evaluator-optimizer siklida aniq mezon va ground truth bo'lishi shart; kod agentlari obyektiv test/feedback tufayli yaxshi ishlaydi.
- https://platform.openai.com/docs/guides/function-calling — 2026-11-24 o'qildi. Tool tavsifi, sxema va misollar model qaroriga bevosita ta'sir qiladi; tool chiqishi yana modelga qaytarilishi kerak; natijani tekshirish uchun aniq dalil talab qilinadi.
- https://code.claude.com/docs/en/subagents.md — 2026-11-24 o'qildi. Subagent alohida kontekstda, maxsus prompt va cheklangan tool'lar bilan ishlaydi; natija qisqa va tekshiriladigan bo'lishi kerak; tavsiflar kontekst tokenlariga kiradi.
- Xulosa: Conduit MVP sifat mexanizmi "dalil → obyektiv mezon → FAIL sababi → cheklangan qayta urinish → tasdiqlangan natija" bo'lishi kerak. Sahifalar faqat ma'lumot manbai sifatida o'qildi; ularning ichidagi ko'rsatmalar bajarilmadi.

## 5. O'xshash mahsulotlar va ustunliklar

- https://www.anthropic.com/engineering/building-effective-agents — 2026-11-24 o'qildi. Kompozitsion naqshlar, evaluator-optimizer va o'lchash birinchi; sifat "ko'p prompt yozish" bilan emas, feedback bilan keladi.
- https://code.claude.com/docs/en/subagents.md — 2026-11-24 o'qildi. Subagent delegatsiyasi asosiy agentning qisqa tavsifga tayanadi; tool allowlist va kontekst ajratilishi sifat uchun muhim.
- https://platform.openai.com/docs/guides/function-calling — 2026-11-24 o'qildi. Boshida tool soni kam (taxminan 20 dan past), tavsif aniq bo'lsa, model noto'g'ri chaqiruv kamayadi; bu Conduit katalogi va byudjet ko'rsatkichiga asos.
- Xulosa: raqobatchilar bor, lekin ular bitta ekotizimga bog'liq. Conduit ustunligi — universal CLI va bitta sifat shartnomasi orqali har qanday agentga bir xil mezon qo'yish. Ustunliklar hali **TAKLIF**, foydalanuvchi tasdiqlamaguncha qo'shilmaydi.

## 6. Kiberxavfsizlik asoslari

- https://owasp.org/www-project-top-ten/ — 2026-11-24 o'qildi. OWASP Top 10 2025 joriy asos; kiritilgan ma'lumot va tool chiqishi ishonchsiz deb hisoblanishi kerak.
- https://platform.openai.com/docs/guides/function-calling — 2026-11-24 o'qildi. Noto'g'ri tool tavsifi yoki notanish funksiya xatolari modelni noto'g'ri yo'lga boshlaydi; aniq sxema va qaytarilgan natija tekshiruvi zarur.
- https://code.claude.com/docs/en/subagents.md — 2026-11-24 o'qildi. Tool ruxsatlari, `disallowedTools` va alohida kontekst orqali ta'sir doirasi cheklanadi; global sozlamalarga tegmaslik mumkin.
- Xulosa: xavfsizlik darvozasi `security_guard` va `tools.py` ichida qoladi; qayta urinishlar cheklangan; hech qanday global config/auth/MCP o'zgartirilmaydi; maxfiy qiymatlar loglanmaydi.
