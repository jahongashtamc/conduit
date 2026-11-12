"""PTY env + conduit CLI testi (terminal ichida)."""
import asyncio
import re

URI = "ws://127.0.0.1:8000/ws/terminal"


def _first_task_id() -> str:
    """Backenddagi mavjud task_id ni oladi (qattiq kodlangan ID o'rniga)."""
    import json
    import urllib.request

    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/api/tasks", timeout=10) as resp:
            tasks = json.load(resp)
    except Exception as exc:
        print(f"[test] /api/tasks olinmadi: {exc}")
        return ""
    if isinstance(tasks, list) and tasks:
        return str(tasks[0].get("task_id") or tasks[0].get("id") or "")
    return ""


async def read_until(ws, needles, timeout, accumulate):
    end = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < end:
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=max(0.5, end - asyncio.get_event_loop().time()))
        except asyncio.TimeoutError:
            return False
        accumulate.append(msg)
        joined = "".join(accumulate)
        for n in needles:
            if re.search(n, joined):
                return True
    return False


async def main():
    import websockets
    results = []
    async with websockets.connect(URI) as ws:
        buf = []
        ok = await read_until(ws, [r"PS .+>"], 25, buf)
        results.append(("PowerShell prompt", ok))
        await ws.send("cls\r")
        await asyncio.sleep(2)
        buf.clear()

        # env o'zgaruvchilar
        await ws.send("echo API=$env:CONDUIT_API SESSION=$env:CONDUIT_SESSION\r")
        ok = await read_until(ws, [r"API=http://127\.0\.0\.1:8000", r"SESSION=\w+"], 15, buf)
        results.append(("CONDUIT_API + CONDUIT_SESSION env", ok))
        env_out = "".join(buf)
        buf.clear()

        # conduit PATH'da
        await ws.send("conduit list --json\r")
        ok = await read_until(ws, [r'"subagents"'], 20, buf)
        results.append(("conduit list --json (PATH'dan)", ok))
        list_out = "".join(buf)
        buf.clear()

        # conduit status --json (mavjud task_id bilan; qattiq kodlangan ID eskirgan)
        task_id = _first_task_id()
        if task_id:
            await ws.send(f"conduit status {task_id} --json\r")
            ok = await read_until(ws, [r'"task_id"'], 20, buf)
            results.append((f"conduit status --json ({task_id})", ok))
        else:
            results.append(("conduit status --json (task topilmadi)", False))

    print("===== NATIJALAR =====")
    for name, okk in results:
        print(f"[{'OK' if okk else 'XATO'}] {name}")
    print("\n--- env ---")
    print(env_out[-200:].replace("\x1b", "^[").replace("\r\n", "\n"))
    print("\n--- list (birinchi 200) ---")
    print(list_out[:200].replace("\x1b", "^[").replace("\r\n", "\n"))


asyncio.run(main())
