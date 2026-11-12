#!/usr/bin/env python3
"""Official pin fills in the Canada and world keys (KPC owner, 2026-11-12; brief item 6, handoff item 5): an official pin is better
than no pin, and an existing pin is never moved. Offline: every socket is refused (here and in the builders this test starts); the real kpc_ca_key.py and
kpc_world_key.py run on SYNTHETIC saved copies (GEO_CACHE_MODE=only) in temp folders.
  1. the file: 74 rows, 25 ready pin-fill rows = CA 22 + PF 2 + AU 1 (the refs listed), 40 point-circle-candidate, 9 held;
  2. kpc_pin_fill.fill: a ready fill applies when POTA's pin is absent / 0,0 (-0.0 too); it is IGNORED when POTA has a usable pin and
     when the POTA pin is impossible (never moved); candidate / held rows do nothing; two ready rows for one park do nothing; a missing,
     unreadable or malformed file, or no file given, applies nothing (warning) and returns the same list; POTA's list is never changed;
  3. mark: 'pf' on the filled parks only, the Canada BKPIN gets POTA's own pin back, POTA's own list is handed back;
  4. the Canada key: only CA-QC changes (CA-BC byte-identical), the filled parks are marked pf and joined by the official pin, bk still
     says pin00, a park with a usable POTA pin keeps it (its fill ignored), the POTA list file is unchanged, and with no file (or a
     malformed one) every output is byte-identical to the builder without this commit;
  5. the world key: PF-0033 / PF-0034 are HELD by the owner (Nov 12; PF byte-identical), only AU changes (NZ byte-identical), same
     no-file / malformed checks;
  6. hashes: CA and world moved (declared in docs/key-rules-change.txt with scope entries CA-QC / AU PF), US and fers did not, and
     kpc_key_facts.py / kpc_match.py are unchanged; kpc_pin_fill.py is in the Canada and world RULE_FILES (Quality must-fix M2);
  7. the workflows: both key workflows read the file from KPC-Data read only (a recorded warning when not read), parse, no cron change."""
import copy, hashlib, io, json, os, pathlib, re, subprocess, sys, tempfile, contextlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import kpc_pinfill_fixture as H   # noqa: E402  (refuses every socket on import)
import kpc_pin_fill as PINF   # noqa: E402
import kpc_key_freeze as KF, kpc_preflight as PF   # noqa: E402

ok = True
def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)

CA22 = 'CA-1974 CA-1997 CA-2056 CA-2058 CA-2064 CA-2080 CA-2082 CA-2089 CA-2092 CA-2093 CA-2097 CA-2099 CA-2103 CA-2198 CA-2223 CA-2227 CA-2228 CA-2238 CA-2241 CA-2246 CA-2261 CA-2274'.split()
FILE = str(H.PINS_FILE)

# ---------------------------------------------------------------- 1. the file
doc = json.load(open(FILE, encoding='utf-8')); rows = doc['rows']
from collections import Counter
check(len(rows) == 74 and Counter(r['action'] for r in rows) == {'pin-fill': 25, 'point-circle-candidate': 40, 'held': 9},
      f"74 rows: 25 pin-fill, 40 point-circle-candidate, 9 held ({dict(Counter(r['action'] for r in rows))})")
ready, prob = PINF.load(FILE)
by = {}
for ref in ready: by.setdefault(ref.split('-')[0], []).append(ref)
check(not prob and {k: len(v) for k, v in by.items()} == {'CA': 22, 'PF': 2, 'AU': 1} and sorted(by['CA']) == CA22 and sorted(by['PF']) == ['PF-0033', 'PF-0034'] and by['AU'] == ['AU-10111'],
      'the ready pin fills are CA 22 (the 22 Quebec refs), PF 2 (PF-0033, PF-0034), AU 1 (AU-10111)')
check(all(r.get('ready_to_apply') is True for r in rows if r['action'] == 'pin-fill') and not any(r.get('ready_to_apply') for r in rows if r['action'] != 'pin-fill'),
      'only pin-fill rows are marked ready')
