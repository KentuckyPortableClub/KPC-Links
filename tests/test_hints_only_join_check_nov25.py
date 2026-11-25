#!/usr/bin/env python3
"""25 Nov 2026, #380 round 13 grade (KPC owner 12:07 PM 'Delete any holds they maybe wrong idk.'; switch KPC_SAVED_HINTS_ONLY).
The join check that runs after the key (GitHub build and the PC test) read overrides.json NOs and signed joins for EVERY state:
a park whose old NO named land of the same name + acres was held back to a pin, though the key had set that NO aside. For a
state with the switch on it now obeys no old saved answer; other states as before. Invented files only.
Prints PASS / FAIL and ends ALL PASS or SOME FAILED."""
import json, os, pathlib, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_join_check as JC  # noqa: E402
import kpc_key_rules as KR  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


check('the switch is on for MN and NY in key-switches.json, off elsewhere',
      KR.on('KPC_SAVED_HINTS_ONLY', area='MN') and KR.on('KPC_SAVED_HINTS_ONLY', area='NY') and not KR.on('KPC_SAVED_HINTS_ONLY', area='KS'))
park = {'n': 'Alpha Lake WMA', 'g': 'outline', 'm': [['sgxx77', 'ALPHA LAKE', 120, 'name']], 'bk': [0.0, 0.0]}
prev = {'US-9001': {'n': 'Alpha Lake WMA', 'g': 'pin', 'm': [], 'c': []}}
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    res = {}
    for st in ('MN', 'KS'):
        JC.NOS.clear(); JC.SIGNED.clear()
        JC.NOS['US-9001'] = [('ALPHA LAKE', 118, 'sgxx12')]   # an old NO: the same name + acres under an old id
        f = td / f'US-{st}.json'
        f.write_text(json.dumps({'parks': {'US-9001': json.loads(json.dumps(park))}}))
        _r, held, _c = JC.mark_file(str(f), {}, plain=True, mode='hold', ok={}, prev=prev, root=str(td))
        res[st] = (held, json.loads(f.read_text())['parks']['US-9001'])
    check('switch OFF (KS): an old NO on the same name + acres still holds the new join (as before)',
          res['KS'][0] and not res['KS'][1]['m'])
    check('switch ON (MN): the old NO is a hint only: the join is not held', not res['MN'][0] and res['MN'][1]['m'])
    # a far join on a park with a signed saved join: exempt only where saved answers are obeyed
    JC.SIGNED.clear(); JC.SIGNED['US-9002'] = {'sgxx5'}; JC.SIGNED_BY['US-9002'] = 'a person'
    far = {'n': 'Beta', 'g': 'outline', 'm': [['sgxx5', 'BETA', 10, 'name']], 'bk': [40.0, 40.0]}
    check('a signed saved join exempts a far join when the switch is off', JC.exempt('US-9002', far, {}) != '')
    check('with the switch on (signed=False, no approvals) it exempts nothing', JC.exempt('US-9002', far, {}, signed=False) == '')
    check('hints_only reads the area from the file name (US-MN on, US-KS off, CA files never)',
          JC.hints_only('x/US-MN.json') and not JC.hints_only('x/US-KS.json') and not JC.hints_only('x/CA-ON.json'))
# a park in several states has ONE override: setting it aside for MN must not take it from WI built next in the same job
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
i = src.index('    for _r, _v in SAVED_HINTS.items():'); j = src.index("    try: P = {k: v for k, v in P.items() if k not in set(json.load(open('data/retired-refs.json'))", i)
blk = '\n'.join(ln[4:] for ln in src[i:j].splitlines())
ovr = {'US-4236': {'join': ['sgiaa34365'], 'no': ['sgwia1']}, 'US-0001': {'no': ['9']}}
ns = {'OVR': ovr, 'SAVED_HINTS': {}, 'notice': lambda *a: None}
for st, P, on in (('MN', {'US-4236': [], 'US-7777': []}, True), ('WI', {'US-4236': [], 'US-0001': []}, False)):
    ns.update(st=st, P=P, _kr=lambda n, on=on: on and n == 'KPC_SAVED_HINTS_ONLY')
    exec(blk, ns)
    if st == 'MN': check('MN (switch on): its park\'s saved answer is set aside (not obeyed)', 'US-4236' not in ovr and 'US-4236' in ns['SAVED_HINTS'])
check('WI (switch off) built after MN in the same job: the shared park\'s saved join and NO are back',
      ovr.get('US-4236') == {'join': ['sgiaa34365'], 'no': ['sgwia1']} and ovr.get('US-0001') == {'no': ['9']})
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
