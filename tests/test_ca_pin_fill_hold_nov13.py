#!/usr/bin/env python3
"""Nov 13 2026 (Quality, delegated by Brandon 4:43 AM CT): hold CA-2241, CA-1974 and CA-1997 like PF-0033/34.
Their Ville de Montréal city-polygon pin fills are not applied, and CA-1974\'s \'Site patrimonial de Montréal\' site note
(which rested on that fill) is not applied either. The other 19 ready Canada fills still apply, CA-2274 keeps its note,
and the change is scoped to CA-QC only (no full CA rebuild)."""
import io, json, copy, contextlib, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_pinfill_fixture as H   # noqa: E402  (refuses every socket on import)
import kpc_pin_fill as PINF   # noqa: E402
import kpc_key_freeze as KF, kpc_preflight as PF   # noqa: E402

ok = True
def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)

HOLD = ('CA-2241', 'CA-1974', 'CA-1997')
CA22 = 'CA-1974 CA-1997 CA-2056 CA-2058 CA-2064 CA-2080 CA-2082 CA-2089 CA-2092 CA-2093 CA-2097 CA-2099 CA-2103 CA-2198 CA-2223 CA-2227 CA-2228 CA-2238 CA-2241 CA-2246 CA-2261 CA-2274'.split()
CA19 = [r for r in CA22 if r not in HOLD]
FILE = str(H.PINS_FILE)

check(set(PINF.held_of('CA')) == set(HOLD) and set(PINF.held_of('PF')) == {'PF-0033', 'PF-0034'}
      and set(PINF.HELD) == set(HOLD) | {'PF-0033', 'PF-0034'},
      'HELD is PF-0033/34 plus CA-2241, CA-1974 and CA-1997 (and no other ref)')
check(all('Nov 13' in PINF.HELD[r] and 'Quality' in PINF.HELD[r] and 'Brandon' in PINF.HELD[r] for r in HOLD),
      'each of the three CA holds names the Nov 13 Quality decision delegated by Brandon')
check('Site patrimonial de Montréal' in PINF.HELD['CA-1974'],
      "CA-1974\'s hold names the Site patrimonial de Montréal site note")
check('CA-2274' not in PINF.HELD, 'CA-2274 is not held (its fill and Tyre-Macfarlane note still apply)')

def row(n, la=0.0, lo=0.0): return [n, '', 'Nature Reserve', '', '', la, lo, 0, 0, 0, 'QC']
names = {
    'CA-2241': "Saint Helen's Island Nature Reserve",
    'CA-1974': 'Champ de Mars (Regional) Nature Reserve',
    'CA-1997': 'Dorchester Square Nature Reserve',
    'CA-2274': 'Tyre Macfa Natrue Reserve Nature Reserve',
    'CA-2056': 'Ile Marianne (282) Nature Reserve',
}
P0 = {r: row(names.get(r, r), 0.0, 0.0) for r in HOLD + ('CA-2274', 'CA-2056')}
keep = copy.deepcopy(P0)
buf = io.StringIO()
with contextlib.redirect_stdout(buf): out = PINF.fill(P0, 'CA', path=FILE)
log = buf.getvalue()
check(P0 == keep, "POTA\'s list is never changed")
check(all(out[r][5:7] == [0.0, 0.0] for r in HOLD) and not (getattr(out, 'fills', None) and any(r in out.fills for r in HOLD)),
      'the three held parks are not filled: POTA\'s 0,0 pin stays, no pf row')
check(all(f'{r}' in log for r in HOLD) and 'HELD' in log and '3 fill(s) HELD' in log,
      'the run lists CA-2241, CA-1974 and CA-1997 as held')
check(isinstance(out, PINF.Filled) and set(out.fills) == {'CA-2274', 'CA-2056'}
      and out['CA-2274'][5:7] != [0.0, 0.0] and out['CA-2056'][5:7] != [0.0, 0.0],
      'the other ready Quebec fills still apply (CA-2274 and CA-2056 here)')

# all 19 non-held Canada fills apply when every ready CA park is a 0,0 pin
P19 = {r: row(r, 0.0, 0.0) for r in CA22}
buf = io.StringIO()
with contextlib.redirect_stdout(buf): out19 = PINF.fill(P19, 'CA', path=FILE)
log19 = buf.getvalue()
check(isinstance(out19, PINF.Filled) and set(out19.fills) == set(CA19) and all(out19[r][5:7] == [0.0, 0.0] for r in HOLD),
      'of the 22 ready Canada fills, the 19 that are not held are applied and the three holds are not')
