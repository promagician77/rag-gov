"""Helpers and SVG charts for the Launch Gates page. No third-party libraries."""
import html
import math
import random

esc = html.escape

BLUE, ORANGE, AQUA, CRIT = "#2a78d6", "#eb6834", "#1baf7a", "#d03b3b"
INK2, MUTED = "#47536a", "#66718a"


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def tag(kind):
    return {"m": '<span class="tag m">measured</span>', "a": '<span class="tag a">assumption</span>'}[kind]


def pair(plain, tech):
    return (f'<div class="pair"><div class="plain"><h4>In plain words</h4>{plain}</div>'
            f'<div class="tech"><h4>In technical terms</h4>{tech}</div></div>')


def figure(inner, caption):
    return f'<figure class="fig">{inner}<figcaption>{caption}</figcaption></figure>'


def heat(v, vmax=0.6):
    """White to blue (step 250 of the sequential ramp), for table cells."""
    a = max(0.0, min(1.0, v / vmax)) ** 0.8
    lo, hi = (255, 255, 255), (134, 182, 239)
    r, g, b = (round(lo[i] + (hi[i] - lo[i]) * a) for i in range(3))
    return f"rgb({r},{g},{b})"


# --------------------------------------------------------------------------- hero
def hero_dots():
    rng = random.Random(7)
    bad = set(rng.sample(range(1000), 30))
    left = "".join(
        f'<rect x="{c * 16}" y="{r * 16}" width="13" height="13" rx="2" fill="#9ec5f4"/>'
        for r in range(10) for c in range(10))
    right = "".join(
        (f'<rect x="{c * 10 + .5}" y="{r * 10 + .5}" width="8" height="8" rx="1.5" fill="url(#hatch)" stroke="{CRIT}" stroke-width="1"/>'
         if r * 40 + c in bad else
         f'<rect x="{c * 10}" y="{r * 10}" width="9" height="9" rx="1.5" fill="#e3e8f1"/>')
        for r in range(25) for c in range(40))
    defs = (f'<defs><pattern id="hatch" width="3.2" height="3.2" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<rect width="3.2" height="3.2" fill="#fbeaea"/><line x1="0" y1="0" x2="0" y2="3.2" stroke="{CRIT}" stroke-width="1.5"/></pattern></defs>')
    return f'''<div class="dotfig" role="img" aria-label="Left: 100 reviewed answers, none flagged. Right: 1,000 unread answers, 30 of them marked as possibly unsafe.">
<div class="dg dg1"><svg class="dots" viewBox="0 0 159 159">{left}</svg>
<p><b>100 answers reviewed</b><br><span>No problem found in any.</span></p></div>
<div class="dg dg2"><svg class="dots" viewBox="0 0 400 250">{defs}{right}</svg>
<p><b>1,000 answers nobody has read yet</b><br><span>Hatched: up to about 30 could be unsafe, and the 100 clean reviews would look exactly the same.</span></p></div></div>'''


HERO_CSS = """
.dotfig{display:grid;grid-template-columns:minmax(0,.62fr) minmax(0,2.4fr);gap:26px;align-items:end}
.dg p{font-size:14.5px;line-height:1.4;margin:9px 0 0;color:var(--ink)}
.dg p span{color:var(--muted)}
@media (max-width:560px){.dotfig{grid-template-columns:1fr 1.6fr;gap:14px}.dg p{font-size:12.5px}}
"""


# --------------------------------------------------------------------------- charts
class Axis:
    def __init__(self, lo, hi, p0, p1, log=False):
        self.lo, self.hi, self.p0, self.p1, self.log = lo, hi, p0, p1, log

    def __call__(self, v):
        if self.log:
            t = (math.log(v) - math.log(self.lo)) / (math.log(self.hi) - math.log(self.lo))
        else:
            t = (v - self.lo) / (self.hi - self.lo)
        return self.p0 + (self.p1 - self.p0) * t


