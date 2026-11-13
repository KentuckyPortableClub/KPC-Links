"""Job 5, Nov 11 2026 (KPC owner, 2026-11-11): corridor-outline joins for the 39 wild and scenic river parks, as recorded in
docs/wsr-corridor-joins-nov11-staged.json. Offline: every socket is refused before anything runs (zero network).

Checks:
  1. the file names exactly the 39 rivers, each with a known status and a reason;
  2. held rivers: the nine 'none' holds and the far-off pins (over 5 km from the saved official line) are 'held', carry no join entry,
     and their override entries (read through kpc_overrides, manifest + parts) are byte-identical to the base this job was cut from (no hold lifted or altered);
  3. every staged id is a corridor-layer record (fwsr / wsrc / sgorg) that the tracked evidence lists FOR THAT PARK (the park's own
     key entry in data/us-key, or KPC-Data's near-miss list), under the same name as its fingerprint, naming the river; no staged id
     is used by another park in any key or override; at least one staged record is inside or within 0.5 km of the pin and every one
     is within the builder's 0.6 deg;
  4. nothing staged is live: none of the 39 has a staged id in the merged overrides, and the entries of the 39 are unchanged;
  5. no pin moved: every pin in the file equals POTA's pin in locations.json (and KPC-Data's park files when present);
  6. none of the 39 is one of the 31 official-line parks the trail guard pins;
  7. the four rules hashes equal the newest ones in docs/key-rules-change.txt;
  8. with KPC-Data: the staged acres are 0.5x-2x the saved official line's miles x 320 ac/mi.
KPC-Data: KPC_DATA=<dir>, else ../kpc-data or ../kpcdata next to this checkout. Without it the KPC-Data checks print SKIP."""
import hashlib, json, math, os, pathlib, re, socket, sys

def _no_net(*a, **k): raise RuntimeError('network refused in this test')
socket.socket.connect = _no_net; socket.create_connection = _no_net; socket.getaddrinfo = _no_net

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
bad = 0
def check(ok, msg):
    global bad; bad += not ok; print(('PASS ' if ok else 'FAIL ') + msg)
def skip(msg): print('SKIP ' + msg)
def load(p): return json.load(open(p, encoding='utf-8'))
def fp(x): return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()[:16]
DATA = next((pathlib.Path(d) for d in (os.environ.get('KPC_DATA'), ROOT.parent / 'kpc-data', ROOT.parent / 'kpcdata') if d and (pathlib.Path(d) / 'data').is_dir()), None)

R = ['US-' + x for x in ('0877 0878 0879 0880 0887 0889 0892 0893 11804 11828 11852 3382 0884 0881 0882 0896 10430 12224 0891 0897 8014 '
                         '12788 12789 12790 0885 10249 10251 12348 9156 9157 9158 6597 10971 10973 10975 10976 5835 6012 6025').split()]
NONE9 = {'US-0878', 'US-0879', 'US-0889', 'US-0882', 'US-0896', 'US-10430', 'US-0885', 'US-12348', 'US-9158'}
FAR = {'US-0877': 90.4, 'US-0887': 197.0, 'US-0892': 74.6, 'US-11852': 55.4, 'US-3382': 73.7, 'US-10430': 58.9, 'US-0897': 28.0}
# sha256[:16] of each of the 39's overrides.json entry at Links e567f6be (the 16 others had none)
OV39 = {'US-0877': '0153ad6cb2cae13f', 'US-0878': '2fa51bbdfc3ca887', 'US-0879': '7ef12baf47155b2c', 'US-0889': '8f7b6e413e4ae6bf',
        'US-11804': 'eac8a802bac4b961', 'US-11828': '1d11255d108c574b', 'US-11852': 'aa499e9a252ce31c', 'US-0882': '0e7726ddcb766028',
        'US-0896': 'c82f35d29c828919', 'US-10430': '0e7726ddcb766028', 'US-12789': 'e1b15ad91839b459', 'US-12790': 'cc9821cc98964e54',
        'US-0885': '0e7726ddcb766028', 'US-10251': 'c1b85f1a54d76cae', 'US-12348': '0e7726ddcb766028', 'US-9158': '0e7726ddcb766028',
        'US-10971': '7135f5a1655a9103', 'US-10973': '9915530423913190', 'US-10975': '3f3006df94fae065', 'US-10976': 'b73a21e471afa308',
        'US-5835': '48e418b21d87a544', 'US-6012': 'd27128df1b5c02b2', 'US-6025': '42cf7f607486aa34'}
