"""Run a cell file against Jev. Resumable: cells already in the results file are skipped.

    python run.py data/custom_cells.jsonl --rep 0
"""
import argparse
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from jev_client import choice, decide

ap = argparse.ArgumentParser()
ap.add_argument("cells")
ap.add_argument("--rep", type=int, default=0)
ap.add_argument("--threads", type=int, default=16)
ap.add_argument("--limit", type=int, default=None)
args = ap.parse_args()

src = Path(args.cells)
out_path = Path("results") / f"{src.stem}_rep{args.rep}.jsonl"
log_path = Path("results") / f"{src.stem}_rep{args.rep}_raw.jsonl"
out_path.parent.mkdir(exist_ok=True)
done = set()
if out_path.exists():
    done = {json.loads(l)["cell_id"] for l in open(out_path, encoding="utf-8")}
cells = [json.loads(l) for l in open(src, encoding="utf-8")]
todo = [c for c in cells if c["cell_id"] not in done][: args.limit]
print(f"{len(done)} done, {len(todo)} to run")

lock = threading.Lock()
cost = 0.0


def one(c):
    out = decide(c["state"], {"q": choice(c["instructions"], c["criteria"])},
                 log_path=log_path, tag={"cell_id": c["cell_id"], "rep": args.rep})
    a = out["answers"]["q"]
    probs = {c["roles"][k]: v for k, v in a["probabilities"].items()}
    return {"cell_id": c["cell_id"], "rep": args.rep, "choice": c["roles"][a["choice"]],
            "probs": probs, "confidence": a.get("confidence"), "model": out.get("model"),
            "cost": out["usage"]["cost"]}


with ThreadPoolExecutor(args.threads) as ex, open(out_path, "a", encoding="utf-8") as f:
    futs = [ex.submit(one, c) for c in todo]
    for n, fu in enumerate(as_completed(futs), 1):
        try:
            r = fu.result()
        except Exception as e:  # keep going; a rerun picks up the gaps
            print("ERR", e)
            continue
        with lock:
            f.write(json.dumps(r) + "\n")
            cost += r["cost"]
        if n % 200 == 0:
            print(n, f"${cost:.4f}")
print(f"finished, ${cost:.4f}")
