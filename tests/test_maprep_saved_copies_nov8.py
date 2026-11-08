#!/usr/bin/env python3
"""Nov 8 (Brandon 8:23 AM CST): the limited-maps note counts our SAVED copies (the published answer key) as well as live layers.
full = no note, some = soft note naming the saved copy and its date, little = the heads-up."""
import json, pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)
js = r"""
const G = require('./kpc-maprep-logic.js'), cat = require('./data/maprep/catalog.json'), fs = require('fs');
const key = r => { try { return JSON.parse(fs.readFileSync(r.region === 'CA' ? 'data/ca-key/CA-' + r.code + '.json' : 'data/us-key/US-' + r.code + '.json')); } catch (e) { return null; } };
const t = {}; G.placeRows().filter(r => /^(US|CA)$/.test(r.region)).forEach(r => { const lim = G.liveLimit(cat, r.code); t[r.code] = G.liveTier(lim, lim ? G.savedShare(key(r)) : null); });
const fake = { parks: { a: { m: [[1]], g: 'official' }, b: { m: [], g: 'pin' }, c: { m: [[2]], g: 'pin' } } };
console.log(JSON.stringify({ t, s: G.savedShare(fake), lim0: G.liveTier(null, null), f: G.liveTier({}, { share: .95 }), so: G.liveTier({}, { share: .7 }), li: G.liveTier({}, { share: .2 }), nk: G.liveTier({}, null),
  txs: G.savedNoteText('Alabama', 'some', { parks: 155, outlines: 133 }, '2026-11-08 04:57 UTC'), txl: G.savedNoteText('Utah', 'little', { parks: 692, outlines: 405 }, ''), txf: G.savedNoteText('Ohio', 'full', {}, '') }));
"""
r = subprocess.run(['node', '-e', js], cwd=ROOT, capture_output=True, text=True, timeout=60)
check(r.returncode == 0, 'node ran ' + r.stderr[:200])
o = json.loads(r.stdout or '{}'); t = o.get('t', {})
check(o['s'] == {'parks': 3, 'outlines': 1, 'share': 1 / 3}, 'savedShare counts outlines (m and not a pin)')
check(o['lim0'] == 'live' and o['f'] == 'full' and o['so'] == 'some' and o['li'] == 'little' and o['nk'] == 'little', 'tiers: live / full >= 90% / some >= 60% / little')
check(t.get('KY') == 'live' and t.get('WI') == 'live', 'live states need no note')
check(t.get('CO') == 'full' and t.get('TN') == 'full', 'CO and TN are robots-blocked live but fully covered by saved outlines: no note')
little = sorted(k for k, v in t.items() if v == 'little')
check(0 < len(little) < 15, f'only places with little saved data get the heads-up ({len(little)}: {" ".join(little)})')
check(o['txs'].startswith('Live agency maps for Alabama') and 'saved copies from 2026-11-08' in o['txs'] and '133 of 155' in o['txs'], 'soft note names the saved copy, its date and the count')
check(o['txl'].startswith('Heads up:') and '405 of 692' in o['txl'] and o['txf'] == '', 'heads-up for little; nothing for full')
chk = (ROOT / 'kpc-maprep-check.js').read_text(encoding='utf-8')
check('G.savedShare(await stateKey(code))' in chk and 'G.liveTier(lim, saved)' in chk, 'the Tool Box note uses the saved key and its build date')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
