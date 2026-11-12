#!/usr/bin/env python3
"""Visitor counter (Nov 11 2026, owner): GoatCounter pinned to count.v4.js with an integrity check, and never on a page where a
member types a password. Offline: node runs kpc-count.js in a stand-in page (no network, nothing is fetched).
 - a public page on github.io: one script, src count.v4.js, crossOrigin anonymous, the sha384 integrity, data-goatcounter
 - members-only page (the members door), a VIP / beta / room lock page, the map-rep door, the old members door, #members: no script
 - every page that loads kpc-count.js loads kpc-gate.js before it (the guard reads window.KPCGate)
 - static: for every real page, which of them would load the counter; none of them carries a lock script or is members-only"""
import json, os, pathlib, re, subprocess, sys
HERE = pathlib.Path(os.environ.get('LINKS') or pathlib.Path(__file__).resolve().parent.parent)
fails = 0
def ok(c, m):
    global fails
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails += 1
SRI = 'sha384-nRw6qfbWyJha9LhsOtSb2YJDyZdKvvCFh0fJYlkquSFjUxp9FVNugbfy8q1jdxI+'
gate = (HERE / 'kpc-gate.js').read_text(encoding='utf-8')
PUBLIC = re.findall(r"'([^']+\.html)'", re.search(r'var PUBLIC = \[(.*?)\];', gate, re.S).group(1))
NODE = r"""
const fs = require('fs'), vm = require('vm'); const [src, cases] = [fs.readFileSync(process.argv[1], 'utf8'), JSON.parse(process.argv[2])]; const out = [];
for (const c of cases) {
  const added = [];
  const doc = { head: { appendChild: s => added.push(s) }, documentElement: { hasAttribute: a => a === 'data-kpc-public' && !!c.attrPublic, classList: { contains: k => k === 'kpc-door' && !!c.boxOpen } },
    getElementById: id => id === 'kpcDoor' && c.boxOpen ? {} : null,
    createElement: () => { const s = { attrs: {}, setAttribute(k, v) { this.attrs[k] = v; } }; return s; },
    querySelector: sel => (c.scripts || []).some(n => sel.includes(n)) ? {} : null };
  const pub = c.public;
  const ctx = { document: doc, location: { hostname: 'kentuckyportableclub.github.io', pathname: '/KPC-Links/' + c.page, search: '', hash: c.hash || '' },
    localStorage: { getItem: () => null, setItem() {}, removeItem() {} }, URLSearchParams,
    window: c.noGate ? {} : { KPCGate: { isPublic: f => pub.includes(f) } } };
  ctx.window.window = ctx.window; vm.runInNewContext('var window = this.window;' + src, Object.assign(ctx, { window: ctx.window }));
  out.push(added.map(s => ({ src: s.src, co: s.crossOrigin, integ: s.integrity, gc: s.attrs['data-goatcounter'] })));
}
console.log(JSON.stringify(out));
"""
cases = [dict(page='index.html', public=PUBLIC), dict(page='kpc-club.html', public=PUBLIC), dict(page='kpc-hunt.html', public=PUBLIC + ['kpc-hunt.html'], scripts=['kpc-vip.js']),
         dict(page='kpc-beta-room.html', public=PUBLIC, scripts=['kpc-vip.js']), dict(page='kpc-maprep-reps.html', public=PUBLIC, attrPublic=True, scripts=['kpc-maprep-gate.js']),
         dict(page='kpc-tracker.html', public=PUBLIC + ['kpc-tracker.html'], scripts=['kpc-members.js']), dict(page='about.html', public=PUBLIC, hash='#members'),
         dict(page='about.html', public=PUBLIC, noGate=True), dict(page='', public=PUBLIC), dict(page='about.html', public=PUBLIC, boxOpen=True)]
try:
    r = subprocess.run(['node', '-e', NODE, str(HERE / 'kpc-count.js'), json.dumps(cases)], capture_output=True, text=True, timeout=120)
    res = json.loads(r.stdout.strip().split('\n')[-1])
except FileNotFoundError:
    res = None; print('SKIP node is not installed here')
except Exception as e:  # noqa: BLE001
    res = None; ok(False, 'node run: ' + repr(e) + ' ' + r.stderr[-300:])
if res is not None:
    one = res[0]
    ok(len(one) == 1 and one[0]['src'] == 'https://gc.zgo.at/count.v4.js' and one[0]['co'] == 'anonymous' and one[0]['integ'] == SRI
       and one[0]['gc'] == 'https://kentuckyportableclub.goatcounter.com/count', 'public page: one pinned count.v4.js with integrity + crossorigin: %s' % one)
    for (c, got), why in zip(list(zip(cases, res))[1:8], ['members-only page (members door)', 'VIP lock page', 'beta room lock page', 'map-rep door page',
                                                         'old members door page', '#members opens the sign-in box', 'no kpc-gate.js on the page']):
        ok(got == [], 'no counter on %s (%s)' % (c['page'], why))
    ok(len(res[8]) == 1, 'the site root (/KPC-Links/) counts as index.html')
    ok(res[9] == [], 'no counter while the members sign-in box is open (Nov 11, third round)')
src = (HERE / 'kpc-count.js').read_text(encoding='utf-8')
ok("gc.zgo.at/count.js'" not in src and 'count.v4.js' in src and SRI in src, 'kpc-count.js: no unpinned count.js left')
loads, bad, order = [], [], []
for f in sorted(os.listdir(HERE)):
    if not f.endswith('.html'): continue
    t = (HERE / f).read_text(encoding='utf-8', errors='replace'); c = t.find('src="kpc-count.js')
    if c < 0: continue
    g = t.find('src="kpc-gate.js')
    if g < 0 or g > c: order.append(f)
    lock = re.search(r'src="(kpc-vip|kpc-maprep-gate|kpc-members)\.js', t)
    pub = f in PUBLIC or 'data-kpc-public' in t[:400]
    if pub and not lock: loads.append(f)
    if pub and lock: pass   # the guard in kpc-count.js skips it (node checked above)
ok(not order, 'kpc-gate.js loads before kpc-count.js on every page: ' + (', '.join(order) or 'yes'))
ok(all(not re.search(r'src="(kpc-vip|kpc-maprep-gate|kpc-members)\.js', (HERE / f).read_text(encoding='utf-8')) for f in loads),
   '%d pages may count; none of them has a password lock' % len(loads))
print('SOME FAILED' if fails else 'ALL PASSED')
sys.exit(1 if fails else 0)
