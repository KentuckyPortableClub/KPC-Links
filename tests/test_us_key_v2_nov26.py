#!/usr/bin/env python3
"""Regression tests for the clean v2 US key matcher (.github/scripts/kpc_us_key_v2.py), 26 Nov 2026.
One test per real bug, on tiny hand-made fixtures (never the real layer files). Then the MUTATION CHECK: every value, every
table and every rule row of .github/us-key-v2-rules.json is broken in turn, and its named test must notice.
Prints one line per test and per mutation, then ALL PASS or SOME FAILED. Run: python3.12 tests/test_us_key_v2_nov26.py"""
import contextlib, copy, gzip, io, json, math, os, re, shutil, sys, tempfile, time, traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, '.github', 'scripts'))
import kpc_us_key_v2 as V  # noqa: E402

LAT, LON = 45.0, -94.0
KX, KY = 111320.0 * math.cos(math.radians(LAT)), 110574.0
SRC = {'github': os.path.join(ROOT, '.github')}   # where Fix copies the rule table from (the mutation check points it elsewhere)


# ------------------------------------------------------------------------------------------------------------- fixtures
def ring(dx_m=0.0, dy_m=0.0, half_w=200.0, half_h=None, lat=LAT, lon=LON):
    """A delta-encoded rectangle (q=6) centred dx_m east and dy_m north of (lat, lon)."""
    half_h = half_w if half_h is None else half_h
    cx, cy = lon + dx_m / KX, lat + dy_m / KY
    pts = [(cx - half_w / KX, cy - half_h / KY), (cx + half_w / KX, cy - half_h / KY), (cx + half_w / KX, cy + half_h / KY),
           (cx - half_w / KX, cy + half_h / KY), (cx - half_w / KX, cy - half_h / KY)]
    ints = [(round(x * 1e6), round(y * 1e6)) for x, y in pts]
    out = [ints[0][0], ints[0][1]]
    for (x0, y0), (x1, y1) in zip(ints, ints[1:]): out += [x1 - x0, y1 - y0]
    return out


def poly(pts_m, lat=LAT, lon=LON):
    """A delta-encoded ring (q=6) through points given in metres east / north of (lat, lon)."""
    ints = [(round((lon + x / KX) * 1e6), round((lat + y / KY) * 1e6)) for x, y in list(pts_m) + [pts_m[0]]]
    out = [ints[0][0], ints[0][1]]
    for (x0, y0), (x1, y1) in zip(ints, ints[1:]): out += [x1 - x0, y1 - y0]
    return out


def rec(layer, key, name, rg=None, **attrs):
    return {'key': key, 'layer': layer, 'record_id': re.sub(r'^[a-z]+', '', key) or key, 'record_name': name,
            'attributes': attrs, 'q': 6, 'rings': [rg if rg is not None else ring()]}


def path(pts_m, lat=LAT, lon=LON):
    """A delta-encoded open line (q=6) through points given in metres east / north of (lat, lon)."""
    ints = [(round((lon + x / KX) * 1e6), round((lat + y / KY) * 1e6)) for x, y in pts_m]
    out = [ints[0][0], ints[0][1]]
    for (x0, y0), (x1, y1) in zip(ints, ints[1:]): out += [x1 - x0, y1 - y0]
    return out


def lrec(layer, key, name, pts=((-3000, 0), (3000, 0)), **attrs):
    """A LINE record in the agreed format: paths, shape 'line', no rings."""
    return {'key': key, 'layer': layer, 'record_id': re.sub(r'^[a-z]+', '', key) or key, 'record_name': name,
            'attributes': attrs, 'q': 6, 'paths': [path(pts)], 'shape': 'line'}


def park(name, kind, dx_m=0.0, dy_m=0.0, link=None, size=None):
    p = {'area': 'US-MN', 'name': name, 'type': kind, 'pin': [LAT + dy_m / KY, LON + dx_m / KX], 'page': {}}
    if link: p['link'] = dict({'usable': True, 'id_is': 'known', 'id_shared_by': 1}, **link)
    if size: p['size'] = size
    return p


class Fix:
    """A tiny repo + store + facts in a temp folder."""

    def __init__(self):
        self.d = tempfile.mkdtemp(prefix='v2test-')
        os.makedirs(os.path.join(self.d, 'repo', '.github'))
        for f in ('us-key-v2-rules.json', 'link-id-ties.json'):
            shutil.copy(os.path.join(SRC['github'], f), os.path.join(self.d, 'repo', '.github', f))
        os.makedirs(os.path.join(self.d, 'store'))
        self.parks, self.files, self.incomplete, self.lists, self.no_manifest, self.listed = {}, {}, {}, {}, {}, {}
        self.urls = {}   # {area: {layer: url}}: manifest sources (rule layer_copy)

    def p(self, path): return os.path.join(self.d, path)

    def write(self):
        for area in sorted(set(self.files) | {V.area_of(k) for k in self.lists}):
            refs = self.lists.get(V.area_label(area), [r for r, p in self.parks.items() if p['area'] == area])
            os.makedirs(self.p('repo/data/pota/saved/parks'), exist_ok=True)
            with gzip.open(self.p(f'repo/data/pota/saved/parks/{area}.json.gz'), 'wt') as f:
                json.dump({'data': [{'reference': r, 'locationDesc': self.listed.get(r, area)} for r in refs]}, f)
        for area, recs in self.files.items():
            man = {r['layer']: dict({'complete': True}, **({'url': self.urls[area][r['layer']], 'where': '1=1'}
                                                           if r['layer'] in self.urls.get(area, {}) else {})) for r in recs}
            for l in self.incomplete.get(area, []): man[l] = {'complete': False}
            for l in self.no_manifest.get(area, []): man.pop(l, None)
            with gzip.open(self.p(f'store/{area}.layer-records.json.gz'), 'wt') as f:
                json.dump({'kpcstore_layers': 1, 'area': area, 'made': '2026-11-26T11:00:00-06:00', 'manifest': man, 'records': recs}, f)
        with gzip.open(self.p('facts.json.gz'), 'wt') as f: json.dump({'parks': self.parks}, f)

    def run(self, out='out', states=('MN',), extra=(), areas=()):
        self.write()
        sel = ['--areas', *areas] if areas else ['--states', *states]
        with contextlib.redirect_stdout(io.StringIO()):
            return V.run([*sel, '--store', self.p('store'), '--facts', self.p('facts.json.gz'), '--out', self.p(out),
                          '--repo', self.p('repo'), *extra])

    def key(self, st='MN', out='out'):
        with gzip.open(self.p(f'{out}/{V.area_of(st)}.json.gz'), 'rt') as f: return json.load(f)

    def info(self, st='MN', out='out'):
        with open(self.p(f'{out}/v2-run.json')) as f: return json.load(f)['states'][st]

    def csv(self, name, out='out'):
        return open(self.p(f'{out}/{name}')).read().splitlines()

    def done(self): shutil.rmtree(self.d, ignore_errors=True)


def ids(doc, ref): return sorted(str(x[0]) for x in doc['parks'][ref]['m'])
def why(doc, ref): return doc['parks'][ref]['match']['why']
def by(doc, ref): return doc['parks'][ref]['match']['by']


RULES = V.load_rules(ROOT)


def pool_of(*recs, area='US-MN'):
    pl = V.Pool(RULES); pl.add_file(area, {'records': list(recs)}); return pl


def one(name, kind, records, dx=0.0, dy=0.0, link=None, size=None):
    f = Fix()
    try:
        f.parks['US-1'] = park(name, kind, dx_m=dx, dy_m=dy, link=link, size=size)
        f.files['US-MN'] = records
        assert f.run() == 0
        return f.key()
    finally: f.done()


# ------------------------------------------------------------------------------------------------------------- load
def test_store_gap_built():
    f = Fix()
    try:   # owner 26 Nov: an area with an incomplete layer is BUILT and flagged (exit 3), no longer refused
        f.parks['US-1'] = park('Crow Wing State Park', 'State Park')
        f.files['US-MN'] = [rec('sgmnd', 'sgmnd1', 'Crow Wing')]
        f.incomplete['US-MN'] = ['sgmnd']
        assert f.run() == 3 and ids(f.key(), 'US-1') == ['sgmnd1'] and f.info()['gaps'] == ['sgmnd']
        assert f.key()['gaps'] == ['sgmnd'] and f.key()['tool'].endswith(' (store gap)') and f.info()['not_built'] is None
        f.incomplete = {}
        f.no_manifest['US-MN'] = ['sgmnd']                     # records, but no manifest row: not complete either
        assert f.run() == 3 and f.key()['gaps'] == ['sgmnd']
        f.no_manifest = {}
        f.incomplete = {'US-WI': ['wsrc']}
        f.files['US-WI'] = [rec('wsrc', 'wsrc1', 'Other River', ring(9000, 9000))]
        assert f.run() == 0 and ids(f.key(), 'US-1') == ['sgmnd1']   # a neighbour's gap does not stop the state
    finally: f.done()


def test_drop_layer_never_matched():
    f = Fix()
    try:
        f.parks['US-1'] = park('Foot Hills State Forest', 'State Forest')
        f.files['US-MN'] = [rec('sgmnb', 'sgmnb1', 'Foot Hills', sft='SFT00019')]
        assert f.run() == 0 and f.key()['parks']['US-1']['m'] == []
        assert f.info()['records_dropped'].get('drop_layer sgmnb') == 1
    finally: f.done()
    # US-4491 Superior NF: the Forest Service's administrative line (3.9 M acres) is not the forest's own land (2.1 M)
    d = one('Superior National Forest', 'National Forest', [rec('sgnvg', 'sgnvg42', 'Superior National Forest'),
                                                           rec('PAD-US', '3082', 'Superior National Forest')])
    assert ids(d, 'US-1') == ['3082']


def test_record_without_shape_dropped():
    pl = pool_of(dict(rec('sgmnd', 'sgmnd1', 'Crow Wing'), rings=[]))
    assert pl.recs == [] and pl.dropped == {'no_shape': 1}


def test_repeated_row_key_dropped():
    pl = pool_of(rec('sgiaa', 'sgiaa247', 'BARBER CREEK WILDLIFE AREA'), rec('sgiaa', 'sgiaa247', 'IHAP JONES 1'),
                 rec('sgiaa', 'sgiaa248', 'COLFAX WILDLIFE AREA'))
    assert [r['key'] for r in pl.recs] == ['sgiaa248'] and pl.dropped == {'key_not_unique sgiaa': 2}


def test_neighbour_copy_not_loaded_twice():
    f = Fix()
    try:
        r = rec('fws', 'fws10', 'X', CMPXNAME='', ORGNAME='AGASSIZ NATIONAL WILDLIFE REFUGE', SUM_GISACRES=100, INTTYPE1='O')
        f.parks['US-1'] = park('Agassiz National Wildlife Refuge', 'National Wildlife Refuge')
        f.files['US-MN'] = [r]; f.files['US-WI'] = [copy.deepcopy(r)]
        assert f.run() == 0 and [x[0] for x in f.key()['parks']['US-1']['m']] == ['fws10']
        assert f.info()['records_dropped'] == {'same_record_in_two_files': 1}
    finally: f.done()


