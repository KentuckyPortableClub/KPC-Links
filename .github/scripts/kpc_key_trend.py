#!/usr/bin/env python3
"""Key trend file, build to build (Nov 6, big key / 2-fer patch; Brandon [pt437u]). Read-only on the keys; REPORT ONLY.

After each key check (kpc_key_postcheck.py) one row per build goes into data/status/key-check/trend-<key>.json:
  far_pins         pins 'well outside' the joined land (the check's pins_outside rows with far = 'well outside')
  pins_outside     'pins outside outline' from the check's summary
  outline_to_pin   'outline -> pin', flat_outlines 'flat outlines', overrides_missed 'overrides not followed'
  held_joins       data/<key>-key/review/held-joins.json 'count' (now only; older rows from the backfill have none)
  acres_off        joined parks whose key acres (sum of m[2]) and OFFICIAL acres disagree (kpc_pin_edge.acres_off: off by more
                   than half and more than 10 acres). Official acres = the tract side files' 'ac' (source field, every tract has
                   one), else data/acres.json / $OFFICIAL_ACRES. The world key has no acres (m[2] is the source): none.
  acres_checked    how many parks had both numbers
A JUMP (a count up by 25% and by 10+ since the previous build) is a ::warning; nothing fails, nothing is changed.
The first run backfills every <key>-*.json report already in the folder (oldest first).
Env: KEY=us|ca|world (or WORKFLOW_NAME), OFFICIAL_ACRES=<file>, TREND_DIR (default data/status/key-check).
"""
import glob, json, os, pathlib, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kpc_pin_edge as PE  # noqa: E402

KEYS = {'us': ('data/us-key', 'US-??.json'), 'ca': ('data/ca-key', 'CA-??.json'), 'world': ('data/world-key', '??.json')}
WF = {'KPC US answer key': 'us', 'KPC Canada answer key': 'ca', 'KPC world answer key': 'world'}
FIELDS = ('far_pins', 'pins_outside', 'outline_to_pin', 'flat_outlines', 'overrides_missed', 'held_joins', 'acres_off')
DIR = pathlib.Path(os.environ.get('TREND_DIR') or 'data/status/key-check')


def note(kind, msg): print(f'::{kind} title=Key trend::' + str(msg).replace('\n', ' ')[:900], flush=True)


def key_of():
    k = (os.environ.get('KEY') or '').strip().lower()
    if k in KEYS: return k
    w = (os.environ.get('WORKFLOW_NAME') or '').strip()
    for n, v in WF.items():
        if n.lower() in w.lower(): return v
    for v in KEYS:
        if re.search(rf'\b{v}\b', w.lower()): return v
    return None


def _j(f):
    try: return json.load(open(f, encoding='utf-8'))
    except Exception: return None  # noqa: BLE001


def row_of(rep):
    s = rep.get('summary') or {}
    po = rep.get('pins_outside') or []
    return {'build': rep.get('build'), 'checked': rep.get('checked'),
            'far_pins': sum(1 for x in po if isinstance(x, dict) and str(x.get('far') or '').startswith('well')),
            'pins_outside': s.get('pins outside outline'), 'outline_to_pin': s.get('outline -> pin'),
            'flat_outlines': s.get('flat outlines'), 'overrides_missed': s.get('overrides not followed')}


def held(key):
    for base in ('.', os.environ.get('DATA') or 'kpcdata'):
        d = _j(os.path.join(base, KEYS[key][0], 'review', 'held-joins.json'))
        if isinstance(d, dict) and isinstance(d.get('count'), int): return d['count']
    return None


