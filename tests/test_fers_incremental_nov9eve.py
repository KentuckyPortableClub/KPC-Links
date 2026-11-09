#!/usr/bin/env python3
"""Nov 9 evening (Brandon t909u-t917u): saved outlines first, every live read saved, and only redo what changed. Offline.
1 a pair's fingerprint has no code hash: an unrelated code edit reuses every saved pair result
2 a declared rule change (.github/fers-rule-scope.json) re-tests only the pairs of the parks in its scope
3 a changed outline / POTA pin re-tests only that park's pairs; KPC_FERS_FULL clears the reuse (emergency / round-robin full area)
4 saved_us keeps state-layer / FWS record ids too (not only PAD-US ints), so those parks are not downloaded live
5 the bot's own saved copy: written, read back, and re-read about once a month in slices (oldest first, a share per run)"""
import gzip, json, os, pathlib, sys, tempfile, types
HERE = pathlib.Path(__file__).resolve().parent.parent
S = HERE / '.github/scripts'
sys.path.insert(0, str(S))
os.environ.setdefault('PASS', '1')
try: import cv2  # noqa: F401
except Exception: sys.modules['cv2'] = types.ModuleType('cv2')  # noqa: BLE001
import kpc_fers as K
ok = True
def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)

src = (S / 'kpc_fers.py').read_text(encoding='utf-8')
check('REUSE_KEY, PASS, CELL' not in src and 'rule_stamp(a), rule_stamp(b)' in src, 'pair fingerprint: declared rule stamps, no code hash')
sc = json.load(open(HERE / '.github/fers-rule-scope.json'))
ids = [c['id'] for c in sc['changes']]
check(len(ids) == len(set(ids)) and all(c.get('scope') for c in sc['changes']), 'every declared rule change has a unique id and a scope')

ring = [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]
G = {'US-0001': [ring], 'US-0002': [ring], 'CA-0003': [ring]}
K.PINS.clear(); K.PINS.update({'US-0001': ('A State Park', 37.0, -85.0, '', 'State Park', 'KY'), 'US-0002': ('B WMA', 37.0, -85.0, '', 'Wildlife Management Area', 'KY'),
                               'CA-0003': ('C Sanctuary', None, None, '', 'Bird Sanctuary', 'CA-QC')})
K.CURG.clear(); K.CURG.update(G); K.CURLN.clear(); K.SCOPE[:] = []; K._STAMP.clear()
f0 = K.pair_fp('US-0001', 'US-0002', G, {}); fc0 = K.pair_fp('US-0001', 'CA-0003', G, {})
K.CODE_HASH = 'something else'; K._STAMP.clear()
check(K.pair_fp('US-0001', 'US-0002', G, {}) == f0, 'an unrelated code edit keeps the saved pair (no code hash)')
K.SCOPE[:] = [{'id': 't1', 'scope': {'kinds': ['Wildlife Management Area']}}]; K._STAMP.clear()
check(K.pair_fp('US-0001', 'US-0002', G, {}) != f0, "a rule change scoped to WMAs re-tests a WMA's pair")
check(K.pair_fp('US-0001', 'CA-0003', G, {}) == fc0, 'and leaves the pairs of other kinds alone')
K.SCOPE[:] = [{'id': 't2', 'scope': {'flags': ['bad-pin']}}]; K._STAMP.clear()
check(K.pair_fp('US-0001', 'CA-0003', G, {}) != fc0 and K.pair_fp('US-0001', 'US-0002', G, {}) == f0, 'bad-pin scope: only the pinless park\'s pairs')
K.SCOPE[:] = [{'id': 't3', 'scope': {'states': ['US-TN']}}]; K._STAMP.clear()
check(K.pair_fp('US-0001', 'US-0002', G, {}) == f0, 'a rule change for another state touches nothing here')
K.SCOPE[:] = []; K._STAMP.clear()
G2 = dict(G, **{'US-0002': [[[[0, 0], [0, 2], [2, 2], [2, 0], [0, 0]]]]})
check(K.pair_fp('US-0001', 'US-0002', G2, {}) != f0 and K.pair_fp('US-0001', 'CA-0003', G2, {}) == fc0, 'a changed outline re-tests only that park\'s pairs')
K.PINS['US-0001'] = ('A State Park', 37.1, -85.0, '', 'State Park', 'KY'); K._STAMP.clear()
check(K.pair_fp('US-0001', 'US-0002', G, {}) != f0, 'a changed POTA entry (pin) re-tests the park')

