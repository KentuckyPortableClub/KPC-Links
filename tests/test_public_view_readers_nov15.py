#!/usr/bin/env python3
"""Owner rule 12 (2026-11-15: "if we dont have state then pad it is"; "Yes to cpad or any other pad ...we use what we got and better 1
wins out") in the KPC-Links store readers (store core 3.6.3 writes the public view: publish_view "public-records-only",
publish_view_records, publish_view_basis, publish_view_ratio >= 0.80, in the park AND its index entry; park_publishable stays false).
Offline; made-up squares and refs only.
 1. 2-fer reader (kpc_fers_store.py), PUBLIC run: a held park with a valid view is read from its view records ONLY; the held record's
    rings are never read (its coordinates are nowhere in what the reader gives); the park counts as read from publishable records.
 2. ...a held park with no view, a view the park and its index do not agree on, a view under 0.80, or a view that names a private
    record: the park needs the private store (as before), nothing read.
 3. ...a PRIVATE run is unchanged: every record is read.
 4. Map display copy (tools/kpc_display_copy.py): a held park with a valid view draws ONLY the view records; with no valid view it
    draws nothing (keeps today's outline); a fully publishable park is drawn as before; nothing of the held record is in the public files.
Run: python3 tests/test_public_view_readers_nov15.py"""
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
            'credit_line': 'USGS PAD-US' if pub else 'held', 'source': 'live', 'use': True, 'q': 6, 'rings': e, 'points': sum(len(x) // 2 for x in e), 'sha256': S.geometry_sha256(e)}


VIEW = {'publish_view': 'public-records-only', 'publish_view_basis': 'owner rule 12 (2026-11-15)', 'publish_view_ratio': 0.99, 'publish_view_credit': 'USGS PAD-US',
        'publish_view_layers': ['PAD-US']}


def held_park(ref, x0, view=True, **over):
    p = {'ref': ref, 'name': f'Test {ref}', 'grade': 'official', 'records': [rec(f'sgzh{ref[-1]}', [sq(HELD_X, 40.0 + x0, 0.01)], pub=False, layer='sgzh'),
                                                                               rec(f'7{ref[-1]}', [sq(-80.12, 40.0 + x0, 0.009)])]}
    if view: p.update(VIEW, publish_view_records=[f'7{ref[-1]}'])
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
    (d / f'index-{area}.json').write_text(json.dumps({'format': 1, 'store_format_version': S.STORE_FORMAT_VERSION, 'area': area, 'made': '2026-11-15T00:00:00-06:00',
                                                      'parks': idx, 'files': {fn: {'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()}}}), encoding='utf-8')


def main():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='kpc-view-readers-'))
    items = [held_park('US-9901', 0.0), held_park('US-9902', 0.1, view=False), held_park('US-9903', 0.2, publish_view_records=['74']),
             held_park('US-9904', 0.3, park={'publish_view_ratio': 0.5}, publish_view_ratio=0.5), held_park('US-9905', 0.4, park={'publish_view_records': ['sgzh5', '75']}, publish_view_records=['sgzh5', '75'])]
    build(tmp / 'store', 'US-ZZ', items)
    pub = S.Store(tmp / 'store', 45, today='2026-11-15', kind='public')
    g, left, why = pub.groups_for('US-9901', 'US-ZZ', ['sgzh1', '71'])
    flat = json.dumps(g)
    check(not why and g and len(g) == 1 and str(HELD_X) not in flat and '-80.12' in flat, f'1. public 2-fer run: a held park with a valid view is read from its PAD-US view record only ({why or "read"})')
    _, _, why_i, info = pub.examine('US-9901', 'US-ZZ', ['sgzh1', '71'], None, keep=False)
    check(not why_i and not info.get('private') and info.get('skipped', {}).get('outside the public view') == 1, '1. ...it counts as read from publishable records only (no private record used; one record outside the view not read)')
    for ref, ids, what in (('US-9902', ['sgzh2', '72'], 'no view'), ('US-9903', ['sgzh3', '73'], 'the park and its index name different views'),
                           ('US-9904', ['sgzh4', '74'], 'a view under 0.80'), ('US-9905', ['sgzh5', '75'], 'a view that names the held record')):
        g2, _, w2 = pub.groups_for(ref, 'US-ZZ', ids)
        check(g2 is None and 'needs the private store' in w2, f'2. public run, {what}: the park needs the private store, nothing read ({w2[:70]})')
    prv = S.Store(tmp / 'store', 45, today='2026-11-15', kind='private')
    g3, _, w3 = prv.groups_for('US-9901', 'US-ZZ', ['sgzh1', '71'])
    check(not w3 and len(g3) == 2 and str(HELD_X) in json.dumps(g3), '3. a private run is unchanged: every record is read')
    # 4. the map's display copy
    C1, C2 = FX.circle(0.6, 0.6, 0.01, 40), FX.circle(0.6, 0.8, 0.01, 40)
    held = FX.record('h1', 'sgzh', [FX.circle(0.6 + 0.123457, 0.6, 0.012, 40)], cls='RESTRICTED IN WRITING', publishable=False)
    v = FX.record('p1', 'PAD-US', [C1], cls='PUBLIC DOMAIN')
    parks = [FX.park('US-7101', [held, v]), FX.park('US-7102', [dict(held, key='h2'), dict(v, key='p2')]), FX.park('US-7103', [FX.record('r3', 'lay1', [C2])])]
    parks[0].update(VIEW, publish_view_records=['p1'])
    ov = {'US-7101': dict(VIEW, publish_view_records=['p1'], park_public=True), 'US-7102': {'park_public': False}, 'US-7103': {'park_public': True}}   # a 3.6.3 store
    FX.write_store(tmp / 'dstore', 'US-ZZ', parks, index_override=ov)
    (tmp / 'released').mkdir()
    rep = DC.build(tmp / 'dstore', ['US-ZZ'], tmp / 'dout', log=lambda *a: None, released=tmp / 'released')
    ix = json.loads((tmp / 'dout' / 'US-ZZ' / 'INDEX.json').read_text(encoding='utf-8'))
    pub_txt = ' '.join(gzip.decompress(f.read_bytes()).decode('utf-8', 'replace') for f in (tmp / 'dout').rglob('*.gz')) + json.dumps(ix)
    drawn = {r['ref'] for r in rep['rows'] if not r.get('failed')}
    check('US-7101' in drawn and 'US-7101' not in ix['fallback'] and 'US-7103' in drawn, f'4. map: the held park with a valid view is drawn (from its view), the fully publishable park as before ({sorted(drawn)})')
    check('US-7102' in ix['fallback'] and 'US-7102' not in drawn, '4. map: a held park with no view draws nothing (keeps today\'s outline), though its PAD-US record passes on its own')
    check('0.72346' not in pub_txt and 'sgzh' not in pub_txt and 'h1' not in [k for r in rep['rows'] for k in (r.get('layers') or [])] and DC.check(tmp / 'dout', 'US-ZZ', public=True) == [],
          '4. map: nothing of the held record (its points, layer, key) is in the public files; the public check passes')
    FX.write_store(tmp / 'dstore2', 'US-ZZ', [FX.park('US-7102', [dict(held, key='h2'), dict(v, key='p2')])])   # a store before 3.6.3: no park_public
    rep2 = DC.build(tmp / 'dstore2', ['US-ZZ'], tmp / 'dout2', log=lambda *a: None, released=tmp / 'released')
    check('US-7102' in {r['ref'] for r in rep2['rows'] if not r.get('failed')}, '4. map: a store written before core 3.6.3 (no park_public field) keeps the per-record rule exactly as before')
    import kpc_key_freeze as KFZ, kpc_preflight as PF
    log = (ROOT / 'docs/key-rules-change.txt').read_text(encoding='utf-8')
    o, n, ln = PF.changelog_hashes(log, 'fers')
    # Nov 15 (partial boundaries): the newest line is whatever the newest 2-fer change is; this test checks the shape of the
    # bookkeeping and that THIS change's own entries are still there (the newest hash is pinned by the newest change's own test).
    own = next((x for x in log.splitlines() if 'fers rules cb894783186f -> 8f5b753ce842' in x), '')   # Nov 16: this change's own line, kept
    check(n == KFZ.rules_hash('fers') and ln in log and 'APPROVED, decided_by KPC owner, 2026-11-15' in own and log[log.index(ln) + len(ln):].lstrip('\n').startswith('Why:'),
          f'the 2-fer hash moves by its newest changelog line, with its Why line (Nov 16: a line of another key may sit above it) ({o} -> {KFZ.rules_hash("fers")})')
    check('fers rules e402c3819224 -> cb894783186f APPROVED, decided_by KPC owner, 2026-11-15' in log,
          'the public-view change keeps its own changelog line (e402c3819224 -> cb894783186f)')
    sc = [x for x in json.loads((ROOT / '.github/fers-rule-scope.json').read_text())['changes'] if x['id'] == '2026-11-15-public-view']
    check(len(sc) == 1 and sc[0]['from'] == 'e402c3819224' and sc[0]['scope'] == 'none' and sc[0].get('approved') == 'APPROVED, decided_by KPC owner, 2026-11-15',
          'scope entry 2026-11-15-public-view (from e402c3819224, scope none, approved)')
    k = {x: KFZ.rules_hash(x) for x in ('us-key', 'ca-key', 'world-key')}
    # KPC owner, 2026-11-16 (handoff item 6): a hash this change did not move is its pinned value OR the newest declared changelog hash
    # (a later change may move it in its own declared line); not 'unchanged for ever'
    check(all(k[_x] in ({'us-key': 'd4ebfafce438', 'ca-key': 'ba480fa34fb6', 'world-key': '24cd942eca01'}[_x], __import__('kpc_preflight').newest_hash(_x)) for _x in k), f'US, CA and world rules hashes do not move, or moved only by a later declared line ({k})')
    print('ALL PASS' if not FAILS else f'SOME FAILED ({len(FAILS)})')
    return 0 if not FAILS else 1


if __name__ == '__main__':
    sys.exit(main())