def line_chart(series, xticks, yticks, xlog, ylog, xr, yr, xlabel, ylabel, yfmt, xfmt, refs=(), notes=(),
               W=760, H=380, ml=64, mr=130, mt=16, mb=54, label_dx=10):
    """series: dicts {name,color,xs,ys,tip(fn),dots(list of idx) or None for all, label(optional)}"""
    X = Axis(xr[0], xr[1], ml, W - mr, xlog)
    Y = Axis(yr[0], yr[1], H - mb, mt, ylog)
    g = []
    for yt in yticks:
        g.append(f'<line class="grid" x1="{ml}" x2="{W - mr}" y1="{Y(yt):.1f}" y2="{Y(yt):.1f}"/>'
                 f'<text x="{ml - 8}" y="{Y(yt) + 4:.1f}" text-anchor="end">{yfmt(yt)}</text>')
    for xt in xticks:
        g.append(f'<line class="axis" x1="{X(xt):.1f}" x2="{X(xt):.1f}" y1="{H - mb}" y2="{H - mb + 5}"/>'
                 f'<text x="{X(xt):.1f}" y="{H - mb + 20}" text-anchor="middle">{xfmt(xt)}</text>')
    g.append(f'<line class="axis" x1="{ml}" x2="{W - mr}" y1="{H - mb}" y2="{H - mb}"/>')
    g.append(f'<text x="{(ml + W - mr) / 2:.0f}" y="{H - 8}" text-anchor="middle">{esc(xlabel)}</text>')
    g.append(f'<text transform="translate(16 {(mt + H - mb) / 2:.0f}) rotate(-90)" text-anchor="middle">{esc(ylabel)}</text>')
    for val, text in refs:
        y = Y(val)
        g.append(f'<line x1="{ml}" x2="{W - mr}" y1="{y:.1f}" y2="{y:.1f}" stroke="{INK2}" stroke-opacity=".45" stroke-width="1"/>'
                 f'<text x="{W - mr - 6}" y="{y - 6:.1f}" text-anchor="end" class="lab">{esc(text)}</text>')
    marks = []
    for s in series:
        pts = [(X(x), Y(y)) for x, y in zip(s["xs"], s["ys"]) if yr[0] <= y <= yr[1] and xr[0] <= x <= xr[1]]
        if len(pts) > 1 and s.get("line", True):
            d = " ".join(f'{"M" if i == 0 else "L"}{px:.1f} {py:.1f}' for i, (px, py) in enumerate(pts))
            marks.append(f'<path d="{d}" fill="none" stroke="{s["color"]}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
        idx = s.get("dots")
        for i, (x, y) in enumerate(zip(s["xs"], s["ys"])):
            if not (yr[0] <= y <= yr[1] and xr[0] <= x <= xr[1]):
                continue
            if idx is not None and i not in idx:
                continue
            vis = "" if s.get("hit_only") else f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="4.5" fill="{s["color"]}" stroke="#fff" stroke-width="2"/>'
            marks.append(vis + f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="{8 if s.get("hit_only") else 13}" fill="transparent" tabindex="0" data-tip="{esc(s["tip"](x, y))}"/>')
        if pts and s.get("label"):
            lx, ly = pts[-1]
            marks.append(f'<text class="lab" x="{lx + label_dx:.1f}" y="{ly + 4 + s.get("label_dy", 0):.1f}">{esc(s["label"])}</text>')
    for (x, y, text, dx, dy, anchor) in notes:
        marks.append(f'<text class="lab" x="{X(x) + dx:.1f}" y="{Y(y) + dy:.1f}" text-anchor="{anchor}">{esc(text)}</text>')
    return f'<svg class="chart" viewBox="0 0 {W} {H}" style="min-width:640px" role="img">{"".join(g)}{"".join(marks)}</svg>'


def legend(items):
    return '<div class="legend">' + "".join(f'<span><i style="background:{c}"></i>{esc(t)}</span>' for t, c in items) + "</div>"


def table(head, rows, cls="tbl", num_cols=()):
    h = "".join(f'<th class="{"n" if i in num_cols else ""}">{c}</th>' for i, c in enumerate(head))
    b = ""
    for r in rows:
        if isinstance(r, str):
            b += r
        else:
            b += "<tr>" + "".join(f'<td class="{"n" if i in num_cols else ""}">{c}</td>' for i, c in enumerate(r)) + "</tr>"
    return f'<div class="scroll"><table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>'


def codeblock(name, text):
    return (f'<div class="codeblock" data-name="{esc(name)}"><header><span>{esc(name)}</span>'
            f'<span class="acts"><button type="button" data-act="copy">Copy</button><button type="button" data-act="dl">Download</button></span></header>'
            f'<pre><code>{esc(text)}</code></pre></div>')
