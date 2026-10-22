"""
Risk router: decides how much human oversight a family's message needs BEFORE any AI text is written.

  tier 1  urgent            -> static crisis card (988 / 911 / helpline), no generation, alert on-call human
  tier 2  clinical-adjacent -> only clinician-approved answer cards; otherwise hand off to a human helpline
  tier 3  family support    -> retrieval-grounded answer with citations, sampled human review afterwards
  tier 4  out of scope      -> polite decline / redirect

Principle: fail upward. When two rules disagree, the more careful tier wins.

Two routers live here:
  route_v0  what most teams ship first: a short keyword list
  route_v2  the rule file rules_v2.json (also used by router.js in the browser demo)
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))


def normalize(text):
    s = text.lower().replace("’", "'").replace("‘", "'").replace("`", "'")
    s = re.sub(r"(.)\1{2,}", r"\1\1", s)                  # pleeease -> pleease
    s = re.sub(r"[^a-z0-9'!\- ]", " ", s)
    return re.sub(r" +", " ", s).strip()


# ---------------------------------------------------------------- v0: keyword list
V0_CRISIS = ["suicide", "kill myself", "kill himself", "kill herself", "overdose", "911", "dying", "emergency"]
V0_CLINICAL = ["dose", "dosage", " mg", "withdrawal", "detox"]
V0_TOPIC = ["addict", "alcohol", "drink", "drug", "rehab", "relapse", "sober", "using", "pills", "heroin", "recovery"]


def route_v0(text):
    s = text.lower()
    if any(k in s for k in V0_CRISIS):
        return 1, ["keyword:crisis"]
    if any(k in s for k in V0_CLINICAL):
        return 2, ["keyword:clinical"]
    if any(k in s for k in V0_TOPIC):
        return 3, ["keyword:topic"]
    return 4, ["default"]


# ---------------------------------------------------------------- v2: rule file
def load_rules(path=None):
    r = json.load(open(path or os.path.join(HERE, "rules_v2.json")))
    comp = lambda items: [(x["id"], x["name"], re.compile(x["pattern"], re.I)) for x in items]
    return {
        "t1_hard": comp(r["t1_hard"]), "t1_soft": comp(r["t1_soft"]), "refuse": comp(r["refuse"]),
        "illicit": comp(r["illicit"]), "t2": comp(r["t2"]), "topic": comp(r["topic"]),
        "question_start": re.compile(r["question_start"], re.I), "urgent_cue": re.compile(r["urgent_cue"], re.I),
        "family_word": re.compile(r["family_word"], re.I),
    }


def hits(rules, s):
    return [f"{i} {n}" for i, n, rx in rules if rx.search(s)]


def route_v2(text, R):
    s = normalize(text)
    h = hits(R["t1_hard"], s)
    if h:
        return 1, h
    soft = hits(R["t1_soft"], s)
    if soft:
        informational = R["question_start"].search(s) and not R["urgent_cue"].search(s + ("!" if "!" in text else ""))
        if not informational:
            return 1, soft
    h = hits(R["refuse"], s)
    if h:
        return 4, h
    if not R["family_word"].search(s):
        h = hits(R["illicit"], s)
        if h:
            return 4, h
    h = hits(R["t2"], s) + (soft if soft else [])
    if h:
        return 2, h
    h = hits(R["topic"], s)
    if h:
        return 3, h
    return 4, ["default: no rule matched"]


def read(path):
    return [json.loads(ln) for ln in open(path) if ln.strip()]
