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
  - Nov 11 (later): a file whose content is the same as main's (even packed into other bytes by another zlib build) is put back
    to main's own bytes, so git sees no change. Main's records are judged by the key the same way as this run's (kpc_master.key_fix):
    a record graded higher than the key allows is approximate, so main's old official copy never flips it back.
  - Nov 11 (later): main's own record for a park the key grades pin is not kept either (the same rule as kpc_master.save_area,
    kpc_master.pin_drops), so a pin outline the save dropped never comes back from main's copy. An area in parts
    (US-AK.geojson.gz + US-AK.p2.geojson.gz ...) is read, compared and put back as a whole.
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


def pick(main, run):
    """Which record is saved when both main and this run have the park."""
    if main.get('hash') == run.get('hash'): return main
    rm, rr = M.RANK.get(main.get('g'), 0), M.RANK.get(run.get('g'), 0)
    if rm != rr: return main if rm > rr else run
    if main.get('layer_url') != run.get('layer_url'): return main            # another layer, same kind: the saved one stays
    return run if str(run.get('date_read') or '') >= str(main.get('date_read') or '') else main


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
    import kpc_release as REL
    repo = pathlib.Path(repo); root = pathlib.Path(root); bad = []; n_kept = n_older = 0
    rel_root = root.resolve().relative_to(repo.resolve()).as_posix()
    rc, out = git(repo, 'ls-tree', '--name-only', f'{ref}:{rel_root}')
    if rc != 0:
        print(f'::error title=Outlines vs main::cannot list {rel_root} on {ref}: nothing was compared'); return 1
    on_main = {n for n in out.decode().split('\n') if AREA_FILE.match(n)}
    key_dir = repo / 'data' / 'us-key'

    def main_read(n):
        rc, b = git(repo, 'show', f'{ref}:{rel_root}/{n}')
        return b if rc == 0 else None

    def here_read(n): return (root / n).read_bytes() if (root / n).is_file() else None

    # a file main has and this run's folder lost is put back too
    for name in sorted(on_main | {p.name for p in root.glob('*.geojson.gz') if AREA_FILE.match(p.name)}):
        p = root / name; area = name[:-len('.geojson.gz')]
        if name not in on_main: continue                                      # a new area: nothing on main to lose
        # Nov 11: an area in parts (US-AK.geojson.gz + US-AK.p2.geojson.gz ...) is read, compared and put back as a whole
        try: main_names, main_raws = REL.read_parts(name, main_read)
        except Exception: main_names, main_raws = [name], [None]  # noqa: BLE001
        if any(b is None for b in main_raws): bad.append(f'{name}: cannot read the copy on {ref}'); continue

        def put_back():
            for n, b in zip(main_names, main_raws): (root / n).write_bytes(b)
        try:
            here = REL.read_parts(name, here_read)
            if here and here[0] == main_names and here[1] == main_raws: continue
            if here and here[0] == main_names and all(M.same_content(a, b) for a, b in zip(here[1], main_raws)):
                put_back(); continue          # the same content packed into other bytes (another zlib build): main's bytes, so git sees no change
            main = M.recs_of_doc(M.load_doc_parts(name, main_read))
            # Nov 11 (KPC owner): a park the key grades pin is no outline: main's old record for it is not brought back either
            if not p.exists():
                drop = M.pin_drops(area, main, key_dir)
                if drop: M.save_area(area, main, root, key_dir=key_dir)
                else: put_back()
                n_kept += len(main) - len(drop); print(f'::warning title=Outlines vs main::{name} was missing in this run: the copy on main is kept'); continue
            mine = M.load_area(area, root)
            pins = M.pin_drops(area, set(main) | set(mine), key_dir)
            main_ok, _, _ = M.key_fix(area, main, key_dir)      # main's records as the key allows them (pins out, grades lowered)
            mine, _, _ = M.key_fix(area, mine, key_dir)
            out_recs, kept, older = put_together(main_ok, mine, pins)
            no_pin = sorted(set(mine) & pins)
            if no_pin: print(f"::warning title=Outlines vs main::{name}: {len(no_pin)} outline(s) not saved, the key grades the park pin ({' '.join(no_pin[:8])})")
            gone = sorted(set(main) & pins)
            if gone: print(f"::notice title=Outlines vs main::{name}: {len(gone)} outline(s) on main not kept, the key grades the park pin ({' '.join(gone[:8])})")
            if set(main_ok) - set(out_recs): raise RuntimeError('the result would lose outlines main has')
            if out_recs != mine: M.save_area(area, out_recs, root, key_dir=key_dir)
            now_names, now_raws = REL.read_parts(name, here_read)
            if now_names == main_names and all(M.same_content(a, b) for a, b in zip(now_raws, main_raws)):
                put_back()                     # the result holds what main holds: main's own bytes
            if kept or older:
                n_kept += len(kept); n_older += len(older)
                print(f"::warning title=Outlines vs main::{name}: this run's file was older than main. Kept {len(kept)} outline(s) only main had"
                      f" and main's record for {len(older)} park(s) both had ({' '.join((kept + older)[:8])}{' ...' if len(kept + older) > 8 else ''})")
        except Exception as e:  # noqa: BLE001  fail closed: main's copy goes back, nothing older is written
            put_back(); bad.append(f'{name}: {type(e).__name__}: {str(e)[:120]} (the copy on main is kept; this run\'s outlines for it are not saved)')
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
