#!/usr/bin/env python3
"""Release the map files (KPC owner, 2026-11-11): the public map reads data/released/ only, never the working folders.

Key runs and PRs keep writing data/outlines/ and data/us-key/ (ca-key, world-key): the WORKING copy. This copies the map files of
one area, as they are at one commit, into data/released/ and lists them in data/released/RELEASED.json:
  areas:  {"US": {"sha": ..., "time": ..., "run": ..., "files": n}}
  files:  {"outlines/US-FL.geojson.gz": [["outlines/US-FL.geojson.gz", "<sha256, 12>"]], ...}   working name -> its released file(s)
The pages ask for RELEASED.json first (never cached) and fetch each file as <file>?v=<its sha256>, so a changed file shows at
once and an unchanged one stays in the browser's cache.
A file over the 1 MB limit is cut into parts (parks of a key file, features of an outline file); the pages put them together.
A file under the limit is copied byte for byte, so git stores it once (same content as the working file).

  python3 .github/scripts/kpc_release.py --area US|CA|world --sha <full commit sha> [--run ID] [--repo .]
Offline: reads `git show <sha>:<file>` only. Fail closed: everything is built in memory first; on any error nothing is written.
Tracts, review pages, overrides and the 2-fers are not map files here (2-fers live in KPC-Data and are hidden)."""
import argparse, gzip, hashlib, json, pathlib, re, subprocess, sys, time

CAP = 1_000_000
AREAS = {
    'US': [('data/outlines', r'US-[A-Z]{2}\.geojson\.gz'), ('data/us-key', r'US-[A-Z]{2}\.json|layers\.json')],
    'CA': [('data/ca-key', r'CA-[A-Z]{2}\.json|refs\.json|layers\.json')],
    'world': [('data/world-key', r'[A-Z]{2}\.json|layers\.json')],
}


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
EXT_RE = re.compile(r'(.*?)(\.geojson\.gz|\.json)$')
PART_RE = re.compile(r'^(.*?)\.p(\d+)(\.geojson\.gz|\.json)$')


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


def cut(rel, raw, cap=None):
    """[(released name, bytes)]: the file itself when it fits, else parts under the cap (the part scheme above)."""
    cap = cap or CAP
    if len(raw) <= cap: return [(rel, raw)]
    return split(rel, json.loads(gzip.decompress(raw) if rel.endswith('.gz') else raw), cap)


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
    kp = load_doc(rel, raw).get('kpc_part')
    names = [part_name(rel, i) for i in range(1, (kp[1] if kp else 1) + 1)]
    return names, [raw] + [read(n) for n in names[1:]]


def build(repo, area, sha):
    """{working rel name: [(released rel name, bytes)]} for the area at the commit."""
    if area not in AREAS: raise ReleaseError(f"area must be one of {', '.join(AREAS)} (2-fers are not released from this repo)")
    if not re.fullmatch(r'[0-9a-f]{40}', sha or ''): raise ReleaseError('source_sha must be the full 40-character commit sha')
    git(repo, 'cat-file', '-e', f'{sha}^{{commit}}')
    out = {}
    for folder, pat in AREAS[area]:
        names = git(repo, 'ls-tree', '--name-only', f'{sha}:{folder}').decode().split('\n')
        for name in sorted(n for n in names if re.fullmatch(pat, n)):
            rel = f"{folder[len('data/'):]}/{name}"
            raw = git(repo, 'show', f'{sha}:{folder}/{name}')
            if (load_doc(rel, raw) or {}).get('kpc_part'):   # a working file already in parts (the same scheme): released as it is
                def read(n, folder=folder): return git(repo, 'show', f"{sha}:{folder}/{n.split('/', 1)[1]}")
                names, raws = read_parts(rel, read)
                join([load_doc(rel, b) for b in raws])                                                  # they must belong together
                if any(len(b) > CAP for b in raws): raise ReleaseError(f'{rel}: a part is over the limit')
                out[rel] = list(zip(names, raws))
            else: out[rel] = cut(rel, raw)
    if not out: raise ReleaseError(f'no map file for {area} at {sha[:12]}')
    return out


def release(repo, area, sha, run='', now=None):
    repo = pathlib.Path(repo); root = repo / 'data' / 'released'; ip = root / 'RELEASED.json'
    new = build(repo, area, sha)                                              # every error happens here, before any write
    idx = json.loads(ip.read_text(encoding='utf-8')) if ip.exists() else {}
    idx.setdefault('areas', {}); idx.setdefault('files', {})
    prefixes = tuple(f[len('data/'):] + '/' for f, _ in AREAS[area])
    old = {p for rel, parts in idx['files'].items() if rel.startswith(prefixes) for p, _ in parts}
    idx['files'] = {rel: v for rel, v in idx['files'].items() if not rel.startswith(prefixes)}
    keep = set()
    for rel, parts in new.items():
        got = []
        for p, b in parts:
            keep.add(p); f = root / p; f.parent.mkdir(parents=True, exist_ok=True)
            if f.exists() and same_content(p, f.read_bytes(), b): b = f.read_bytes()   # Nov 11: the same content in other bytes keeps the released file and its version
            else: f.write_bytes(b)
            got.append([p, hashlib.sha256(b).hexdigest()[:12]])
        idx['files'][rel] = got
    for p in old - keep: (root / p).unlink(missing_ok=True)
    idx['about'] = 'The map files the public pages read. Written only by kpc_release.py (the by-hand Release workflow). files: working name -> [[released file, version]].'
    idx['areas'][area] = {'sha': sha, 'time': now or time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'run': str(run or ''), 'files': len(new)}
    ip.write_text(json.dumps(idx, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    return {'files': len(new), 'parts': sum(len(v) for v in new.values()), 'removed': len(old - keep), 'cut': sorted(r for r, v in new.items() if len(v) > 1)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--area', required=True); ap.add_argument('--sha', required=True)
    ap.add_argument('--run', default=''); ap.add_argument('--repo', default=str(pathlib.Path(__file__).resolve().parents[2]))
    a = ap.parse_args()
    try: r = release(a.repo, a.area, a.sha, a.run)
    except (ReleaseError, ValueError, OSError) as e:
        print(f'::error title=Release::{e}. Nothing was released.'); return 1
    print(f"::notice title=Release::{a.area} released from {a.sha[:12]}: {r['files']} file(s) in {r['parts']} part(s), {r['removed']} old file(s) removed"
          + (f"; cut to stay under 1 MB: {' '.join(r['cut'])}" if r['cut'] else ''))
    return 0


if __name__ == '__main__': sys.exit(main())
