#!/usr/bin/env python3
"""FAR-SPOT HOLD (chat 2, Oct 29 2026; chat 10's 'wrong far joins live today' + Brandon 7:23 AM 'some live 2fers were wrong,
correct them'). A LIVE 'area' or 'same land' row whose spot sits more than 100 km from the pin of a STATE-LEVEL park (not a
national unit, trail, river, refuge, BLM or other spread-out kind) is almost always that park's outline holding a far piece
(a same-named place in one record, rule B13) or a wrong join (record-id collision): the row is HELD as NOT SURE with the
reason, its old status kept in 'was'. Holding never invents a 2-fer; the rule B13 ruling or a key fix releases it.
Usage: python3 kpc_fers_far_hold.py [data/fers dir] [parkinfo dir]  (also imported by kpc_fers.py pass 5). Never fails."""
import glob, gzip, json, math, os, re, sys

LIVE = ('candidate', 'very tight', 'water only')
SPREAD = re.compile(r'national|trail|river|greenway|canal|byway|scenic|grassland|blm|wilderness|parkway|seashore|lakeshore|corps|federal|heritage area|route|highway|refuge|marine', re.I)
FAR_KM = 100


def pins(pdir):
    P = {}
    for f in glob.glob(os.path.join(pdir, 'US-*.json')) + [os.path.join(pdir, 'CA.json')]:
        try:
            for r, v in json.load(open(f))['parks'].items():
                if len(v) > 6 and v[5] is not None and v[6] is not None and (v[5] or v[6]):
                    la_, lo_ = (abs(v[6]), -abs(v[5])) if abs(v[5]) > 90 else (v[5], v[6])   # Oct 31 (Fable #28): swapped Canadian pins
                    P[r] = (la_, lo_, str(v[0]), str(v[2]) if len(v) > 2 else '')
        except Exception: pass  # noqa: BLE001
    return P


def km(la1, lo1, la2, lo2): return math.hypot((lo1 - lo2) * 111.32 * math.cos(math.radians(la1)), (la1 - la2) * 110.57)


def hold_spots(spots, P):
    n = 0
    for s in spots:
        if not str(s.get('status', '')).startswith(LIVE) or s.get('kind') not in ('area', 'same land') or not s.get('center'): continue
        la, lo = s['center']
        for r in s.get('refs') or []:
            if r not in P or SPREAD.search(P[r][2] + ' ' + P[r][3]): continue
            d = km(la, lo, P[r][0], P[r][1])
            if d > FAR_KM:
                s['was'] = s['status']
                s['status'] = (f"not sure: this spot is {round(d)} km from {P[r][2]}'s POTA pin: its outline may hold a far piece of a "
                               "same-named place, or the record is a wrong join (held until checked; rule B13)")
                s.pop('list', None); n += 1
                break
    return n


def main(fdir='data/fers', pdir='data/parkinfo'):
    P = pins(pdir); tot = {}
    for f in sorted(glob.glob(os.path.join(fdir, '*-*.json')) + glob.glob(os.path.join(fdir, '*-*.json.gz'))):
        b = os.path.basename(f)
        if not re.match(r'(US|CA)-[A-Z]{2}\.json', b): continue
        gz = f.endswith('.gz')
        try: d = json.load(gzip.open(f, 'rt') if gz else open(f))
        except Exception: continue  # noqa: BLE001
        n = hold_spots(d.get('spots') or [], P)
        if n:
            tot[b[:5]] = n
            try:
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from kpc_save import canon
                txt = canon(d, 1)
            except Exception: txt = json.dumps(d, indent=1, ensure_ascii=False)  # noqa: BLE001
            if gz:
                with gzip.open(f, 'wt', encoding='utf-8') as fh: fh.write(txt)
            else: open(f, 'w').write(txt if txt.endswith('\n') else txt + '\n')
    print(f"::notice title=2-fer far-spot hold::{sum(tot.values())} live rows held: {tot}", flush=True)
    return tot


if __name__ == '__main__':
    try: main(*sys.argv[1:3])
    except Exception as e: print(f'::notice title=2-fer far-spot hold::stopped: {str(e)[:200]}')  # noqa: BLE001
    sys.exit(0)
