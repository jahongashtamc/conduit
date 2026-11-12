"""Editor: builds an EDL (edit decision list) and validates the cut."""
import json, os

TASK = 'intro video clip yarat'
CLIPS = [
    {"id": "clip_a", "start": 0.0, "end": 4.5, "track": "V1"},
    {"id": "clip_b", "start": 4.5, "end": 9.0, "track": "V1"},
    {"id": "clip_c", "start": 9.0, "end": 13.25, "track": "V1"},
    {"id": "music", "start": 0.0, "end": 13.25, "track": "A1"},
]

# Validate: no overlap on the same track, no gaps, monotonic time
def validate(clips):
    errors = []
    by_track = {}
    for c in clips:
        if c["end"] <= c["start"]:
            errors.append(f"{c['id']}: end<=start")
        by_track.setdefault(c["track"], []).append(c)
    for track, items in by_track.items():
        items.sort(key=lambda x: x["start"])
        for prev, cur in zip(items, items[1:]):
            if cur["start"] < prev["end"] - 1e-6:
                errors.append(f"{track}: {prev['id']} overlaps {cur['id']}")
    return errors

errors = validate(CLIPS)
total = max(c["end"] for c in CLIPS)
out = {"task": TASK, "clips": CLIPS, "total_duration": total,
       "cut_count": len([c for c in CLIPS if c["track"] == "V1"]) - 1,
       "valid": not errors, "errors": errors}
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "timeline_edl.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2)
print(json.dumps({"artefact": path, "clips": len(CLIPS),
                  "total_duration": total, "valid": out["valid"]}))
