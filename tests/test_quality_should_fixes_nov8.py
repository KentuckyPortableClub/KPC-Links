#!/usr/bin/env python3
"""Nov 8 regrade (Quality on US-42504172086 / W-42509770852) should-fixes:
 1. the 5 km new-join hold drops only the NEW far ids and keeps a park's earlier joins (US-13132, 13134, 13138, 4868, 4886);
    an all-new join over 5 km still pins the whole park; over 15 km still pins the whole park.
 2-5 are flags for a person (docs/quality-should-fixes-nov8.md); nothing decided here. Rules hashes unchanged."""
import json, pathlib, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_join_check as J, kpc_key_freeze as KF
bad = 0
def check(ok, msg):
    global bad; bad += not ok; print(('PASS ' if ok else 'FAIL ') + msg)
check({k: KF.rules_hash(k) for k in ('us-key', 'ca-key', 'world-key')} == {'us-key': '2900f362e70b', 'ca-key': '7fb6aaef38c0', 'world-key': '10e4092cc97f'}, 'rules hashes unchanged')
check('kpc_join_check.py' in KF.NOT_RULES, 'kpc_join_check.py is not a rules file')
T = pathlib.Path(tempfile.mkdtemp(prefix='kpc-qsf-nov8-'))
def run(parks, prev):
    f = T / 'US-NV.json'; f.write_text(json.dumps({'parks': parks}), encoding='utf-8')
    J.SIGNED.clear(); J.SIGNED_BY.clear(); J.NOS.clear()
    rows, held, ch = J.mark_file(str(f), {}, True, 'hold', {}, False, None, str(T), prev)
    return json.loads(f.read_text(encoding='utf-8'))['parks'], held
old = {'n': 'Seven Mile HMA', 'g': 'official', 'm': [['hma50', 'Seven Mile', 90000, 'name']], 'bk': ['hma50', 9.2, '', '-'], 'c': []}
now = {'n': 'Seven Mile HMA', 'g': 'official', 'm': [['hma50', 'Seven Mile', 90000, 'name'], ['sgnvi77', 'Seven Mile', 91000, 'name']], 'bk': ['hma50', 9.2, '', '-'], 'c': []}
p, h = run({'US-13132': now}, {'US-13132': old})
check(p['US-13132']['g'] == 'official' and [x[0] for x in p['US-13132']['m']] == ['hma50'] and any(x[0] == 'sgnvi77' for x in p['US-13132']['c']),
      '1: earlier join kept live; only the new far id goes back to c')
check(h and h[0]['held_ids'] == 'sgnvi77' and 'earlier joins stay' in h[0]['reason'], '1: the held row names only the new id')
allnew = {'n': 'Annett SF', 'g': 'official', 'm': [['sgnhd9', 'Annett', 1200, 'name']], 'bk': ['sgnhd9', 9.3, '', '-'], 'c': []}
p, h = run({'US-4868': allnew}, {'US-4868': {'n': 'Annett SF', 'g': 'pin', 'm': [], 'c': []}})
check(p['US-4868']['g'] == 'pin', '1: an all-new join over 5 km still pins the park')
far = dict(now, bk=['hma50', 20.0, '', '-'])
p, h = run({'US-1': far}, {'US-1': dict(old, bk=['hma50', 20.0, '', '-'])})
check(p['US-1']['g'] == 'pin', '1: over 15 km still pins the whole park')
near = dict(now, bk=['hma50', 2.0, '', '-'])
p, h = run({'US-2': near}, {'US-2': old})
check([x[0] for x in p['US-2']['m']] == ['hma50', 'sgnvi77'] and not h, '1: a new piece under 5 km is kept')
doc = (ROOT / 'docs/quality-should-fixes-nov8.md').read_text(encoding='utf-8')
check(all(x in doc for x in ('sgnvh1238', 'US-9268', 'US-13178', 'CL-0012', 'Rule 18', 'failed', 'complete')), 'flags 2-5 are written down for a person')
print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
