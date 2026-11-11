#!/usr/bin/env python3
"""Never save an outline file that is OLDER than the one already on main (KPC owner, 2026-11-11).

Why: a key run checks the repo out when it starts and saves about an hour later by copying its files on top of the newest main.
On Nov 11 a run that started before #129 merged put its own US-FL.geojson.gz over the new one and 97 FL outlines were lost.
Now, just before the save (and again inside the save, on the newest main), every area file data/outlines/<AREA>.geojson.gz
that differs from main's copy is put together with it, record by record:
  - an outline main has and this run's file lacks is KEPT (the master never deletes an outline);
  - both have it: the higher kind wins (kpc_master.RANK); same kind from the same layer = the newer date_read wins, and on the
    same date this run's fresh read wins; same kind from another layer = main's is kept (the master's own merge rule).
  - an outline only this run has is added, unless the key (data/us-key/US-XX.json in the working tree) grades the park pin:
    a bare-pin park never gets a new outline (Nov 11: the run wrote US-8689, US-8696 and US-8712 that way).
The two shared row files in the same folder are treated the same way: a row main has and this run's copy lacks is kept
(layers.json 'layers' and 'caches', raw-manifest.json 'files' by name). A row both have is this run's.
So the saved file always holds every outline and row main had. Fail closed: a file that cannot be put together is put back to main's
copy (nothing older is ever written) and the exit code is 1.

  python3 .github/scripts/kpc_outlines_keep_main.py [--ref origin/main] [--root data/outlines] [--fetch]
Offline except `git fetch origin main` with --fetch. Reads `git show <ref>:<file>` only."""
import argparse, gzip, json, pathlib, re, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import kpc_master as M  # noqa: E402

AREA_FILE = re.compile(r'^[A-Z]{2}(-[A-Z0-9]+)?\.geojson\.gz$')   # US-FL.geojson.gz, not a layer file like US-FL.sgfla.geojson.gz


def git(repo, *a):
    r = subprocess.run(['git', *a], cwd=repo, capture_output=True)
    return r.returncode, r.stdout


def recs_of(raw):
    doc = json.loads(gzip.decompress(raw))
    return {f['properties']['ref']: dict(f['properties'], geometry=f['geometry']) for f in doc.get('features', [])}


def pick(main, run):
    """Which record is saved when both main and this run have the park."""
    if main.get('hash') == run.get('hash'): return main
    rm, rr = M.RANK.get(main.get('g'), 0), M.RANK.get(run.get('g'), 0)
    if rm != rr: return main if rm > rr else run
    if main.get('layer_url') != run.get('layer_url'): return main            # another layer, same kind: the saved one stays
    return run if str(run.get('date_read') or '') >= str(main.get('date_read') or '') else main


def key_pins(repo, area):
    """Refs the key in the working tree grades pin (US areas only; no key file = none)."""
    try: parks = json.loads((pathlib.Path(repo) / 'data' / 'us-key' / f'{area}.json').read_text(encoding='utf-8')).get('parks') or {}
    except (OSError, ValueError): return set()
    return {r for r, p in parks.items() if isinstance(p, dict) and p.get('g') == 'pin'}


def rows_keep(name, main, run):
    """Shared row files: rows only main has are put into this run's copy. Returns how many."""
    n = 0
    if name == 'raw-manifest.json':
        have = {f.get('name') for f in run.get('files') or []}
        for f in main.get('files') or []:
            if f.get('name') not in have: run.setdefault('files', []).append(f); n += 1
        run['files'] = sorted(run.get('files') or [], key=lambda f: str(f.get('name')))
    else:
        for part in ('layers', 'caches'):
            for k, v in (main.get(part) or {}).items():
                if k not in (run.get(part) or {}): run.setdefault(part, {})[k] = v; n += 1
    return n


def put_together(main, run, pins=()):
    out = dict(main); kept = [r for r in main if r not in run]; older = []
    for ref, rec in run.items():
        if ref not in main:
            if ref not in pins: out[ref] = rec
            continue
        out[ref] = pick(main[ref], rec)
        if out[ref] is main[ref] and main[ref].get('hash') != rec.get('hash'): older.append(ref)
    return out, kept, older


