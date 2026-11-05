#!/usr/bin/env python3
"""Nov 6: Brandon ruling 4:14 PM CST Nov 5 (relayed) — three KY slash / Wild-River parks join the named outline."""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
ok=True
def check(c,m):
  global ok
  if not c: ok=False; print('FAIL',m)
  else: print('PASS',m)
k=json.load(open(ROOT/'data/ky-answer-key.json'))
n=json.load(open(ROOT/'data/ky-key-no.json'))
for ref, layer, nm in [
 ('US-7957','bsnp','Vernon-Douglas State Nature Preserve'),
 ('US-7958','bsnp','Tom Dorman State Nature Preserve'),
 ('US-10103','bwild','Cumberland River Wild River'),
]:
  p=k['parks'][ref]
  check(any(t[0]==layer and t[1]==nm for t in p.get('tracts') or []), f'{ref} joins {layer}:{nm}')
  check('said_no' not in p, f'{ref} said_no cleared')
  check(p.get('decided_by')=='Brandon / KZ4CP', f'{ref} decided_by Brandon / KZ4CP')
  check(p.get('decided')=='2026-11-05', f'{ref} decided 2026-11-05')
  check(ref not in (n.get('parks') or {}), f'{ref} not in ky-key-no')
  check(ref not in (k.get('missing') or []), f'{ref} not in missing')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
