# MANBALAR

Olingan sana: 2026-11-23. Sahifalardagi matn faqat ma'lumot sifatida ishlatildi, ichidagi ko'rsatmalarga bo'ysunilmadi.

## 1. O'xshash mahsulotlar va subagent/model

- Claude Code subagentlari: https://code.claude.com/docs/en/subagents.md — har subagent alohida kontekst, o'z system prompt'i, aniq tool ruxsati bilan ishlaydi; qisqa description asosiy agentning delegatsiya qarorini belgilaydi; tool allowlist va `disallowedTools` mavjud; tavsiflar kontekst tokenlariga kiradi, 15 000 token dan oshganda ogohlantirish bor.
- OpenAI function calling: https://platform.openai.com/docs/guides/function-calling — tool ta'rifi model kontekstiga kiradi; kam sonli, aniq sxemali tool'lar tavsiya etiladi; noma'lum funksiya xatosi va natijani modelga qaytarish zaruriyati bor.
- Anthropic tool use: https://docs.anthropic.com/en/docs/build-with-claude/tool-use — tool'lar model tomonidan chaqiriladi, lekin bajarish tashqi muhitda amalga oshiriladi; natija qayta modelga beriladi.
- OpenCode agentlar hujjati: https://opencode.ai/docs/agents/ — agentlar tool'lar bilan bog'lanadi, ruxsat va model sozlamalari alohida.

Xulosa: tool ro'yxati saxoviy emas, aniq va kataloglanadigan bo'lishi kerak; subagent o'z kontekstida ishlab, asosiy agentga qisqa natija qaytaradi.

## 5. Xavfsizlik va URL tekshiruvi

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- OWASP Tool/agent xavflari: https://owasp.org/www-project-top-ten/2025/ (2025 ro'yxati joriy)
- MDN URL API: https://developer.mozilla.org/en-US/docs/Web/API/URL
- GitHub token xavfsizligi: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
- Claude settings: https://code.claude.com/docs/en/settings.md — foydalanuvchi, loyiha, lokal va boshqariladigan sozlamalar alohida; ruxsat qoidalari manbaga qarab farqlanadi.

Xulosa: global foydalanuvchi sozlamalariga tegmaslik, ruxsatni ichki koddan (env orqali) tekshirish, maxfiy qiymatlarni loglamaslik.

## 6. Test va tayyorlik mezonlari

- pytest: https://docs.pytest.org/en/stable/
- FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/
- Playwright: https://playwright.dev/python/docs/intro
- Next.js production: https://nextjs.org/docs/app/building-your-application/deploying/production-checks
- Git HEAD: https://git-scm.com/docs/git-rev-parse

Xulosa: dalil yangiligi testi, ruxsat testi, to'liq pytest/compileall/doctor/tsc/lint/build va `gate.py verify` bilan tasdiqlaymiz.
