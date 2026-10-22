// node parity.js <rules.json> <jsonl> [<jsonl> ...]  -> prints JSON {id: [tier, why...]}
const fs = require("fs");
const Router = require("./router.js");
const R = Router.load(JSON.parse(fs.readFileSync(process.argv[2], "utf8")));
const out = {};
for (const f of process.argv.slice(3)) {
  for (const line of fs.readFileSync(f, "utf8").split("\n")) {
    if (!line.trim()) continue;
    const x = JSON.parse(line);
    const r = Router.routeV2(x.text, R);
    out[x.id] = [r.tier, r.why];
  }
}
process.stdout.write(JSON.stringify(out));