def test_agency_spelling_zero_led():
    rs = [{'key': 'sgmnb6', 'attributes': {'sft': 'SFT00006'}}, {'key': 'sgmnb7', 'attributes': {'sft': 'SFT00019'}}]
    sp = V.spell_layer(rs, 'sgmnb', RULES)
    assert sp == {'sgmnb6': 'sgmnb06', 'sgmnb7': 'sgmnb019'} and sp['sgmnb6'] != 'sgmnb6'
    two = [{'key': 'sgmnd1', 'attributes': {'pgrm_project': 'SPK00139'}}, {'key': 'sgmnd2', 'attributes': {'PGRM_PROJECT': 'SRA00304'}}]
    assert V.spell_layer(two, 'sgmnd', RULES) == {}   # two letter prefixes: the file's own keys


def test_acres_square_feet_converted():
    r = pool_of(rec('sgmnd', 'sgmnd1', 'Crow Wing', ring(half_w=200), GIS_ACRES=40 * 43560.0)).recs[0]
    assert abs(V.agency_acres(r, RULES) - 40.0) < 0.1
    r2 = pool_of(rec('sgmne', 'sgmne1', 'X', ring(half_w=200), su_acres=12.5)).recs[0]
    assert V.agency_acres(r2, RULES) == 12.5 and V.rec_acres(r2, RULES) == 12.5      # the first field with 'acre' in its name
    r3 = pool_of(rec('sgnyb', 'sgnyb1', 'X', ring(half_w=200))).recs[0]
    assert V.agency_acres(r3, RULES) is None and abs(V.rec_acres(r3, RULES) - 39.5) < 1   # measured: 400 m square
    r4 = pool_of(rec('fws', 'fws1', 'X', ring(half_w=200), SUM_DOCACRES=30, GIS_Acres=31)).recs[0]
    assert V.agency_acres(r4, RULES) == 31                                            # acre_fields before the fallback


# ------------------------------------------------------------------------------------------------------------- step 2
def mn_valley(f, extra=0, acres=60):
    f.parks['US-7145'] = park('Minnesota Valley State Recreation Area', 'State Recreation Area',
                              link={'id_kind': 'MN DNR unit id', 'id_value': 'SRA00304'})
    f.files['US-MN'] = [rec('sgmne', f'sgmne{n}', 'MINNESOTA VALLEY', ring(n * 500), su_id=340000 + n, mgtprgprj='SRA00304  ',
                            mgtprjname='MINNESOTA VALLEY', mgtprgname='STATE RECREATION AREA', su_acres=acres) for n in range(1, 4 + extra)]


def test_id_ties_minnesota_valley():
    f = Fix()
    try:
        mn_valley(f)
        assert f.run() == 0
        d = f.key()
        assert ids(d, 'US-7145') == ['sgmne0340001', 'sgmne0340002', 'sgmne0340003'] and by(d, 'US-7145') == 'id'
        assert d['parks']['US-7145']['match']['step'] == 2 and d['parks']['US-7145']['ac'] == 180
    finally: f.done()
    # the PAD-US Loc_Nm tie is for Park Service records only (non-NPS records use 4-letter Loc_Nm such as BACH)
    d = one('Bach Hill National Historic Site', 'National Historic Site',
            [rec('PAD-US', '41', 'Bach Hill Wildlife Area', Loc_Nm='BACH', Mang_Name='FWS')],
            link={'id_kind': 'NPS unit code', 'id_value': 'BACH'})
    assert by(d, 'US-1') != 'id'
    d = one('Bach Hill National Historic Site', 'National Historic Site', [rec('PAD-US', '41', 'Bach Hill Site', Loc_Nm='BACH', Mang_Name='NPS')],
            link={'id_kind': 'NPS unit code', 'id_value': 'BACH'})
    assert by(d, 'US-1') == 'id'


def test_shared_id_goes_to_name_step():
    f = Fix()
    try:
        lk = {'id_kind': 'MN DNR unit id', 'id_value': 'SPK00139'}
        f.parks['US-2477'] = park('Crow Wing State Park', 'State Park', link=lk)
        f.parks['US-4792'] = park('Other Place State Park', 'State Park', dx_m=30000, link=lk)
        f.files['US-MN'] = [rec('sgmnd', 'sgmnd1', 'Crow Wing', PGRM_PROJECT='SPK00139')]
        assert f.run() == 0
        d = f.key()
        assert by(d, 'US-2477') == 'name+pin' and d['parks']['US-2477']['match']['step'] == 3 and d['parks']['US-4792']['m'] == []
    finally: f.done()


def test_id_guard_name_or_pin():
    f = Fix()
    try:   # two parks of one kind 3 km apart, their ids swapped in the facts: neither is joined by id
        u = lambda n: f'https://www.dec.ny.gov/lands/{n}.html'
        f.parks['US-1'] = park('Oak Hill State Forest', 'State Forest', link={'id_kind': 'NY DEC page number', 'id_value': '2'})
        f.parks['US-2'] = park('Elm Ridge State Forest', 'State Forest', dx_m=3000, link={'id_kind': 'NY DEC page number', 'id_value': '1'})
        f.files['US-MN'] = [rec('sgnya', 'sgnya1', 'Oak Hill State Forest', URL=u(1)), rec('sgnya', 'sgnya2', 'Elm Ridge State Forest', ring(3000), URL=u(2))]
        assert f.run() == 0
        d = f.key()
        assert by(d, 'US-1') != 'id' and by(d, 'US-2') != 'id' and ids(d, 'US-1') == ['sgnya1'] and ids(d, 'US-2') == ['sgnya2']
    finally: f.done()
    # US-5249 Pine Hill (Delaware County): its DEC id points at the Cattaraugus forest 300 km away
    d = one('Pine Hill (Delaware County) State Forest', 'State Forest',
            [rec('sgnya', 'sgnya72664', 'Pine Hill State Forest', ring(300000), URL='https://www.dec.ny.gov/lands/68174.html'),
             rec('sgnya', 'sgnya75517', 'Pine Hill State Forest', ring(), URL='https://www.dec.ny.gov/lands/102363.html')],
            link={'id_kind': 'NY DEC page number', 'id_value': '68174'})
    assert ids(d, 'US-1') == ['sgnya75517'] and by(d, 'US-1') == 'name+pin'
    # the park's own name, but 15 km off: more than near_km, so not proven by id
    d = one('Bearpen Hill State Forest', 'State Forest', [rec('sgnya', 'sgnya1', 'Bearpen Hill State Forest', ring(15000), URL='https://www.dec.ny.gov/lands/7.html')],
            link={'id_kind': 'NY DEC page number', 'id_value': '7'})
    assert d['parks']['US-1']['m'] == []
    d = one('Bearpen Hill State Forest', 'State Forest', [rec('sgnya', 'sgnya1', 'Bearpen Hill State Forest', ring(5000), URL='https://www.dec.ny.gov/lands/7.html')],
            link={'id_kind': 'NY DEC page number', 'id_value': '7'})
    assert by(d, 'US-1') == 'id'                                         # the name and 5 km: proven by id


def test_wetland_district_fee_only():
    f = Fix()
    try:
        f.parks['US-0356'] = park('Big Stone Wetland Management District', 'Wetland Management District')
        cx = 'BIG STONE WETLAND MANAGEMENT DISTRICT'
        f.files['US-MN'] = [rec('fws', 'fws1', 'A WPA', ring(), CMPXNAME=cx, INTTYPE1='O', RSL_TYPE='WPA', SUM_GISACRES=100),
                            rec('fws', 'fws2', 'B WPA', ring(8000), CMPXNAME=cx, INTTYPE1='O', RSL_TYPE='WPA', SUM_GISACRES=50),
                            rec('fws', 'fws3', 'C easement', ring(2000), CMPXNAME=cx, INTTYPE1='E', RSL_TYPE='WPA', SUM_GISACRES=500),
                            rec('fws', 'fws4', 'D refuge', ring(3000), CMPXNAME=cx, INTTYPE1='O', RSL_TYPE='NWR', SUM_GISACRES=50),
                            rec('PAD-US', '77', cx, ring(), Unit_Nm=cx, Loc_Nm=cx, GIS_Acres=9000)]
        assert f.run() == 0 and ids(f.key(), 'US-0356') == ['fws1', 'fws2']
    finally: f.done()


def test_record_with_other_park_name_refused():
    f = Fix()
    try:
        lk = {'id_kind': 'NY DEC page number', 'id_value': '8269'}
        f.parks['US-5046'] = park('Harris Hill State Forest', 'State Forest', link=lk)
        f.parks['US-5047'] = park('Hatch Creek State Forest', 'State Forest', dx_m=5000)
        url = 'https://www.dec.ny.gov/lands/8269.html'
        f.files['US-MN'] = [rec('sgnya', 'sgnya1', 'Harris Hill State Forest', ring(), URL=url),
                            rec('sgnya', 'sgnya2', 'Hatch Creek State Forest', ring(5000), URL=url),
                            rec('sgmnd', 'sgmnd9', 'Minnesota Valley', ring(20000), AREA_NAME='Minnesota Valley',
                                AREA_TYPE='State Recreation Area', LEGISLATIVE_NAME='Minnesota Valley State Recreation Area')]
        f.parks['US-7145'] = park('Minnesota Valley State Recreation Area', 'State Recreation Area', dx_m=40000)
        f.parks['US-9384'] = park('Minnesota Valley State Trail', 'State Trail', dx_m=20000)
        assert f.run() == 0
        d = f.key()
        assert ids(d, 'US-5046') == ['sgnya1'] and ids(d, 'US-5047') == ['sgnya2']
        assert d['parks']['US-9384']['m'] == []   # the SRA's land never goes to the trail by its bare name
    finally: f.done()


def test_wma_project_pieces():
    f = Fix()
    try:
        f.parks['US-12693'] = park('Swan Lake Wildlife Management Area', 'Wildlife Management Area',
                                   link={'id_kind': 'MN DNR unit id', 'id_value': 'WMA0129500'})
        mk = lambda k, u, unit, dx: rec('sgmna', k, unit, ring(dx), uniqueid=u, lam_program_project_code='WMA01295', unit_name=unit)
        f.files['US-MN'] = [mk('sgmna1', 'WMA0129500', 'Swan Lake WMA', 0), mk('sgmna2', 'WMA0129501', 'Swan Lake WMA', 3000),
                            mk('sgmna3', 'WMA0129502', 'Swan Lake WMA', 6000), mk('sgmna4', 'WMA0129503', 'Other Slough WMA', 9000)]
        assert f.run('cold', extra=['--write-locks']) == 0
        d = f.key(out='cold')
        assert ids(d, 'US-12693') == ['sgmna0129500', 'sgmna0129501', 'sgmna0129502'] and by(d, 'US-12693') == 'id'
        assert f.info(out='cold')['gate']['id_mismatch'] == 0
        assert json.load(open(f.p('cold/locks/US-MN.json')))['locks']['US-12693'][0]['count'] == 3
    finally: f.done()