if H.DATA and (H.DATA / 'data/intake/official-pins-nov12.json').is_file():
    check((H.DATA / 'data/intake/official-pins-nov12.json').read_bytes() == H.PINS_FILE.read_bytes(), f'the fixture is still the KPC-Data file ({H.DATA})')
    ca = json.load(open(H.DATA / 'data/parkinfo/CA.json', encoding='utf-8'))['parks']
    check(all(ca[r][10] == 'QC' for r in CA22), 'KPC-Data park list: all 22 Canada fills are Quebec parks (only CA-QC can change)')
    check(all(PINF.KF.pin_why((ca[r][5], ca[r][6])) == 'pin00' for r in CA22), 'KPC-Data park list: POTA has a 0,0 pin for all 22 today')
else:
    print('     (no KPC-Data checkout next to this repo: the park-list checks are skipped)')

# ---------------------------------------------------------------- 2. fill
def row(n, la, lo, pv='QC'): return [n, '', 'Nature Reserve', '', '', la, lo, 0, 0, 0, pv]
P0 = {'CA-2056': row('Ile Marianne (282) Nature Reserve', 0.0, -0.0), 'CA-2058': row('Ile Poirier Old-Growth Forest Nature Reserve', None, None),
      'CA-2080': row('Lac a Jos Old Growth Forest Nature Reserve', 49.4, -68.7), 'CA-2082': row('Lac Ancelin Old Growth Forest Nature Reserve', 95.0, -71.8),
      'CA-2089': ['Lac-Brule Natrue Reserve Nature Reserve', '', 'Nature Reserve'], 'CA-0001': row('Alaksen National Wildlife Area', 49.1013, -123.173, 'BC')}
keep = copy.deepcopy(P0)
def run(P, area, path):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): out = PINF.fill(P, area, path=path)
    return out, buf.getvalue()
out, log = run(P0, 'CA', FILE)
check(P0 == keep, "POTA's list (and every row in it) is never changed by fill")
check(out['CA-2056'][5:7] == [50.25, -59.845833] and out['CA-2058'][5:7] == [49.552639, -70.795083] and out['CA-2089'][5:7] == [46.082167, -74.302444],
      'a ready fill applies when POTA has a 0,0 pin (-0.0 too), no pin, or a row too short to hold one')
check(out['CA-2080'] is P0['CA-2080'] and out['CA-2080'][5:7] == [49.4, -68.7] and 'IGNORED' in log and 'CA-2080' in log,
      'a ready fill is IGNORED when POTA now has a usable pin (the pin is not moved, the run says so)')
check(out['CA-2082'] is P0['CA-2082'] and out['CA-2082'][5] == 95.0 and 'pinbad' in log, 'an impossible POTA pin is never moved (said, a person checks)')
check(out['CA-0001'] is P0['CA-0001'] and set(out) == set(P0), 'every other park row is the same object; no park added or dropped')
check(isinstance(out, PINF.Filled) and set(out.fills) == {'CA-2056', 'CA-2058', 'CA-2089'} and out.pota is P0, 'the filled list remembers POTA\'s own list and what it filled')
w, wl = run({'PF-0033': ['Est du lagon', '', 'Biological Reserve', '', '', 0.0, 0.0], 'PF-0008': ['AMP de Moorea', '', 'x', '', '', -17.5, -149.8]}, 'PF', FILE)
check(not isinstance(w, PINF.Filled) and w['PF-0033'][5:7] == [0.0, 0.0] and w['PF-0008'][5:7] == [-17.5, -149.8] and 'HELD' in wl and 'PF-0033' in wl,
      'world: PF-0033 is HELD by the owner (Nov 12): its ready fill is not applied, POTA\'s 0,0 pin stays, the run lists it held')
