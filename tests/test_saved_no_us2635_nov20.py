#!/usr/bin/env python3
"""US-2635 saved no (20 Nov 2026). The state park must not keep the national recreation area record.
Invented checks on the saved answer only: no key build. Run: python3 tests/test_saved_no_us2635_nov20.py"""
import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_overrides as KO  # noqa: E402
import kpc_key_rules as KR  # noqa: E402
R = []
def check(ok, what): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + what)

def json_parks():
    import json
    return json.loads((ROOT / 'data/us-key/overrides.json').read_text(encoding='utf-8'))['parks']

ov = KO.load(str(ROOT / 'data/us-key/overrides.json'))['parks']['US-2635']
ev = ov.get('evidence') or {}
check(ov.get('no') == ['fsod68'], 'the recreation-area record is a saved no')
check(all(str(ev.get(k) or '').strip() for k in ('who', 'source', 'saw', 'date')), 'the no carries who, source, what was seen, and the date')
check('parks.nv.gov' in ev.get('source', ''), 'the source is the Nevada State Parks page')
check(ev.get('date') == '2026-11-20', 'the date is 20 Nov 2026')
check(KR.is_no(ov, 'fsod68', 'Spring Mountains National Recreation Area', 321709), 'the no matches that record by id')
check(not KR.is_no(ov, 'sgnve18', 'Spring Mountain Ranch State Park', 539), "the person's yes on the state-park record is not knocked out")
check(not KR.is_no(ov, '230201', 'Spring Mountain Ranch State Park', 539), 'the other state-park record is not knocked out')
check('US-2635' in json_parks(), 'a no lives in the manifest, not in a part file')
print('ALL PASS' if all(R) else f'{R.count(False)} FAILED')
sys.exit(0 if all(R) else 1)
