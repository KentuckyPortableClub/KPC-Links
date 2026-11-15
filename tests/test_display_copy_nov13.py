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
from display_copy_fixture import circle, square, record, park, write_store, line_record, pin_record, wiggle_line  # noqa: E402

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


def LAY(rep, ref):
    """the layers drawn for a park, from the PRIVATE report (public files carry no layer names)"""
    row = next((r for r in rep['rows'] if r['ref'] == ref), None)
    return sorted({l for v in (row or {}).get('layers_by_area', {}).values() for l in v})


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
        park('US-0012', [record('m1', 'lay2', [circle(0.5, 0.1, 0.01, 50)], publishable=False, cls='PRIVATE UNTIL LICENCE READ')]),
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
    check("a park with one publishable and one unpublishable tract is DRAWN from the publishable tract alone (each record judged on its own): "
          "only its layer is named, the private tract's land is not drawn, and no land is called lost",
          'US-0003' in feats and 'US-0003' not in idx['fallback'] and LAY(rep, 'US-0003') == ['lay1']
          and one['US-0003']['properties']['cr'] == ['Test Agency lay1'] and rows['US-0003']['held_records'] == 1
          and rows['US-0003']['public_records'] == 1 and rows['US-0003']['lost_m2'] == 0 and rows['US-0003']['missing_m'] == 0
          and max(x for l in drawn_lines(feats['US-0003']) for x, y in l) < 0.3105)
    check("a park whose ONLY tract is unpublishable keeps today's outline", 'US-0012' not in feats and 'US-0012' in idx['fallback'])
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
    r1, o1 = build('g1', [park('US-7024', [record('a', 'stl', [A]), record('p', 'PAD-US', [A, extra])])])
    l1 = drawn_lines(by_ref(feats_of(o1, 'US-ZZ')[1]).get('US-7024', []))
    check('GRADER CASE: state tract A + a PAD-US record holding a copy of A and an extra parcel: ALL of A is drawn',
          bool(l1) and ring_drawn(A, l1) and r1['rows'][0]['missing_m'] == 0)
    check('...and the extra parcel is drawn', ring_drawn(extra, l1))
    r5, o5 = build('twin', [park('US-7028', [record('p', 'PAD-US', [A]), record('a', 'stl', [A])])])
    check("GRADER CASE: identical geometry with the lower layer first in the store: the winning layer's copy is the one kept",
          r5['rows'][0]['won'] == 'stl' and 'US-7028' in by_ref(feats_of(o5, 'US-ZZ')[1]) and LAY(r5, 'US-7028') == ['stl'])
    # ---- must-fix 2: lower layers judged per part and per stretch; holes are not land -------------------------------------
    dense = square(0.1, 0.1, 0.1 + D, 0.1 + D, 400)
    for size, name in ((0.00054, '60 m'), (0.0036, '400 m')):
        par = square(0.1 + D + 0.001, 0.1, 0.1 + D + 0.001 + size, 0.1 + size, 8)
        rr, oo = build('g2-' + name[:-2].strip(), [park('US-7025', [record('a', 'stl', [A]), record('p', 'PAD-US', [dense, par])])])
        ll = drawn_lines(by_ref(feats_of(oo, 'US-ZZ')[1]).get('US-7025', []))
        check(f'GRADER CASE: a {name} extra parcel inside a multipart PAD-US record (dense copy of the state tract) is kept and drawn',
              bool(ll) and ring_drawn(par, ll) and rr['rows'][0]['lost_m2'] == 0)
    outer = square(0.1, 0.1, 0.1 + D, 0.1 + D, 40); hole = square(0.103, 0.103, 0.1066, 0.1066, 10, clockwise=False)
    holeland = square(0.103, 0.103, 0.1066, 0.1066, 10)
    rh, oh = build('hole', [park('US-7027', [record('a', 'stl', [outer, hole]), record('p', 'PAD-US', [holeland])])])
    check("GRADER CASE: land a lower layer has inside the winner's HOLE is not 'covered': it is kept (no land lost)",
          'US-7027' not in rh['fallback_reasons'] and rh['rows'][0]['lost_m2'] == 0 and rh['rows'][0]['kept_whole_for_land'] == 1)
    for off, kept in ((10, False), (25, False), (29, False), (31, True), (45, True)):
        B = [(round(x + off / 111320, 6), y) for x, y in A]
        ro, oo = build(f'off{off}', [park('US-7029', [record('a', 'stl', [A]), record('p', 'PAD-US', [B])])])
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
        rr, oo = build('gate-' + name, [park('US-7014', [rec])], ws=ws)
        return 'US-7014' in json.loads((oo / 'US-ZZ' / 'INDEX.json').read_text())['fallback']
    odd = ['yes', 'TRUE', 1, None, '', [], {}]
    check("'publishable' must be exactly true: 'yes', 'TRUE', 1, None, '', [], {} in the index's record_meta are all refused",
          all(gate_run(f'pv{i}', record('r1', 'lay1', C), ws={'index_override': {'US-7014': {'record_meta': {'r1': {'publishable': v}}}}}) for i, v in enumerate(odd)))
    check('...and in the record', all(gate_run(f'pr{i}', record('r1', 'lay1', C, publishable=v, publish_basis='verified-row', private_reason=''),
                                               ws={'index_override': {'US-7014': {'record_meta': {'r1': {'publishable': True, 'publish_basis': 'verified-row', 'private_reason': ''}},
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
    try: build('unkidx', [park('US-7014', [record('r1', 'lay1', C)])], ws={'classes': sorted(K.LICENCE_CLASSES) + ['NEW CLASS']}); unk_idx = False
    except K.DisplayError as ex: unk_idx = 'does not know' in str(ex)
    check("a licence class the builder does not know in the INDEX's licence_classes list stops the build", unk_idx)
    ru, ou = build('unkrec', [park('US-7014', [record('r1', 'lay1', C, cls='LOOKS RESTRICTED')]),
                              park('US-7015', [record('r2', 'lay1', [circle(0.6, 0.8, 0.01, 40)]),
                                          record('r3', 'lay2', [circle(0.62, 0.8, 0.01, 40)], cls='BRAND NEW CLASS')])])   # marked publishable, class unknown
    iu, fu = feats_of(ou, 'US-ZZ'); bu = by_ref(fu)
    check("...but an unknown class on ONE record drops that record only (the private report says why); the area is built",
          'US-7014' not in bu and iu['fallback'].get('US-7014') == K.FALLBACK_CODE and 'builder knows' in ru['fallback_reasons']['US-7014']
          and 'US-7015' in bu and LAY(ru, 'US-7015') == ['lay1'] and 'builder knows' in ru['held_records_reasons']['US-7015']
          and K.check(ou, 'US-ZZ', public=True) == [])
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
          gate_run('wdi', record('r1', 'lay1', C), ws={'index_override': {'US-7014': {'record_meta': {'r1': {'wdpa_derived': True}}}}}))
    plain = record('r1', 'lay1', C)
    check("...a plain v3 record (it HAS a field named wdpa_derived, false) is NOT WDPA: field names are never searched",
          'wdpa_derived' in plain and not K.wdpa_hit(plain, {k: plain[k] for k in K.META_KEYS}, None) and not gate_run('wdplain', plain))
    check("...and PAD-US's own WDPA_Cd code field does not make a record WDPA",
          not gate_run('wdcd', record('r1', 'PAD-US', C, attributes={'WDPA_Cd': 'WDPA 0', 'Own_Name': 'FWS'})))
    check('the stricter answer wins: index and record classes differ = refused',
          gate_run('dis2', record('r1', 'lay1', C), ws={'index_override': {'US-7014': {'record_meta': {'r1': {'licence_class': 'NO TERMS STATED'}}}}}))
    check('...index and record credit lines differ = refused',
          gate_run('dis4', record('r1', 'lay1', C), ws={'index_override': {'US-7014': {'record_meta': {'r1': {'credit_line': 'Someone Else'}}}}}))
    check('...a record with no record_meta entry in the index = refused',
          gate_run('dis5', record('r1', 'lay1', C), ws={'index_override': {'US-7014': {'record_meta': {'r1': None}}}}))
    check("...but the park-level flag park_publishable is NOT read: a record that passes on its own is drawn",
          not gate_run('dis3', record('r1', 'lay1', C), ws={'index_override': {'US-7014': {'park_publishable': False}}}))
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
                      ('store_format_version kpc-outline-store-index/5 (newer than this reader)', {'fmt': 'kpc-outline-store-index/5'}),
                      ('store_format_version kpc-outline-store-index/99', {'fmt': 'kpc-outline-store-index/99'}),
                      ('store_format_version kpc-outline-store-index/4x', {'fmt': 'kpc-outline-store-index/4x'}),
                      ('store_format_version bogus/4', {'fmt': 'bogus/4'}),
                      ('no store_format_version (store tool before full 3)', {'fmt': None}),
                      ('no record_meta (nothing is ever guessed from licence text)', {'maps': False})):
        try: build('old' + str(len(label)), [park('US-7014', [record('r1', 'lay1', C)])], ws=ws); refused = False
        except K.DisplayError: refused = True
        check(f'an index with {label} is refused for a public build', refused)
    try: build('prev5', [park('US-7014', [record('r1', 'lay1', C)])], ws={'fmt': 'kpc-outline-store-index/5'}, preview=True); pv5 = False
    except K.DisplayError as ex: pv5 = 'reader knows' in str(ex)
    check('...and a PRIVATE PREVIEW refuses a newer format too (/5)', pv5)
    for n in (3, 4):
        r34, o34 = build(f'fmt{n}ok', [park('US-7014', [record('r1', 'lay1', C)])], ws={'fmt': f'kpc-outline-store-index/{n}'})
        check(f'kpc-outline-store-index/{n} is read', r34['parks_drawn'] == 1)
    rp, op = build('oldprev', [park('US-7014', [record('r1', 'lay1', C)])], ws={'fmt': None, 'maps': False}, preview=True)
    check('...a PRIVATE PREVIEW may still read an older index (for measuring on the PC), stamped',
          json.loads((op / 'US-ZZ' / 'INDEX.json').read_text()).get('stamp') == K.PREVIEW_STAMP)
    st_nf = tmp / 'st-nofiles'; write_store(st_nf, 'US-ZZ', [park('US-7014', [record('r1', 'lay1', C)])])
    ixp = st_nf / 'index-US-ZZ.json'; ix = json.loads(ixp.read_text()); ix['files'] = {}; ixp.write_text(json.dumps(ix))
    try: K.build(st_nf, 'US-ZZ', tmp / 'out-nofiles', log=NOLOG); nf_refused = False
    except K.DisplayError: nf_refused = True
    check('an index without file checksums is refused for a public build', nf_refused)
    st_bad = tmp / 'st-badsha'; write_store(st_bad, 'US-ZZ', [park('US-7014', [record('r1', 'lay1', C)])])
    ixp = st_bad / 'index-US-ZZ.json'; ix = json.loads(ixp.read_text())
    ix['files']['US-ZZ.kpcstore.json.gz']['sha256'] = '0' * 64; ixp.write_text(json.dumps(ix))
    try: K.build(st_bad, 'US-ZZ', tmp / 'out-badsha', log=NOLOG); bad_refused = False
    except K.DisplayError as ex: bad_refused = 'sha256' in str(ex)
    ix['files']['US-ZZ.kpcstore.json.gz']['sha256'] = hashlib.sha256((st_bad / 'US-ZZ.kpcstore.json.gz').read_bytes()).hexdigest()
    ix['files']['US-ZZ-extra.kpcstore.json.gz'] = {'sha256': 'f' * 64}; ixp.write_text(json.dumps(ix))
    try: K.build(st_bad, 'US-ZZ', tmp / 'out-badsha2', log=NOLOG); bad2 = False
    except K.DisplayError: bad2 = True
    check("every area file the index lists is checked: a wrong sha256, or a listed file that is missing, stops a public build", bad_refused and bad2)
    st_c = tmp / 'st-combined'; write_store(st_c, 'US-ZZ', [park('US-7014', [record('r1', 'lay1', C)])])
    (st_c / 'index-US-ZZ.json').rename(st_c / 'index.json')
    try: K.build(st_c, 'US-ZZ', tmp / 'out-combined', log=NOLOG); comb = False
    except K.DisplayError as ex: comb = 'per-area' in str(ex)
    check("a public build reads only the PER-AREA index (the combined index.json merges parks that span areas)", comb)

    # ---- the licence gate is per RECORD: each record stands on its own --------------------------------------------------------
    USGS = ('U.S. Geological Survey (USGS) Gap Analysis Project (GAP), 2024, Protected Areas Database of the United States '
            '(PAD-US) 4.1')
    def priv(key, rings):   # a state record whose own terms are private: never drawn, never named
        return record(key, 'nhgranit', rings, publishable=False, cls='PRIVATE UNTIL LICENCE READ', credit='NH GRANIT conservation lands')
    mix = [park('US-7016', [priv('nh1', [circle(0.5, 0.2, 0.012, 60)]), record('pad1', 'PAD-US', [circle(0.5, 0.2, 0.01, 60)], cls='PUBLIC DOMAIN', credit=USGS)]),
           park('US-7017', [priv('nh2', [circle(0.8, 0.2, 0.01, 60)])]),
           park('US-7018', [priv('nh3', [circle(0.5, 0.45, 0.012, 60)]), record('sa3', 'PAD-US', [circle(0.5, 0.45, 0.01, 60)], cls='SHARE-ALIKE', credit=USGS)]),
           park('US-7019', [priv('nh4', [circle(0.8, 0.45, 0.012, 60)]), record('wd4', 'PAD-US', [circle(0.8, 0.45, 0.01, 60)], cls='PUBLIC DOMAIN', credit=USGS, wdpa_derived=True)])]
    rmx, omx = build('mixed', mix)
    imx, fmx = feats_of(omx, 'US-ZZ'); bmx = by_ref(fmx); rwx = {r['ref']: r for r in rmx['rows']}
    far = max(math.hypot(x - 0.5, y - 0.2) for l in drawn_lines(bmx.get('US-7016', [])) for x, y in l) if 'US-7016' in bmx else 9
    blob = b''.join(gzip.decompress(q.read_bytes()) if q.suffix == '.gz' else q.read_bytes() for q in sorted((omx / 'US-ZZ').rglob('*')) if q.is_file())
    check("PER-RECORD GATE: a park whose state record is private and whose PAD-US record is public is drawn from PAD-US, "
          "with the USGS credit, although the store calls the park not publishable as a whole",
          'US-7016' in bmx and LAY(rmx, 'US-7016') == ['PAD-US'] and rwx['US-7016']['won'] == 'PAD-US'
          and bmx['US-7016'][0]['properties']['cr'] == [USGS] and not imx['fallback'].get('US-7016'))
    check('...the private state shape is NOT drawn (only the PAD-US ring) and no land is reported lost or missing',
          far < 0.0105 and rwx['US-7016']['lost_m2'] == 0 and rwx['US-7016']['missing_m'] == 0 and not rwx['US-7016']['lost_fail']
          and rwx['US-7016']['held_records'] == 1 and rwx['US-7016']['public_records'] == 1 and rwx['US-7016']['distinct_records'] == 1)
    check('...and the private layer, its credit and its record key are nowhere in the public files',
          not any(w in blob for w in (b'nhgranit', b'NH GRANIT', b'nh1', b'PRIVATE UNTIL')) and b'PAD-US' in blob)
    check("a park whose only record is private keeps today's outline", 'US-7017' not in bmx and imx['fallback'].get('US-7017') == K.FALLBACK_CODE)
    check("a private record beside a SHARE-ALIKE one keeps today's outline (no record passes the gate)",
          'US-7018' not in bmx and imx['fallback'].get('US-7018') == K.FALLBACK_CODE and 'SHARE-ALIKE' in rmx['fallback_reasons']['US-7018'])
    check("a private record beside a WDPA-derived one keeps today's outline (no record passes the gate)",
          'US-7019' not in bmx and imx['fallback'].get('US-7019') == K.FALLBACK_CODE and 'WDPA' in rmx['fallback_reasons']['US-7019'])
    check('the reasons the private records were held are kept in the PRIVATE report for the park that was drawn',
          'nh1' in rmx['held_records_reasons'].get('US-7016', '') and 'US-7017' not in rmx['held_records_reasons'])

    # a WDPA-derived record that is otherwise perfect (publishable, PUBLIC DOMAIN, verified row, plain credit) beside a passing
    # record; and a record with good geometry and every other field good but publishable false, beside two passing records
    # that carry different credits. Only the passing records are drawn, and only their credits are carried.
    def good_but(key, layer, rings, credit, **kw):
        return record(key, layer, rings, cls='PUBLIC DOMAIN', credit=credit, **kw)
    mix2 = [park('US-7020', [record('st5', 'lay1', [circle(0.2, 0.7, 0.01, 60)], credit='State Parks Office'),
                        good_but('wd5', 'lay3', [circle(0.215, 0.7, 0.004, 40)], 'Global Areas Credit', wdpa_derived=True)]),
            park('US-7021', [record('st6', 'lay1', [circle(0.5, 0.7, 0.008, 60)], credit='State Parks Office'),
                        record('co6', 'lay3', [circle(0.53, 0.7, 0.005, 50)], credit='County Lands Office'),
                        good_but('np6', 'lay2', [circle(0.515, 0.715, 0.004, 40)], 'Hidden Town Office', publishable=False,
                                 publish_basis='verified-row', private_reason='',
                                 publish_basis_detail={'evidence_url': 'https://example.invalid/terms', 'date_read': '2026-11-14'})]),
            park('US-7022', [good_but('wd7', 'lay1', [circle(0.8, 0.7, 0.01, 60)], 'Global Areas Credit', wdpa_derived=True)]),
            park('US-7023', [good_but('np8', 'lay1', [circle(0.8, 0.9, 0.01, 60)], 'Hidden Town Office', publishable=False,
                                 publish_basis='verified-row', private_reason='')])]
    rm2, om2 = build('mixed2', mix2)
    im2, fm2 = feats_of(om2, 'US-ZZ'); bm2 = by_ref(fm2); rw2 = {r['ref']: r for r in rm2['rows']}
    blob2 = b''.join(gzip.decompress(q.read_bytes()) if q.suffix == '.gz' else q.read_bytes() for q in sorted((om2 / 'US-ZZ').rglob('*')) if q.is_file())
    def max_from(ref, cx, cy):
        return max(math.hypot(x - cx, y - cy) for l in drawn_lines(bm2.get(ref, [])) for x, y in l) if ref in bm2 else 9
    def near_pt(ref, px, py, tol):
        return any(math.hypot(x - px, y - py) < tol for l in drawn_lines(bm2.get(ref, [])) for x, y in l)
    check('the public check of the mixed-park build finds no problem', K.check(om2, 'US-ZZ', public=True) == [])
    check('WDPA-DERIVED beside a passing record: the park is drawn from the passing record only, with its credit only',
          'US-7020' in bm2 and LAY(rm2, 'US-7020') == ['lay1'] and bm2['US-7020'][0]['properties']['cr'] == ['State Parks Office']
          and rw2['US-7020']['public_records'] == 1 and rw2['US-7020']['held_records'] == 1 and not im2['fallback'].get('US-7020'))
    check('...the WDPA-derived ring (which reaches about 1 km outside the state ring) is not drawn',
          max_from('US-7020', 0.2, 0.7) < 0.0105 and not near_pt('US-7020', 0.219, 0.7, 0.0003))
    check('...and nothing of the WDPA-derived record (its credit, its key, the word WDPA) is in any public file',
          not any(w in blob2 for w in (b'Global Areas', b'wd5', b'wd7', b'wdpa', b'WDPA')))
    check('NOT PUBLISHABLE but good geometry and every other field good: not drawn; the two passing records are drawn with BOTH credits',
          'US-7021' in bm2 and LAY(rm2, 'US-7021') == ['lay1', 'lay3']
          and bm2['US-7021'][0]['properties']['cr'] == ['County Lands Office', 'State Parks Office']
          and rw2['US-7021']['public_records'] == 2 and rw2['US-7021']['held_records'] == 1
          and 'np6' in rm2['held_records_reasons'].get('US-7021', '') and 'publishable' in rm2['held_records_reasons'].get('US-7021', ''))
    check("...the not-publishable record's ring (outside both passing rings) is not drawn, and its credit and key are in no public file",
          not near_pt('US-7021', 0.515, 0.719, 0.0005) and b'Hidden Town' not in blob2 and b'np6' not in blob2 and b'np8' not in blob2)
    check('ALL FAIL, WDPA-derived only: nothing drawn from the store (today\'s outline kept; the pin is not touched)',
          'US-7022' not in bm2 and im2['fallback'].get('US-7022') == K.FALLBACK_CODE and 'WDPA' in rm2['fallback_reasons']['US-7022']
          and 'US-7022' not in rw2)
    check("ALL FAIL, not-publishable only (good geometry): nothing drawn from the store (today's outline kept)",
          'US-7023' not in bm2 and im2['fallback'].get('US-7023') == K.FALLBACK_CODE and 'publishable' in rm2['fallback_reasons']['US-7023'])
    check('...the public INDEX lists the all-fail parks only as "kept today\'s outline" (no reason, no record key)',
          set(im2['fallback']) == {'US-7022', 'US-7023'} and set(im2['fallback'].values()) == {K.FALLBACK_CODE})

    # ---- store index format 4 (full 3.5): geometry kinds area / line / pin, the same per-record gate for every kind ----------
    T1 = wiggle_line(0.32, 0.3, 0.36, 80); T4 = wiggle_line(0.6, 0.6, 0.66, 120)
    TRAIL = dict(boundary_rule='trail_100ft', corridor_ft=100, corridor_m=30.48, corridor_from='centreline')
    RIVER = dict(boundary_rule='river_100ft_from_bank', corridor_from='waters_edge', bank_status='bank_missing', river_class='big river')
    f4 = [park('US-7005', [record('a1', 'lay1', [circle(0.3, 0.3, 0.01, 60)], credit='State Parks Office'),
                      line_record('t1', 'lay3', [T1], credit='Trail Office', **TRAIL),
                      pin_record('p1', 'lay2', 0.305, 0.305, credit='Point Office'),
                      line_record('t2', 'lay3', [wiggle_line(0.3, 0.33, 0.34, 40)], credit='Hidden Trail Office', publishable=False),
                      line_record('t3', 'lay3', [wiggle_line(0.3, 0.27, 0.34, 40)], cls='PUBLIC DOMAIN', credit='Global Line Credit', wdpa_derived=True)]),
          park('US-7006', [line_record('t4', 'lay1', [T4], credit='Trail Office', **RIVER)]),
          park('US-7007', [pin_record('p3', 'lay1', 0.9, 0.9, credit='Point Office')]),
          park('US-7008', [line_record('t5', 'lay1', [wiggle_line(0.1, 0.9, 0.15, 40)], credit='Hidden Trail Office', publishable=False)]),
          park('US-7009', [record('a5', 'lay1', [circle(0.5, 0.9, 0.006, 40)]), record('u5', 'lay1', [circle(0.52, 0.9, 0.006, 40)], geometry_kind='blob')]),
          park('US-7010', [record('a6', 'lay1', [circle(0.81, 0.3, 0.004, 40)]),
                      record('c6', 'lay1', [circle(0.8, 0.3, 0.0003, 16)], geometry_kind='pin', pin_point=[0.8, 0.3], ring_is_stand_in_circle=True)])]
    r4, o4 = build('fmt4', f4, ws={'fmt': 'kpc-outline-store-index/4'})
    i4, fs4 = feats_of(o4, 'US-ZZ'); b4 = by_ref(fs4); rw4 = {r['ref']: r for r in r4['rows']}
    blob4 = b''.join(gzip.decompress(q.read_bytes()) if q.suffix == '.gz' else q.read_bytes() for q in sorted((o4 / 'US-ZZ').rglob('*')) if q.is_file())
    same = lambda a, b: len(a) == len(b) and all(abs(p[0] - q[0]) <= 0.6e-5 and abs(p[1] - q[1]) <= 0.6e-5 for p, q in zip(a, b))   # only rounded
    has = lambda lines, path: [l for l in lines if same(l, path)]
    check('FORMAT 4: a /4 store is read and its public files pass the public check; INDEX.json names the line rule (no band drawn)',
          K.check(o4, 'US-ZZ', public=True) == [] and 'no zone band is drawn' in i4.get('line_rule', ''))
    f1 = {f['properties']['role']: f for f in b4.get('US-7005', [])}
    l1 = f1['line']['geometry']['coordinates'] if 'line' in f1 else []
    check('MIXED /4 park: the area is drawn as an area (its hit polygon) and the official line AS GIVEN (open, every point, '
          'only rounded), both credits carried, the zone note from allow-listed values only',
          set(f1) == {'line', 'hit'} and len(has(l1, T1)) == 1 and has(l1, T1)[0][0] != has(l1, T1)[0][-1]
          and len(f1['hit']['geometry']['coordinates']) == 1 and f1['line']['properties']['cr'] == ['State Parks Office', 'Trail Office']
          and LAY(r4, 'US-7005') == ['lay1', 'lay3'] and f1['line']['properties'].get('line') is True
          and f1['line']['properties'].get('zone') == [{'rule': 'trail_100ft', 'from': 'centreline', 'ft': 100}] and not i4['fallback'].get('US-7005'))
    check('...the line is never turned into a polygon: no line point is in the hit polygon\'s rings',
          bool(has(l1, T1)) and 'hit' in f1 and not {tuple(p) for p in has(l1, T1)[0]} & {tuple(p) for poly in f1['hit']['geometry']['coordinates'] for ring in poly for p in ring})
    ys = [y for l in l1 for x, y in l] + [y for poly in (f1['hit']['geometry']['coordinates'] if 'hit' in f1 else []) for ring in poly for x, y in ring]
    check('...the private line and the WDPA-derived line are not drawn (every drawn point is on the park area or the public line)',
          ys and all(0.2895 <= y <= 0.3105 for y in ys))
    check('...the pin record is not drawn; the private report counts each kind',
          rw4['US-7005']['line_records'] == 1 and rw4['US-7005']['pin_records_not_drawn'] == 1
          and rw4['US-7005']['held_records'] == 2 and r4['kinds_not_outlines']['US-7005'] == {'line': 1, 'pin': 1, 'unknown': 0})
    check('...nothing of the records that were not drawn (credit lines, keys) is in a public file',
          not any(w in blob4 for w in (b'Hidden Trail', b'Global Line', b'Point Office', b'"t2"', b'"t3"', b'"p1"')))
    f2 = b4.get('US-7006', [])
    check('A RIVER park of one official line: drawn as that line only (one open line, every point), no polygon, no band; '
          "the zone note says 100 ft from the bank, banks missing; river_class (not on the allow-list) is not passed on",
          len(f2) == 1 and f2[0]['geometry']['type'] == 'MultiLineString' and len(f2[0]['geometry']['coordinates']) == 1
          and same(f2[0]['geometry']['coordinates'][0], T4) and f2[0]['properties']['role'] == 'line' and f2[0]['properties']['points'] == len(T4)
          and f2[0]['properties'].get('zone') == [{'rule': 'river_100ft_from_bank', 'from': 'waters_edge', 'bank': 'bank_missing'}]
          and 'US-7006' not in i4['fallback'] and b'big river' not in blob4 and b'river_class' not in blob4)
    check("A PIN-only park (publishable official point): not drawn as an outline, today's outline kept, the POTA pin untouched; counted",
          'US-7007' not in b4 and i4['fallback'].get('US-7007') == K.FALLBACK_CODE and '1 pin' in r4['fallback_reasons']['US-7007']
          and r4['pin_records_not_drawn'] == 3 and b'0.9, 0.9' not in blob4 and b'[0.9,0.9]' not in blob4)
    check("a park whose only line is not publishable: nothing drawn, today's outline",
          'US-7008' not in b4 and i4['fallback'].get('US-7008') == K.FALLBACK_CODE and 'publishable' in r4['fallback_reasons']['US-7008'])
    xs5 = [x for f in b4.get('US-7009', []) for l in drawn_lines([f]) for x, y in l]
    check('an UNKNOWN geometry kind is left out (counted); the area beside it is drawn',
          xs5 and max(xs5) < 0.5065 and r4['unknown_kind_records_not_drawn'] == 1)
    xs6 = [x for f in b4.get('US-7010', []) for l in drawn_lines([f]) for x, y in l]
    check("a stand-in circle (geometry_kind pin, ring_is_stand_in_circle) is never drawn as an outline; the real area is",
          xs6 and min(xs6) > 0.8055 and rw4['US-7010']['pin_records_not_drawn'] == 1)

    # stand-in circles in ANY form, the store's use flag, bad checksums: each drops ONE record, never the area
    def beside(ref, bad_rec):
        return park(ref, [record(ref.lower() + 'ok', 'lay1', [circle(0.81, 0.6, 0.004, 40)], credit='Good Office'), bad_rec])
    SMALL = [circle(0.8, 0.6, 0.0003, 16)]
    odd_recs = {'US-7035': record('sc1', 'lay1', SMALL, credit='Circle One', ring_is_stand_in_circle='true'),
                'US-7036': record('sc2', 'lay1', SMALL, credit='Circle Two', ring_is_stand_in_circle=1),
                'US-7037': record('sc3', 'lay1', SMALL, credit='Circle Three', circle=True),
                'US-7038': record('sc4', 'lay1', SMALL, credit='Circle Four', grade='point-circle'),
                'US-7039': record('sc5', 'lay1', SMALL, credit='Circle Five', circle='yes'),
                'US-7040': record('us1', 'lay1', SMALL, credit='Unused Office', use=False, use_why='proclamation line (not land)'),
                'US-7041': record('us2', 'lay1', SMALL, credit='Unused Office', use='false'),
                'US-7002': dict(record('ck1', 'lay1', SMALL, credit='Moved Point Office'), sha256='0' * 64),
                'US-7003': dict(line_record('ck2', 'lay1', [T4], credit='Moved Line Office'), line_sha256='0' * 64),
                'US-7004': dict(line_record('ck3', 'lay1', [T4], credit='Moved Line Office', publishable=False), line_points=3)}
    ro, oo = build('oddrecs', [beside(k, v) for k, v in odd_recs.items()] + [park('US-7042', [record('us3', 'lay1', [circle(0.81, 0.6, 0.004, 40)])])],
                   ws={'fmt': 'kpc-outline-store-index/4'})
    io, fo = feats_of(oo, 'US-ZZ'); bo = by_ref(fo)
    blobo = b''.join(gzip.decompress(q.read_bytes()) if q.suffix == '.gz' else q.read_bytes() for q in sorted((oo / 'US-ZZ').rglob('*')) if q.is_file())
    def only_good(ref):
        xs = [x for f in bo.get(ref, []) for l in drawn_lines([f]) for x, y in l]
        return bool(xs) and min(xs) > 0.8055 and bo[ref][0]['properties']['cr'] == ['Good Office']
    check('STAND-IN CIRCLES in any form (ring_is_stand_in_circle "true" or 1, record-level circle true or "yes", grade point-circle) '
          'are never drawn; the real area beside each is', all(only_good(k) for k in ('US-7035', 'US-7036', 'US-7037', 'US-7038', 'US-7039'))
          and b'Circle ' not in blobo)
    check("the store's use flag: use false (or anything but true) is never drawn, and the reason is private; use missing is drawn",
          only_good('US-7040') and only_good('US-7041') and 'do not use' in ro['held_records_reasons']['US-7040'] and 'proclamation' in ro['held_records_reasons']['US-7040']
          and b'Unused' not in blobo and 'US-7042' in bo)
    check('a BAD CHECKSUM on one record (rings, or a line, publishable or not) drops that record only; the area is built and passes',
          only_good('US-7002') and only_good('US-7003') and only_good('US-7004') and 'checksum' in ro['held_records_reasons']['US-7002']
          and 'line checksum' in ro['held_records_reasons']['US-7003'] and 'point count' in ro['held_records_reasons']['US-7004']
          and b'Moved' not in blobo and K.check(oo, 'US-ZZ', public=True) == [])

    # HOSTILE STRINGS in every field that could reach the public zone note: only allow-listed values ever pass
    EVIL = 'owner@example.com PRIVATE NOTE licence restricted https://x.invalid'
    hostile = []
    for i, (k, v) in enumerate([('boundary_rule', EVIL), ('corridor_from', EVIL), ('bank_status', EVIL), ('corridor_ft', EVIL),
                                ('corridor_ft', True), ('corridor_ft', -5), ('corridor_ft', 1e9), ('corridor_ft', float('nan')),
                                ('corridor_ft', '100'), ('corridor_from', ['centreline']), ('boundary_rule', {'x': 1}),
                                ('river_class', EVIL), ('corridor_rule', EVIL), ('bank_source', EVIL), ('line_extent', EVIL),
                                ('boundary_kind', EVIL), ('bank_near_parks', [EVIL]), ('corridor_m', EVIL)]):
        hostile.append(park(f'US-{7700 + i}', [line_record(f'h{i}', 'lay1', [wiggle_line(0.1, 0.1 + 0.02 * i, 0.12, 20)], credit='Trail Office',
                                                  **dict({kk: vv for kk, vv in TRAIL.items() if kk != k}, **{k: v}))]))
    rh, oh = build('hostile', hostile, ws={'fmt': 'kpc-outline-store-index/4'})
    ih, fh = feats_of(oh, 'US-ZZ')
    blobh = b''.join(gzip.decompress(q.read_bytes()) if q.suffix == '.gz' else q.read_bytes() for q in sorted((oh / 'US-ZZ').rglob('*')) if q.is_file())
    check(f'HOSTILE values in {len(hostile)} pass-through fields: none reaches a public file, every line is still drawn, '
          f'the bad values are counted privately ({rh["zone_values_dropped"]} dropped), and the public check passes',
          rh['parks_drawn'] == len(hostile) and not any(w in blobh for w in (b'PRIVATE NOTE', b'owner@', b'restricted', b'x.invalid', b'nan', b'NaN', b'1000000000'))
          and rh['zone_values_dropped'] == 11 and K.check(oh, 'US-ZZ', public=True) == []
          and all(K.zone_ok(z) for f in fh for z in f['properties'].get('zone') or []))
    # check --public catches a non-allow-listed value even if the builder were wrong: tamper one written part (and its INDEX sha)
    import hashlib as _h
    tam = tmp / 'out-tamper'; shutil.copytree(oh, tam)
    ixt = json.loads((tam / 'US-ZZ' / 'INDEX.json').read_text()); part = ixt['parts'][0]
    d = json.loads(gzip.decompress((tam / 'US-ZZ' / part[0]).read_bytes()))
    d['features'][0]['properties']['zone'] = [{'rule': 'trail_100ft', 'from': EVIL}]
    d['features'][1]['properties']['river_class'] = 'big river'
    b_ = K.gz(d); (tam / 'US-ZZ' / part[0]).write_bytes(b_); part[1] = _h.sha256(b_).hexdigest()[:12]; part[3] = len(b_)
    (tam / 'US-ZZ' / 'INDEX.json').write_text(json.dumps(ixt))
    pt = K.check(tam, 'US-ZZ', public=True)
    check('check --public refuses a zone value that is not on the allow-list, and a property that is not on the public list',
          any('allow-list' in x for x in pt) and any('not on the public list' in x for x in pt))

    lv = [park('US-7013', [record('a9', 'lay1', [circle(0.5, 0.5, 0.01, 900, wobble=0.05)], credit='State Parks Office'),
                      line_record('t9', 'lay3', [T1], credit='Trail Office')])]
    r9, o9 = build('fmt4lv', lv, ws={'fmt': 'kpc-outline-store-index/4'}, cap=40, mid_cap=30)
    i9, fs9 = feats_of(o9, 'US-ZZ')
    mid9 = json.loads(gzip.decompress((o9 / 'US-ZZ' / i9['mid']['US-7013'][0]).read_bytes()))['features'][0]['geometry']['coordinates'] if 'US-7013' in i9['mid'] else []
    fine9 = [l for t in (i9['fine'].get('US-7013') or {}).get('tiles', {})
             for l in json.loads(gzip.decompress((o9 / 'US-ZZ' / 'fine' / 'US-7013' / (t + '.geojson.gz')).read_bytes()))['features'][0]['geometry']['coordinates']]
    check('...an area simplified into middle and fine levels: the official line is in every level, never simplified '
          '(whole in the overview and the middle file; every one of its points in the fine pieces)',
          'US-7013' in i9['mid'] and 'US-7013' in i9['fine'] and fine9
          and len(has([l for f in fs9 for l in drawn_lines([f])], T1)) == 1 and len(has(mid9, T1)) == 1
          and all(any(abs(x - p[0]) <= 0.6e-5 and abs(y - p[1]) <= 0.6e-5 for l in fine9 for x, y in l) for p in T1))
    long_line = [park('US-7012', [line_record('t8', 'lay1', [wiggle_line(0.1, 0.5, 0.9, K.LINE_CAP + 10, amp=0.00001)], credit='Trail Office')])]
    r8, o8 = build('fmt4long', long_line, ws={'fmt': 'kpc-outline-store-index/4'})
    check("an official line over the points drawn as given keeps today's outline (never simplified into something else here)",
          'over the' in r8['fallback_reasons'].get('US-7012', '') and r8['parks_drawn'] == 0)
    gw = tmp / 'a-git-work-tree'; (gw / '.git').mkdir(parents=True)
    stg = tmp / 'st-prevgit'; write_store(stg, 'US-ZZ', [park('US-7014', [record('r1', 'lay1', C)])])
    try: K.build(stg, 'US-ZZ', gw / 'preview', preview=True, log=NOLOG); pg = False
    except K.DisplayError as ex: pg = 'git work tree' in str(ex)
    check('a PRIVATE PREVIEW is never written inside a git work tree (any folder with .git above it), and nothing is written there',
          pg and not (gw / 'preview').exists())

    # ---- re-grade: no free store text in public files except scrubbed names and credits; refs are POTA refs --------------
    base_blob = b''.join(gzip.decompress(q.read_bytes()) if q.suffix == '.gz' else q.read_bytes() for q in sorted((out / 'US-ZZ').rglob('*')) if q.is_file())
    check("public features carry no layer names ('layers' / 'won' are in the private report only; the loader never read them)",
          not any('layers' in f['properties'] or 'won' in f['properties'] for f in fs) and b'"layers"' not in base_blob and b'"won"' not in base_blob
          and LAY(rep, 'US-0001') == ['lay1'])
    EVIL2 = 'owner@example.com password=abc licence restricted <script>alert(1)</script>'
    def drawn_rec(key, **kw): return record(key, 'lay1', [circle(0.5, 0.5, 0.01, 40)], **kw)
    fr = [park('owner@example.com', [drawn_rec('x1')]), park('../../evil', [drawn_rec('x2')]), park('us-0001', [drawn_rec('x3')]),
          park('US-0001x', [drawn_rec('x4')]), park('US-01', [drawn_rec('x5')]),
          park('US-7801', [record('x6', EVIL2, [circle(0.5, 0.5, 0.01, 40)], credit='Good Office')], name=EVIL2),
          park('US-7802', [drawn_rec('x7', credit='<script>alert(1)</script>')]),
          park('US-7803', [drawn_rec('x8', credit='Town GIS password=abc')]), park('US-7804', [drawn_rec('x9', credit='Town GIS token 77')]),
          park('US-7805', [drawn_rec('x10', credit='Town GIS secret note')]), park('US-7806', [drawn_rec('x11', credit='Town GIS key=abc')]),
          park('US-7807', [drawn_rec('x12', credit='Town <b>GIS</b>')]),
          park('US-7808', [None, 'just a string', {'key': ['a', 'list']}, {'key': None}, drawn_rec('x13'),
                           drawn_rec('dupkey'), record('dupkey', 'lay2', [circle(0.9, 0.9, 0.01, 40)], publishable=False)])]
    rf, of_ = build('freetext', fr)
    i_f, f_f = feats_of(of_, 'US-ZZ'); b_f = by_ref(f_f)
    blobf = b''.join(gzip.decompress(q.read_bytes()) if q.suffix == '.gz' else q.read_bytes() for q in sorted((of_ / 'US-ZZ').rglob('*')) if q.is_file())
    check('a park ref that is not a POTA reference (e-mail, path, lower case, extra text, short) is left out of EVERY public file, '
          'not even listed as fallback; the private report lists it',
          not any(r in i_f['fallback'] or r in b_f for r in ('owner@example.com', '../../evil', 'us-0001', 'US-0001x', 'US-01'))
          and sorted(rf['refs_not_pota_left_out']) == sorted(['owner@example.com', '../../evil', 'us-0001', 'US-0001x', 'US-01'])
          and b'evil' not in blobf and b'0001x' not in blobf)
    check("a hostile park name is replaced by the park's ref; a hostile layer name is in no public file",
          'US-7801' in b_f and b_f['US-7801'][0]['properties']['name'] == 'US-7801' and b'script' not in blobf and b'password' not in blobf
          and b'owner@' not in blobf and b'restricted' not in blobf)
    check("credit lines with < or >, password, token, secret or key= are not plain: those records do not pass (today's outline)",
          all(r not in b_f and i_f['fallback'].get(r) == K.FALLBACK_CODE for r in ('US-7802', 'US-7803', 'US-7804', 'US-7805', 'US-7806', 'US-7807'))
          and not any(w in blobf for w in (b'Town GIS', b'<b>', b'token', b'secret', b'key=')))
    check('MALFORMED records (null, a string, a list key, no key, a key twice) are left out and counted, never a traceback; the good record draws',
          'US-7808' in b_f and rf['malformed_records_left_out'].get('US-7808') == 6 and b_f['US-7808'][0]['properties']['cr'] == ['Test Agency lay1']
          and 'malformed' in rf['held_records_reasons'].get('US-7808', '') and K.check(of_, 'US-ZZ', public=True) == [])

    def tamper(src, name, edit_feature=None, edit_index=None):
        """copy a written public copy, change one thing (re-listing the part's sha so only the change itself is judged)"""
        dst = tmp / ('out-tamper-' + name); shutil.copytree(src, dst)
        ixt = json.loads((dst / 'US-ZZ' / 'INDEX.json').read_text()); part = ixt['parts'][0]
        if edit_feature:
            d = json.loads(gzip.decompress((dst / 'US-ZZ' / part[0]).read_bytes())); edit_feature(d['features'][0]['properties'])
            b_ = K.gz(d); (dst / 'US-ZZ' / part[0]).write_bytes(b_); part[1] = hashlib.sha256(b_).hexdigest()[:12]; part[3] = len(b_)
        if edit_index: edit_index(ixt)
        (dst / 'US-ZZ' / 'INDEX.json').write_text(json.dumps(ixt))
        return K.check(dst, 'US-ZZ', public=True)
    cases = {'a hostile name': (lambda pr: pr.update(name='Park <script>'), None, 'name'),
             'a credit with password=': (lambda pr: pr.update(cr=['Town GIS password=abc']), None, 'credit'),
             'a credit with token': (lambda pr: pr.update(cr=['Town GIS token 99']), None, 'credit'),
             'a credit with key=': (lambda pr: pr.update(cr=['Town key=abc']), None, 'credit'),
             'a layers property': (lambda pr: pr.update(layers=['nhgranit']), None, 'public list'),
             'a ref that is not a POTA ref': (lambda pr: pr.update(ref='../../evil'), None, 'POTA'),
             'an INDEX key not on the list': (None, lambda ix: ix.update(note='from the store'), 'INDEX keys'),
             'an INDEX about text changed': (None, lambda ix: ix.update(about='owner notes'), 'fixed text'),
             'an INDEX fallback ref that is not a POTA ref': (None, lambda ix: ix['fallback'].update({'owner@example.com': K.FALLBACK_CODE}), 'POTA')}
    caught = {k: any(w in x for x in tamper(out, str(i), ef, ei)) for i, (k, (ef, ei, w)) in enumerate(cases.items())}
    check(f'check --public refuses each of {len(cases)} tampered public files (missed: {[k for k, v in caught.items() if not v] or "none"})', all(caught.values()))

    for iv, v in enumerate(('kpc-outline-store-index/04', ' kpc-outline-store-index/4 ', 'kpc-outline-store-index/\u0664',
                            'kpc-outline-store-index/4 ', 'KPC-OUTLINE-STORE-INDEX/4', 4)):
        try: build(f'fmtx{iv}', [park('US-7811', [record('r1', 'lay1', C)])], ws={'fmt': None, 'top': {'store_format_version': v}}); rx = False
        except K.DisplayError: rx = True
        check(f'public format parsing is exact: {v!r} is refused', rx)
    pvok, pvbad = [], []
    for v in (None, 'kpc-outline-store-index/3', 'kpc-outline-store-index/4'):
        try: build('pvok' + str(len(pvok)), [park('US-7812', [record('r1', 'lay1', C)])], ws={'fmt': None, 'top': {'store_format_version': v}} if v else {'fmt': None}, preview=True); pvok.append(True)
        except K.DisplayError: pvok.append(False)
    for v in ('4x', 'junk', 'kpc-outline-store-index/1', 'kpc-outline-store-index/2', 'kpc-outline-store-index/3.5', 'bogus/4', 'kpc-outline-store-index/0'):
        try: build('pvbad' + str(len(pvbad)), [park('US-7812', [record('r1', 'lay1', C)])], ws={'fmt': None, 'top': {'store_format_version': v}}, preview=True); pvbad.append(False)
        except K.DisplayError as ex: pvbad.append('reader knows' in str(ex) and 'no format' in str(ex))
    check('a PRIVATE PREVIEW reads only an index with no format, /3 or /4; every other format string (4x, junk, /1, /2, /3.5, bogus/4, /0) '
          'is refused with a message that says so', all(pvok) and all(pvbad))
    gw2 = tmp / 'another-git-tree'; (gw2 / '.git').mkdir(parents=True)
    st_r = tmp / 'st-reportgit'; write_store(st_r, 'US-ZZ', [park('US-7813', [record('r1', 'lay1', C)])])
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()) as so:
        rc = K.main(['build', '--store', str(st_r), '--area', 'US-ZZ', '--out', str(tmp / 'out-reportgit'), '--doubtful', str(dcsv),
                     '--precedence', str(tmp / 'prec.json'), '--report', str(gw2 / 'report.json')]) if (tmp / 'prec.json').write_text(json.dumps(PREC)) else 9
    check('--report inside a git work tree is refused, and nothing is written there', rc == 1 and 'git work tree' in so.getvalue() and not (gw2 / 'report.json').exists())

    # ---- must-fix 4: nothing private in the public files; credits per park --------------------------------------------------
    sec = [park('US-7030', [record('sgPRIVATEKEY77', 'lay1', C, cls='RESTRICTED IN WRITING')]), park('US-7031', [record('r2', 'lay1', [circle(0.8, 0.6, 0.01, 40)], publishable=False)]),
           park('US-7032', [record('r3', 'PAD-US', [circle(0.6, 0.8, 0.01, 40)], credit='National Park Service')]),
           park('US-7033', [record('r4', 'PAD-US', [circle(0.8, 0.8, 0.01, 40)], credit='US Forest Service')]),
           park('US-7034', [record('r5', 'lay2', [circle(0.6, 0.95, 0.01, 40)], credit='Town GIS (owner nancy.x@town.gov)')])]
    rs, os_ = build('secret', sec)
    raw = (os_ / 'US-ZZ' / 'INDEX.json').read_text()
    check('public INDEX.json carries no record keys, licence classes, reasons or store names (fallback = "kept today\'s outline" only)',
          'sgPRIVATEKEY77' not in raw and 'RESTRICTED' not in raw.upper() and 'WDPA' not in raw.upper() and set(json.loads(raw)['fallback'].values()) == {K.FALLBACK_CODE}
          and 'kpcstore' not in raw and 'made' not in json.loads(raw))
    check('...the detailed reasons are in the private report only', 'RESTRICTED IN WRITING' in rs['fallback_reasons'].get('US-7030', ''))
    f2 = by_ref(feats_of(os_, 'US-ZZ')[1])
    check('credits are per park: two PAD-US parks keep their own agency (no last-park-wins)',
          f2['US-7032'][0]['properties']['cr'] == ['National Park Service'] and f2['US-7033'][0]['properties']['cr'] == ['US Forest Service'])
    check('an e-mail and an owner note in a credit line are removed before it is written', f2['US-7034'][0]['properties']['cr'] == ['Town GIS'] and '@' not in raw)
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
    rm, om = build('far451', [park('US-7005', many)])
    check("451 tracts 30 km apart: check join (today's outline), even with more than 400 groups", 'check join' in rm['fallback_reasons'].get('US-7005', ''))
    am = [record('w1', 'lay1', [square(179.993, 52.0, 179.9995, 52.006, 5)]), record('e1', 'lay1', [square(-179.9995, 52.0, -179.993, 52.006, 5)])]
    ra, oa = build('am', [park('US-7001', am)])
    check('two tracts 1 km apart across 180 degrees are one park (not "20,000 km apart")', 'US-7001' not in ra['fallback_reasons'] and ra['rows'][0]['missing_m'] == 0)
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
    twin = record('tw1', 'stl', [square(0.4, 0.5, 0.44, 0.54, 10)])
    two = {'US-ZA': [park('US-0040', [record('w1', 'stl', [west]), record('cp1', 'stl', [copy_a]), shared]), park('US-0041', [record('o1', 'stl', [circle(0.15, 0.5, 0.01, 40)])]),
                     park('US-0042', [twin])],
           'US-ZB': [park('US-0040', [record('e1', 'stl', [east]), record('cp2', 'stl', [copy_b]), dict(shared)]), park('US-0042', [dict(twin)])]}
    r2, o2 = build('two', two, areas=['US-ZA', 'US-ZB'])
    ia, fa = feats_of(o2, 'US-ZA'); ib, fb = feats_of(o2, 'US-ZB')
    la = drawn_lines([f for f in fa if f['properties']['ref'] == 'US-0040']); lb = drawn_lines([f for f in fb if f['properties']['ref'] == 'US-0040'])
    on_line = [1 for l in la + lb for a, b in zip(l, l[1:]) if a[0] == 0.2 and b[0] == 0.2 and 0.1 < a[1] < 0.2 and 0.1 < b[1] < 0.2]
    check('A PARK ACROSS TWO STATES: no line where its own tracts meet at the state line, outer edges drawn, invariants pass',
          not on_line and ring_drawn([p for p in west if p[0] < 0.2], la + lb) and ring_drawn([p for p in east if p[0] > 0.2], la + lb)
          and {r['ref']: r for r in r2['rows']}['US-0040']['missing_m'] == 0)
    check("...two copies of one boundary with both tracts on the same side keep their line",
          len([p for l in la + lb for p in l if 0.25 - 1e-9 <= p[1] <= 0.3 + 1e-9 and 0.12 <= p[0] <= 0.18001]) > 20)
    check("...an area that holds only a copy of another area's tract keeps today's outline there, never an empty shape with no credit",
          'US-0042' in by_ref(fa) and by_ref(fa)['US-0042'][0]['properties']['cr'] == ['Test Agency stl'] and 'US-0042' not in by_ref(fb)
          and ib['fallback'].get('US-0042') == K.FALLBACK_CODE
          and not [f for f in fa + fb if not f['properties'].get('cr') or not f['geometry']['coordinates']])
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
        old = {'features': [{'type': 'Feature', 'properties': {'ref': r, 'g': 'official', 'old': True}, 'geometry': None} for r in ('US-0001', 'US-0012', 'US-0099', 'US-0040')]
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
              sorted(r.get('oldKept') or []) == ['US-0012', 'US-0040', 'US-0099'] and 'US-0098' not in (r.get('refs') or []))
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