def test_id_unit_pieces():
    f = Fix()
    try:   # US-5416 Michigan Hill: a second DEC record of the forest carries no page number
        u = 'https://www.dec.ny.gov/lands/37372.html'
        f.parks['US-5416'] = park('Michigan Hill State Forest', 'State Forest', link={'id_kind': 'NY DEC page number', 'id_value': '37372'})
        f.parks['US-9'] = park('Michigan Hill (B County) State Forest', 'State Forest', dx_m=70000)
        f.files['US-MN'] = [rec('sgnya', 'sgnya1', 'Michigan Hill State Forest', URL=u),
                            rec('sgnya', 'sgnya2', 'Michigan Hill State Forest', ring(4000), URL=''),
                            rec('sgnya', 'sgnya3', 'Michigan Hill State Forest', ring(6000), URL='https://www.dec.ny.gov/lands/102358.html'),
                            rec('sgnya', 'sgnya4', 'Michigan Hill State Forest', ring(40000), URL=''),
                            rec('sgnya', 'sgnya5', 'Michigan Hill State Forest', ring(70000), URL=''),
                            rec('PAD-US', '236641', 'Michigan Hill State Forest', ring(2000))]
        assert f.run('cold', extra=['--write-locks']) == 0
        d = f.key(out='cold')
        assert ids(d, 'US-5416') == ['sgnya1', 'sgnya2']   # not another id, not 40 km, not another park's pin, not another layer
        assert [x[3] for x in d['parks']['US-5416']['m'] if x[0] == 'sgnya2'] == ['piece of id unit']
        assert json.load(open(f.p('cold/locks/US-MN.json')))['locks']['US-5416'][0]['count'] == 2 and f.info(out='cold')['gate']['ok']
    finally: f.done()
    # US-0673 Saint Croix: a PAD-US record of the same name held by a city, a private owner or the state fails the tie's
    # where-filter (Mang_Name NPS), so it is not a piece of the Park Service unit
    d = one('Saint Croix National Scenic Riverway', 'National Scenic Riverway',
            [rec('PAD-US', '3561', 'St. Croix National Scenic Riverway', Loc_Nm='SACN', Mang_Name='NPS'),
             rec('PAD-US', '69293', 'St. Croix National Scenic Riverway', ring(600), Loc_Nm='St. Croix National Scenic Riverway', Mang_Name='PVT'),
             rec('PAD-US', '72037', 'St. Croix National Scenic Riverway', ring(1000), Loc_Nm='', Mang_Name='SDNR')],
            link={'id_kind': 'NPS unit code', 'id_value': 'SACN'})
    assert ids(d, 'US-1') == ['3561'] and by(d, 'US-1') == 'id'


def test_far_pin_listed_states():
    cajo = {'id_kind': 'NPS unit code', 'id_value': 'CAJO'}
    nm = 'Captain John Smith Chesapeake National Historic Trail'
    def case(listed, rec_name=nm, line=False):
        f = Fix()
        try:
            f.parks['US-4567'] = park(nm, 'National Historic Trail', link=cajo)
            if listed: f.listed['US-4567'] = listed
            r = (lrec('PAD-US', '3601', rec_name, ((390000, 0), (420000, 0)), Loc_Nm='CAJO', Mang_Name='NPS') if line else
                 rec('PAD-US', '3601', rec_name, ring(400000), Loc_Nm='CAJO', Mang_Name='NPS'))
            f.files['US-MN'] = [r]
            assert f.run() == 0
            return f.key()['parks']['US-4567']
        finally: f.done()
    k = case('US-DC,US-DE,US-MD,US-MN,US-PA,US-VA')       # US-4567: pin in DC, its land 400 km off: listed in 6 states
    assert [x[0] for x in k['m']] == ['3601'] and k['match']['by'] == 'id'
    assert k['match']['evidence']['far_pin'] is True and k['match']['evidence']['listed_in'][:2] == ['US-DC', 'US-DE']
    k = case('US-DC,US-MN', line=True)                     # a multi-state trail's far LINE joins by id too
    assert [x[0] for x in k['m']] == ['3601'] and k.get('line') is True and k['m'][0][2] == 0
    assert case('US-MN')['m'] == []                        # one state: never (a far id with the very name is still refused)
    assert case('US-DC,US-MN', rec_name='Chesapeake Bay Gateways')['m'] == []   # several states, but not the park's full name
    # US-5249 Pine Hill stays refused: a one-state park (see test_id_guard_name_or_pin)


def test_line_load():
    pl = pool_of(lrec('sgxx', 'sgxx1', 'Root River'), lrec('sgxx', 'sgxx2', 'Elm'))
    assert len(pl.recs) == 2 and pl.dropped == {} and pl.recs[0]['line'] and V.rec_box(pl.recs[0])[2] > V.rec_box(pl.recs[0])[0]
    assert V.has_shape({'paths': [[1, 2, 3, 4]], 'shape': 'line'}) and not V.has_shape({'paths': [[1, 2, 3, 4]]})
    f = Fix()
    try:   # a line with an acres field: 0 acres in m, ac 0; the size never proves it
        f.parks['US-1'] = park('Root River State Trail', 'State Trail', size={'acres': 50, 'witness': 'agency_document'})
        f.parks['US-2'] = park('Douglas State Trail', 'State Trail', dy_m=5000, size={'acres': 50, 'witness': 'agency_document'})
        f.files['US-MN'] = [lrec('sgxx', 'sgxx1', 'Root River', GIS_ACRES=50),
                            lrec('sgxx', 'sgxx2', 'Douglas', ((-3000, 3000), (3000, 3000)), GIS_ACRES=50)]
        assert f.run() == 0
        d = f.key()
        assert d['parks']['US-1']['m'] == [['sgxx1', 'Root River', 0, 'name+pin']] and d['parks']['US-1']['ac'] == 0
        assert d['parks']['US-2']['m'] == []                       # 2 km off the line: its acres field proves nothing
        assert f.info()['lines'] == {'sgxx': 2}
    finally: f.done()


def test_line_pin_distance():
    def case(dy, kind='State Trail', name='Root River State Trail'):
        f = Fix()
        try:
            f.parks['US-1'] = park(name, kind, dy_m=dy)
            f.files['US-MN'] = [lrec('sgxx', 'sgxx1', 'Root River')]
            assert f.run() == 0
            return f.key(), f.csv('v2-proof.csv')
        finally: f.done()
    d, proof = case(20)                                        # 20 m off the line: within 100 ft
    k = d['parks']['US-1']
    assert k['m'] == [['sgxx1', 'Root River', 0, 'name+pin']] and k.get('line') is True and proof[1].split(',')[-1] == 'line'
    d, _ = case(60)                                            # 60 m off: pin only
    assert d['parks']['US-1']['m'] == [] and why(d, 'US-1') == 'name_but_no_pin_or_size_proof'
    # two same-named lines 300 km apart, no unit value: never one trail
    d = one('Root River State Trail', 'State Trail', [lrec('sgxx', 'sgxx1', 'Root River'),
                                                      lrec('sgxx', 'sgxx2', 'Root River', ((300000, 0), (303000, 0)))])
    assert ids(d, 'US-1') == ['sgxx1']
    # another same-named park's pin within 100 ft of the line: refused for both
    f = Fix()
    try:
        f.parks['US-1'] = park('Root River State Trail', 'State Trail')
        f.parks['US-2'] = park('Root River (Fillmore County) State Trail', 'State Trail', dx_m=2000, dy_m=10)
        f.files['US-MN'] = [lrec('sgxx', 'sgxx1', 'Root River')]
        assert f.run() == 0 and f.key()['parks']['US-1']['m'] == [] == f.key()['parks']['US-2']['m']
    finally: f.done()


def test_line_name_needs_trail_kind():
    line = [lrec('sgxx', 'sgxx1', 'Glacial Lakes')]
    assert one('Glacial Lakes State Park', 'State Park', line)['parks']['US-1']['m'] == []     # named like the trail: no
    assert ids(one('Glacial Lakes State Trail', 'State Trail', line), 'US-1') == ['sgxx1']
    d = one('Glacial Lakes State Park', 'State Park', [lrec('sgmne', 'sgmne1', 'Glacial Lakes', mgtprgprj='SPK00170')],
            link={'id_kind': 'MN DNR unit id', 'id_value': 'SPK00170'})
    assert ids(d, 'US-1') == ['sgmne1'] and by(d, 'US-1') == 'id'                              # by id, any park


def test_key_text_sha256():
    f = Fix()
    try:
        f.parks['US-1'] = park('Crow Wing State Park', 'State Park')
        f.files['US-MN'] = [rec('sgmnd', 'sgmnd1', 'Crow Wing')]
        assert f.run() == 0
        with gzip.open(f.p('out/US-MN.json.gz'), 'rb') as g: text = g.read()
        import hashlib
        assert f.info()['key_text_sha256'] == hashlib.sha256(text).hexdigest()
    finally: f.done()


# ------------------------------------------------------------------------------------------------------------- areas, Canada
def ca_park(name, kind, area='CA-QC', **k):
    return dict(park(name, kind, **k), area=area)


def ca_one(name, kind, records, area='CA-QC', link=None, dx=0.0):
    f = Fix()
    try:
        f.parks['CA-1'] = ca_park(name, kind, area, link=link, dx_m=dx)
        f.files[area] = records
        assert f.run(areas=[area]) == 0
        return f.key(area)
    finally: f.done()


def test_ca_area_and_neighbours():
    assert V.area_of('mn') == 'US-MN' and V.area_of('CA-ON') == 'CA-ON' and V.area_label('US-MN') == 'MN' and V.area_label('CA-QC') == 'CA-QC'
    assert V.area_neighbours('CA-PE', RULES) == ['CA-NB', 'CA-NS'] and 'US-WI' in V.area_neighbours('US-MN', RULES)
    f = Fix()
    try:   # an NB park whose land is in the Québec file (a neighbour): found, and the files are named by area
        f.parks['CA-1'] = ca_park('Mount Carleton Provincial Park', 'Provincial Park', 'CA-NB')
        f.files['CA-NB'] = [rec('CPCAD', '9', 'Other Place', ring(50000))]
        f.files['CA-QC'] = [rec('CPCAD', '7', 'Mount Carleton Provincial Park')]
        assert f.run(areas=['CA-NB']) == 0 and os.path.exists(f.p('out/CA-NB.json.gz'))
        assert ids(f.key('CA-NB'), 'CA-1') == ['7'] and f.key('CA-NB')['st'] == 'CA-NB'
        run = json.load(open(f.p('out/v2-run.json')))
        assert run['areas']['CA-NB'] is not None and 'CA-NB' in run['states'] and f.csv('v2-proof.csv')[1].split(',')[1] == 'CA-NB'
    finally: f.done()
    # a page address in a record's web field is the park's id (Manitoba Parks URL, measured)
    d = ca_one('Hecla / Grindstone Provincial Park', 'Provincial Park',
               [rec('Manitoba Par', 'Manitoba Par:1', 'Hecla/Grindstone Provincial Park', ring(3000),
                    URL='https://www.gov.mb.ca/sd/parks/park-maps-and-locations/central/hecla.html')], area='CA-MB',
               link={'id_kind': 'page address', 'id_value': 'GOV.MB.CA/SD/PARKS/PARK-MAPS-AND-LOCATIONS/CENTRAL/HECLA.HTML'})
    assert ids(d, 'CA-1') == ['Manitoba Par:1'] and by(d, 'CA-1') == 'id'


