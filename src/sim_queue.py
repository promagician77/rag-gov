"""
Discrete-event simulation: can part-time clinicians review AI answers BEFORE they reach a family?

Scenario (every number is an ASSUMPTION, written into the output JSON so the page can show it):
  - items needing review arrive as a Poisson stream with a weekly total `lam`, shaped by hour of day
    (families write more in the evening) and a weekend uplift
  - reviewers work fixed daily windows, Monday to Friday; total paid review hours per week = H
  - review time per item is lognormal, median 6 minutes
  - FIFO queue; a reviewer finishes the item they started even if the shift ends
  - turnaround = time from the family's message to the reviewer's decision

  python3 sim_queue.py <out_json> [reps=10] [seed=0]
"""
import bisect
import heapq
import json
import math
import sys

import numpy as np

WEEK = 168.0
HOUR_WEIGHT = [0.6, 0.4, 0.3, 0.25, 0.25, 0.3, 0.5, 0.8, 1.0, 1.0, 1.0, 1.0,
               1.1, 1.0, 1.0, 1.0, 1.1, 1.3, 1.6, 1.9, 2.0, 1.9, 1.5, 1.0]
WEEKEND_UPLIFT = 1.2
SERVICE_MEDIAN_MIN, SERVICE_SIGMA = 6.0, 0.5
SERVICE_MEAN_MIN = SERVICE_MEDIAN_MIN * math.exp(SERVICE_SIGMA ** 2 / 2)
SIM_WEEKS, WARMUP_WEEKS = 56, 4
START_HOUR = {"weekday daytime": 9.0, "weekday evening": 18.0, "24/7 coverage": 0.0}


def arrivals(lam, rng):
    """Arrival times in hours from Monday 00:00, inhomogeneous Poisson via per-hour bins."""
    w = np.array([HOUR_WEIGHT[h % 24] * (WEEKEND_UPLIFT if (h // 24) >= 5 else 1.0) for h in range(168)])
    rate = lam * w / w.sum()                                  # expected items in each hour of the week
    out = []
    for wk in range(SIM_WEEKS):
        counts = rng.poisson(rate)
        for h in np.nonzero(counts)[0]:
            out.append(wk * WEEK + h + rng.random(counts[h]))
    return np.sort(np.concatenate(out))


def windows(H, scenario):
    """(opens, closes, servers). Servers share the same daily windows; each works at most 8 h a day."""
    if scenario == "24/7 coverage":                # H/168 reviewers, each continuously on shift
        servers = int(round(H / WEEK))
        opens = [wk * WEEK for wk in range(SIM_WEEKS + 6)]
        return opens, [o + WEEK for o in opens], servers
    servers = max(1, math.ceil(H / 40.0))
    per_day = H / 5.0 / servers
    opens, closes = [], []
    for wk in range(SIM_WEEKS + 6):
        for d in range(5):
            o = wk * WEEK + d * 24 + START_HOUR[scenario]
            opens.append(o)
            closes.append(o + per_day)
    return opens, closes, servers


def run(lam, H, scenario, rng):
    arr = arrivals(lam, rng)
    opens, closes, servers = windows(H, scenario)
    svc = rng.lognormal(math.log(SERVICE_MEDIAN_MIN), SERVICE_SIGMA, len(arr)) / 60.0
    free = [0.0] * servers
    heapq.heapify(free)
    done = np.full(len(arr), np.inf)            # inf = not reviewed before the simulation ended
    busy = 0.0
    for i, a in enumerate(arr):
        t = max(a, heapq.heappop(free))
        j = bisect.bisect_right(opens, t) - 1
        if not (j >= 0 and t < closes[j]):
            if j + 1 >= len(opens):
                break
            t = opens[j + 1]
        t_end = t + svc[i]
        heapq.heappush(free, t_end)
        done[i] = t_end
        busy += svc[i]
    keep = arr >= WARMUP_WEEKS * WEEK
    horizon = (SIM_WEEKS + 6) * WEEK
    turn = (np.minimum(done, horizon) - arr)[keep]      # unfinished items are censored at the horizon (lower bound)
    # share of messages that arrive while somebody is on shift
    on = np.array([(lambda j: j >= 0 and a < closes[j])(bisect.bisect_right(opens, a) - 1) for a in arr[keep]])
    capacity_hours = H * (SIM_WEEKS - WARMUP_WEEKS)
    return turn, float(on.mean()), float(busy / (H * SIM_WEEKS))


def summarize(turns, ons, utils):
    allt = np.concatenate(turns)
    return {
        "p50_h": float(np.percentile(allt, 50)), "p90_h": float(np.percentile(allt, 90)),
        "p95_h": float(np.percentile(allt, 95)),
        "within_1h": float((allt <= 1).mean()), "within_4h": float((allt <= 4).mean()),
        "within_24h": float((allt <= 24).mean()),
        "on_shift_when_message_arrives": float(np.mean(ons)),
        "utilization": float(np.mean(utils)), "items": int(len(allt)),
    }


def main(out, reps=10, seed=0):
    rng = np.random.default_rng(seed)
    lams, hours = [40, 120, 300], [5, 10, 20, 40, 80]
    res = {
        "assumptions": {"hour_weight": HOUR_WEIGHT, "weekend_uplift": WEEKEND_UPLIFT,
                        "service_median_min": SERVICE_MEDIAN_MIN, "service_sigma": SERVICE_SIGMA,
                        "service_mean_min": SERVICE_MEAN_MIN, "sim_weeks": SIM_WEEKS, "warmup_weeks": WARMUP_WEEKS,
                        "reps": reps, "seed": seed, "start_hour": START_HOUR},
        "lams": lams, "hours": hours, "grid": [],
    }
    for scenario in START_HOUR:
        for lam in lams:
            for H in (hours if scenario != "24/7 coverage" else [168, 336]):
                turns, ons, utils = [], [], []
                for _ in range(reps):
                    t, on, u = run(lam, H, scenario, rng)
                    turns.append(t), ons.append(on), utils.append(u)
                s = summarize(turns, ons, utils)
                rho = lam * SERVICE_MEAN_MIN / 60.0 / H
                s.update({"scenario": scenario, "lam": lam, "H": H, "offered_load": rho, "overloaded": rho >= 0.95,
                          "reviews_per_week_capacity": H * 60.0 / SERVICE_MEAN_MIN,
                          "weeks_to_299": 299 / (H * 60.0 / SERVICE_MEAN_MIN)})
                res["grid"].append(s)
                print(f'{scenario:16s} lam={lam:3d} H={H:2d}  p50={s["p50_h"]:7.1f}h p95={s["p95_h"]:7.1f}h '
                      f'<=4h={s["within_4h"]:5.1%}  on-shift={s["on_shift_when_message_arrives"]:5.1%} load={rho:4.2f}')
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    a = sys.argv
    main(a[1], int(a[2]) if len(a) > 2 else 10, int(a[3]) if len(a) > 3 else 0)
