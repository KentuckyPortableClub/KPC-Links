#!/usr/bin/env python3
"""2-fer count switch (Nov 6, big key / 2-fer patch; Brandon [pt437u]). KPC_FERS_COUNT_MODE:

  whole_park (DEFAULT) - today's rows, untouched. apply() hands back the very same object, so the spot files are byte-identical.
  tracts               - adds to each spot 'tracts': {ref: [tract ids whose box holds the spot]} from the tract side files
                         (data/us-key/tracts, data/ca-key/tracts, data/world-key/tracts, data/tracts). A park made of separate
                         tracts then shows WHICH tract the 2-fer is in. Nothing is dropped; 'count_tracts' in the file = distinct
                         (tract, tract) combos among candidate spots.
  nested               - a spot whose parks are parent + child (the child park lies inside the other, kpc_tracts.nested_geometry)
                         gets 'nested': {'parent', 'child'}; the file gets 'nested_pairs': one row per such pair ('the whole child
                         park is a 2-fer with its parent'). Spots are not dropped or merged.

No mode changes a status, drops, merges or adds a spot; the extra fields are labels for the pages to use once Brandon picks.
Self-test / proof: python3 kpc_fers_count.py --prove <dir of spot files>  (whole_park must give 0 changed files).
"""
import json, os, sys, gzip, pathlib, copy

MODES = ('whole_park', 'tracts', 'nested')
MODE = (os.environ.get('KPC_FERS_COUNT_MODE') or 'whole_park').strip().lower()
if MODE not in MODES:
    print(f'::warning title=2-fer count switch::unknown KPC_FERS_COUNT_MODE {MODE!r}; using whole_park', flush=True); MODE = 'whole_park'
_IDX = None


def index():
    global _IDX
    if _IDX is None:
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import kpc_tracts as TR
            _IDX = TR.index()
        except Exception as e:  # noqa: BLE001
            print(f'::warning title=2-fer count switch::tract side files unreadable ({type(e).__name__}); labels skipped', flush=True); _IDX = {}
    return _IDX


def _at(spot):
    c = spot.get('center')
    return (c[0], c[1]) if isinstance(c, (list, tuple)) and len(c) == 2 else None


def _tracts_at(ref, la, lo, IDX):
    out = []
    for i, t in enumerate((IDX.get(ref) or {}).get('tracts') or []):
        b = t.get('box')
        if b and b[0] - 1e-4 <= lo <= b[2] + 1e-4 and b[1] - 1e-4 <= la <= b[3] + 1e-4:
            out.append(str(t.get('sid') or t.get('rid') or i))
    return out


def apply(path, d, mode=None, IDX=None):
    """Called on every data/fers save. Returns d itself in whole_park mode (no copy, no change)."""
    mode = mode or MODE
    if mode == 'whole_park' or not isinstance(d, dict) or not isinstance(d.get('spots'), list): return d
    IDX = index() if IDX is None else IDX
    if not IDX: return d
    if mode == 'tracts':
        combos = set()
        for s in d['spots']:
            at = _at(s)
            if not at: continue
            lab = {r: _tracts_at(r, at[0], at[1], IDX) for r in s.get('refs') or []}
            lab = {r: v for r, v in lab.items() if v}
            if lab:
                s['tracts'] = lab
                if s.get('status') == 'candidate': combos.add(tuple(sorted(f'{r}#{"|".join(v)}' for r, v in lab.items())))
        d['count_mode'] = 'tracts'; d['count_tracts'] = len(combos)
    elif mode == 'nested':
        pairs = {}
        for s in d['spots']:
            refs = s.get('refs') or []
            for c in refs:
                p = (IDX.get(c) or {}).get('parent')
                if p and p in refs:
                    s['nested'] = {'parent': p, 'child': c}
                    pairs.setdefault((p, c), []).append(s.get('id'))
        d['count_mode'] = 'nested'
        d['nested_pairs'] = [{'parent': p, 'child': c, 'spots': len(v), 'note': 'the whole child park lies inside the parent'} for (p, c), v in sorted(pairs.items())]
    return d


def _load(f):
    op = gzip.open if str(f).endswith('.gz') else open
    with op(f, 'rt', encoding='utf-8') as h: return json.load(h)


def prove(folder):
    """whole_park: every file round-trips unchanged; other modes: counts only (nothing written)."""
    IDX = index(); rep = {m: {'files': 0, 'changed': 0} for m in MODES}
    tot = {'spots': 0, 'candidates': 0, 'tract_labels': 0, 'nested_spots': 0, 'nested_pairs': 0, 'count_tracts': 0}
    for f in sorted(pathlib.Path(folder).glob('*.json*')):
        try: d = _load(f)
        except Exception: continue  # noqa: BLE001
        if not isinstance(d, dict) or not isinstance(d.get('spots'), list): continue
        raw = json.dumps(d, sort_keys=True)
        for m in MODES:
            x = apply(f, copy.deepcopy(d) if m != 'whole_park' else d, m, IDX)
            rep[m]['files'] += 1; rep[m]['changed'] += json.dumps(x, sort_keys=True) != raw
            if m == 'tracts':
                tot['tract_labels'] += sum(1 for s in x['spots'] if s.get('tracts')); tot['count_tracts'] += x.get('count_tracts') or 0
            if m == 'nested':
                tot['nested_spots'] += sum(1 for s in x['spots'] if s.get('nested')); tot['nested_pairs'] += len(x.get('nested_pairs') or [])
        tot['spots'] += len(d['spots']); tot['candidates'] += sum(1 for s in d['spots'] if s.get('status') == 'candidate')
    return rep, tot


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--prove':
        rep, tot = prove(sys.argv[2]); print(json.dumps({'modes': rep, 'totals': tot}, indent=1))
        sys.exit(1 if rep['whole_park']['changed'] else 0)
    print(__doc__)