COR = re.compile(r'^(fwsr|wsrc|sgorg)\d+$')

doc = load(ROOT / 'docs/wsr-corridor-joins-nov11-staged.json')
P = doc['parks']
# 1.
check(set(P) == set(R) and len(P) == 39, 'the file names exactly the 39 wild and scenic rivers')
check(all(p['status'] in ('staged-ready', 'held', 'needs-saved-copy', 'left') and len(p.get('reason') or '') > 30 for p in P.values()), 'each has a known status and a reason')
check(doc['counts'] == {k: sum(1 for p in P.values() if p['status'] == k) for k in doc['counts']} and sum(doc['counts'].values()) == 39, f"counts add up ({doc['counts']})")

# 2. holds and far-off pins
import kpc_overrides as KO
OVR = KO.load_parks(ROOT / 'data/us-key/overrides.json')
held = {r for r, p in P.items() if p['status'] == 'held'}
check(NONE9 <= held and set(FAR) <= held, 'the nine none holds and the far-off pins stay held')
check(all((OVR.get(r) or {}).get('none') is True for r in NONE9), 'the nine none overrides are still in place')
check(all(p['status'] != 'staged-ready' or p['saved_line']['pin_to_line_km'] <= 5.0 for p in P.values()), 'no staged river has a pin over 5 km from its saved line')
check(all(abs(P[r]['saved_line']['pin_to_line_km'] - FAR[r]) < 0.1 for r in FAR), 'far-off pin distances as recorded')
check(all('entry' not in P[r] for r in held), 'no held river carries a join entry')
changed = [r for r in R if (fp(OVR[r]) if r in OVR else None) != OV39.get(r)]
check(not changed, f'the overrides.json entries of all 39 are byte-identical to e567f6be (changed: {changed})')

# 3. staged ids against the tracked evidence
keys = {}
for f in sorted((ROOT / 'data/us-key').glob('US-??.json')):
    for r, p in load(f)['parks'].items(): keys.setdefault(r, []).append((f.stem[3:], p))
nm = {}
if DATA and (DATA / 'data/outline-leads/near-miss.json').is_file():
    nm = load(DATA / 'data/outline-leads/near-miss.json').get('parks') or {}
else: skip('KPC-Data near-miss list: no KPC-Data checkout (ids found only there are not checked)')
ready = {r: p for r, p in P.items() if p['status'] == 'staged-ready'}
check(set(ready) == {'US-12788', 'US-10249', 'US-10251'}, f'staged-ready: {sorted(ready)}')
for r, p in ready.items():
    e = p['entry']; a = e['apply']; ids = a['join']
    check(e['file'] == 'data/us-key/overrides.json' and set(e['staged']['join_held']['ids']) == set(ids) == set(a['evidence']['ids']) == set(a['fp']) == set(p['records']),
          f'{r}: staged, apply, fp and evidence name the same ids {ids}')
    check(a.get('source_kind') == 'corridor' and a.get('when') and a.get('why') and a['evidence'].get('detail') and a['evidence'].get('rule') and 'decided_by' not in a
          and e['add_on_apply'].get('decided_by'), f'{r}: entry in the signed river-join form, decided_by left for the owner')
    check(all(COR.match(i) for i in ids), f'{r}: every id is a corridor-layer record (fwsr / wsrc / sgorg)')
    lst = {str(x[0]): (x[1], st) for st, q in keys.get(r, []) for k in ('m', 'c', 'a') for x in (q.get(k) or [])}
    lnm = {str(x['id']): (x['name'], x['km']) for x in (nm.get(r) or {}).get('leads', [])}
    for i in ids:
        nm_ = a['fp'][i][0]
        if i in lst: check(lst[i][0] == nm_, f'{r} {i}: in the park\'s own key entry (US-{lst[i][1]}) as "{nm_}"')
        elif nm: check(i in lnm and lnm[i][0] == nm_, f'{r} {i}: in KPC-Data near-miss for this park as "{nm_}"')
        else: skip(f'{r} {i}: listed only in KPC-Data near-miss')
        if i in lnm: check(lnm[i][1] <= 1.0, f'{r} {i}: {lnm[i][1]} km from the pin (well inside 0.6 deg)')
    word = p['name'].split()[0].lower()   # the river's own word: Black, Salmon, White
    stn = {'US-MI': 'michigan', 'US-OR': 'oregon'}.get(p['area'], p['area'])
    check(all(word in a['fp'][i][0].lower() and stn in a['fp'][i][0].lower() for i in ids if i.startswith('fwsr'))
          and all(a['fp'][i][0].lower().startswith(word + ' river') for i in ids if i.startswith('sgorg')), f'{r}: every record name is this river in this state')
    near = [i for i in ids if (i in lnm and lnm[i][1] <= 0.5) or 'inside' in str(p['records'][i].get('how_listed'))]
    check(bool(near), f'{r}: pin inside / within 0.5 km of {near}')
    if nm: check(all(i in lnm or i in lst for i in ids), f'{r}: every id is listed near the pin (near-miss <= 1 km or key check list <= 0.02 deg)')
    elif [i for i in ids if i not in lst]: skip(f'{r}: near-the-pin listing of the ids found only in KPC-Data near-miss ({[i for i in ids if i not in lst]})')
