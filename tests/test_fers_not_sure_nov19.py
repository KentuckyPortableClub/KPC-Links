#!/usr/bin/env python3
"""Hand-off 06 part 3: the 2-fer bot writes its own doubts and settles nothing. Offline."""
import json, os, pathlib, sys, tempfile
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts'))
os.environ.setdefault('PASS', '3')
import kpc_fers_not_sure as NS
import kpc_fers as K
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg, flush=True)
    ok = ok and bool(c)


def summary_only(ref, parks):
    return ref == 'US-2'


spots = {'US-ZZ': [
    {'refs': ['US-10', 'US-2'], 'status': 'not sure: near a size line: measured 25 m wide', 'kind': 'area'},
    {'refs': ['US-10', 'US-9'], 'status': 'candidate', 'kind': 'area'},
]}
parks = {'US-2': {'st': 'US-ZZ', 'ids': ['sg1']}, 'US-10': {'st': 'US-ZZ', 'ids': [1]}, 'US-9': {'st': 'US-ZZ', 'ids': [2]}}
names = {'US-2': 'Two', 'US-10': 'Ten', 'US-9': 'Nine'}
rows = NS.rows_from(spots, parks, names, summary_only, withheld=['US-9'], tripwire=['US-10'])
check([r['ref'] for r in rows] == ['US-2', 'US-2'], f'one row per park per doubt, tripwire and withheld left out ({[r["ref"] for r in rows]})')
by = {(r['ref'], r['code']): r for r in rows}
check(by[('US-2', 'SUMMARY_MAP_ONLY')]['wants'] == ['official layer'] and by[('US-2', 'SUMMARY_MAP_ONLY')]['found_by'] == '2-fer bot',
      'a summary-map park wants an official layer')
check(by[('US-2', 'NEAR_SIZE_LINE')]['wants'] == ['map', 'a person'] and by[('US-2', 'NEAR_SIZE_LINE')]['how_sure'] == 'unsure',
      'a park near a size line wants a map and a person')
check('US-9' not in NS.dumps(rows) and 'US-10' not in NS.dumps(rows), 'a withheld park and a tripwire park are not in the file')
check(NS.dumps(rows) == NS.dumps(NS.rows_from(spots, parks, names, summary_only, ['US-9'], ['US-10'])),
      'two runs on the same inputs write the same bytes')
check(not hasattr(NS, 'settle'), 'the bot does not settle a row')
# the order is park number, then code: NEAR before SUMMARY because N < S
check([r['code'] for r in rows if r['ref'] == 'US-2'] == ['NEAR_SIZE_LINE', 'SUMMARY_MAP_ONLY'], 'rows of one park are sorted by code')

out = pathlib.Path(tempfile.mkdtemp())
(out / 'US-ZZ.json').write_text(json.dumps({'st': 'US-ZZ', 'spots': spots['US-ZZ']}), encoding='utf-8')
(out / 'US-OR.json').write_text(json.dumps({'st': 'US-OR', 'spots': [
    {'refs': ['US-555', 'US-2'], 'status': 'not sure: near a size line: neighbour', 'kind': 'area'}]}), encoding='utf-8')
K.RUN_TAG = 't'
K.ONLY = {'US-ZZ'}
K.REGION = 'na'
K.PIN = {}
os.chdir(out)   # kpc_save writes data/status/<this test>.json in the working directory; keep that out of the repo
os.environ['KPC_FERS_NOT_SURE'] = 'none'   # review M8 (22 Nov 2026): no list stops the bot; these checks run without D10 on purpose
K._write_not_sure(out, dict(parks, **{'US-555': {'st': 'US-OR', 'ids': [5]}}),
                  {'US-2': ('Two',), 'US-9': ('Nine',), 'US-10': ('Ten',), 'US-555': ('Neighbour',)})
# summary_only in the real writer is K.summary_only, which these made-up ids do not trip.
# US-OR is a neighbour of this run (ONLY is US-ZZ), so its row is not in the file.
text = (out / 'not-sure-rows-t.json').read_text(encoding='utf-8')
again = text
K._write_not_sure(out, parks, {'US-2': ('Two',), 'US-9': ('Nine',), 'US-10': ('Ten',)})
check((out / 'not-sure-rows-t.json').read_text(encoding='utf-8') == again, 'the written file is the same the second time')
check('not sure: near a size line' in text and 'US-555' not in text and '"rows"' in text,
      'the near-line doubt is in the written file, a neighbour area is not, and the file is the rows document')
import kpc_fers_store as KS
KS.STORE_ON = True
KS.withheld_refs = lambda: {'US-777'}
held_spots = {'US-ZZ': [
    {'refs': ['US-2', 'US-777'], 'status': 'not sure: near a size line: beside US-777 Secret Park', 'kind': 'area'},
    {'refs': ['US-4', 'US-2'], 'status': 'not sure: near a size line: measured 25 m', 'kind': 'area'},
]}
(out / 'US-ZZ.json').write_text(json.dumps({'st': 'US-ZZ', 'spots': held_spots['US-ZZ']}), encoding='utf-8')
held_parks = {'US-2': {'st': 'US-ZZ', 'ids': ['sg1']}, 'US-4': {'st': 'US-ZZ', 'ids': [4]},
              'US-777': {'st': 'US-ZZ', 'ids': [7]}}
K._write_not_sure(out, held_parks, {'US-2': ('Two',), 'US-4': ('Four',), 'US-777': ('Secret Park',)})
written = json.loads((out / 'not-sure-rows-t.json').read_text(encoding='utf-8'))
blob = json.dumps(written)
check('US-777' not in blob and 'Secret' not in blob, 'a store run with a withheld park: that park is not in the file we read')
check(any(r.get('ref') == 'US-4' for r in written.get('rows') or []), 'the other park of this run is still in the file')
KS.STORE_ON = False
bad = out / 'trip.json'
bad.write_text('{', encoding='utf-8')
os.environ['KPC_FERS_NOT_SURE'] = str(bad)
K._TRIPWIRE.clear(); _code = None
try: K._write_not_sure(out, parks, {'US-2': ('Two',)})
except SystemExit as _e: _code = _e.code
os.environ.pop('KPC_FERS_NOT_SURE', None); K._TRIPWIRE.clear()
check(_code == 4, 'an unreadable tripwire list stops the bot (exit 4, review M8 22 Nov 2026)')
K.ONLY = set()
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
