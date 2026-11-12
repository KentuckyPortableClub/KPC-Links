#!/usr/bin/env python3
"""Release the map files (KPC owner, 2026-11-11): the public map reads data/released/ only, never the working folders.

Key runs and PRs keep writing data/outlines/ and data/us-key/ (ca-key, world-key): the WORKING copy. This copies the map files of
one area, as they are at one commit, into data/released/ and lists them in data/released/RELEASED.json:
  areas:  {"US": {"sha": ..., "time": ..., "run": ..., "files": n}}
  files:  {"outlines/US-FL.geojson.gz": [["outlines/US-FL.geojson.gz", "<sha256, 12>"]], ...}   working name -> its released file(s)
  subs:   {"canada-bounds/": {"area": "CA", "file": "canada-bounds/INDEX.json", "v": "<sha256, 12>", "files": n}}   (see below)
The pages ask for RELEASED.json first (never cached) and fetch each file as <file>?v=<its sha256>, so a changed file shows at
once and an unchanged one stays in the browser's cache.
A file over the 1 MB limit is cut into parts (parks of a key file, features of an outline file); the pages put them together.
A file under the limit is copied byte for byte, so git stores it once (same content as the working file).

  python3 .github/scripts/kpc_release.py --area US|CA|KY|world --sha <full commit sha> [--run ID] [--repo .] [--dry-run]
Offline: reads `git show <sha>:<file>` only. Fail closed: everything is built in memory first; on any error nothing is written.
--dry-run builds the same release in memory and only lists what would be written (path, bytes, new / changed / same) and removed.
Tracts, review pages, overrides and the 2-fers are not map files here (2-fers live in KPC-Data and are hidden).

Nov 11 (job 3, the Canada outlines and Kentucky freeze). The areas and where their files go (working file -> released name):
  US     data/outlines/US-XX.geojson.gz, data/us-key/US-XX.json + layers.json   -> outlines/..., us-key/...
  CA     data/ca-key/CA-XX.json + refs.json + layers.json                        -> ca-key/...
         data/canada-bounds/CA-<4 or 5 digits>.json (one official outline per park) -> canada-bounds/CA-1234.json
         (data/canada-bounds/index.json and refine-report.json are bot files no page reads: not released)
  KY     data/ky-answer-key.json                                                  -> ky/ky-answer-key.json
         the root ky-*.geojson layers in KY_LAYERS below (a reviewed list)         -> ky/ky-state-parks.geojson, ...
         (kpc-ky-data.json is not a map file here: the owner keeps it as it is for now)
  world  data/world-key/XX.json + layers.json                                    -> world-key/...
A released name never starts with "data/". A row key in files / a sub-index is the released name of the WHOLE file (part 1's name).

The Canada sub-index (subs). 2,952 Canada outline rows in RELEASED.json would grow it from about 11 KB to about 300 KB, and every
map page reads RELEASED.json fresh. So the rows of a folder named in SUBS are written to that folder's own index file instead:
  data/released/canada-bounds/INDEX.json = {"about", "area": "CA", "prefix": "canada-bounds/", "sha", "run", "time",
                                            "files": {"canada-bounds/CA-1234.json": [["canada-bounds/CA-1234.json", "<v12>"]], ...}}
  (the same row shape as RELEASED.json files; one row per line; sha / run / time are the area's release, equal to areas.CA)
and RELEASED.json keeps one small row for it:  subs["canada-bounds/"] = {"area": "CA", "file": "canada-bounds/INDEX.json",
  "v": <first 12 hex of the sha256 of INDEX.json's bytes>, "files": <rows in it>}.
How a page reads a Canada outline (the loader half, for whoever writes it):
  1. RELEASED.json: is areas.CA there? no -> not released (nothing). Is the rel in files? (never, for canada-bounds/)
  2. the rel starts with a subs prefix -> fetch data/released/<subs[p].file>?v=<subs[p].v> (cache it: the ?v= is its version) and
     check its sha and time equal areas[subs[p].area]: a sub-index of another release is never used (=> nothing, ask again later).
  3. the rel is listed there -> fetch data/released/<part>?v=<version> for each part, as for any released file; not listed -> nothing
     (no working-copy fall back). One extra fetch per page, and only when a Canada park outline is asked for.
A new release of the area always writes a new INDEX.json (its sha / time change), so its v changes too.
Pages built before subs existed ignore it: they read only areas and files (tests/test_release_ca_outlines_ky_nov11.py proves it)."""
import argparse, gzip, hashlib, json, pathlib, re, subprocess, sys, time

