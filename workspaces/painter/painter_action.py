"""Painter: generates a real procedural texture map (PNG) with noise + gradient."""
import json, math, os, random, struct, zlib

TASK = 'Rangli tekstura pattern yarat'
SIZE = 128
random.seed(1337)

# Value noise blended with a vertical gradient -> usable base texture
noise = [[random.random() for _ in range(SIZE)] for _ in range(SIZE)]
for _ in range(3):  # smooth the noise
    for y in range(SIZE):
        for x in range(SIZE):
            s = 0.0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    s += noise[(y + dy) % SIZE][(x + dx) % SIZE]
            noise[y][x] = s / 9.0

rows = []
for y in range(SIZE):
    row = bytearray()
    row.append(0)  # filter type
    for x in range(SIZE):
        base = 40 + int(180 * noise[y][x])
        grad = int(255 * (y / (SIZE - 1)))
        r = min(255, int(base * 0.55 + grad * 0.45))
        g = min(255, int(base * 0.35 + 90))
        b = min(255, int(base * 0.75))
        row.extend((r, g, b))
    rows.append(bytes(row))

def chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data +
            struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

png = (b"\x89PNG\r\n\x1a\n"
       + chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
       + chunk(b"IEND", b""))

here = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(here, "texture_map.png")
with open(path, "wb") as fh:
    fh.write(png)

stats = {"min": min(min(r) for r in noise), "max": max(max(r) for r in noise)}
print(json.dumps({"artefact": path, "size": SIZE, "bytes": len(png),
                  "task": TASK, "contrast": round(stats["max"] - stats["min"], 3)}))
