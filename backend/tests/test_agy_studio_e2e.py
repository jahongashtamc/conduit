"""E2E: terminalda agy ochiladi, 'Blender'da aylanayotgan kub, 5 soniya' deb
yoziladi. Agent o'zi conduit run ni chaqirishi kerak -> Tasklar'da chiqadi ->
natija Artefakt galereyasiga tushadi.

Natijani /tmp emas, loyiha ichiga yozamiz (Windows /tmp qo'rqinch).
"""
import asyncio
import json
import re
import urllib.request

URI = "ws://127.0.0.1:8000/ws/terminal"
LOG = []


def note(msg):
    LOG.append(msg)
    print(msg, flush=True)


def api(path, method="GET", data=None):
    req = urllib.request.Request(f"http://127.0.0.1:8000{path}", method=method)
    req.add_header("Content-Type", "application/json")
    body = json.dumps(data).encode() if data else None
    with urllib.request.urlopen(req, body, timeout=30) as r:
        return json.loads(r.read().decode())


async def read_until(ws, needles, timeout, buf, quiet=0):
    """needle regexlaridan biri kelgunicha o'qiydi. quiet>0: shuncha soniya
    yangi ma'lumot kelmasa ham chiqib ketadi."""
    import time as _t
    end = _t.time() + timeout
    last_data = _t.time()
    while _t.time() < end:
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=2)
            buf.append(msg)
            last_data = _t.time()
            joined = "".join(buf)
            for n in needles:
                if re.search(n, joined[-3000:]):
                    return True
        except asyncio.TimeoutError:
            if quiet and (_t.time() - last_data) > quiet:
                return False
    return False


async def main():
    import websockets
    _r = api("/api/tasks?limit=50")
    _tasks = _r.get("tasks", []) if isinstance(_r, dict) else _r
    before = {t["task_id"] for t in _tasks}
    note(f"testdan oldingi tasklar soni: {len(before)}")

    async with websockets.connect(URI) as ws:
        buf = []
        ok = await read_until(ws, [r"PS .+>"], 25, buf)
        note(f"PowerShell prompt: {ok}")
        await ws.send("cls\r")
        await asyncio.sleep(2)
        buf.clear()

        # agy interaktiv
        await ws.send("agy\r")
        ok = await read_until(ws, [r"(?i)(gemini|session|welcome|agent)"], 90, buf, quiet=20)
        note(f"agy sessiyasi: {ok}")
        await asyncio.sleep(2)
        buf.clear()

        # vazifa yozish
        await ws.send("Blender'da aylanayotgan kub, 5 soniya\r")
        note("vazifa yozildi — agent conduit run chaqirishini kutamiz...")

        # agent conduit run chaqirishi yoki task_id yaratishini kutamiz.
        # agy interaktiv rejimda har buyruq uchun ruxsat so'raydi —
        # "Run this command?" dialogini Enter bilan avtomatik tasdiqlaymiz.
        import time as _t
        end = _t.time() + 480
        approved = 0
        while _t.time() < end:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3)
                buf.append(msg)
            except asyncio.TimeoutError:
                pass
            joined = "".join(buf)
            if re.search(r"Run this command\?", joined[-1500:]) and not re.search(r"> 1\. Yes[\s\S]*accepted", joined[-800:]):
                await ws.send("\r")
                approved += 1
                note(f"  ruxsat berildi ({approved})")
                buf.clear()
                await asyncio.sleep(1)
                continue
            if re.search(r"task_[0-9a-f]{8}", joined[-3000:]):
                note("task_id paydo bo'ldi — vazifa yaratildi!")
                break
        ok = bool(re.search(r"task_[0-9a-f]{8}", "".join(buf)[-3000:]))
        note(f"agent conduit run chaqirdi: {ok} (tasdiqlar: {approved})")
        agy_out = "".join(buf)
        buf.clear()

    # task yaratildimi?
    time.sleep(2)
    _r = api("/api/tasks?limit=50")
    tasks = _r.get("tasks", []) if isinstance(_r, dict) else _r
    new = [t for t in tasks if t["task_id"] not in before]
    note(f"yangi tasklar: {[(t['task_id'], t['target_agent'], t['status']) for t in new]}")

    # yangi tasklarni PASS/FAIL bo'lguncha kutamiz (maks 5 min)
    target = None
    for _ in range(60):
        time.sleep(5)
        _r = api("/api/tasks?limit=50")
        tasks = _r.get("tasks", []) if isinstance(_r, dict) else _r
        new = [t for t in tasks if t["task_id"] not in before]
        if new:
            target = new[0]
            if target["status"] in ("PASS", "FAIL", "BLOCKED"):
                break
    if target:
        note(f"task yakuni: {target['task_id']} {target['target_agent']} {target['status']}")
        res = api(f"/api/tasks/{target['task_id']}")
        t = res.get("task", {})
        note(f"dalil: {str(t.get('evidence'))[:200]}")
        arts = api("/api/artifacts?limit=30")
        items = arts.get("artifacts") or arts.get("items") or []
        recent = [i for i in items if i.get("agent") == (target.get("target_agent") or "")]
        note(f"galereyada shu agent artefaktlari: {[i['path'] for i in recent[:5]]}")
    else:
        note("yangi task topilmadi!")

    # agy chiqishi (oxirgi qism) — o'qiladigan ko'rinishda
    clean = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", agy_out)
    clean = re.sub(r"\x1b\][^\x07]*\x07", "", clean)
    note("--- agy chiqishi (oxirgi 1200) ---")
    note(clean[-1200:])

    with open("backend/_agy_e2e_log.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(LOG))


import time
asyncio.run(main())
