# DEBUG

## 1. get_logs soxta javob qaytarardi

Alomat: `python tools.py get_logs <pid>` har doim `No active process errors reported` degan statik matnni qaytarardi.
Ildiz sabab: `tool_run_process` Popen handle'larini saqlamaydi, `tool_get_logs` esa umuman o'qish qilmay, doimiy qiymat qaytarardi.
Dalil: `tools.py:318-325` dagi funksiya 5 qatorlik hardcode edi; haqiqiy chiqish hech qayerda olinmagan.
Tuzatish: thread-safe, 500 qatorlik bufer bilan real stdout/stderr yig'ildi; jarayon registry vaqti-vaqti bilan atomik faylga saqlanadi, ikki alohida CLI jarayonida ham ishlaydi.
Tekshiruv: real ikki jarayon testida `REAL_LOG True [stdout] CLI_LOG_OK`; 20 targeted test o'tdi.

## 2. CLI status --json noto'g'ri shaklda edi

Alomat: E2E skripti 3 ta vazifani `TIMEOUT` deb yozdi, lekin DB ularning barchasi PASS ekanini ko'rsatdi.
Ildiz sabab: `conduit status <id> --json` faqat ichma-ich `{task:{status},logs}` qaytaradi; skript yuqori darajadagi `status` kutgan.
Tuzatish: CLI endi `task_id`, `status`, `evidence`, `screenshot_url`, `total_duration` ni yuqori darajada ham qaytaradi, eski ichma-ich shakl saqlanadi.
Dalil: uchala vazifa (`task_2d4f45d9`, `task_dcd44c15`, `task_50adce9f`) DB da real dalil bilan PASS.
Tekshiruv: qayta ishlangan E2E va `conduit status --json` chiqishi tekshirildi; yangi regression test qo'shildi.

## 3. JSON xato holati mashina o'qiy olmaydigan edi

Alomat: `conduit status no_such_task --json` oddiy stderr matni chiqarardi, JSON emas.
Ildiz sabab: `conduit.py::_request` HTTPError/URLError da faqat rangli xato matni yozardi; `--json` rejimi hisobga olinmagan.
Dalil: to'g'ridan-to'g'ri CLI probe xato chiqishida JSON parse qilib bo'lmagani qayd etildi.
Tuzatish: `_JSON_MODE` joriy etildi; xatolar `success:false`, `http_status`, `error` bilan JSON qilib stdout'ga chiqariladi.
Tekshiruv: real `conduit status no_such_task --json` → `http_status:404`, `error:"Task not found"`; regression test o'tdi.

## 4. Noma'lum agent bilan vazifa yaratilardi

Alomat: `conduit run no_such_agent test --json` `ok:true` va yangi task_id qaytardi.
Ildiz sabab: `backend/main.py::create_new_task` `target_agent` ni hech qayerda tekshirmagan; `manager_router` ham faqat yo'naltiradi.
Dalil: noto'g'ri agent bilan `task_27a4395e` yaratildi va DB ga yozildi.
Tuzatish: `known_agent_ids()`/`validate_agent_id()` qo'shildi; subagents/app.json ID'lari va maxsus rejimlar ruxsat etiladi, qolgani 400 bilan rad etiladi.
Tekshiruv: real CLI `success:false, http_status:400`; API testi o'tdi.

## 5. `list --json` chiqishida ANSI banner bor edi

Alomat: `conduit list --json` ni `json.loads` qilib bo'lmadi.
Ildiz sabab: `cmd_list` avval rangli banner chop etadi, keyin JSON yozardi.
Dalil: CLI probe natijasida JSON oldida rangli qatorlar ko'ringan.
Tuzatish: `cmd_list` da JSON banner oldidan chop etiladi; `--json` bo'lganda faqat JSON chiqadi.
Tekshiruv: `LIST_JSON_OK True`; regression test qo'shildi.

## 6. HTML hisobotda XSS xavfi bor edi

Alomat: vazifa matni yoki loglarga `<script>` yozilsa, HTML hisobotda xom HTML sifatida chiqishi mumkin edi.
Ildiz sabab: `generate_task_html_report` foydalanuvchi ma'lumotlarini escape qilmay to'g'ridan-to'g'ri HTML ichiga qo'yardi.
Dalil: kodda `html.escape()` yo'q edi; test vazifasida `<script>` va `<img onerror>` ishlatildi.
Tuzatish: code block, sarlavha, blockquote, ro'yxat, paragraf va title uchun `html.escape()` qo'llanildi.
Tekshiruv: xom `<script>`/`<img` yo'q, `&lt;script&gt;`/`&lt;img` borligi test bilan tasdiqlandi.

## 7. Hardcoded plugin yo'llari va jim o'chirish

Alomat: ba'zi tool'lar `C:\Users\user\agent-studio-plugin\src` ga murojaat qilardi; `tool_run_process` da `except TimeoutExpired: pass` bor edi.
Ildiz sabab: eski foydalanuvchi yo'li qolib ketgan; `test_no_silent_except` talabi buzilgan.
Dalil: `grep` uchta hardcoded yo'lni, test esa jim `pass` ni topdi.
Tuzatish: barcha yo'llar `PLUGIN_LIB` dan olingan `PLUGIN_SRC` ga almashtirildi; timeout holati `LOGGER.debug` bilan loglanadi.
Tekshiruv: hardcoded yo'l qolmadi; `test_no_silent_except` va to'liq test to'plami o'tdi.
