"""
Monte Carlo: does a "zero flagged in n reviews" launch gate still pass when reviewers miss unsafe answers?

Model (every parameter is an ASSUMPTION, listed in the output JSON):
  - each reviewed answer is unsafe with probability p
  - an unsafe answer is "hard" (subtle) with probability q_hard, otherwise "easy"
  - a reviewer flags an easy unsafe answer with probability catch_easy, a hard one with catch_hard,
    independently of other reviewers
  - gate passes if the number of flagged answers is <= c  (c = 0 here)

Reviewer setups:
  perfect          : flags every unsafe answer
  one reviewer     : one pass per answer
  two reviewers    : answer flagged if EITHER flags it (twice the hours)
  two, if independent : what you would compute if reviewer misses were independent of subtlety

The simulation is agent-level (one random draw per answer per reviewer), so it is an independent check
of the closed-form probability, not a restatement of it.

  python3 sim_gate.py <out_json> [trials=40000] [seed=0]
"""
import json
import sys

import numpy as np

N_REVIEWS = 299            # smallest n that proves <=1% when nothing is flagged (see evidence.py)
C_ALLOWED = 0
Q_HARD, CATCH_EASY, CATCH_HARD = 0.20, 0.95, 0.30
P_GRID = [0.0025, 0.005, 0.01, 0.015, 0.02, 0.03, 0.05]


def sens_one():
    return (1 - Q_HARD) * CATCH_EASY + Q_HARD * CATCH_HARD


def sens_two():
    return (1 - Q_HARD) * (1 - (1 - CATCH_EASY) ** 2) + Q_HARD * (1 - (1 - CATCH_HARD) ** 2)


def sens_two_naive():
    s = sens_one()
    return 1 - (1 - s) ** 2


def analytic_pass(p, s, n=N_REVIEWS, c=C_ALLOWED):
    """P(flagged <= c) with flagged ~ Binomial(n, p*s)."""
    from scipy.stats import binom
    return float(binom.cdf(c, n, p * s))


def simulate(p, reviewers, rng, trials, n=N_REVIEWS, c=C_ALLOWED):
    """reviewers: 0 = perfect, 1 = one reviewer, 2 = two reviewers (either flags)."""
    unsafe = rng.random((trials, n)) < p
    if reviewers == 0:
        flagged = unsafe
    else:
        hard = rng.random((trials, n)) < Q_HARD
        catch = np.where(hard, CATCH_HARD, CATCH_EASY)
        flagged = unsafe & (rng.random((trials, n)) < catch)
        if reviewers == 2:
            flagged |= unsafe & (rng.random((trials, n)) < catch)
    return float((flagged.sum(axis=1) <= c).mean())


def main(out, trials=40000, seed=0):
    rng = np.random.default_rng(seed)
    setups = [
        ("perfect", 0, 1.0),
        ("one reviewer", 1, sens_one()),
        ("two reviewers", 2, sens_two()),
    ]
    res = {
        "assumptions": {"n_reviews": N_REVIEWS, "flags_allowed": C_ALLOWED, "q_hard": Q_HARD,
                        "catch_easy": CATCH_EASY, "catch_hard": CATCH_HARD, "trials": trials, "seed": seed},
        "sensitivity": {"one reviewer": sens_one(), "two reviewers": sens_two(),
                        "two reviewers if independent": sens_two_naive()},
        "p_grid": P_GRID, "rows": [],
    }
    worst = 0.0
    for name, r, s in setups:
        row = {"setup": name, "sensitivity": s, "mc": [], "analytic": []}
        for p in P_GRID:
            mc = simulate(p, r, rng, trials)
            an = analytic_pass(p, s)
            row["mc"].append(mc)
            row["analytic"].append(an)
            worst = max(worst, abs(mc - an))
        res["rows"].append(row)
    res["max_abs_diff_mc_vs_analytic"] = worst
    # standard error of an MC proportion at p=0.5 is 0.5/sqrt(trials); report it so the diff can be read
    res["mc_standard_error_max"] = 0.5 / trials ** 0.5
    # the same gate with a certified bound on the TRUE rate
    res["certified_true_rate_if_pass"] = {name: 0.00997 / s for name, _, s in setups}
    json.dump(res, open(out, "w"), indent=1)
    print("sensitivity:", {k: round(v, 4) for k, v in res["sensitivity"].items()})
    for row in res["rows"]:
        print(row["setup"].ljust(14), " ".join(f"{x:6.1%}" for x in row["mc"]))
    print("max |MC - analytic| =", round(worst, 4), " MC std error <=", round(res["mc_standard_error_max"], 4))


if __name__ == "__main__":
    a = sys.argv
    main(a[1], int(a[2]) if len(a) > 2 else 40000, int(a[3]) if len(a) > 3 else 0)