with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); cwd = os.getcwd(); os.chdir(t)
    try:
        (t / 'data/fers').mkdir(parents=True); K.OUT = t / 'data/fers'
        K.CACHE_US = t / 'cache/us'; K.CACHE_US.mkdir(parents=True)
        with gzip.open(K.CACHE_US / 'US-NY.json.gz', 'wt') as fh:
            json.dump({'st': 'NY', 'saved': '2026-11-03', 'recs': [{'OBJECTID': 5, 'Category': 'Fee', '_r': ring}, {'OBJECTID': 'sgnya64818', '_r': ring, 'rd': '2026-11-03'},
                                                                   {'OBJECTID': 'fws61', 'INTTYPE1': 'E', '_r': ring}, {'OBJECTID': 'fws62', 'INTTYPE1': 'F', '_r': ring}]}, fh)
        with gzip.open(K.CACHE_US / 'prev-US-NY.json.gz', 'wt') as fh: json.dump({'recs': [{'OBJECTID': 'sgold1', '_r': ring}]}, fh)
        K.SAVED_STR.clear(); K.SAVED_LEFT.clear()
        pad = K.saved_us({})
        check(5 in pad and 'sgnya64818' in K.SAVED_STR and 'fws62' in K.SAVED_STR, 'saved_us keeps PAD-US, state-layer and FWS fee records')
        check('fws61' in K.SAVED_LEFT and 'fws61' not in K.SAVED_STR, 'an FWS easement stays left out (same rule as a live read)')
        check('sgold1' not in K.SAVED_STR, 'the previous copy (prev-*) is never used as the saved outline')
        K.live_load('t'); K.LIVE.update({f'US-{i:04d}': {'ids': ['x'], 'g': [ring], 'rd': '2026-09-01' if i < 8 else '2026-11-01'} for i in range(20)})
        due = K.live_due('2026-11-09')
        check(len(due) == 5 and all(int(r[3:]) < 8 for r in due), f'monthly re-read: only due entries, at most a quarter per run, oldest first ({len(due)})')
        K.live_save('2026-11-09'); K.LIVE = {}; K.live_load('t')
        check(len(K.LIVE) == 20 and (t / 'data/fers/saved-live-t.json.gz').exists(), 'the saved-live copy round-trips')
    finally: os.chdir(cwd)

K.FULL = True; K.REUSE_FILE = None
with tempfile.TemporaryDirectory() as t:
    K.OUT = pathlib.Path(t); K.RUN_TAG = 'x'
    (K.OUT / f'reuse-p{K.PASS}-x.json').write_text(json.dumps({'pairs': {'a+b': {'fp': 1}}}))
    K.reuse_load(); check(K.REUSE == {}, 'KPC_FERS_FULL: every pair is tested again')
    K.FULL = False; K.reuse_load(); check('a+b' in K.REUSE, 'without the switch the saved pairs are reused')
# Nov 9 evening (Brandon t926u): a crash / time-out keeps the pair answers that finished (merged with the older ones)
with tempfile.TemporaryDirectory() as t:
    K.OUT = pathlib.Path(t); K.RUN_TAG = 'y'; K.FULL = False
    (K.OUT / f'reuse-p{K.PASS}-y.json').write_text(json.dumps({'pairs': {'old+one': {'fp': 'o'}}}))
    K.reuse_load(); K.REUSE_NEW['a+b'] = {'fp': 'n', 'spots': []}
    _cwd = os.getcwd(); os.chdir(t)   # save_json notes the change under ./data/status: keep it out of the repo
    try: n = K.reuse_keep_finished()
    finally: os.chdir(_cwd)
    d = json.load(open(K.OUT / f'reuse-p{K.PASS}-y.json'))
    check(n == 1 and set(d['pairs']) == {'old+one', 'a+b'} and d.get('partial'), 'a break keeps the finished pair answers (next run skips them) and the older ones')
check(src.count('{reuse_keep_finished()}') == 2 and src.index('except HardStop') < src.index("{reuse_keep_finished()} finished pair answers"), 'both a time-out (3) and a crash (1) keep them; the exit code stays (red)')
check('not RECHECK_ANSWERS or answers_unchanged' in src, "the old 'read every server answer again' check is off by default")
# keys: saved outlines first (Brandon t909u); the monthly re-read stays with the boundary check / the Canada monthly run
U = (HERE / '.github/workflows/kpc-us-key.yml').read_text(encoding='utf-8')
check("GEO_CACHE_MODE: ${{ vars.KPC_KEY_LIVE == '1' && 'off' || 'use' }}" in U and 'gh release download boundary-cache -R "$GITHUB_REPOSITORY" -p "US-$st.json.gz"' in U,
      'US key build: saved copy first, live only for what it lacks')
check('-newer "$RUNNER_TEMP/cache-t0"' in U and 'gh release upload boundary-cache $F' in U, "US key: this job's live reads are saved to boundary-cache")
C = (HERE / '.github/workflows/kpc-ca-key.yml').read_text(encoding='utf-8')
check("== '43 10 2 * *' && !inputs.saved && 'refresh' || 'use'" in C, 'Canada key: saved copy first; only the monthly run re-reads live')
print('ALL PASS' if ok else 'FAILED'); sys.exit(0 if ok else 1)
