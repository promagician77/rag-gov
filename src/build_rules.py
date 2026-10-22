"""
Writes rules_v2.json, the single rule file read by BOTH router.py (Python) and router.js (browser demo).
Patterns use only syntax common to Python `re` and JavaScript RegExp, always matched case-insensitively
against the NORMALISED text (see router.normalize).

Written from the dev set and from general design principles only. The frozen test set was not consulted.
"""
import json
import sys

# ---- Tier 1: urgent. Hard rules always fire. ------------------------------------------------------
T1_HARD = [
    ("breathing stopped", r"\b(not|isn'?t|wasn'?t|stopped|stops|stop|barely|can'?t|cannot|won'?t|no longer|hardly)\b[^.]{0,20}\bbreath"),
    ("breathing sounds", r"\b(gasping|gurgl\w+|chok(ing|ed)|snoring weird\w*)\b|\bbreathing\b[^.]{0,20}\b(slow|weird|shallow|funny|strange|rattl\w+)"),
    ("unresponsive", r"\b(unresponsive|unconscious|non-?responsive|passed out|not responding|stopped responding|not waking|not moving|(won'?t|wont|can'?t|cant) (wake|respond|stay awake))\b"),
    ("nodding off", r"\bnodd?(ed|ing) (off|out)\b|\bfalling asleep (mid|in the middle)\b|\bcan'?t (get|keep) (him|her|them) (awake|to wake)"),
    ("colour change", r"\b(blue|purple|gr[ae]y|pale)\b[^.]{0,12}\b(lips|face|skin|fingers|nails)\b|\b(lips|face|skin)\b[^.]{0,12}\b(blue|purple|gr[ae]y)\b|\b(turning|still|going) (blue|purple)\b|\bcold and not\b"),
    ("took too much", r"\btoo many pills\b|\btook (too (many|much)|(a|the) (whole|bunch|handful|lot)|(\d+|eight|ten|twenty) (pills|klonopin|xanax)|a lot of)\b|\bswallowed (a )?(bunch|handful|lot|whole|all)\b|\b(whole|entire) bottle\b|\bhandful of (pills|meds)\b|\bpills (saved|stockpiled|stashed)\b|\bsaved up\b[^.]{0,20}\bpills\b"),
    ("naloxone used", r"\b(gave|used|administered|sprayed|gave him|gave her)\b[^.]{0,20}\b(narcan|naloxone)\b"),
    ("emergency words", r"\b911\b|\bambulance\b|\bparamedic\w*|\bemergency room\b"),
    ("cardiac/respiratory", r"\bchest (pain|hurts|tight\w*)\b|\bcan'?t (catch|get) (his|her|their)? ?breath\b|\bshort of breath\b|\bheart (racing|pounding)\b"),
    ("delirium now", r"\b(he|she|they)('s| is| are)\b[^.]{0,30}\b(seeing things|hallucinat\w+|confused and)\b|\bdelirium\b|\bshaking badly\b|\bshaking all over\b|\bjump(ed|ing)? (out|off|from)\b"),
    ("suicide", r"\bsuicid\w*|\bkill(ing)? (my ?self|him ?self|her ?self|them ?selves|me)\b|\b(end|ending) (it all|my life|his life|her life|their life)\b|\b(want|wants|wanted|wanting|wanna) to (die|end it)\b|\bdon'?t (want|wanna) to (be here|live|go on|exist)\b|\bdoesn'?t want to (be here|live|go on|exist)\b|\bbetter off (dead|without me)\b|\brather be dead\b|\bno reason to live\b|\bplan to end\b|\bdie slowly\b"),
    ("can't go on", r"\bcan'?t (do|take|go on|handle) (this|it) (any ?more|anymore)\b|\bjust want it to stop\b|\bgive up on (life|living)\b"),
    ("self-harm", r"\bself ?-?harm\w*|\bcutting (my ?self|her ?self|him ?self|again)\b|\bhurt (my ?self|him ?self|her ?self|them ?selves)\b|\bdoesn'?t care if (she|he|they) lives?\b|\bcutting\b[^.]{0,15}\bsays\b"),
    ("goodbye", r"\bgoodbye\b[^.]{0,20}\b(note|message|text|letter|post)\b|\b(texted|said|wrote|left|sent)\b[^.]{0,15}\bgoodbye\b"),
    ("violence", r"\b(hit|hurt|threaten\w*|chok\w+|beat|punch\w*|attack\w*|strangl\w*)\b[^.]{0,20}\b(me|us|the kids|my kids|children|my (mom|mother|wife|husband|child|baby))\b|\b(has|got|with) a (gun|knife|weapon)\b|\bafraid for my (life|safety)\b|\b(scared|afraid) to go home\b"),
    ("child exposure", r"\b(toddler|baby|infant|child|kid|kids|little (one|girl|boy))\b[^.]{0,40}\b(ate|eat|swallowed|chewing|got into|drank|licked)\b"),
]