check('CA-2274' in out19.fills and 'CA-1974' not in out19.fills, 'CA-2274 is among the 19; CA-1974 is not (so its site note is not produced)')

# mark: held parks get no pf
parks = {r: {'g': 'pin'} for r in CA22}
Pback = PINF.mark(parks, out19)
check(all('pf' not in parks[r] for r in HOLD) and all('pf' in parks[r] for r in CA19) and Pback is out19.pota,
      "mark writes 'pf' only on the 19 applied fills, not on the three holds")

# review list: the CA review writer lists the holds for QC; a standing review file names them
rev = (ROOT / 'data/ca-key/review/CA-QC.md').read_text(encoding='utf-8')
standing = (ROOT / 'data/ca-key/review/held-pin-fills.md').read_text(encoding='utf-8')
check(all(r in rev and r in standing for r in HOLD) and 'Owner hold (pin fills not applied)' in rev
      and 'Site patrimonial de Montréal' in rev and 'CA-2274' in standing and 'CA-QC' in standing,
      'the three parks are on the CA-QC review list and the standing held-pin-fills list, with the CA-1974 site note named')

# the review writer hook (same text the next CA-QC key will write)
writer = (ROOT / '.github/scripts/kpc_ca_key.py').read_text(encoding='utf-8')
check("_PFHOLD.HELD" in writer and 'Owner hold (pin fills not applied)' in writer,
      'the Canada key review page writer puts owner-held pin fills of that province on the review list')

# scope: CA-QC only; world none (hash moves, no country rebuild); US and fers unchanged
cur = {k: KF.rules_hash(k) for k in ('us-key', 'ca-key', 'world-key', 'fers')}
check(cur['us-key'] == 'd4ebfafce438' and cur['fers'] == 'cef323de4c9a',
      f"US and fers hashes are unchanged ({cur['us-key']}, {cur['fers']})")
check(cur['ca-key'] == 'ba480fa34fb6' and cur['world-key'] == '158325de87ce',
      f"CA and world hashes are the post-hold hashes ({cur['ca-key']}, {cur['world-key']})")
log = (ROOT / 'docs/key-rules-change.txt').read_text(encoding='utf-8')
o_ca, n_ca, ln_ca = PF.changelog_hashes(log, 'ca-key')
o_w, n_w, ln_w = PF.changelog_hashes(log, 'world-key')
check(o_ca == '2a4d0154d95c' and n_ca == cur['ca-key'] and o_w == 'a47e0479ad41' and n_w == cur['world-key']
      and 'APPROVED, decided_by KPC owner, 2026-11-13' in ln_ca and 'CA-QC' in ln_ca,
      'the newest changelog line is this hold: CA 2a4d0154d95c -> ba480fa34fb6, world a47e0479ad41 -> 158325de87ce, decided_by KPC owner, 2026-11-13')
sc_ca = json.loads((ROOT / '.github/ca-key-rule-scope.json').read_text(encoding='utf-8'))
sc_w = json.loads((ROOT / '.github/world-key-rule-scope.json').read_text(encoding='utf-8'))
e_ca = next((c for c in sc_ca['changes'] if c.get('id') == '2026-11-13-hold-ca-2241-1974-1997'), {})
e_w = next((c for c in sc_w['changes'] if c.get('id') == '2026-11-13-hold-ca-2241-1974-1997'), {})
check(e_ca.get('from') == '2a4d0154d95c' and e_ca.get('scope') == {'states': ['CA-QC']}
      and e_w.get('from') == 'a47e0479ad41' and e_w.get('scope') == 'none',
      'scope: Canada from 2a4d0154d95c touches CA-QC only (no full CA rebuild); world from a47e0479ad41 is none')
# pending_scope from the previous hash is QC only
states, saved, parks = KF.pending_scope('ca-key', '2a4d0154d95c', ROOT)
check(states == {'CA-QC'} and saved is False and not parks,
      f'pending CA scope from 2a4d0154d95c is CA-QC only (got {states!r})')
wstates, _, _ = KF.pending_scope('world-key', 'a47e0479ad41', ROOT)
check(wstates == set() or wstates == 'none' or wstates is not None and len(wstates) == 0,
      f'pending world scope from a47e0479ad41 rebuilds no country (got {wstates!r})')

print('ALL PASS' if ok else 'FAILED')
sys.exit(0 if ok else 1)
