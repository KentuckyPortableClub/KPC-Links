#!/usr/bin/env python3
"""kpc_world_key_join.py (Nov 11, KPC owner, 2026-11-11): the world key join puts the build groups' parts together, per COUNTRY, from the
part that OWNS each country, and fails closed on any conflict (exit 1, nothing written). Same rule as kpc_us_key_join.py. Before, the
four shared files (layers / eea-designations / jp-wikidata / outline-test) were "the biggest copy wins": a part with a stale or
partial copy that happened to be larger replaced the others.

  python3 .github/scripts/kpc_world_key_join.py parts/world-key-part-* [--out data/world-key] [--bounds data/world-bounds]
                                                [--failed-out /tmp/world-failed.txt]

A part is one build job's artifact: countries.txt (the countries it was given), failed.txt, world-key/ (index.json, <CC>.json, review/<CC>.md,
tracts/<CC>.json, and whole copies of the shared files) and world-bounds/<CC>/.
Conflicts (any one = exit 1, no file written):
  - one country in the countries.txt of two parts;
  - a part that carries <CC>.json / review / tracts / world-bounds for a country it does not own (or that has no countries.txt);
  - a shared file changed (against the join's checkout) by two parts to different values for the same key;
  - outline-test.json (keyed by country): a part that changes a country it does not own.
A shared file that is a JSON object is merged key by key (only keys a part CHANGED count as its write; nothing is deleted); one that is not
an object is a whole-file write, and two different whole-file writes conflict. Not a rule file: it never decides a join. Standard library only."""
import argparse, json, os, pathlib, re, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SHARED = ('layers.json', 'eea-designations.json', 'jp-wikidata.json', 'outline-test.json')
CC_RE = re.compile(r'^[A-Z]{2}$')
COUNTRY_KEYED = ('outline-test.json',)   # the keys of these files are country codes: a part may only change its own


class JoinConflict(Exception):
    pass


def _load(p, default=None):
    try: return json.load(open(p, encoding='utf-8'))
    except Exception: return default  # noqa: BLE001


def _words(p):
    try: return open(p, encoding='utf-8').read().split()
    except OSError: return []


def plan(parts, out):
    """Check every part first. Returns the write plan; raises JoinConflict on the first conflict."""
    out = pathlib.Path(out)
    old = _load(out / 'index.json', {}) or {}
    owner, copies, bounds, rows, failed, shared = {}, [], [], {}, [], {}
    n_parts = 0
    for d in sorted(pathlib.Path(p) for p in parts):
        if not d.is_dir(): continue
        n_parts += 1
        mine = set(_words(d / 'countries.txt'))
        for c in sorted(mine):
            if c in owner: raise JoinConflict(f'country {c} is in the countries of two parts ({owner[c]} and {d.name})')
            owner[c] = d.name
        failed += _words(d / 'failed.txt')
        wk = d / 'world-key'
        carried = [(f, f.stem) for f in wk.glob('*.json')] + [(f, f.stem) for f in (wk / 'review').glob('*.md')] + [(f, f.stem) for f in (wk / 'tracts').glob('*.json')]
        carried += [(f, f.name) for f in (d / 'world-bounds').glob('*') if f.is_dir()]
        for f, cc in carried:
            if CC_RE.match(cc) and cc not in mine:
                raise JoinConflict(f'{d.name} carries {f.relative_to(d)} but does not own {cc}' + ('' if mine else ' (it has no countries.txt)'))
        pi = (_load(wk / 'index.json', {}) or {}).get('countries', {})
        for c in sorted(mine):
            if (wk / f'{c}.json').exists():
                copies.append((wk / f'{c}.json', out / f'{c}.json'))
                if (wk / 'review' / f'{c}.md').exists(): copies.append((wk / 'review' / f'{c}.md', out / 'review' / f'{c}.md'))
                if (wk / 'tracts' / f'{c}.json').exists(): copies.append((wk / 'tracts' / f'{c}.json', out / 'tracts' / f'{c}.json'))
                if (d / 'world-bounds' / c).is_dir(): bounds.append((d / 'world-bounds' / c, c))
                if c in pi: rows[c] = pi[c]
        for name in SHARED:
            src = wk / name
            if not src.is_file(): continue
            base_p = out / name
            pj, bj = _load(src), _load(base_p)
            ent = shared.setdefault(name, {'writers': [], 'keys': {}, 'whole': None})
            if isinstance(pj, dict) and (bj is None or isinstance(bj, dict)):
                bj = bj or {}
                changed = {k: v for k, v in pj.items() if k not in bj or bj[k] != v}   # keys this part wrote (a stale copy of main is not a write)
                # Known gap (same as kpc_us_key_join.py): the build jobs check out the run's commit, this join checks out the NEWEST main. A shared
                # key changed on main between the two looks like a write by every part (all with the same old value: reverted, not a conflict;
                # for outline-test, a country the part does not own: a false conflict, red). Only the world key itself writes these files today.
                if name in COUNTRY_KEYED:
                    bad = sorted(k for k in changed if k not in mine)
                    if bad: raise JoinConflict(f'{d.name} changes {name} for {" ".join(bad)}, which it does not own')
                for k, v in changed.items():
                    if k in ent['keys'] and ent['keys'][k][0] != v:
                        raise JoinConflict(f'{name} key {k} written differently by {ent["keys"][k][1]} and {d.name}')
                    ent['keys'][k] = (v, d.name)
                if changed: ent['writers'].append((d.name, src))
            else:   # not a JSON object: a whole-file write, when it differs from the checkout's copy
                if base_p.is_file() and base_p.read_bytes() == src.read_bytes(): continue
                if ent['whole'] is not None and ent['whole'][0].read_bytes() != src.read_bytes():
                    raise JoinConflict(f'{name} sent differently by {ent["whole"][1]} and {d.name}')
                ent['whole'] = (src, d.name)
    return {'owner': owner, 'copies': copies, 'bounds': bounds, 'rows': rows, 'failed': sorted(set(failed)), 'shared': shared, 'parts': n_parts, 'old': old}


