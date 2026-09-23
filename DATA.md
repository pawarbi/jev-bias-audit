# Data dictionary

All files are JSON Lines, one record per line, UTF-8.

## Cells: `data/custom_cells.jsonl`, `data/custom_ext_cells.jsonl`

One record per model call. A base scenario expands into 2 demographic variants x 2 option
orders x 3 question wordings, and x 2 formats for equal-record hiring.

| Field | Meaning |
|---|---|
| `cell_id` | Unique id (`c...` for the main set, `x...` for the replication) |
| `base_id` | The base scenario. Confidence intervals resample these, not cells |
| `type` | `hiring_matched`, `hiring_evidence`, `incident`, `refund`, `support_triage` |
| `arm` | `forced` (two options), `with_third` (adds "equal" or "cannot determine"), `single` (one person) |
| `variant` | 0 or 1. In two-person types, variant 0 gives slot 1 descriptor a; variant 1 swaps them |
| `order` | 0 is the designed option order, 1 is reversed |
| `para` | Which of the three question wordings |
| `axis` | `gender`, `age`, `race`, `name_gender`, `name_race` |
| `a`, `b`, `pair` | The descriptor pair. `a` is the group being tested, `b` its comparison |
| `state` | The exact text sent as Jev's state |
| `instructions` | The exact question |
| `criteria` | The options exactly as sent, in the order sent (key to description) |
| `roles` | What each option key means: `slot1`, `slot2`, `equal`, `unknown`, `approve`, `deny`, `urgent`, ... |
| `groups` | Which descriptor each slot or subject holds in this variant |
| `expected` | The role the evidence determines, or null where only invariance is tested |
| `expected_group` | The group of the person or subject holding the expected answer |
| `subtype` | For refunds and triage: `eligible`, `ineligible`, `borderline`, or the priority level |

## Cells: `data/bbq_cells.jsonl`

| Field | Meaning |
|---|---|
| `cell_id` | `b_<category>_<example_id>_<order>` |
| `category`, `example_id` | The BBQ item |
| `template` | `<category>:<question_index>`, the resampling unit |
| `polarity` | `neg` or `nonneg` question |
| `condition` | `ambig` or `disambig` context |
| `order` | 0 is BBQ's order, 1 is reversed |
| `state`, `instructions`, `criteria` | As above; options are keyed by their answer text |
| `roles` | Answer text to `ans0`, `ans1` or `ans2` |
| `label`, `unknown`, `target` | The correct answer, the "unknown" answer, and the stereotyped target (from BBQ's metadata) |

## Raw traces: `results/*_raw.jsonl`

| Field | Meaning |
|---|---|
| `ts` | UTC time the response was received |
| `tag` | `cell_id` and `rep` (0 or 1) |
| `request` | The exact JSON body sent: `model`, `state`, `questions` |
| `response` | The full JSON response: `model` (the version that answered), `answers.q.choice`, `answers.q.probabilities`, `answers.q.confidence`, `usage` (tokens and cost), `id`, `provider` |

Only successful responses are logged. There were no failed calls in the six main runs. The
request headers, which carry the API key, are never logged.

## Parsed results: `results/*_rep0.jsonl`, `results/*_rep1.jsonl`

| Field | Meaning |
|---|---|
| `cell_id`, `rep` | As above |
| `choice` | The role of the chosen option |
| `probs` | Probability for each role |
| `confidence`, `model`, `cost` | Copied from the raw response |

`verify.py` rebuilds these from the raw traces and checks that they match.

## Probes: `probe_log.jsonl`

Same shape as the raw traces. `tag` holds `case` (the first six probes), `q`, `first` and `rep`
(the order-repeat probes), or `probe: abstain` with `labels`, `q`, `order` and `rep` (the
"don't know" probes). The very first probe call returned HTTP 400 because the question
format was wrong, and is not logged.
