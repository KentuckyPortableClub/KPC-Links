#!/usr/bin/env python3
"""Display copy from the outline store (KPC owner, 2026-11-13; levels, pieces, one layer per park, parks across state lines and
the grade fixes 2026-11-14): tools/kpc_display_copy.py and kpc-outline-display.js.

Everything here is SYNTHETIC: small fake stores are written into a temporary folder by this test (made-up parks near 0 N 0 E,
tests/display_copy_fixture.py), in the store's format 1 with a store-tool "full 3" index. No real outline, no network (sockets
are blocked), no repo file written. The 500,000-point two-state park is in tests/test_display_copy_huge_nov14.py and the publish
script in tests/test_display_publish_nov14.py. Prints PASS / FAIL lines and ends ALL PASS or SOME FAILED."""
import gzip, hashlib, json, math, os, pathlib, shutil, socket, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(ROOT / 'tests'))


def _no_net(*a, **k): raise OSError('network blocked in this test')


socket.socket.connect = _no_net
socket.create_connection = _no_net
import kpc_display_copy as K  # noqa: E402
from display_copy_fixture import circle, square, record, park, write_store  # noqa: E402

FAILS = []
NOLOG = lambda *a: None


def check(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok: FAILS.append(name)


def feats_of(out, area):
    idx = json.loads((out / area / 'INDEX.json').read_text())
    fs = []
    for name, *_ in idx['parts']: fs += json.loads(gzip.decompress((out / area / name).read_bytes()))['features']
    return idx, fs


def by_ref(fs):
    d = {}
    for f in fs: d.setdefault(f['properties']['ref'], []).append(f)
    return d


def drawn_lines(fs):
    out = []
    for f in fs:
        if f['properties'].get('role') == 'hit': continue
        g = f['geometry']
        out += g['coordinates'] if g['type'] == 'MultiLineString' else [r for p in g['coordinates'] for r in p]
    return out


def near_any(pt, lines, tol_deg):
    px, py = pt
    for l in lines:
        for (ax, ay), (bx, by) in zip(l, l[1:]):
            dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
            t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
            if math.hypot(px - ax - t * dx, py - ay - t * dy) <= tol_deg: return True
    return False


def ring_drawn(ring, lines, tol_m=5.0):
    """every vertex of ring within tol_m of a drawn line (near 0 N: 1 degree ~ 111 km)"""
    return all(near_any(p, lines, tol_m / 111000) for p in ring)


PREC = {'US-ZZ': ['stl', 'lay1', 'lay2', 'lay3', 'lay4', 'lay5', '*', 'PAD-US']}
tmp = pathlib.Path(tempfile.mkdtemp(prefix='kpc-display-test-'))
try:
    def build(name, parks, areas='US-ZZ', ws=None, **kw):
        st = tmp / ('st-' + name)
        for a in ([areas] if isinstance(areas, str) else areas):
            write_store(st, a, parks if isinstance(areas, str) else parks[a], **(ws or {}))
        kw.setdefault('precedence_table', PREC)
        rep = K.build(st, areas, tmp / ('out-' + name), log=NOLOG, **kw)
        return rep, tmp / ('out-' + name)

    # ---- basics ------------------------------------------------------------------------------------------------------------
    big = [circle(0.5 + 0.02 * k, 0.5, 0.008, 900, wobble=0.05, phase=k) for k in range(6)]
    parks = [
        park('US-0001', [record('a1', 'lay1', [circle(0.1, 0.1, 0.01, 200, wobble=0.03)])]),
        park('US-0002', [record('b1', 'lay1', [circle(0.2, 0.1, 0.01, 120)]), record('b2', 'lay2', [circle(0.2, 0.1, 0.01, 120)]),
                         record('b3', 'lay1', [circle(0.2, 0.1, 0.0100001, 97)])]),
        park('US-0003', [record('c1', 'lay1', [circle(0.3, 0.1, 0.01, 80)]), record('c2', 'lay2', [circle(0.31, 0.1, 0.004, 60)], publishable=False, cls='PRIVATE UNTIL LICENCE READ')]),
        park('US-0004', [record('d1', 'lay1', [circle(0.4, 0.1, 0.01, 60)]), record('d2', 'lay1', [circle(0.9, 0.1, 0.01, 60)])]),
        park('US-0005', [record('e%d' % k, 'lay1', [r]) for k, r in enumerate(big)]),
        park('US-0007', [record('g1', 'lay1', [circle(0.7, 0.2, 0.02, 100), circle(0.7, 0.2, 0.005, 40, clockwise=False)])]),
        park('US-0009', [record('i1', 'lay1', [circle(0.1, 0.3, 0.01, 50)])]),
        park('US-0010', [record('j1', 'lay5', [circle(0.2, 0.3, 0.01, 50)], cls='NON-COMMERCIAL', credit='County Parks')]),
        park('US-0011', [record('k%d' % k, 'lay1', [circle(0.3 + 0.005 * (k % 26), 0.4 + 0.005 * (k // 26), 0.002, 8, phase=k)]) for k in range(650)]),
    ]
    dcsv = tmp / 'doubtful.csv'
    dcsv.write_text('state,park,name,matcher_doubt_code,key_records_joined,matcher_records,matcher_review_state\n'
                    'ZZ,US-0009,Test,pin-far,i1,,KEEP-FLAGGED\nAA,US-0001,Other state,pin-far,a1,,KEEP-FLAGGED\n')
    rep, out = build('base', parks, doubtful=K.read_doubtful([dcsv], 'US-ZZ'))
    idx, fs = feats_of(out, 'US-ZZ'); feats = by_ref(fs); one = {r: v[0] for r, v in feats.items()}; rows = {r['ref']: r for r in rep['rows']}
    check('the public check of what was written finds no problem', K.check(out, 'US-ZZ', public=True) == [])
    check('a one-tract park is drawn with every point (no simplifying under the cap)', rows['US-0001']['detail_m'] == 0 and rows['US-0001']['points'] == 201)
    check('identical geometry in two layers is drawn once; a near-identical tract of the same layer is drawn once too',
          rows['US-0002']['drawn_records'] == 1 and rows['US-0002']['once_m'] > 0)
    check("a park with ONE unpublishable tract keeps today's outline (never half a park)", 'US-0003' not in feats and 'US-0003' in idx['fallback'])
    check("tracts 10 km or more apart = check join: today's outline", 'US-0004' not in feats and 'check join' in rep['fallback_reasons']['US-0004'])
    check('a park over the cap is simplified to the cap with the smallest ladder step (written on it), error measured',
          rows['US-0005']['points'] <= 3000 and one['US-0005']['properties']['detail_m'] == rows['US-0005']['detail_m'] and rows['US-0005']['worst_m'] <= rows['US-0005']['detail_m'] + 0.7)
    check('a hole stays a hole', len(one['US-0007']['geometry']['coordinates']) == 1 and len(one['US-0007']['geometry']['coordinates'][0]) == 2)
    check("a park in the doubtful-joins list keeps today's outline (another state's row is ignored)", 'US-0009' in idx['fallback'] and 'US-0001' in feats)
    check("NON-COMMERCIAL is publishable; the credit line is the park's own", one['US-0010']['properties']['cr'] == ['County Parks'])
    check('every park is drawn or listed under fallback, never both', set(feats) | set(idx['fallback']) == {p['ref'] for p in parks} and not set(feats) & set(idx['fallback']))
    check('the 650-tract park: overview within the cap, middle level when the overview is over 25 m off',
          rows['US-0011']['points'] <= 3000 and ((rows['US-0011']['worst_m'] <= 25) == ('US-0011' not in idx['mid'])))
    check('invariants hold on every drawn park (0 m of boundary missing, no land lost)', all(r['missing_m'] == 0 and not r['lost_fail'] for r in rep['rows']))

    # ---- must-fix 1: the winning layer is always drawn in full; draw once only against what is drawn ------------------------
    D = 0.009                                                              # about 1 km
    A = square(0.1, 0.1, 0.1 + D, 0.1 + D, 40)
    extra = square(0.1 + D + 0.002, 0.1, 0.1 + D + 0.006, 0.104, 20)
    r1, o1 = build('g1', [park('P1', [record('a', 'stl', [A]), record('p', 'PAD-US', [A, extra])])])
    l1 = drawn_lines(by_ref(feats_of(o1, 'US-ZZ')[1]).get('P1', []))
    check('GRADER CASE: state tract A + a PAD-US record holding a copy of A and an extra parcel: ALL of A is drawn',
          bool(l1) and ring_drawn(A, l1) and r1['rows'][0]['missing_m'] == 0)
    check('...and the extra parcel is drawn', ring_drawn(extra, l1))
    r5, o5 = build('twin', [park('P5', [record('p', 'PAD-US', [A]), record('a', 'stl', [A])])])
    check("GRADER CASE: identical geometry with the lower layer first in the store: the winning layer's copy is the one kept",
          r5['rows'][0]['won'] == 'stl' and by_ref(feats_of(o5, 'US-ZZ')[1])['P5'][0]['properties']['layers'] == ['stl'])
    # ---- must-fix 2: lower layers judged per part and per stretch; holes are not land -------------------------------------
    dense = square(0.1, 0.1, 0.1 + D, 0.1 + D, 400)
    for size, name in ((0.00054, '60 m'), (0.0036, '400 m')):
        par = square(0.1 + D + 0.001, 0.1, 0.1 + D + 0.001 + size, 0.1 + size, 8)
        rr, oo = build('g2-' + name[:-2].strip(), [park('P2', [record('a', 'stl', [A]), record('p', 'PAD-US', [dense, par])])])
        ll = drawn_lines(by_ref(feats_of(oo, 'US-ZZ')[1]).get('P2', []))
        check(f'GRADER CASE: a {name} extra parcel inside a multipart PAD-US record (dense copy of the state tract) is kept and drawn',
              bool(ll) and ring_drawn(par, ll) and rr['rows'][0]['lost_m2'] == 0)
    outer = square(0.1, 0.1, 0.1 + D, 0.1 + D, 40); hole = square(0.103, 0.103, 0.1066, 0.1066, 10, clockwise=False)
    holeland = square(0.103, 0.103, 0.1066, 0.1066, 10)
    rh, oh = build('hole', [park('P4', [record('a', 'stl', [outer, hole]), record('p', 'PAD-US', [holeland])])])
    check("GRADER CASE: land a lower layer has inside the winner's HOLE is not 'covered': it is kept (no land lost)",
          'P4' not in rh['fallback_reasons'] and rh['rows'][0]['lost_m2'] == 0 and rh['rows'][0]['kept_whole_for_land'] == 1)
    for off, kept in ((10, False), (25, False), (29, False), (31, True), (45, True)):
        B = [(round(x + off / 111320, 6), y) for x, y in A]
        ro, oo = build(f'off{off}', [park('P6', [record('a', 'stl', [A]), record('p', 'PAD-US', [B])])])
        rw = ro['rows'][0]
        check(f'a lower-layer copy offset {off} m is ' + ('kept (drawn where outside the 30 m strip)' if kept else
                                                          f'not drawn; the strip it adds is reported ({rw["band_m2"]:.0f} m2), never lost'),
              rw['missing_m'] == 0 and rw['lost_m2'] == 0 and ((rw['drawn_records'] == 2) == kept) and (kept or rw['band_m2'] > 0))
    # ---- the invariants themselves fail a park ----------------------------------------------------------------------------
    recs = [K.Rec('US-ZZ', 'a', 'stl', [A], 'x', 0)]; K.clusters(recs); K.process_park(recs, PREC)
    inv_ok = K.invariants(recs, [A]); inv_miss = K.invariants(recs, [A[:len(A) // 2]])
    check('INVARIANT I1: a drawn copy missing half the winning boundary is caught (metres missing > 0)',
          inv_ok['missing_m'] == 0 and inv_miss['missing_m'] > 1000)
    recs2 = [K.Rec('US-ZZ', 'a', 'stl', [A], 'x', 0), K.Rec('US-ZZ', 'p', 'PAD-US', [extra], 'y', 1)]; K.clusters(recs2); K.process_park(recs2, PREC)
    recs2[1].seg = [bytearray([K.COVERED] * len(s)) for s in recs2[1].seg]       # pretend the extra parcel was wrongly hidden
    inv_lost = K.invariants(recs2, [A])
    check('INVARIANT I2: land wrongly hidden (a parcel no shown tract holds) is caught and fails the park', inv_lost['lost_m2'] > 1000 and inv_lost['lost_fail'])

    # ---- must-fix 3: the licence gate ------------------------------------------------------------------------------------
    C = [circle(0.6, 0.6, 0.01, 40)]
    def gate_run(name, rec, ws=None):
        rr, oo = build('gate-' + name, [park('G1', [rec])], ws=ws)
        return 'G1' in json.loads((oo / 'US-ZZ' / 'INDEX.json').read_text())['fallback']
    odd = ['yes', 'TRUE', 1, None, '', [], {}]
    check("'publishable' must be exactly true: 'yes', 'TRUE', 1, None, '', [], {} in the index's record_meta are all refused",
          all(gate_run(f'pv{i}', record('r1', 'lay1', C), ws={'index_override': {'G1': {'record_meta': {'r1': {'publishable': v}}}}}) for i, v in enumerate(odd)))
    check('...and in the record', all(gate_run(f'pr{i}', record('r1', 'lay1', C, publishable=v, publish_basis='verified-row', private_reason=''),
                                               ws={'index_override': {'G1': {'record_meta': {'r1': {'publishable': True, 'publish_basis': 'verified-row', 'private_reason': ''}},
                                                                          'park_publishable': True}}})
                                      for i, v in enumerate(odd)))
    no_draw = [c for c, ok in K.LICENCE_CLASSES.items() if not ok]
    leaked = [c for i, c in enumerate(no_draw) if not gate_run(f'cls{i}', record('r1', 'lay1', C, cls=c))]
    check(f"LICENCE CLASSES from the store's licence-classes.json: the {len(no_draw)} classes it does not allow (incl. SHARE-ALIKE) are refused "
          f"even when marked publishable (drawn: {leaked or 'none'})", not leaked and 'SHARE-ALIKE' in no_draw and len(no_draw) == 5)
    ok_classes = sorted(K.ALLOW_CLASSES)
    check(f'...and the allowed ones pass, PUBLIC DOMAIN included ({", ".join(ok_classes)})',
          'PUBLIC DOMAIN' in ok_classes and len(ok_classes) == 5 and all(not gate_run(f'ok{i}', record('r1', 'lay1', C, cls=c)) for i, c in enumerate(ok_classes)))
    lc = json.loads(K.LICENCE_CLASSES_FILE.read_text(encoding='utf-8'))
    check("...the builder's class list is the store tool's licence-classes.json (store_format_version kpc-outline-store-index/3)",
          lc.get('store_format_version') == 'kpc-outline-store-index/3' and set(K.LICENCE_CLASSES) == set(lc['classes'])
          and all(K.LICENCE_CLASSES[c] == (v['can_be_publishable'] and c != 'SHARE-ALIKE') for c, v in lc['classes'].items()))
    unk = []
    for label, rec_, ws_ in (('a record class', record('r1', 'lay1', C, cls='LOOKS RESTRICTED'), None),
                             ("the index's licence_classes list", record('r1', 'lay1', C), {'classes': sorted(K.LICENCE_CLASSES) + ['NEW CLASS']})):
        try: build('unk' + str(len(unk)), [park('G1', [rec_])], ws=ws_); unk.append(False)
        except K.DisplayError as ex: unk.append('does not know' in str(ex))
    check('a licence class the builder does not know (in a record, or in the index list) STOPS the build', all(unk))
    wd = {'key "wdpa123"': record('wdpa123', 'lay1', C), 'record_id "WDPA-1234"': record('r1', 'lay1', C, record_id='WDPA-1234'),
          'attribute WDPAID': record('r1', 'lay1', C, attributes={'WDPAID': 555}), 'agency UNEP-WCMC': record('r1', 'lay1', C, agency_label='UNEP-WCMC'),
          'agency "World Database on Protected Areas"': record('r1', 'lay1', C, agency_label='World Database on Protected Areas'),
          'credit "Protected Planet"': record('r1', 'lay1', C, credit='Protected Planet'),
          'WDPA after 3,000 characters of source_detail': record('r1', 'lay1', C, source_detail={'note': 'x' * 3000 + ' from WDPA'}),
          'wdpa_derived true (record and index)': record('r1', 'lay1', C, wdpa_derived=True),
          'wdpa_derived "false" (a string)': record('r1', 'lay1', C, wdpa_derived='false'),
          'wdpa_derived missing': {k: v for k, v in record('r1', 'lay1', C).items() if k != 'wdpa_derived'}}
    leaked = [k for i, (k, rec) in enumerate(wd.items()) if not gate_run(f'wd{i}', rec)]
    check(f'WDPA: the boolean wdpa_derived first, then the words in VALUES ({len(wd)} placements; drawn: {leaked or "none"})', not leaked)
    check('...wdpa_derived true in the index only (record false) = refused',
          gate_run('wdi', record('r1', 'lay1', C), ws={'index_override': {'G1': {'record_meta': {'r1': {'wdpa_derived': True}}}}}))
    plain = record('r1', 'lay1', C)
    check("...a plain v3 record (it HAS a field named wdpa_derived, false) is NOT WDPA: field names are never searched",
          'wdpa_derived' in plain and not K.wdpa_hit(plain, {k: plain[k] for k in K.META_KEYS}, None) and not gate_run('wdplain', plain))
    check("...and PAD-US's own WDPA_Cd code field does not make a record WDPA",
          not gate_run('wdcd', record('r1', 'PAD-US', C, attributes={'WDPA_Cd': 'WDPA 0', 'Own_Name': 'FWS'})))
    check('the stricter answer wins: index and record classes differ = refused',
          gate_run('dis2', record('r1', 'lay1', C), ws={'index_override': {'G1': {'record_meta': {'r1': {'licence_class': 'NO TERMS STATED'}}}}}))
    check('...index and record credit lines differ = refused',
          gate_run('dis4', record('r1', 'lay1', C), ws={'index_override': {'G1': {'record_meta': {'r1': {'credit_line': 'Someone Else'}}}}}))
    check('...a record with no record_meta entry in the index = refused',
          gate_run('dis5', record('r1', 'lay1', C), ws={'index_override': {'G1': {'record_meta': {'r1': None}}}}))
    check('...park_publishable false = refused', gate_run('dis3', record('r1', 'lay1', C), ws={'index_override': {'G1': {'park_publishable': False}}}))
    check("...a publish basis other than a verified row or the owner's confirmation = refused",
          gate_run('basis', record('r1', 'lay1', C, basis='none')) and gate_run('basis2', record('r1', 'lay1', C, basis='layer metadata')))
    lt_no = {'publishable': False, 'class': 'OPEN'}
    check("...the index layers table saying no = refused, whether its key is the store's own form (no https://) or a full address",
          gate_run('lt', record('r1', 'lay1', C), ws={'layers': {'example.invalid/arcgis/rest/services/x/mapserver/0': lt_no}})
          and gate_run('lt2', record('r1', 'lay1', C), ws={'layers': {'https://example.invalid/arcgis/rest/services/x/MapServer/0/query': lt_no}}))
    check('...and a layers table row saying yes (store form) lets it pass',
          not gate_run('lt3', record('r1', 'lay1', C), ws={'layers': {'example.invalid/arcgis/rest/services/x/mapserver/0': {'publishable': True, 'class': 'OPEN'}}}))
    check("layer keys are normalised like the store tool's norm_layer (scheme, case, /query, slash, port)",
          K.norm_layer_url('https://Example.invalid/A/MapServer/0/query') == K.norm_layer_url('example.invalid/a/mapserver/0') == 'example.invalid/a/mapserver/0'
          and K.norm_layer_url('http://127.0.0.1:8080/x/') == '127.0.0.1:8080/x' and K.norm_layer_url('https://h.gov:443/x') == 'h.gov/x')
    for label, ws in (('store_format_version kpc-outline-store-index/2', {'fmt': 'kpc-outline-store-index/2'}),
                      ('no store_format_version (store tool before full 3)', {'fmt': None}),
                      ('no record_meta (nothing is ever guessed from licence text)', {'maps': False})):
        try: build('old' + str(len(label)), [park('G1', [record('r1', 'lay1', C)])], ws=ws); refused = False
        except K.DisplayError: refused = True
        check(f'an index with {label} is refused for a public build', refused)
    rp, op = build('oldprev', [park('G1', [record('r1', 'lay1', C)])], ws={'fmt': None, 'maps': False}, preview=True)
    check('...a PRIVATE PREVIEW may still read an older index (for measuring on the PC), stamped',
          json.loads((op / 'US-ZZ' / 'INDEX.json').read_text()).get('stamp') == K.PREVIEW_STAMP)
    st_nf = tmp / 'st-nofiles'; write_store(st_nf, 'US-ZZ', [park('G1', [record('r1', 'lay1', C)])])
    ixp = st_nf / 'index-US-ZZ.json'; ix = json.loads(ixp.read_text()); ix['files'] = {}; ixp.write_text(json.dumps(ix))
    try: K.build(st_nf, 'US-ZZ', tmp / 'out-nofiles', log=NOLOG); nf_refused = False
    except K.DisplayError: nf_refused = True
    check('an index without file checksums is refused for a public build', nf_refused)
    st_bad = tmp / 'st-badsha'; write_store(st_bad, 'US-ZZ', [park('G1', [record('r1', 'lay1', C)])])
    ixp = st_bad / 'index-US-ZZ.json'; ix = json.loads(ixp.read_text())
    ix['files']['US-ZZ.kpcstore.json.gz']['sha256'] = '0' * 64; ixp.write_text(json.dumps(ix))
    try: K.build(st_bad, 'US-ZZ', tmp / 'out-badsha', log=NOLOG); bad_refused = False
    except K.DisplayError as ex: bad_refused = 'sha256' in str(ex)
    ix['files']['US-ZZ.kpcstore.json.gz']['sha256'] = hashlib.sha256((st_bad / 'US-ZZ.kpcstore.json.gz').read_bytes()).hexdigest()
    ix['files']['US-ZZ-extra.kpcstore.json.gz'] = {'sha256': 'f' * 64}; ixp.write_text(json.dumps(ix))
    try: K.build(st_bad, 'US-ZZ', tmp / 'out-badsha2', log=NOLOG); bad2 = False
    except K.DisplayError: bad2 = True
    check("every area file the index lists is checked: a wrong sha256, or a listed file that is missing, stops a public build", bad_refused and bad2)
    st_c = tmp / 'st-combined'; write_store(st_c, 'US-ZZ', [park('G1', [record('r1', 'lay1', C)])])
    (st_c / 'index-US-ZZ.json').rename(st_c / 'index.json')
    try: K.build(st_c, 'US-ZZ', tmp / 'out-combined', log=NOLOG); comb = False
    except K.DisplayError as ex: comb = 'per-area' in str(ex)
    check("a public build reads only the PER-AREA index (the combined index.json merges parks that span areas)", comb)

    # ---- must-fix 4: nothing private in the public files; credits per park --------------------------------------------------
    sec = [park('S1', [record('sgPRIVATEKEY77', 'lay1', C, cls='RESTRICTED IN WRITING')]), park('S2', [record('r2', 'lay1', [circle(0.8, 0.6, 0.01, 40)], publishable=False)]),
           park('S3', [record('r3', 'PAD-US', [circle(0.6, 0.8, 0.01, 40)], credit='National Park Service')]),
           park('S4', [record('r4', 'PAD-US', [circle(0.8, 0.8, 0.01, 40)], credit='US Forest Service')]),
           park('S5', [record('r5', 'lay2', [circle(0.6, 0.95, 0.01, 40)], credit='Town GIS (owner nancy.x@town.gov)')])]
    rs, os_ = build('secret', sec)
    raw = (os_ / 'US-ZZ' / 'INDEX.json').read_text()
    check('public INDEX.json carries no record keys, licence classes, reasons or store names (fallback = "kept today\'s outline" only)',
          'sgPRIVATEKEY77' not in raw and 'RESTRICTED' not in raw.upper() and 'WDPA' not in raw.upper() and set(json.loads(raw)['fallback'].values()) == {K.FALLBACK_CODE}
          and 'kpcstore' not in raw and 'made' not in json.loads(raw))
    check('...the detailed reasons are in the private report only', 'RESTRICTED IN WRITING' in rs['fallback_reasons'].get('S1', ''))
    f2 = by_ref(feats_of(os_, 'US-ZZ')[1])
    check('credits are per park: two PAD-US parks keep their own agency (no last-park-wins)',
          f2['S3'][0]['properties']['cr'] == ['National Park Service'] and f2['S4'][0]['properties']['cr'] == ['US Forest Service'])
    check('an e-mail and an owner note in a credit line are removed before it is written', f2['S5'][0]['properties']['cr'] == ['Town GIS'] and '@' not in raw)
    (os_ / 'US-ZZ' / 'INDEX.json').write_text(raw.replace('"about"', '"note": "licence class OPEN", "about"'))
    check('check --public refuses a private word in INDEX.json', any('private word' in x for x in K.check(os_, 'US-ZZ', public=True)))

    # ---- inputs that must exist, far groups, 180 degrees, rebuilds ----------------------------------------------------------
    try: K.read_doubtful([tmp / 'no-such.csv'], 'US-ZZ'); dmiss = False
    except K.DisplayError: dmiss = True
    check('a doubtful-joins list that does not exist stops the build (never "nothing is doubtful")', dmiss)
    check('the shipped doubtful-joins list exists and is read', len(K.read_doubtful([ROOT / 'tools' / 'kpc_display_doubtful.csv'], 'US-NH')) > 0)
    try: K.key_areas(tmp / 'no-such-dir'); kmiss = False
    except K.DisplayError: kmiss = True
    check('a --key-dir that does not exist stops the build', kmiss)
    many = [record('m%d' % k, 'lay1', [square(round(0.3 * (k % 30), 6), round(1.0 + 0.3 * (k // 30), 6), round(0.3 * (k % 30) + 0.001, 6), round(1.0 + 0.3 * (k // 30) + 0.001, 6), 2)])
            for k in range(451)]
    rm, om = build('far451', [park('F1', many)])
    check("451 tracts 30 km apart: check join (today's outline), even with more than 400 groups", 'check join' in rm['fallback_reasons'].get('F1', ''))
    am = [record('w1', 'lay1', [square(179.993, 52.0, 179.9995, 52.006, 5)]), record('e1', 'lay1', [square(-179.9995, 52.0, -179.993, 52.006, 5)])]
    ra, oa = build('am', [park('A1', am)])
    check('two tracts 1 km apart across 180 degrees are one park (not "20,000 km apart")', 'A1' not in ra['fallback_reasons'] and ra['rows'][0]['missing_m'] == 0)
    rb1, ob1 = build('rep1', parks[:3]); rb2, ob2 = build('rep2', parks[:3])
    names = ['INDEX.json'] + [x[0] for x in json.loads((ob1 / 'US-ZZ' / 'INDEX.json').read_text())['parts']]
    check('the same store gives byte-identical files, INDEX.json included', all((ob1 / 'US-ZZ' / n).read_bytes() == (ob2 / 'US-ZZ' / n).read_bytes() for n in names))

    # ---- fine pieces ------------------------------------------------------------------------------------------------------
    rough = [(round(0.1 + i * 0.00002, 6), round(0.8 + 0.0003 * math.sin(i / 7) + 0.00001 * math.sin(i * 1.7), 6)) for i in range(6000)]
    ring = list(reversed(rough + [(round(0.1 + 5999 * 0.00002, 6), 0.81), (0.1, 0.81)] + [rough[0]]))
    write_store(tmp / 'store-f', 'US-ZZ', [park('US-0020', [record('p1', 'lay1', [ring])])])
    rf = K.build(tmp / 'store-f', 'US-ZZ', tmp / 'out-f', cap=200, piece_cap=1000, mid_cap=500, log=NOLOG)
    fe = json.loads((tmp / 'out-f' / 'US-ZZ' / 'INDEX.json').read_text())['fine'].get('US-0020') or {}
    sizes = [t[1] for t in (fe.get('tiles') or {}).values()]
    check(f'FINE pieces: every piece under the hard cap ({len(sizes)} pieces, largest {max(sizes or [0])} B, cap 1000), tiles shrank to fit',
          bool(sizes) and max(sizes) <= 1000 and fe['t'] < K.TILE_START and K.check(tmp / 'out-f', 'US-ZZ', piece_cap=1000) == [])
    ends = {}
    for t in fe.get('tiles') or {}:
        for l in json.loads(gzip.decompress((tmp / 'out-f' / 'US-ZZ' / 'fine' / 'US-0020' / f'{t}.geojson.gz').read_bytes()))['features'][0]['geometry']['coordinates']:
            for pt in (tuple(l[0]), tuple(l[-1])): ends[pt] = ends.get(pt, 0) + 1
    check('...the pieces join exactly (every cut point shared by two pieces), within 5 m of the store, invariants pass',
          bool(ends) and not [p for p, n in ends.items() if n % 2] and rf['rows'][0]['fine_worst_m'] <= 5 and rf['rows'][0]['missing_m'] == 0)

    # ---- two areas: one park across a state line ---------------------------------------------------------------------------
    west, east = square(0.1, 0.1, 0.2, 0.2, 30), square(0.2, 0.1, 0.3, 0.2, 30)
    copy_a = square(0.12, 0.25, 0.18, 0.3, 30); copy_b = [(round(x + 0.000005, 6), y) for x, y in copy_a]
    shared = record('sh1', 'stl', [square(0.2, 0.32, 0.24, 0.36, 10)])
    two = {'US-ZA': [park('US-0040', [record('w1', 'stl', [west]), record('cp1', 'stl', [copy_a]), shared]), park('US-0041', [record('o1', 'stl', [circle(0.15, 0.5, 0.01, 40)])])],
           'US-ZB': [park('US-0040', [record('e1', 'stl', [east]), record('cp2', 'stl', [copy_b]), dict(shared)])]}
    r2, o2 = build('two', two, areas=['US-ZA', 'US-ZB'])
    ia, fa = feats_of(o2, 'US-ZA'); ib, fb = feats_of(o2, 'US-ZB')
    la = drawn_lines([f for f in fa if f['properties']['ref'] == 'US-0040']); lb = drawn_lines([f for f in fb if f['properties']['ref'] == 'US-0040'])
    on_line = [1 for l in la + lb for a, b in zip(l, l[1:]) if a[0] == 0.2 and b[0] == 0.2 and 0.1 < a[1] < 0.2 and 0.1 < b[1] < 0.2]
    check('A PARK ACROSS TWO STATES: no line where its own tracts meet at the state line, outer edges drawn, invariants pass',
          not on_line and ring_drawn([p for p in west if p[0] < 0.2], la + lb) and ring_drawn([p for p in east if p[0] > 0.2], la + lb)
          and {r['ref']: r for r in r2['rows']}['US-0040']['missing_m'] == 0)
    check("...two copies of one boundary with both tracts on the same side keep their line",
          len([p for l in la + lb for p in l if 0.25 - 1e-9 <= p[1] <= 0.3 + 1e-9 and 0.12 <= p[0] <= 0.18001]) > 20)
    rbb, obb = build('two-b', {'US-ZA': two['US-ZA']}, areas=['US-ZA'], park_areas={'US-0040': ['US-ZA', 'US-ZB']})
    check("...built WITHOUT its other state (the key says it is in both): today's outline", 'not in this run' in rbb['fallback_reasons'].get('US-0040', ''))

    # ---- the browser loader (node) --------------------------------------------------------------------------------------
    node = shutil.which('node')
    if not node:
        print('SKIP browser loader checks: node is not installed here')
    else:
        site = tmp / 'site'; (site / 'data' / 'display').mkdir(parents=True)
        shutil.copytree(out / 'US-ZZ', site / 'data/display/US-ZZ')
        rpv, opv = build('pv', parks[:2], preview=True); shutil.copytree(opv / 'US-ZZ', site / 'data/display/US-ZY')
        shutil.copytree(o2 / 'US-ZA', site / 'data/display/US-ZA'); shutil.copytree(o2 / 'US-ZB', site / 'data/display/US-ZB')
        js = (ROOT / 'kpc-outline-display.js').resolve()
        old = {'features': [{'type': 'Feature', 'properties': {'ref': r, 'g': 'official', 'old': True}, 'geometry': None} for r in ('US-0001', 'US-0003', 'US-0099', 'US-0040')]
               + [{'type': 'Feature', 'properties': {'ref': 'US-0098', 'g': 'pin'}, 'geometry': None}]}
        script = r'''
const fs=require('fs'),path=require('path'),zlib=require('zlib');const SITE=process.argv[2],JS=process.argv[3],OLD=JSON.parse(process.argv[4]);
function setup(search,store){const ls={};global.localStorage={getItem:k=>k in ls?ls[k]:null,setItem:(k,v)=>{ls[k]=String(v)},removeItem:k=>{delete ls[k]}};if(store)ls.kpcOutlineStore='1';
 global.location={search};global.window=global;delete global.kpcDisplayOutlines;global.fetched=[];
 global.fetch=(u,o)=>{global.fetched.push(u);const p=path.join(SITE,u.replace(/\?.*$/,''));if(!fs.existsSync(p))return Promise.resolve({ok:false,status:404});const b=fs.readFileSync(p);
  return Promise.resolve({ok:true,status:200,arrayBuffer:()=>Promise.resolve(b.buffer.slice(b.byteOffset,b.byteOffset+b.length))});};
 global.DecompressionStream=function(){};global.Blob=function(parts){this.b=Buffer.from(parts[0])};
 global.Blob.prototype.stream=function(){const b=this.b;return{pipeThrough:()=>zlib.gunzipSync(b)}};global.Response=function(x){this.x=x};global.Response.prototype.text=function(){return Promise.resolve(this.x.toString())};
 delete require.cache[require.resolve(JS)];return require(JS);}
(async()=>{const r={};
 let A=setup('',false);r.offNull=(await A.load('US-ZZ',OLD))===null;r.offFetched=global.fetched.length;
 A=setup('?outlines=store',false);let pk=await A.load('US-ZZ',OLD);r.on=pk&&pk.source;r.refs=pk?[...new Set(pk.features.map(f=>f.properties.ref))]:[];
 r.oldKept=pk?pk.features.filter(f=>f.properties.old).map(f=>f.properties.ref):[];r.remember=global.localStorage.getItem('kpcOutlineStore');
 r.versioned=global.fetched.filter(u=>/geojson\.gz\?v=[0-9a-f]{12}$/.test(u)).length;r.credit=pk?A.creditLine(pk,pk.by['US-0010']):'';
 A=setup('?outlines=store',false);let pa=await A.load('US-ZA',OLD);r.multiOn=pa?pa.features.filter(f=>f.properties.ref==='US-0040'&&!f.properties.old).length:-1;
 A=setup('?outlines=store',false);const ip=path.join(SITE,'data/display/US-ZB/INDEX.json'),keep=fs.readFileSync(ip);const ix=JSON.parse(keep);ix.gen='000000000000';fs.writeFileSync(ip,JSON.stringify(ix));
 pa=await A.load('US-ZA',OLD);r.multiGen=pa?pa.features.filter(f=>f.properties.ref==='US-0040').map(f=>!!f.properties.old):null;fs.writeFileSync(ip,keep);
 A=setup('?outlines=old',true);r.oldParam=(await A.load('US-ZZ',OLD))===null;r.forgot=global.localStorage.getItem('kpcOutlineStore');
 A=setup('',true);r.preview=(await A.load('US-ZY',OLD))===null;
 A=setup('',true);r.missing=(await A.load('US-QQ',OLD))===null;
 r.badArea=setup('?outlines=store',false).wanted('../x')===false;
 A=setup('?outlines=store',false);r.limits=[A.MAX_PIECES,A.MAX_LOOK_BYTES,A.FINE_KEEP];
 console.log(JSON.stringify(r));})().catch(e=>{console.log(JSON.stringify({error:String(e&&e.stack||e)}));});
'''
        sp = tmp / 'loader_test.js'; sp.write_text(script)
        env = {k: v for k, v in os.environ.items() if 'proxy' not in k.lower()}
        res = subprocess.run([node, str(sp), str(site), str(js), json.dumps(old)], capture_output=True, text=True, timeout=120, env=env)
        try: r = json.loads(res.stdout.strip().splitlines()[-1])
        except Exception: r = {'error': res.stdout + res.stderr}
        if r.get('error'): print('   ', r['error'][:600])
        check('loader: switch off = null and NOTHING is fetched', r.get('offNull') is True and r.get('offFetched') == 0)
        check('loader: ?outlines=store draws the display copy and is remembered', r.get('on') == 'store' and r.get('remember') == '1')
        check("loader: today's outline is kept for every park the display copy leaves out; pin rows stay out",
              sorted(r.get('oldKept') or []) == ['US-0003', 'US-0040', 'US-0099'] and 'US-0098' not in (r.get('refs') or []))
        check('loader: every part is asked for with its own ?v=<sha12>', (r.get('versioned') or 0) >= 1)
        check("loader: the popup credit line is the park's own and says to check the official map", (r.get('credit') or '').startswith('Outline: County Parks.'))
        check('loader: a park across two states is new only when both are on and from the same build', (r.get('multiOn') or 0) >= 1 and r.get('multiGen') == [True])
        check('loader: ?outlines=old switches it off and forgets the toggle', r.get('oldParam') is True and r.get('forgot') is None)
        check('loader: a PRIVATE PREVIEW is never drawn; no copy = null; a bad area name is refused', r.get('preview') is True and r.get('missing') is True and r.get('badArea') is True)
        check('loader: per-look limits 48 pieces / 1 MB, fine-piece cache 60', r.get('limits') == [48, 1000000, 60])
        src = js.read_text(encoding='utf-8')
        check('loader: the go-live list ships empty (LIVE_AREAS = [])', 'var LIVE_AREAS = [];' in src)
        pages = [p.name for p in ROOT.glob('*.html') if 'kpc-outline-display.js' in p.read_text(encoding='utf-8', errors='replace')]
        check('loader: no page includes kpc-outline-display.js yet (nothing changes for the public)', pages == [])
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print('ALL PASS' if not FAILS else f'SOME FAILED ({len(FAILS)})')
sys.exit(1 if FAILS else 0)
