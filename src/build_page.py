"""Assemble the Launch Gates page from the measured results (results/*.json) and the source files."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from evidence import n_needed  # noqa: E402
from pagelib import (esc, pct, tag, pair, figure, heat, hero_dots, HERO_CSS, line_chart, legend, table, codeblock,  # noqa: E402
                     BLUE, ORANGE, AQUA, CRIT)

J = lambda p: json.load(open(os.path.join(ROOT, p)))
EV, GATE, Q, RT, PAR = J("results/evidence.json"), J("results/gate.json"), J("results/queue.json"), J("results/router.json"), J("results/parity.json")
RULES = J("src/rules_v2.json")
AUTHOR = "Marcus"
SVC_MEAN = Q["assumptions"]["service_mean_min"]
fmt = lambda x: f"{round(x):,}"


def qrow(scn, lam, H):
    return next(r for r in Q["grid"] if r["scenario"] == scn and r["lam"] == lam and r["H"] == H)


# =========================================================================== 1. Evidence
def panel_evidence():
    c = EV["curve"]
    ns = c["n"]
    series = []
    for k, col, name in ((0, BLUE, "0 flagged"), (1, ORANGE, "1 flagged"), (2, AQUA, "2 flagged")):
        series.append({"name": name, "color": col, "xs": ns, "ys": c[f"k{k}"], "hit_only": True, "dots": list(range(0, len(ns), 2)),
                       "tip": (lambda kk, nm: (lambda x, y: f"{nm} in {x:,} reviews: the unsafe rate could still be {y * 100:.2f}%"))(k, name),
                       "label": name, "label_dy": {0: 0, 1: 2, 2: 6}[k]})
    z = {r["n"]: r for r in EV["zero_failures"]}
    series.append({"name": "marks", "color": BLUE, "xs": [100, 299], "ys": [z[100]["exact"], z[299]["exact"]], "line": False,
                   "tip": lambda x, y: f"{x} clean reviews: the unsafe rate could still be {y * 100:.2f}%"})
    chart = line_chart(series, xticks=[10, 30, 100, 300, 1000, 3000], yticks=[0.001, 0.003, 0.01, 0.03, 0.1, 0.3],
                       xlog=True, ylog=True, xr=(10, 3000), yr=(0.001, 0.3),
                       xlabel="Human reviews done (log scale)", ylabel="Worst unsafe rate still possible (log scale)",
                       yfmt=lambda v: f"{v * 100:g}%", xfmt=lambda v: f"{v:,}",
                       refs=[(0.03, "3%"), (0.01, "1%")],
                       notes=[(100, z[100]["exact"], f"100 clean: {z[100]['exact'] * 100:.2f}%", -10, 22, "end"),
                              (299, z[299]["exact"], f"299 clean: {z[299]['exact'] * 100:.2f}%", -10, 22, "end")])
    tv = table(["Reviews, none flagged", "Worst rate still possible", "Rule of three (3 / n)"],
               [(f"{r['n']:,}", f"{r['exact'] * 100:.2f}%", f"{r['rule_of_three'] * 100:.2f}%") for r in EV["zero_failures"]],
               num_cols=(0, 1, 2))
    tg = EV["targets"]
    lab = lambda t: f"{t * 100:g}%"
    rows = []
    for t in tg:
        cells = []
        for k in range(0, 4):
            v = EV["n_needed"][str(k)][str(t)]
            cells.append(f"<b>{v:,}</b>" if (k == 0 and t == 0.01) else f"{v:,}")
        rows.append((f"at most {lab(t)}", *cells))
    need = table(["To show the unsafe rate is", "0 flagged", "1 flagged", "2 flagged", "3 flagged"], rows, num_cols=(1, 2, 3, 4))
    w = EV["worked"]
    return f'''
<section class="sec first">
  <h2>What a pile of clean reviews proves</h2>
  {pair("<p>Before an AI answers a parent at two in the morning, someone has to say how sure we are that it is safe. &ldquo;We read a lot of answers and found nothing wrong&rdquo; sounds like an answer. It is a statement about the answers you read, not the thousands you did not.</p><p>The honest question is: given what we checked, what is the worst unsafe rate we still cannot rule out? That number depends almost entirely on how many answers were checked.</p>",
        "<p>One-sided exact (Clopper&ndash;Pearson) upper confidence limit on the unsafe-answer rate, 95% confidence. With zero flagged in n reviews it equals 1 &minus; 0.05<sup>1/n</sup>, which the &ldquo;rule of three&rdquo; approximates as 3/n (Hanley &amp; Lippman-Hand, <i>JAMA</i> 1983).</p><p>Assumes reviews are a random sample of what families will see and that a reviewer flags every unsafe answer. The next tab removes the second assumption.</p>")}
  {figure('<div class="scroll">' + chart + '</div>' + legend([("0 flagged", BLUE), ("1 flagged", ORANGE), ("2 flagged", AQUA)]),
          "Both axes are logarithmic. Each line shows the worst unsafe rate that cannot be ruled out (95% confidence) after that many human reviews. Hover a point for the value.")}
  <details class="more"><summary>Table view</summary>{tv}</details>
</section>

<section class="sec">
  <div class="cols3">
    <div class="fact"><b>{w["clean_100"] * 100:.2f}%</b><small>after 100 clean reviews</small><p>About 3 in 100 could still be unsafe. On 1,000 answers to families that is up to 29 you have not seen. {tag("m")}</p></div>
    <div class="fact"><b>{w["n_for_1pct_k0"]}</b><small>clean reviews to show 1% or less</small><p>Not 100, not 200. And that is for one kind of question. Each risk tier needs its own sample. {tag("m")}</p></div>
    <div class="fact"><b>{w["n_for_05pct_k0"]:,} and {w["n_for_01pct_k0"]:,}</b><small>for 0.5% and for 0.1%</small><p>Halving the rate you can claim doubles the reading. One flagged answer pushes 1% from {w["n_for_1pct_k0"]} to {w["n_for_1pct_k1"]}. {tag("m")}</p></div>
  </div>
</section>

<section class="sec">
  <h2>Reviews needed, by what you want to claim</h2>
  <p class="lede">Smallest number of human reviews that still proves the target, 95% confidence, if up to 0, 1, 2 or 3 answers were flagged. Bold is the 1% case from above.</p>
  {need}
</section>

<section class="sec">
  <h2>Try your own numbers</h2>
  {pair("<p>Put in how many answers were reviewed and how many were flagged. The calculator tells you the worst case you cannot rule out, and how many more reviews you would need to claim a better one. The last slider lets reviewers miss some unsafe answers, which they do.</p>",
        "<p>Runs the same exact binomial maths as <code>evidence.py</code> in your browser. With reviewer sensitivity s, the bound on the true rate is U/s, where U is the bound on the detected rate. The two implementations agree on every cell of the table above.</p>")}
  <div class="calc" id="calc">
    <div>
      <div class="row"><label for="c-n">Answers reviewed</label><input id="c-n" type="number" min="1" step="1" value="100"></div>
      <div class="row"><label for="c-k">Answers flagged as unsafe</label><input id="c-k" type="number" min="0" step="1" value="0"></div>
      <div class="row"><label for="c-conf">Confidence</label><select id="c-conf"><option value="0.9">90%</option><option value="0.95" selected>95%</option><option value="0.99">99%</option></select></div>
      <div class="row"><label for="c-t">Claim you want to make: unsafe rate at most (%)</label><input id="c-t" type="number" min="0.01" max="50" step="0.1" value="1"></div>
      <div class="row"><label for="c-s">Share of unsafe answers a reviewer catches: <span id="c-sv">100%</span></label><input id="c-s" type="range" min="50" max="100" step="1" value="100"><div class="hint">100% means reviewers never miss. Measure this with canaries (next tab).</div></div>
    </div>
    <div class="out" aria-live="polite">
      <div class="big" id="o-big">&nbsp;</div>
      <p id="o-txt"></p><hr>
      <div class="big" id="o-need">&nbsp;</div>
      <p id="o-needtxt"></p>
    </div>
  </div>
</section>

<section class="sec">
  <h2>Why the average answer is the wrong thing to measure</h2>
  <div class="cols2">
    <div class="fact"><b>91% and 22%</b><small>ChatGPT on public-health questions, 2023</small><p>Ayers et al. asked 23 public-health questions, 14 of them about addiction. 91% of answers were evidence-based, but only 22% pointed to a specific resource, and only 2 of the 14 addiction answers did. The failure was a silent omission, not a wrong fact. Models have changed since; the shape of the failure has not.</p></div>
    <div class="fact"><b>One third lower</b><small>worst of 16 answers vs the average (HealthBench)</small><p>HealthBench scores 5,000 health conversations against rubrics written by 262 physicians. For the strongest model reported, the worst of 16 attempts scored about a third below its average. Families do not get the average answer. They get one.</p></div>
  </div>
</section>
'''


# =========================================================================== 2. Reviewers
def panel_reviewers():
    G = GATE
    P = G["p_grid"]
    rows = []
    for r in G["rows"]:
        cells = "".join(
            f'<td class="heat{" hl" if abs(p - 0.01) < 1e-9 else ""}" style="background:{heat(v, .6)}" data-tip="Simulated {v * 100:.1f}%; closed form {a * 100:.1f}%">{v * 100:.1f}%</td>'
            for p, v, a in zip(P, r["mc"], r["analytic"]))
        rows.append(f'<tr><td><b>{esc(r["setup"])}</b><br><span class="hint">catches {r["sensitivity"] * 100:.0f}% of unsafe answers</span></td>{cells}</tr>')
    head = "".join(f'<th class="n">{p * 100:g}%</th>' for p in P)
    heat_tbl = (f'<div class="scroll"><table class="tbl"><thead><tr><th>Reviewers</th>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')
    s1, s2, sn = G["sensitivity"]["one reviewer"], G["sensitivity"]["two reviewers"], G["sensitivity"]["two reviewers if independent"]
    p1 = {r["setup"]: r["mc"][P.index(0.01)] for r in G["rows"]}
    cert = EV["certified_true_rate_after_n_clean"]
    crow = [(f"{float(s) * 100:.0f}%", *[f"{cert[s][n] * 100:.2f}%" for n in ("100", "299", "500", "1000")]) for s in ("1.0", "0.9", "0.82", "0.7")]
    ctab = table(["Reviewers catch", "after 100 clean", "after 299 clean", "after 500 clean", "after 1,000 clean"], crow, num_cols=(1, 2, 3, 4))
    ncert = EV["n_clean_to_certify_1pct_true_rate"]
    can = EV["canaries_needed"]
    cantab = table(["True catch rate", "Canaries for +/- 10 points", "Canaries for +/- 5 points"],
                   [(f"{float(s) * 100:.0f}%", can[s]["0.1"], can[s]["0.05"]) for s in ("0.7", "0.82", "0.9")], num_cols=(1, 2))
    a = G["assumptions"]
    return f'''
<section class="sec first">
  <h2>Reviewers miss things, so a clean review proves less than it seems</h2>
  {pair("<p>Suppose a reviewer catches 8 of every 10 unsafe answers. Then &ldquo;nothing flagged&rdquo; is weaker evidence than the last tab said, because some unsafe answers were read and waved through.</p><p>The fix is not to distrust reviewers. It is to measure them. Slip in answers that are known to be bad (canaries), count how many get caught, and use that rate when you decide whether to launch.</p>",
        f"<p>Agent-level Monte Carlo of a launch gate: pass if zero of {a['n_reviews']} reviewed answers are flagged. Each answer is unsafe with probability p. {a['q_hard'] * 100:.0f}% of unsafe answers are subtle: a reviewer flags those with probability {a['catch_hard']}, others with {a['catch_easy']}. That gives one-reviewer sensitivity {s1:.2f}. {a['trials']:,} trials per cell, seed {a['seed']}.</p>")}
  <p>{tag("a")} reviewer catch rates and the share of subtle failures are assumptions, shown so you can change them in <code>sim_gate.py</code>. {tag("m")} the simulated pass rates, and their agreement with the closed form: largest difference {G["max_abs_diff_mc_vs_analytic"] * 100:.2f} points, simulation standard error up to {G["mc_standard_error_max"] * 100:.2f} points.</p>
</section>

<section class="sec">
  <h2>How often a bad system passes the gate</h2>
  <p class="lede">The gate is built so that a system with a true 1% unsafe rate passes only 5% of the time. Columns are the true unsafe rate; each cell is the share of simulated launches where the gate was passed. Outlined column: the 1% boundary.</p>
  {heat_tbl}
  <div class="cols3">
    <div class="fact"><b>{p1["perfect"] * 100:.1f}% &rarr; {p1["one reviewer"] * 100:.1f}%</b><small>false pass at a true 1% rate</small><p>With perfect reviewers the gate does what it says. With one realistic reviewer it lets a 1% system through {p1["one reviewer"] / p1["perfect"]:.1f} times as often.</p></div>
    <div class="fact"><b>{s2:.2f}, not {sn:.2f}</b><small>two reviewers, either can flag</small><p>If misses were independent, two reviewers would catch {sn * 100:.0f}%. Subtle failures are missed by both, so the simulation gives {s2 * 100:.0f}%. A second reviewer is worth having and worth less than the arithmetic suggests.</p></div>
    <div class="fact"><b>{ncert["0.82"]} vs {ncert["1.0"]}</b><small>clean reviews to certify a true 1% rate</small><p>With one reviewer at {s1 * 100:.0f}% sensitivity, 299 clean reviews do not certify 1%. {ncert["0.82"]} do. With two, {ncert["0.9"]}.</p></div>
  </div>
</section>

<section class="sec">
  <h2>What a pass actually certifies</h2>
  <p class="lede">Worst true unsafe rate still possible after n clean reviews, if reviewers catch the share in the left column (95% confidence, bound on the detected rate divided by the catch rate).</p>
  {ctab}
</section>

<section class="sec">
  <h2>Measuring the reviewers: canaries</h2>
  {pair("<p>About one in twenty items in the review queue is a deliberately bad answer that staff wrote and the reviewer does not know about. If the reviewer catches 9 of 10 canaries, you know something real about how often they catch real failures. Reviewers who are fresh, tired, new or rushed all show up.</p>",
        "<p>Seeded-fault sampling to estimate sensitivity. Table: canaries needed for a 95% Wilson interval of the stated half-width. The canary catch rate is itself a launch gate, and it is tracked weekly after launch to catch reviewer drift.</p>")}
  {cantab}
  <div class="caveat"><b>Caveat.</b> Canaries only measure the failures you thought to write. They cover known failure types, not new ones, so they are one input to the gate, never the whole gate.</div>
</section>
'''


# =========================================================================== 3. Capacity
def panel_capacity():
    A = Q["assumptions"]
    lam = 120
    xs_h = [5, 10, 20, 40, 80]
    mk = lambda scn, col, name, hs: {
        "name": name, "color": col, "xs": hs, "ys": [qrow(scn, lam, h)["on_shift_when_message_arrives"] * 100 for h in hs],
        "tip": (lambda nm: (lambda x, y: f"{nm}, {x} reviewer-hours a week: {y:.0f}% of messages arrive while a reviewer is on shift"))(name)}
    s1 = mk("weekday daytime", BLUE, "Weekday 9 to 5", xs_h)
    s2 = mk("weekday evening", ORANGE, "Weekday evenings", xs_h)
    s3 = mk("24/7 coverage", AQUA, "24/7 coverage", [168, 336])
    s1["label"], s2["label"], s3["label"] = "Weekdays, daytime", "Weekday evenings", "24/7"
    s1["label_dy"], s2["label_dy"], s3["label_dy"] = 14, -6, 4
    chart = line_chart([s1, s2, s3], xticks=[5, 10, 20, 40, 80, 168, 336], yticks=[0, 20, 40, 60, 80, 100],
                       xlog=True, ylog=False, xr=(4, 400), yr=(0, 105),
                       xlabel="Paid reviewer hours per week (log scale)", ylabel="Messages arriving on shift (%)",
                       yfmt=lambda v: f"{v:g}%", xfmt=lambda v: f"{v:g}", mr=150)
    rows = []
    for H in (5, 10, 20, 40, 80):
        a, b = qrow("weekday daytime", lam, H), qrow("weekday evening", lam, H)
        cell = lambda r: ("backlog grows" if r["overloaded"] else f'{r["p50_h"]:.0f} h', "" if r["overloaded"] else f'{r["p95_h"]:.0f} h')
        ca, cb = cell(a), cell(b)
        rows.append((f"{H}", f"{a['reviews_per_week_capacity']:.0f}", f"{a['weeks_to_299']:.1f}", ca[0], ca[1] or "&ndash;", cb[0], cb[1] or "&ndash;",
                     f'{a["on_shift_when_message_arrives"] * 100:.0f}% / {b["on_shift_when_message_arrives"] * 100:.0f}%'))
    for H in (168, 336):
        r = qrow("24/7 coverage", lam, H)
        rows.append((f"{H}", f"{r['reviews_per_week_capacity']:.0f}", f"{r['weeks_to_299']:.1f}", f"{r['p50_h'] * 60:.0f} min", f"{r['p95_h'] * 60:.0f} min",
                     f"{r['p50_h'] * 60:.0f} min", f"{r['p95_h'] * 60:.0f} min", "100%"))
    tbl = table(["Reviewer hours / week", "Reviews / week", "Weeks to 299 reviews", "Weekday day: median wait", "p95 wait", "Weekday evening: median wait", "p95 wait", "Arrive on shift (day / evening)"],
                rows, num_cols=(0, 1, 2, 3, 4, 5, 6, 7))
    full = []
    for scn in ("weekday daytime", "weekday evening", "24/7 coverage"):
        hs = (168, 336) if scn.startswith("24") else (5, 10, 20, 40, 80)
        body = ""
        for H in hs:
            tds = ""
            for l in Q["lams"]:
                r = qrow(scn, l, H)
                tds += f'<td class="n">{"backlog grows" if r["overloaded"] else f"{r['p95_h']:.1f} h"}</td>'
            body += f'<tr><td>{H}</td>{tds}</tr>'
        full.append(f'<p class="hint" style="margin-top:14px"><b>{scn}</b>, p95 turnaround</p>' + table(["Reviewer hours / week", *[f"{l} items / week" for l in Q["lams"]]], [body], num_cols=(0, 1, 2, 3)))
    r10 = qrow("weekday daytime", lam, 10)
    r80 = qrow("weekday daytime", lam, 80)
    r168 = qrow("24/7 coverage", lam, 168)
    return f'''
<section class="sec first">
  <h2>Part-time clinicians cannot check every answer before a family sees it</h2>
  {pair(f"<p>Families write in the evening and on weekends. Part-time reviewers work weekday hours. With 10 reviewer-hours a week, {r10['on_shift_when_message_arrives'] * 100:.0f}% of messages arrive while someone is on shift. Even with 80 hours, a weekday-only desk is on shift for {r80['on_shift_when_message_arrives'] * 100:.0f}% of them.</p><p>So the plan cannot be &ldquo;a clinician approves each answer first.&rdquo; The clinician has to move earlier: approve the library of answers once, and let the AI assemble only from approved material for anything high-risk. Review of generated answers happens afterwards, on a sample.</p>",
        f"<p>Discrete-event simulation of review-before-send: Poisson arrivals shaped by hour of day, FIFO queue, reviewers on fixed weekday windows, lognormal review time (median {A['service_median_min']:.0f} min, mean {SVC_MEAN:.1f}). {A['reps']} replications of {A['sim_weeks']} weeks per cell, first {A['warmup_weeks']} weeks discarded. Turnaround runs from the family&rsquo;s message to the reviewer&rsquo;s decision. Table shows {lam} items a week needing review.</p>")}
  <p>{tag("a")} the arrival pattern, the review time and the 120 items a week are assumptions. {tag("m")} what a queue does with them. Change any of it in <code>sim_queue.py</code>.</p>
  {figure('<div class="scroll">' + chart + '</div>' + legend([("Weekdays, daytime (9 to 5 style)", BLUE), ("Weekday evenings", ORANGE), ("24/7 coverage", AQUA)]),
          "Share of family messages that arrive while at least one reviewer is on shift, by paid reviewer hours per week. Adding hours to a weekday schedule flattens out: the nights and weekends stay uncovered.")}
</section>

<section class="sec">
  <h2>Turnaround by staffing</h2>
  <p class="lede">At {r168['H']} hours a week the queue is fast, because someone is always on, and almost idle: {r168['utilization'] * 100:.0f}% busy. That is about four full-time people to review {lam} items a week.</p>
  {tbl}
  <details class="more"><summary>Other traffic levels (p95 turnaround)</summary>{"".join(full)}</details>
  <div class="note"><b>What this changes in the plan.</b> Tier 1 and Tier 2 questions are answered only from clinician-approved cards, so the review happens once, in advance, when the card is written. Generated answers (Tier 3) get sampled review after the fact. Emergencies go to 911, 988 and the SAMHSA helpline immediately, because no part-time desk can be the safety net.</div>
</section>

<section class="sec">
  <h2>How long the evidence takes to collect</h2>
  {pair("<p>Reviewing is slow, and each kind of question needs its own pile of clean reviews. This calculator turns reviewer hours into calendar weeks.</p>",
        f"<p>Reviews per week = hours &times; 60 / minutes per review. Required reviews from the exact bound, zero flags, 95% confidence. Default {SVC_MEAN:.1f} minutes is the simulation&rsquo;s mean review time.</p>")}
  <div class="calc" id="cap">
    <div>
      <div class="row"><label for="k-h">Reviewer hours per week</label><input id="k-h" type="number" min="0.5" step="0.5" value="8"></div>
      <div class="row"><label for="k-m">Minutes per review</label><input id="k-m" type="number" min="1" step="0.5" value="{SVC_MEAN:.1f}"></div>
    </div>
    <div class="out" id="k-out" aria-live="polite"></div>
  </div>
</section>
'''


# =========================================================================== 4. Router
def panel_router():
    T = RT["test"]
    P = RT["probe"]

    def line(split, v, label):
        r = RT[split][v]
        n1 = r["n"]["1"]
        caught = r["confusion"][0][0]
        t1 = f"{caught} of {n1} <span class=\"hint\">(&ge;{r['tier1_recall_lb95'] * 100:.0f}%)</span>" if n1 else "&ndash;"
        under = sum(r["under"].values())
        over = sum(r["over"].values())
        return (label, f"{r['total']}", f"{r['exact']}", t1, f"{under}", f"{over}")

    rows = [line("dev", "v0", "Keyword list, dev set"), line("dev", "v2", "Rule set, dev set (used to write it)"),
            line("test", "v0", "Keyword list, frozen test"), line("test", "v2", "Rule set, frozen test"),
            line("probe", "v0", "Keyword list, probes"), line("probe", "v2", "Rule set, probes")]
    res = table(["Router and set", "Messages", "Right tier", "Urgent messages caught", "Under-triaged", "Over-triaged"], rows, num_cols=(1, 2, 3, 4, 5))
    # failures
    miss = [x for x in T["v2"]["rows"] if x["needed"] != x["assigned"]]
    mt = table(["Message", "Needed", "Got", "Why"],
               [(esc(x["text"]), f"Tier {x['needed']}", f"Tier {x['assigned']}", esc(x["why"][0])) for x in miss])
    kinds = P["kinds"]
    byk = {}
    for x in P["v2"]["rows"]:
        k = kinds[x["id"]]
        if k == "benign":
            continue
        d = byk.setdefault(k, [0, 0])
        d[1] += 1
        d[0] += x["assigned"] == 1
    names = {"es": "Spanish", "typo": "Misspelled", "indirect": "Indirect or euphemistic"}
    pk = table(["Urgent probes written to break the rules", "Caught", "Sent to"],
               [(names[k], f"{c} of {n}", "ordinary answer or decline") for k, (c, n) in byk.items()], num_cols=(1,))
    benign = [x for x in P["v2"]["rows"] if kinds[x["id"]] == "benign"]
    ben_up = sum(1 for x in benign if x["assigned"] < x["needed"])
    t2v = T["v2"]
    p1 = P["v2"]["n"]["1"]
    return f'''
<section class="sec first">
  <h2>Deciding how much human oversight a message needs, before any AI text exists</h2>
  {pair("<p>The first thing the system does with a family&rsquo;s message is decide how careful to be. An overdose gets an emergency card and a human alert, not a paragraph. A medication question gets a clinician-approved card, not something the AI made up. An ordinary &ldquo;how do I talk to him&rdquo; gets a cited answer.</p><p>When rules disagree, the more careful tier wins. Try it below, then try to break it.</p>",
        f"<p>A rules-based triage router ({RT['n_rules']} regular-expression rules, one JSON file read identically by Python and the browser demo; {PAR['compared']} test messages compared, {PAR['disagreements']} disagreements). Tier 1 urgent, 2 clinical-adjacent, 3 family support, 4 out of scope. Normalisation, then ordered rules with fail-upward precedence. Informational questions that mention an overdose are down-weighted unless an urgency cue is present.</p>")}
  <div class="demo" id="demo">
    <div>
      <label for="d-in" style="font-weight:700;font-size:14.5px">A message from a family member</label>
      <textarea id="d-in" placeholder="Type something, or pick an example"></textarea>
      <div class="chips"><span class="lab">Works:</span>
        <button type="button" data-q="my husband took too many pills and won't wake up">overdose</button>
        <button type="button" data-q="Is it safe for him to stop drinking all at once?">withdrawal</button>
        <button type="button" data-q="how do I talk to my son about his drinking without a fight">talking</button>
        <button type="button" data-q="what's the weather tomorrow">off topic</button></div>
      <div class="chips"><span class="lab">Breaks it:</span>
        <button type="button" data-q="mi hija dice que quiere morir">Spanish</button>
        <button type="button" data-q="shes unconsious on the flor">misspelled</button>
        <button type="button" data-q="he's out cold and I can't shake him awake">indirect</button>
        <button type="button" data-q="I can't do this anymore, the app keeps logging me out">false alarm</button></div>
    </div>
    <div id="d-out" class="verdict t4" aria-live="polite"></div>
  </div>
</section>

<section class="sec">
  <h2>Results, including the ones that look bad</h2>
  <p class="lede">Three message sets, written by one person: a development set used to write the rules, a test set written before the rules and run once (file hash recorded), and a probe set written after the rules were frozen, to break them.</p>
  {res}
  <div class="cols3">
    <div class="fact"><b>{T["v2"]["confusion"][0][0]} of {T["v2"]["n"]["1"]}</b><small>urgent test messages caught</small><p>Even a perfect score on {T["v2"]["n"]["1"]} urgent cases only shows recall of at least {T["v2"]["tier1_recall_lb95"] * 100:.0f}% (95% confidence). Showing 97% needs 99 urgent cases, all caught. {tag("m")}</p></div>
    <div class="fact"><b>0 of {p1}</b><small>urgent probes caught</small><p>The same rules that scored {T["v2"]["confusion"][0][0]} of {T["v2"]["n"]["1"]} on my test set caught none of the probes. Every miss was silent: an ordinary answer or a polite decline. {tag("m")}</p></div>
    <div class="fact"><b>{ben_up} of {len(benign)}</b><small>harmless messages sent upward</small><p>Words like &ldquo;overdosed&rdquo; or &ldquo;can&rsquo;t do this anymore&rdquo; fire the emergency path on a joke about coffee or a login bug. That is the price of failing upward, and it costs reviewer hours. {tag("m")}</p></div>
  </div>
  <h3>Where the rule set misses</h3>
  <p>Frozen test set, {len(miss)} of {t2v["total"]} in the wrong tier:</p>
  {mt}
  <p style="margin-top:20px">Probes, by how they were written to break it:</p>
  {pk}
  <div class="caveat"><b>Read these numbers as a smoke test, not a validation.</b> I wrote the dev, test and probe sets, and the rules, so the 100% on the test set overstates what a stranger&rsquo;s messages would get. The probe result is the more honest number. A real held-out set has to come from real research transcripts, labelled by clinicians.</div>
</section>

<section class="sec">
  <h2>What I would build on top of it</h2>
  <div class="cards">
    <div><h3>Unrecognised means upward</h3><p>Today an unmatched message is declined as out of scope. Out of scope should need positive evidence. Anything the router cannot read, in any language, should show the crisis card and go to a human.</p></div>
    <div><h3>Language first</h3><p>Two of the supports I checked offer Spanish. A rules list in English only fails the whole Spanish-speaking audience silently. Decide the launch languages in Stage 0, and test each one.</p></div>
    <div><h3>Layers, not one filter</h3><p>Rules for the obvious, a classifier trained on clinician-labelled research transcripts for the rest, a model-based check on the answer before it is shown, and humans auditing near-misses every week.</p></div>
    <div><h3>A replay set that only grows</h3><p>Every message that was misrouted becomes a permanent test. Every change to a rule, prompt, model or library runs the full set before release.</p></div>
  </div>
  <p class="hint">These four are design, not measurements. I have not tested the layered version.</p>
</section>
'''


# =========================================================================== 5. Governed content
HAZ = [
    # id, hazard, who is hurt, severity, likelihood, control, proof
    ("H01", "A message describing an overdose, self-harm or violence is treated as an ordinary question", "Person in danger", 5, 3,
     "Router with fail-upward rules; crisis card on every screen; unknown language shows the card; on-call alert", "Clinician-labelled replay set: at least 99 urgent cases all caught (97% lower bound), rerun on every change"),
    ("H02", "Advice to stop alcohol or benzodiazepines suddenly", "Person using", 5, 2,
     "Withdrawal and tapering questions are Tier 2: approved cards only, never generated. The FDA boxed warning (2020) says abrupt stops can cause withdrawal reactions, including seizures, that can be life-threatening", "Golden questions on withdrawal, tapering and mixing; card sign-off by a named clinician"),
    ("H03", "Wrong or incomplete overdose-response guidance (naloxone)", "Person overdosing", 5, 2,
     "Approved card only, checked against product labelling and SAMHSA material; version-stamped; review date shown", "Card has approver, date and source; expired card cannot render"),
    ("H04", "Language the evidence does not support: ultimatums, confrontation, shaming", "Family relationships", 4, 3,
     "Tier 3 answers only from approved sources; style rules; directive advice on custody or legal steps is refused and handed off", "Sample-review rubric with a flag for directive advice; canary items of this type"),
    ("H05", "Invented or outdated resources: phone numbers, programs, facilities", "Family in need", 4, 3,
     "Resource directory is a database record, never generated text; weekly number and link check", "Check log: 100% of listed numbers verified in the last 7 days"),
    ("H06", "Stigmatising wording (&ldquo;addict&rdquo;, &ldquo;clean&rdquo;, &ldquo;abuse&rdquo;)", "Family and loved one", 3, 4,
     "Language lint from the NIDA preferred-language guidance, applied to library and to generated text", "Lint passes in the build; sampled review"),
    ("H07", "Privacy: details about a loved one&rsquo;s substance use shared with third parties", "Family and loved one", 5, 2,
     "No advertising or analytics scripts on health pages; collect little, keep it briefly; counsel decides how 42 CFR Part 2 and the FTC rule apply", "Network-call audit on every release: no third-party health data calls"),
    ("H08", "Over-reliance: treating the AI as a counsellor or a clinician", "User", 4, 3,
     "Plain statement that this is an AI and education, not treatment; limits on session length; one-tap handoff to a human helpline", "Comprehension question in closed beta: users can say what it is and is not"),
    ("H09", "Referral bias toward paying treatment providers", "Family in need", 4, 2,
     "No paid placement; published criteria for what appears in the directory", "Referral audit each quarter"),
    ("H10", "Silent change in behaviour when the model provider updates a model", "All", 4, 3,
     "Pinned model versions; every model, prompt or library change runs the regression and canary suite first", "Suite green before release; release blocked otherwise"),
    ("H11", "Reviewer fatigue or drift: the miss rate rises over time", "All", 4, 3,
     "Canaries in about 5% of the queue; rotating reviewers; calibration sessions", "Weekly canary catch rate at or above the launch-gate value"),
    ("H12", "Instructions hidden in user text or retrieved pages change the AI&rsquo;s behaviour", "All", 3, 3,
     "No tools or actions for the model; retrieved text treated as data; output checked against the approved sources", "Adversarial test set run on every release (NIST AI 600-1 suggests regular adversarial testing)"),
    ("H13", "Approved pages go out of date and are still served", "Family", 3, 4,
     "Every page has an expiry date; the system refuses to use an expired page; reviewers see a due-soon list", "Share of served content in date: 100% is a hard gate"),
    ("H14", "Messages in a language or reading level the system was not tested on", "Spanish-speaking and low-literacy families", 4, 4,
     "Launch languages decided up front; unsupported language shows the crisis card and a human route; reading level checked on every card", "Per-language golden sets; the probe result above (0 of 6 Spanish) is the baseline to beat"),
]

COMPLIANCE = [
    ("42 CFR Part 2", "Confidentiality rules for substance use disorder treatment records. The 2024 final rule aligned them more closely with HIPAA. Compliance date was February 16, 2026, and the HHS Office for Civil Rights now enforces.",
     "Matters if the platform ever receives records from a treatment program, or partners with one. Default: do not ingest treatment records. Counsel decides what is a Part 2 program or lawful holder."),
    ("FTC Health Breach Notification Rule", "Amended in 2024 (effective July 29, 2024) to cover health apps outside HIPAA. A breach includes an unauthorised disclosure, such as sharing health data with an advertiser, not only a hack.",
     "No advertising pixels or third-party analytics on pages where someone describes a family member&rsquo;s use. First-party measurement only."),
    ("State laws on AI and mental health", "California SB 243, Illinois HB 1806, Nevada AB 406, New York S 3008 and Utah HB 452 address disclosure, crisis protocols, and AI offering therapy. They differ, and they change.",
     "Position the product as education and navigation, never as counselling or therapy. Disclose that it is an AI. Have counsel map the states the first families live in."),
    ("FDA", "In November 2025 the Digital Health Advisory Committee discussed generative-AI mental health devices (recommendations, not guidance): risk-based oversight, predefined human escalation, one-tap escalation, stepwise rollout, postmarket monitoring.",
     "Intended use and claims decide the category. Keep claims at education and navigation on purpose, and use the committee&rsquo;s staged, monitored approach anyway."),
    ("NIST AI 600-1 (July 2024)", "Voluntary generative-AI profile of the NIST AI Risk Management Framework. It names confabulation, human-AI configuration, information integrity and data privacy among its twelve risks, and suggests recording who provides human oversight, setting minimum thresholds before deployment, and planning how to halt a system.",
     "The hazard log and launch gates map onto it directly. It gives an outside reference when the board asks &ldquo;according to what?&rdquo;."),
]

SEEDS = [
    ("SAMHSA National Helpline", "Free, confidential treatment referral and information, 24/7/365, English and Spanish: 1-800-662-HELP (4357).", "Tier 1 crisis card and directory", "Check hours and numbers weekly."),
    ("NIDA, Words Matter", "Preferred language: person with a substance use disorder, not addict; &ldquo;use&rdquo; or &ldquo;misuse&rdquo;, not &ldquo;abuse&rdquo;; remission or recovery, not &ldquo;clean&rdquo;.", "House style and language lint", "Applies to wording, not medical content."),
    ("FDA Drug Safety Communication, Sept 23, 2020", "Benzodiazepine boxed warning: stopping suddenly or cutting the dose too fast can cause withdrawal reactions, including seizures, that can be life-threatening.", "Tier 2 withdrawal card", "Needs a clinician to write the family-facing version."),
    ("Partnership to End Addiction", "Free family supports: helpline, text support, online coaching, support groups.", "Directory and benchmark for response times", "Their page states text and email responses within 24 hours."),
    ("Allies in Recovery", "Membership programme built on CRAFT, with self-guided video modules and live groups led by a psychotherapist.", "Benchmark for family-skills content", "Its outcome figures are self-reported surveys."),
    ("CDC / NCHS provisional overdose data", "About 69,973 US overdose deaths in 2025, down nearly 14% from 81,313 in 2024, the third straight annual decline. Provisional.", "Context cards", "Figures are provisional and will be revised."),
]


def panel_content():
    hz = sorted(HAZ, key=lambda h: (-h[3] * h[4], h[0]))
    hrows = []
    for hid, hz_t, who, s, l, ctrl, proof in hz:
        sc = s * l
        cls = "bad" if sc >= 15 else ("mid" if sc >= 12 else "a")
        hrows.append((hid, hz_t, who, f'<span class="tag {cls}">{sc}</span> <span class="hint">{s} &times; {l}</span>', ctrl, proof))
    htab = table(["ID", "What could go wrong", "Who is hurt", "Risk (severity &times; likelihood)", "Control", "How I would prove the control works"], hrows)
    ctab = table(["Rule or framework", "What it is", "What it means for the product"], COMPLIANCE)
    stab = table(["Source", "What it gives us", "Where it would be used", "Caveat"], SEEDS)
    path = '''
<svg class="chart" viewBox="0 0 860 300" style="min-width:760px" role="img" aria-label="Message flows to a router, then to one of four paths">
 <defs><marker id="ar" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0 0L8 4L0 8z" fill="#47536a"/></marker></defs>
 <g font-family="inherit">
  <rect x="6" y="116" width="112" height="56" rx="8" fill="#fff" stroke="#9aa5ba"/><text x="62" y="140" text-anchor="middle" class="lab">Family</text><text x="62" y="158" text-anchor="middle">message</text>
  <rect x="170" y="108" width="128" height="72" rx="8" fill="#e8f0fc" stroke="#2a78d6"/><text x="234" y="136" text-anchor="middle" class="lab">Risk router</text><text x="234" y="154" text-anchor="middle">rules, then more</text><text x="234" y="168" text-anchor="middle">careful wins</text>
  <path d="M118 144H170" stroke="#47536a" stroke-width="1.5" marker-end="url(#ar)" fill="none"/>
  <path d="M298 130C340 130 340 38 378 38" stroke="#47536a" stroke-width="1.5" marker-end="url(#ar)" fill="none"/>
  <path d="M298 138C340 138 340 112 378 112" stroke="#47536a" stroke-width="1.5" marker-end="url(#ar)" fill="none"/>
  <path d="M298 150C340 150 340 188 378 188" stroke="#47536a" stroke-width="1.5" marker-end="url(#ar)" fill="none"/>
  <path d="M298 158C340 158 340 262 378 262" stroke="#47536a" stroke-width="1.5" marker-end="url(#ar)" fill="none"/>
  <rect x="380" y="10" width="236" height="56" rx="8" fill="#fbeaea" stroke="#d03b3b"/><text x="394" y="32" class="lab">Tier 1  Urgent</text><text x="394" y="50">Static crisis card. Human alerted.</text>
  <rect x="380" y="84" width="236" height="56" rx="8" fill="#fff3e6" stroke="#ec835a"/><text x="394" y="106" class="lab">Tier 2  Clinical</text><text x="394" y="124">Approved cards only, else handoff.</text>
  <rect x="380" y="160" width="236" height="56" rx="8" fill="#f1f7fe" stroke="#86b6ef"/><text x="394" y="182" class="lab">Tier 3  Family support</text><text x="394" y="200">Grounded answer with citations.</text>
  <rect x="380" y="234" width="236" height="56" rx="8" fill="#f4f6fa" stroke="#c5ccda"/><text x="394" y="256" class="lab">Tier 4  Out of scope</text><text x="394" y="274">Decline kindly, point elsewhere.</text>
  <path d="M616 188H664" stroke="#47536a" stroke-width="1.5" marker-end="url(#ar)" fill="none"/>
  <rect x="666" y="150" width="190" height="76" rx="8" fill="#fff" stroke="#9aa5ba"/><text x="680" y="172" class="lab">Checks before showing</text><text x="680" y="190">every claim has a source</text><text x="680" y="204">source is approved and</text><text x="680" y="218">in date, wording lint</text>
  <rect x="666" y="236" width="190" height="54" rx="8" fill="#fff" stroke="#9aa5ba"/><text x="680" y="258" class="lab">After the fact</text><text x="680" y="276">sampled human review</text>
  <path d="M761 226V236" stroke="#47536a" stroke-width="1.5" marker-end="url(#ar)" fill="none"/>
 </g>
</svg>'''
    life = '''
<svg class="chart" viewBox="0 0 860 150" style="min-width:760px" role="img" aria-label="Content lifecycle from draft to expired">
 <defs><marker id="ar2" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0 0L8 4L0 8z" fill="#47536a"/></marker></defs>
 <g>
  <rect x="4" y="46" width="108" height="48" rx="8" fill="#f4f6fa" stroke="#c5ccda"/><text x="58" y="75" text-anchor="middle" class="lab">Draft</text>
  <rect x="152" y="46" width="130" height="48" rx="8" fill="#fff" stroke="#9aa5ba"/><text x="217" y="68" text-anchor="middle" class="lab">Clinical review</text><text x="217" y="84" text-anchor="middle">named approver</text>
  <rect x="322" y="46" width="108" height="48" rx="8" fill="#e8f0fc" stroke="#2a78d6"/><text x="376" y="75" text-anchor="middle" class="lab">Approved</text>
  <rect x="470" y="46" width="108" height="48" rx="8" fill="#e5f4e5" stroke="#0ca30c"/><text x="524" y="68" text-anchor="middle" class="lab">Live</text><text x="524" y="84" text-anchor="middle">has an expiry</text>
  <rect x="618" y="46" width="108" height="48" rx="8" fill="#fff3e6" stroke="#ec835a"/><text x="672" y="68" text-anchor="middle" class="lab">Due</text><text x="672" y="84" text-anchor="middle">30 days left</text>
  <rect x="756" y="46" width="100" height="48" rx="8" fill="#fbeaea" stroke="#d03b3b"/><text x="806" y="68" text-anchor="middle" class="lab">Expired</text><text x="806" y="84" text-anchor="middle">never served</text>
  <path d="M112 70H152M282 70H322M430 70H470M578 70H618M726 70H756" stroke="#47536a" stroke-width="1.5" marker-end="url(#ar2)" fill="none"/>
  <path d="M672 94C672 130 217 130 217 98" stroke="#47536a" stroke-width="1.5" marker-end="url(#ar2)" fill="none"/><text x="445" y="124" text-anchor="middle">re-review resets the clock</text>
  <path d="M217 46C217 14 58 14 58 44" stroke="#47536a" stroke-width="1.5" marker-end="url(#ar2)" fill="none"/><text x="137" y="12" text-anchor="middle">changes requested</text>
 </g>
</svg>'''
    return f'''
<section class="sec first">
  <h2>Every sentence a family reads traces to a page a clinician approved</h2>
  {pair("<p>The AI does not get to know things. It gets to quote a library. Each page in the library has a named clinician who approved it, a date, a source and an expiry. If a page expires, the answers that used it stop. If no approved page fits the question, the system says it does not know and offers a human.</p><p>That makes the review work finite and visible: a library you can count, instead of an AI whose every answer needs checking.</p>",
        "<p>Retrieval is filtered before ranking: <code>status = live AND expires_at &gt; now AND tier_allowed</code>. Generation is allowed only in Tier 3, must cite retrieved passages, and a post-check rejects any claim without an approved source (the NIST profile suggests verifying sources and citations before launch and during operation). Retrieved text is data, not instructions. Records carry provenance fields: publisher, URL, licence or reuse terms, approver, approval date, expiry, language, reading level, tier.</p>")}
  {figure('<div class="scroll">' + path + '</div>', "How a message moves through the system. The checks box applies to Tier 3 only; Tier 1 and 2 show approved cards as written.")}
  {figure('<div class="scroll">' + life + '</div>', "Life of a library page. The system, not a person, refuses to serve an expired page.")}
</section>

<section class="sec">
  <h2>Where the library could start</h2>
  <p class="lede">Public sources I checked while preparing this. I would use them as seeds and benchmarks, and a clinician would write and approve the family-facing text. Reuse terms need checking page by page.</p>
  {stab}
</section>

<section class="sec">
  <h2>Hazard log</h2>
  {pair("<p>The list of ways this could hurt a family, scored, with what stops each one and how we would know the control works. It is the document the launch gates answer to. This is a first draft written before any research; the foundation&rsquo;s clinicians would rewrite half of it.</p>",
        "<p>Severity and likelihood on a 1&ndash;5 scale, risk = product, highest first. Draft in the style of a clinical risk-management hazard log. Scores are my judgement, shown to be argued with, not measurements.</p>")}
  {htab}
</section>

<section class="sec">
  <h2>What applies, and who decides</h2>
  <p class="lede">I am not a lawyer, and these five need counsel before anything is built on them. The summaries come from the secondary sources listed in the last tab.</p>
  {ctab}
</section>
'''


# =========================================================================== 6. Roadmap
def panel_roadmap():
    n1 = EV["worked"]["n_for_1pct_k0"]
    cap8 = 8 * 60 / SVC_MEAN
    ncert82 = EV["n_clean_to_certify_1pct_true_rate"]["0.82"]
    scope_rows = []
    for s in (1, 2, 4, 8):
        tot = s * ncert82
        scope_rows.append((s, f"{tot:,}", f"{tot / cap8:.0f}", f"{tot / (2 * cap8):.0f}"))
    scope = table(["Separate topic areas to launch", "Clean reviews needed", "Weeks at 8 reviewer-hours", "Weeks at 16"], scope_rows, num_cols=(0, 1, 2, 3))
    stages = [
        ("Stage 0  Decide", "Weeks 1 to 4",
         ["One integrated plan across research, content and engineering", "Decision log started; hazard log v1; evidence thresholds agreed before any testing", "First family situation chosen from the research; launch languages chosen; named clinical approver"],
         "Ten open decisions each have an owner and a date. A clinician has agreed to approve content. The thresholds in the next stages are written down."),
        ("Stage 1  Library", "Weeks 5 to 12",
         ["Clinician-approved cards for Tier 1 and Tier 2, resource directory, house language rules", "Published as a plain site with a human helpline route. No AI text yet", "Router replay set built from research transcripts, labelled by clinicians"],
         "Every live card has an approver, a date, a source and an expiry. Replay set has at least 99 urgent cases, all caught, for a 97% lower bound."),
        ("Stage 2  Retrieve", "Weeks 13 to 20",
         ["Search over the approved library that returns passages with citations, or says it does not know", "Gold question set from real family questions", "No generated text"],
         "No answer without a citation: 100%. Abstains correctly on questions outside the library. Retrieval targets agreed in Stage 0 are met on the gold set."),
        ("Stage 3  Generate, staff only", "Weeks 21 to 30",
         ["Tier 3 answers written by the AI from retrieved passages, seen only by staff", "Every answer reviewed; canaries in about 5% of the queue", "Weekly evidence note: reviews, flags, canary catch rate"],
         f"Per topic area: {ncert82} clean reviews at 82% measured reviewer sensitivity ({n1} if reviewers are shown to catch everything), after at least 56 canaries pin the catch rate to +/- 10 points."),
        ("Stage 4  Closed beta", "Weeks 31 to 42",
         ["Invited families; all four tiers live; sampled review afterwards; incident process with a named on-call human", "Research on whether families use the skills, not just whether they log in"],
         f"At least {n_needed(0.005 * 0.82, 0)} clean sampled reviews per topic area (0.5% or lower, at 82% measured reviewer sensitivity), no Tier 1 miss on live replay, escalations handed to a human within the time agreed in Stage 0."),
        ("Stage 5  MVP launch", "Week 43 onward",
         ["Public launch of the scope that cleared Stage 4", "Same gates keep running: canaries, replay set, expiry, weekly evidence note", "Rollback plan rehearsed before launch day"],
         "The board has seen the evidence note and a rollback rehearsal. Anything not cleared stays off."),
    ]
    st = "".join(
        f'<div class="stage"><div><h3>{esc(t)}</h3><div class="wk">{esc(w)}</div></div><div><ul>{"".join(f"<li>{esc(x)}</li>" for x in items)}</ul>'
        f'<div class="gate"><b>Gate to the next stage</b>{esc(g)}</div></div></div>'
        for t, w, items, g in stages)
    roles = table(["Role", "Hours / week", "Does"],
                  [("Product lead", "15 to 20", "Roadmap, decision log, backlog, partners, the weekly evidence note"),
                   ("Clinical approver", "3 to 5", "Approves cards; owns the hazard log with me; reviews near-misses"),
                   ("Content editor", "10 to 12", "Writes and maintains the library, language rules, expiry dates"),
                   ("Engineer(s)", "16 to 24", "Router, retrieval, review queue, tests, release gates"),
                   ("Researcher / designer", "8 to 10", "Interviews, usability, comprehension checks"),
                   ("Reviewers", "8 to 16", "Sample review and canaries; the number comes from the capacity tab"),
                   ("Counsel", "as needed", "Part 2, the FTC rule, state laws, wording of claims")],
                  num_cols=())
    rhythm = table(["When", "What", "Output"],
                   [("Monday", "One-page written plan: what ships, what is blocked, who owns each", "Plan post, read async"),
                    ("Wednesday", "30 minutes, decisions only; anything undecided gets an owner and a date", "Decision log entries within 24 hours"),
                    ("Friday", "State of the evidence: reviews done, flags, canary catch rate, expiries due", "One page for the foundation"),
                    ("Per partner", "One intake form, one owner, one running list of asks with due dates", "No requests lost in email")])
    return f'''
<section class="sec first">
  <h2>A roadmap where each stage must earn the next</h2>
  {pair("<p>The brief says there is patient funding and no rush, and that each piece should be proven before the next is added. This is that, written as stages with a gate at the end of each. A gate is a thing you can check, such as a number of clean reviews or a list of approved pages, not a feeling.</p><p>The dates are a guess to make the plan concrete. The gates matter more than the dates.</p>",
        "<p>Stage-gated plan with exit criteria stated in advance, using the bounds from the Evidence and Reviewer tabs. Thresholds are set per risk tier before testing, so nobody tunes them to what the system happens to achieve. Staged rollout from library to retrieval to staff-only generation to closed beta echoes the stepwise approach the FDA advisory committee discussed in November 2025.</p>")}
  {st}
</section>

<section class="sec">
  <h2>Why the first version should be narrow</h2>
  {pair(f"<p>Every separate topic area needs its own pile of clean reviews before it can launch. At 8 reviewer-hours a week that is about {cap8:.0f} reviews a week, so each extra topic adds roughly {ncert82 / cap8:.0f} weeks of review time. Launching with eight topics instead of one is not eight times the content. It is most of a year of reviewing.</p>",
        f"<p>Required reviews per stratum = {ncert82} (zero flags, 95% confidence, reviewer sensitivity 0.82, true rate at most 1%). Throughput {cap8:.0f} reviews a week at 8 reviewer-hours and {SVC_MEAN:.1f} minutes each. Pooling strata hides failures in the risky ones, so the strata are not merged.</p>")}
  {scope}
</section>

<section class="sec">
  <h2>How a small part-time team stays in step</h2>
  <p class="lede">Proposed sizing for a small, mostly part-time team. Hours are a starting point to adjust against the budget.</p>
  {roles}
  <h3>Weekly rhythm</h3>
  {rhythm}
  <p class="hint">Proposed, not measured. The foundation&rsquo;s own constraints would change both tables.</p>
</section>
'''


# =========================================================================== 7. Backlog and decisions
STORIES = [
    # id, title, stage, R, I, C, E, gate, acceptance
    ("S01", "Emergency banner on every screen", 1, 5, 5, 0.9, 1, True, "Given any screen at 320 px wide, when it loads, then 911 and 988 are visible without scrolling."),
    ("S02", "Clinician-labelled replay set from research transcripts", 1, 5, 5, 0.8, 3, True, "Given the set, when the router runs, then every urgent case routes to Tier 1; at least 99 urgent cases."),
    ("S03", "Library editor with approver, date, source and expiry", 1, 4, 4, 0.9, 3, True, "Given a page without an approver or past its expiry, when the site builds, then the page is not published."),
    ("S04", "Resource directory with weekly number and link check", 1, 5, 4, 0.9, 2, True, "Given a listed phone number that fails the weekly check, when the check runs, then the entry is hidden and an editor is notified."),
    ("S05", "Retrieval with citations and a clear &ldquo;I don&rsquo;t know&rdquo;", 2, 5, 5, 0.7, 4, True, "Given a question outside the library, when asked, then no answer text is generated and a human route is offered."),
    ("S06", "Review queue with canaries and a catch-rate dashboard", 3, 3, 5, 0.8, 3, True, "Given 5% canaries, when a week closes, then the catch rate and its interval are shown against the launch-gate value."),
    ("S07", "Conversation-skills lesson: raising a worry without a fight", 1, 4, 4, 0.7, 2, False, "Given the lesson, when a user finishes it, then they can pick the opening line they would use, and we record the choice."),
    ("S08", "Reading-level check on every card", 1, 4, 3, 0.8, 1, False, "Given a card above the Stage 0 target, when it is saved, then the editor sees a warning with the offending sentences."),
    ("S09", "Spanish versions of Tier 1 and Tier 2 cards", 4, 3, 4, 0.7, 3, False, "Given a Spanish message, when it is not recognised, then the crisis card and a human route are shown."),
]

ADRS = [
    ("ADR-001", "Tier 1 and Tier 2 answers come from approved cards, not from generation",
     "Reviewing each answer before it is sent needs someone on shift at all hours; the capacity simulation shows a part-time desk is on shift for a fraction of messages.",
     "(a) Review every answer before sending. (b) Generate everything and sample afterwards. (c) Approved cards for high-risk questions, grounded generation only for low-risk ones.",
     "(c).", "Library work comes first and the first version feels less conversational. Review effort is finite and countable.", "Revisit at the Stage 4 gate if Tier 2 coverage gaps dominate what families ask."),
    ("ADR-002", "Evidence thresholds are set per tier, and before testing",
     "A threshold chosen after seeing results gets tuned to the results. Pooled results hide failures in the riskiest tier.",
     "(a) One overall error target. (b) Per-tier targets fixed in Stage 0.",
     "(b), written into the stage gates.", "More reviews are needed, and the number is known in advance.", "Only changed by a logged decision with the clinical approver."),
    ("ADR-003", "Retrieval before generation",
     "Citing approved passages can be tested with a gold question set; free generation cannot be proven safe cheaply.",
     "(a) Build the generative assistant first. (b) Library, then retrieval, then staff-only generation.",
     "(b).", "Families get value earlier, from a library, and the risky part waits for evidence.", "Revisit if retrieval alone clears the success measures."),
    ("ADR-004", "Launch narrow: one family situation, as few topic areas as the research allows",
     "Each topic area needs its own clean reviews. Eight topics is most of a year of review time at 8 hours a week.",
     "(a) Broad coverage at launch. (b) One situation, one to two topic areas.",
     "(b).", "Fewer features at launch; a defensible safety claim for each one.", "Add an area only when its gate is cleared."),
    ("ADR-005", "No third-party advertising or analytics scripts on health pages",
     "Under the FTC&rsquo;s 2024 amendments an unauthorised disclosure of health information is a breach. A family describing a loved one&rsquo;s use is health information.",
     "(a) Standard analytics. (b) First-party, minimal measurement.",
     "(b).", "Less detailed usage data; far less privacy exposure.", "Counsel reviews at each stage."),
    ("ADR-006", "Pinned model versions behind a gateway, with a release gate",
     "A provider can change a model without changing its name in your logs. Behaviour on edge cases can shift silently.",
     "(a) Call a provider directly. (b) Gateway with pinned versions; any model, prompt or library change must pass the replay set and canaries.",
     "(b).", "Slower upgrades; every change is tested.", "Revisit if the provider offers stable, versioned snapshots with notice periods."),
    ("ADR-007", "Position the product as education and navigation, never counselling or therapy",
     "Several US states restrict AI that provides or appears to provide therapy, and FDA treats intended use as decisive.",
     "(a) Persona that talks like a counsellor. (b) Plain tool that explains, cites and refers.",
     "(b).", "Less warmth in tone, and fewer legal and clinical claims to defend.", "Counsel confirms wording before Stage 4."),
]


def panel_backlog():
    sc = lambda s: s[3] * s[4] * s[5] / s[6]
    order = sorted(STORIES, key=lambda s: (not s[7], s[2], -sc(s)))
    rows = ""
    for sid, title, stage, R, I, C, E, gate, ac in order:
        score = R * I * C / E
        chip = (f'<span class="tag bad">blocks Stage {stage} gate</span>' if gate else '<span class="tag a">not gate-blocking</span>')
        rows += (f'<div class="story"><div class="id">{sid}</div><div><b>{title}</b>'
                 f'<div class="ac"><span class="hint">Acceptance.</span> {esc(ac)}</div></div>'
                 f'<div>{chip}<div class="hint">reach {R}, impact {I}, confidence {C}, effort {E}<br>score {score:.1f}</div></div></div>')
    adrs = ""
    for aid, title, ctx, opts, dec, cons, rev in ADRS:
        adrs += (f'<details class="adr"><summary><span class="id">{aid}</span>{esc(title)}</summary><div class="body"><dl>'
                 f'<dt>Context</dt><dd>{ctx}</dd><dt>Options</dt><dd>{esc(opts)}</dd><dt>Decision</dt><dd>{dec}</dd>'
                 f'<dt>Consequences</dt><dd>{esc(cons)}</dd><dt>Revisit when</dt><dd>{esc(rev)}</dd></dl></div></details>')
    reqs = table(["#", "Requirement", "How it is checked"],
                 [("R1", "A banner with 911 and 988 is visible on every screen without scrolling, down to 320 px wide.", "Automated screenshot test on every release"),
                  ("R2", "A Tier 1 message shows the crisis card in under 1 second at the 95th percentile, without calling a model.", "Latency test on static path"),
                  ("R3", "A card renders only if it has a named approver, a date and an unexpired review. Otherwise the system shows the fallback card.", "Unit test; expired-card test in CI"),
                  ("R4", "On Tier 1 the on-call human is alerted and delivery is logged. The screen states that the service is not monitored in real time unless it is staffed around the clock.", "Alert log; wording approved by counsel and the clinical approver"),
                  ("R5", "A message in an unrecognised language, or one the router cannot read, shows the crisis card and a human route.", "Per-language golden sets"),
                  ("R6", "Tier 1 messages are used only for incident review. Not for model training, advertising or analytics.", "Data-flow audit each release"),
                  ("R7", "A clinician replays every Tier 1 and near-miss message weekly; results enter the decision log.", "Weekly log entry exists")])
    return f'''
<section class="sec first">
  <h2>From research to a backlog that can be argued with</h2>
  {pair("<p>Research findings become stories; stories get a score; anything that blocks a stage gate goes first, whatever its score. That way a pleasant feature never outranks the emergency banner.</p><p>The findings and stories below are <b>illustrative</b>. They show how I write them. Your research would replace them.</p>",
        "<p>Prioritisation by reach &times; impact &times; confidence / effort, with a lexicographic override for gate-blocking items and acceptance criteria in Given/When/Then form. Scores are judgement, kept visible so they can be disputed in the Wednesday meeting.</p>")}
  <h3>Three findings I would expect to see, and what they turn into</h3>
  <div class="cols3">
    <div><p><b>Parents search at night, mid-crisis, unsure if it is an emergency.</b></p><p class="hint">Becomes: S01, S02</p></div>
    <div><p><b>Families want something to say, not a lecture.</b></p><p class="hint">Becomes: S07, S08</p></div>
    <div><p><b>Distrust of sources tied to treatment providers.</b></p><p class="hint">Becomes: S03, S04 and ADR-005</p></div>
  </div>
  <h3>The backlog, ordered</h3>
  {rows}
  <p class="hint">Gate-blocking first, then by stage, then by score.</p>
</section>

<section class="sec">
  <h2>A requirements document you could build from</h2>
  {pair("<p>Requirements should say what the product must do and how someone will check it. Here is one for the feature that matters most: the emergency card. Each line can be tested.</p>",
        "<p>Excerpt of a one-feature requirements document: problem, scope, numbered requirements with verification, non-goals, success measures, open questions.</p>")}
  <p><b>Problem.</b> A person writing in the middle of the night about someone who may be in danger needs the right number in front of them within a second, in their language, whatever the AI does.</p>
  {reqs}
  <p style="margin-top:18px"><b>Not in scope.</b> This is not a crisis line. No AI-written text on Tier 1. No promise of monitoring we cannot staff.</p>
  <p><b>Success measures.</b> At least 99 clinician-labelled urgent cases, all caught (97% lower bound); p95 time to card under 1 second; zero renders of an expired card.</p>
  <p><b>Open questions.</b> Who is on call, and when? Which wording on monitoring has counsel&rsquo;s approval? Which languages at launch?</p>
</section>

<section class="sec">
  <h2>Decisions, written down</h2>
  <p class="lede">A decision log is only useful if each entry says what was decided, what else was considered and when to revisit it. These seven are what I would put on the table in the first two weeks, as proposals.</p>
  {adrs}
</section>
'''


# =========================================================================== 8. Code
def read(p):
    return open(os.path.join(ROOT, p)).read()


def panel_code():
    files = ["src/evidence.py", "src/sim_gate.py", "src/sim_queue.py", "src/build_rules.py", "src/router.py", "src/eval_router.py", "src/router.js"]
    blocks = "".join(codeblock(os.path.basename(f), read(f)) for f in files)
    return f'''
<section class="sec first">
  <h2>The code behind every number</h2>
  <p class="lede">Python 3 with NumPy and SciPy, no other libraries. Each file runs on its own and writes JSON that this page reads.</p>
  <div class="codeblock" data-name="run.sh"><header><span>run.sh</span><span class="acts"><button type="button" data-act="copy">Copy</button></span></header><pre><code>python3 -I src/evidence.py    results/evidence.json
python3 -I src/sim_gate.py    results/gate.json 40000 0
python3 -I src/sim_queue.py   results/queue.json 10 0
python3 -I src/build_rules.py src/rules_v2.json
python3 -I src/eval_router.py results/router.json
sha256sum -c data/router_test.sha256   # frozen test set unchanged
node src/parity.js src/rules_v2.json data/router_*.jsonl   # browser router matches Python</code></pre></div>
  <p class="hint">The three message sets are in <code>data/</code> in the source zip, with the hash of the frozen test set.</p>
  {blocks}
</section>
'''


# =========================================================================== 9. Sources
SOURCES = [
    ("The rule of three and exact bounds", [
        ("Hanley &amp; Lippman-Hand, &ldquo;If nothing goes wrong, is everything all right?&rdquo; JAMA 1983", "https://jamanetwork.com/journals/jama/article-abstract/389714"),
        ("Rule of three (statistics), summary page", "https://en.wikipedia.org/wiki/Rule_of_three_(statistics)")]),
    ("AI answers to health questions", [
        ("Ayers et al., Evaluating AI Responses to Public Health Questions, JAMA Network Open, June 2023", "https://doi.org/10.1001/jamanetworkopen.2023.17517"),
        ("HealthBench: Evaluating Large Language Models Towards Improved Human Health (arXiv)", "https://arxiv.org/abs/2505.08775")]),
    ("Family-based approaches", [
        ("Manuel et al., CRAFT: group vs self-directed delivery, pilot RCT (n = 40), J Subst Abuse Treat 2012", "https://pmc.ncbi.nlm.nih.gov/articles/PMC3331969/"),
        ("Psychiatric Times, on Miller, Meyers &amp; Tonigan 1999 (64% / 30% / 13%) and Meyers et al. 2002 (67% / 29%)", "https://www.psychiatrictimes.com/view/enlisting-family-members-address-treatment-refusal-substance-abusers"),
        ("Partnership to End Addiction, support for families", "https://drugfree.org/about-us/"),
        ("Allies in Recovery", "https://alliesinrecovery.net/")]),
    ("Facts used in cards and hazards", [
        ("CDC / NCHS, US overdose deaths decrease for a third consecutive year in 2025", "https://cdc.gov/nchs/pressroom/releases/20260513.html"),
        ("NIDA, Words Matter: preferred language for talking about addiction", "https://nida.nih.gov/drug-topics/addiction-science/words-matter-preferred-language-talking-about-addiction"),
        ("FDA Drug Safety Communication, September 23, 2020, benzodiazepine boxed warning", "https://www.fda.gov/drugs/drug-safety-and-availability/fda-requires-boxed-warning-updated-improve-safe-use-benzodiazepine-drug-class"),
        ("SAMHSA National Helpline", "https://www.samhsa.gov/find-help/helplines/national-helpline")]),
    ("Rules and frameworks (secondary summaries: confirm against the primary text)", [
        ("42 CFR Part 2, OCR guidance ahead of the February 2026 compliance date (Reed Smith)", "https://www.reedsmith.com/our-insights/blogs/health-industry-washington-watch/102mhjo/ocr-issues-part-2-guidance-ahead-of-the-february-2026-compliance-deadline/"),
        ("FTC Health Breach Notification Rule, 2024 final rule (Morrison Foerster)", "https://www.mofo.com/resources/insights/240514-ftc-issues-final-rule-to-expand"),
        ("State laws on AI chatbots and suicide prevention (ASTHO)", "https://www.astho.org/communications/blog/2026/legislative-snapshot-suicide-prevention-infrastructure-and-ai-chatbots/"),
        ("FDA Digital Health Advisory Committee, generative-AI mental health devices, November 2025 (Orrick)", "https://www.orrick.com/en/insights/2025/11/fdas-digital-health-advisory-committee-considers-generative-ai-therapy-chatbots-for-depression"),
        ("NIST AI 600-1, Generative AI Profile (July 2024), guide", "https://www.anaconda.com/blog/nist-ai-600-1-generative-ai-profile-guide")]),
]


def panel_sources():
    blocks = "".join(f'<h3>{t}</h3><ul>' + "".join(f'<li><a href="{u}" rel="noopener">{n}</a></li>' for n, u in items) + "</ul>" for t, items in SOURCES)
    return f'''
<section class="sec first src">
  <h2>Sources and what I did not verify</h2>
  <p class="lede">Everything that is a claim about the world is linked here. Everything that is a number from a simulation is in the Code tab.</p>
  {blocks}
  <div class="caveat"><b>Not verified.</b> I could not find a public website for the Sanchez Dooner Foundation, so nothing on this page describes it. The 42 CFR Part 2, FTC, state-law, FDA and NIST items come from the summaries linked above, not from the primary documents. The CRAFT trials predate digital delivery, and the one pilot of self-directed delivery was small (40 people) and underpowered, so I would not promise an engagement rate to anyone.</div>
</section>
'''


# =========================================================================== assemble
def assemble():
    tabs = [("evidence", "Evidence", panel_evidence()), ("reviewers", "Reviewer error", panel_reviewers()),
            ("capacity", "Review capacity", panel_capacity()), ("router", "Risk router", panel_router()),
            ("content", "Governed content", panel_content()), ("roadmap", "Roadmap", panel_roadmap()),
            ("backlog", "Backlog and decisions", panel_backlog()), ("code", "Code", panel_code()), ("sources", "Sources", panel_sources())]
    btns = "".join(f'<button class="tab" role="tab" id="tab-{i}" data-tab="{i}" aria-controls="panel-{i}" aria-selected="{"true" if k == 0 else "false"}" tabindex="{0 if k == 0 else -1}">{esc(l)}</button>'
                   for k, (i, l, _) in enumerate(tabs))
    panels = "".join(f'<div class="panel" role="tabpanel" id="panel-{i}" aria-labelledby="tab-{i}"{"" if k == 0 else " hidden"}><div class="wrap">{b}</div></div>'
                     for k, (i, _, b) in enumerate(tabs))
    css = read("src/web/style.css") + HERO_CSS
    js = read("src/web/app.js")
    router_js = read("src/router.js")
    logo = ('<svg width="26" height="26" viewBox="0 0 26 26" aria-hidden="true"><rect x="1" y="1" width="10" height="10" rx="2" fill="#9ec5f4"/>'
            '<rect x="15" y="1" width="10" height="10" rx="2" fill="#9ec5f4"/><rect x="1" y="15" width="10" height="10" rx="2" fill="#9ec5f4"/>'
            '<rect x="15" y="15" width="10" height="10" rx="2" fill="#fbeaea" stroke="#d03b3b" stroke-width="1.5"/></svg>')
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Launch Gates</title>
<meta name="description" content="How much human review it takes to prove a family-support AI is safe to launch, with measured simulations, a risk router, a hazard log, a stage-gated roadmap and the code.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible+Next:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{css}</style>
</head>
<body>
<header class="wrap mast"><div class="brand">{logo}Launch Gates</div><div class="by">Prepared by <b>{AUTHOR}</b> for the Sanchez Dooner Foundation product role</div></header>
<section class="wrap hero">
  <div>
    <h1>Nothing wrong in 100 reviews still leaves room for 30 in 1,000</h1>
    <p class="lede">Before an AI answers a parent at two in the morning, someone has to say how sure we are it is safe. This page works out what that takes: how many human reviews, from whom, at what hours. Every number comes from code in the last tabs, and the places where my own test failed are left in.</p>
  </div>
  <div>{hero_dots()}</div>
</section>
<nav class="tabs" aria-label="Sections"><div class="wrap"><div class="tabs-in" role="tablist">{btns}</div></div></nav>
<main>{panels}</main>
<footer class="foot"><span>Prepared by <b>{AUTHOR}</b>. {tag("m")} means the number was produced by the code in the Code tab. {tag("a")} means I chose it, and you can change it.</span><span>No cookies, no tracking, no data leaves your browser.</span></footer>
<script>window.RULES={json.dumps(RULES)};</script>
<script>{router_js}</script>
<script>{js}</script>
</body>
</html>'''


if __name__ == "__main__":
    out = os.path.join(ROOT, "site", "index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    page = assemble()
    open(out, "w").write(page)
    print(f"wrote {out} ({len(page):,} bytes)")