check(PINF.HELD.keys() == {'PF-0033', 'PF-0034'}, 'the owner hold list is exactly PF-0033 and PF-0034 (one shared low-confidence official point)')
au, al = run({'AU-10111': ['Cobourg', '', 'Conservation Area', '', '', 0.0, 0.0]}, 'AU', FILE)
check(isinstance(au, PINF.Filled) and au['AU-10111'][5:7] != [0.0, 0.0] and 'HELD' not in al, 'world: the AU fill still applies (refs of other countries are never read for AU)')
nz, _ = run({'NZ-0001': ['x', '', 'y', '', '', 0.0, 0.0]}, 'NZ', FILE)
check(not isinstance(nz, PINF.Filled), 'a country with no ready fill gets its own list back (same object)')
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    only_other = t / 'other.json'; only_other.write_text(json.dumps({'rows': [r for r in rows if r['action'] != 'pin-fill'] + [dict(rows[1], ready_to_apply=False), dict(rows[2], ready_to_apply='yes')]}), encoding='utf-8')
    for name, p in (('candidate / held rows and not-ready pin-fill rows', only_other),):
        o, l = run(P0, 'CA', str(p))
        check(o is P0 and P0 == keep, f'{name} do nothing (the same list back)')
    twice = t / 'twice.json'; r1 = next(r for r in rows if r['ref'] == 'CA-2056'); twice.write_text(json.dumps({'rows': [r1, dict(r1, lat=50.3)]}), encoding='utf-8')
    o, l = run(P0, 'CA', str(twice)); check(o is P0 and 'two ready rows' in l, 'two ready rows for one park: neither is used (never guess)')
    badc = t / 'badc.json'; badc.write_text(json.dumps({'rows': [dict(r1, lat='x')]}), encoding='utf-8')
    o, l = run(P0, 'CA', str(badc)); check(o is P0 and 'not usable' in l, 'a fill whose own coordinate is not usable is not applied')
    for name, content in (('a missing file', None), ('a file that is not JSON', '{"rows": [ oops'), ('rows that are not a list', '{"rows": {"CA-2056": 1}}'),
                          ('a list instead of the object', '[1, 2]'), ('rows that are not objects', '{"rows": [1, 2]}')):
        p = t / 'f.json'
        if content is None: p.unlink(missing_ok=True)
        else: p.write_text(content, encoding='utf-8')
        o, l = run(P0, 'CA', str(p))
        check(o is P0 and P0 == keep and '::warning title=Official pin fills (CA)::' in l and 'NO official pin fill' in l, f'{name}: nothing applied, a warning, the same list back')
    env0 = os.environ.pop(PINF.ENV, None)
    try:
        o, l = run(P0, 'CA', None); check(o is P0 and 'not given' in l, 'no file given (KPC_OFFICIAL_PINS unset): nothing applied, a warning')
        os.environ[PINF.ENV] = FILE; o, _ = run(P0, 'CA', None); check(isinstance(o, PINF.Filled), 'KPC_OFFICIAL_PINS names the file the builders read')
    finally:
        os.environ.pop(PINF.ENV, None)
        if env0 is not None: os.environ[PINF.ENV] = env0

# ---------------------------------------------------------------- 3. mark
parks = {r: {'n': x[0] if x else '', 'm': [], 'c': []} for r, x in P0.items()}
BK = {r: (x[5], x[6]) if len(x) > 6 else (None, None) for r, x in out.items()}
back = PINF.mark(parks, out, BK)
check(back is P0, "mark hands back POTA's own list")
check(set(r for r, p in parks.items() if 'pf' in p) == {'CA-2056', 'CA-2058', 'CA-2089'} and parks['CA-2056']['pf']['why'] == 'official pin (filled; POTA has none)'
      and parks['CA-2056']['pf']['la'] == 50.25 and parks['CA-2056']['pf']['pota'] == 'pin00' and parks['CA-2058']['pf']['pota'] == 'nopin' and parks['CA-2056']['pf']['url'].startswith('http'),
      "only the filled parks are marked 'pf' (official pin, filled; POTA has none; with POTA's own reason)")
check(BK['CA-2056'] == (0.0, -0.0) and BK['CA-2058'] == (None, None) and BK['CA-2080'] == (49.4, -68.7), "the Canada BKPIN gets POTA's own pin back (bk measures from POTA's pin)")
check(PINF.mark(parks, P0) is P0, 'mark on a list nothing was filled in changes nothing')

# ---------------------------------------------------------------- 4. the Canada key, end to end
def ca_parks():
    return {'CA-2056': row('Ile Marianne (282) Nature Reserve', 0.0, -0.0), 'CA-2058': row('Ile Poirier Old-Growth Forest Nature Reserve', 0.0, -0.0),
            'CA-2080': row('Lac a Jos Old Growth Forest Nature Reserve', 49.40, -68.70), 'CA-2111': row('Lac Pas Dans La Liste Nature Reserve', 47.0, -71.0),
            'CA-0001': row('Alaksen National Wildlife Area', 49.1013, -123.173, 'BC')}