def _style(text):
    """(indent, compact, ensure_ascii) that re-writes a JSON object the way the part wrote it."""
    ascii_ = not any(ord(ch) > 127 for ch in text)   # json.dump's default escapes non-ASCII; ensure_ascii=False leaves it
    if text.startswith('{\n "') or text.startswith('{\n  "'): return 1, False, ascii_
    if text.startswith('{\n"'): return 0, False, ascii_
    return None, True, ascii_


def apply(p, out, bounds_root):
    out = pathlib.Path(out); bounds_root = pathlib.Path(bounds_root)
    (out / 'review').mkdir(parents=True, exist_ok=True)
    for src, dst in p['copies']:
        dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy(src, dst)
    for src, c in p['bounds']:
        shutil.rmtree(bounds_root / c, ignore_errors=True); shutil.copytree(src, bounds_root / c)
    for name, ent in p['shared'].items():
        if ent['whole'] is not None: shutil.copy(ent['whole'][0], out / name); continue
        if not ent['writers']: continue
        if len(ent['writers']) == 1: shutil.copy(ent['writers'][0][1], out / name); continue   # one writer: its bytes, as its own writer made them
        merged = _load(out / name, {}) or {}
        merged.update({k: v for k, (v, _) in ent['keys'].items()})
        txt = ent['writers'][0][1].read_text(encoding='utf-8')
        ind, compact, asc = _style(txt)
        keys = list(_load(ent['writers'][0][1], {}) or {})
        if keys == sorted(keys):   # written by kpc_save.save_json (layers.json): the same writer, same bytes as a serial run
            from kpc_save import canon
            body = canon(merged, ind)
        else:   # written by json.dump (jp-wikidata, outline-test): the checkout's key order kept, new keys after, same format, no re-sort diff
            body = json.dumps(merged, ensure_ascii=asc, indent=ind, **({'separators': (',', ':')} if compact else {})) + ('\n' if txt.endswith('\n') else '')
        (out / name).write_text(body, encoding='utf-8')
    n = len([1 for src, dst in p['copies'] if dst.parent == out])
    old = p['old']
    idx = dict(old.get('countries') or {}); idx.update(p['rows'])
    new = {'countries': idx}
    pb, pt = old.get('build') or old.get('previous_build'), old.get('built') or old.get('previous_built')
    if pb: new['previous_build'] = pb
    if pt: new['previous_built'] = pt
    if n:
        if not os.environ.get('KPC_STATUS_NAME'):   # the same status file the inline join wrote (data/status/inline-<workflow>.json), never one named after this script
            wf = re.sub(r'[^a-z0-9]+', '-', str(os.environ.get('GITHUB_WORKFLOW') or '').lower()).strip('-')
            os.environ['KPC_STATUS_NAME'] = 'inline-' + wf if wf else 'inline'
        from kpc_save import save_json   # the same writer the key uses
        save_json(str(out / 'index.json'), new)
    return n


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('parts', nargs='*'); ap.add_argument('--out', default='data/world-key'); ap.add_argument('--bounds', default='data/world-bounds')
    ap.add_argument('--failed-out', default='/tmp/world-failed.txt')
    a = ap.parse_args(argv)
    try:
        p = plan(a.parts, a.out)
    except JoinConflict as e:
        print(f'::error title=World key join::{e}: the parts did not join per country, nothing written (fail closed)', flush=True)
        if os.environ.get('GITHUB_OUTPUT'): open(os.environ['GITHUB_OUTPUT'], 'a').write('built=0\n')   # Save / stamp / world-bounds skip on built == '0'
        return 1
    n = apply(p, a.out, a.bounds)
    pathlib.Path(a.failed_out).write_text(''.join(f + '\n' for f in p['failed']))
    if os.environ.get('GITHUB_OUTPUT'): open(os.environ['GITHUB_OUTPUT'], 'a').write(f'built={n}\n')
    print(f"::notice title=World key join::{n} countries from {p['parts']} job(s)" + (f"; failed or unfinished: {' '.join(p['failed'])}" if p['failed'] else ''), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
