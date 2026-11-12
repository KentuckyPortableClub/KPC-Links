#!/usr/bin/env python3
"""Part A v2 (Quality NO on 07): Gladstone CREEK removal is durable via ca-key overrides 'no'.
US-7322 River Bend PAD-US kept (verify-then-fix evidence). No hand-edit of built key JSON."""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
ok=True
def check(c,m):
  global ok
  print(('PASS ' if c else 'FAIL ')+m); ok = ok and bool(c)

ov=json.load(open(ROOT/'data/ca-key/overrides.json'))['parks']['CA-3550']
no={str(x) for x in ov.get('no') or []}
check('BC recreatio:1006529' in no or any('1006529' in x for x in no), f'override no has recreatio id ({no})')
check(any('GLADSTONE CREEK' in x.upper() for x in no), f'override no has CREEK name ({no})')
check('verify-then-fix' in (ov.get('decided_by') or ov.get('why') or ''), f'decided_by/why cites verify-then-fix')

# US-7322: both joins still in key; acres not left as only 0-ac
us=json.load(open(ROOT/'data/us-key/US-AR.json'))['parks']['US-7322']
ids=[str(x[0]) for x in us['m']]
check('166815' in ids, f'US-7322 keeps the PAD-US record ({ids})')
check(any(i.startswith('arw') for i in ids), f'US-7322 keeps an AR WMA (arw) record too ({ids}; the record number is bot-written, so the layer prefix is tested)')
check((us.get('ac') or 0) > 0 or any((x[2] or 0) > 0 for x in us['m'] if isinstance(x[2], (int,float))),
      f'US-7322 not left with only 0-ac join (ac={us.get("ac")} m={us["m"]})')
# No US-7322 override stripping River Bend
sys.path.insert(0, str(ROOT / '.github/scripts')); import kpc_overrides as _KOVR
uov=((_KOVR.load(ROOT/'data/us-key/overrides.json').get('parks') or {}).get('US-7322') or {})
check('166815' not in {str(x) for x in uov.get('no') or []}, 'US-7322 has no override no on PAD-US River Bend')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
