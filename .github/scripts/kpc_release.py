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


def cut(rel, raw, cap=None):
    """[(released name, bytes)]: the file itself when it fits, else parts under the cap."""
    cap = cap or CAP
    if len(raw) <= cap: return [(rel, raw)]
    is_gz = rel.endswith('.gz'); doc = json.loads(gzip.decompress(raw) if is_gz else raw)
    if isinstance(doc.get('features'), list): items, field = doc['features'], 'features'
    elif isinstance(doc.get('parks'), dict): items, field = sorted(doc['parks'].items()), 'parks'
    else: raise ReleaseError(f'{rel}: {len(raw):,} bytes is over the limit and it has no parks / features to cut by')
    pack = (lambda d: gz(dumps(d))) if is_gz else dumps
    stem, ext = re.match(r'(.*?)(\.geojson\.gz|\.json)$', rel).groups()
    for n in range(2, 200):
        size = -(-len(items) // n); parts = []
        for i in range(n):
            d = dict(doc); chunk = items[i * size:(i + 1) * size]
            d[field] = chunk if field == 'features' else dict(chunk)
            d['kpc_part'] = [i + 1, n]
            parts.append((f'{stem}.p{i + 1}{ext}', pack(d)))
        if all(len(b) <= cap for _, b in parts): return parts
    raise ReleaseError(f'{rel}: could not be cut into parts under the limit')


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
            out[rel] = cut(rel, git(repo, 'show', f'{sha}:{folder}/{name}'))
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
        idx['files'][rel] = [[p, hashlib.sha256(b).hexdigest()[:12]] for p, b in parts]
        for p, b in parts:
            keep.add(p); f = root / p; f.parent.mkdir(parents=True, exist_ok=True)
            if not f.exists() or f.read_bytes() != b: f.write_bytes(b)
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