CAP = 1_000_000
# Nov 11 (job 3): the Kentucky layer files the pages fetch from the repo root, a REVIEWED list (not a loose pattern), so a file is
# released only when someone added it here. tests/test_release_ca_outlines_ky_nov11.py fails when a root page fetches a
# ky-*.geojson that is not on this list. Readers on main 11f908d9 (grep "ky-[a-z0-9-]*\.geojson" over the root *.js / *.html):
#   every layer: kpc-planner.js (layer table) and gis-overlays.js (bounds / trail tables); polygon layers also kpc-bounds.js ky(),
#   kpc-padus-layer.js attachKyOfficial; trails also kpc-park-control.js; ky-overlaps.geojson: finder.js, kpc-map-extras.js,
#   kpc-planner.js, kpc-maprep-check.js; the offline list kpc-offline.js names most of them.
KY_LAYERS = ('ky-dawkins.geojson', 'ky-dbnf-owned.geojson', 'ky-dbnf.geojson', 'ky-fws.geojson', 'ky-hunting-areas.geojson',
             'ky-kpc-drawn.geojson', 'ky-lecl-auto.geojson', 'ky-natural-areas.geojson', 'ky-nature-preserves.geojson', 'ky-nps.geojson',
             'ky-overlaps.geojson', 'ky-padus-parks.geojson', 'ky-pine-mountain.geojson', 'ky-sheltowee.geojson', 'ky-state-parks.geojson',
             'ky-usace.geojson', 'ky-wild-rivers.geojson', 'ky-wilderness.geojson')
# area -> sources (folder at the commit, '' = the repo root; a filename regex, or a tuple of exact names that must all be there;
# optional released prefix, default = the folder without 'data/')
AREAS = {
    'US': [('data/outlines', r'US-[A-Z]{2}\.geojson\.gz'), ('data/us-key', r'US-[A-Z]{2}\.json|layers\.json')],
    'CA': [('data/ca-key', r'CA-[A-Z]{2}\.json|refs\.json|layers\.json'), ('data/canada-bounds', r'CA-\d{4,5}\.json')],
    'KY': [('data', ('ky-answer-key.json',), 'ky'), ('', KY_LAYERS, 'ky')],
    'world': [('data/world-key', r'[A-Z]{2}\.json|layers\.json')],
}
# a released folder whose rows go to its own index file (see the docstring): prefix -> (area, index file)
SUBS = {'canada-bounds/': ('CA', 'canada-bounds/INDEX.json')}


def sources(area):
    """[(folder, pattern, released prefix)] of an area."""
    return [(s[0], s[1], s[2] if len(s) > 2 else s[0][len('data/'):]) for s in AREAS[area]]


class ReleaseError(Exception): pass


def git(repo, *a):
    r = subprocess.run(['git', *a], cwd=repo, capture_output=True)
    if r.returncode != 0: raise ReleaseError(f"git {' '.join(a)[:80]}: {r.stderr.decode('utf-8', 'replace').strip()[:160]}")
    return r.stdout


def gz(raw):
    import io
    b = io.BytesIO()
    with gzip.GzipFile(fileobj=b, mode='wb', mtime=0, compresslevel=9) as z: z.write(raw)
    return b.getvalue()


def dumps(doc): return json.dumps(doc, separators=(',', ':'), sort_keys=True, ensure_ascii=False).encode()