def test_layer_copy_dropped():
    f = Fix()
    try:   # CA-QC: 'Québec prote' and 'Qu_bec prote' are one layer read twice: one copy is kept
        f.parks['CA-1'] = ca_park('Cap Tourmente National Wildlife Area', 'National Wildlife Area')
        f.files['CA-QC'] = [rec('Qu_bec prote', 'Qu_bec prote:1', 'Cap Tourmente National Wildlife Area'),
                            rec('Québec prote', 'Québec prote:1', 'Cap Tourmente National Wildlife Area')]
        u = 'https://example/Aires_protegees/MapServer/23/query'
        f.urls['CA-QC'] = {'Qu_bec prote': u, 'Québec prote': u}
        assert f.run(areas=['CA-QC']) == 0
        assert ids(f.key('CA-QC'), 'CA-1') == ['Qu_bec prote:1'] and f.info('CA-QC')['records_dropped'] == {'layer_copy Québec prote': 1}
    finally: f.done()


def test_bilingual_name():
    en, fr = 'Cap Tourmente National Wildlife Area', 'Réserve nationale de faune du Cap-Tourmente'
    both = rec('CPCAD', '22109', en, ring(9000), NAME_E=en, NAME_F=fr)      # carries both names, 9 km off the pin
    reg = rec('Qu_bec prote', 'Qu_bec prote:2872', '', TOPONYME=fr)        # the French name only, under the pin
    d = ca_one(en, 'National Wildlife Area', [both, reg])
    assert ids(d, 'CA-1') == ['Qu_bec prote:2872'] and by(d, 'CA-1') == 'name+pin'
    assert d['parks']['CA-1']['m'][0][1] == fr                              # the record's own name, never ''
    # no record carrying both names: only the kind-word rule (ca_kind_words, longer or shorter name) can still see it
    assert by(ca_one(en, 'National Wildlife Area', [reg]), 'CA-1') == 'longer or shorter name+pin'
    reg2 = rec('Qu_bec prote', 'Qu_bec prote:9', '', TOPONYME='Réserve nationale de faune du Lac-Saint-François')
    one_name = rec('CPCAD', '22109', en, ring(9000), NAME_E=en, NAME_F='None')
    assert ca_one(en, 'National Wildlife Area', [one_name, reg2])['parks']['CA-1']['m'] == []   # never a guess


def test_ca_kind_words():
    r = [rec('CPCAD', '22022', 'Forillon National Park Of Canada')]
    d = ca_one('Forillon National Park', 'National Park', r)
    assert ids(d, 'CA-1') == ['22022'] and by(d, 'CA-1') == 'longer or shorter name+pin'
    assert one('Forillon National Park', 'National Park', r)['parks']['US-1']['m'] == []   # US areas: not their words
    # a longer-or-shorter name never joins a place of another kind (CA-0852 Basin Head)
    d = ca_one('Basin Head Provincial Park', 'Provincial Park', [rec('CPCAD', '21882', 'Basin Head Marine Protected Area')], area='CA-PE')
    assert d['parks']['CA-1']['m'] == []


def test_stream_read_same():
    d = tempfile.mkdtemp(prefix='v2stream-')
    try:
        recs = [rec('sgmnd', f'sgmnd{i}', f'Park {i}', ring(i * 1000), AREA_NAME=f'Park {i}', NOT_USED='x' * 50) for i in range(400)]
        recs.append(dict(rec('PAD-US', '9', 'Lake', ring()), rings=json.dumps([ring()])))      # rings written as text
        doc = {'kpcstore_layers': 1, 'area': 'US-MN', 'made': 'm', 'manifest': {'sgmnd': {'complete': True}}, 'records': recs,
               'after': 'a key after the records'}
        p = os.path.join(d, 'x.json.gz')
        with gzip.open(p, 'wt') as f: json.dump(doc, f)
        got = V.read_layer_file(p, RULES)
        assert got['made'] == 'm' and got['after'] == 'a key after the records' and len(got['records']) == 401
        a, b = got['records'][3], recs[3]
        assert a['key'] == b['key'] and 'NOT_USED' not in a['attributes'] and a['attributes']['AREA_NAME'] == 'Park 3'
        assert V.decode_rings(a['rings'], a['q']) == V.decode_rings(b['rings'], b['q'])
        assert V.decode_rings(got['records'][-1]['rings'], 6) == V.decode_rings([ring()], 6)
    finally: shutil.rmtree(d, ignore_errors=True)


# ------------------------------------------------------------------------------------------------------------- step 3
def test_exact_name_and_kind_word():
    d = one('Crow Wing State Park', 'State Park', [rec('sgmnd', 'sgmnd1', 'Crow Wing')])
    assert ids(d, 'US-1') == ['sgmnd1'] and by(d, 'US-1') == 'name+pin'
    d = one('Itasca State Park', 'State Park', [rec('sgnyb', 'sgnyb1', 'Itasca SP')])
    assert ids(d, 'US-1') == ['sgnyb1'] and by(d, 'US-1') == 'name+pin'   # 'SP' written out is the exact name
    assert V.full('The Saddles  State-Forest', RULES) == 'saddles state forest'
    assert V.generic('Wildlife Management Area', RULES) and V.generic('Unit IV', RULES) and not V.generic('Crow Wing', RULES)


def test_possessive_second_try():
    assert V.full_ps("DEVIL'S TRACK", RULES) == V.full('Devils Track', RULES) != V.full("DEVIL'S TRACK", RULES)
    d = one("Knox's Headquarters State Historic Site", 'State Historic Site', [rec('PAD-US', '237417', 'Knox Headquarters State Historic Site')])
    assert ids(d, 'US-1') == ['237417']                                   # first try: single letters set aside (US-10048)
    d = one("Knox's Headquarters State Historic Site", 'State Historic Site', [rec('sgnyb', 'sgnyb1', 'Knoxs Headquarters State Historic Site')])
    assert ids(d, 'US-1') == ['sgnyb1']                                   # second try: the possessive as one word
    d = one("Knox's", '', [rec('sgnyb', 'sgnyb2', 'Knox')])
    assert d['parks']['US-1']['m'] == []                                  # one real word: never
    d = one("Knox's Headquarters State Historic Site", 'State Historic Site', [rec('PAD-US', '237417', 'Knox Headquarters State Historic Site')], dx=3000)
    assert d['parks']['US-1']['m'] == []                                  # still needs its second proof


def test_wildlife_and_fish_refuge():
    d = one('Upper Mississippi River National Wildlife Refuge', 'National Wildlife Refuge',
            [rec('sgmng', 'sgmng1009', 'UPPER MISSISSIPPI RIVER NATIONAL WILDLIFE AND FISH REFUGE')])
    assert ids(d, 'US-1') == ['sgmng1009'] and by(d, 'US-1') == 'name+pin'
    d = one('Upper Mississippi River National Wildlife Refuge', 'National Wildlife Refuge',
            [rec('fws', 'fws7', 'N/A WPA, Upper Mississippi Tract', ORGNAME='UPPER MISSISSIPPI RIVER NATIONAL WILDLIFE AND FISH REFUGE', INTTYPE1='O')])
    assert ids(d, 'US-1') == ['fws7']                                     # found by its second name field (ORGNAME)


def test_name_alone_never_joins():
    # US-4236 Upper Mississippi: the name fits, the pin is 350 m outside the outline, no size proves it: pin only
    d = one('Upper Mississippi River National Wildlife Refuge', 'National Wildlife Refuge',
            [rec('sgmng', 'sgmng1009', 'UPPER MISSISSIPPI RIVER NATIONAL WILDLIFE AND FISH REFUGE', ring(half_w=200))], dx=550)
    assert d['parks']['US-1']['m'] == [] and why(d, 'US-1') == 'name_but_no_pin_or_size_proof'
    d = one('Lost Lake State Forest', 'State Forest', [rec('sgmnf', 'sgmnf1', 'Lost Lake State Forest')], dx=5000)
    assert d['parks']['US-1']['m'] == []


def test_pin_within_100_m():
    d = one('Crow Wing State Park', 'State Park', [rec('sgmnd', 'sgmnd1', 'Crow Wing', ring(half_w=200))], dx=260)
    assert ids(d, 'US-1') == ['sgmnd1'] and d['parks']['US-1']['match']['evidence']['proofs'][0]['pin_m'] == 60
    d = one('Crow Wing State Park', 'State Park', [rec('sgmnd', 'sgmnd1', 'Crow Wing', ring(half_w=200))], dx=350)
    assert d['parks']['US-1']['m'] == []
    d = one('Crow Wing State Park', 'State Park', [rec('sgmnd', 'sgmnd1', 'Crow Wing', ring(half_w=200))], dx=210)
    assert ids(d, 'US-1') == ['sgmnd1']                                   # 10 m out


def test_thin_strip_vs_small_square():
    sq = V.decode_rings([ring(half_w=168.5)], 6)                         # a true 28-acre square
    strip = V.decode_rings([ring(half_w=1500, half_h=12.5)], 6)          # a 25 m strip, 3 km long
    assert abs(V.acres_of(sq) - 28) < 0.5 and not V.too_thin(sq, RULES) and V.too_thin(strip, RULES)
    d = one('Crow Wing State Park', 'State Park', [rec('sgmnd', 'sgmnd1', 'Crow Wing', ring(half_w=168.5))], dx=218)
    assert ids(d, 'US-1') == ['sgmnd1']                                   # 50 m outside the small square: measurable
    d = one('Elm Nook State Park', 'State Park', [rec('sgmnd', 'sgmnd1', 'Elm Nook', ring(half_w=85))], dx=175)
    assert ids(d, 'US-1') == ['sgmnd1']                                   # a 7-acre square, 90 m out: not a strip
    d = one('Luce Line State Trail', 'State Trail', [rec('sgmnf', 'sgmnf1', 'Luce Line', ring(half_w=1500, half_h=12.5))], dy=62.5)
    assert d['parks']['US-1']['m'] == []                                  # 50 m beside a 25 m strip: more than its own width
    d = one('Luce Line State Trail', 'State Trail', [rec('sgmnf', 'sgmnf1', 'Luce Line', ring(half_w=1500, half_h=12.5))], dy=22.5)
    assert ids(d, 'US-1') == ['sgmnf1']                                   # 10 m beside it (US-9102 Swallow Bluffs: 4 m from 55 m)


def test_name_and_size_join():
    sz = {'acres': 1000.0, 'witness': 'agency_document'}
    big = lambda ac: [rec('PAD-US', '3040', 'Chippewa National Forest', ring(half_w=1300), GIS_Acres=ac)]
    d = one('Chippewa National Forest', 'National Forest', big(1050), dx=2000, size=sz)
    assert ids(d, 'US-1') == ['3040'] and by(d, 'US-1') == 'name+size'
    assert one('Chippewa National Forest', 'National Forest', big(1200), dx=2000, size=sz)['parks']['US-1']['m'] == []
    assert one('Chippewa National Forest', 'National Forest', big(1050), dx=2000, size={'acres': 1000.0, 'witness': 'same_record'})['parks']['US-1']['m'] == []
    f = Fix()
    try:   # an own-page clean total counts as an agency document
        f.parks['US-1'] = park('Chippewa National Forest', 'National Forest', dx_m=2000)
        f.parks['US-1']['page'] = {'own_page': 'own', 'sizes': [{'acres': 1000.0, 'total': True, 'clean': True}]}
        f.parks['US-1']['link'] = {'page_kind': 'own page', 'site': 'agency (known)'}
        f.files['US-MN'] = big(1050)
        assert f.run() == 0 and by(f.key(), 'US-1') == 'name+size'
    finally: f.done()
    f = Fix()
    try:   # two parks of the state share the name: no size can pick between them
        f.parks['US-1'] = park('Chippewa National Forest', 'National Forest', dx_m=2000, size=sz)
        f.parks['US-2'] = park('Chippewa National Forest', 'National Forest', dx_m=90000)
        f.files['US-MN'] = big(1050)
        assert f.run() == 0 and f.key()['parks']['US-1']['m'] == []
    finally: f.done()


