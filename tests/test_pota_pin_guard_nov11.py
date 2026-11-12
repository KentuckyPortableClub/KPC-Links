#!/usr/bin/env python3
"""Nov 11 (data-quality review, rank 14 'never move POTA pins'): the nightly pin updaters (kpc_canada.py, kpc_northam.py,
kpc_world_pota.py and the Finder search list kpc_search_lists.py) against a FAKE api.pota.app. urllib's urlopen and time.sleep are
replaced in this process: no socket is opened.

What is pinned here:
  * the published pin FOLLOWS POTA (a park POTA moved gets the new pin) and the move is recorded in data/pota-pin-changes.json
    (old -> new, km, date); a move past 1 km is flagged 'check', past 15 km 'big'; the pin still follows POTA;
  * a pin POTA sent that cannot be a pin (no number, 0,0, past 90 / 180, or the old pin turned around) keeps the LAST GOOD pin and is
    recorded as 'kept-last-good'; the park is not dropped and not called 'Retired by POTA';
  * kpc_northam.py: a failed /locations answer used to rewrite northam.json with no POTA rows at all; an empty program answer likewise;
  * kpc_world_pota.py: a 0,0 pin used to drop the park (then 'Retired by POTA');
  * the Kentucky club pin on the search list is not changed, but a difference from POTA's pin is recorded."""
import contextlib, io, json, os, pathlib, runpy, sys, tempfile, time, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCR = ROOT / '.github' / 'scripts'
sys.path.insert(0, str(SCR))
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


class Resp:
    def __init__(self, body): self.b = body
    def read(self): return self.b
    def __enter__(self): return self
    def __exit__(self, *a): return False


API = {}          # url -> list/dict to answer, or an Exception to raise
ASKED = []


def fake_urlopen(req, *a, **k):
    u = req.full_url if hasattr(req, 'full_url') else str(req)
    ASKED.append(u)
    if not u.startswith('https://api.pota.app/'): raise AssertionError('a request to somewhere that is not the fake api.pota.app: ' + u)
    v = API.get(u, [])
    if isinstance(v, Exception): raise v
    return Resp(json.dumps(v).encode())


urllib.request.urlopen = fake_urlopen
time.sleep = lambda *a, **k: None


def run(script, cwd):
    os.chdir(cwd)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try: runpy.run_path(str(SCR / script), run_name='__main__')
        except SystemExit: pass
    return buf.getvalue()


def sandbox():
    d = pathlib.Path(tempfile.mkdtemp(prefix='kpc-pin-'))
    (d / 'data').mkdir()
    return d


def jl(p, d=None):
    try: return json.load(open(p))
    except Exception: return d


def log_events(d): return {(e['ref'], e['kind']): e for e in (jl(d / 'data/pota-pin-changes.json', {}) or {}).get('events', [])}


# ---------------------------------------------------------------- the guard on its own
import kpc_pin_guard as PG   # noqa: E402
check(PG.problem(0, 0) == '0,0 pin' and PG.problem(91, 5) and PG.problem(5, 181) and PG.problem(None, 5) and PG.problem('x', 1) and PG.problem(float('nan'), 1),
      'problem(): 0,0 / past 90 / past 180 / missing / not a number / NaN are all unusable')
check(PG.problem(36.5, -85.2) == '' and PG.problem(0, -85.2) == '' and PG.problem(-33.9, 151.2) == '', 'problem(): a real pin (even on the equator line or south) is fine')
import importlib.util
spec = importlib.util.spec_from_file_location('pc', SCR / 'kpc_precheck.py')
try:
    PC = importlib.util.module_from_spec(spec); spec.loader.exec_module(PC)
    same = all(bool(PG.problem(a, b)) == bool(PC.bad_pin((None, a, b))) for a, b in ((0, 0), (91, 0), (0, 181), (-90, 180), (45, -75), (None, 1), ('a', 2), (-91, 5)))
    check(same, "problem() agrees with kpc_precheck.bad_pin on the same table (the key's own test)")