# ---- Tier 1 soft rules: urgent UNLESS phrased as a general question with no urgency cue ----------
T1_SOFT = [
    ("overdose", r"\bod'?d\b|\bod(ed|ing)\b|\boverdos\w*|\bover dos\w*"),
    ("seizure", r"\bseiz(ure|ures|ing)\b|\bconvuls\w+|\bfoaming\b"),
]
QUESTION_START = r"^(can|could|does|do|did|what|how|why|is|are|will|would|should)\b"
URGENT_CUE = r"\b(now|right now|just|tonight|currently|help|please|hurry|emergency|he'?s|she'?s|they'?re|i think|my \w+ (is|just|was)|had a)\b|!"

# ---- Refusals and illicit requests: out of scope --------------------------------------------------
REFUSE = [
    ("hack or spy", r"\bhack\w*|\bspy on\b|\bwithout (him|her|them) knowing\b"),
    ("prompt attack", r"\bignore (all |your |previous )*instructions\b|\bsystem prompt\b"),
]
ILLICIT = [   # only when no family/relationship word is present (first-person acquisition or dealing)
    ("buy", r"\b(where|how)\b[^.]{0,30}\b(buy|get|order|score|find)\b[^.]{0,30}\b(fentanyl|xanax|adderall|oxy\w*|percocet|heroin|meth|cocaine|crack|pills|drugs|weed|molly|lsd|ketamine)\b"),
    ("buy2", r"\bcan i (buy|order|get)\b[^.]{0,30}\b(online|without a prescription|no prescription)\b"),
    ("make", r"\bhow (do i|to|can i)\b[^.]{0,20}\bmake\b[^.]{0,20}\b(meth|bong|pipe|crack|drugs|lsd|cocaine)\b"),
    ("sell", r"\b(sell|selling)\b[^.]{0,30}\b(weed|oxy\w*|pills|drugs|xanax|adderall|fentanyl|heroin|meth|coke)\b|\b(weed|oxy\w*|pills|drugs|xanax|adderall|fentanyl|heroin|meth|coke)\b[^.]{0,30}\bto sell\b"),
    ("hide", r"\bhide\b[^.]{0,20}\b(pills|drugs|weed|it)\b[^.]{0,20}\b(from the police|from police|from cops)\b"),
]

# ---- Tier 2: clinical-adjacent. A wrong answer could directly harm. -----------------------------
T2 = [
    ("medication names", r"\b(naloxone|narcan|suboxone|subutex|buprenorphine|methadone|vivitrol|naltrexone|antabuse|disulfiram|campral|acamprosate|xanax|alprazolam|klonopin|clonazepam|valium|diazepam|ativan|lorazepam|benzo\w*|gabapentin|neurontin|lyrica|tramadol|oxy\w*|percocet|vicodin|hydrocodone|adderall|ritalin|opioid\w*|fentanyl|heroin|morphine|codeine|kratom|tylenol|acetaminophen|benadryl|trazodone|seroquel|sleeping (pill|med)\w*|prescri\w+|medication\w*|meds)\b"),
    ("dosing", r"\b\d+ ?(mg|milligrams?|ml|mcg)\b|\bdos(e|es|ing|age)\b|\b(max|maximum) dose\b"),
    ("withdrawal and tapering", r"\bwithdraw\w*|\bdetox\w*|\btaper\w*|\bcold turkey\b|\ball at once\b|\bquit(ting)? (drinking|using)\b|\bcut(ting)? (back|down)\b|\b(stop|stopping|stopped)\b[^.]{0,25}\b(suddenly|abruptly|on (his|her|their) own)\b|\b(shakes|sweats|tremors)\b|\bsafe (way )?to (stop|quit|cut)\b"),
    ("mixing", r"\bmix(ing|ed)?\b|\bcombin\w+|\bwith alcohol\b|\bwhile drinking\b|\binteract\w*"),
    ("legal and coercion", r"\bmarchman\b|\bbaker act\b|\binvoluntar\w+|\bcommit(ment|ted|ting)?\b|\bforce (him|her|them|my \w+) (into|to go)\b|\bcourt[- ]ordered\b|\bcustody\b|\bpolice\b|\barrest\w*|\bjail\b|\bcops?\b|\blegal\b|\bhave to report\b|\bmandatory report\w*"),
    ("treatment suitability", r"\b(inpatient|outpatient|residential|rehab)\b[^.]{0,30}\b(better|best|which|work|worth|right)\b|\bwhich (is|are) better\b|\bbest rehab\b|\bdoes [a-z ]{0,20}\bwork\b"),
    ("medical risk cues", r"\bis (it|that) (safe|ok|okay|dangerous)\b|\bsafe (to|for)\b|\bdangerous\b|\bside effects?\b|\bcan (a person|you|he|she|someone|people) (die|overdose)\b|\bpregnan\w*|\bdrug test\w*|\btest(ed)? positive\b|\blaced\b|\bfake pills?\b|\bcounterfeit\b|\bfentanyl strips?\b|\bhallucinat\w+|\bpsychosis\b|\bparanoi\w+"),
    ("clinicians", r"\b(doctor|physician|psychiatrist|nurse|hospital|anesthesia)\b"),
]

