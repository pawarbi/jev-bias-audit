"""Sample the balanced BBQ pilot: about 23 quads per category, spread over templates.

A quad is four consecutive example_ids sharing one template and one name pair:
(ambiguous, disambiguated) x (negative, non-negative question).
"""
import glob
import json
import random
from collections import defaultdict
from pathlib import Path

import pandas as pd

SEED = 7
QUADS_PER_CAT = 23
OUT = Path("data/bbq_cells.jsonl")

rows = []
for f in sorted(glob.glob("data/bbq/*.jsonl")):
    rows += [json.loads(l) for l in open(f, encoding="utf-8")]
meta = pd.read_csv("data/bbq/additional_metadata.csv")
tloc = {(r.category, int(r.example_id)): r.target_loc for r in meta.itertuples()}

quads = defaultdict(list)
for r in rows:
    quads[(r["category"], r["example_id"] // 4)].append(r)

rng = random.Random(SEED)
cells = []
for cat in sorted({k[0] for k in quads}):
    by_tpl = defaultdict(list)
    for (c, q), items in quads.items():
        if c == cat and all(pd.notna(tloc.get((c, it["example_id"]))) for it in items):
            by_tpl[items[0]["question_index"]].append(q)
    tpls = sorted(by_tpl)
    rng.shuffle(tpls)
    for t in tpls:
        rng.shuffle(by_tpl[t])
    picked, k = [], 0
    while len(picked) < QUADS_PER_CAT:  # round-robin over templates
        t = tpls[k % len(tpls)]
        if by_tpl[t]:
            picked.append(by_tpl[t].pop())
        k += 1
    for q in picked:
        for it in quads[(cat, q)]:
            answers = [it["ans0"], it["ans1"], it["ans2"]]
            unk = next(i for i in range(3) if it["answer_info"][f"ans{i}"][1] == "unknown")
            for order in (0, 1):
                idx = [0, 1, 2] if order == 0 else [2, 1, 0]
                cells.append({
                    "cell_id": f"b_{cat}_{it['example_id']}_{order}", "category": cat,
                    "example_id": it["example_id"], "template": f"{cat}:{it['question_index']}",
                    "polarity": it["question_polarity"], "condition": it["context_condition"],
                    "order": order, "state": it["context"], "instructions": it["question"],
                    "criteria": {answers[i]: answers[i] for i in idx},
                    "roles": {answers[i]: f"ans{i}" for i in idx},
                    "label": f"ans{it['label']}", "unknown": f"ans{unk}",
                    "target": f"ans{int(tloc[(cat, it['example_id'])])}",
                })

OUT.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cells), encoding="utf-8")
print(len(cells), "cells,", len(cells) // 2, "items,", len({c["template"] for c in cells}), "templates")