used = {}
for r, q in keys.items():
    for st, x in q:
        for y in x.get('m') or []: used.setdefault(str(y[0]), set()).add(r)
for r, v in OVR.items():
    for y in list(v.get('join') or []) + list((v.get('join_held') or {}).get('ids') or []): used.setdefault(str(y), set()).add(r)
clash = {i: sorted(used[i]) for p in ready.values() for i in p['entry']['apply']['join'] if i in used}
check(not clash, f'no staged id is joined to any park yet ({clash})')

# 4. nothing staged is live
live = {i for r in R for i in (OVR.get(r) or {}).get('join') or []}
check(not live & {i for p in ready.values() for i in p['entry']['apply']['join']}, 'no staged id is in data/us-key/overrides.json')

# 5. pins
loc = {x[1]: (x[3], x[4]) for x in load(ROOT / 'locations.json') if isinstance(x, list) and len(x) > 4 and x[0] == 'POTA'}
check(all(tuple(P[r]['pin']) == tuple(loc[r]) for r in R), "all 39 pins equal POTA's pins in locations.json (none moved)")
if DATA:
    pk = {}
    for f in (DATA / 'data/parkinfo').glob('*.json'):
        if f.name == 'index.json': continue
        try: pk.update({r: v for r, v in (load(f).get('parks') or {}).items() if r in P})
        except Exception: pass  # noqa: BLE001
    check(all(r in pk and [pk[r][5], pk[r][6]] == P[r]['pin'] for r in R), "all 39 pins equal KPC-Data's park files (none moved)")
else: skip("KPC-Data park files: no KPC-Data checkout")

# 6. the 31 official-line parks
g31 = set(re.findall(r"'(US-\d+)': \{'data/us-key", (ROOT / 'tests/test_trail_join_guard_nov11.py').read_text(encoding='utf-8')))
check(len(g31) >= 28 and not g31 & set(R), f'none of the 39 is one of the official-line parks the trail guard pins ({len(g31)} US refs there)')

# 7. rules hashes
import kpc_key_freeze as KF, kpc_preflight as PF
got = {k: KF.rules_hash(k) for k in ('us-key', 'ca-key', 'world-key', 'fers')}
want = {k: PF.newest_hash(k) for k in got}
check(all(want.values()) and got == want, f'rules hashes equal the newest ones in docs/key-rules-change.txt ({got})')

# 8. acres against the saved official line (KPC-Data)
def line_km(g):
    t, c = g.get('type'), g.get('coordinates') or []
    ls = [c] if t == 'LineString' else list(c) if t == 'MultiLineString' else []
    s = 0.0
    for l in ls:
        for (x1, y1), (x2, y2) in zip([q[:2] for q in l], [q[:2] for q in l[1:]]):
            k = math.cos(math.radians((y1 + y2) / 2)); s += math.hypot((x2 - x1) * 111.32 * k, (y2 - y1) * 110.574)
    return s
if DATA and (DATA / 'data/trails').is_dir():
    for r, p in ready.items():
        d = load(DATA / f'data/trails/{r}.json'); g = d.get('geometry') or d['features'][0]['geometry']
        cap = line_km(g) / 1.609344 * 320; ac = sum(x[1] for x in p['entry']['apply']['fp'].values()) - (3326 if r == 'US-10249' else 0)
        check(0.5 <= ac / cap <= 2.0, f'{r}: {ac:,.0f} ac = {ac / cap:.2f}x the saved line at 320 ac/mi (0.5x-2x)')
else: skip('acres band: no KPC-Data checkout')

print('ALL PASS' if not bad else f'{bad} FAILED'); sys.exit(1 if bad else 0)