# ---- the ONE part scheme (KPC owner, 2026-11-11): the release cut and the working outline files (kpc_master.save_area) use it, and
# the pages' KPCREL block reads it. A file over the 1 MB cap is cut into N parts: part 1 keeps the file's own name, part i >= 2 is
# <stem>.p<i><ext> (US-AK.geojson.gz, US-AK.p2.geojson.gz, ...). Every part is a whole document of the same kind (the same header
# fields) plus kpc_part = [i, N, tag]; tag = the first 12 hex of the sha256 of the whole file, so parts of two different saves
# are never put together. Features (outline files) or parks (key files) are packed in their own order, part by part. One outline
# that alone does not fit is cut into pieces by its polygons: each piece is a Feature with the same properties plus
# kpc_piece = [k, M]; joining puts the polygons back in order (the same geometry, so the record's content hash still matches).
# Nov 11 (job 3): + plain .geojson (the Kentucky layer files), cut and named the same way (ky-usace.geojson, ky-usace.p2.geojson, ...).
EXT_RE = re.compile(r'(.*?)(\.geojson\.gz|\.geojson|\.json)$')
PART_RE = re.compile(r'^(.*?)\.p(\d+)(\.geojson\.gz|\.geojson|\.json)$')


def part_name(rel, i):
    """Part i of `rel`: part 1 is `rel` itself, part i >= 2 is <stem>.p<i><ext>."""
    if i == 1: return rel
    stem, ext = EXT_RE.match(rel).groups()
    return f'{stem}.p{i}{ext}'


def _pieces(f, budget):
    """A Feature too big for one part, cut by its polygons into pieces of about `budget` bytes (None = it cannot be cut)."""
    g = f.get('geometry') or {}
    if g.get('type') != 'MultiPolygon' or len(g.get('coordinates') or []) < 2: return None
    groups, cur, size = [], [], 0
    for poly in g['coordinates']:
        n = len(dumps(poly))
        if cur and size + n > budget: groups.append(cur); cur, size = [], 0
        cur.append(poly); size += n
    groups.append(cur)
    if len(groups) < 2: return None
    return [dict(f, geometry={'type': 'MultiPolygon', 'coordinates': c}, kpc_piece=[k + 1, len(groups)]) for k, c in enumerate(groups)]


def split(rel, doc, cap=None, pack=None):
    """[(part name, bytes)] for a document that does not fit in one file. pack(name, part doc) -> bytes (default: the release's own
    gzip / json). Deterministic: the same document always gives the same parts."""
    cap = cap or CAP; is_gz = rel.endswith('.gz')
    pack = pack or ((lambda name, d: gz(dumps(d))) if is_gz else (lambda name, d: dumps(d)))
    if isinstance(doc.get('features'), list): items, field = doc['features'], 'features'
    elif isinstance(doc.get('parks'), dict): items, field = sorted(doc['parks'].items()), 'parks'
    else: raise ReleaseError(f'{rel}: it is over the limit and it has no parks / features to cut by')
    whole = dumps(doc); tag = hashlib.sha256(whole).hexdigest()[:12]
    size = (lambda it: len(dumps(it))) if field == 'features' else (lambda it: len(dumps({it[0]: it[1]})))
    ratio = max(1.0, len(whole) / max(1, len(pack(rel, doc))))       # how much the packing shrinks this kind of text
    budget = cap * ratio * 0.9
    for _ in range(60):
        chunks, cur, used = [], [], 0
        for it in items:
            n = size(it)
            if n > budget and field == 'features':
                ps = _pieces(it, budget)
                if ps:
                    if cur: chunks.append(cur); cur, used = [], 0
                    chunks += [[p] for p in ps]; continue
            if cur and used + n > budget: chunks.append(cur); cur, used = [], 0
            cur.append(it); used += n
        if cur: chunks.append(cur)
        out = []
        for i, chunk in enumerate(chunks):
            d = dict(doc); d[field] = chunk if field == 'features' else dict(chunk); d['kpc_part'] = [i + 1, len(chunks), tag]
            out.append((part_name(rel, i + 1), pack(part_name(rel, i + 1), d)))
        if len(out) > 1 and all(len(b) <= cap for _, b in out): return out
        budget *= 0.85
    raise ReleaseError(f'{rel}: could not be cut into parts under the limit')


def canon(doc):
    """A content hash of a document (sorted keys, no spaces): the same features / parks in the same order = the same hash."""
    return hashlib.sha256(dumps(doc)).hexdigest()


def cut(rel, raw, cap=None):
    """[(released name, bytes)]: the file itself when it fits, else parts under the cap (the part scheme above). Nov 11: parts that
    do not join back to the very same document (canon) are an error, never released."""
    cap = cap or CAP
    if len(raw) <= cap: return [(rel, raw)]
    doc = load_doc(rel, raw)
    if not isinstance(doc, dict): raise ReleaseError(f'{rel}: it is over the limit and it is not a document that can be cut')
    out = split(rel, doc, cap)
    if canon(join([load_doc(n, b) for n, b in out])) != canon(doc): raise ReleaseError(f'{rel}: its parts do not join back to the same file')
    return out


