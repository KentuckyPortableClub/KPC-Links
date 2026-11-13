#!/usr/bin/env python3
"""U1 (Quality Nov 13): working US outlines agree with the key. 0 PIN-graded leftovers,
0 held records (AK US-10281 no longer carries record 2165), MN US-13655-13658 gone,
and AK official/approximate outlines are 63 more than the live released file."""
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_master as M

ok = True
def check(name, cond, extra=''):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name + (f' {extra}' if extra and not cond else ''))
    ok = ok and bool(cond)

ol, kd, rel = ROOT / 'data/outlines', ROOT / 'data/us-key', ROOT / 'data/released/outlines'

def recs(folder, area):
    def read(n):
        p = folder / n
        return p.read_bytes() if p.is_file() else None
    if read(f'{area}.geojson.gz') is None:
        return {}
    return M.recs_of_doc(M.load_doc_parts(f'{area}.geojson.gz', read))

states = sorted({p.name.split('.')[0] for p in ol.glob('US-??.geojson.gz')})
pins, held, unks = [], [], []
for st in states:
    r = recs(ol, st)
    pins += [(st, x) for x in sorted(M.pin_drops(st, r, kd))]
    unks += [(st, x) for x in sorted(M.not_in_key_drops(st, r, kd))]
    held += [(st, ref, ids) for ref, ids in sorted(M.held_record_refs(st, r, kd).items())]

check('U1: 0 PIN-graded outline leftovers in any state', pins == [], pins[:8])
check('U1: 0 not-in-key outline leftovers in any state', unks == [], unks[:8])
check('U1: 0 held-record leftovers in any state', held == [], held[:8])
ak = recs(ol, 'US-AK')
check('U1: AK US-10281 no longer holds record 2165',
      'US-10281' in ak and '2165' not in M.outline_record_ids(ak['US-10281']),
      M.outline_record_ids(ak.get('US-10281') or {}))
mn = recs(ol, 'US-MN')
check('U1: MN US-13655-13658 are gone',
      not any(r in mn for r in ('US-13655', 'US-13656', 'US-13657', 'US-13658')))
live = recs(rel, 'US-AK')
n_work = sum(1 for v in ak.values() if isinstance(v, dict) and v.get('g') in ('official', 'approximate'))
n_live = sum(1 for v in live.values() if isinstance(v, dict) and v.get('g') in ('official', 'approximate'))
check('U1: AK official/approximate outlines are 63 more than live (70 -> 133)',
      n_live == 70 and n_work == 133 and n_work - n_live == 63,
      f'live {n_live} working {n_work}')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