def crec(oid, n, la, lo, d=.01, ty='Nature Reserve'): return {'oid': oid, 'n': n, 'nf': '', 'ty': ty, 'ow': '', 'mg': '', 'ha': 30, '_r': [H.ring(la, lo, d)], '_k': []}
CREC = [crec(1, 'Ile Marianne (282) Nature Reserve', 50.25, -59.845833), crec(2, 'Ile Marianne (282) Nature Reserve', 46.0, -78.0),   # same name: at the official pin, and far away
        crec(3, 'Reserve de biodiversite X', 49.552639, -70.795083, ty='Biodiversity Reserve'), crec(4, 'Lac a Jos Old Growth Forest Nature Reserve', 49.40, -68.70),
        crec(5, 'Lac Pas Dans La Liste Nature Reserve', 47.0, -71.0), crec(6, 'Alaksen National Wildlife Area', 49.1013, -123.173, ty='National Wildlife Area')]
CA_SRC = (H.SCRIPTS / 'kpc_ca_key.py').read_text(encoding='utf-8')
CA_OLD = H.strip_hook(H.strip_hook(CA_SRC, '# Nov 12 (KPC owner, 2026-11-12; kpc_pin_fill.py): an OFFICIAL pin', 'PINF.fill(P,'),
                      "# Nov 12 (KPC owner, 2026-11-12; kpc_pin_fill.py): a filled park is marked 'pf'", 'P = PINF.mark(')
check('kpc_pin_fill' not in CA_OLD and CA_SRC.count('kpc_pin_fill') == 3, 'the Canada builder without this commit = the builder minus its two pin-fill hooks')
def cmp(a, b, skip=('data/status/',)):
    ks = sorted(k for k in set(a) | set(b) if not k.startswith(skip) and not k.startswith('_'))
    return [k for k in ks if a.get(k) != b.get(k)]
rO, oO = H.ca_build(ca_parks(), CREC, {}, src=CA_OLD)
rN, oN = H.ca_build(ca_parks(), CREC, {PINF.ENV: FILE})
r0, o0 = H.ca_build(ca_parks(), CREC, {})
with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f: f.write('{"rows": [ broken'); bad = f.name
rB, oB = H.ca_build(ca_parks(), CREC, {PINF.ENV: bad}); os.unlink(bad)
check(all(r.returncode == 0 for r in (rO, rN, r0, rB)), f'the Canada builder runs offline in every case (exit {[r.returncode for r in (rO, rN, r0, rB)]})')
check(not cmp(oO, o0) and not cmp(oO, oB), f'no file given, or a malformed file: every Canada output is byte-identical to the builder without this commit ({cmp(oO, o0) + cmp(oO, oB)})')
check('::warning title=Official pin fills (CA)::' in rB.stdout and 'not given' in r0.stdout, 'a malformed / missing file is said loudly; the build went on')
ch = cmp(oO, oN)
check(set(ch) == {'data/ca-key/CA-QC.json', 'data/ca-key/index.json', 'data/ca-key/review/CA-QC.md'} and oO['data/ca-key/CA-BC.json'] == oN['data/ca-key/CA-BC.json'] and oO['data/ca-key/refs.json'] == oN['data/ca-key/refs.json'],
      f'with the fills only Quebec changes (CA-BC.json, refs.json byte-identical; index.json differs only in the QC row): {ch}')
iO, iN = json.loads(oO['data/ca-key/index.json']), json.loads(oN['data/ca-key/index.json'])
check({k: v for k, v in iO['provinces'].items() if k != 'QC'} == {k: v for k, v in iN['provinces'].items() if k != 'QC'}, 'index.json: every province row but QC is the same')
qO, qN = json.loads(oO['data/ca-key/CA-QC.json'])['parks'], json.loads(oN['data/ca-key/CA-QC.json'])['parks']
check(sorted(r for r in qN if qN[r] != qO[r]) == ['CA-2056', 'CA-2058'], f"only the two filled Quebec parks change ({sorted(r for r in qN if qN[r] != qO[r])})")
a, b = qN['CA-2056'], qO['CA-2056']
check(not b['m'] and b['g'] == 'pin' and [q[0] for q in a['m']] == [1] and a['g'] == 'official' and a['pf']['why'] == 'official pin (filled; POTA has none)' and a['pf']['la'] == 50.25,
      'CA-2056: with no pin it found nothing (as in the live key); with the official pin it joins the same-name record AT the pin, never the far one of the same name; marked pf; grade official (the existing rule)')
