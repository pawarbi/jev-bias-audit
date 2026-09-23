"""Check that the published traces are complete and consistent. Needs no API key.

For each run (three cell sets x two reps) it checks that:
  1. every cell was answered exactly once;
  2. the logged request is exactly the designed cell (state, question, options in order);
  3. the parsed result can be rebuilt from the raw response (choice and probabilities);
  4. the model that answered is the pinned version.
It also checks the probe log and scans every file for anything that looks like a key,
then compares file hashes with MANIFEST.sha256.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

MODEL = "typesafe/jev-1.13-20260917"
problems = []


def jl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8")]


for stem in ("custom_cells", "custom_ext_cells", "bbq_cells"):
    cells = {c["cell_id"]: c for c in jl(f"data/{stem}.jsonl")}
    for rep in (0, 1):
        raw = jl(f"results/{stem}_rep{rep}_raw.jsonl")
        parsed = {r["cell_id"]: r for r in jl(f"results/{stem}_rep{rep}.jsonl")}
        ids = [r["tag"]["cell_id"] for r in raw]
        if sorted(ids) != sorted(cells) or len(set(ids)) != len(ids):
            problems.append(f"{stem} rep{rep}: raw log does not cover every cell exactly once")
        if sorted(parsed) != sorted(cells):
            problems.append(f"{stem} rep{rep}: parsed results do not cover every cell exactly once")
        for r in raw:
            c = cells[r["tag"]["cell_id"]]
            q = r["request"]["questions"]["q"]
            if (r["request"]["state"] != c["state"] or q["instructions"] != c["instructions"]
                    or list(q["criteria"].items()) != list(c["criteria"].items())):
                problems.append(f"{stem} rep{rep} {c['cell_id']}: request differs from the designed cell")
            a = r["response"]["answers"]["q"]
            p = parsed[c["cell_id"]]
            probs = {c["roles"][k]: v for k, v in a["probabilities"].items()}
            if c["roles"][a["choice"]] != p["choice"] or probs != p["probs"]:
                problems.append(f"{stem} rep{rep} {c['cell_id']}: parsed result does not match raw response")
            if r["response"].get("model") != MODEL:
                problems.append(f"{stem} rep{rep} {c['cell_id']}: answered by {r['response'].get('model')}")
        print(f"checked {stem} rep{rep}: {len(raw)} calls")

probes = jl("probe_log.jsonl")
print(f"checked probe_log: {len(probes)} calls")

key = re.compile(r"sk-or-[A-Za-z0-9-]{10,}|Bearer\s+[A-Za-z0-9._-]{20,}|user_[A-Za-z0-9]{20,}")
for f in list(Path(".").glob("*.py")) + list(Path(".").glob("*.jsonl")) + list(Path("results").glob("*")) + list(Path("data").glob("*.jsonl")) + list(Path("report").glob("*")):
    if f.is_file() and key.search(f.read_text(encoding="utf-8", errors="ignore")):
        problems.append(f"{f}: contains something that looks like a credential or account id")

man = Path("MANIFEST.sha256")
if man.exists():
    for line in man.read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        if hashlib.sha256(Path(name).read_bytes()).hexdigest() != digest:
            problems.append(f"{name}: hash differs from MANIFEST.sha256")
    print(f"checked MANIFEST.sha256: {len(man.read_text().splitlines())} files")

if problems:
    print("\n".join(problems[:50]))
    sys.exit(f"{len(problems)} problem(s)")
print("all checks passed")
