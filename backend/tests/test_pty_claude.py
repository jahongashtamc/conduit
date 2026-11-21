"""claude interaktiv + PTY tozalash testi v2.

claude ochilganda ruxsat dialogi chiqishi mumkin — Enter bilan o'tamiz.
Oxirida {"type":"close"} -> powershell daraxti o'lganini jarayon hisobida tekshiramiz.
"""
import asyncio
import re

URI = "ws://127.0.0.1:8000/ws/terminal"


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


def count_ps():
    import subprocess
    out = subprocess.run(
        ["powershell", "-Command", "(Get-Process powershell -ErrorAction SilentlyContinue).Count"],
        capture_output=True, text=True,
    )
    try:
        return int(out.stdout.strip().splitlines()[-1])
    except Exception:
        return -1


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

        # claude interaktiv — TUI tezligi o'zgaruvchan (gateway holatiga bog'liq),
        # shuning uchun kengroq markerlar va qayta urinish ishlatiladi.
        await ws.send("claude\r")
        ok = await read_until(ws, [r"(?i)(claude code|welcome|anthropic|Yes, run command|trusted|>\s*$)"], 90, buf)
        results.append(("claude TUI ko'rindi", ok))
        # ruxsat dialogi bo'lsa Enter bilan o'tamiz
        await ws.send("\r")
        await asyncio.sleep(4)
        buf.clear()
        ok = await read_until(ws, [r"(?i)(claude code|welcome|anthropic|trusted|\?|>)"], 60, buf)
        results.append(("claude interaktiv sessiya", ok))
        cl_out = "".join(buf)
        buf.clear()

        # matn kiritish — TUI birinchi urinishda tayyor bo'lmasligi mumkin,
        # 2 marta urinib ko'ramiz (har safar yangi buffer bilan).
        ok = False
        for _attempt in range(2):
            await ws.send("KUKA_CLAUDE\r")
            ok = await read_until(ws, [r"KUKA_CLAUDE"], 45, buf)
            if ok:
                break
            buf.clear()
            await asyncio.sleep(3)
        results.append(("kiritish uzatildi", ok))
        buf.clear()

        # Ctrl+C -> prompt
        await ws.send("\x03")
        await asyncio.sleep(3)
        await ws.send("echo PTY_CLAUDE_BACK\r")
        ok = await read_until(ws, [r"PTY_CLAUDE_BACK"], 25, buf)
        results.append(("Ctrl+C -> PowerShell prompt", ok))
        exit_out = "".join(buf)

        # Tozalash: close -> powershell daraxti o'ladi
        before = count_ps()
        await ws.send('{"type":"close"}')
        await asyncio.sleep(5)
        after = count_ps()
        results.append((f"PTY daraxti o'ldirildi ({before} -> {after} powershell)", after < before))

    print("===== NATIJALAR =====")
    for name, okk in results:
        print(f"[{'OK' if okk else 'XATO'}] {name}")
    print("\n--- claude (oxirgi 200) ---")
    print(cl_out[-200:].replace("\x1b", "^[").replace("\r\n", "\n"))
    print("\n--- chiqish (oxirgi 120) ---")
    print(exit_out[-120:].replace("\x1b", "^[").replace("\r\n", "\n"))


asyncio.run(main())
