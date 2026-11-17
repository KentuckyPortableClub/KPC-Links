#!/usr/bin/env python3
"""D9 (KPC owner, 2026-11-17): one record, one park. (a) the drawn outline honours the key's part boxes (rule B12 'parts'), so a
record holding two separate places is drawn for each park from its own parts only (Pine Hill); (b) behind KPC_ONE_RECORD_ONE_PARK,
a record joined by name to two parks of the same kind stays with the park whose full name is the record's own name.
Run:  python3 tests/test_d9_one_record_nov17.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import gzip, json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_rules as KR  # noqa: E402
import kpc_outlines_from_key as O  # noqa: E402
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)

sq = lambda x, y, s=0.01: [[x, y], [x + s, y], [x + s, y + s], [x, y + s], [x, y]]
rec = {'OBJECTID': 1, '_r': [sq(-79.0, 42.08), sq(-78.99, 42.09, .002), sq(-75.36, 42.27)]}
west = O.clip_rec(rec, [[-79.01, 42.07, -78.95, 42.11]]); east = O.clip_rec(rec, [[-75.39, 42.26, -75.32, 42.29]])
check(len(west['_r']) == 2 and len(east['_r']) == 1, 'a two-place record: each park keeps only the rings in its own part boxes')
check(O.clip_rec(rec, None) is rec and O.clip_rec(rec, [[0, 0, 1, 1]]) is rec, 'no box, or no ring in the boxes = the record as it is')
check(KR.d9_winner('Glacier Bay National Park', {'US-12607': 'Glacier Bay National Park', 'US-0029': 'Glacier Bay National Preserve'}) == 'US-12607',
      'the park whose full name is the record name keeps it (Glacier Bay)')
check(KR.d9_winner('Pine Hill State Forest', {'A': 'Pine Hill (Cattaraugus County) State Forest', 'B': 'Pine Hill (Delaware County) State Forest'}) is None,
      'two parks that both carry the name (brackets aside) = no single winner: left for a person')
check(KR.d9_winner('Boise National Forest', {'A': 'Boise National Forest', 'B': 'Salmon-Challis National Forest'}) == 'A', 'Boise keeps its own forest record')
check(KR.d9_winner('Muddy Mountains', {'A': 'Muddy Mountains BLM Herd Management Area', 'B': 'Muddy Mountains BLM Wilderness'}) is None,
      'no park carries the record name exactly = no winner')
check(not KR.on('KPC_ONE_RECORD_ONE_PARK', {}), 'the D9 switch is OFF unless set')
f = ROOT / 'cache/us/US-NY.json.gz'
if f.is_file():
    recs = {str(a['OBJECTID']): a for a in json.load(gzip.open(f, 'rt'))['recs']}
    ny = json.load(open(ROOT / 'data/us-key/US-NY.json'))['parks']
    a, b = ny['US-12030'], ny['US-5249']
    ra, rb = O.clip_rec(recs['236695'], a['parts']['236695']), O.clip_rec(recs['236695'], b['parts']['236695'])
    check(len(ra['_r']) + len(rb['_r']) == len(recs['236695']['_r']) and len(rb['_r']) >= 1,
          f"New York saved copy: Pine Hill record 236695 splits {len(ra['_r'])} / {len(rb['_r'])} of its {len(recs['236695']['_r'])} rings between the two forests")
else: print('SKIP: no cache/us/US-NY.json.gz')
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