def test_name_two_sources():
    rs = [rec('PAD-US', '237514', 'Harriman State Park', ring(half_w=900), GIS_Acres=500),
          rec('sgnyb', 'sgnyb486', 'Harriman', ring(half_w=880), Acres=505)]
    d = one('Harriman State Park', 'State Park', rs, dx=1500)
    assert ids(d, 'US-1') == ['237514', 'sgnyb486'] and by(d, 'US-1') == 'name+two_sources'
    rs = [rec('sgnyb', 'sgnyb1', 'Harriman', ring(half_w=900), Acres=500), rec('sgnyb', 'sgnyb2', 'Harriman', ring(half_w=880), Acres=505)]
    assert one('Harriman State Park', 'State Park', rs, dx=1500)['parks']['US-1']['m'] == []   # one layer is one source
    rs = [rec('PAD-US', '237514', 'Harriman State Park', ring(half_w=900), GIS_Acres=500),
          rec('sgnyb', 'sgnyb486', 'Harriman', ring(half_w=880), Acres=575)]
    assert one('Harriman State Park', 'State Park', rs, dx=1500)['parks']['US-1']['m'] == []   # sizes 15% apart: no
    rs = [rec('PAD-US', '237514', 'Harriman State Park', ring(half_w=200), GIS_Acres=30),
          rec('sgnyb', 'sgnyb486', 'Harriman', ring(1100, half_w=200), Acres=30)]
    assert one('Harriman State Park', 'State Park', rs, dx=550)['parks']['US-1']['m'] == []    # boxes apart: no


def test_name_and_size_any_layer():
    sz = {'acres': 2_092_768.0, 'witness': 'agency_document'}
    rs = [rec('PAD-US', '3040', 'Superior National Forest', ring(half_w=47000), GIS_Acres=2_093_610, FeatClass='Fee'),
          rec('sgmng', 'sgmng1', 'Superior National Forest', ring(half_w=50000))]
    d = one('Superior National Forest', 'National Forest', rs, dx=52000, size=sz)
    assert ids(d, 'US-1') == ['3040'] and by(d, 'US-1') == 'name+size'   # PAD-US's own total proves it, not the largest layer
    d = one('Superior National Forest', 'National Forest', rs, size=sz)
    e = d['parks']['US-1']['match']['evidence']
    assert set(e['acres_by_layer']) == {'PAD-US', 'sgmng'} and d['parks']['US-1']['ac'] == max(e['acres_by_layer'].values())


def test_water_only_refused():
    d = one('Cedar Lake State Park', 'State Park', [rec('PAD-US', '5', 'Cedar Lake')])
    assert d['parks']['US-1']['m'] == [] and why(d, 'US-1') == 'water_only'
    assert ids(one('Cedar Lake State Fishing Lake', 'State Fishing Lake', [rec('PAD-US', '5', 'Cedar Lake')]), 'US-1') == ['5']
    d = one('Greenleaf Lake State Recreation Area', 'State Recreation Area',
            [rec('sgmnd', 'sgmnd51', 'Greenleaf Lake', AREA_NAME='Greenleaf Lake', AREA_TYPE='State Recreation Area')])
    assert ids(d, 'US-1') == ['sgmnd51']   # the agency files it as a State Recreation Area, not water


def test_office_refused():
    d = one('Laurentian Ranger District', 'National Forest', [rec('PAD-US', '2162', 'Laurentian Ranger District')])
    assert d['parks']['US-1']['m'] == [] and why(d, 'US-1') == 'office_only'


def test_ny_dec_wild_forest():
    d = one('Crystal Lake State Forest', 'State Forest', [rec('sgnya', 'sgnya72140', 'Crystal Lake Wild Forest')])
    assert ids(d, 'US-1') == ['sgnya72140']
    assert V.kind_swap_keys('lake wild forest', 'sgnya', RULES) == set()            # no real place word
    assert V.kind_swap_keys('oak wild forest', 'sgnya', RULES) == set()             # 'oak' has fewer than 4 letters
    assert V.kind_swap_keys('crystal lake wild forest', 'sgmnf', RULES) == set()    # NY DEC layer only


def test_name_kind_swaps():
    d = one('Canandaigua Lake State Park', 'State Park', [rec('sgnyb', 'sgnyb330', 'Canandaigua Lake Marine Park')])
    assert ids(d, 'US-1') == ['sgnyb330'] and by(d, 'US-1') == 'name+pin'
    d = one('Black Diamond State Trail', 'State Trail', [rec('sgnyb', 'sgnyb928', 'Black Diamond Trail', ring(half_w=300))])
    assert ids(d, 'US-1') == ['sgnyb928'] and by(d, 'US-1') == 'name+pin'
    assert one('Lake State Park', 'State Park', [rec('sgnyb', 'sgnyb1', 'Lake Marine Park')])['parks']['US-1']['m'] == []
    d = one('Canandaigua Lake State Park', 'State Park', [rec('sgnyb', 'sgnyb330', 'Canandaigua Lake Marine Park')], dx=3000)
    assert d['parks']['US-1']['m'] == []                                  # still needs its second proof


def test_name_compound():
    r = rec('sgscc', 'sgscc27', 'Buzzard Roost Heritage Preserve and Wildlife Management Area')
    d = one('Buzzard Roost Heritage Preserve', 'Heritage Preserve', [r])
    assert ids(d, 'US-1') == ['sgscc27'] and by(d, 'US-1') == 'name+pin'
    d = one('Buzzard Roost Wildlife Management Area', 'Wildlife Management Area', [r])
    assert ids(d, 'US-1') == ['sgscc27'] and by(d, 'US-1') == 'name+pin'
    assert one('Buzzard Roost State Park', 'State Park', [r])['parks']['US-1']['m'] == []
    f = Fix()
    try:                                                                  # the record carries another park's full name: no
        f.parks['US-1'] = park('Buzzard Roost Heritage Preserve', 'Heritage Preserve')
        f.parks['US-2'] = park('Buzzard Roost Heritage Preserve and Wildlife Management Area', 'Heritage Preserve', dx_m=4000)
        f.files['US-MN'] = [r]
        assert f.run() == 0 and f.key()['parks']['US-1']['m'] == []
    finally: f.done()


def test_page_name():
    lk = {'page_kind': 'own page', 'site': 'agency (known)', 'state_check': 'same state', 'name_match': 'strong',
          'web_name': 'keystone woods wma', 'id_kind': 'page address', 'id_value': 'DNR.STATE.MN.US/WMAS/KEYSTONE-WOODS-WMA.HTML'}
    r = rec('sgmnf', 'sgmnf5878', 'Keystone Woods WMA')
    d = one('Keystone Wildlife Management Area', 'Wildlife Management Area', [r], link=lk)
    assert ids(d, 'US-1') == ['sgmnf5878'] and by(d, 'US-1') == 'page name+pin'
    assert one('Keystone Wildlife Management Area', 'Wildlife Management Area', [r], link=dict(lk, name_match='part'))['parks']['US-1']['m'] == []
    assert one('Keystone Wildlife Management Area', 'Wildlife Management Area', [r], link=dict(lk, page_kind='list'))['parks']['US-1']['m'] == []
    assert one('Keystone Wildlife Management Area', 'Wildlife Management Area', [r], link=lk, dx=3000)['parks']['US-1']['m'] == []


def test_name_longer_or_shorter():
    nick = "Nick’s Lake Campground and Day Use State Recreation Site"
    d = one(nick, 'State Recreation Site', [rec('sgnya', 'sgnya72628', 'Nicks Lake Campground')])
    assert ids(d, 'US-1') == ['sgnya72628'] and by(d, 'US-1') == 'longer or shorter name+pin'
    d = one('Franny Reese State Park', 'State Park', [rec('PAD-US', '237501', 'Franny Reese Preserve State Park'),
                                                     rec('PAD-US', '235540', 'Franny Reese State Park', ring(600, half_w=20))])
    assert ids(d, 'US-1') == ['237501']               # the exact name proved nothing (273 m off); the longer name holds the pin
    assert one(nick, 'State Recreation Site', [rec('sgnya', 'sgnya1', 'Nicks Lake Campground', ring(3000))])['parks']['US-1']['m'] == []
    assert one('Bear Hill State Forest', 'State Forest', [rec('PAD-US', '1', 'Bear Hill State Park')])['parks']['US-1']['m'] == []
    assert one('Bear Hill State Park', 'State Park', [rec('PAD-US', '1', 'Bear Hill Lake State Park')])['parks']['US-1']['m'] == []
    d = one('Crow Wing State Park', 'State Park', [rec('sgmnd', 'sgmnd1', 'Crow Wing'), rec('PAD-US', '9', 'Crow Wing State Park Annex')])
    assert ids(d, 'US-1') == ['sgmnd1'] and by(d, 'US-1') == 'name+pin'   # tried only when the exact names proved nothing
    f = Fix()
    try:                                               # another park's full name is refused first
        f.parks['US-1'] = park('Franny Reese State Park', 'State Park')
        f.parks['US-2'] = park('Franny Reese Preserve State Park', 'State Park', dx_m=8000)
        f.files['US-MN'] = [rec('PAD-US', '237501', 'Franny Reese Preserve State Park')]
        assert f.run() == 0 and f.key()['parks']['US-1']['m'] == []
    finally: f.done()
    d = one('Adirondack State Park', 'State Park', [rec('sgnyc', 'sgnyc1', '', ring(half_w=5000))])
    assert ids(d, 'US-1') == ['sgnyc1'] and d['parks']['US-1']['m'][0][1] == 'Adirondack Park'   # the layer's fixed name
    d = one('Lock 32 Canal State Park', 'State Park', [rec('sgnyb', 'sgnyb290', 'Canal Park Lock 32')])
    assert ids(d, 'US-1') == ['sgnyb290']             # 75% of a 3-word core; the layer's kind (state parks) agrees
    d = one('Lock 32 Canal State Park', 'State Park', [rec('PAD-US', '7', 'Lock 32 Canal Visitor Grounds', Des_Tp='SP')])
    assert ids(d, 'US-1') == ['7']                    # the core begins the record's; the PAD-US designation type agrees
    d = one('Elm Woods Protected Area', '', [rec('PAD-US', '8', 'Elm Woods')])
    assert ids(d, 'US-1') == ['8']                    # 'protected' is set aside (core_drop)


def test_name_words_run_together():
    d = one('Roeliff Jansen Kill Multiple Use Area', 'Multiple Use Area', [rec('PAD-US', '237217', 'Roeliff Jansenkill Multiple Use Area')])
    assert ids(d, 'US-1') == ['237217'] and by(d, 'US-1') == 'name+pin'
    assert one('Roeliff Jansen Kill Multiple Use Area', 'Multiple Use Area', [rec('PAD-US', '1', 'Roeliff Jansenkill State Forest')])['parks']['US-1']['m'] == []
    assert one('Roeliff Jansen Kill Multiple Use Area', 'Multiple Use Area', [rec('PAD-US', '237217', 'Roeliff Jansenkill Multiple Use Area')],
               dx=3000)['parks']['US-1']['m'] == []


