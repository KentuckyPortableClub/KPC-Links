#!/usr/bin/env python3
"""25 Nov 2026 (owner: 'YOU HAVE 10 MN AND NY FROM TODAY TO COMPARE TOO'; 'WHY ARE WE DROPPING STUFF ALL THE TIME'): each PC
test keeps its own key files (zipped) in its report folder, finds the earlier tests that kept one, and lists park by park
every outline -> pin with the builder's reason. Offline, made-up keys. Prints PASS / FAIL, ends ALL PASS or SOME FAILED."""
import json, pathlib, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'pc-keys'))
import kpc_test_keys as K  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


def park(ids, n='Test Park', bk=None, c=None):
    return {'n': n, 'm': [[i, n, 100, 'name'] for i in ids], 'c': c or [], 'bk': bk or ['x', 0.0, '', '-']}


with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    K.HERE = t
    kf = t / 'US-ZZ.json'
    old = {'parks': {'Z-1': park(['a1']), 'Z-2': park(['b1']), 'Z-3': park([]), 'Z-4': park(['d1', 'd2'])}}
    new = {'parks': {'Z-1': park(['a1']),
                     'Z-2': park([], 'Lost Park', bk=['b1', 0.0, '', 'not proven (no name in common)'],
                                 c=[['b1', 'Other Name', 50, 'the POTA pin is inside it (different name)']]),
                     'Z-3': park(['c1']), 'Z-4': park(['d1'])}}
    r1, r2, r3 = (t / 'reports' / f'test-2026-11-25-{h}' for h in ('0428', '1743', '2023'))
    kf.write_text(json.dumps(old)); k1 = K.keep_key(kf, r1)
    check('a test keeps its key zipped in its own report folder', k1 == r1 / 'keys' / 'US-ZZ.json.gz' and K.load(k1) == old)
    kf.write_text(json.dumps(new)); K.keep_key(kf, r2)
    (r3).mkdir(parents=True)
    e = K.earlier_tests(kf, r3)
    check('earlier tests are found newest first, never the test itself', [x[0] for x in e] == [r2.name, r1.name])
    check('a later test folder is never taken as "earlier"', [x[0] for x in K.earlier_tests(kf, r1)] == [])
    ch = '\n'.join(K.park_changes('Against test-2026-11-25-0428', k1, r2 / 'keys' / 'US-ZZ.json.gz'))
    check('counts: 1 outline to pin, 1 pin to outline, 1 records changed',
          'outline to pin 1, pin to outline 1, records changed 1' in ch)
    lost = ch[ch.index('OUTLINE TO PIN:'):ch.index('PIN TO OUTLINE:')]
    check('the lost park is named with its records before and after', 'Z-2 Lost Park' in lost and "('b1'" in lost and 'now pin' in lost)
    check("the builder's own reason is shown (best try and first check row)",
          'not proven (no name in common)' in lost and 'different name' in lost)
    check('an unchanged park is not listed', 'Z-1' not in ch)
    l, n = K.compare('US-ZZ against test-2026-11-25-0428', k1, r2 / 'keys' / 'US-ZZ.json.gz')
    check('the counts compare reads the zipped copies too', n['to_pin'] == 1 and n['from_pin'] == 1)
    src = (ROOT / 'tools' / 'pc-keys' / 'kpc_test_keys.py').read_text(encoding='utf-8')
    rs = src[src.index('def _run_state('):src.index('def main(argv):')]
    check('every built state keeps its key and writes CHANGES-<area>.txt', 'keep_key(kf, rep)' in rs and "f'CHANGES-{tag}.txt'" in rs)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