except Exception as e:  # noqa: BLE001
    print('SKIP-NOTE precheck not importable here:', str(e)[:80])
p, ev = PG.decide('CA-1', (45.0, -75.0), (45.0, -75.0), 't', today='2026-11-11')
check(p == (45.0, -75.0) and ev is None, 'decide(): same pin = no event')
p, ev = PG.decide('CA-1', (45.0, -75.0), (45.000004, -75.0), 't', today='2026-11-11')
check(ev is None, 'decide(): a change below one storage step (5 decimals) is the same pin')
p, ev = PG.decide('CA-1', (45.0, -75.0), (45.0005, -75.0), 't', today='2026-11-11')
check(p == (45.0005, -75.0) and ev['kind'] == 'moved' and ev['flag'] == '' and 0.04 < ev['km'] < 0.07, f"decide(): a 55 m move follows POTA, recorded, not flagged ({ev and ev['km']} km)")
p, ev = PG.decide('CA-1', (45.0, -75.0), (45.05, -75.0), 't', today='2026-11-11')
check(p == (45.05, -75.0) and ev['flag'] == 'check', f"decide(): a 5.6 km move follows POTA and is flagged 'check' ({ev['flag']})")
p, ev = PG.decide('CA-1', (45.0, -75.0), (47.0, -75.0), 't', today='2026-11-11')
check(p == (47.0, -75.0) and ev['flag'] == 'big', "decide(): a 222 km move still follows POTA and is flagged 'big'")
p, ev = PG.decide('CA-1', (45.0, -75.0), (-75.0, 45.0), 't', today='2026-11-11')
check(p == (45.0, -75.0) and ev['kind'] == 'kept-last-good' and 'swapped' in ev['why'], 'decide(): the old pin turned around is not taken')
p, ev = PG.decide('CA-1', (45.3, 60.1), (60.1, 45.3), 't', today='2026-11-11')
check(p == (45.3, 60.1) and ev['kind'] == 'kept-last-good', 'decide(): a swap that is still a possible place is caught by comparison with the old pin')
for bad in ((0, 0), (None, None), (95.0, 10.0), (10.0, 200.0), ('x', 'y')):
    p, ev = PG.decide('CA-1', (45.0, -75.0), bad, 't', today='2026-11-11')
    check(p == (45.0, -75.0) and ev['kind'] == 'kept-last-good', f'decide(): {bad} keeps the last good pin')
check(PG.decide('CA-1', None, (0, 0), 't') == (None, None), 'decide(): unusable pin and no earlier pin: left to the caller (None, no event)')
check(PG.decide('CA-1', (0, 0), (45.0, -75.0), 't')[0] == (45.0, -75.0), 'decide(): an earlier 0,0 is not a last good pin: POTA fixing its error is taken')
check(PG.club_pin_event('US-1', (36.5, -85.2), (36.5, -85.2), 's') is None and PG.club_pin_event('US-1', (36.5, -85.2), (0, 0), 's') is None, 'club_pin_event(): same, or POTA unusable: nothing to say')
e = PG.club_pin_event('US-1', (36.5, -85.2), (36.6, -85.2), 's', today='2026-11-11')
check(e and e['kind'] == 'club-pin-differs' and e['flag'] == 'check' and e['old'] == [36.5, -85.2] and e['new'] == [36.6, -85.2], 'club_pin_event(): a 11 km difference is recorded, flagged')

# record(): dedupe, aging, writes only when something is new
d = sandbox(); os.chdir(d)
lines = []
mv = PG.decide('CA-9', (45.0, -75.0), (45.05, -75.0), 'canada', 'Nine', today='2026-11-11')[1]
n1 = PG.record([mv], today='2026-11-11', say=lines.append)
t1 = (d / 'data/pota-pin-changes.json').read_text()
n2 = PG.record([mv], today='2026-11-12', say=lines.append)
check(n1 == 1 and n2 == 0 and (d / 'data/pota-pin-changes.json').read_text() == t1, 'record(): the same event the next night is not added again and the file is not rewritten')
check(any(x.startswith('::warning title=POTA pin check::') and 'CA-9' in x for x in lines), "record(): a 'check' event prints one warning naming the park")
old_ev = dict(mv, ref='CA-OLD', date='2026-06-01')
PG.record([old_ev], today='2026-06-02', say=lambda x: None)
PG.record([dict(mv, ref='CA-10')], today='2026-11-11', say=lambda x: None)
refs = {e['ref'] for e in jl(d / 'data/pota-pin-changes.json')['events']}
check('CA-OLD' not in refs and {'CA-9', 'CA-10'} <= refs, 'record(): entries older than 120 days are dropped')

