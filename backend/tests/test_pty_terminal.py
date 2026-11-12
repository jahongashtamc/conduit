"""PTY terminal testi v2: aniq markerlar bilan.

1) PowerShell prompt
2) 'agy' interaktiv sessiya
3) agentga aniq so'z yozamiz (KUKA_MARKER) va javobda shu so'zni kutamiz
4) Ctrl+C -> keyin 'echo PTY_BACK' yozamiz; PowerShell echo qilsa prompt qaytgan
"""
import asyncio
import re
import sys

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

        # agy interaktiv
        await ws.send("agy\r")
        ok = await read_until(ws, [r"(?i)(gemini|model|session|agent|welcome)"], 90, buf)
        results.append(("agy sessiyasi ochildi", ok))
        agy_out = "".join(buf)
        buf.clear()

        # aniq marker bilan so'rov
        await ws.send("KUKA_MARKER so'zini aynan takrorla\r")
        ok = await read_until(ws, [r"KUKA_MARKER"], 150, buf)
        results.append(("agent javobida marker bor", ok))
        resp_out = "".join(buf)
        buf.clear()

        # Ctrl+C -> keyin echo bilan prompt tekshirish
        await ws.send("\x03")
        await asyncio.sleep(3)
        await ws.send("echo PTY_BACK\r")
        ok = await read_until(ws, [r"PTY_BACK"], 25, buf)
        results.append(("Ctrl+C -> PowerShell prompt (echo ishledi)", ok))
        exit_out = "".join(buf)

    print("===== NATIJALAR =====")
    for name, okk in results:
        print(f"[{'OK' if okk else 'XATO'}] {name}")
    print("\n--- agy (oxirgi 250) ---")
    print(agy_out[-250:].replace("\x1b", "^[").replace("\r\n", "\n"))
    print("\n--- javob (oxirgi 250) ---")
    print(resp_out[-250:].replace("\x1b", "^[").replace("\r\n", "\n"))
    print("\n--- chiqish (oxirgi 250) ---")
    print(exit_out[-250:].replace("\x1b", "^[").replace("\r\n", "\n"))


asyncio.run(main())