def official(key):
    """(per_area {(area, ref): ac} from the tract side files, whole {ref: ac} from data/acres.json). A park in two states has a
    side-file row in each, so the side files are compared area by area; acres.json (whole park) against the summed key."""
    per, whole = {}, {}
    for f in glob.glob(os.path.join(KEYS[key][0], 'tracts', '*.json')) + (glob.glob('data/tracts/*.json') if key == 'us' else []):
        area = pathlib.Path(f).stem
        for r, ts in ((_j(f) or {}).get('parks') or {}).items():
            if ts and all(isinstance(t.get('ac'), (int, float)) and t['ac'] > 0 for t in ts): per[(area, r)] = float(sum(t['ac'] for t in ts))
    for f in [os.environ.get('OFFICIAL_ACRES'), 'data/acres.json', 'kpcdata/data/acres.json']:
        d = _j(f) if f and os.path.exists(f) else None
        if not isinstance(d, dict): continue
        for r, v in (d.get('parks', d) or {}).items():
            a = v.get('acres') if isinstance(v, dict) else v
            if isinstance(a, (int, float)) and not isinstance(a, bool) and a > 0: whole[r] = float(a)
        break
    return per, whole


def acres_off(key):
    if key == 'world': return None, 0, []
    per, whole = official(key)
    if not per and not whole: return None, 0, []
    d, g = KEYS[key]
    ka, tot = {}, {}
    for f in sorted(glob.glob(os.path.join(d, g))):
        area = pathlib.Path(f).stem
        for r, p in ((_j(f) or {}).get('parks') or {}).items():
            m = (p.get('m') or []) if isinstance(p, dict) else []
            a = sum(float(x[2]) for x in m if len(x) > 2 and isinstance(x[2], (int, float)) and not isinstance(x[2], bool))
            if a: ka[(area, r)] = a; tot[r] = tot.get(r, 0) + a
    rows, seen = [], set()
    for (area, r), a in ka.items():
        if (area, r) in per:
            seen.add(r)
            if PE.acres_off(a, per[(area, r)]): rows.append({'area': area, 'park': r, 'key_acres': round(a), 'official_acres': round(per[(area, r)]), 'from': 'tract side file'})
    for r, a in tot.items():
        if r in whole and r not in seen:
            seen.add(r)
            if PE.acres_off(a, whole[r]): rows.append({'park': r, 'key_acres': round(a), 'official_acres': round(whole[r]), 'from': 'acres.json'})
    return len(rows), len(seen), rows


def jumps(prev, cur):
    out = []
    for k in FIELDS:
        a, b = prev.get(k), cur.get(k)
        if isinstance(a, int) and isinstance(b, int) and b - a >= 10 and b >= a * 1.25: out.append(f'{k} {a} -> {b}')
    return out


def main():
    key = key_of()
    if not key: note('notice', 'no key given (KEY=us|ca|world): nothing done'); return
    f = DIR / f'trend-{key}.json'
    T = _j(f) or {'key': key, 'about': __doc__.split('\n\n')[0], 'rows': []}
    have = {r.get('build') for r in T['rows']}
    reps = [x for x in (_j(p) for p in glob.glob(str(DIR / f'{key}-*.json'))) if isinstance(x, dict) and x.get('summary')]
    reps.sort(key=lambda r: str(r.get('checked') or ''))
    if not reps: note('notice', f'{key}: no key check report yet'); return
    for rep in reps[:-1]:
        if rep.get('build') not in have: T['rows'].append(dict(row_of(rep), backfill=True)); have.add(rep.get('build'))
    cur = row_of(reps[-1]); cur['held_joins'] = held(key)
    ao, n, rows = acres_off(key); cur['acres_off'] = ao; cur['acres_checked'] = n
    T['rows'] = [r for r in T['rows'] if r.get('build') != cur['build']]
    prev = T['rows'][-1] if T['rows'] else {}
    T['rows'].append(cur); T['rows'] = sorted(T['rows'], key=lambda r: str(r.get('checked') or ''))[-200:]
    T['acres_off_latest'] = rows[:300]
    J = jumps(prev, cur) if prev else []
    T['last_jumps'] = J
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(T, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    if J: note('warning', f"{key} build {cur['build']}: JUMP since {prev.get('build')}: " + '; '.join(J))
    note('notice', f"{key} build {cur['build']}: " + ', '.join(f'{k} {cur.get(k)}' for k in FIELDS) + f" ({n} parks had official acres); {len(T['rows'])} builds in {f}")


if __name__ == '__main__':
    try: main()
    except Exception as e:  # noqa: BLE001
        note('warning', f'stopped: {type(e).__name__}: {str(e)[:200]} (report only; nothing else affected)')
