# Launch Gates

A single-page report (`site/index.html`) and the code behind it. It answers one question for a family-support AI:
how much human review does it take to prove the AI is safe to launch, when the reviewers are part-time?

Prepared by Marcus for the Sanchez Dooner Foundation product role.

## What is measured

| File | What it does | Output |
|---|---|---|
| `src/evidence.py` | One-sided exact (Clopper-Pearson) bounds, reviews needed per claim, canary sizing | `results/evidence.json` |
| `src/sim_gate.py` | Monte Carlo of a "zero flagged in 299" gate with imperfect reviewers, checked against the closed form | `results/gate.json` |
| `src/sim_queue.py` | Discrete-event simulation of a part-time review desk (review before send) | `results/queue.json` |
| `src/build_rules.py`, `src/router.py`, `src/router.js` | Risk router: one rule file, Python and browser versions | `src/rules_v2.json` |
| `src/eval_router.py` | Router on dev, frozen test and probe sets | `results/router.json` |
| `src/parity.js` | Browser router vs Python router on all 235 messages | `results/js_router_out.json`, `results/parity.json` |
| `src/build_page.py` | Assembles `site/index.html` from the results | `site/index.html` |

Assumptions (reviewer catch rates, arrival pattern, review time) are written into each results JSON and labelled on the page.

## Run it

```
python3 -I src/evidence.py    results/evidence.json
python3 -I src/sim_gate.py    results/gate.json 40000 0
python3 -I src/sim_queue.py   results/queue.json 10 0
python3 -I src/build_rules.py src/rules_v2.json
python3 -I src/eval_router.py results/router.json
sha256sum -c data/router_test.sha256
node src/parity.js src/rules_v2.json data/router_dev.jsonl data/router_test.jsonl data/router_probe.jsonl > results/js_router_out.json
python3 -I src/build_page.py
```

Needs Python 3 with NumPy and SciPy, and Node for the parity check. Seeds are fixed, so results reproduce.

## Honest limits

- The router dev, test and probe sets and the rules were all written by one person. 30 of 30 on the test set is a smoke test, not a validation. The probe result (0 of 20 urgent messages caught) is the more honest number.
- The reviewer, arrival and review-time parameters are assumptions, not observations of real reviewers.
- The legal and regulatory items come from secondary summaries; confirm against primary text with counsel.
- Nothing on the page describes the foundation itself; no public site was found.

## Deploy

Put `site/index.html` at the repository root as `index.html` and push to `main`; Vercel serves it as a static site. Fonts load from Google Fonts and fall back to system fonts if blocked. No cookies, no analytics, no external scripts.
