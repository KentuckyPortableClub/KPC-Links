#!/usr/bin/env python3
"""Nov 8 (Brandon 8:01 / 8:05 AM CST): the Mapping Rep Tool Box on its own password page for mapping reps, and a friendly note
when a state's own agency maps can't load live (driven by data/maprep/catalog.json, not a hard-coded list)."""
import json, pathlib, re, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)
rd = lambda f: (ROOT / f).read_text(encoding='utf-8')
main, reps, gate, club = rd('kpc-maprep.html'), rd('kpc-maprep-reps.html'), rd('kpc-maprep-gate.js'), rd('kpc-club.html')
# the reps page is the Tool Box byte for byte, apart from the two head changes
undo = reps.replace('<html lang="en" data-kpc-public data-kpc-rep>', '<html lang="en">').replace('<script src="kpc-maprep-gate.js?v=20261108a"></script>', '')
check(undo == main, 'kpc-maprep-reps.html is kpc-maprep.html plus the rep door only (every Tool Box feature kept)')
check('noindex' in reps and 'data-kpc-public' in reps, 'reps page: noindex, and the members door lets it through to the rep door')
check(reps.index('kpc-gate.js') < reps.index('kpc-maprep-gate.js'), 'rep door loads after the members gate (members go straight in)')
m = re.search(r"RH = '([0-9a-f]{64})'", gate)
check(bool(m), 'the rep door holds a SHA-256 hash')
check("localStorage.setItem(KEY, RH)" in gate and "'kpcMapRep'" in gate, 'a good password is remembered on the device')
# no plain password anywhere in the committed text files (the hash is checked against a value given to this test by env only)
import os
pw = os.environ.get('KPC_REP_PW')
if pw:
    import hashlib
    check(hashlib.sha256(('kpc-maprep:' + pw.strip().lower()).encode()).hexdigest() == m.group(1), 'KPC_REP_PW matches the stored hash')
    new = ['kpc-maprep-gate.js', 'kpc-maprep-reps.html', 'kpc-club.html', 'kpc-maprep-check.js', 'kpc-maprep-logic.js', 'tests/test_maprep_reps_page_nov8.py']
    hits = [f for f in new if pw.lower() in rd(f).lower()]
    check(not hits, 'the plain password is not written in the rep door, the page or this test: ' + ' '.join(hits))
# not linked from anywhere public; the Club Room card is unchanged but tappable
links = subprocess.run(['git', 'grep', '-l', 'kpc-maprep-reps.html', '--', '*.html', '*.js'], cwd=ROOT, capture_output=True, text=True).stdout.split()
check([x for x in links if x != 'kpc-maprep-gate.js'] == [], 'no page links to the reps page (share the link by hand): ' + ' '.join(links))
check('class="cr-app cr-tap"' in club and '<a class="cr-main" href="kpc-maprep.html">OPEN TOOL BOX ›</a>' in club and 'CANDIDATES PDF' in club, 'Club Room card: same links, whole card tappable')
check('.cr-tap a.cr-main::after{content:"";position:absolute;inset:0' in club, 'stretched link covers the card; the PDF link stays on top')
# limited live maps note
js = """
const G = require('./kpc-maprep-logic.js'), cat = require('./data/maprep/catalog.json');
const cp = JSON.parse(JSON.stringify(cat)); cp.blockedLiveStates = (cp.blockedLiveStates || []).concat(['WI']);
console.log(JSON.stringify({co: G.liveLimit(cat, 'CO'), tn: G.liveLimit(cat, 'TN'), ky: G.liveLimit(cat, 'KY'), wi: G.liveLimit(cat, 'WI'),
  wi2: G.liveLimit(cp, 'WI'), none: G.liveLimit(null, 'CO'), txt: G.liveNoteText('Colorado')}));"""
r = subprocess.run(['node', '-e', js], cwd=ROOT, capture_output=True, text=True, timeout=30)
o = json.loads(r.stdout or '{}')
check((o.get('co') or {}).get('reason') == 'blocked' and (o.get('tn') or {}).get('reason') == 'blocked', 'CO and TN (robots-blocked in the catalog) get the note')
check(o.get('ky') is None and o.get('wi') is None, 'KY (open folder) and WI (live layers) get no note')
check((o.get('wi2') or {}).get('reason') == 'blocked' and o.get('none') is None, 'driven by the catalog data, not a list in the code')
check(o.get('txt', '').startswith('Heads up: we can') and 'Colorado' in o.get('txt', '') and 'official links below' in o.get('txt', ''), 'friendly wording')
chk = rd('kpc-maprep-check.js')
check('updateLiveNote(code)' in chk and "G.liveLimit(cat, code)" in chk, 'the place menus show the note (both Check and Desk menus)')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