def load_doc(rel, raw): return json.loads(gzip.decompress(raw) if rel.endswith('.gz') else raw)


def join(docs):
    """Put parts back into one document (the Python twin of the pages' KPCREL join). Raises ReleaseError on a missing part, parts of
    two different saves, or a missing piece: never half a file."""
    if any(d is None for d in docs): raise ReleaseError('a part is missing')
    k0 = docs[0].get('kpc_part')
    if not k0: return docs[0]
    if len(docs) != k0[1] or any((d.get('kpc_part') or [None])[:3] != [i + 1, k0[1], *k0[2:3]] for i, d in enumerate(docs)):
        raise ReleaseError(f'the parts do not belong together (part 1 says {k0})')
    out = dict(docs[0]); out.pop('kpc_part', None)
    if isinstance(out.get('features'), list):
        feats, by = [], {}
        for f in (f for d in docs for f in d.get('features') or []):
            kp = f.get('kpc_piece') if isinstance(f, dict) else None
            if not kp: feats.append(f); continue
            ref = (f.get('properties') or {}).get('ref'); g = by.get(ref)
            if g is None:
                g = by[ref] = [dict(f, geometry={'type': 'MultiPolygon', 'coordinates': []}), kp[1], 0]; g[0].pop('kpc_piece'); feats.append(g[0])
            if kp[0] != g[2] + 1 or kp[1] != g[1]: raise ReleaseError(f'{ref}: piece {kp} out of order')
            g[0]['geometry']['coordinates'] += f['geometry']['coordinates']; g[2] += 1
        if any(n != got for _, n, got in by.values()): raise ReleaseError('a piece of an outline is missing')
        out['features'] = feats
    elif isinstance(out.get('parks'), dict):
        out['parks'] = {k: v for d in docs for k, v in (d.get('parks') or {}).items()}
    return out


def same_content(rel, old, new):
    """The same released content in other bytes (a gzip file packed by another zlib build) is no change."""
    if old == new: return True
    try: return load_doc(rel, old) == load_doc(rel, new)
    except (OSError, EOFError, ValueError): return False


def read_parts(rel, read):
    """(names, [bytes]) of a file and its parts as its part 1 declares them. read(name) -> bytes or None. None when part 1 is missing."""
    raw = read(rel)
    if raw is None: return None
    d = load_doc(rel, raw); kp = d.get('kpc_part') if isinstance(d, dict) else None
    names = [part_name(rel, i) for i in range(1, (kp[1] if kp else 1) + 1)]
    return names, [raw] + [read(n) for n in names[1:]]


def _ls(repo, sha, folder):
    """Names in a folder at the commit; None when the folder is not there."""
    r = subprocess.run(['git', 'ls-tree', '--name-only', f'{sha}:{folder}' if folder else f'{sha}^{{tree}}'], cwd=repo, capture_output=True)
    return r.stdout.decode().split('\n') if r.returncode == 0 else None


def build(repo, area, sha, missing=None):
    """{released rel name of the whole file: [(released rel name, bytes)]} for the area at the commit. A folder of a regex source
    that is not there at the commit adds nothing and is named in `missing` (release() refuses it when files from it were
    released before). A name of an exact list that is not there is an error."""
    if area not in AREAS: raise ReleaseError(f"area must be one of {', '.join(AREAS)} (2-fers are not released from this repo)")
    if not re.fullmatch(r'[0-9a-f]{40}', sha or ''): raise ReleaseError('source_sha must be the full 40-character commit sha')
    git(repo, 'cat-file', '-e', f'{sha}^{{commit}}')
    out = {}
    for folder, pat, dest in sources(area):
        names = _ls(repo, sha, folder)
        if isinstance(pat, tuple):
            gone = [n for n in pat if n not in (names or [])]
            if gone: raise ReleaseError(f"{area}: {' '.join(gone)} not at {sha[:12]} in {folder or 'the repo root'} (the reviewed list)")
            pick = sorted(pat)
        elif names is None:
            if missing is not None: missing.append(dest + '/')
            continue
        else: pick = sorted(n for n in names if re.fullmatch(pat, n))
        for name in pick:
            rel = f'{dest}/{name}'; src = f'{folder}/{name}' if folder else name
            raw = git(repo, 'show', f'{sha}:{src}')
            d = load_doc(rel, raw)
            if isinstance(d, dict) and d.get('kpc_part'):   # a working file already in parts (the same scheme): released as it is
                def read(n, folder=folder, dest=dest):
                    s = n[len(dest) + 1:]
                    return git(repo, 'show', f"{sha}:{folder + '/' + s if folder else s}")
                names_p, raws = read_parts(rel, read)
                join([load_doc(rel, b) for b in raws])                                                  # they must belong together
                if any(len(b) > CAP for b in raws): raise ReleaseError(f'{rel}: a part is over the limit')
                out[rel] = list(zip(names_p, raws))
            else: out[rel] = cut(rel, raw)
    if not out: raise ReleaseError(f'no map file for {area} at {sha[:12]}')
    return out


