"""Probe results and exploratory detail for the HTML report (results/report_extra.json).

Everything here is labelled exploratory in the report: the pre-registered
metrics come from analyze.py.
"""
import json
from collections import defaultdict
from pathlib import Path

import pandas as pd

out = {}

# probes: president question, order x wording, 5 repeats
probe = [json.loads(l) for l in open("probe_log.jsonl", encoding="utf-8")]
rep = defaultdict(list)
single = {}
for r in probe:
    t, a = r["tag"], r["response"]["answers"]["q"]
    if "rep" in t and "first" in t:
        rep[(t["q"], t["first"])].append(a["probabilities"]["man"])
    elif "case" in t:
        single[t["case"]] = a["probabilities"]
out["probe_repeat"] = [{"q": q, "first": f, "p_man": v} for (q, f), v in rep.items()]
out["probe_single"] = single

# matched hiring: per-base P(pick descriptor a) and P(second profile), forced arm
c = pd.DataFrame([json.loads(l) for l in open("data/custom_cells.jsonl", encoding="utf-8")])
res = pd.concat([pd.DataFrame([json.loads(l) for l in open(f"results/custom_cells_rep{i}.jsonl")]) for i in (0, 1)])
d = c.merge(res, on="cell_id")
m = d[d.type == "hiring_matched"].copy()
f = m[m.arm == "forced"].copy()
f["pa"] = [p.get("slot1", 0) if v == 0 else p.get("slot2", 0) for p, v in zip(f.probs, f.variant)]
f["p2"] = [p.get("slot2", 0) for p in f.probs]
per = f.groupby(["base_id", "axis", "pair"]).agg(pa=("pa", "mean"), p2=("p2", "mean")).reset_index()
out["matched_bases"] = per.to_dict("records")

# with-tie arm: direction of variant flips
w = m[m.arm == "with_third"].pivot_table(index=["base_id", "order", "para", "rep"], columns="variant",
                                          values="choice", aggfunc="first").reset_index()
w = w[w[0] != w[1]]


def direction(v0, v1):
    # v0: slot1=a, slot2=b.  v1: slot1=b, slot2=a.
    pick = lambda v, ch: ("a" if (ch == "slot1") == (v == 0) else "b") if ch.startswith("slot") else "equal"
    p0, p1 = pick(0, v0), pick(1, v1)
    if "a" in (p0, p1) and "b" not in (p0, p1):
        return "toward a"
    if "b" in (p0, p1) and "a" not in (p0, p1):
        return "toward b"
    return "mixed"


out["tie_flips"] = pd.Series([direction(a, b) for a, b in zip(w[0], w[1])]).value_counts().to_dict()
out["tie_cells"] = int(len(m[m.arm == "with_third"]))

# one worked example, forced arm, first paraphrase, rep 0
ex = f[(f.base_id == "hire_match_07") & (f.para == 0) & (f.rep == 0)].sort_values(["variant", "order"])
out["example"] = {"state_v0": ex[ex.variant == 0].state.iloc[0], "state_v1": ex[ex.variant == 1].state.iloc[0],
                  "question": ex.instructions.iloc[0],
                  "rows": [{"variant": int(r.variant), "order": int(r.order), "groups": r.groups, "probs": r.probs}
                           for r in ex.itertuples()]}
Path("results/report_extra.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps({k: v for k, v in out.items() if k not in ("example", "matched_bases")}, indent=1)[:1500])
