#!/usr/bin/env python3
"""Nov 9 amendment (Quality regrade v2 must-fix h) + amendment 2 (Brandon t938u recheck, 6:17 PM CST): of the 19 held parks, 18 met
Brandon's t927u sure rule on saved / official data and are joined decided_by 'Brandon t927u+t938u' with evidence; US-12471 Lone Rock
stays held (Brandon: Lone Rock stays out). The 25 t927u signings are unchanged."""
import json, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent.parent
ok = True
def check(c, m):
    global ok; print(('ok   ' if c else 'FAIL ') + m); ok &= bool(c)
P = json.load(open(HERE / 'data/us-key/overrides.json', encoding='utf-8'))['parks']
NOW = 'US-0197 US-0822 US-0894 US-4370 US-12235 US-12791 US-3722 US-3000 US-3498 US-8745 US-8911 US-3732 US-7463 US-7464 US-7465 US-7466 US-0754 US-11900'.split()
for r in NOW:
    v = P.get(r) or {}; e = v.get('evidence') or {}
    check(v.get('decided_by') == 'Brandon t927u+t938u' and not v.get('join_held') and e.get('ids') and set(e['ids']) <= {str(x) for x in v.get('join') or []}
          and all(i in (v.get('fp') or {}) for i in e['ids']) and e.get('rule') and e.get('detail'), f'{r} joined with evidence: {e.get("ids")}')
check(set(P['US-0197']['join']) >= {'fwsr41', 'fwsr118', 'fwsr208'} and 'wsrc4' in P['US-0197'].get('no', []), 'Kern: all 3 USFS segments; the Nov 2 NO on wsrc4 kept')
check('wsrc3' in P['US-0894'].get('no', []), 'Tuolumne: the Nov 2 NO on wsrc3 kept')
check('sgaki387660' in P['US-0822']['join'], 'Fort Smith keeps its older NRHP join')
lr = P['US-12471']
check(lr.get('none') is True and (lr.get('join_held') or {}).get('ids') == ['sgakg13505'] and not lr.get('decided_by'), 'US-12471 Lone Rock stays held')
check(sum(1 for v in P.values() if v.get('decided_by') == 'Brandon t927u') == 25, 'still exactly 25 signed Brandon t927u')
print('ALL PASS' if ok else 'FAILED'); sys.exit(0 if ok else 1)