# ---------------------------------------------------------------- kpc_canada.py
d = sandbox()
old_rows = [['POTA', 'CA-0001', 'One', 45.0, -75.0, 'u'], ['POTA', 'CA-0002', 'Two', 46.0, -76.0, 'u'], ['POTA', 'CA-0003', 'Three', 47.0, -77.0, 'u'],
            ['POTA', 'CA-0004', 'Four', 48.0, -78.0, 'u'], ['POTA', 'CA-0005', 'Five', 50.1, -100.2, 'u'], ['POTA', 'CA-0006', 'Six', 51.0, -101.0, 'u']]
json.dump({'rows': old_rows}, open(d / 'data/canada.json', 'w'))
API.clear()
for pv in 'AB BC MB NB NL NS NT NU ON PE QC SK YT'.split(): API[f'https://api.pota.app/location/parks/CA-{pv}'] = []
API['https://api.pota.app/location/parks/CA-ON'] = [
    {'reference': 'CA-0001', 'name': 'One', 'latitude': 45.0005, 'longitude': -75.0},      # 55 m: followed, recorded
    {'reference': 'CA-0002', 'name': 'Two', 'latitude': 0, 'longitude': 0},                 # 0,0: last good kept
    {'reference': 'CA-0003', 'name': 'Three', 'latitude': 47.0, 'longitude': -77.0},        # unchanged
    {'reference': 'CA-0004', 'name': 'Four', 'latitude': 49.5, 'longitude': -78.0},         # 167 km: followed, 'big'
    {'reference': 'CA-0005', 'name': 'Five', 'latitude': -100.2, 'longitude': 50.1},        # turned around
    {'reference': 'CA-0006', 'name': 'Six', 'latitude': None, 'longitude': None},           # listed with no number
    {'reference': 'CA-0007', 'name': 'Seven', 'latitude': 0, 'longitude': 0},               # new park, 0,0, no earlier pin: as before (passed on, the key marks pin00)
    {'reference': 'CA-0008', 'name': 'Eight', 'latitude': None, 'longitude': None}]         # new park, no number: skipped as before
out = run('kpc_canada.py', d)
rows = {r[1]: r for r in jl(d / 'data/canada.json')['rows'] if r[0] == 'POTA'}
check([rows['CA-0001'][3], rows['CA-0001'][4]] == [45.0005, -75.0], 'canada: the moved park follows POTA')
check([rows['CA-0002'][3], rows['CA-0002'][4]] == [46.0, -76.0], 'canada: 0,0 from POTA keeps the last good pin')
check([rows['CA-0004'][3], rows['CA-0004'][4]] == [49.5, -78.0], 'canada: a 167 km move still follows POTA')
check([rows['CA-0005'][3], rows['CA-0005'][4]] == [50.1, -100.2], 'canada: a turned-around pin keeps the last good pin')
check([rows['CA-0006'][3], rows['CA-0006'][4]] == [51.0, -101.0], 'canada: a park listed with no number keeps its pin (it used to be dropped)')
check('CA-0007' in rows and rows['CA-0007'][3:5] == [0.0, 0.0] and 'CA-0008' not in rows, 'canada: a new park with no earlier pin behaves as before (0,0 passed on, no-number skipped)')
rr = jl(d / 'data/retired-refs.json', {'refs': {}})
check(not (set(rr.get('refs', {})) & {'CA-0002', 'CA-0005', 'CA-0006'}), "canada: no park whose pin was unusable is called 'Retired by POTA' (CA-0006 used to be)")
ev = log_events(d)
check(set(ev) == {('CA-0001', 'moved'), ('CA-0002', 'kept-last-good'), ('CA-0004', 'moved'), ('CA-0005', 'kept-last-good'), ('CA-0006', 'kept-last-good')}, f'canada: the pin log holds exactly those events ({sorted(ev)})')
check(ev[('CA-0004', 'moved')]['flag'] == 'big' and ev[('CA-0001', 'moved')]['flag'] == '' and ev[('CA-0001', 'moved')]['old'] == [45.0, -75.0] and ev[('CA-0001', 'moved')]['new'] == [45.0005, -75.0],
      'canada: flags and old -> new are right')
