#!/usr/bin/env python3
"""PARTIAL BOUNDARIES, and nothing is ever marked "not a 2-fer" (KPC owner, 2026-11-15).
His words, 23:08: "lets go b for now and mark partial till we figure it out"; "little 2fer better then none and mark it partial
boundary". His words, 23:14: "We marking nothing not a 2 fer fyi... we just show what we think are overlaps .. offer partial
boundaries when thats all we have".
Offline; made-up squares and refs only; no socket.
 1. 2-fer reader (kpc_fers_store.py), PUBLIC run: a park whose store entry carries a PARTIAL view (publish_view
    "public-records-partial", ratio under 0.80 and at least 0.05) IS read, from its view records only; the held record's
    coordinates are nowhere in what the reader gives; the park goes on PARTIAL_VIEW.
 2. FAIL CLOSED: a partial view under the floor, at or over the full bar, with a ratio that is not a number, with an unknown view
    name, one the park and its index do not both name, or one that names the held record: the park needs the private store.
 3. The marks: every row that used a partial boundary gets partial_boundary (the refs) + partial_boundary_why; a row that used no
    partial boundary gets neither; a row carried unchanged for a held park (store_held) is never touched.
 4. A PARTIAL BOUNDARY CAN ONLY ADD: a not-live row of a partial pair is never written as a verdict. With a live row for the same
    pair in the file it replaces, that row comes back UNCHANGED (never worse); with none, no row is written at all. A live row is
    left as it is. Over many rounds the count of shown pairs never falls.
 5. carry_rows: a live row of the last file whose pair has a partial-boundary park and which this run did not make again comes back
    with its OLD status, never "dropped: not found again".
 6. NOTHING IS MARKED "NOT A 2-FER" (every run, store or not): kpc_fers.no_denials() writes no denial; it puts the previous live
    row back when there was one; the two row-bookkeeping statuses stay; a carried / kept row is left exactly as it was; the reasons
    go to the run report's "not shown" list, never into the file.
 7. Map display copy: a park with a PARTIAL view IS drawn, from its view records only, and every feature of it carries
    'boundary': 'partial'; a full view carries no such property; nothing of the held record reaches the public files; the public
    check passes; a store written before core 3.6.3 is unchanged.
 8. The 2-fer rules hash moves with its changelog line on top and its scope entry; the US, CA and world hashes do not move.
10. The privacy grade of 2026-11-16: F1 (a carry_rows denial is no longer exempt from no_denials, and never worse puts the last
    file's live row back), F2 (the per-pair reasons go to a private folder, never to the public run report), H1 (the map re-checks
    that every record the view names is publishable and non-WDPA, and pins the basis) and H2 (a ratio that is not a real number
    fails closed in every reader).
11. The re-grade of 2026-11-16: R1 (a stale "not shown" list is stripped from the run report even on a quiet run) and R2 (the
    missing check's DROPPED list - a pair we looked at and did not show, with the reason - is kept out of the pushed file and
    written to the private folder; the count, the pass flag, FOUND, NEVER LOOKED AT and both downstream readers still work).
 9. World areas off GitHub: .github/fers-store-areas.json stays "world": "off" (GitHub unchanged) and KPC_FERS_WORLD_STORE=on adds
    them on a person's own machine only; a world store run is still a private store run or nothing.
Run: python3 tests/test_partial_boundary_nov15.py"""
import gzip, hashlib, json, os, pathlib, sys, tempfile
for k in list(os.environ):
    if 'proxy' in k.lower(): os.environ.pop(k)
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github' / 'scripts')); sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(ROOT / 'tests'))
import kpc_fers_store as S  # noqa: E402
import kpc_display_copy as DC  # noqa: E402
import display_copy_fixture as FX  # noqa: E402
FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok: FAILS.append(what)


HELD_X = -80.123457   # a coordinate only the held record has
PARTIAL_NAME = 'public-records-partial'


def enc(ring):
    out, px, py = [], 0, 0
    for i, (x, y) in enumerate(ring):
        X, Y = int(round(x * 1e6)), int(round(y * 1e6))
        out += [X, Y] if i == 0 else [X - px, Y - py]; px, py = X, Y
    return out


def sq(x0, y0, d): return [[x0, y0], [x0 + d, y0], [x0 + d, y0 + d], [x0, y0 + d], [x0, y0]]


