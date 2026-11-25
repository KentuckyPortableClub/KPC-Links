#!/usr/bin/env python3
"""24 Nov 2026 (owner t2067u 8:32 PM CT 'I agree work on it'): the trail fixes from the check of 787 loose-name confirms.
(1) built-only hand picks for US-8313 and US-12717 (data/trails-hand.json), read from a saved copy with their filter;
(2) a state line read before Nov 2 (or with no read date) is stale: not reused, and a new line may replace it only when
it is at least half the saved length (anything shorter keeps the old line and goes to a person);
owner call: closed segments are not drawn, except 'closed to' phrases on an allow list that leave the trail usable on foot;
owner call: a line more than 1 km (0.6 mi) from POTA's pin goes to a person;
(4) no found line under 1 km (0.6 mi) on an area park (kpc_finds_lines.py / kpc_us_trails.py).
Synthetic data only. No network. kpc_state_trails.py / kpc_us_trails.py are not imported (both start work at import).
Prints PASS / FAIL, ends ALL PASS or SOME FAILED."""
import json, math, os, pathlib, re, socket, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts'))


def _no_net(*a, **k):
    raise RuntimeError('no network in tests')


socket.socket.connect = _no_net
SRC = (HERE / '.github/scripts/kpc_state_trails.py').read_text(encoding='utf-8')
UST = (HERE / '.github/scripts/kpc_us_trails.py').read_text(encoding='utf-8')
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg, flush=True)
    ok = ok and bool(c)


def km(a, b, c, d):
    r = math.radians
    return 6371 * 2 * math.asin(math.sqrt(math.sin(r(c - a) / 2) ** 2 + math.cos(r(a)) * math.cos(r(c)) * math.sin(r(d - b) / 2) ** 2))


ns = {'json': json, 'os': os, 're': re, 'math': math, 'km': km}
a, b = SRC.find('\nPLANNED = re.compile('), SRC.find('\nWATER = re.compile(')
if a > 0 and b > a: exec(compile(SRC[a + 1:b], 'top', 'exec'), ns)
a, b = SRC.find('\ndef trail_line_stats('), SRC.find('\n# ---------------------------------------------------------------- run')
if a > 0 and b > a: exec(compile(SRC[a + 1:b], 'helpers', 'exec'), ns)
need = ('saved_record', 'keep_saved_reason', 'stale_read', 'closed', 'not_drawn', 'osm_closed', 'pin_check_reason',
        'short_replace_reason', 'line_near_km', 'where_test', 'saved_part_lines')
missing = [n for n in need if not callable(ns.get(n))]
check(not missing, f'kpc_state_trails.py defines the 24 Nov helpers (missing: {missing})')
G = lambda n: ns.get(n) or (lambda *a, **k: None)


def write_line(folder, ref, npts, km_len, lo=0.0, la=0.0):
    deg = km_len / 111.195
    pts = [[lo, la + i * deg / (npts - 1)] for i in range(npts)]
    feat = {'type': 'Feature', 'properties': {'ref': ref, 'source': 'official', 'by': 'US Forest Service'},
            'geometry': {'type': 'MultiLineString', 'coordinates': [pts]}}
    (folder / f'{ref}.json').write_text(json.dumps(feat), encoding='utf-8')


# ---------------------------------------------------------------- fix 1: built-only hand picks
H = json.load(open(HERE / 'data/trails-hand.json', encoding='utf-8')).get('parks') or {}
for ref in ('US-8313', 'US-12717'):
    parts = (H.get(ref) or {}).get('parts') or []
    check(bool(parts) and all(p.get('saved') and re.search(r"TRAILSTAT IN \('Constructed','Designated'\)", p.get('where') or '')
                             and 'Planned' not in (p.get('where') or '') for p in parts),
          f'fix 1: {ref} has a hand pick that takes only built segments, from a saved copy of the official layer')