check('::warning title=POTA pin check::' in out, 'canada: a person is told in the log')
check(all(u.startswith('https://api.pota.app/') for u in ASKED), 'canada: only the fake api.pota.app was asked')
# nothing changed the next night: no new events, files identical
before = (d / 'data/pota-pin-changes.json').read_text(), (d / 'data/canada.json').read_text()
run('kpc_canada.py', d)
check(before == ((d / 'data/pota-pin-changes.json').read_text(), (d / 'data/canada.json').read_text()), 'canada: a second night with the same answer changes nothing (no extra commit)')

# ---------------------------------------------------------------- kpc_northam.py
d = sandbox()
mx = [['POTA', f'MX-{i:04d}', f'M{i}', 20.0 + i / 100, -100.0, 'u'] for i in range(12)]
bz = [['POTA', 'BZ-0001', 'B1', 17.2, -88.7, 'u']]
json.dump({'rows': mx + bz}, open(d / 'data/northam.json', 'w'))
API.clear()
API['https://api.pota.app/locations'] = RuntimeError('boom')
run('kpc_northam.py', d)
got = jl(d / 'data/northam.json')
check(sorted(tuple(r[:5]) for r in got['rows']) == sorted(tuple(r[:5]) for r in mx + bz),
      'northam: POTA /locations failed -> all 13 last POTA pins stay (the file used to be rewritten with none)')
API.clear()
API['https://api.pota.app/locations'] = [{'locationDesc': 'MX-A'}, {'locationDesc': 'BZ-A'}]
API['https://api.pota.app/location/parks/MX-A'] = []                      # answered, but with nothing: 12 -> 0
API['https://api.pota.app/location/parks/BZ-A'] = [{'reference': 'BZ-0001', 'name': 'B1', 'latitude': 0, 'longitude': 0}]
run('kpc_northam.py', d)
rows = {r[1]: r for r in jl(d / 'data/northam.json')['rows'] if r[0] == 'POTA'}
check(sum(1 for r in rows if r.startswith('MX-')) == 12, 'northam: a program that answers with an empty list (12 -> 0) keeps its last pins')
check(rows['BZ-0001'][3:5] == [17.2, -88.7], 'northam: 0,0 from POTA keeps the last good pin')
check(('BZ-0001', 'kept-last-good') in log_events(d), 'northam: and records it')
API['https://api.pota.app/location/parks/MX-A'] = [{'reference': f'MX-{i:04d}', 'name': f'M{i}', 'latitude': 20.0 + i / 100 + (0.2 if i == 3 else 0), 'longitude': -100.0} for i in range(12)]
API['https://api.pota.app/location/parks/BZ-A'] = [{'reference': 'BZ-0001', 'name': 'B1', 'latitude': 17.2, 'longitude': -88.7}]
run('kpc_northam.py', d)
rows = {r[1]: r for r in jl(d / 'data/northam.json')['rows'] if r[0] == 'POTA'}
check(rows['MX-0003'][3] == 20.23 and ('MX-0003', 'moved') in log_events(d) and log_events(d)[('MX-0003', 'moved')]['flag'] == 'big', 'northam: a 22 km move follows POTA and is flagged big')

