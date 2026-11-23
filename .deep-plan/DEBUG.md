# DEBUG

## 1. Anime.js Timer demo progress 0% bo'lib qolgan
Alomat: `verify_animejs_demo.py` da `TIMER 0% 0% ADVANCED False`, `CONSOLE_ERRORS []`.
Ildiz sabab: `loop: true` bo'lganda `self.progress` doim 0 va `self.duration` `1000000000000` (cheksizlik belgisi); haqiqiy davr `self.iterationDuration`, vaqt esa `self.currentTime`. Bu Anime.js v4 semantikasi noto'g'ri tushunilgani edi.
Dalil: `compare_timer_configs.py` barcha 5 konfiguratsiyada ishladi; instrumentatsiya `window.__demoSeen=29..47` va progress 0 ekanligini ko'rsatdi; `loop:false` da progress 0.416.
Tuzatish: `demos/timer.html` onUpdate ichida `const t = self.currentTime % self.iterationDuration; out.textContent = Math.round((t / self.iterationDuration) * 100) + '%';`
Tekshiruv: `TIMER 82% 55% ADVANCED True`, `PAUSE 59% 59% STOPPED True`, `CONSOLE_ERRORS []`.

## 2. Resurs byudjeti testlari iflos DB tufayli yiqilgan
Alomat: `3 failed, 148 passed` — testlar `Token limiti tugadi! Sarflangan: 614,644 / Limit: 500,000` olgan.
Ildiz sabab: real ish jarayonida to'plangan `resource_ledger` testlarning toza byudjet taxminini buzgan; dastlabki fixture faqat snapshot/restore qilgani uchun iflos holat saqlanib qolgan.
Dalil: xato xabari va DB hisobi; 3 ta aniq test: `test_api_task_lifecycle_endpoints`, `test_resource_limits_and_budget_enforcement`, `test_task_blocked_when_tool_budget_insufficient`.
Tuzatish: `backend/tests/conftest.py` da session `resource_state_backup` + function-scoped `isolate_resource_state` — har testdan oldin/so'ng ledger tozalanadi va settings standartga qaytariladi.
Tekshiruv: 3 ta test `3 passed in 1.75s`; to'liq `151 passed, 2 skipped`.
