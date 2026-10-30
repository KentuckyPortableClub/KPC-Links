#!/usr/bin/env python3
"""Builds Brandon's key preview page (old key on the site vs the new Rule G key) from key-preview.json (+ key-preview-shapes.json
when the shapes run has answered). Usage: make_preview_page.py PREVIEW.json SHAPES.json PINS_DIR OUT.html"""
import html, json, math, os, sys, glob

prev = json.load(open(sys.argv[1]))
try: shapes = json.load(open(sys.argv[2]))
except Exception: shapes = {}  # noqa: BLE001
pins = {}
for f in glob.glob(os.path.join(sys.argv[3], 'US-*.json')):
    try:
        for r, v in json.load(open(f))['parks'].items():
            if len(v) > 6 and v[5] is not None: pins[r] = (v[5], v[6])
    except Exception: pass  # noqa: BLE001
E = html.escape


def svg(ref):
    old = shapes.get(f'{ref}|old') or []; new = shapes.get(f'{ref}|new') or []
    pin = pins.get(ref)
    pts = [p for s in old + new for r in s['rings'] for p in r]
    if not pts and not pin: return '<div class="noshape">No outline drawn (pin only)</div>'
    if pin: pts = pts + [[pin[1], pin[0]]]
    lat0 = sum(p[1] for p in pts) / len(pts); k = math.cos(math.radians(lat0))
    xs = [p[0] * k for p in pts]; ys = [-p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w, h = max(x1 - x0, 1e-4), max(y1 - y0, 1e-4); pad = max(w, h) * .08
    vb = f'{x0 - pad:.6f} {y0 - pad:.6f} {w + 2 * pad:.6f} {h + 2 * pad:.6f}'
    sw = max(w, h) / 220

    def path(s):
        return ' '.join('M' + ' L'.join(f'{p[0] * k:.6f},{-p[1]:.6f}' for p in r) + ' Z' for r in s['rings'])
    out = [f'<svg viewBox="{vb}" role="img" aria-label="outline of {E(ref)}" preserveAspectRatio="xMidYMid meet">']
    out += [f'<path class="o-old" d="{path(s)}" stroke-width="{sw * 1.6:.6f}"/>' for s in old]
    out += [f'<path class="o-new" d="{path(s)}" stroke-width="{sw:.6f}"/>' for s in new]
    if pin: out.append(f'<circle class="pin" cx="{pin[1] * k:.6f}" cy="{-pin[0]:.6f}" r="{sw * 3.2:.6f}"/>')
    out.append('</svg>')
    km = w * 111.32
    return ''.join(out) + f'<div class="scale">about {km:,.1f} km across</div>'


def why(s):
    o, n = len(s['old']), len(s['new'])
    if not o and n: return f'New outline: {n} official piece{"s" if n > 1 else ""}'
    if o and not n: return 'Outline taken away (now pin only)'
    if n < o: return f'{o - n} wrong piece{"s" if o - n > 1 else ""} removed'
    if n > o: return f'{n - o} piece{"s" if n - o > 1 else ""} added'
    return 'Pieces swapped'


T = prev['totals']; per = prev['per_state']
rows = ''.join(f"<tr><td>{st}</td><td>{v['parks']:,}</td><td>{v['new outline']}</td><td>{v['outline lost']}</td><td>{v['pieces added']:,}</td><td>{v['pieces removed']:,}</td><td>{v['grade changed']}</td></tr>"
               for st, v in sorted(per.items(), key=lambda kv: -(kv[1]['new outline'] + kv[1]['outline lost'] + kv[1]['grade changed'])))
cards = []
for s in prev['samples']:
    names_new = ', '.join(sorted({x[1] for x in s['new']}))[:180]
    names_old = ', '.join(sorted({x[1] for x in s['old']}))[:180]
    held = ', '.join(f"{x[1]} ({x[3].split(':')[0]})" for x in s.get('check') or [])[:200]
    cards.append(f"""<article class="park"><header><span class="st">{E(s['st'])}</span><h3>{E(s['n'] or s['ref'])}</h3><span class="ref">{E(s['ref'])}</span></header>
<div class="change">{E(why(s))} <span class="grade">{E(s['old_g'])} → {E(s['new_g'])}</span></div>
<div class="map">{svg(s['ref'])}</div>
<dl><dt>Now on the site</dt><dd>{E(names_old) or '<i>nothing (pin only)</i>'}</dd><dt>New key</dt><dd>{E(names_new) or '<i>nothing (pin only)</i>'}</dd>{f'<dt>Held for a yes/no</dt><dd>{E(held)}</dd>' if held else ''}</dl></article>""")
page = f"""<title>New Park Key Preview</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;700&family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: a survey-sheet page: summary strip, the per-state ledger, then a grid of park cards drawn old-vs-new on one scale */
:root {{ --bg:#f3f5f2; --paper:#ffffff; --ink:#1d2621; --muted:#5d6b63; --line:#d6ddd8; --new:#1f7a5c; --newfill:rgba(31,122,92,.16); --old:#b4542f; --pin:#1d2621;
  --f-display:'Barlow Condensed','Arial Narrow',sans-serif; --f-body:'IBM Plex Sans',system-ui,sans-serif; --f-mono:'IBM Plex Mono',ui-monospace,monospace }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#141a17; --paper:#1c2420; --ink:#e3ebe6; --muted:#9aaba2; --line:#2e3a34; --new:#5fc79f; --newfill:rgba(95,199,159,.18); --old:#e08a63; --pin:#e3ebe6; color-scheme:dark }} }}
:root[data-theme="dark"] {{ --bg:#141a17; --paper:#1c2420; --ink:#e3ebe6; --muted:#9aaba2; --line:#2e3a34; --new:#5fc79f; --newfill:rgba(95,199,159,.18); --old:#e08a63; --pin:#e3ebe6; color-scheme:dark }}
body {{ background:var(--bg); color:var(--ink); font:15px/1.5 var(--f-body); padding-left:max(16px,env(safe-area-inset-left,0px)); padding-right:max(16px,env(safe-area-inset-right,0px)); padding-block:28px 48px }}
main {{ max-width:1120px; margin:0 auto; display:grid; grid-template-columns:minmax(0,1fr); gap:28px }}
main > * {{ min-width:0 }}
.ledger {{ overflow-x:auto; max-width:100% }}
.ledger table {{ min-width:520px }}
h1 {{ font:700 clamp(1.8rem,7vw,2.4rem)/1.05 var(--f-display); letter-spacing:.01em; margin:0; text-wrap:balance }}
h2 {{ font:700 1.35rem/1.2 var(--f-display); letter-spacing:.04em; text-transform:uppercase; margin:0 0 10px }}
.lede {{ color:var(--muted); max-width:68ch; margin:6px 0 0 }}
.strip {{ display:flex; flex-wrap:wrap; gap:10px }}
.stat {{ background:var(--paper); border:1px solid var(--line); border-radius:6px; padding:10px 14px; min-width:0 }}
.stat b {{ display:block; font:600 1.4rem var(--f-mono); font-variant-numeric:tabular-nums }}
.stat span {{ font-size:.8rem; color:var(--muted); letter-spacing:.04em; text-transform:uppercase }}
.legend {{ display:flex; flex-wrap:wrap; gap:16px; font-size:.85rem; color:var(--muted) }}
.legend i {{ display:inline-block; width:22px; height:10px; vertical-align:middle; margin-right:6px; border-radius:2px }}
.l-new {{ background:var(--newfill); border:2px solid var(--new) }} .l-old {{ border:2px dashed var(--old) }} .l-pin {{ width:10px!important; height:10px!important; border-radius:50%!important; background:var(--pin) }}
.ledger {{ overflow-x:auto; background:var(--paper); border:1px solid var(--line); border-radius:6px }}
table {{ border-collapse:collapse; width:100%; font:13px var(--f-mono); font-variant-numeric:tabular-nums }}
th,td {{ padding:6px 10px; text-align:right; border-bottom:1px solid var(--line); white-space:nowrap }}
th:first-child,td:first-child {{ text-align:left }} th {{ font:600 .72rem var(--f-body); letter-spacing:.05em; text-transform:uppercase; color:var(--muted) }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:14px }}
.park {{ background:var(--paper); border:1px solid var(--line); border-radius:6px; padding:12px; display:grid; gap:8px; min-width:0 }}
.park header {{ display:grid; grid-template-columns:auto 1fr; gap:2px 8px; align-items:baseline }}
.park h3 {{ font:700 1.15rem/1.15 var(--f-display); margin:0; min-width:0; overflow-wrap:anywhere }}
.st {{ font:500 .75rem var(--f-mono); color:var(--muted); grid-row:span 2 }} .ref {{ font:.75rem var(--f-mono); color:var(--muted) }}
.change {{ font-weight:600; font-size:.9rem }} .grade {{ font:400 .75rem var(--f-mono); color:var(--muted); margin-left:6px }}
.map {{ background:var(--bg); border-radius:4px; aspect-ratio:4/3; max-width:100%; display:grid; place-items:center; position:relative; overflow:hidden }}
.map svg {{ width:100%; height:100% }}
.o-new {{ fill:var(--newfill); stroke:var(--new); stroke-linejoin:round }} .o-old {{ fill:none; stroke:var(--old); stroke-dasharray:4 3; vector-effect:non-scaling-stroke }}
.o-new {{ vector-effect:non-scaling-stroke }} .pin {{ fill:var(--pin) }}
.scale {{ position:absolute; right:6px; bottom:4px; font:.7rem var(--f-mono); color:var(--muted) }}
.noshape {{ color:var(--muted); font-size:.85rem }}
dl {{ margin:0; display:grid; grid-template-columns:auto 1fr; gap:3px 10px; font-size:.82rem }} dt {{ color:var(--muted) }} dd {{ margin:0; min-width:0; overflow-wrap:anywhere }}
.note {{ font-size:.85rem; color:var(--muted); max-width:72ch }}
</style>
<main>
<section><h1>New park key: what changes</h1>
<p class="lede">The key the website uses today, compared with the new Rule G key. Nothing below is live: the site keeps the old key until you say release.</p></section>
<section class="strip">
<div class="stat"><b>{prev['changed_count']:,}</b><span>parks changed</span></div>
<div class="stat"><b>{T['new outline']}</b><span>get an outline</span></div>
<div class="stat"><b>{T['outline lost']}</b><span>lose their outline</span></div>
<div class="stat"><b>{T['pieces added']:,}</b><span>pieces added</span></div>
<div class="stat"><b>{T['pieces removed']:,}</b><span>pieces removed</span></div>
<div class="stat"><b>{T['same']:,}</b><span>unchanged of {T['parks']:,}</span></div>
</section>
<section><h2>Sample parks, old and new</h2>
<div class="legend"><span><i class="l-new"></i>New key</span><span><i class="l-old"></i>On the site now</span><span><i class="l-pin"></i>POTA pin</span></div>
<p class="note">Each drawing uses the official records at 3 m detail. Big parks show at most 40 of their pieces. No background map: the page cannot load map tiles.</p>
<div class="grid">{''.join(cards)}</div></section>
<section><h2>Parks that lose their outline ({len(prev.get('lost') or [])})</h2><p class="note">These go back to a pin until the waiting room says yes to a piece. The pieces they had are listed with why the new rules hold them.</p><div class="ledger"><table><thead><tr><th>Park</th><th>State</th><th>Had on the site</th><th>Held now</th></tr></thead><tbody>{''.join(f"<tr><td>{E(c['ref'])} {E((c['n'] or '')[:38])}</td><td>{E(c['st'])}</td><td>{E(', '.join(sorted({x[1] for x in c['old']}))[:70])}</td><td>{E(', '.join(x[3].split(':')[0] for x in c.get('check') or [])[:60]) or 'kind / name rule'}</td></tr>" for c in prev.get('lost') or [])}</tbody></table></div></section>
<section><h2>By state</h2><div class="ledger"><table><thead><tr><th>State</th><th>Parks</th><th>New outline</th><th>Lost outline</th><th>Pieces added</th><th>Pieces removed</th><th>Grade changed</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<p class="note">ℹ️ Maps and park info are a planning aid, not a guarantee. Always check the official agency map and rules before you go.</p>
</main>"""
open(sys.argv[4], 'w').write(page)
print('written', len(page))