# ---------------------------------------------------------------- kpc_world_pota.py
d = sandbox()
(d / 'data/pota/t').mkdir(parents=True)
fr = [['FR-%04d' % i, 'F%d' % i, 48.0 + i / 100, 2.0] for i in range(6)]
json.dump(sorted(fr), open(d / 'data/pota/t/48_2.json', 'w'))
API.clear()
API['https://api.pota.app/locations'] = [{'locationDesc': 'FR-A'}, {'locationDesc': 'US-KY'}]
API['https://api.pota.app/location/parks/FR-A'] = [
    {'reference': 'FR-0000', 'name': 'F0', 'latitude': 48.0, 'longitude': 2.0},
    {'reference': 'FR-0001', 'name': 'F1', 'latitude': 0, 'longitude': 0},                   # 0,0: used to DROP the park
    {'reference': 'FR-0002', 'name': 'F2', 'latitude': 48.02, 'longitude': 2.0},
    {'reference': 'FR-0003', 'name': 'F3', 'latitude': 48.03, 'longitude': 2.05},          # ~3.7 km move
    {'reference': 'FR-0004', 'name': 'F4', 'latitude': 2.0, 'longitude': 48.04},            # swapped: still a possible place
    {'reference': 'FR-0005', 'name': 'F5', 'latitude': 95, 'longitude': 2.0},               # past 90
    {'reference': 'FR-0006', 'name': 'F6 new', 'latitude': 0, 'longitude': 0}]              # new, 0,0: skipped as before
run('kpc_world_pota.py', d)
tiles = {}
for f in (d / 'data/pota/t').glob('*.json'):
    for r in jl(f): tiles[r[0]] = r
check(all(f'FR-000{i}' in tiles for i in range(6)), f'world: all six parks are still on the map ({sorted(tiles)})')
check(tiles['FR-0001'][2:] == [48.01, 2.0] and tiles['FR-0004'][2:] == [48.04, 2.0] and tiles['FR-0005'][2:] == [48.05, 2.0], 'world: 0,0 / swapped / past-90 keep the last good pin')
check(tiles['FR-0003'][2:] == [48.03, 2.05] and 'FR-0006' not in tiles, 'world: a move follows POTA; a new 0,0 park is skipped as before')
ev = log_events(d)
check(set(ev) == {('FR-0001', 'kept-last-good'), ('FR-0003', 'moved'), ('FR-0004', 'kept-last-good'), ('FR-0005', 'kept-last-good')}, f'world: the pin log ({sorted(ev)})')
check(ev[('FR-0003', 'moved')]['flag'] == 'check', 'world: the 3.7 km move is flagged')
check('FR-0001' not in (jl(d / 'data/retired-refs.json', {'refs': {}}) or {}).get('refs', {}), "world: FR-0001 is not 'Retired by POTA'")

# ---------------------------------------------------------------- kpc_search_lists.py (the US list new_refs keeps)
d = sandbox()
os.chdir(d)
json.dump([['POTA', 'US-0001', 'One', 40.0, -80.0, 'u'], ['POTA', 'US-0002', 'Two', 41.0, -81.0, 'u'], ['POTA', 'US-0003', 'Three', 42.0, -82.0, 'u'],
           ['POTA', 'US-0004', 'Four', 43.0, -83.0, 'u'], ['POTA', 'US-1264', 'Kentucky One', 37.0, -85.0, 'u']], open('locations.json', 'w'))
json.dump({'parks': [{'c': 'US-1264', 'n': 'Kentucky One', 'la': 37.0, 'lo': -85.0}], 'kff': [], 'summits': []}, open('kpc-ky-data.json', 'w'))
json.dump({'box': [36, 39, -90, -81], 'rows': [], 'total': 0}, open('locations-ky.json', 'w'))
import kpc_search_lists as SL   # noqa: E402
cur = {'US-0001': {'name': 'One', 'la': 40.0, 'lo': -80.0},
       'US-0002': {'name': 'Two', 'la': 41.5, 'lo': -81.0},      # moved 55 km
       'US-0003': {'name': 'Three', 'la': 142.0, 'lo': -82.0},   # impossible
       'US-0004': {'name': 'Four', 'la': -83.0, 'lo': 43.0},     # turned around
       'US-1264': {'name': 'Kentucky One', 'la': 37.2, 'lo': -85.0},   # POTA's pin is 22 km from the club's
       'US-0005': {'name': 'New', 'la': 44.0, 'lo': -84.0}}