with tempfile.TemporaryDirectory() as t:
    T = pathlib.Path(t)
    seg = lambda name, stat, lo, extra=None: {'type': 'Feature', 'properties': dict({'SYSTEMNAME': name, 'TRAILSTAT': stat}, **(extra or {})),
                                              'geometry': {'type': 'LineString', 'coordinates': [[lo, 35.0], [lo + 0.01, 35.01]]}}
    fc = {'type': 'FeatureCollection', 'features': [seg('Zeta Trail', 'Constructed', -80.0), seg('Zeta Trail', 'Designated', -80.1),
                                                    seg('Zeta Trail', 'Planned', -80.2), seg('Other Trail', 'Constructed', -80.3),
                                                    seg('Zeta Trail', 'Constructed', -80.4, {'STATUS': 'Closed'})]}
    (T / 'saved.geojson').write_text(json.dumps(fc))
    got = G('saved_part_lines')({'saved': 'saved.geojson', 'where': "SYSTEMNAME = 'Zeta Trail' AND TRAILSTAT IN ('Constructed','Designated')"}, [str(T)])
    check(isinstance(got, list) and sorted(round(l[0][0], 1) for l in got) == [-80.1, -80.0],
          f'fix 1: the saved copy gives the built segments only (no planned, no other trail, no closed); got {got and len(got)}')
    check(G('saved_part_lines')({'saved': 'nope.geojson', 'where': '1=1'}, [str(T)]) is None, 'fix 1: no saved copy on disk = None (the bot notes it)')
try:
    G('where_test')("NAME LIKE 'x%'"); bad = False
except ValueError:
    bad = True
check(bad, 'fix 1: a filter that cannot be read on a saved copy is refused, never guessed')

# ---------------------------------------------------------------- fix 2: lines read before Nov 2 are stale
SR, KR, ST = G('saved_record'), G('keep_saved_reason'), G('stale_read')
check(ST('2026-10-30') is True and ST('') is True and ST(None) is True and ST('2026-11-02') is False and ST('2026-11-20') is False,
      'fix 2: read before Nov 2 or no read date = stale; Nov 2 or later = not stale')
with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t)
    write_line(d, 'US-S', 100, 100)
    old = {'US-S': {'ref': 'US-S', 'read': '2026-10-28', 'official': True, 'source': 'official', 'by': 'US Forest Service', 'km': 100}}
    s_old = SR('US-S', old, {}, str(d)) or {}
    check(s_old.get('stale') is True and KR(s_old, True, 60, 50) is None,
          'fix 2: a shorter official line at least half as long may replace a stale saved line (read Oct 28)')
    new = {'US-S': dict(old['US-S'], read='2026-11-04')}
    s_new = SR('US-S', new, {}, str(d)) or {}
    check(not s_new.get('stale') and 'kept' in (KR(s_new, True, 40, 30) or ''),
          'fix 2: a line read Nov 4 keeps the 75% guard (a shorter line is still blocked)')
    s_nat = SR('US-S', {}, {'US-S': {'ref': 'US-S', 'by': 'USGS National Transportation Dataset (public domain, Nov 7 extract)'}}, str(d)) or {}
    check(not s_nat.get('stale'), 'fix 2: a line only in index.json (national, US-9203 style) is not marked stale')
    check(KR(s_old, False, 120, 300) is not None, 'fix 2: a stale official line is still not replaced by an OpenStreetMap line')
check("if stale_read(x.get('read')): return False" in SRC, 'fix 2: fresh() does not reuse a stale line for 60 days')
check('REUSE_DAYS' in SRC and '75%' in SRC, 'fix 2: the 60-day reuse and 75% guards are still there')

# ---------------------------------------------------------------- grade: replacement must be at least half the saved length
SRH = G('short_replace_reason')
MI = ns.get('MI_PER_KM') or 0.621371
def _km(mi):
    return mi / MI
s100 = {'exists': True, 'official': True, 'km': _km(100), 'pts': 80, 'stale': True, 'by': 'US Forest Service'}
why5, hold5 = KR(s100, True, _km(5), 10), SRH(s100, _km(5))
check(why5 is not None and 'kept' in (why5 or '') and 'half' in (why5 or '') and hold5 and '5.0 mi' in hold5 and '100.0 mi' in hold5 and 'person checks' in hold5,
      'grade: a 5-mile new line against a 100-mile stale line is held for a person; the old line is kept')