def test_easement_by_name_refused():
    rs = [rec('sgnyb', 'sgnyb407', 'Olana', Category='State Historic Site'), rec('sgnyb', 'sgnyb999', 'Olana', ring(300), Category='Conservation Easement')]
    assert ids(one('Olana State Historic Site', 'State Historic Site', rs), 'US-1') == ['sgnyb407']
    assert one('Elm Creek Lease Area', '', [rec('PAD-US', '5', 'Elm Creek Lease Area')])['parks']['US-1']['m'] == []   # a lease
    f = Fix()
    try:                                               # an agency-id proof is unaffected
        mn_valley(f)
        for r in f.files['US-MN']: r['attributes']['Category'] = 'Easement'
        assert f.run() == 0 and len(ids(f.key(), 'US-7145')) == 3
    finally: f.done()


def test_fws_interest_by_name():
    nm = 'MONTEZUMA NATIONAL WILDLIFE REFUGE'
    rs = [rec('fws', 'fws1', 'A', ORGNAME=nm, CMPXNAME='N/A', INTTYPE1='O', SUM_GISACRES=100),
          rec('fws', 'fws2', 'A', ring(300), ORGNAME=nm, CMPXNAME='N/A', INTTYPE1='E', SUM_GISACRES=50)]
    assert ids(one('Montezuma National Wildlife Refuge', 'National Wildlife Refuge', rs), 'US-1') == ['fws1']
    assert one('Montezuma National Wildlife Refuge', 'National Wildlife Refuge', rs[1:])['parks']['US-1']['m'] == []


def test_placeholder_not_unit():
    nm = 'TAMARAC NATIONAL WILDLIFE REFUGE'
    rs = [rec('fws', 'fws1', 'A WPA', ORGNAME=nm, CMPXNAME='N/A', INTTYPE1='O'),
          rec('fws', 'fws2', 'B WPA', ring(3000), ORGNAME=nm, CMPXNAME='N/A', INTTYPE1='O')]
    assert ids(one('Tamarac National Wildlife Refuge', 'National Wildlife Refuge', rs), 'US-1') == ['fws1']   # 'N/A' is no unit
    home = 'https://www.dec.ny.gov/'
    rs = [rec('sgnya', 'sgnya1', 'Bearpen Hill State Forest', URL=home), rec('sgnya', 'sgnya2', 'Bearpen Hill Wild Forest', ring(3000), URL=home)]
    assert ids(one('Bearpen Hill State Forest', 'State Forest', rs), 'US-1') == ['sgnya1']                   # nor the bare home page
    assert V.is_placeholder('N/A', RULES) and V.is_placeholder(home, RULES) and not V.is_placeholder(home + 'lands/8.html', RULES)


def test_unit_pieces_taken():
    u = lambda n: f'https://www.dec.ny.gov/lands/{n}.html'
    rs = [rec('sgnya', 'sgnya1', 'Bearpen Hill State Forest', URL=u(1)), rec('sgnya', 'sgnya2', 'Bearpen Hill State Forest', ring(3000), URL=u(2)),
          rec('sgnya', 'sgnya3', 'Bearpen Hill Wild Forest', ring(4000), URL=u(1))]
    assert ids(one('Bearpen Hill State Forest', 'State Forest', rs), 'US-1') == ['sgnya1', 'sgnya3']   # one DEC page is one unit


def test_far_pieces_not_joined():
    rs = [rec('sgnyb', 'sgnyb1', 'Oak Hill'), rec('sgnyb', 'sgnyb2', 'Oak Hill', ring(6000)), rec('sgnyb', 'sgnyb3', 'Oak Hill', ring(15000)),
          rec('sgnyb', 'sgnyb4', 'Oak Hill', ring(60000))]
    assert ids(one('Oak Hill State Park', 'State Park', rs), 'US-1') == ['sgnyb1', 'sgnyb2', 'sgnyb3']   # a chain, never 60 km


def test_unit_at_any_distance():
    # US-0373 Windom WMD: fee tracts 80 km apart share the district (CMPXNAME): all are the district; its easement never is
    nm = 'WINDOM WETLAND MANAGEMENT DISTRICT'
    rs = [rec('fws', 'fws1', 'A WPA', ORGNAME='JACKSON COUNTY WPA', CMPXNAME=nm, INTTYPE1='O', RSL_TYPE='WPA', LIT='WJC'),
          rec('fws', 'fws2', 'B WPA', ring(80000), ORGNAME='MURRAY COUNTY WPA', CMPXNAME=nm, INTTYPE1='O', RSL_TYPE='WPA', LIT='MRY'),
          rec('fws', 'fws3', 'C WPA', ring(81000), ORGNAME='MURRAY COUNTY WPA', CMPXNAME=nm, INTTYPE1='E', RSL_TYPE='WPA', LIT='MRY')]
    assert ids(one('Windom Wetland Management District', 'Wetland Management District', rs), 'US-1') == ['fws1', 'fws2']
    # US-0367 Northern Tallgrass Prairie: no complex (N/A), so the refuge's own LIT is the unit
    nm = 'NORTHERN TALLGRASS PRAIRIE NATIONAL WILDLIFE REFUGE'
    rs = [rec('fws', 'fws1', 'A Unit', ORGNAME=nm, CMPXNAME='N/A', INTTYPE1='O', LIT='NTP'),
          rec('fws', 'fws2', 'B Unit', ring(150000), ORGNAME=nm, CMPXNAME='N/A', INTTYPE1='O', LIT='NTP'),
          rec('fws', 'fws3', 'C Unit', ring(151000), ORGNAME=nm, CMPXNAME='N/A', INTTYPE1='E', LIT='NTP')]
    assert ids(one('Northern Tallgrass Prairie National Wildlife Refuge', 'National Wildlife Refuge', rs), 'US-1') == ['fws1', 'fws2']
    # two same-named forests 300 km apart in a layer with no unit field never merge
    rs = [rec('sgnyb', 'sgnyb1', 'Lost Lake State Forest'), rec('sgnyb', 'sgnyb2', 'Lost Lake State Forest', ring(300000))]
    assert ids(one('Lost Lake State Forest', 'State Forest', rs), 'US-1') == ['sgnyb1']
    # a unit far away still takes every refusal: another park's full name
    f = Fix()
    try:
        u = 'https://www.dec.ny.gov/lands/9.html'
        f.parks['US-1'] = park('Bearpen Hill State Forest', 'State Forest')
        f.parks['US-2'] = park('Bearpen Hill Wild Forest', 'Wild Forest', dx_m=200000)
        f.files['US-MN'] = [rec('sgnya', 'sgnya1', 'Bearpen Hill State Forest', URL=u),
                            rec('sgnya', 'sgnya2', 'Bearpen Hill State Forest', ring(90000), URL=u),
                            rec('sgnya', 'sgnya3', 'Bearpen Hill Wild Forest', ring(200000), URL=u)]
        assert f.run() == 0
        assert ids(f.key(), 'US-1') == ['sgnya1', 'sgnya2']
    finally: f.done()


def test_piece_suffix():
    rs = [rec('sgnya', 'sgnya1', 'Otis Pike Pine Barrens State Forest - West'), rec('sgnya', 'sgnya2', 'Otis Pike Pine Barrens State Forest - East', ring(3000)),
          rec('sgnyb', 'sgnyb2', 'Otis Pike Pine Barrens State Forest - East', ring(3000)),
          rec('sgnya', 'sgnya3', 'Otis Pike Pine Barrens State Forest - North', ring(60000))]
    assert ids(one('Otis Pike Pine Barrens State Forest', 'State Forest', rs), 'US-1') == ['sgnya1', 'sgnya2']
    assert V.piece_base('x state forest unit 2', RULES) == 'x state forest'


def test_two_parks_one_record_two_names():
    f = Fix()
    try:
        f.parks['US-1'] = park('Pine Ridge State Park', 'State Park')
        f.parks['US-2'] = park('Pine Ridge Wildlife Management Area', 'Wildlife Management Area', dx_m=50)
        f.files['US-MN'] = [rec('sgnyb', 'sgnyb1', 'Pine Ridge')]
        assert f.run() == 0
        d = f.key()
        assert d['parks']['US-1']['m'] == [] == d['parks']['US-2']['m']
        assert why(d, 'US-1') == why(d, 'US-2') == 'record_shared_with_another_park'
    finally: f.done()


def test_other_park_pin_refused():
    f = Fix()
    try:   # PAD-US 236785: one record, rings at both Tracy Creek forests (102 km apart)
        f.parks['US-12778'] = park('Tracy Creek (Steuben County) State Forest', 'State Forest')
        f.parks['US-5342'] = park('Tracy Creek (Broome County) State Forest', 'State Forest', dx_m=100000,
                                  link={'id_kind': 'NY DEC page number', 'id_value': '9'})
        f.files['US-MN'] = [dict(rec('PAD-US', '236785', 'Tracy Creek State Forest', GIS_Acres=60), rings=[ring(), ring(100000)]),
                            rec('sgnya', 'sgnya1', 'Tracy Creek State Forest', URL='https://www.dec.ny.gov/lands/8.html'),
                            rec('sgnya', 'sgnya2', 'Tracy Creek State Forest', ring(100000), URL='https://www.dec.ny.gov/lands/9.html')]
        assert f.run() == 0
        d = f.key()
        assert ids(d, 'US-12778') == ['sgnya1'] and ids(d, 'US-5342') == ['sgnya2'] and by(d, 'US-5342') == 'id'
    finally: f.done()


def test_id_beats_name():
    f = Fix()
    try:
        f.parks['US-1'] = park('Bearpen Hill State Forest', 'State Forest', dx_m=5000, link={'id_kind': 'NY DEC page number', 'id_value': '8000'})
        f.parks['US-2'] = park('Bearpen Hill State Forest', 'State Forest', dx_m=150)
        f.files['US-MN'] = [rec('sgnya', 'sgnya1', 'Bearpen Hill State Forest', URL='https://www.dec.ny.gov/lands/8000.html')]
        assert f.run() == 0
        d = f.key()
        assert by(d, 'US-1') == 'id' and d['parks']['US-2']['m'] == [] and why(d, 'US-2') == 'record_shared_with_another_park'
    finally: f.done()


def test_two_records_fit():
    sz = {'acres': 100.0, 'witness': 'agency_document'}
    rs = [rec('sgnya', 'sgnya1', 'Elm Point State Forest', ring(3000, half_w=330), ACRES=100, URL='https://www.dec.ny.gov/lands/1.html'),
          rec('sgnya', 'sgnya2', 'Elm Point State Forest', ring(-3000, half_w=330), ACRES=102, URL='https://www.dec.ny.gov/lands/2.html')]
    d = one('Elm Point State Forest', 'State Forest', rs, size=sz)
    assert d['parks']['US-1']['m'] == [] and why(d, 'US-1') == 'two_records_fit'


def test_trail_park_reason():
    assert why(one('Paul Bunyan State Trail', 'State Trail', [rec('sgmnd', 'sgmnd1', 'Crow Wing')]), 'US-1') == 'record_layer_not_in_store'


def test_pin_only_reasons_fixed_list():
    sheet = {'no_record_with_this_name', 'name_but_no_pin_or_size_proof', 'two_records_fit', 'record_shared_with_another_park',
             'water_only', 'office_only'}   # layer_not_complete left the list: a state with a gap is not built at all
    assert set(RULES['pin_only_reasons']) == sheet | {'record_layer_not_in_store'}
    assert why(one('Nowhere State Park', 'State Park', [rec('sgmnd', 'sgmnd1', 'Crow Wing')]), 'US-1') == 'no_record_with_this_name'


