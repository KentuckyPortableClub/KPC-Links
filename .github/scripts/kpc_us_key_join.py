#!/usr/bin/env python3
"""kpc_us_key_join.py (Nov 11, KPC owner, 2026-11-11): the US key join job puts the build groups' parts together, per state, from
the part that OWNS each state, and fails closed on any conflict (exit 1, nothing written).

  python3 .github/scripts/kpc_us_key_join.py parts/us-key-part-* [--out data/us-key] [--key-src .github/scripts/kpc_us_key.py]

A part is one build group's artifact: states.txt (the states it built) + index.json (a red group without them is skipped; its states
are named failed by the stamp), US-ST.json and tracts/US-ST.json for its states, layers.json (its whole copy), zip-<prefix>.json
(only the zipped-shapefile copies that build WROTE, newer than its build start).
Conflicts (any one = exit 1, no file written):
  - one state in the states.txt of two parts (US-ST.json, tracts and index rows would be last-write-wins);
  - a part that carries US-ST.json / tracts for a state it does not own;
  - one data/us-key/layers.json prefix changed (against the join's checkout) by two parts to different rows;
  - a zip-<prefix>.json from a part that does not own every state of that zip layer (SZ_US in kpc_us_key.py, read as text, not run),
    or one zip file sent by two parts with different contents.
Not a rule file: it never decides a join. Standard library only."""
import argparse, ast, glob, json, os, pathlib, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class JoinConflict(Exception):
    pass


def zip_owners(src_path):
    """{zip prefix: set(states)} from the SZ_US list of kpc_us_key.py (parsed, never imported: an import runs a build)."""
    tree = ast.parse(pathlib.Path(src_path).read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SZ_US' for t in node.targets):
            out = {}
            for el in node.value.elts:
                pre, sts = el.elts[0], el.elts[6]
                out[ast.literal_eval(pre)] = set(ast.literal_eval(sts))
            return out
    raise JoinConflict(f'{src_path}: no SZ_US list (the zip layer owners cannot be read)')


def _load(p, default):
    try: return json.load(open(p, encoding='utf-8'))
    except Exception: return default  # noqa: BLE001


def plan(parts, out, owners):
    """Check every part first. Returns the write plan; raises JoinConflict on the first conflict."""
    out = pathlib.Path(out)
    base_lj = _load(out / 'layers.json', {})
    owner, files, idx_rows, lj_set, zips = {}, [], {}, {}, {}
    for d in sorted(parts):
        d = pathlib.Path(d)
        if not ((d / 'states.txt').exists() and (d / 'index.json').exists()): continue   # a red group: named failed in the stamp
        sts = open(d / 'states.txt', encoding='utf-8').read().split()
        for st in sts:
            if st in owner: raise JoinConflict(f'state {st} is in the states of two parts ({owner[st]} and {d.name})')
            owner[st] = d.name
        mine = set(sts)
        for f in list(d.glob('US-*.json')) + list((d / 'tracts').glob('US-*.json')):
            st = f.stem[3:]
            if st not in mine: raise JoinConflict(f'{d.name} carries {f.relative_to(d)} but does not own {st}')
        pi = (_load(d / 'index.json', {}) or {}).get('states', {})
        for st in sts:
            if (d / f'US-{st}.json').exists(): files.append((d / f'US-{st}.json', out / f'US-{st}.json'))
            if (d / 'tracts' / f'US-{st}.json').exists(): files.append((d / 'tracts' / f'US-{st}.json', out / 'tracts' / f'US-{st}.json'))
            if st in pi: idx_rows[st] = pi[st]
        for k, v in (_load(d / 'layers.json', {}) or {}).items():
            if base_lj.get(k) == v: continue   # this part did not change that row (a stale copy of main is not a write)
            if k in lj_set and lj_set[k][0] != v:
                raise JoinConflict(f'layer prefix {k} written differently by {lj_set[k][1]} and {d.name}')
            lj_set[k] = (v, d.name)
        for z in d.glob('zip-*.json'):
            pre = z.name[4:-5]
            need = owners.get(pre)
            if need is None: raise JoinConflict(f'{d.name} sent {z.name}, a zip layer kpc_us_key.py does not list')
            if not need <= mine: raise JoinConflict(f'{d.name} sent {z.name} but does not own its states ({" ".join(sorted(need - mine))})')
            if z.name in zips and zips[z.name][0].read_bytes() != z.read_bytes():
                raise JoinConflict(f'{z.name} sent differently by {zips[z.name][1]} and {d.name}')
            zips[z.name] = (z, d.name)
    return {'owner': owner, 'files': files, 'idx_rows': idx_rows, 'lj': {k: v for k, (v, _) in lj_set.items()}, 'zips': {n: z for n, (z, _) in zips.items()}}


def apply(p, out):
    if not os.environ.get('KPC_STATUS_NAME'):   # the same status file the inline join wrote (data/status/inline-<workflow>.json)
        import re
        wf = re.sub(r'[^a-z0-9]+', '-', str(os.environ.get('GITHUB_WORKFLOW') or '').lower()).strip('-')
        os.environ['KPC_STATUS_NAME'] = 'inline-' + wf if wf else 'inline'
    from kpc_save import save_json   # the same writer the key uses (same bytes as a serial run)
    out = pathlib.Path(out)
    for src, dst in p['files']:
        dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy(src, dst)
    for name, z in p['zips'].items(): shutil.copy(z, out / name)
    idx = (_load(out / 'index.json', {}) or {}).get('states', {})
    idx.update(p['idx_rows'])
    for st, row in list(idx.items()):
        fp = out / f'US-{st}.json'
        if not fp.exists() or not isinstance(row, dict): continue
        counts = (_load(fp, {}) or {}).get('counts') or {}
        if counts.get('padus') is not None and row.get('padus') != counts.get('padus'):
            row = dict(row); row.update(counts); idx[st] = row
    save_json(str(out / 'index.json'), {'states': {k: idx[k] for k in idx}})
    lj = _load(out / 'layers.json', {}) or {}
    lj.update(p['lj'])
    save_json(str(out / 'layers.json'), lj)
    return len([f for f in p['files'] if f[1].parent == out])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('parts', nargs='*'); ap.add_argument('--out', default='data/us-key')
    ap.add_argument('--key-src', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kpc_us_key.py'))
    a = ap.parse_args(argv)
    try:
        p = plan(a.parts, a.out, zip_owners(a.key_src))
    except JoinConflict as e:
        print(f'::error title=US key join::{e}: the parts did not join per state, nothing written (fail closed)', flush=True)
        return 1
    n = apply(p, a.out)
    print(f'::notice title=US key join::{n} state files from {len(a.parts)} parts; {len(p["lj"])} layer row(s) and {len(p["zips"])} zip file(s) changed', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
