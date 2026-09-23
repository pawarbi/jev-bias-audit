# Does Jev Discriminate? A Counterfactual Bias Audit

A pilot study of TypeSafe's Jev decision model (`typesafe/jev-1.13`), run through OpenRouter's
decisions endpoint on 22 and 23 September 2026. It started from one screenshot: asked who would
make a better president, a man or a woman, Jev said "man" at 67%.

**Read the report: [https://claude.ai/artifact/DMMxb6Vi724gg9zLrYtQwD](https://claude.ai/artifact/DMMxb6Vi724gg9zLrYtQwD)**

That is the published version, with interactive charts and a scenario explorer. The same page
is in this repository as `report/jev-swap-test.html`; open it in a browser, no server needed.

## What we found

- The 67% was mostly option order. Whichever option is listed first gains 0.37. With a third
  option, "don't know", Jev chose it in 72 of 72 calls.
- When the evidence decides the case (a hiring rubric, a refund policy, ticket rules, camera or
  log evidence), swapping a demographic descriptor changed nothing. Jev was correct for every group.
- Between two equally qualified applicants, the first 17 scenarios leaned toward the woman, the
  older applicant and the non-white applicant. A pre-registered replication on 50 new scenarios
  did not reproduce it (27 of 50, one-sided p = 0.34). The descriptor still moves the probabilities
  by about 0.04 on average, three times run-to-run noise, but in both directions.
- None of the 40 pre-registered tests met the bar for a demographic effect.
- On 1,012 BBQ items, Jev scored 98.7% on ambiguous contexts and 96.5% on clear ones, with bias
  scores at zero. BBQ is public, so treat that as a floor.

The short version: no consistent preference for any group, but Jev is not fully invariant to
demographics in near-ties, and it is sensitive to how a question is framed. Give it a way to say
"I can't tell", and average over both option orders.

## What is in this repository

| Path | Contents |
|---|---|
| `PREREGISTRATION.md` | The metrics and decision rules, written before the main run, plus Addendum 1, written before the replication |
| `data/*_cells.jsonl` | Every test cell: the exact prompt, the options in order, which person holds which descriptor, and the expected answer |
| `results/*_raw.jsonl` | Every request sent and the full raw response, with a UTC timestamp |
| `results/*_rep{0,1}.jsonl` | The same responses with each option mapped back to its meaning |
| `probe_log.jsonl` | The 108 president-question probes |
| `results/*.json`, `results/report.md` | Analysis outputs that the report is built from |
| `report/` | The report template, the build script and the built page |
| `DATA.md` | Field-by-field description of the files |

BBQ itself is not included. `fetch_bbq.py` downloads it from the
[official repository](https://github.com/nyu-mll/BBQ) and checks each file against the hash of
the copy we used.

## Reproducing it

Checking the traces and rebuilding every result needs no API key and makes no model calls:

```
pip install -r requirements.txt
python verify.py          # traces are complete, requests match the design, parsed = raw
python fetch_bbq.py       # BBQ, hash-checked
python bbq_cells.py       # 2,024 BBQ cells, seed 7
python scenarios.py       # 1,404 custom cells, seed 11
python ext_scenarios.py   # 1,200 replication cells, seed 23
python analyze.py         # pre-registered metrics, results/report.md
python ext_analyze.py     # Addendum 1 tests
python report_extra.py
python report_bundle.py
python report/build.py    # report/jev-swap-test.html
```

Run from a clean copy, each of those steps reproduces the committed files byte for byte. We
checked this before publishing.

Re-running the model calls needs an OpenRouter key in `OPENROUTER_API_KEY`:

```
python run.py data/custom_cells.jsonl --rep 0      # and --rep 1
python run.py data/custom_ext_cells.jsonl --rep 0  # and --rep 1
python run.py data/bbq_cells.jsonl --rep 0         # and --rep 1
python probe_repeat.py
python probe_abstain.py
```

Jev is not fully deterministic. Identical requests changed 1 to 3 percent of decisions between
our two runs, so a fresh run will differ at about that level. The whole study cost about $0.16.

## Limits

These are 150 synthetic scenarios in US English, covering five demographic axes (gender, age,
and race or ethnicity, stated explicitly or signalled by a name) and one model version. The
descriptors are more explicit than real records usually are. A counterfactual swap shows that a
detail changes the output; it does not establish fairness in the formal causal sense. Analyses
not in the pre-registration are labelled exploratory in the report.

## Licence and attribution

Code is released under the MIT licence. The BBQ-derived cells in `data/bbq_cells.jsonl` and their
responses reproduce BBQ items, which are CC-BY-4.0: Parrish et al.,
[BBQ: A Hand-Built Bias Benchmark for Question Answering](https://arxiv.org/abs/2110.08193),
Findings of ACL 2022. All names and people in the custom scenarios are synthetic.
