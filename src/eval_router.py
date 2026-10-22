"""
Evaluate the risk routers on the dev set (used to write the rules) and the frozen test set (run once).

Tier numbers: 1 urgent, 2 clinical-adjacent, 3 family support, 4 out of scope.
  under-triage : router assigns a LESS careful tier than the message needed (assigned > needed)
  over-triage  : router assigns a MORE careful tier than needed (assigned < needed)

  python3 eval_router.py <out_json>
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import router as R   # noqa: E402
from evidence import cp_upper   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def lower_bound_recall(k, n, conf=0.95):
    """One-sided exact lower bound on recall when k of n were caught."""
    return 1 - cp_upper(n - k, n, conf)


def evaluate(rows, fn):
    conf = [[0] * 4 for _ in range(4)]
    out = []
    for x in rows:
        t, why = fn(x["text"])
        conf[x["tier"] - 1][t - 1] += 1
        out.append({"id": x["id"], "text": x["text"], "needed": x["tier"], "assigned": t, "why": why})
    n = {t: sum(conf[t - 1]) for t in range(1, 5)}
    exact = sum(conf[i][i] for i in range(4))
    under = {t: sum(conf[t - 1][j] for j in range(t, 4)) for t in range(1, 4)}      # needed t, got a higher number
    over = {t: sum(conf[t - 1][j] for j in range(0, t - 1)) for t in range(2, 5)}    # needed t, got a lower number
    t1_caught = conf[0][0]
    t2_safe = conf[1][0] + conf[1][1]
    return {
        "confusion": conf, "n": n, "exact": exact, "total": len(rows), "under": under, "over": over,
        "tier1_recall": t1_caught / n[1] if n[1] else None,
        "tier1_recall_lb95": lower_bound_recall(t1_caught, n[1]) if n[1] else None,
        "tier2_at_least_tier2": t2_safe / n[2] if n[2] else None,
        "tier2_lb95": lower_bound_recall(t2_safe, n[2]) if n[2] else None,
        "over_triaged_total": sum(over.values()), "rows": out,
    }


def main(out):
    dev = R.read(os.path.join(ROOT, "data/router_dev.jsonl"))
    test_path = os.path.join(ROOT, "data/router_test.jsonl")
    test = R.read(test_path)
    rules_path = os.path.join(ROOT, "src/rules_v2.json")
    rules = R.load_rules(rules_path)
    v2 = lambda t: R.route_v2(t, rules)
    probe_path = os.path.join(ROOT, "data/router_probe.jsonl")
    probe = R.read(probe_path)
    res = {
        "test_sha256": sha(test_path), "rules_sha256": sha(rules_path), "probe_sha256": sha(probe_path),
        "dev": {"v0": evaluate(dev, R.route_v0), "v2": evaluate(dev, v2)},
        "test": {"v0": evaluate(test, R.route_v0), "v2": evaluate(test, v2)},
        "probe": {"v0": evaluate(probe, R.route_v0), "v2": evaluate(probe, v2), "kinds": {x["id"]: x["kind"] for x in probe}},
        "n_rules": sum(len(json.load(open(rules_path))[k]) for k in ("t1_hard", "t1_soft", "refuse", "illicit", "t2", "topic")),
    }
    json.dump(res, open(out, "w"), indent=1)
    for split in ("dev", "test", "probe"):
        for v in ("v0", "v2"):
            r = res[split][v]
            f = lambda x: "n/a" if x is None else f"{x:.3f}"
            print(f'{split:5s} {v}: exact {r["exact"]}/{r["total"]}  tier1 recall {f(r["tier1_recall"])} '
                  f'(lb95 {f(r["tier1_recall_lb95"])})  tier2 careful {f(r["tier2_at_least_tier2"])}  '
                  f'under {r["under"]}  over {r["over"]}')


if __name__ == "__main__":
    main(sys.argv[1])
