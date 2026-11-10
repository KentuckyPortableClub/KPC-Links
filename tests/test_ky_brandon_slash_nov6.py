#!/usr/bin/env python3
"""Nov 6: Brandon ruling 4:14 PM CST Nov 5 (relayed) — three KY slash / Wild-River parks join the named outline.
Part A (d): US-10172 Salato outline from PAD-US 202779."""
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
# Part A (d): Salato outline from PAD-US 202779
p=k['parks']['US-10172']
check(any(str(t[0])=='bpad' and 'Salato' in str(t[1]) for t in p.get('tracts') or []), f'US-10172 has Salato bpad tract ({p.get("tracts")})')
# Nov 9 (Brandon 10:05 AM CST: Salato -> KDFWR HQ polygon OID 1: YES): the outline is now the KDFWR HQ polygon, 132 ac
_t = [t for t in p.get('tracts') or [] if str(t[0]) == 'bpad']
check(_t and _t[0][2] == 132, f'US-10172 bpad tract 132 ac, the KDFWR HQ polygon ({_t})')
check('US-10172' not in (k.get('missing') or []), 'US-10172 left the missing list')
g=json.load(open(ROOT/'ky-padus-parks.geojson'))
check(any(f.get('properties',{}).get('ref')=='US-10172' and f['properties'].get('KDFWR_OID')==1 and str(f['properties'].get('OLD_PADUS_ID'))=='202779' for f in g['features']),
      'ky-padus-parks.geojson carries US-10172 = KDFWR HQ OID 1 (was PAD-US 202779)')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
