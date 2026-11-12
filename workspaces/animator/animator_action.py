"""Animator: builds a keyframe timeline and bakes sampled frames."""
import json, math, os

TASK = 'keyframe animatsiya yarat'
FRAMES = 24
FPS = 24

def ease_in_out(t):
    return t * t * (3.0 - 2.0 * t)

keys = [
    {"frame": 0, "prop": "opacity", "value": 0.0},
    {"frame": FRAMES // 2, "prop": "opacity", "value": 1.0},
    {"frame": FRAMES, "prop": "opacity", "value": 0.0},
    {"frame": 0, "prop": "scale", "value": 0.8},
    {"frame": FRAMES, "prop": "scale", "value": 1.2},
]

samples = []
for f in range(FRAMES + 1):
    t = f / FRAMES
    samples.append({"frame": f, "opacity": round(ease_in_out(t), 4),
                    "scale": round(0.8 + 0.4 * ease_in_out(t), 4),
                    "rot": round(360.0 * t, 2)})

out = {"task": TASK, "fps": FPS, "duration": round(FRAMES / FPS, 3),
       "keyframes": keys, "samples": samples}
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "timeline.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2)
print(json.dumps({"artefact": path, "keyframes": len(keys), "frames": len(samples),
                  "duration_s": out["duration"]}))