check(KR(s100, True, _km(60), 50) is None and SRH(s100, _km(60)) is None,
      'grade: a 60-mile new line replaces a 100-mile stale line')
check(KR(s100, True, _km(50), 40) is None and SRH(s100, _km(50)) is None,
      'grade: the replacement floor is exactly 50% (a 50-mile line may replace a 100-mile stale line)')
check(KR(s100, True, _km(49.9), 40) is not None and SRH(s100, _km(49.9)),
      'grade: just under 50% of the saved length is held for a person')
check(SRH(dict(s100, stale=False), _km(5)) is None and SRH(s100, _km(5), True) is None,
      'grade: a non-stale saved line and a hand pick are not held by the half-length floor')
after = SRC.split('why = keep_saved_reason', 1)[-1].split('xs = [p[0]', 1)[0]
check('short_replace_reason(' in after and 'PIN_HELD.append(ref)' in after and "report.setdefault('check'" in after,
      'grade: a short replacement keeps the old line and goes to the same check list as a line far from the pin')

# ---------------------------------------------------------------- owner call: closed segments are not drawn
C, ND, OC = G('closed'), G('not_drawn'), G('osm_closed')
check(C({'TRAILSTAT': 'Closed'}) and C({'STATUS': 'Decommissioned'}) and ND({'CONDITION': 'Abandoned'}),
      'closed: a segment whose status says closed / decommissioned / abandoned is not drawn')
check(not C({'STATUS': 'Closed to motor vehicles'}) and not C({'STATUS': 'Seasonal closure'}) and not C({'STATUS': 'Open'})
      and not C({'NAME': 'Closed Loop Trail'}), 'closed: a partial or seasonal closure, an open trail, or a name is drawn')
check(C({'STATUS': 'Closed to the public'}) and C({'STATUS': 'closed'}),
      "closed: 'closed to the public' or a plain 'closed' is not drawn")
check(not C({'STATUS': 'Closed to vehicles'}) and not C({'STATUS': 'Closed to bikes'})
      and not C({'STATUS': 'Closed to horses'}) and not C({'STATUS': 'Closed to OHV'}),
      "closed: only allow-list 'closed to' phrases that leave the trail usable on foot are drawn")
check('CLOSED_TO_OK' in SRC and 'CLOSED_TO_OK_RE' in SRC,
      "closed: the 'closed to' exceptions are an explicit allow list, not a blanket 'closed to'")
check(OC({'access': 'no'}) and OC({'abandoned:highway': 'path'}) and not OC({'access': 'yes', 'highway': 'path'}),
      'closed: an OpenStreetMap way marked access=no or abandoned is not drawn')
check(SRC.count('not_drawn(') >= 4 and 'osm_closed(' in SRC.split('def osm_closed', 1)[1],
      'closed: the forest, agency and hand-pick readers and the OpenStreetMap search all skip closed segments')

# ---------------------------------------------------------------- owner call: lines over 1 km from POTA's pin go to a person
P = G('pin_check_reason')
check(P(0.9) is None and '1.4 mi' in (P(2.2) or '') and '0.6 mi' in (P(2.2) or '') and P(9.6, True) is None,
      "pin: a line over 1 km (0.6 mi) from POTA's pin is held for a person (miles in the reason); a hand pick is not held")
with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t)
    write_line(d, 'US-P', 10, 5, lo=-84.0, la=38.0)
    n = G('line_near_km')(str(d / 'US-P.json'), 38.0, -84.03)
    check(n is not None and 2.4 < n < 2.8, f'pin: distance from the pin to the saved line is measured (got {n})')
check("report.setdefault('check'" in SRC or "report['check']" in SRC, "pin: held lines go to the state report's 'check' list")
check('PIN_HELD.append(ref)' in SRC and 'held for a person' in SRC, 'pin: held lines are counted and the gate says so')

# ---------------------------------------------------------------- fix 4: no found line under 1 km on an area park
try:
    import kpc_finds_lines as FL
except Exception as e:  # noqa: BLE001
    FL = None; print('import kpc_finds_lines failed:', e)