check(a['bk'][4:] == ['pin00'] or (len(a['bk']) > 4 and a['bk'][4] == 'pin00'), f"CA-2056: bk still measures from POTA's own pin and says pin00 ({a['bk']})")
c = qN['CA-2058']
check(c['pf']['pota'] == 'pin00' and not c['m'] and c['g'] == 'pin' and any(q[1] == 'Reserve de biodiversite X' for q in (c.get('a') or []) + (c.get('c') or [])) and not (qO['CA-2058'].get('a') or qO['CA-2058'].get('c')),
      'CA-2058: the official pin lets the key look by location like any park (the differently named land at the pin is listed, never joined); still grade pin, marked pf')
check(qN['CA-2080'] == qO['CA-2080'] and 'pf' not in qN['CA-2080'] and 'IGNORED' in rN.stdout and 'CA-2080' in rN.stdout,
      'CA-2080: POTA has a usable pin (fixture), so its ready fill is IGNORED and the park is byte-identical (the pin never moves)')
check(qN['CA-2111'] == qO['CA-2111'], 'a Quebec park with no fill row is unchanged')
check(all(o['_parkinfo_unchanged'] for o in (oO, oN, r0 and o0, oB)), 'the POTA park list file is never changed by the build')
check(sum(1 for p in qN.values() if 'pf' in p) == 2, "only filled parks carry 'pf'")

# ---------------------------------------------------------------- 5. the world key, end to end
def wrow(n, t, la, lo): return [n, '', t, '', '', la, lo, 0, 0, 0, '']
def wrec(i, n, la, lo, src, d=.01, **k): return dict({'id': i, 'n': n, 'ty': '', 'src': src, '_bb': [lo - d, la - d, lo + d, la + d], '_r': [H.ring(la, lo, d)], 'code': '', 'dc': ''}, **k)
WP = {'PF': {'PF-0033': wrow('Est du lagon et Motu Manu Biological Reserve', 'Biological Reserve', 0.0, 0.0), 'PF-0034': wrow('Village de Pahua Biological Reserve', 'Biological Reserve', 0.0, 0.0),
             'PF-0008': wrow('AMP de Moorea', 'Marine Protected Area', -17.53, -149.83)},
      'NZ': {'NZ-0001': wrow('Abel Tasman National Park', 'National Park', -40.9, 173.0)},
      'AU': {'AU-10111': wrow('Cobourg Peninsula Conservation Area', 'Conservation Area', 0.0, 0.0), 'AU-0001': wrow('Kakadu National Park', 'National Park', -13.0, 132.5)}}
WR = {'PF': [wrec(1, 'Motu Manu', -17.5, -149.833333, 'French Polynesia: PGEM'), wrec(2, 'AMP de Moorea', -17.53, -149.83, 'French Polynesia: PGEM')],
      'NZ': [wrec(1, 'Abel Tasman National Park', -40.9, 173.0, 'DOC')],
      'AU': [wrec(1, 'Garig Gunak Barlu National Park', -11.346944, 132.229722, 'CAPAD (DCCEEW)', d=.3), wrec(2, 'Kakadu National Park', -13.0, 132.5, 'CAPAD (DCCEEW)', d=.5)]}
W_SRC = (H.SCRIPTS / 'kpc_world_key.py').read_text(encoding='utf-8')
W_OLD = H.strip_hook(H.strip_hook(W_SRC, '# Nov 12 (KPC owner, 2026-11-12; kpc_pin_fill.py): an OFFICIAL pin', 'PINF.fill(P,'),
                     "# Nov 12 (KPC owner, 2026-11-12; kpc_pin_fill.py): a filled park is marked 'pf'", 'P = PINF.mark(')
check('kpc_pin_fill' not in W_OLD and W_SRC.count('kpc_pin_fill') == 3, 'the world builder without this commit = the builder minus its two pin-fill hooks')
CC = ['PF', 'NZ', 'AU']
wO = H.world_build(CC, WP, WR, {}, src=W_OLD); wN = H.world_build(CC, WP, WR, {PINF.ENV: FILE}); w0 = H.world_build(CC, WP, WR, {})
with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f: f.write('[]'); bad = f.name
wB = H.world_build(CC, WP, WR, {PINF.ENV: bad}); os.unlink(bad)
check(all(r.returncode == 0 for r, _ in (wO, wN, w0, wB)), f'the world builder runs offline in every case (exit {[r.returncode for r, _ in (wO, wN, w0, wB)]})')
check(not cmp(wO[1], w0[1]) and not cmp(wO[1], wB[1]), f'no file given, or a malformed file: every world output is byte-identical to the builder without this commit ({cmp(wO[1], w0[1]) + cmp(wO[1], wB[1])})')
ch = cmp(wO[1], wN[1])
check(all(re.search(r'/AU(\.json|\.md|/)', k) or k == 'data/world-key/index.json' for k in ch) and not any('NZ' in k or '/PF' in k for k in ch),
      f'with the fills only AU outputs change (PF held and NZ byte-identical; index.json only in AU\'s row): {ch}')
