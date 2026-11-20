#!/usr/bin/env python3
"""Nov 20 (job 5, evidence batch 04): nine saved "no" answers, each with who checked, the official source, what it showed and the
date (key-quality.md section 5). Runs on the REAL saved answers in data/us-key/overrides*.json; contacts no server."""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_overrides as O  # noqa: E402
import kpc_key_rules as KR  # noqa: E402
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


parks = O.load(ROOT / 'data/us-key/overrides.json')['parks']
WANT = {'US-2635': ['fsod68'], 'US-7461': ['sggaa111'], 'US-7462': ['sggaa66'], 'US-12233': ['sgida73156'], 'US-9202': ['sgsca111'],
        'US-7578': ['sgtnc23'], 'US-3933': ['sgtnc308'], 'US-7581': ['sgtnc687'], 'US-5154': ['sgnya68324', 'sgnya64544', '236464']}
for ref, ids in WANT.items():
    v = parks.get(ref) or {}
    check(f'{ref}: a saved NO on {", ".join(ids)}', all(KR.is_no(v, i) for i in ids))
    check(f'{ref}: each NO keeps its fingerprint (name, acres)', all(len((v.get('nofp') or {}).get(i) or []) == 2 for i in ids))
    ev = v.get('evidence') or {}
    check(f'{ref}: evidence names who, source, what was seen and the date',
          all(str(ev.get(k) or '').strip() for k in ('who', 'source', 'saw', 'date')) and ev.get('date') == '2026-11-20'
          and str(ev.get('source', '')).startswith('https://'))
    check(f'{ref}: a NO is never also a YES', not (set(map(str, v.get('join') or [])) & set(ids)))
# the saved YES the batch keeps
check('US-7578 keeps its own YES on sgtnc308', 'sgtnc308' in (parks['US-7578'].get('join') or []))
check('US-3933 keeps its own YES on sgtnc23', 'sgtnc23' in (parks['US-3933'].get('join') or []))
check('US-2635 keeps its own YES on sgnve18', 'sgnve18' in (parks['US-2635'].get('join') or []))
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