ap = getattr(FL, 'area_park', None)
check(ap is not None and ap('BLM Recreation Management Area') and ap('State Wildlife Area') and not ap('National Recreation Trail')
      and not ap('Wild and Scenic River'), 'fix 4: area parks are the ones whose POTA type is not a trail / river / route')
ts = getattr(FL, 'too_short_for_area', None)
short = [[[-110.0, 40.0], [-110.0, 40.004]]]   # about 1,460 ft
longl = [[[-110.0, 40.0], [-110.0, 40.02]]]    # about 1.4 mi
check(ts is not None and ts({'min_km': 1.0}, short) and not ts({'min_km': 1.0}, longl) and not ts({}, short),
      'fix 4: a line under 1 km is too short for a row that carries min_km; rows without it are not changed')
with tempfile.TemporaryDirectory() as t:
    R = pathlib.Path(t)
    for dd in ('data/parkinfo', 'data/us-key', 'data/trails', 'kpcdata/data/intake', 'kpcdata/data/waiting/questions'): (R / dd).mkdir(parents=True)
    json.dump({'parks': {'US-1': ['Alpha Trails Recreation Area', '', 'BLM Recreation Management Area', '', '', '40.0', '-110.0'],
                         'US-2': ['Bravo National Recreation Trail', '', 'National Recreation Trail', '', '', '37.0', '-80.0'],
                         'US-3': ['Charlie Recreation Area', '', 'BLM Recreation Management Area', '', '', '41.0', '-111.0'],
                         'US-4': ['Delta Recreation Area', '', 'BLM Recreation Management Area', '', '', '42.0', '-112.0']}},
              open(R / 'data/parkinfo/US-XX.json', 'w'))
    json.dump({'parks': {r: {'n': r, 'm': []} for r in ('US-1', 'US-2', 'US-3', 'US-4')}}, open(R / 'data/us-key/US-XX.json', 'w'))
    json.dump({'type': 'Feature', 'geometry': {'type': 'LineString', 'coordinates': short[0]}}, open(R / 'data/trails/US-3.json', 'w'))
    json.dump({'type': 'Feature', 'geometry': {'type': 'LineString', 'coordinates': longl[0]}}, open(R / 'data/trails/US-4.json', 'w'))
    json.dump([{'ref': 'US-3', 'kind': 'found'}, {'ref': 'US-4', 'kind': 'found'}], open(R / 'data/trails/index.json', 'w'))
    url = 'https://gis.example.gov/arcgis/rest/services/Trails/MapServer/0'
    json.dump({'pairs': {f'US-1|{url}': {'result': 'SURE', 'record_name': 'Alpha Loop'},
                         f'US-2|{url}': {'result': 'SURE', 'record_name': 'Bravo National Recreation Trail'}},
               'layers': {url: {'geometry': 'esriGeometryPolyline', 'name_field': 'TRAIL_NAME', 'title': 'trails', 'host': 'gis.example.gov'}}},
              open(R / 'kpcdata/data/intake/external-results.json', 'w'))
    out = R / 'finds.json'
    pr = subprocess.run([sys.executable, str(HERE / '.github/scripts/kpc_finds_lines.py'), str(out)], cwd=R,
                        env=dict(os.environ, DATA='kpcdata'), capture_output=True, text=True)
    rows = json.load(open(out)) if out.exists() else []
    by = {x['ref']: x for x in rows}
    check(pr.returncode == 0 and (by.get('US-1') or {}).get('min_km') == 1.0 and 'min_km' not in (by.get('US-2') or {'min_km': 1}),
          f'fix 4: a found row for an area park carries min_km 1.0; a trail park does not ({pr.stderr.strip()[-160:]})')
    check((by.get('US-3') or {}).get('drop') is True and 'US-4' not in by and 'ft' in (by.get('US-3') or {}).get('why', ''),
          'fix 4: a saved found line under 1 km on an area park is handed back to be taken off (feet in the reason); a longer one is left')
check('too_short_for_area(x, L)' in UST and "if x.get('drop'):" in UST and "== 'found' and os.path.exists(_f)" in UST,
      'fix 4: the trail bot does not write a too-short line and takes off only a handed-back found line')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
