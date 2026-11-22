#!/usr/bin/env python3
"""F2, F5, F10 (22 Nov 2026): KPC_ANSWER_HOLDERS, KPC_SAVED_ANSWERS_SAY and
KPC_HOLD_ON_PASS_ERROR are on in the same 50 areas as KPC_MATCH_CHECKS
(every area including DC, not Kentucky). Fail without the switch-file change.
Run: python3 -B tests/test_review_switches_on_nov22.py
"""
import json, pathlib, sys
sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_rules as KR  # noqa: E402

FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok:
        FAILS.append(what)


NAMES = ('KPC_ANSWER_HOLDERS', 'KPC_SAVED_ANSWERS_SAY', 'KPC_HOLD_ON_PASS_ERROR')
sw = json.loads((ROOT / '.github/key-switches.json').read_text(encoding='utf-8'))['switches']
want = list(sw['KPC_MATCH_CHECKS']['on'])
check(len(want) == 50 and 'DC' in want and 'KY' not in want,
      'KPC_MATCH_CHECKS is on in 50 areas including DC and not KY')
for name in NAMES:
    on = list((sw.get(name) or {}).get('on') or [])
    check(on == want, f'{name} is on in the same 50 areas as KPC_MATCH_CHECKS ({len(on)} listed)')
    check(KR.DEFAULTS.get(name) == '0', f'{name} still defaults off in the code')
    check(KR.on(name, env={}, area='OH') and KR.on(name, env={}, area='DC') and not KR.on(name, env={}, area='KY'),
          f'{name} is on for OH and DC in the committed file, and off for KY')

print(f'{len(FAILS)} failed' if FAILS else 'ALL PASS')
sys.exit(1 if FAILS else 0)