ixO, ixN = json.loads(wO[1]['data/world-key/index.json'])['countries'], json.loads(wN[1]['data/world-key/index.json'])['countries']
check(ixO['NZ'] == ixN['NZ'], 'index.json: the NZ row is the same')
pO, pN = json.loads(wO[1]['data/world-key/PF.json'])['parks'], json.loads(wN[1]['data/world-key/PF.json'])['parks']
check(pN == pO and 'pf' not in pN['PF-0033'] and 'pf' not in pN['PF-0034'] and not pN['PF-0033']['m'] and not pN['PF-0034']['m'],
      'PF (owner hold, Nov 12): PF-0033 and PF-0034 are NOT filled, not marked pf, not joined; every PF park is byte-identical to the builder without this commit')
check('HELD by the owner' in wN[0].stdout and 'PF-0033' in wN[0].stdout and 'PF-0034' in wN[0].stdout, 'the world run lists PF-0033 and PF-0034 as held')
aO, aN = json.loads(wO[1]['data/world-key/AU.json'])['parks'], json.loads(wN[1]['data/world-key/AU.json'])['parks']
check('pf' in aN['AU-10111'] and aN['AU-0001'] == aO['AU-0001'], 'AU-10111: its fill applies when AU is built (on main AU is a signed expected hold: kept from main until it is built again)')
check(all(o['_parkinfo_unchanged'] for _, o in (wO, wN, w0, wB)), 'the POTA park list files are never changed by the build')

# ---------------------------------------------------------------- 6. hashes
cur = {k: KF.rules_hash(k) for k in ('us-key', 'ca-key', 'world-key', 'fers')}
check(cur['us-key'] == PF.newest_hash('us-key') and cur['fers'] == PF.newest_hash('fers'), f"US stays its newest declared hash ({cur['us-key']}; this change does not move it), fers stays the newest declared ({cur['fers']})")   # Nov 12 CHANGED (stacked after D6 and the overrides split, which move US)
log = (H.ROOT / 'docs/key-rules-change.txt').read_text(encoding='utf-8')
o_ca, n_ca, ln_ca = PF.changelog_hashes(log, 'ca-key'); o_w, n_w, ln_w = PF.changelog_hashes(log, 'world-key')
check(n_ca == cur['ca-key'] or 'official pin fills' not in ln_ca.lower(), f"CA: the pin-fill ledger line ends at the current CA hash or a later line moved it ({o_ca} -> {n_ca}, now {cur['ca-key']})")
pin_line = next((l for l in log.splitlines() if l.startswith('Official pin fills in the Canada and world keys')), '')
check('CA rules 4b4176190334 -> ' in pin_line and 'world rules 889d37136cf8 -> ' in pin_line and 'APPROVED, decided_by KPC owner, 2026-11-12' in pin_line and 'FINAL' not in pin_line,
      'the ledger line: CA 4b4176190334 -> new, world 889d37136cf8 -> new, decided_by KPC owner, 2026-11-12, not claimed FINAL')
sc = {k: json.load(open(H.ROOT / KF.SCOPE_FILES[k], encoding='utf-8')) for k in ('ca-key', 'world-key')}
e_ca = next((c for c in sc['ca-key']['changes'] if c.get('id') == '2026-11-12-official-pin-fills'), {})
e_w = next((c for c in sc['world-key']['changes'] if c.get('id') == '2026-11-12-official-pin-fills'), {})
check(e_ca.get('from') == '4b4176190334' and e_ca.get('scope') == {'states': ['CA-QC']} and re.fullmatch(r'[0-9a-f]{12}', e_w.get('from') or '') and e_w.get('scope') == {'states': ['AU', 'PF']},
      'scope entries: Canada from 4b4176190334 touches CA-QC only; world (from the hash just before this change: D6 moved it first) touches AU and PF only')   # Nov 12 CHANGED (stacked after D6)