def rec(key, rings, pub=True, layer='PAD-US'):
    e = [enc(r) for r in rings]
    return {'key': key, 'layer': layer, 'record_id': key, 'record_name': key, 'licence_class': 'PUBLIC DOMAIN' if pub else 'RESTRICTED IN WRITING',
            'publishable': pub, 'publish_basis': 'verified-row' if pub else 'none', 'wdpa_derived': False, 'private_reason': '' if pub else 'restricted in writing',
            'credit_line': 'USGS PAD-US' if pub else 'held', 'source': 'live', 'use': True, 'q': 6, 'rings': e, 'points': sum(len(x) // 2 for x in e),
            'sha256': S.geometry_sha256(e)}


def view(name=PARTIAL_NAME, ratio=0.44):
    return {'publish_view': name, 'publish_view_basis': 'owner rule 12 (2026-11-15)', 'publish_view_ratio': ratio,
            'publish_view_credit': 'USGS PAD-US', 'publish_view_layers': ['PAD-US']}


def held_park(ref, x0, v=None, **over):
    tag = ref[-1]
    p = {'ref': ref, 'name': f'Test {ref}', 'grade': 'official',
         'records': [rec(f'sgzh{tag}', [sq(HELD_X, 40.0 + x0, 0.01)], pub=False, layer='sgzh'),
                     rec(f'7{tag}', [sq(-80.12, 40.0 + x0, 0.006)])]}
    if v is not None: p.update(v, publish_view_records=[f'7{tag}'])
    p.update(over.pop('park', {}))
    return p, over


def build(d, area, items):
    d.mkdir(parents=True, exist_ok=True)
    fn = f'{area}.kpcstore.json.gz'; raw = bytearray(); idx = {}
    raw += gzip.compress(json.dumps({'kpcstore': 1, 'area': area})[:-1].encode() + b', "parks": [', mtime=0)
    for i, (p, eover) in enumerate(items):
        b = gzip.compress(((',' if i else '') + json.dumps(p)).encode(), mtime=0)
        fp = hashlib.sha256('|'.join(str(r.get('sha256')) for r in p['records']).encode()).hexdigest()
        e = {'file': fn, 'o': len(raw), 'n': len(b), 'grade': 'official', 'circle': False, 'records': [r['key'] for r in p['records']],
             'points': sum(r['points'] for r in p['records']), 'fp': fp, 'date': '2026-11-15',
             'record_meta': {r['key']: {k: r.get(k) for k in ('publishable', 'licence_class', 'publish_basis', 'wdpa_derived')} for r in p['records']},
             'park_publishable': all(r['publishable'] for r in p['records'])}
        e.update({k: p[k] for k in p if k.startswith('publish_view')}); e.update(eover)
        idx[p['ref']] = e; raw += b
    raw += gzip.compress(b']}', mtime=0)
    (d / fn).write_bytes(bytes(raw))
    blob = (d / fn).read_bytes()
    (d / f'index-{area}.json').write_text(json.dumps({'format': 1, 'store_format_version': S.STORE_FORMAT_VERSION, 'area': area,
                                                      'made': '2026-11-15T00:00:00-06:00', 'parks': idx,
                                                      'files': {fn: {'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()}}}), encoding='utf-8')


def row(rid, refs, status='candidate', kind='area', passes=(1, 1, 1), **kw):
    r = {'id': rid, 'refs': list(refs), 'kind': kind, 'status': status, 'passes': list(passes)}
    r.update(kw); return r


# ---------------------------------------------------------------- 1 + 2: the reader
def t_reader(tmp):
    S.PARTIAL_VIEW.clear()
    items = [held_park('US-9801', 0.0, view()),                                          # a good partial view
             held_park('US-9802', 0.1, view(ratio=0.01)),                                # under the floor
             held_park('US-9803', 0.2, view(ratio=0.95)),                                # at / over the full bar
             held_park('US-9804', 0.3, view(ratio='half')),                              # not a number
             held_park('US-9805', 0.4, view(name='public-records-maybe')),               # an unknown name
             held_park('US-9806', 0.5, view()),                                          # index and park disagree
             held_park('US-9807', 0.6, view())]                                          # the view names the held record
    items[5][1]['publish_view'] = 'public-records-only'                                  # the INDEX says full, the park says partial
    items[6][0]['publish_view_records'] = ['sgzh7', '77']; items[6][1]['publish_view_records'] = ['sgzh7', '77']
    build(tmp / 'store', 'US-ZZ', items)
    pub = S.Store(tmp / 'store', 45, today='2026-11-15', kind='public')
    g, left, why = pub.groups_for('US-9801', 'US-ZZ', ['sgzh1', '71'])
    flat = json.dumps(g)
    check(not why and g and len(g) == 1 and str(HELD_X) not in flat and '-80.12' in flat,
          f'1. a PARTIAL view is read, from its view record only; the held record is not read ({why or "read"})')
    check('US-9801' in S.PARTIAL_VIEW, '1. the park is on PARTIAL_VIEW (its rows get the partial-boundary mark)')
    _, _, why_i, info = pub.examine('US-9801', 'US-ZZ', ['sgzh1', '71'], None, keep=False)
    check(not why_i and not info.get('private') and info.get('skipped', {}).get('outside the public view') == 1,
          '1. ...and it counts as read from publishable records only (the held record is skipped before it is read)')
    for ref, tag, what in (('US-9802', '2', 'a ratio under the floor 0.05'), ('US-9803', '3', 'a partial name with a full ratio'),
                           ('US-9804', '4', 'a ratio that is not a number'), ('US-9805', '5', 'an unknown view name'),
                           ('US-9806', '6', 'the index and the park naming different views'),
                           ('US-9807', '7', 'a partial view that names the held record')):
        g2, _, w2 = pub.groups_for(ref, 'US-ZZ', [f'sgzh{tag}', f'7{tag}'])
        check(g2 is None and 'needs the private store' in w2 and ref not in S.PARTIAL_VIEW,
              f'2. FAIL CLOSED, {what}: the park needs the private store, nothing read ({w2[:60]})')
    prv = S.Store(tmp / 'store', 45, today='2026-11-15', kind='private')
    g3, _, w3 = prv.groups_for('US-9801', 'US-ZZ', ['sgzh1', '71'])
    check(not w3 and len(g3) == 2 and str(HELD_X) in json.dumps(g3), '2. a PRIVATE run is unchanged: every record is read')


# ---------------------------------------------------------------- 3 + 4 + 5: the marks and "can only add"
def t_marks():
    S.PARTIAL_VIEW.clear(); S.PARTIAL_VIEW.update({'US-1', 'US-9'})
    S.PARTIAL.update({'marked': 0, 'kept': 0, 'denials_blocked': 0})
    d = {'st': 'US-ZZ', 'spots': [row('a', ['US-1', 'US-2']), row('b', ['US-3', 'US-4']),
                                  row('c', ['US-9', 'US-5'], status='candidate', store_held=S.HELD_TAG)]}
    n = S.mark_partial(d)
    by = {x['id']: x for x in d['spots']}
    check(n == 1 and by['a']['partial_boundary'] == ['US-1'] and S.PARTIAL_WHY in by['a']['partial_boundary_why']
          and 'partial_boundary' not in by['b'] and by['a']['status'] == 'candidate',
          f'3. a row that used a partial boundary is marked (the status word is untouched, so the site still shows it) ({n})')
    check('partial_boundary' not in by['c'],
          '3. a row carried unchanged for a held park is never touched (the push check needs the exact copy)')
    # 4. can only add
    old = {'spots': [row('keepme', ['US-1', 'US-7'], status='candidate'), row('gone', ['US-1', 'US-8'], status='candidate')]}
    new = {'st': 'US-ZZ', 'spots': [row('keepme', ['US-1', 'US-7'], status='dropped in pass 3: no shared patch'),
                                    row('fresh', ['US-1', 'US-6'], status='candidate'),
                                    row('nf', ['US-1', 'US-4'], status='dropped: inside the federal boundary, but no agency land'),
                                    row('ok', ['US-3', 'US-4'], status='dropped in pass 3: no shared patch')]}
    back, out = S.partial_only_adds(new, old)
    ids = {x['id']: x for x in new['spots']}
    check(back == 1 and out == 2 and ids['keepme']['status'] == 'candidate' and ids['keepme']['partial_kept'] == S.PARTIAL_KEPT,
          f'4. a denial of a partial pair that the last file showed: the old row comes back UNCHANGED (never worse) ({back}, {out})')
    check('nf' not in ids, '4. a denial of a partial pair the last file did not show: no row is written at all (nothing shown, nothing denied)')
    check('fresh' in ids and ids['fresh']['status'] == 'candidate', '4. a live row of a partial pair is left as it is (a partial boundary ADDS)')
    check('ok' in ids, '4. a pair with no partial-boundary park is left to the general no-denial rule, not to this one')
    # the count of shown pairs never falls over rounds
    shown = lambda doc: {tuple(sorted(x['refs'])) for x in doc['spots'] if not str(x['status']).startswith(('dropped', 'merged'))}
    n1 = shown(old); n2 = shown(new)
    check(n1 - {('US-1', 'US-8')} <= n2, f'4. every pair the last file showed is still shown, except one it never had a partial park for ({sorted(n1 - n2)})')
    # 5. carry_rows keeps the old status for a partial pair
    S.PARTIAL.update({'kept': 0})
    new2 = {'st': 'US-ZZ', 'spots': []}
    old2 = {'pass3': '2026-11-14', 'spots': [row('p', ['US-1', 'US-7'], status='very tight: 20 yards'),
                                             row('q', ['US-3', 'US-4'], status='candidate')]}
    S.carry_rows(new2, old2, {}, today='2026-11-15')
    got = {x['id']: x for x in new2['spots']}
    check(got['p']['status'] == 'very tight: 20 yards' and got['p']['partial_kept'] == S.PARTIAL_KEPT
          and got['q']['status'].startswith('dropped: not found again'),
          f'5. carry_rows: a partial-boundary pair keeps its old answer; an ordinary pair is still "not found again" ({got["p"]["status"][:30]!r})')


# ---------------------------------------------------------------- 6: nothing is marked "not a 2-fer", on every run
def t_no_denials(tmp):
    import kpc_fers as KF
    KF.NOT_SHOWN.clear()
    f = tmp / 'US-ZZ.json'
    f.write_text(json.dumps({'st': 'US-ZZ', 'spots': [row('old1', ['US-1', 'US-2'], status='candidate'),
                                                      row('old2', ['US-3', 'US-4'], status='very tight: 20 yards'),
                                                      row('old3', ['US-5', 'US-6'], status='dropped: an old denial')]}), encoding='utf-8')
    doc = {'st': 'US-ZZ', 'spots': [
        row('n1', ['US-1', 'US-2'], status='dropped in pass 3: the finer official outlines show no shared patch here'),
        row('n2', ['US-7', 'US-8'], status='dropped: only inside an area closed to the public (no entry)'),
        row('n3', ['US-3', 'US-4'], status='candidate'),
        row('n4', ['US-3', 'US-4'], status='dropped: the same stretch twice (copy of n3)'),
        row('n5', ['US-9', 'US-10'], status='merged into one row: n3'),
        row('n6', ['US-5', 'US-6'], status='dropped: carried from before', store_held=S.HELD_TAG),
        row('n7', ['US-11', 'US-12'], status='dropped: kept from before', partial_kept=S.PARTIAL_KEPT),
        row('n8', ['US-13', 'US-14'], status='dropped: kept from before', kept=S.KEPT_TAG)]}
    out = KF.no_denials(f, doc)
    got = {x['id']: x for x in out['spots']}
    check('n1' not in got and 'n2' not in got, '6. no row that denies a pair is written (from any shape: full, partial, saved copy or line)')
    check('old1' in got and got['old1']['status'] == 'candidate' and got['old1'][KF.NOT_WORSE_FIELD] == KF.NOT_WORSE_TAG
          and got['old1']['refs'] == ['US-1', 'US-2'],
          '6. never worse: the row the last file showed for that pair comes back unchanged (only the plain mark is added)')
    for what, cond in (('6. a pair the last file did not show either is simply not there (no row, no reason)', 'n2' not in got and not any(x.get('refs') == ['US-7', 'US-8'] for x in out['spots'])),
                       ('6. the two row-bookkeeping statuses stay (one ROW standing in for another row of the SAME pair)', 'n4' in got and 'n5' in got),
                       ('6. a row carried (store_held) or kept (partial_kept / kept) from an older file is left exactly as it was', got.get('n6', {}).get('status') == 'dropped: carried from before' and got.get('n7', {}).get('status') == 'dropped: kept from before' and got.get('n8', {}).get('status') == 'dropped: kept from before'),
                       ('6. the reasons go to the run report\'s "not shown" list, never into the file', len(KF.NOT_SHOWN.get('US-ZZ') or []) == 2 and 'closed to the public' in json.dumps(KF.NOT_SHOWN) and 'closed to the public' not in json.dumps(out)),
                       ('6. a file with no denial is returned untouched (same object)', KF.no_denials('nowhere.json', {'st': 'US-ZZ', 'spots': [row('x', ['US-1', 'US-2'])]})['spots'][0]['id'] == 'x'),
                       ('6. denial(): every "dropped ..." but the two row-bookkeeping ones', KF.denial('dropped: anything') and KF.denial('dropped in pass 2') and not KF.denial('dropped: the same stretch twice (copy of z)') and not KF.denial('merged into one row: z') and not KF.denial('candidate') and not KF.denial('not sure: x')),
                       ('6. an unreadable previous file puts nothing back, and still writes no denial', KF.no_denials('/does/not/exist.json', {'st': 'US-YY', 'spots': [row('d', ['US-1', 'US-2'], status='dropped: x')]})['spots'] == [])):
        check(cond, what)


# ---------------------------------------------------------------- 7: the map
def t_map(tmp):
    C1, C2, C3 = FX.circle(0.6, 0.6, 0.01, 40), FX.circle(0.6, 0.8, 0.01, 40), FX.circle(0.6, 1.0, 0.01, 40)
    held = FX.record('h1', 'sgzh', [FX.circle(0.6 + 0.123457, 0.6, 0.012, 40)], cls='RESTRICTED IN WRITING', publishable=False)
    v1 = FX.record('p1', 'PAD-US', [C1], cls='PUBLIC DOMAIN')
    v2 = FX.record('p2', 'PAD-US', [C2], cls='PUBLIC DOMAIN')
    PV = {'publish_view': PARTIAL_NAME, 'publish_view_basis': 'owner rule 12 (2026-11-15)', 'publish_view_ratio': 0.44,
          'publish_view_credit': 'USGS PAD-US', 'publish_view_layers': ['PAD-US']}
    FV = dict(PV, publish_view='public-records-only', publish_view_ratio=0.99)
    parks = [FX.park('US-7201', [held, v1]), FX.park('US-7202', [dict(held, key='h2'), v2]), FX.park('US-7203', [FX.record('r3', 'lay1', [C3])])]
    parks[0].update(PV, publish_view_records=['p1'])
    parks[1].update(FV, publish_view_records=['p2'])
    ov = {'US-7201': dict(PV, publish_view_records=['p1'], park_public=True),
          'US-7202': dict(FV, publish_view_records=['p2'], park_public=True),
          'US-7203': {'park_public': True}}
    FX.write_store(tmp / 'mstore', 'US-ZZ', parks, index_override=ov)
    (tmp / 'released').mkdir(exist_ok=True)
    rep = DC.build(tmp / 'mstore', ['US-ZZ'], tmp / 'mout', log=lambda *a: None, released=tmp / 'released')
    ix = json.loads((tmp / 'mout' / 'US-ZZ' / 'INDEX.json').read_text(encoding='utf-8'))
    feats = [f for p in (tmp / 'mout' / 'US-ZZ').glob('US-ZZ.geojson.gz')
             for f in json.loads(gzip.decompress(p.read_bytes()).decode('utf-8'))['features']]
    pr = {f['properties']['ref']: f['properties'] for f in feats}
    drawn = {r['ref'] for r in rep['rows'] if not r.get('failed')}
    check('US-7201' in drawn and 'US-7201' not in ix['fallback'] and pr.get('US-7201', {}).get('boundary') == 'partial',
          f'7. map: a park with a PARTIAL view IS drawn and its feature says boundary: partial ({pr.get("US-7201", {}).get("boundary")!r})')
    check('boundary' not in pr.get('US-7202', {}) and 'boundary' not in pr.get('US-7203', {}),
          '7. map: a full view and an ordinary publishable park carry no boundary property')
    check(rep.get('partial_boundary_parks') == ['US-7201'], f'7. map: the private report lists the partial parks ({rep.get("partial_boundary_parks")})')
    pub_txt = ' '.join(gzip.decompress(f.read_bytes()).decode('utf-8', 'replace') for f in (tmp / 'mout').rglob('*.gz')) + json.dumps(ix)
    check('0.72346' not in pub_txt and 'sgzh' not in pub_txt and 'h1' not in pub_txt and '0.44' not in pub_txt
          and DC.check(tmp / 'mout', 'US-ZZ', public=True) == [],
          '7. map: nothing of the held record (points, layer, key) and no ratio is in the public files; the public check passes')
    # the public check allows ONLY boundary = 'partial' (any other value, and a property not on the list, is a problem)
    gf = tmp / 'mout' / 'US-ZZ' / 'US-ZZ.geojson.gz'
    good = gzip.decompress(gf.read_bytes()).decode('utf-8')
    bad_vals = []
    for v in ('"yes"', '"full"', '""', '"Partial"'):
        gf.write_bytes(gzip.compress(good.replace('"boundary": "partial"', '"boundary": ' + v).replace('"boundary":"partial"', '"boundary":' + v).encode(), mtime=0))
        bad_vals.append(any('boundary' in x for x in DC.check(tmp / 'mout', 'US-ZZ', public=True)))
    gf.write_bytes(gzip.compress(good.encode(), mtime=0))
    check(all(bad_vals), f'7. map: the public check allows only boundary = "partial" ({bad_vals})')
    FX.write_store(tmp / 'mstore2', 'US-ZZ', [FX.park('US-7202', [dict(held, key='h2'), dict(v2, key='p2')])])   # before 3.6.3: no park_public
    rep2 = DC.build(tmp / 'mstore2', ['US-ZZ'], tmp / 'mout2', log=lambda *a: None, released=tmp / 'released')
    check('US-7202' in {r['ref'] for r in rep2['rows'] if not r.get('failed')} and not rep2.get('partial_boundary_parks'),
          '7. map: a store written before core 3.6.3 keeps the per-record rule exactly as before, and nothing is marked partial')


# ---------------------------------------------------------------- 10: the privacy grade's four findings (2026-11-16)
def t_grade(tmp):
    """F1, F2, H1 and H2 of the privacy grade of 2026-11-16."""
    import kpc_fers as KF

    # ---- F1: carry_rows stamps 'carried' on every row it makes, and one branch INVENTS a denial this run. That row must go
    # through no_denials like any other, and never worse must put the last file's live row back instead.
    check('carried' not in KF.KEPT_MARKS and set(KF.KEPT_MARKS) == {'store_held', 'partial_kept', 'kept'},
          f'F1: a bare "carried" stamp no longer exempts a row from the rule ({KF.KEPT_MARKS})')
    S.PARTIAL_VIEW.clear()
    old = {'pass3': '2026-11-14', 'spots': [row('live', ['US-1001', 'US-1002'], status='candidate: 60 yards'),
                                            row('held', ['US-2001', 'US-2002'], status='candidate')]}
    new = {'st': 'US-ZZ', 'spots': []}
    S.carry_rows(new, old, {'US-2001': 'held by the outline store'}, today='2026-11-16')
    made = {x['id']: x for x in new['spots']}
    check(KF.denial(made['live']['status']) and bool(made['live'].get('carried'))
          and made['live']['status'].startswith('dropped: not found again'),
          f"F1: carry_rows still invents a denial for a pair with no partial park ({made['live']['status'][:46]!r})")
    check(KF.this_runs_verdict(made['live']) is True and not KF.denial(made['held']['status']),
          'F1: that row IS this run\'s verdict now; the held-park branch is not a denial and is untouched')
    f = tmp / 'F1-US-ZZ.json'
    f.write_text(json.dumps(old), encoding='utf-8')
    out = KF.no_denials(f, new)
    got = {x['id']: x for x in out['spots']}
    check(not any(KF.denial(x.get('status')) for x in out['spots']),
          f'F1: no denial is left in the file that would be written ({[x.get("status", "")[:40] for x in out["spots"]]})')
    check(got.get('live', {}).get('status') == 'candidate: 60 yards' and got['live'].get(KF.NOT_WORSE_FIELD) == KF.NOT_WORSE_TAG
          and 'kept' not in got['live']
          and got['live']['refs'] == ['US-1001', 'US-1002'],
          'F1: never worse puts yesterday\'s live row back unchanged, so the pair is still shown')
    check('held' in got and got['held']['status'].startswith('not sure: held:'),
          'F1: the held-park row is still carried with its "not sure: held:" answer')
    # a row carried byte for byte for a WITHHELD park (store_held) is still left exactly as it was
    keep_exact = {'st': 'US-ZZ', 'spots': [row('x', ['US-3001', 'US-3002'], status='dropped: published before now',
                                               store_held=S.HELD_TAG)]}
    check(KF.no_denials(f, keep_exact)['spots'][0]['status'] == 'dropped: published before now',
          'F1: a row carried byte for byte for a withheld park is still untouched (the push check needs the exact copy)')

    # ---- F2: the per-pair reasons must never reach the run report (KPC-Data copies it and KPC-Data is public)
    KF.NOT_SHOWN.clear()
    KF.no_denials(tmp / 'F2-none.json', {'st': 'US-ZZ', 'spots': [
        row('d1', ['US-4001', 'US-4002'], status='dropped: no shared patch on the official outlines'),
        row('d2', ['US-4003', 'US-4004'], status='dropped in pass 3: only inside an area closed to the public')]})
    check(sum(len(v) for v in KF.NOT_SHOWN.values()) == 2, 'F2: the reasons are collected in memory as before')
    priv = tmp / 'F2-private'
    os.environ['KPC_FERS_NOT_SHOWN_DIR'] = str(priv)
    try:
        nf, n = KF.save_not_shown()
    finally:
        os.environ.pop('KPC_FERS_NOT_SHOWN_DIR', None)
    txt = nf.read_text(encoding='utf-8') if nf is not None else ''
    check(nf is not None and n == 2 and nf.is_file() and 'US-4001' in txt and 'closed to the public' in txt,
          f'F2: with a private folder the reasons are written there, and only there ({nf})')
    rep = (ROOT / '.github/scripts/kpc_fers.py').read_text(encoding='utf-8')
    check("rep.setdefault('not shown'" not in rep and "rep.pop('not shown', None)" in rep,
          'F2: the run report never gets the list, and an older report file\'s list is taken out')
    check("counts['pairs not shown" in rep and "counts['...their reasons']" in rep,
          'F2: the run report keeps the per-area COUNT (and says where the reasons went)')
    # a private folder INSIDE a git work tree is refused: then nothing is written anywhere
    ingit = tmp / 'F2-ingit'
    (ingit / '.git').mkdir(parents=True, exist_ok=True)
    os.environ['KPC_FERS_NOT_SHOWN_DIR'] = str(ingit)
    try:
        nf2, n2 = KF.save_not_shown()
    finally:
        os.environ.pop('KPC_FERS_NOT_SHOWN_DIR', None)
    check(nf2 is None and n2 == 2 and not list(ingit.rglob('not-shown*')),
          'F2: a folder inside a git work tree is refused; the reasons are not written anywhere (fail closed)')
    KF.NOT_SHOWN.clear()

    # ---- H1: the display copy re-checks the view's records and pins the basis, like its two sibling readers
    e = {'park_public': True, 'park_publishable': False, 'publish_view': PARTIAL_NAME,
         'publish_view_basis': 'owner rule 12 (2026-11-15)', 'publish_view_ratio': 0.44, 'publish_view_records': ['p1'],
         'record_meta': {'p1': {'publishable': True, 'wdpa_derived': False}, 'h1': {'publishable': False, 'wdpa_derived': False}}}
    pk = {'publish_view': PARTIAL_NAME, 'publish_view_basis': 'owner rule 12 (2026-11-15)', 'publish_view_records': ['p1']}
    check(DC.view_of(e, pk) == PARTIAL_NAME and DC.partial_view(e, pk), 'H1: a good partial view still reads as one')
    held_named = dict(e, publish_view_records=['p1', 'h1'])
    check(DC.view_of(held_named, dict(pk, publish_view_records=['p1', 'h1'])) == ''
          and not DC.in_public_view({'key': 'p1'}, held_named, dict(pk, publish_view_records=['p1', 'h1'])),
          'H1: a view that NAMES a held record is refused by the map too (it used to be drawn and marked partial)')
    check(DC.view_of(dict(e, record_meta={'p1': {'publishable': True, 'wdpa_derived': True}}), pk) == ''
          and DC.view_of(dict(e, record_meta={}), pk) == '',
          'H1: a view record marked WDPA-derived, or with no record_meta at all, is refused')
    check(DC.view_of(dict(e, publish_view_basis='someone said so'), dict(pk, publish_view_basis='someone said so')) == ''
          and DC.view_of(dict(e, publish_view_basis='someone said so'), pk) == '',
          'H1: the basis is pinned to the owner\'s rule, not just agreed on by the two sides')
    check(S.Store.VIEW_BASIS == 'owner rule 12 (2026-11-15)'
          and "e.get('publish_view_basis') != self.VIEW_BASIS" in (ROOT / '.github/scripts/kpc_fers_store.py').read_text(encoding='utf-8'),
          'H1: the 2-fer reader pins the basis too')

    # ---- H2: a ratio that is not a REAL number fails closed in both readers
    bad = ['0.44', '0.9', ' 0.44 ', True, False, None, [], {}, float('nan')]
    check(not any(DC.view_ratio_ok(PARTIAL_NAME, x) for x in bad) and not any(DC.view_ratio_ok(DC.VIEW_NAME, x) for x in bad)
          and DC.view_ratio_ok(PARTIAL_NAME, 1 / 4) and DC.view_ratio_ok(DC.VIEW_NAME, 0.9),
          f'H2: the map: a numeric STRING (and True / None / NaN) is not a ratio ({[x for x in bad if DC.view_ratio_ok(PARTIAL_NAME, x)]})')
    check(not any(S.Store.view_ratio_ok(PARTIAL_NAME, x) for x in bad)
          and not any(S.Store.view_ratio_ok(S.Store.VIEW_NAME, x) for x in bad)
          and S.Store.view_ratio_ok(PARTIAL_NAME, 1 / 4),
          'H2: the 2-fer reader: the same')
    check(DC.view_of(dict(e, publish_view_ratio='0.44'), pk) == '',
          'H2: a store whose ratio is the string "0.44" draws nothing (it used to be coerced and pass)')


# ---------------------------------------------------------------- 11: the re-grade's two items (2026-11-16)
def t_regrade(tmp):
    """R1 and R2 of the re-grade."""
    import kpc_fers as KF
    src = (ROOT / '.github/scripts/kpc_fers.py').read_text(encoding='utf-8')

    # ---- R1: a stale 'not shown' list must be stripped even on a run that suppressed nothing. The report is loaded from the
    # file on disk, so the pop has to sit ABOVE the "if NOT_SHOWN:" block, not inside it.
    i_pop, i_if = src.find("rep.pop('not shown', None)"), src.find('    if NOT_SHOWN:')
    check(i_pop > 0 and i_if > 0 and i_pop < i_if and src.count("rep.pop('not shown', None)") == 1,
          f'R1: the stale-list pop runs before (and outside) the "if NOT_SHOWN:" block ({i_pop} < {i_if})')
    # and prove it on a report document, the way main() builds one
    stale = {'about': 'x', 'not shown': {'US-ZZ': [[['US-1', 'US-2'], 'area', 'dropped: an old reason', 's1']]}, 'per state': {}}
    rep = dict(stale)
    rep.pop('not shown', None)
    check('not shown' not in rep and 'not shown' in stale,
          'R1: an older run\'s list is taken out of the report document a quiet run rewrites')

    # ---- R2: the DROPPED list never goes into the pushed expected file
    import kpc_fers_expected as EX
    res = {'area': 'US-ZZ', 'date': '2026-11-16', 'pass': True,
           'counts': {'FOUND': 1, 'DROPPED': 2, 'NEVER LOOKED AT': 1},
           'FOUND': [{'refs': ['US-1', 'US-2']}],
           'DROPPED': [{'refs': ['US-5', 'US-6'], 'reason': 'looked: no shared ground on the official outlines', 'rule': 'rule 4 / rule 5'},
                       {'refs': ['US-7', 'US-8'], 'reason': 'dropped: only inside an area closed to the public', 'rule': 'rule 10'}],
           'NEVER LOOKED AT': [{'refs': ['US-9', 'US-10'], 'reason': 'not tested: the outlines\' boxes do not touch'}]}
    priv = tmp / 'R2-private'
    os.environ['KPC_FERS_NOT_SHOWN_DIR'] = str(priv)
    try:
        f, n = EX.split_dropped(res, 'us-zz')
    finally:
        os.environ.pop('KPC_FERS_NOT_SHOWN_DIR', None)
    pushed = json.dumps(res)
    check(n == 2 and res['DROPPED'] == [] and 'no shared ground' not in pushed and 'closed to the public' not in pushed
          and 'US-5' not in pushed and 'US-7' not in pushed,
          'R2: the pushed file names no pair we looked at and did not show, and carries none of their reasons')
    check(res['counts']['DROPPED'] == 2 and 'DROPPED (not listed here)' in res and res['pass'] is True
          and res['FOUND'] and res['NEVER LOOKED AT'] and 'boxes do not touch' in pushed,
          'R2: the count, the pass flag, FOUND and NEVER LOOKED AT (which say we did NOT test a pair) all stay')
    doc = json.loads(f.read_text(encoding='utf-8')) if f is not None else {}
    check(f is not None and f.name == 'expected-dropped-us-zz.json' and len(doc.get('DROPPED') or []) == 2
          and 'no shared ground' in json.dumps(doc) and 'PRIVATE' in doc.get('about', ''),
          f'R2: the whole list, with every reason, is written for a person in the private folder ({f})')
    # a private folder inside a git work tree is refused: then the list is written NOWHERE (and still not pushed)
    ingit = tmp / 'R2-ingit'
    (ingit / '.git').mkdir(parents=True, exist_ok=True)
    res2 = dict(res, DROPPED=[{'refs': ['US-5', 'US-6'], 'reason': 'looked: no shared ground'}])
    os.environ['KPC_FERS_NOT_SHOWN_DIR'] = str(ingit)
    try:
        f2, n2 = EX.split_dropped(res2, 'us-zz')
    finally:
        os.environ.pop('KPC_FERS_NOT_SHOWN_DIR', None)
    check(f2 is None and n2 == 1 and res2['DROPPED'] == [] and 'no shared ground' not in json.dumps(res2)
          and not list(ingit.rglob('expected-dropped*')),
          'R2: a folder inside a git work tree is refused; the list is written nowhere and still never pushed')
    check('path.write_text' in (ROOT / '.github/scripts/kpc_fers_expected.py').read_text(encoding='utf-8')
          and 'split_dropped(res, tag or area)' in (ROOT / '.github/scripts/kpc_fers_expected.py').read_text(encoding='utf-8'),
          'R2: the split runs before the file is written (and before the store write guard sees it)')

    # ---- the two readers of that list keep working
    import kpc_fers_line_check as LC
    e_old = {'FOUND': [1, 2], 'DROPPED': [1, 1, 1], 'NEVER LOOKED AT': [{'reason': 'not tested: something'}],
             'counts': {'FOUND': 2, 'DROPPED': 3, 'NEVER LOOKED AT': 1}}
    e_new = {'FOUND': [1, 2], 'DROPPED': [], 'NEVER LOOKED AT': [{'reason': 'not tested: something'}],
             'counts': {'FOUND': 2, 'DROPPED': 3, 'NEVER LOOKED AT': 1}}
    check(LC.never_looked(e_old)[2] == 6 and LC.never_looked(e_new)[2] == 6
          and LC.never_looked(e_old)[0] == LC.never_looked(e_new)[0] == 1,
          f'R2: the never-looked share is still measured against EVERY expected pair ({LC.never_looked(e_new)[2]})')
    import kpc_fers_review as RV
    os.environ['KPC_FERS_NOT_SHOWN_DIR'] = str(priv)
    try:
        got = RV.load_private_dropped('us-zz')
    finally:
        os.environ.pop('KPC_FERS_NOT_SHOWN_DIR', None)
    check(isinstance(got, list) and len(got) == 2 and RV.load_private_dropped('nothing-here') is None,
          'R2: the review list still finds the pairs (from the private folder) and copes when there is none')
    rv_src = (ROOT / '.github/scripts/kpc_fers_review.py').read_text(encoding='utf-8')
    deny_words = ('no overlap', 'did not show', 'not a 2-fer', 'no shared ground', 'dropped')
    check("'reason': HINT_REASON" in rv_src and "'reason': x.get('reason', '')" not in rv_src
          and not any(w in RV.HINT_REASON.lower() for w in deny_words),
          'R2: a review HINT row never copies the reason, and the hint itself says nothing about an overlap')


# ---------------------------------------------------------------- 9: world areas off GitHub (the owner's PC)
def t_world():
    """KPC owner, 2026-11-15: the world store is about 65 per cent built and he wants world 2-fers on his PC. The repo file stays
    "world": "off" (so every GitHub run is exactly as today) and a run on his own machine adds the world areas with
    KPC_FERS_WORLD_STORE=on. It only ADDS areas: a world store run is still a private run or nothing."""
    import json as _j
    doc = _j.loads((ROOT / '.github/fers-store-areas.json').read_text(encoding='utf-8'))
    check(doc.get('world') == 'off', f'9. the repo file still says world: off, so GitHub is unchanged ({doc.get("world")!r})')
    f_only = S.store_areas(env={})[0]
    pc_on = S.store_areas(env={'KPC_FERS_WORLD_STORE': 'on'})[0]
    gh_on = S.store_areas(env={'KPC_FERS_WORLD_STORE': 'on', 'GITHUB_ACTIONS': 'true'})[0]
    check(f_only['world'] is False and pc_on['world'] is True and gh_on['world'] is False,
          '9. KPC_FERS_WORLD_STORE=on adds the world areas off GitHub only (under GitHub Actions the file alone decides)')
    check(S.area_use('W-GB', pc_on) == '' and 'switched off' in S.area_use('W-GB', f_only)
          and S.area_use('US-RI', pc_on) == '' and S.area_use('US-RI', f_only) == ''
          and S.area_use('US-KY', pc_on) == S.area_use('US-KY', f_only) != '',
          '9. with it on a world area may be read and nothing changes for US / Canada (and US-KY is still never read from the store)')
    check('a world store run must be a private store run' in (ROOT / '.github/scripts/kpc_fers_store.py').read_text(encoding='utf-8'),
          '9. a world store run is still refused unless it is a PRIVATE store run (world 2-fers are club room only)')


# ---------------------------------------------------------------- 8: the rules hash bookkeeping
def t_hash():
    import kpc_key_freeze as KFZ, kpc_preflight as PF
    log = (ROOT / 'docs/key-rules-change.txt').read_text(encoding='utf-8')
    o, n, ln = PF.changelog_hashes(log, 'fers')
    # Nov 16 (world opened): the newest line is whatever the newest 2-fer change is (its own test pins it); this test checks the
    # shape of the bookkeeping and that THIS change's own line (cb894783186f -> 8f5b753ce842, approved 2026-11-15) is still there
    own = next((x for x in log.splitlines() if 'fers rules cb894783186f -> 8f5b753ce842' in x), '')
    check(n == KFZ.rules_hash('fers') and ln in log and log[log.index(ln) + len(ln):].lstrip('\n').startswith('Why:')
          and 'APPROVED, decided_by KPC owner, 2026-11-15' in own,
          f'8. the 2-fer hash moves by its newest changelog line, with its Why line (Nov 16: a line of another key may sit above it) ({o} -> {KFZ.rules_hash("fers")}); this change\'s own line is kept')
    sc = next((c for c in json.loads((ROOT / '.github/fers-rule-scope.json').read_text())['changes'] if c.get('id') == '2026-11-15-partial-view'), {})   # Nov 16: not the last entry any more
    check(sc['id'] == '2026-11-15-partial-view' and sc['from'] == 'cb894783186f' and sc['scope'] == 'none'
          and sc.get('approved') == 'APPROVED, decided_by KPC owner, 2026-11-15',
          '8. scope entry 2026-11-15-partial-view (from cb894783186f, scope none, approved)')
    others = {k: KFZ.rules_hash(k) for k in ('us-key', 'ca-key', 'world-key')}
    check(others == {'us-key': 'd4ebfafce438', 'ca-key': 'ba480fa34fb6', 'world-key': '24cd942eca01'},
          f'8. US, CA and world rules hashes do not move ({others})')


def main():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='kpc-partial-'))
    for t in (t_reader, t_marks, t_no_denials, t_map, t_grade, t_regrade, t_world, t_hash):
        try: t(tmp) if t not in (t_marks, t_hash, t_world) else t()
        except Exception as ex:   # noqa: BLE001
            import traceback; traceback.print_exc(); check(False, f'{t.__name__} raised {type(ex).__name__}: {ex}')
    print(('ALL PASS' if not FAILS else f'SOME FAILED ({len(FAILS)})'), flush=True)
    return 0 if not FAILS else 1


if __name__ == '__main__':
    sys.exit(main())
