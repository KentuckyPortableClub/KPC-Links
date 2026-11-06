#!/usr/bin/env python3
"""Quarter-mile pin coverage (Nov 6 2026 follow-up key / 2-fer patch, Brandon [pt449u]; the KY GIS Workbench FIND NEW rule
CAND_NEAR_MI = 0.25: official land counts as 'covered' by a POTA park when the park's pin is inside it or within 0.25 mi of its edge).
Offline, REPORT ONLY: reads the built keys' 'bk' (kpc_key_facts: km from the POTA pin to the nearest joined piece, 0.0 = inside);
never changes a join, a pin or a 2-fer (kept out of the rules hash, kpc_key_freeze.NOT_RULES).

For every park:
  joined      inside (km 0) | quarter_mile (0 < km <= 0.402) | beyond (km > 0.402: the pin does not 'cover' its own joined land
              by the workbench rule; listed, biggest distance first) | no_distance (bk has no km: no pin / no shape)
  not joined  unjoined_near: the best unjoined official record ('c' then 'a') is under 0.25 mi from the pin (a possible missed
              join, for a person to look at; listed)
The distance is measured on the key's working copy (GEO_DETAIL, ~1 km in the US key), so 'quarter_mile' vs 'beyond' is 'about';
the workbench measures the full-detail shape. Rows carry the 'also in' layers (kpc_also_in.py).
Writes data/status/key-check/pin-cover-<key>.json; one notice. Env KEY=us|ca|world (or WORKFLOW_NAME), TREND_DIR.
"""
import collections, glob, json, os, pathlib, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kpc_key_trend import KEYS, key_of, note, _j, DIR  # noqa: E402
from kpc_also_in import also_in  # noqa: E402

QUARTER_MI_KM = 0.25 * 1.609344   # 0.402 km


def classify(p):
    bk = p.get('bk') if isinstance(p, dict) else None
    km = bk[1] if isinstance(bk, list) and len(bk) > 1 else None
    if p.get('m'):
        if km is None: return 'no_distance', None
        km = float(km)
        if km <= 0.0: return 'inside', km
        return ('quarter_mile' if km <= QUARTER_MI_KM else 'beyond'), km
    if km is not None and float(km) <= QUARTER_MI_KM and bk and bk[0] is not None: return 'unjoined_near', float(km)
    return 'not_joined', None


def main():
    key = key_of()
    if not key: note('notice', 'pin cover: no key given'); return
    d, g = KEYS[key]
    n, beyond, near = collections.Counter(), [], []
    by_area = collections.defaultdict(collections.Counter)
    for f in sorted(glob.glob(os.path.join(d, g))):
        area = pathlib.Path(f).stem
        for r, p in ((_j(f) or {}).get('parks') or {}).items():
            if not isinstance(p, dict): continue
            c, km = classify(p)
            n[c] += 1; by_area[area][c] += 1
            if c == 'beyond':
                beyond.append({'park': r, 'name': p.get('n') or '', 'mi': round(km / 1.609344, 2), 'far': p.get('far'), 'also_in': also_in(key, p)})
            elif c == 'unjoined_near':
                near.append({'park': r, 'name': p.get('n') or '', 'record': p['bk'][0], 'mi': round(km / 1.609344, 2)})
    beyond.sort(key=lambda x: -x['mi'])
    out = DIR / f'pin-cover-{key}.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'key': key, 'about': __doc__.split('\n\n')[0], 'rule_km': round(QUARTER_MI_KM, 3), 'counts': dict(sorted(n.items())),
                               'by_area': {a: dict(sorted(c.items())) for a, c in sorted(by_area.items())},
                               'beyond': beyond, 'unjoined_near': near}, separators=(',', ':'), ensure_ascii=False) + '\n', encoding='utf-8')
    j = n['inside'] + n['quarter_mile'] + n['beyond']
    note('notice', f"{key}: of {j} joined parks with a distance, {n['inside']} pins inside, {n['quarter_mile']} within 0.25 mi, "
                   f"{n['beyond']} beyond 0.25 mi; {n['unjoined_near']} unjoined parks have an official record within 0.25 mi (listed in {out}; joins unchanged)")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in ('--test', '--selftest'):
        assert classify({'m': [[1]], 'bk': [1, 0.0, '', '-']}) == ('inside', 0.0)
        assert classify({'m': [[1]], 'bk': [1, 0.4, '', '-']})[0] == 'quarter_mile'
        assert classify({'m': [[1]], 'bk': [1, 0.41, '', '-']})[0] == 'beyond'
        assert classify({'m': [[1]], 'bk': [1, None, '', '-', 'nopin']})[0] == 'no_distance'
        assert classify({'m': [], 'c': [[7]], 'bk': [7, 0.1, '', '-']})[0] == 'unjoined_near'
        assert classify({'m': [], 'bk': [None, None, '', '-', 'nocand']})[0] == 'not_joined'
        print('pin-cover self-test OK'); sys.exit(0)
    try: main()
    except Exception as e:  # noqa: BLE001
        note('warning', f'pin cover stopped: {type(e).__name__}: {str(e)[:200]} (report only)')