check('kpc_pin_fill.py' not in KF.NOT_RULES
      and '.github/scripts/kpc_pin_fill.py' in KF.RULE_FILES['ca-key']
      and '.github/scripts/kpc_pin_fill.py' in KF.RULE_FILES['world-key']
      and '.github/scripts/kpc_pin_fill.py' not in KF.RULE_FILES['us-key']
      and '.github/scripts/kpc_pin_fill.py' not in KF.RULE_FILES['fers'],
      'kpc_pin_fill.py is in the Canada and world RULE_FILES, not in NOT_RULES (Quality must-fix M2)')
with tempfile.TemporaryDirectory() as t:
    import shutil
    for k in ('us-key', 'ca-key', 'world-key', 'fers'):
        for rel in list(KF.RULE_FILES[k]) + [KF.VERSION_FILE]:
            if (H.ROOT / rel).is_file(): (pathlib.Path(t) / rel).parent.mkdir(parents=True, exist_ok=True); shutil.copy(H.ROOT / rel, pathlib.Path(t) / rel)
    check(all(KF.rules_hash(k, t) == cur[k] for k in cur) and '.github/scripts/kpc_key_freeze.py' not in sum(KF.RULE_FILES.values(), []),
          'kpc_key_freeze.py is in no rules hash')
    # an edit to the pin-fill helper moves the Canada and world hashes, not US or fers
    (pathlib.Path(t) / '.github/scripts/kpc_pin_fill.py').write_bytes((H.ROOT / '.github/scripts/kpc_pin_fill.py').read_bytes() + b'\n')
    check(KF.rules_hash('ca-key', t) != cur['ca-key'] and KF.rules_hash('world-key', t) != cur['world-key']
          and KF.rules_hash('us-key', t) == cur['us-key'] and KF.rules_hash('fers', t) == cur['fers'],
          'an edit to kpc_pin_fill.py moves the Canada and world hashes only')
base = next((r for r in ('origin/main',) if subprocess.run(['git', 'rev-parse', '-q', '--verify', r], cwd=H.ROOT, capture_output=True).returncode == 0), None)
if base:
    same = subprocess.run(['git', 'diff', '--quiet', base, '--', '.github/scripts/kpc_key_facts.py', '.github/scripts/kpc_match.py', '.github/scripts/kpc_key_rules.py'], cwd=H.ROOT).returncode == 0
    check(same, f'kpc_key_facts.py, kpc_match.py, kpc_key_rules.py are as on {base} (shared rule files untouched; kpc_us_key.py is moved by D6 and the overrides split earlier in this set, not by this change)')   # Nov 12 CHANGED (stacked)
else:
    print('SKIP shared-rule-file diff: no origin/main in this clone')

# ---------------------------------------------------------------- 7. workflows
import yaml   # noqa: E402
for wf, title in (('kpc-ca-key.yml', 'the Canada build goes on'), ('kpc-world-key.yml', 'every country is still built')):
    txt = (H.ROOT / '.github/workflows' / wf).read_text(encoding='utf-8'); d = yaml.safe_load(txt)
    check(isinstance(d, dict) and 'jobs' in d, f'{wf}: parses')
    check('KPC_OFFICIAL_PINS: .op/data/intake/official-pins-nov12.json' in txt and 'sparse-checkout set --no-cone data/intake/official-pins-nov12.json' in txt
          and f'no official pin fill this run; {title}"; echo "official pin fills - KPC-Data could not be read (exit $kpc_rc); no fill applied" >> "$RUNNER_TEMP/kpc-hidden.txt"; }}' in txt
          and 'https://github.com/KentuckyPortableClub/KPC-Data .op' in txt,
          f'{wf}: reads the file from KPC-Data read only (github.com, as the other KPC-Data reads), a recorded warning when it cannot')
    if base:
        old = subprocess.run(['git', 'show', f'{base}:.github/workflows/{wf}'], cwd=H.ROOT, capture_output=True, text=True).stdout
        cr = lambda t: sorted(re.findall(r'^\s*-\s*cron:.*$', t, re.M))
        ev = lambda t: sorted(((yaml.safe_load(t) or {}).get(True) or {}).keys())
        check(cr(old) == cr(txt) and ev(old) == ev(txt), f'{wf}: no cron line and no trigger kind changed against {base}')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