SL.update(pota=cur)
rows = {r[1]: r for r in json.load(open('locations.json'))}
check(rows['US-0002'][3:5] == [41.5, -81.0], 'search list: a moved park follows POTA')
check(rows['US-0003'][3:5] == [42.0, -82.0] and rows['US-0004'][3:5] == [43.0, -83.0], 'search list: an impossible pin, and an old pin turned around, keep the last good pin (past 90 used to be published)')
check(rows['US-1264'][3:5] == [37.0, -85.0], "search list: the Kentucky club pin is NOT changed")
check(rows['US-0005'][3:5] == [44.0, -84.0], 'search list: a new park gets POTA pin')
kinds = {(e['ref'], e['kind']) for e in SL.PINLOG}
check(kinds == {('US-0002', 'moved'), ('US-0003', 'kept-last-good'), ('US-0004', 'kept-last-good'), ('US-1264', 'club-pin-differs')}, f'search list: PINLOG holds those four ({sorted(kinds)})')
PG.record(SL.PINLOG, say=lambda x: None)
check(set(log_events(d)) == kinds, 'search list: new_refs writes them with PG.record')


# ---------------------------------------------------------------- kpc_state_links.py (data/parkinfo: the third copy of POTA's pins)
d = sandbox(); (d / 'data/parkinfo').mkdir()
old = {f'US-{i:04d}': [f'P{i}', '', 'State Park', '', '', 35.0 + i / 10, -85.0, 1, 1, 1] for i in range(12)}
json.dump({'state': 'TN', 'updated': '2026-11-01', 'stateSite': '', 'parks': old}, open(d / 'data/parkinfo/US-TN.json', 'w'))
API.clear()
API['https://api.pota.app/location/parks/US-TN'] = [
    {'reference': f'US-{i:04d}', 'name': f'P{i}', 'latitude': 35.0 + i / 10, 'longitude': -85.0, 'activations': 1, 'attempts': 1, 'qsos': 1} for i in range(12)]
API['https://api.pota.app/location/parks/US-TN'][1].update(latitude=0, longitude=0)               # 0,0
API['https://api.pota.app/location/parks/US-TN'][2].update(latitude=35.2, longitude=-84.0)        # ~91 km east: followed, 'big'
API['https://api.pota.app/location/parks/US-TN'][3].update(latitude=None, longitude=None)         # no number
os.environ['STATES'] = 'TN'
run('kpc_state_links.py', d)
got = jl(d / 'data/parkinfo/US-TN.json')['parks']
check(got['US-0001'][5:7] == [35.1, -85.0] and got['US-0003'][5:7] == [35.3, -85.0], 'parkinfo: 0,0 and a missing number keep the last good pin')
check(got['US-0002'][5:7] == [35.2, -84.0], 'parkinfo: a 91 km move still follows POTA')
ev = {(e['ref'], e['kind']): e for e in (jl(d / 'data/parkinfo/pin-changes.json', {}) or {}).get('events', [])}
check(set(ev) == {('US-0001', 'kept-last-good'), ('US-0002', 'moved'), ('US-0003', 'kept-last-good')} and ev[('US-0002', 'moved')]['flag'] == 'big', f'parkinfo: the log ({sorted(ev)})')
API['https://api.pota.app/location/parks/US-TN'] = []        # 200 with nothing in it
snap = (d / 'data/parkinfo/US-TN.json').read_text()
run('kpc_state_links.py', d)
check((d / 'data/parkinfo/US-TN.json').read_text() == snap, 'parkinfo: an empty list for a state with 12 parks keeps last week\'s file (it used to be rewritten with no parks)')
os.environ.pop('STATES')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
