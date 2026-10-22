"""
Evidence arithmetic for launch gates: how many clean human reviews does it take to claim a safety level?

All bounds are ONE-SIDED exact (Clopper-Pearson) upper confidence limits on the unsafe-answer rate.
For zero failures in n reviews this is 1 - alpha**(1/n), which the "rule of three" approximates as 3/n.

  python3 evidence.py <out_json>
"""
import json
import math
import sys

import numpy as np
from scipy.stats import beta


def cp_upper(k, n, conf=0.95):
    """One-sided exact upper confidence limit for a rate, k failures in n reviews."""
    if k >= n:
        return 1.0
    return float(beta.ppf(conf, k + 1, n - k))


def n_needed(target, k=0, conf=0.95):
    """Smallest n such that k failures in n reviews still proves rate <= target."""
    if k == 0:
        return int(math.ceil(math.log(1 - conf) / math.log(1 - target)))
    n = max(k + 1, int(k / target))
    while cp_upper(k, n, conf) > target:
        n += 1
    while n > k + 1 and cp_upper(k, n - 1, conf) <= target:
        n -= 1
    return n


def wilson_halfwidth(p, n, z=1.959964):
    centre_den = 1 + z * z / n
    return z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / centre_den


def canaries_needed(s, halfwidth, z=1.959964):
    """Seeded known-bad items needed to estimate reviewer sensitivity s to +/- halfwidth (Wilson, two-sided 95%)."""
    n = 5
    while wilson_halfwidth(s, n, z) > halfwidth:
        n += 1
    return n


def main(out):
    res = {"conf": 0.95, "sided": "one-sided exact (Clopper-Pearson)"}

    # 1. upper bound after zero failures, exact vs rule of three
    ns = [10, 20, 30, 50, 100, 150, 200, 299, 300, 500, 1000, 2000]
    res["zero_failures"] = [
        {"n": n, "exact": cp_upper(0, n), "rule_of_three": 3 / n, "closed_form": 1 - 0.05 ** (1 / n)} for n in ns
    ]
    # sanity: scipy beta.ppf must equal the closed form for k=0
    res["max_abs_diff_exact_vs_closed_form"] = max(abs(r["exact"] - r["closed_form"]) for r in res["zero_failures"])

    # 2. reviews needed to prove a target, allowing k failures
    targets = [0.05, 0.03, 0.02, 0.01, 0.005, 0.002, 0.001]
    res["targets"] = targets
    res["n_needed"] = {str(k): {str(t): n_needed(t, k) for t in targets} for k in range(0, 6)}

    # 3. curve for the chart (log grid), k = 0, 1, 2
    grid = sorted(set(int(round(x)) for x in np.geomspace(5, 3000, 90)))
    res["curve"] = {"n": grid, **{f"k{k}": [cp_upper(k, n) if n > k else 1.0 for n in grid] for k in (0, 1, 2)}}

    # 4. reviewer sensitivity: what a "pass" certifies when reviewers miss some unsafe answers
    # detected rate <= U  =>  true rate <= U / s   (if sensitivity s is known)
    res["certified_true_rate_after_n_clean"] = {
        str(s): {str(n): cp_upper(0, n) / s for n in (100, 299, 500, 1000)} for s in (1.0, 0.9, 0.82, 0.7)
    }
    res["n_clean_to_certify_1pct_true_rate"] = {str(s): n_needed(0.01 * s, 0) for s in (1.0, 0.95, 0.9, 0.82, 0.7)}

    # 5. canaries: seeded known-bad answers to measure reviewer sensitivity
    res["canaries_needed"] = {
        str(s): {str(h): canaries_needed(s, h) for h in (0.10, 0.05)} for s in (0.7, 0.82, 0.9)
    }

    # 6. a few worked examples quoted in prose
    res["worked"] = {
        "clean_100": cp_upper(0, 100),
        "clean_299": cp_upper(0, 299),
        "one_fail_in_500": cp_upper(1, 500),
        "n_for_1pct_k0": n_needed(0.01, 0),
        "n_for_1pct_k1": n_needed(0.01, 1),
        "n_for_05pct_k0": n_needed(0.005, 0),
        "n_for_01pct_k0": n_needed(0.001, 0),
    }
    json.dump(res, open(out, "w"), indent=1)
    w = res["worked"]
    print(f"100 clean -> {w['clean_100']:.4f}; 299 clean -> {w['clean_299']:.5f}; 1 fail in 500 -> {w['one_fail_in_500']:.4f}")
    print("n for <=1%:", w["n_for_1pct_k0"], "(k=0)", w["n_for_1pct_k1"], "(k=1);  <=0.5%:", w["n_for_05pct_k0"], " <=0.1%:", w["n_for_01pct_k0"])
    print("closed-form check max diff:", res["max_abs_diff_exact_vs_closed_form"])
    print("clean needed to certify 1% true rate by sensitivity:", res["n_clean_to_certify_1pct_true_rate"])
    print("canaries:", res["canaries_needed"])


if __name__ == "__main__":
    main(sys.argv[1])
