"""H bosqich — yakuniy qabul sinovi (haqiqiy agent terminal oqimi).

Har bir agent uchun: PTY terminalda agent CLI qo'llaniladi (agy / claude /
codex), agent ichida `conduit run inspector ...` yoziladi, vazifa paydo
bo'ladi, jonli sahna (/ws/task/{id}) hodisalarni ko'rsatadi, natija PASS
bo'ladi va dalil task'ga yoziladi.

Terminal WS protokoli: xom matn (input va output JSON emas).

Ishga tushirish: backend 8000-portda jonli bo'lishi shart.
    PYTHONIOENCODING=utf-8 python backend/tests/test_acceptance_h.py <engine>
"""
import asyncio
import json
import re
import sys
import urllib.request

URI = "ws://127.0.0.1:8000/ws/terminal"
API = "http://127.0.0.1:8000"

LAUNCHERS = {
    "agy": "agy",
    "claude_code": "claude --dangerously-skip-permissions",
    "codex_cli": "codex --dangerously-bypass-approvals-and-sandbox",
}
APPROVAL_KEY = {"agy": "1\r", "claude_code": None, "codex_cli": None}


def api(path, method="GET", data=None):
    req = urllib.request.Request(f"{API}{path}", method=method)
    req.add_header("Content-Type", "application/json")
    body = json.dumps(data).encode() if data else None
    with urllib.request.urlopen(req, body, timeout=30) as r:
        return json.loads(r.read().decode())


async def read_until(ws, needles, timeout, buf, quiet=12.0):
    """needle regexlaridan biri kelgunicha o'qiydi (xom matn). None = timeout."""
    import time as _t
    end = _t.time() + timeout
    last = _t.time()
    while _t.time() < end:
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=1.0)
        except asyncio.TimeoutError:
            if _t.time() - last > quiet:
                return None
            continue
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        buf.append(raw)
        joined = "".join(buf)
        for pat in needles:
            if re.search(pat, joined):
                return pat
        last = _t.time()
    return None


def _created_after(task_rec, t_start):
    """Task yaratilish vaqti sinov boshlanishidan keyinmi?"""
    import datetime as _dt
    raw = task_rec.get("created_at") or task_rec.get("timestamp") or ""
    if not raw:
        return False
    try:
        ts = _dt.datetime.fromisoformat(str(raw).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return False
    return ts >= t_start - 5


async def main(engine_name):
    import websockets

    api("/api/engine/select", "POST", {"engine": engine_name})
    print(f"[0] Dvigatel tanlandi: {engine_name}", flush=True)
    import time as _t0
    t_start = _t0.time()
    results = {}

    async with websockets.connect(URI, max_size=5 * 1024 * 1024) as ws:
        buf = []
        # Terminal umumiy/persistan — avval ishlayotgan CLI'dan chiqamiz
        # (\x03 = interrupt, \x04 = EOF/claude REPL'dan chiqish)
        for _ in range(3):
            await ws.send("\x03")
            await asyncio.sleep(1.5)
            await ws.send("\x04")
            await asyncio.sleep(2)
        await read_until(ws, [r"PS .+>"], 20, buf, quiet=6)
        results["prompt"] = bool(buf)
        print("[1] PowerShell prompt ko'rindi" if buf else "[1] DIQQAT: prompt ko'rinmadi", flush=True)
        buf.clear()

        # Agent CLI'ni terminalda ishga tushirish
        await ws.send(LAUNCHERS[engine_name] + "\r")
        tui_pat = await read_until(ws, [r"❯", r"shortcuts", r"Shortcuts", r"Tips", r"\?"], 60, buf, quiet=15)
        results["tui"] = bool(tui_pat)
        print(f"[2] Agent CLI terminalda ishga tushdi ({LAUNCHERS[engine_name]})", flush=True)
        buf.clear()

        # Agent ichida conduit run yozamiz
        marker = f"ACCEPT_{engine_name.upper().replace('_', '')}"
        goal = f"Salomatlik tekshiruvi {marker}: /api/health 200 qaytarsin"
        await ws.send(f'conduit run inspector "{goal}"\r')

        # Tasdiqlash menyusi chiqsa (agy) — "Yes" ni tanlaymiz
        if APPROVAL_KEY[engine_name]:
            seen = await read_until(ws, [r"Navigate"], 60, buf, quiet=8)
            if seen:
                await ws.send(APPROVAL_KEY[engine_name])
                print("[3] Agent ruxsat so'radi -> Yes tanlandi", flush=True)

        # Yangi task'ni API orqali aniqlaymiz (sinov boshlanganidan keyin yaratilganini olamiz)
        task_id = None
        import time as _t
        deadline = _t.time() + 150
        while _t.time() < deadline:
            await asyncio.sleep(4)
            try:
                tasks = api("/api/tasks")
                for t in tasks:
                    tid = t.get("task_id") or ""
                    if tid.startswith("task_") and _created_after(t, t_start):
                        task_id = tid
                        break
            except Exception as exc:
                print(f"    [poll xato] {exc}", flush=True)
            if task_id:
                break
        results["task_created"] = bool(task_id)
        print(f"[4] conduit run agent orqali -> task_id: {task_id}", flush=True)
        if not task_id:
            print("[4] XATO. Oxirgi terminal chiqishi: " + "".join(buf)[-500:], flush=True)
            return 1
        buf.clear()

        # Agent CLI'dan chiqib, PowerShell'ga qaytamiz (terminal erkin qolsin)
        await ws.send("\x03")
        await asyncio.sleep(2)
        await ws.send("exit\r")
        await asyncio.sleep(1)

    # 5) Jonli sahna: /ws/task/{task_id} hodisalari
    import websockets
    events = {"log": 0, "preview_frame": 0, "completed": 0, "other": 0}
    status = None
    async with websockets.connect(f"ws://127.0.0.1:8000/ws/task/{task_id}", max_size=10 * 1024 * 1024) as tws:
        deadline = asyncio.get_event_loop().time() + 420
        while asyncio.get_event_loop().time() < deadline:
            try:
                raw = await asyncio.wait_for(tws.recv(), timeout=25)
            except asyncio.TimeoutError:
                continue
            try:
                msg = json.loads(raw)
            except (json.JSONDecodeError, TypeError, ValueError):
                continue
            t = msg.get("type", "")
            if t == "log":
                events["log"] += 1
            elif t == "preview_frame":
                events["preview_frame"] += 1
            elif t == "task_completed":
                events["completed"] += 1
                status = msg.get("status")
                break
            elif t == "snapshot":
                status = msg.get("task", {}).get("status")
            else:
                events["other"] += 1
    print(f"[5] Jonli sahna: {events}, holat: {status}", flush=True)

    # 6) Yakuniy holat + dalil
    task = api(f"/api/tasks/{task_id}")
    tdata = task.get("task", task)
    final = tdata.get("status")
    evidence = (tdata.get("evidence") or "")[:140]
    print(f"[6] Yakun: {final} | dalil: {evidence}", flush=True)

    ok = events["log"] >= 1 and status is not None
    verdict = "OK" if (ok and final == "PASS") else ("QISMIY" if ok else "XATO")
    print(f"=== {engine_name}: {verdict} ===", flush=True)
    return 0 if (ok and final == "PASS") else 1


if __name__ == "__main__":
    engine = sys.argv[1] if len(sys.argv) > 1 else "claude_code"
    raise SystemExit(asyncio.run(main(engine)))
