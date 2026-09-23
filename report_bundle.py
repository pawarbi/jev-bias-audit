"""Bundle every number the interactive report needs into results/bundle.json.

Sources: results/report_data.json (analyze.py), results/report_extra.json
(report_extra.py), results/ext_data.json (ext_analyze.py), plus per-scenario
detail for the equal-records hiring explorer, read from the raw cells.
"""
import json
from pathlib import Path

import pandas as pd

R = Path("results")


def load(stem):
    c = pd.DataFrame([json.loads(l) for l in open(f"data/{stem}.jsonl", encoding="utf-8")])
    r = pd.concat([pd.DataFrame([json.loads(l) for l in open(R / f"{stem}_rep{i}.jsonl")]) for i in (0, 1)])
    return c.merge(r, on="cell_id")


def mean_probs(s):
    return {k: round(float(v), 4) for k, v in pd.DataFrame(list(s)).fillna(0).mean().items()}


explorer = []
for stem, label in (("custom_cells", "original"), ("custom_ext_cells", "extension")):
    d = load(stem)
    d = d[d.type == "hiring_matched"]
    for bid, g in d.groupby("base_id"):
        rec = {"id": bid, "set": label, "axis": g.axis.iloc[0], "a": g.a.iloc[0], "b": g.b.iloc[0],
               "pair": g.pair.iloc[0]}
        for v in (0, 1):
            gv = g[g.variant == v]
            rec[f"state{v}"] = gv.state.iloc[0]
            rec[f"groups{v}"] = gv.groups.iloc[0]
            rec[f"forced{v}"] = mean_probs(gv[gv.arm == "forced"].probs)
            rec[f"tie{v}"] = mean_probs(gv[gv.arm == "with_third"].probs)
            rec[f"keys{v}"] = list(gv[gv.arm == "forced"].criteria.iloc[0].keys())
        rec["pa"] = round((rec["forced0"].get("slot1", 0) + rec["forced1"].get("slot2", 0)) / 2, 4)
        explorer.append(rec)

# exploratory: magnitude of the swap effect regardless of sign, against rep-to-rep noise
sens = []
for stem, label in (("custom_cells", "original"), ("custom_ext_cells", "extension")):
    d = load(stem)
    f = d[(d.type == "hiring_matched") & (d.arm == "forced")].copy()
    f["pa"] = [p.get("slot1", 0) if v == 0 else p.get("slot2", 0) for p, v in zip(f.probs, f.variant)]
    g = f.groupby(["base_id", "axis", "rep"]).pa.mean().unstack()
    g["shift"] = 2 * (g[[0, 1]].mean(axis=1) - 0.5)
    g["noise"] = (2 * (g[0] - g[1])).abs()
    g = g.reset_index()
    for ax, h in list(g.groupby("axis")) + [("ALL", g)]:
        sens.append({"set": label, "axis": ax, "net": float(h["shift"].mean()), "abs": float(h["shift"].abs().mean()),
                     "noise": float(h["noise"].mean()), "n": int(len(h)),
                     "pos": int((h["shift"] > 0).sum()), "neg": int((h["shift"] < 0).sum())})

from ext_analyze import arm_stats, load as ext_load, unsupported
_o = ext_load("custom_cells")
_o = _o[_o.type == "hiring_matched"]
orig_pooled = {"forced": arm_stats(_o, "forced"), "tie": arm_stats(_o, "with_third"), "unsupported": unsupported(_o)}

# position effect: P(option | listed first) - P(same option | listed last), per base, then
# averaged over options; order flip: share of cells whose top choice changes with the order
import numpy as np

_rng = np.random.default_rng(0)


def _ci(v):
    v = np.asarray(v, float)
    bs = [_rng.choice(v, len(v)).mean() for _ in range(2000)]
    return [float(v.mean()), *map(float, np.percentile(bs, [2.5, 97.5]))]


def position_rows(d, cluster):
    per, flips = [], []
    for bid, h in d.groupby(cluster):
        k = len(h.criteria.iloc[0])
        diffs = []
        for role in set(h.roles.iloc[0].values()):
            pos = [list(ro.values()).index(role) for ro in h.roles]
            pf = [p.get(role, 0) for p, q in zip(h.probs, pos) if q == 0]
            pl = [p.get(role, 0) for p, q in zip(h.probs, pos) if q == k - 1]
            if pf and pl:
                diffs.append(np.mean(pf) - np.mean(pl))
        per.append(np.mean(diffs))
        idx = [c for c in ("variant", "para", "rep", "example_id") if c in h]
        w = h.pivot_table(index=idx, columns="order", values="choice", aggfunc="first").dropna()
        flips.append(float((w[0] != w[1]).mean()))
    return {"effect": _ci(per), "flip": float(np.mean(flips)), "n": len(per), "k": int(k)}