# ---- Tier 3: on topic, general support. Anything else is out of scope (tier 4). ------------------
TOPIC = [
    ("substance and recovery words", r"\b(addict\w*|alcohol\w*|drink\w*|drank|drunk|sober\w*|recover\w*|relaps\w*|rehab\w*|treatment|substance|drug\w*|using|use disorder|enabl\w*|codepend\w*|al-?anon|nar-?anon|aa|smart recovery|intervention|boundar\w*|craft|stigma|harm reduction|support group|counsel\w*|therap\w*|vap\w*|weed|marijuana|cannabis|pills?|high)\b"),
    ("family and feelings", r"\b(son|daughter|husband|wife|brother|sister|mom|mother|dad|father|friend|boyfriend|girlfriend|partner|spouse|child|children|kid|kids|teen\w*|loved one|family|parent\w*|sibling\w*|grandson|granddaughter|niece|nephew)\b|\b(struggling|worried|worry|scared|afraid|exhausted|guilty|ashamed|angry|lonely|overwhelmed|hopeless)\b"),
    ("people and care words", r"\b(he|she|him|her|his|they|them|myself|fault|selfish|lie|lies|lying|hurting|get better|disorder|disease|management|stages of change|cope|coping)\b"),
    ("asking for help", r"\b(where to start|don'?t know what to do|dont know (where|what)|what (should|can|do) i do|need help|please help)\b"),
]
FAMILY_WORD = r"\b(son|daughter|husband|wife|brother|sister|mom|mother|dad|father|friend|boyfriend|girlfriend|partner|spouse|child|children|kid|kids|teen\w*|loved one|family|parent\w*|sibling\w*|him|his|her|he|she|they|them)\b"


def main(out):
    rules = {
        "version": "v2",
        "t1_hard": [{"id": f"1.{i + 1:02d}", "name": n, "pattern": p} for i, (n, p) in enumerate(T1_HARD)],
        "t1_soft": [{"id": f"1s.{i + 1:02d}", "name": n, "pattern": p} for i, (n, p) in enumerate(T1_SOFT)],
        "question_start": QUESTION_START, "urgent_cue": URGENT_CUE,
        "refuse": [{"id": f"4r.{i + 1:02d}", "name": n, "pattern": p} for i, (n, p) in enumerate(REFUSE)],
        "illicit": [{"id": f"4i.{i + 1:02d}", "name": n, "pattern": p} for i, (n, p) in enumerate(ILLICIT)],
        "family_word": FAMILY_WORD,
        "t2": [{"id": f"2.{i + 1:02d}", "name": n, "pattern": p} for i, (n, p) in enumerate(T2)],
        "topic": [{"id": f"3.{i + 1:02d}", "name": n, "pattern": p} for i, (n, p) in enumerate(TOPIC)],
    }
    json.dump(rules, open(out, "w"), indent=1)
    n = sum(len(rules[k]) for k in ("t1_hard", "t1_soft", "refuse", "illicit", "t2", "topic"))
    print(f"wrote {out} with {n} rules")


if __name__ == "__main__":
    main(sys.argv[1])
