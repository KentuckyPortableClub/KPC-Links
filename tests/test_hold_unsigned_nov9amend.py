#!/usr/bin/env python3
"""Nov 9 amendment (Quality regrade v2 must-fix h, 6:00 PM CST): the 19 joins this batch added that are NOT sure under Brandon t927u
are held (join_held), never joined; every join this batch added is signed decided_by Brandon (t918u / t927u) or older."""
import json, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent.parent
ok = True
def check(c, m):
    global ok; print(('ok   ' if c else 'FAIL ') + m); ok &= bool(c)
P = json.load(open(HERE / 'data/us-key/overrides.json', encoding='utf-8'))['parks']
HELD = 'US-0197 US-0822 US-0894 US-12471 US-4370 US-12235 US-12791 US-3722 US-3000 US-3498 US-8745 US-8911 US-3732 US-7463 US-7464 US-7465 US-7466 US-0754 US-11900'.split()
for r in HELD:
    v = P.get(r) or {}; h = v.get('join_held') or {}
    check(h.get('ids') and not set(h['ids']) & {str(x) for x in v.get('join') or []} and h.get('reason') and not v.get('decided_by'),
          f'{r} held, not joined: {h.get("ids")} ({h.get("reason", "")[:60]})')
check(P['US-12471'].get('none') is True, 'US-12471 Lone Rock back to its Oct 22 none (Quality NOT SURE)')
check(sum(1 for v in P.values() if v.get('decided_by') == 'Brandon t927u') == 25, 'still exactly 25 signed Brandon t927u')
print('ALL PASS' if ok else 'FAILED'); sys.exit(0 if ok else 1)