pr = [json.loads(l) for l in open("probe_log.jsonl", encoding="utf-8")]
reps = {}
for r in pr:
    t = r["tag"]
    if "rep" in t and "first" in t:
        reps.setdefault((t["q"], t["first"]), []).append(r["response"]["answers"]["q"]["probabilities"]["man"])
pres = [np.mean(reps[(q, "man")]) - np.mean(reps[(q, "woman")]) for q in {q for q, _ in reps}]
position = [{"key": "president", "label": "President question", "note": "two bare labels; 3 wordings x 5 repeats",
             "effect": [float(np.mean(pres)), float(min(pres)), float(max(pres))], "range_is_wordings": True,
             "flip": 1.0, "n": 3, "k": 2}]
spec = [("custom_cells", "hiring_matched", "forced", "Hiring, equal records, forced", "first 17 scenarios"),
        ("custom_ext_cells", "hiring_matched", "forced", "Hiring, equal records, forced", "replication 50"),
        ("custom_cells", "hiring_matched", "with_third", 'Hiring, equal records, "equal" offered', "first 17 scenarios"),
        ("custom_ext_cells", "hiring_matched", "with_third", 'Hiring, equal records, "equal" offered', "replication 50"),
        ("custom_cells", "hiring_evidence", "with_third", "Hiring by rubric", "17 scenarios"),
        ("custom_cells", "incident", "with_third", "Incident responsibility", "33 scenarios"),
        ("custom_cells", "refund", "single", "Refund decision", "22 scenarios"),
        ("custom_cells", "support_triage", "single", "Support triage", "11 scenarios")]
_cache = {}
for stem, t, arm, lab, note in spec:
    d = _cache.setdefault(stem, load(stem))
    row = position_rows(d[(d.type == t) & (d.arm == arm)], "base_id")
    position.append({"key": f"{stem}:{t}:{arm}", "label": lab, "note": note, **row})
bq = load("bbq_cells")
position.append({"key": "bbq", "label": "BBQ, 11 categories", "note": "253 question sets, 1,012 items",
                 **position_rows(bq, "template")})

# how far one record's probability moves when only its descriptor changes (same slot, forced choice)
_sw = np.array([abs(e["forced0"].get("slot1", 0) - e["forced1"].get("slot1", 0)) for e in explorer])
swing = {"n": int(len(_sw)), "mean": float(_sw.mean()), "median": float(np.median(_sw)),
         "p90": float(np.percentile(_sw, 90)), "p95": float(np.percentile(_sw, 95)), "max": float(_sw.max())}

# president question with a third "don't know" option (probe_abstain.py)
abstain = {}
for r in pr:
    t = r["tag"]
    if t.get("probe") != "abstain":
        continue
    probs = r["response"]["answers"]["q"]["probabilities"]
    unk = probs.get("don't know", probs.get("insufficient information", 0))
    man = probs.get("male", probs.get("man", 0))
    a = abstain.setdefault(t["q"], {"n": 0, "unk": [], "man": [], "woman": []})
    a["n"] += 1
    a["unk"].append(unk)
    a["man"].append(man)
    a["woman"].append(probs.get("female", probs.get("woman", 0)))
abstain = {q: {"n": v["n"], "p_unknown": float(np.mean(v["unk"])), "p_man": float(np.mean(v["man"])),
               "max_person": float(max(v["man"] + v["woman"])),
               "abstained": int(sum(u > max(m, w) for u, m, w in zip(v["unk"], v["man"], v["woman"])))}
           for q, v in abstain.items()}

bundle = {
    "abstain": abstain,
    "swing": swing,
    "position": position,
    "orig_pooled": orig_pooled,
    "sensitivity": sens,
    "main": json.loads((R / "report_data.json").read_text(encoding="utf-8")),
    "extra": json.loads((R / "report_extra.json").read_text(encoding="utf-8")),
    "ext": json.loads((R / "ext_data.json").read_text(encoding="utf-8")),
    "explorer": explorer,
}
(R / "bundle.json").write_text(json.dumps(bundle), encoding="utf-8")
print(len(explorer), "explorer bases;", len(json.dumps(bundle)) // 1024, "KB")