def test_acres_no_double_count():
    rs = [rec('PAD-US', '1', 'Agassiz National Wildlife Refuge', ring(half_w=10000), GIS_Acres=61000, FeatClass='Fee'),
          rec('PAD-US', '2', 'Agassiz National Wildlife Refuge', ring(half_w=10000), GIS_Acres=61400, FeatClass='Designation'),
          rec('PAD-US', '3', 'Agassiz NWR east piece', ring(15000, half_w=300), GIS_Acres=20, FeatClass='Fee')]
    assert V.land_acres(pool_of(*rs).recs, RULES) == {'PAD-US': 61400.0}   # per class, the largest class; never 122,420
    assert one('Agassiz National Wildlife Refuge', 'National Wildlife Refuge', rs[:2])['parks']['US-1']['ac'] == 61400
    d = one('Agassiz National Wildlife Refuge', 'National Wildlife Refuge', rs[:2], dx=10500, size={'acres': 61000.0, 'witness': 'agency_document'})
    assert by(d, 'US-1') == 'name+size'                                   # the same number proves the size


def test_acres_same_ground_once():
    rs = [rec('PAD-US', '8850', 'Helen L. McNitt', ring(half_w=380), GIS_Acres=143, FeatClass='Fee'),
          rec('PAD-US', '237438', 'Helen L. McNitt', ring(half_w=370), GIS_Acres=135, FeatClass='Fee'),
          rec('PAD-US', '9', 'Helen L. McNitt', ring(5000, half_w=370), GIS_Acres=135, FeatClass='Fee')]
    assert V.land_acres(pool_of(*rs).recs, RULES) == {'PAD-US': 278.0}    # 143 once + the other piece 135
    assert V.land_acres(pool_of(*rs[:2]).recs, RULES, agency_only=True) == {'PAD-US': 143.0}
    # US-5145 Burnt-Rossman Hills: two L-shaped neighbours whose boxes overlap are NOT the same ground
    la = poly([(0, 0), (1000, 0), (1000, 300), (300, 300), (300, 1000), (0, 1000)])
    lb = poly([(1000, 1000), (1000, 330), (330, 330), (330, 1000)])
    ls = [rec('sgnya', 'sgnya1', 'Burnt-Rossman Hills State Forest', la, ACRES=124), rec('sgnya', 'sgnya2', 'Burnt-Rossman Hills State Forest', lb, ACRES=112)]
    assert V.land_acres(pool_of(*ls).recs, RULES) == {'sgnya': 236.0}


# ------------------------------------------------------------------------------------------------------------- step 1: locks
def warm(f, out='warm', cold='cold'):
    assert f.run(out, extra=['--locks', f.p(cold)]) == 0
    return [x['why'] for x in f.info(out=out)['locked_broken']]


def test_lock_holds_same_as_cold():
    f = Fix()
    try:
        mn_valley(f)
        assert f.run('cold', extra=['--write-locks']) == 0 and warm(f) == []
        assert open(f.p('cold/US-MN.json.gz'), 'rb').read() == open(f.p('warm/US-MN.json.gz'), 'rb').read()   # the key hides the lock
        assert f.info(out='warm')['locks'] == {'held': 1, 'broken': 0, 'new': 0} and f.info(out='cold')['locks']['new'] == 1
        rows = [l.split(',') for l in f.csv('v2-proof.csv', 'warm')[1:]]
        assert {r[7] for r in rows} == {'2'} and {r[-2] for r in rows} == {'held'} and {r[-1] for r in rows} == {'area'}
        row = json.load(open(f.p('cold/locks/US-MN.json')))['locks']['US-7145'][0]
        assert row['count'] == 3 and row['acres'] == 180 and row['agency_id'] == 'SRA00304' and row['layer'] == 'sgmne'
    finally: f.done()


def test_broken_lock_logged():
    f = Fix()
    try:
        mn_valley(f)
        assert f.run('cold', extra=['--write-locks']) == 0
        mn_valley(f, extra=1)                                  # a fourth tract with the same id: the park takes all four
        assert warm(f) == ['record count changed'] and len(ids(f.key(out='warm'), 'US-7145')) == 4
        mn_valley(f)
        for r in f.files['US-MN']: r['record_name'] = 'MN VALLEY'
        assert warm(f) == ['record renamed']
        mn_valley(f, acres=64.2)                               # 7% bigger
        assert warm(f) == ['size changed']
        mn_valley(f)
        f.files['US-MN'].append(rec('sgmnd', 'sgmnd1', 'Crow Wing', ring(50000)))
        for r in f.files['US-MN'][:3]: r['attributes']['mgtprgprj'] = 'SRA00999'
        assert warm(f) == ["id not in today's file"]
        mn_valley(f)
        f.parks['US-9'] = park('Other Place State Park', 'State Park', dx_m=30000, link={'id_kind': 'MN DNR unit id', 'id_value': 'SRA00304'})
        assert warm(f) == ['id now claimed by a second park']
        del f.parks['US-9']
        f.parks['US-7145']['link']['id_value'] = 'SRA00399'
        assert warm(f) == ["the park's page id changed or is missing"]
        mn_valley(f)
        f.parks['US-7146'] = f.parks.pop('US-7145')
        assert warm(f) == ['the park is no longer in the list']
        del f.parks['US-7146']
        mn_valley(f)
        for r in f.files['US-MN']: r['rings'] = [ring(40000)]  # the id's land now lies 40 km off: step 2 refuses it
        why_ = warm(f)
        assert len(why_) == 1 and why_[0].startswith('step 2 no longer proves it')
    finally: f.done()


def test_lock_zero_acres():
    t = 0.05
    assert V.acres_unchanged(0, 0, t) and V.acres_unchanged(None, 0, t)
    assert not V.acres_unchanged(0, 5, t) and not V.acres_unchanged(5, 0, t)
    assert V.acres_unchanged(100, 104, t) and not V.acres_unchanged(100, 106, t)
    f = Fix()
    try:   # a layer with no acre field: the lock measures the shape, and holds on an unchanged layer
        f.parks['US-0963'] = park('Statue of Liberty National Monument', 'National Monument', link={'id_kind': 'NPS unit code', 'id_value': 'STLI'})
        f.files['US-MN'] = [rec('sgakd', 'sgakd5', 'Statue of Liberty National Monument', UNIT_CODE='STLI')]
        assert f.run('cold', extra=['--write-locks']) == 0
        assert json.load(open(f.p('cold/locks/US-MN.json')))['locks']['US-0963'][0]['acres'] > 0 and warm(f) == []
    finally: f.done()


def test_lock_never_changes_answer():
    f = Fix()
    try:   # a hand-edited lock points park A at park B's id: A's answer is today's, and the lock is logged broken
        u = lambda n: f'https://www.dec.ny.gov/lands/{n}.html'
        f.parks['US-1'] = park('Oak Hill State Forest', 'State Forest', link={'id_kind': 'NY DEC page number', 'id_value': '1'})
        f.parks['US-2'] = park('Elm Ridge State Forest', 'State Forest', dx_m=20000, link={'id_kind': 'NY DEC page number', 'id_value': '2'})
        f.files['US-MN'] = [rec('sgnya', 'sgnya1', 'Oak Hill State Forest', URL=u(1)), rec('sgnya', 'sgnya2', 'Elm Ridge State Forest', ring(20000), URL=u(2))]
        assert f.run('cold', extra=['--write-locks']) == 0
        L = json.load(open(f.p('cold/locks/US-MN.json')))
        L['locks']['US-1'] = copy.deepcopy(L['locks']['US-2'])
        json.dump(L, open(f.p('cold/locks/US-MN.json'), 'w'))
        assert warm(f) == ["the park's page id changed or is missing"]
        assert ids(f.key(out='warm'), 'US-1') == ['sgnya1']
        assert open(f.p('cold/US-MN.json.gz'), 'rb').read() == open(f.p('warm/US-MN.json.gz'), 'rb').read()
    finally: f.done()


# ------------------------------------------------------------------------------------------------------------- gate
def gate_case(parks_doc, joins=None, how=None, parks=None):
    pl = pool_of(rec('sgnya', 'sgnya1', 'Oak Hill State Forest', URL='https://www.dec.ny.gov/lands/8000.html'))
    return V.gate(parks_doc, {'joins': joins or {}, 'how': how or {}}, pl, RULES, parks)


def test_gate_refuses_old_id():
    g = gate_case({'US-0681': {'n': 'Upper Delaware', 'm': [['3562~old', 'Upper Delaware', 5, 'name']], 'c': []}})
    assert not g['ok'] and g['old_ids'] == 1


def test_gate_refuses_missing_record():
    g = gate_case({}, joins={'US-1': [5]}, how={'US-1': (3, 'name+pin', {})})
    assert not g['ok'] and g['not_in_file'] == 1
    assert gate_case({}, joins={'US-1': [0]}, how={'US-1': (3, 'name+pin', {})})['ok']
    real = V.spell_layer
    try:   # a spelling clash: two raw records written with one id
        V.spell_layer = lambda recs, layer, rules: {r['key']: 'sgmne0777' for r in recs} if layer == 'sgmne' else {}
        pl = pool_of(rec('sgmne', 'sgmne1', 'A', su_id=1), rec('sgmne', 'sgmne2', 'B', ring(5000), su_id=2))
    finally: V.spell_layer = real
    g = V.gate({}, {'joins': {'US-1': [0]}, 'how': {'US-1': (3, 'name+pin', {})}}, pl, RULES)
    assert not g['ok'] and g['not_in_file'] == 1


def test_gate_refuses_two_name_share():
    g = gate_case({'US-1': {'n': 'Pine Ridge State Park', 'm': [['sgnyb1', 'Pine Ridge', 5, 'name+pin']]},
                   'US-2': {'n': 'Pine Ridge Wildlife Management Area', 'm': [['sgnyb1', 'Pine Ridge', 5, 'name+pin']]}})
    assert not g['ok'] and g['two_name'] == 1
    g = gate_case({'US-1': {'n': 'Pine Hill (Delaware County) State Forest', 'm': [['236695', 'Pine Hill State Forest', 5, 'name+pin']]},
                   'US-2': {'n': 'Pine Hill (Cattaraugus County) State Forest', 'm': [['236695', 'Pine Hill State Forest', 5, 'name+pin']]}})
    assert not g['ok'] and g['two_name'] == 1                   # brackets make two names
    g = gate_case({'US-1': {'n': 'Bear Swamp State Forest', 'm': [['236421', 'Bear Swamp', 5, 'id']]},
                   'US-2': {'n': 'Bear Swamp State Forest', 'm': [['236421', 'Bear Swamp', 5, 'id']]}})
    assert g['ok']                                              # one land, two park numbers, one name: allowed


def test_gate_id_mismatch():
    g = gate_case({}, joins={'US-1': [0]}, how={'US-1': (2, 'id', {'id_kind': 'NY DEC page number', 'id_value': '8001'})})
    assert not g['ok'] and g['id_mismatch'] == 1
    assert gate_case({}, joins={'US-1': [0]}, how={'US-1': (2, 'id', {'id_kind': 'NY DEC page number', 'id_value': '8000'})})['ok']


