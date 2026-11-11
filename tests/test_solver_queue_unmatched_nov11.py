#!/usr/bin/env python3
"""Nov 11 (KPC owner, 2026-11-11), job 3 part 1: every record or park the master tool cannot match lands in data/outlines/solver-queue/ with a
reason, deduped, and a queue file is written only when its bytes change (no noisy bot commits).
  trim:    a record matched by id but with no usable outline; a record that names a POTA ref the park list does not hold (same country only)
  collect: every park the live key knows that has no outline in the master and is in no layer queue -> US-ST.nomatch.csv (no layer / joined but not kept)
Nothing here contacts any server."""
import csv, json, pathlib, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_master as M  # noqa: E402
import kpc_master_cli as CLI  # noqa: E402
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


def sq(sqdir):
    return {p.name: list(csv.DictReader(open(p, newline='', encoding='utf-8'))) for p in sorted(pathlib.Path(sqdir).glob('*.csv'))}


SQUARE = {'type': 'Polygon', 'coordinates': [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}
PARKS = [('US-0001', 'Alpha State Park', 0.5, 0.5), ('US-0002', 'Beta State Park', 5.0, 5.0)]
CFG = {'id_fields': ['POTA'], 'name_fields': ['NAME'], 'record_id_field': 'OID', 'g': 'official', 'agency': 'a', 'layer_url': 'file:x', 'license': ''}
FEATS = [
    {'properties': {'OID': 1, 'NAME': 'Alpha State Park', 'POTA': 'US-0001'}, 'geometry': SQUARE},   # good, by id
    {'properties': {'OID': 2, 'NAME': 'Beta State Park', 'POTA': 'US-0002'}, 'geometry': None},      # matched by id, no outline
    {'properties': {'OID': 3, 'NAME': 'Gone State Park', 'POTA': 'US-9999'}, 'geometry': SQUARE},    # names a ref the list does not hold
    {'properties': {'OID': 4, 'NAME': 'Other Land', 'POTA': 'CA-0007'}, 'geometry': SQUARE},         # another country's ref: not this run's miss
    {'properties': {'OID': 5, 'NAME': 'Gone State Park', 'POTA': 'US-9999'}, 'geometry': SQUARE},    # the same unknown ref again: one row
]
recs, queue = M.trim(PARKS, FEATS, CFG, '2026-11-11')
check('trim: the good record is kept, the no-outline one is not', sorted(recs) == ['US-0001'])
by = {(q['ref'], q['why']): q for q in queue}
check('trim: matched by id but no usable outline -> queued with that reason', ('US-0002', M.WHY_NO_GEOM) in by and by[('US-0002', M.WHY_NO_GEOM)]['candidates'] == '2')
check('trim: a record naming an unknown POTA ref of the same country -> queued once', [q['ref'] for q in queue].count('US-9999') == 1 and ('US-9999', M.WHY_UNKNOWN_REF) in by)
check("trim: another country's ref is not queued", not any(q['ref'] == 'CA-0007' for q in queue))
check('trim: rows carry only the six queue columns', all(list(q) == M.QUEUE_FIELDS for q in queue))
# name + pin path: matched by name with the pin inside, but the record has no outline
recs2, q2 = M.trim([('US-0003', 'Gamma State Park', 0.5, 0.5)],
                   [{'properties': {'OID': 9, 'NAME': 'Gamma State Park'}, 'geometry': SQUARE}, {'properties': {'OID': 10, 'NAME': 'Gamma State Park'}, 'geometry': None}],
                   dict(CFG, id_fields=[]), '2026-11-11')
check('trim: name + pin match still builds (a second, empty record does not queue it)', 'US-0003' in recs2 and not q2)

recs3, q3 = M.trim([('US-0002', 'Beta State Park', 0.5, 0.5)],
                   [{'properties': {'OID': 1, 'NAME': 'Beta State Park', 'POTA': 'US-0002'}, 'geometry': None},
                    {'properties': {'OID': 2, 'NAME': 'Beta State Park', 'POTA': ''}, 'geometry': SQUARE}], CFG, '2026-11-11')
check('trim: an id record with no outline is not queued when name + pin gives the park an outline', 'US-0002' in recs3 and not q3)

# dedupe + quiet write
dup = [{'ref': 'US-1', 'name': 'n', 'lat': 1, 'lon': 2, 'why': 'w', 'candidates': 'a'}, {'ref': 'US-1', 'name': 'n', 'lat': 1, 'lon': 2, 'why': 'w', 'candidates': 'b'},
       {'ref': 'US-1', 'name': 'n', 'lat': 1, 'lon': 2, 'why': 'w2', 'candidates': ''}]
check('dedupe: one row per (ref, reason), first wins, order kept', [(r['why'], r['candidates']) for r in M.dedupe_queue(dup)] == [('w', 'a'), ('w2', '')])
with tempfile.TemporaryDirectory() as td:
    p = pathlib.Path(td) / 'solver-queue' / 'US-AL.x.csv'
    check('write_queue: a new file is written', M.write_queue(p, dup) is True and p.is_file())
    b0, m0 = p.read_bytes(), p.stat().st_mtime_ns
    check('write_queue: the same rows again change nothing (same bytes, file not touched)', M.write_queue(p, dup) is False and p.read_bytes() == b0 and p.stat().st_mtime_ns == m0)
    check('write_queue: csv line endings match the existing queue files', b'\r\n' in b0)
    check('write_queue: new rows are written', M.write_queue(p, dup[:1]) is True and len(sq(p.parent)['US-AL.x.csv']) == 1)
    e = pathlib.Path(td) / 'solver-queue' / 'US-AL.nomatch.csv'
    check('write_queue: empty + keep_empty=False writes no file', M.write_queue(e, [], keep_empty=False) is False and not e.exists())
    check('write_queue: empty + keep_empty=True (trim) keeps a header-only file like before', M.write_queue(e, []) is True and e.read_bytes().startswith(b'ref,name,lat,lon,why,candidates'))
    check('write_queue: an empty queue removes an old no-match file', M.write_queue(e, dup, keep_empty=False) and M.write_queue(e, [], keep_empty=False) is True and not e.exists())

# trim end to end: a second identical run leaves the queue file untouched
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); root = t / 'outlines'; root.mkdir()
    M.save_layers({'format': 1, 'layers': {}, 'caches': {}}, root)
    parks = t / 'parks.json'; parks.write_text(json.dumps([['POTA', r, n, la, lo, 'u'] for r, n, la, lo in PARKS]))
    src = t / 'x.geojson'; src.write_text(json.dumps({'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': f['properties'], 'geometry': f['geometry']} for f in FEATS]}))
    args = ['trim', '--layer-key', 'US-AL.x', '--input', str(src), '--expected', str(len(FEATS)), '--parks', str(parks), '--area', 'US-AL', '--root', str(root),
            '--id-fields', 'POTA', '--name-fields', 'NAME', '--record-id-field', 'OID']
    rc = CLI.main(args); qf = root / 'solver-queue' / 'US-AL.x.csv'
    rows = sq(qf.parent).get('US-AL.x.csv', [])
    check('trim command: exit 0 and the queue file holds the two reasons', rc == 0 and sorted(r['why'] for r in rows) == sorted([M.WHY_NO_GEOM, M.WHY_UNKNOWN_REF]))
    b0, m0 = qf.read_bytes(), qf.stat().st_mtime_ns
    rc = CLI.main(args)
    check('trim command again: queue file byte-identical and not rewritten', rc == 0 and qf.read_bytes() == b0 and qf.stat().st_mtime_ns == m0)

