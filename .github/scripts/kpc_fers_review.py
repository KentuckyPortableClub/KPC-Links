#!/usr/bin/env python3
"""ONE BIG 'NEEDS A HUMAN LOOK' LIST (chat 2, Oct 28 2026; HQ 5:55 PM, Brandon GO). Chat 8 works through it after the US queue.

For one area (TAG + STATES) the line's checker adds/updates its rows in data/fers/review-all.json (+ review-all.md):
  - every NOT SURE row (the reason in plain words),
  - every missing-check DROPPED pair that POTA's own history says people activate together (not confirmed by the outlines),
  - every WATER ONLY row (a boat spot: is there really no land?),
  - every pair whose overlap leaves a river channel out between two banks (river slot).
One row per pair + kind; a rerun replaces that area's rows (never duplicates). Sorted biggest first.
Env: TAG, STATES, DATA (data/fers, the fresh files), OUT (where review-all.json lives; default DATA)."""
import json, os, pathlib, re, sys, time

TAG = os.environ.get('TAG') or ''
STATES = (os.environ.get('STATES') or '').split()
DATA = pathlib.Path(os.environ.get('DATA') or 'data/fers')
OUT = pathlib.Path(os.environ.get('OUT') or DATA)


def load(p):
    for q in (p, pathlib.Path(str(p) + '.gz')):
        try:
            if str(q).endswith('.gz'):
                import gzip
                return json.loads(gzip.decompress(q.read_bytes()))
            return json.load(open(q))
        except Exception: pass  # noqa: BLE001
    return None


def size_of(s):
    if s.get('kind') == 'area' or s.get('kind') == 'same land': return float(s.get('acres_all') or s.get('acres') or 0), f"{s.get('acres_all') or s.get('acres') or 0} ac"
    m = float(s.get('len_m') or 0); return m / 40.0, f"{round(m * 1.09361)} yd of line"   # ~40 m of line ~ 1 acre, only for sorting


def plain(status):
    st = str(status)
    return re.sub(r'^not sure: ', '', st)


def main():
    rows = []
    for st in STATES:
        d = load(DATA / f'{st}.json')
        if not d: continue
        for s in d.get('spots') or []:
            stt = str(s.get('status', ''))
            if stt.startswith('merged'): continue
            kind = None
            if re.search(r'water not checked|water map did not answer', stt): kind = 'water map weak here (fix later: a better water source)'   # Brandon Oct 28 8:53 PM: keep running, list them
            elif stt.startswith('not sure'): kind = 'not sure'
            elif stt.startswith('water only'): kind = 'water only (boat spot): is there really no land?'
            elif stt.startswith(('candidate', 'very tight')) and s.get('kind') == 'area' and s.get('river_slot'): kind = 'river slot between the two banks'
            if not kind: continue
            sz, szt = size_of(s)
            rows.append({'area': TAG, 'state': st, 'refs': s.get('refs'), 'names': s.get('names') or {}, 'what': kind, 'kind': s.get('kind'),
                         'size': szt, 'sort': round(sz, 1), 'reason': plain(stt)[:300], 'id': s.get('id'),
                         'sources': s.get('map_dates') or {}, 'checked': s.get('checked') or s.get('pass5') or d.get('pass5') or ''})
    e = load(DATA / f'expected-{TAG}.json') or {}
    for x in (e.get('DROPPED') or []) + [y for y in e.get('NEVER LOOKED AT') or [] if 'boxes do not touch' in str(y.get('reason', ''))]:
        # Oct 28 (chat 8, Iowa): pairs POTA history ties together but whose official outlines are apart (box test) are listed too: a hint only
        if not isinstance(x, dict): continue
        why = ' / '.join(x.get('why_expected') or [])
        if 'activated together' not in why: continue
        n = re.search(r'\((\d+)x', why)
        rows.append({'area': TAG, 'state': '', 'refs': x.get('refs'), 'names': {}, 'what': 'HINT only (look here): POTA history shows people activating these together; logs have mistakes, it never decides',
                     'kind': 'pair', 'size': f"{n.group(1) if n else '?'} same-day activations", 'sort': float(n.group(1)) if n else 0,
                     'reason': x.get('reason', ''), 'id': '+'.join(x.get('refs') or []) + '@pota', 'sources': {'POTA history': why[:160]}, 'checked': e.get('date', '')})
    # one row per pair + what (the biggest)
    best = {}
    for r in rows:
        k = (tuple(sorted(r['refs'] or [])), r['what'])
        if k not in best or r['sort'] > best[k]['sort']: best[k] = r
    rows = sorted(best.values(), key=lambda r: -r['sort'])
    # each area writes its OWN file (two areas' checkers never push the same file); combine() builds the one big list
    (OUT / 'review').mkdir(parents=True, exist_ok=True)
    json.dump({'area': TAG, 'date': time.strftime('%Y-%m-%d'), 'states': STATES, 'rows': rows}, open(OUT / 'review' / f'{TAG}.json', 'w'), indent=1)
    combine()
    print(f"::notice title=2-fer review list::{TAG}: {len(rows)} rows need a human look (not sure {sum(1 for r in rows if r['what'] == 'not sure')}, "
          f"POTA pairs not confirmed {sum(1 for r in rows if r['kind'] == 'pair')}, water only {sum(1 for r in rows if r['what'].startswith('water only'))}, river slots {sum(1 for r in rows if r['what'].startswith('river slot'))})", flush=True)


def combine():
    """data/fers/review-all.json + .md from every area's data/fers/review/<tag>.json (run by the last step of the queue too)."""
    import glob
    allr = {'about': "ONE BIG 'NEEDS A HUMAN LOOK' LIST (HQ + Brandon Oct 28): every NOT SURE row, POTA pairs our outlines do not confirm, water-only rows, river slots; one row per pair; an area's rows are replaced on each run. Chat 8 works it after the US queue.", 'areas': {}}
    for g in sorted(glob.glob(str(OUT / 'review' / '*.json'))):
        v = load(pathlib.Path(g))
        if v: allr['areas'][v['area']] = v
    f = OUT / 'review-all.json'
    json.dump(allr, open(f, 'w'), indent=1)
    L = ['# Needs a human look (all areas, biggest first per area)', '', "Written by the 2-fer line's checker. Chat 8 works it after the US queue. Nothing here is shown to anyone.", '']
    for a, v in sorted(allr['areas'].items()):
        L += [f"## {a} ({len(v['rows'])} rows, {v['date']})", '', '| what | parks | size | reason | sources |', '|---|---|---|---|---|']
        for r in v['rows'][:400]:
            pk = ' + '.join(f"{x} {r['names'].get(x, '')}".strip() for x in (r['refs'] or []))
            L.append(f"| {r['what']} | {pk[:120]} | {r['size']} | {str(r['reason'])[:160]} | {'; '.join(f'{k}: {v2}' for k, v2 in (r['sources'] or {}).items())[:120]} |")
        L.append('')
    (OUT / 'review-all.md').write_text('\n'.join(L) + '\n')


if __name__ == '__main__':
    try: combine() if os.environ.get('COMBINE_ONLY') else main()
    except Exception as e: print(f'::notice title=2-fer review list::stopped: {str(e)[:200]}')  # noqa: BLE001
    sys.exit(0)