def test_gate_other_park_pin():
    parks = {'US-1': park('Oak Hill (A County) State Forest', 'State Forest'), 'US-2': park('Oak Hill (B County) State Forest', 'State Forest', dx_m=50)}
    g = gate_case({}, joins={'US-1': [0]}, how={'US-1': (3, 'name+pin', {})}, parks=parks)
    assert not g['ok'] and g['other_park_pin'] == 1
    parks['US-2'] = park('Oak Hill (B County) State Forest', 'State Forest', dx_m=50000)
    assert gate_case({}, joins={'US-1': [0]}, how={'US-1': (3, 'name+pin', {})}, parks=parks)['ok']


# ------------------------------------------------------------------------------------------------------------- whole run
def test_two_runs_same_bytes():
    f = Fix()
    try:
        mn_valley(f)
        f.parks['US-2'] = park('Crow Wing State Park', 'State Park', dx_m=8000)
        f.files['US-MN'].append(rec('sgmnd', 'sgmnd1', 'Crow Wing', ring(8000)))
        assert f.run('a') == 0 and f.run('b') == 0
        for n in ('US-MN.json.gz', 'v2-proof.csv', 'v2-pin-only.csv', 'v2-id-other-names.csv'):
            assert open(f.p(f'a/{n}'), 'rb').read() == open(f.p(f'b/{n}'), 'rb').read(), n
        assert f.csv('v2-proof.csv', 'a')[0] == 'ref,st,file_key,agency_id,layer,record_name,acres,step,by,evidence,file_area,lock,shape'
    finally: f.done()


def test_stale_key_removed():
    f = Fix()
    try:
        mn_valley(f)
        assert f.run(extra=['--write-locks']) == 0 and os.path.exists(f.p('out/US-MN.json.gz'))
        os.remove(f.p('store/US-MN.layer-records.json.gz'))
        f.files = {}; f.lists = {'MN': ['US-0364']}
        assert f.run() == 2 and not os.path.exists(f.p('out/US-MN.json.gz')) and not os.path.exists(f.p('out/locks/US-MN.json'))
    finally: f.done()


def test_id_other_names_report():
    f = Fix()
    try:   # US-10293 Raquette Boreal: DEC's page groups other named land with the park
        url = 'https://www.dec.ny.gov/lands/83175.html'
        f.parks['US-10293'] = park('Raquette Boreal Complex State Preserve', 'State Preserve', link={'id_kind': 'NY DEC page number', 'id_value': '83175'})
        f.files['US-MN'] = [rec('sgnya', 'sgnya1', 'Raquette-Jordan Boreal Primitive Area', URL=url),
                            rec('sgnya', 'sgnya2', 'Lake Ozonia Fishing Access Site', ring(4000), URL=url)]
        assert f.run() == 0 and len(ids(f.key(), 'US-10293')) == 2
        rows = f.csv('v2-id-other-names.csv')
        assert rows[0] == 'ref,st,park_name,record_key,record_name,layer,km_from_pin' and len(rows) == 2 and 'Lake Ozonia' in rows[1]
    finally: f.done()


def test_no_legacy_import():
    src = open(os.path.join(ROOT, '.github', 'scripts', 'kpc_us_key_v2.py'), encoding='utf-8').read()
    bad = re.findall(r'^\s*(?:import|from)\s+[^\n]*\b(kpc_us_key|kpc_match_checks|kpc_same_land|kpc_store_attrs)\b', src, re.M)
    assert not bad, bad
    assert not re.search(r'__import__|importlib', src)


def test_rule_table_typo_refused():
    good = json.load(open(os.path.join(ROOT, '.github', 'us-key-v2-rules.json')))
    def setp(d, path, v):
        for k in path[:-1]: d = d[k]
        if v is KeyError: d.pop(path[-1])
        else: d[path[-1]] = v
    cases = [(['switches'], {}), (['values', 'pin_ft'], {'value': 1, 'why': 'x', 'test': 'y'}), (['values', 'pin_m', 'why'], KeyError),
             (['values', 'pin_m', 'value'], '100'), (['rules', 0, 'test'], KeyError), (['rules', 0, 'step'], 'later'),
             (['rules', 0, 'stub'], 'maybe'), (['rules', 0, 'fn'], ''), (['tables', 'id_ties', 'value', 0, 'field'], KeyError),
             (['tables', 'kind_patterns', 'value', 0, 1], '(unclosed'), (['tables', 'kind_swaps', 'value', 0, 'park'], 'x'),
             (['notes', 'x'], 5), (['tables', 'own_page', 'value', 'sites'], 'agency')]
    for path, v in cases:
        d = copy.deepcopy(good); setp(d, path, v)
        f = Fix()
        try:
            json.dump(d, open(f.p('repo/.github/us-key-v2-rules.json'), 'w'))
            f.parks['US-1'] = park('Crow Wing State Park', 'State Park'); f.files['US-MN'] = [rec('sgmnd', 'sgmnd1', 'Crow Wing')]
            assert f.run() == 2, path
        finally: f.done()


def test_trial_rules():
    f = Fix()
    try:
        f.parks['US-1'] = park('Crow Wing State Park', 'State Park', dx_m=350); f.files['US-MN'] = [rec('sgmnd', 'sgmnd1', 'Crow Wing')]
        assert f.run() == 0 and f.key()['parks']['US-1']['m'] == [] and '(trial' not in f.key()['tool']
        d = json.load(open(f.p('repo/.github/us-key-v2-rules.json'))); d['values']['pin_m']['value'] = 200
        json.dump(d, open(f.p('trial.json'), 'w'))
        assert f.run('t', extra=['--rules', f.p('trial.json')]) == 0
        k = f.key(out='t')
        assert ids(k, 'US-1') == ['sgmnd1'] and k['tool'].endswith('(trial rules)')
        r = json.load(open(f.p('t/v2-run.json')))['inputs']['rules']
        assert r['file'] == f.p('trial.json') and r['trial'] and len(r['sha256']) == 64
        d['values']['pin_ft'] = {'value': 1, 'why': 'x', 'test': 'y'}; json.dump(d, open(f.p('bad.json'), 'w'))
        assert f.run('b', extra=['--rules', f.p('bad.json')]) == 2   # the same guards
    finally: f.done()


def test_selftest_runs():
    with contextlib.redirect_stdout(io.StringIO()): assert V.run(['--selftest']) == 0


def test_every_rule_names_a_test():
    d = json.load(open(os.path.join(ROOT, '.github', 'us-key-v2-rules.json')))
    names = [r['test'] for r in d['rules']] + [v['test'] for part in ('values', 'tables') for v in d[part].values()]
    missing = sorted({n for n in names if not callable(globals().get(n)) or not n.startswith('test_')})
    assert not missing, missing
    assert all(hasattr(V, fn) for r in d['rules'] for fn in r['fn'].split(',') if fn), 'a rule row names a function the module lacks'


TESTS = [(n, f) for n, f in list(globals().items()) if n.startswith('test_') and callable(f)]


# ------------------------------------------------------------------------------------------------------------- mutation check
def passes(name):
    try:
        globals()[name]()
        return True
    except Exception:  # noqa: BLE001  (a failure or a crash: the test noticed)
        return False


def with_table(d, name):
    """Run test `name` against a mutated rule table d. -> True when the test still passes (the mutation survived)."""
    global RULES
    tmp = tempfile.mkdtemp(prefix='v2mut-')
    old_rules, old_src = RULES, SRC['github']
    try:
        os.makedirs(os.path.join(tmp, '.github'))
        json.dump(d, open(os.path.join(tmp, '.github', 'us-key-v2-rules.json'), 'w'))
        shutil.copy(os.path.join(ROOT, '.github', 'link-id-ties.json'), os.path.join(tmp, '.github', 'link-id-ties.json'))
        try: RULES = V.load_rules(tmp)
        except V.RulesError: return False                       # the table is refused: noticed
        SRC['github'] = os.path.join(tmp, '.github')
        return passes(name)
    finally:
        RULES, SRC['github'] = old_rules, old_src
        shutil.rmtree(tmp, ignore_errors=True)


def emptied(v):
    if isinstance(v, list): return []
    if isinstance(v, dict): return {}
    return '(?!)'                                               # a pattern that never matches


def stub_for(kind, real):
    if kind == 'true': return lambda *a, **k: True
    if kind == 'false': return lambda *a, **k: False
    if kind == 'identity': return lambda *a, **k: a[0]
    def empty(*a, **k):
        r = real(*a, **k)
        return tuple(type(x)() for x in r) if isinstance(r, tuple) else (type(r)() if r is not None else None)
    return empty


def mutation_lines():
    """Every value x10 and /10, every table emptied, every id_ties 'where' removed, every rule row's function stubbed: the
    named test must fail. -> [(ok, line)]."""
    good = json.load(open(os.path.join(ROOT, '.github', 'us-key-v2-rules.json')))
    out = []
    for k, row in good['values'].items():
        alive = []
        for f in (10.0, 0.1):
            d = copy.deepcopy(good); d['values'][k]['value'] = row['value'] * f
            if with_table(d, row['test']): alive.append(f'x{f:g}')
        ok = len(alive) < 2
        out.append((ok, f"{'PASS' if ok else 'FAIL'} mutation value {k}: {row['test']} {'notices' if ok else 'does not notice x10 or /10'}"))
    for k, row in good['tables'].items():
        d = copy.deepcopy(good); d['tables'][k]['value'] = emptied(row['value'])
        ok = not with_table(d, row['test'])
        out.append((ok, f"{'PASS' if ok else 'FAIL'} mutation table {k} emptied: {row['test']} {'notices' if ok else 'does not notice'}"))
    for n, t in enumerate(good['tables']['id_ties']['value']):
        if not t.get('where'): continue
        d = copy.deepcopy(good); d['tables']['id_ties']['value'][n].pop('where')
        test = good['tables']['id_ties']['test']
        ok = not with_table(d, test)
        out.append((ok, f"{'PASS' if ok else 'FAIL'} mutation id_ties {t['layer']}.{t['field']} 'where' removed: {test} {'notices' if ok else 'does not notice'}"))
    for row in good['rules']:
        if row['stub'] == 'none':
            out.append((True, f"PASS mutation rule {row['id']}: no function to stub; {row['test']} checks it directly"))
            continue
        fns = [x for x in row['fn'].split(',') if x]
        real = {fn: getattr(V, fn) for fn in fns}
        try:
            for fn in fns: setattr(V, fn, stub_for(row['stub'], real[fn]))
            ok = not passes(row['test'])
        finally:
            for fn in fns: setattr(V, fn, real[fn])
        out.append((ok, f"{'PASS' if ok else 'FAIL'} mutation rule {row['id']} ({row['fn']} -> {row['stub']}): {row['test']} {'notices' if ok else 'does not notice'}"))
    return out


# ------------------------------------------------------------------------------------------------------------- runner
def main():
    t0, failed = time.time(), 0
    for n, f in TESTS:
        try:
            f()
            print(f'PASS {n}')
        except Exception:  # noqa: BLE001
            failed += 1
            print(f'FAIL {n}: {traceback.format_exc().strip().splitlines()[-1][:300]}')
    if '--no-mutation' not in sys.argv:
        for ok, line in mutation_lines():
            failed += not ok
            print(line)
    print(('ALL PASS' if not failed else f'SOME FAILED ({failed})') + f' ({time.time() - t0:.0f} s)')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
