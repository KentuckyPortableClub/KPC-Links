#!/usr/bin/env python3
"""Nov 9 evening (Brandon t919u, 4:48 PM CST): a 'bad ID' block list (overrides.json blocked_ids: ref, id, reason, decided_by).
A blocked id is never used for that park (US key, Canada key, 2-fer bot); the park goes back to normal matching or to a person;
an entry without decided_by does nothing. Offline."""
import json, os, pathlib, re, sys, tempfile, types
HERE = pathlib.Path(__file__).resolve().parent.parent
S = HERE / '.github/scripts'
ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)
for name in ('kpc_us_key.py', 'kpc_ca_key.py'):
    src = (S / name).read_text(encoding='utf-8')
    a = src.index('BLOCKED = {}'); b = src.index("_o['no'] = ", a); b = src.index('\n', b) + 1
    code = src[a:b]
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t)
        (t / 'overrides.json').write_text(json.dumps({'blocked_ids': [
            {'ref': 'US-1', 'id': '77', 'reason': 'wrong land', 'decided_by': 'Brandon test'},
            {'ref': 'US-2', 'id': 'sgx5', 'reason': 'test', 'decided_by': 'Brandon test'},
            {'ref': 'US-3', 'id': '9', 'reason': 'no person', 'decided_by': ''}]}))
        OVR = {'US-1': {'join': ['77', '78'], 'fp': {'77': ['A', 1], '78': ['B', 2]}, 'no': ['5']}, 'US-3': {'join': ['9']}}
        g = {'json': json, 'OUT': t, 'OVR': OVR}
        exec(code, g)
        check(OVR['US-1']['join'] == ['78'] and '77' not in OVR['US-1']['fp'] and '77' in OVR['US-1']['no'] and '5' in OVR['US-1']['no'], f'{name}: a blocked saved id leaves join/fp and is a NO; the rest stays')
        check(OVR['US-2'] == {'join': [], 'no': ['sgx5']}, f'{name}: a park with no override gets the block as a NO (normal matching otherwise)')
        check(OVR['US-3'] == {'join': ['9']}, f'{name}: an entry without decided_by is ignored')
    # Nov 12 (KPC-Links #151): the US key loads its overrides (manifest + parts) through kpc_overrides; blocked_ids stay in the manifest
    _ld = "_KOVR.load(OUT / 'overrides.json'" if name == 'kpc_us_key.py' else "OVR = json.load(open(OUT / 'overrides.json'))"
    check(src.index('BLOCKED = {}') > src.index(_ld), f'{name}: the block list runs right after the overrides load (before any join)')
for p in ('data/us-key/overrides.json', 'data/ca-key/overrides.json'):
    d = json.load(open(HERE / p))
    check(isinstance(d.get('blocked_ids'), list) and all(b.get('ref') and b.get('id') and b.get('reason') and b.get('decided_by') for b in d['blocked_ids']),
          f'{p}: blocked_ids is a list and every entry has ref, id, reason, decided_by')
sys.path.insert(0, str(S)); os.environ.setdefault('PASS', '1')
try: import cv2  # noqa: F401
except Exception: sys.modules['cv2'] = types.ModuleType('cv2')  # noqa: BLE001
import kpc_fers as K
parks = {'US-1': {'st': 'US-KY', 'ids': [77, 78], 'names': {}}, 'US-2': {'st': 'US-KY', 'ids': ['sgx5'], 'names': {}}, 'US-4': {'st': 'US-KY', 'ids': [1], 'names': {}}}
K.drop_blocked(parks, {'US-1': {'77'}, 'US-2': {'sgx5'}})
check(parks['US-1']['ids'] == [78] and 'US-2' not in parks and parks['US-4']['ids'] == [1], '2-fer bot: a blocked id is not used; a park left with no id is not tested (named in the log)')
check(any('US-2' in x and 'blocked' in x for x in K.LOG), '2-fer bot: the block is in the run log')
print('ALL PASS' if ok else 'FAILED'); sys.exit(0 if ok else 1)