def sub_bytes(head, rows):
    """A sub-index file: the head fields, then files with one row per line (valid JSON; a new release diffs row by row)."""
    h = json.dumps(head, separators=(',', ':'), sort_keys=True, ensure_ascii=False)
    lines = [json.dumps(k, ensure_ascii=False) + ':' + json.dumps(v, separators=(',', ':'), ensure_ascii=False) for k, v in sorted(rows.items())]
    return ('{' + h[1:-1] + ',"files":{\n' + ',\n'.join(lines) + '\n}}\n').encode()


def release(repo, area, sha, run='', now=None, dry_run=False):
    """Release one area. Everything (the files, every sub-index, RELEASED.json) is built and checked in memory first; on any error
    nothing is written. Other areas' rows and files are left byte for byte. dry_run=True writes nothing and returns the plan too."""
    repo = pathlib.Path(repo); root = repo / 'data' / 'released'; ip = root / 'RELEASED.json'
    missing = []
    new = build(repo, area, sha, missing)                                     # every error happens here or below, before any write
    idx = json.loads(ip.read_text(encoding='utf-8')) if ip.exists() else {}
    idx.setdefault('areas', {}); idx.setdefault('files', {})
    subs = idx.get('subs') or {}
    if not isinstance(subs, dict) or any(not isinstance(v, dict) or not isinstance(v.get('file'), str) for v in subs.values()):
        raise ReleaseError('RELEASED.json subs is not in the expected form')
    prefixes = tuple(dest + '/' for _, _, dest in sources(area))
    mine = {pre: ix for pre, (a, ix) in SUBS.items() if a == area}
    rows_now = {r: v for r, v in idx['files'].items() if r.startswith(prefixes)}
    for pre, ix in mine.items():                                              # this area's rows kept in its sub-index (the last release)
        if pre in subs:
            f = root / subs[pre]['file']
            try: rows_now.update({r: v for r, v in json.loads(f.read_text(encoding='utf-8'))['files'].items() if r.startswith(pre)})
            except (OSError, ValueError, KeyError, AttributeError) as e: raise ReleaseError(f"{subs[pre]['file']}: cannot be read ({e}); nothing was released")
    old = {p for parts in rows_now.values() for p, _ in parts}
    for pre, ix in mine.items():                                              # a file left in a sub folder by any older release
        d = root / pre.rstrip('/')
        if d.is_dir(): old |= {f.relative_to(root).as_posix() for f in d.rglob('*') if f.is_file() and f.relative_to(root).as_posix() != ix}
    for pre in missing:
        n = sum(1 for r in rows_now if r.startswith(pre))
        if n: raise ReleaseError(f'{pre} is not at {sha[:12]} but {n} file(s) from it are released: refusing to remove them all')
    keep, rows, writes = set(), {}, []
    for rel, parts in new.items():
        got = []
        for p, b in parts:
            keep.add(p); f = root / p
            if f.exists() and same_content(p, f.read_bytes(), b): b = f.read_bytes(); how = 'same'   # Nov 11: the same content in other bytes keeps the released file and its version
            else: how = 'changed' if f.exists() else 'new'
            writes.append((p, b, how)); got.append([p, hashlib.sha256(b).hexdigest()[:12]])
        rows[rel] = got
    files = {r: v for r, v in idx['files'].items() if not r.startswith(prefixes)}
    t = now or time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    head = {'sha': sha, 'time': t, 'run': str(run or ''), 'files': len(new)}
    subs = {k: v for k, v in subs.items() if k not in mine}
    for rel, got in rows.items():
        if not any(rel.startswith(pre) for pre in mine): files[rel] = got
    dead = set()
    for pre, ix in mine.items():
        sr = {rel: got for rel, got in rows.items() if rel.startswith(pre)}
        if not sr:
            if (root / ix).exists(): dead.add(ix)                              # no rows any more: the sub-index goes with them
            continue
        b = sub_bytes({'about': f'The released {pre} files of area {area}: the same rows as RELEASED.json files. Written only by kpc_release.py; '
                       f'RELEASED.json subs names this file and its version. sha / time / run = areas.{area} of the release that wrote it.',
                       'area': area, 'prefix': pre, 'sha': sha, 'time': t, 'run': str(run or '')}, sr)
        if len(b) > CAP: raise ReleaseError(f'{ix}: over the 1 MB limit ({len(b)} bytes)')
        writes.append((ix, b, 'changed' if (root / ix).exists() else 'new'))
        subs[pre] = {'area': area, 'file': ix, 'v': hashlib.sha256(b).hexdigest()[:12], 'files': len(sr)}
    idx['files'] = files
    if subs: idx['subs'] = subs
    else: idx.pop('subs', None)
    idx['about'] = ('The map files the public pages read. Written only by kpc_release.py (the by-hand Release workflow). files: working name -> '
                    '[[released file, version]]. subs: a folder whose rows are in its own index file {prefix: {area, file, v, files}}.')
    idx['areas'][area] = head
    ib = (json.dumps(idx, indent=1, sort_keys=True) + '\n').encode()
    if len(ib) > CAP: raise ReleaseError(f'RELEASED.json would be over the 1 MB limit ({len(ib)} bytes)')
    gone = sorted((old - keep - set(mine.values())) | dead)
    res = {'files': len(new), 'parts': sum(len(v) for v in new.values()), 'removed': len(gone), 'cut': sorted(r for r, v in new.items() if len(v) > 1)}
    if dry_run:
        res['plan'] = [(p, len(b), how) for p, b, how in writes] + [('RELEASED.json', len(ib), 'changed' if ip.exists() else 'new')]
        res['gone'] = gone
        return res
    for p, b, how in writes:
        if how == 'same': continue
        f = root / p; f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(b)
    for p in gone: (root / p).unlink(missing_ok=True)
    root.mkdir(parents=True, exist_ok=True); ip.write_bytes(ib)
    return res


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--area', required=True); ap.add_argument('--sha', required=True)
    ap.add_argument('--run', default=''); ap.add_argument('--repo', default=str(pathlib.Path(__file__).resolve().parents[2]))
    ap.add_argument('--dry-run', action='store_true', help='build the release in memory and list what would be written; write nothing')
    a = ap.parse_args()
    try: r = release(a.repo, a.area, a.sha, a.run, dry_run=a.dry_run)
    except (ReleaseError, ValueError, OSError) as e:
        print(f'::error title=Release::{e}. Nothing was released.'); return 1
    if a.dry_run:
        for p, n, how in r['plan']: print(f'would write {how:7} {n:>9} data/released/{p}')
        for p in r['gone']: print(f'would remove         data/released/{p}')
        print(f"DRY RUN {a.area} from {a.sha[:12]}: {r['files']} file(s) in {r['parts']} part(s), "
              f"{sum(n for p, n, how in r['plan'])} bytes listed, {sum(1 for x in r['plan'] if x[2] != 'same')} to write, {r['removed']} to remove"
              + (f"; cut to stay under 1 MB: {' '.join(r['cut'])}" if r['cut'] else '') + '. Nothing was written.')
        return 0
    print(f"::notice title=Release::{a.area} released from {a.sha[:12]}: {r['files']} file(s) in {r['parts']} part(s), {r['removed']} old file(s) removed"
          + (f"; cut to stay under 1 MB: {' '.join(r['cut'])}" if r['cut'] else ''))
    return 0


if __name__ == '__main__': sys.exit(main())