# collect: the parks the key knows with no outline
def rec(ref):
    return M.make_record(ref, ref, 'official', SQUARE, 'a', 'file:x', ['r'], 1, '2026-11-11', '', 'id')


with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); root = t / 'outlines'; root.mkdir()
    M.save_area('US-AL', {'US-0001': rec('US-0001')}, root)
    M.save_layers({'format': 1, 'layers': {}, 'caches': {}}, root); M.raw_manifest_path(root).write_text(json.dumps({'format': 1, 'files': []}))
    (root / 'solver-queue').mkdir()
    M.write_queue(root / 'solver-queue' / 'US-AL.sgx.csv', [{'ref': 'US-0003', 'name': 'Queued Park', 'lat': 1, 'lon': 1, 'why': 'w', 'candidates': ''}])
    key = t / 'us-key'; key.mkdir()
    (key / 'US-AL.json').write_text(json.dumps({'st': 'AL', 'parks': {
        'US-0001': {'n': 'Has Outline', 'm': [[1, 'X', 5, 'name']]},
        'US-0002': {'n': 'No Layer Park', 'm': [], 'c': []},
        'US-0003': {'n': 'Queued Park', 'm': []},
        'US-0004': {'n': 'Joined Not Kept', 'm': [[7, 'Joined Land Name', 9, 'name']], 'bk': [7, 0.0, 'SP', 'des']}}}))
    part = t / 'part1'; part.mkdir(); (part / 'states.txt').write_text('AL\n')
    rc = CLI.main(['collect', str(part), '--root', str(root), '--us-key', str(key)])
    nm = sq(root / 'solver-queue').get('US-AL.nomatch.csv', [])
    check('collect: exit 0 and a no-match file exists', rc == 0 and bool(nm))
    check('collect: a park with an outline is not listed; a park already in a layer queue is not listed twice',
          sorted(r['ref'] for r in nm) == ['US-0002', 'US-0004'])
    why = {r['ref']: r['why'] for r in nm}
    check('collect: reasons say no layer / joined but not kept', why.get('US-0002') == M.WHY_NO_LAYER and why.get('US-0004') == M.WHY_NOT_KEPT)
    check('collect: names and candidates are kept; lat / lon stay blank (no pin invented)', {r['ref']: r['name'] for r in nm}['US-0004'] == 'Joined Not Kept'
          and all(r['lat'] == '' and r['lon'] == '' for r in nm) and [r['candidates'] for r in nm if r['ref'] == 'US-0004'] == ['Joined Land Name'])
    f = root / 'solver-queue' / 'US-AL.nomatch.csv'; b0, m0 = f.read_bytes(), f.stat().st_mtime_ns
    rc = CLI.main(['collect', str(part), '--root', str(root), '--us-key', str(key)])
    check('collect again: the no-match file is byte-identical and not rewritten', rc == 0 and f.read_bytes() == b0 and f.stat().st_mtime_ns == m0)
    # a park gets an outline: it leaves the file; when none is left the file is removed
    have = M.load_area('US-AL', root); have['US-0002'] = rec('US-0002'); have['US-0004'] = rec('US-0004'); M.save_area('US-AL', have, root)
    rc = CLI.main(['collect', str(part), '--root', str(root), '--us-key', str(key)])
    check('collect: once every park has an outline, the no-match file is emptied to its header (not deleted: the save carries no deletions)',
          rc == 0 and f.is_file() and not sq(f.parent)['US-AL.nomatch.csv'] and (root / 'solver-queue' / 'US-AL.sgx.csv').is_file())
    hb = f.read_bytes()
    # without --us-key nothing is added (old behaviour); a state with no key file is left alone
    have.pop('US-0002'); M.save_area('US-AL', have, root)
    rc = CLI.main(['collect', str(part), '--root', str(root)])
    check('collect without --us-key: the no-match file is not touched', rc == 0 and f.read_bytes() == hb)
    (key / 'US-AL.json').unlink()
    rc = CLI.main(['collect', str(part), '--root', str(root), '--us-key', str(key)])
    check('collect with no key file for the state: nothing said about it', rc == 0 and f.read_bytes() == hb)
    # a state this part does not own is not touched
    (key / 'US-AL.json').write_text(json.dumps({'st': 'AL', 'parks': {'US-0002': {'n': 'No Layer Park', 'm': []}}}))
    (key / 'US-TX.json').write_text(json.dumps({'st': 'TX', 'parks': {'US-0500': {'n': 'Texas Park', 'm': []}}}))
    rc = CLI.main(['collect', str(part), '--root', str(root), '--us-key', str(key)])
    check('collect: only the part\'s own states get a no-match file', rc == 0 and len(sq(f.parent)['US-AL.nomatch.csv']) == 1 and not (root / 'solver-queue' / 'US-TX.nomatch.csv').exists())
    # a state with no misses and no old file gets no empty file
    (key / 'US-AL.json').write_text(json.dumps({'st': 'AL', 'parks': {}})); f.unlink()
    rc = CLI.main(['collect', str(part), '--root', str(root), '--us-key', str(key)])
    check('collect: no misses and no old file -> no header-only file is made', rc == 0 and not f.exists())

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
