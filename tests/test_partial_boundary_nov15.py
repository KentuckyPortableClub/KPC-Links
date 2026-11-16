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
        row('n7', ['US-11', 'US-12'], status='dropped: kept from before', partial_kept=S.PARTIAL_KEPT)]}
    out = KF.no_denials(f, doc)
    got = {x['id']: x for x in out['spots']}
    check('n1' not in got and 'n2' not in got, '6. no row that denies a pair is written (from any shape: full, partial, saved copy or line)')
    check('old1' in got and got['old1']['status'] == 'candidate' and got['old1']['kept'] == KF.NOT_WORSE_TAG
          and got['old1']['refs'] == ['US-1', 'US-2'],
          '6. never worse: the row the last file showed for that pair comes back unchanged (only the plain mark is added)')
    for what, cond in (('6. a pair the last file did not show either is simply not there (no row, no reason)', 'n2' not in got and not any(x.get('refs') == ['US-7', 'US-8'] for x in out['spots'])),
                       ('6. the two row-bookkeeping statuses stay (one ROW standing in for another row of the SAME pair)', 'n4' in got and 'n5' in got),
                       ('6. a row carried (store_held) or kept (partial_kept) from an older file is left exactly as it was', got.get('n6', {}).get('status') == 'dropped: carried from before' and got.get('n7', {}).get('status') == 'dropped: kept from before'),
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
    check(o == 'cb894783186f' and n == KFZ.rules_hash('fers') and log.startswith(ln)
          and 'APPROVED, decided_by KPC owner, 2026-11-15' in ln and log.split('\n')[1].startswith('Why:'),
          f'8. the 2-fer hash moves by the newest changelog line, on top, with its Why line (cb894783186f -> {KFZ.rules_hash("fers")})')
    sc = json.loads((ROOT / '.github/fers-rule-scope.json').read_text())['changes'][-1]
    check(sc['id'] == '2026-11-15-partial-view' and sc['from'] == 'cb894783186f' and sc['scope'] == 'none'
          and sc.get('approved') == 'APPROVED, decided_by KPC owner, 2026-11-15',
          '8. scope entry 2026-11-15-partial-view (from cb894783186f, scope none, approved)')
    others = {k: KFZ.rules_hash(k) for k in ('us-key', 'ca-key', 'world-key')}
    check(others == {'us-key': 'd4ebfafce438', 'ca-key': 'ba480fa34fb6', 'world-key': '158325de87ce'},
          f'8. US, CA and world rules hashes do not move ({others})')


def main():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='kpc-partial-'))
    for t in (t_reader, t_marks, t_no_denials, t_map, t_world, t_hash):
        try: t(tmp) if t not in (t_marks, t_hash, t_world) else t()
        except Exception as ex:   # noqa: BLE001
            import traceback; traceback.print_exc(); check(False, f'{t.__name__} raised {type(ex).__name__}: {ex}')
    print(('ALL PASS' if not FAILS else f'SOME FAILED ({len(FAILS)})'), flush=True)
    return 0 if not FAILS else 1


if __name__ == '__main__':
    sys.exit(main())