def run(repo, root, ref):
    repo = pathlib.Path(repo); root = pathlib.Path(root); bad = []; n_kept = n_older = 0
    rel_root = root.resolve().relative_to(repo.resolve()).as_posix()
    rc, out = git(repo, 'ls-tree', '--name-only', f'{ref}:{rel_root}')
    if rc != 0:
        print(f'::error title=Outlines vs main::cannot list {rel_root} on {ref}: nothing was compared'); return 1
    on_main = {n for n in out.decode().split('\n') if AREA_FILE.match(n)}
    # a file main has and this run's folder lost is put back too
    for name in sorted(on_main | {p.name for p in root.glob('*.geojson.gz') if AREA_FILE.match(p.name)}):
        p = root / name
        if name not in on_main: continue                                      # a new area: nothing on main to lose
        rc, raw = git(repo, 'show', f'{ref}:{rel_root}/{name}')
        if rc != 0: bad.append(f'{name}: cannot read the copy on {ref}'); continue
        try:
            if p.exists() and p.read_bytes() == raw: continue
            main = recs_of(raw)
            if not p.exists():
                p.write_bytes(raw); n_kept += len(main); print(f'::warning title=Outlines vs main::{name} was missing in this run: the copy on main is kept'); continue
            mine = recs_of(p.read_bytes())
            pins = key_pins(repo, name[:-len('.geojson.gz')]); out_recs, kept, older = put_together(main, mine, pins)
            no_pin = sorted(set(mine) - set(out_recs))
            if no_pin: print(f"::warning title=Outlines vs main::{name}: {len(no_pin)} new outline(s) not saved, the key grades the park pin ({' '.join(no_pin[:8])})")
            if set(main) - set(out_recs): raise RuntimeError('the result would lose outlines main has')
            if out_recs != mine: M.save_area(name[:-len('.geojson.gz')], out_recs, root)
            if kept or older:
                n_kept += len(kept); n_older += len(older)
                print(f"::warning title=Outlines vs main::{name}: this run's file was older than main. Kept {len(kept)} outline(s) only main had"
                      f" and main's record for {len(older)} park(s) both had ({' '.join((kept + older)[:8])}{' ...' if len(kept + older) > 8 else ''})")
        except Exception as e:  # noqa: BLE001  fail closed: main's copy goes back, nothing older is written
            p.write_bytes(raw); bad.append(f'{name}: {type(e).__name__}: {str(e)[:120]} (the copy on main is kept; this run\'s outlines for it are not saved)')
    for name in ('layers.json', 'raw-manifest.json'):
        p = root / name; rc, raw = git(repo, 'show', f'{ref}:{rel_root}/{name}')
        if rc != 0 or not p.exists() or p.read_bytes() == raw: continue
        try:
            mine = json.loads(p.read_text(encoding='utf-8')); before = json.dumps(mine, sort_keys=True); n = rows_keep(name, json.loads(raw), mine)
            if n:
                p.write_text(json.dumps(mine, indent=1, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')
                print(f"::warning title=Outlines vs main::{name}: kept {n} row(s) only main had")
        except Exception as e:  # noqa: BLE001
            p.write_bytes(raw); bad.append(f'{name}: {type(e).__name__}: {str(e)[:120]} (the copy on main is kept)')
    for b in bad: print(f'::error title=Outlines vs main::{b}')
    print(f'outlines vs main ({ref}): {n_kept} outline(s) kept from main, {n_older} park(s) where the record on main stays, {len(bad)} file(s) put back')
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--ref', default='origin/main'); ap.add_argument('--root', default=str(M.OUTLINES))
    ap.add_argument('--repo', default=str(M.ROOT)); ap.add_argument('--fetch', action='store_true')
    a = ap.parse_args()
    if a.fetch:
        rc, _ = git(a.repo, 'fetch', '-q', 'origin', 'main')
        if rc != 0: print('::error title=Outlines vs main::git fetch origin main failed: main was not re-read'); return 1
    return run(a.repo, a.root, a.ref)


if __name__ == '__main__': sys.exit(main())
