// Browser/Node port of router.route_v2. Reads the same rules_v2.json as the Python router.
// Parity with Python is checked by parity.js on every message in the dev, test and probe sets.
(function (root) {
  function normalize(text) {
    var s = text.toLowerCase().replace(/[’‘`]/g, "'");
    s = s.replace(/(.)\1{2,}/g, "$1$1");
    s = s.replace(/[^a-z0-9'!\- ]/g, " ");
    return s.replace(/ +/g, " ").trim();
  }
  function compile(items) {
    return items.map(function (x) { return { id: x.id, name: x.name, rx: new RegExp(x.pattern, "i") }; });
  }
  function load(rules) {
    return {
      t1_hard: compile(rules.t1_hard), t1_soft: compile(rules.t1_soft), refuse: compile(rules.refuse),
      illicit: compile(rules.illicit), t2: compile(rules.t2), topic: compile(rules.topic),
      question_start: new RegExp(rules.question_start, "i"), urgent_cue: new RegExp(rules.urgent_cue, "i"),
      family_word: new RegExp(rules.family_word, "i")
    };
  }
  function hits(list, s) {
    var out = [];
    list.forEach(function (r) { if (r.rx.test(s)) out.push(r.id + " " + r.name); });
    return out;
  }
  function routeV2(text, R) {
    var s = normalize(text);
    var h = hits(R.t1_hard, s);
    if (h.length) return { tier: 1, why: h };
    var soft = hits(R.t1_soft, s);
    if (soft.length) {
      var informational = R.question_start.test(s) && !R.urgent_cue.test(s + (text.indexOf("!") >= 0 ? "!" : ""));
      if (!informational) return { tier: 1, why: soft };
    }
    h = hits(R.refuse, s);
    if (h.length) return { tier: 4, why: h };
    if (!R.family_word.test(s)) {
      h = hits(R.illicit, s);
      if (h.length) return { tier: 4, why: h };
    }
    h = hits(R.t2, s).concat(soft);
    if (h.length) return { tier: 2, why: h };
    h = hits(R.topic, s);
    if (h.length) return { tier: 3, why: h };
    return { tier: 4, why: ["default: no rule matched"] };
  }
  var api = { normalize: normalize, load: load, routeV2: routeV2 };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.Router = api;
})(typeof window !== "undefined" ? window : this);
