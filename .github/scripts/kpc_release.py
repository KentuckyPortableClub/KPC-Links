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

Nov 13 (KPC owner): a release can name one or more areas (country, state or province), e.g. areas="DE FR US-KY".
Each area is judged on its own. If it is green, Quality has marked it RELEASE-READY: YES, and it is no worse than
what is live now, it is promoted and the others are left alone. A held or failed area keeps its live data and never
blocks the others. RELEASED.json live records, for each area, the commit, the build id and the rules hash its live files came from.
An area is shipped only when its key-check and gate passed on the same build id (a missing or older check is refused).
US-42797939226 is never released (the refuse-list BLOCKED_BUILDS; a sha whose key index names a blocked build is refused).
Expected holds (MT) and AU (until a graded world build) are refused.
The release trims outline features for parks the key grades PIN and for refs no key lists, and refuses an area whose
outline still holds a record missing from the key's m (held land). That check is per area, so a clean state can ship
while a dirty neighbour stays on live data. The by-hand workflow stays owner-run. 2-fers are not released from this repo
(WDPA and world 2-fers stay off the public site on the KPC-Data side).

  python3 .github/scripts/kpc_release.py --area US --areas "US-KY US-OH" --sha <sha> --grade data/status/quality/verdicts.json
  python3 .github/scripts/kpc_release.py --areas "DE FR US-KY" --sha <sha> --grade <verdicts.json>

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
import argparse, tempfile, gzip, hashlib, json, pathlib, re, subprocess, sys, time

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
# Nov 13: a superseded US build that must never go live, even if a grade says YES.
BLOCKED_BUILDS = frozenset({'US-42797939226'})
# World countries that stay off a public release until a graded world build exists (Quality, Nov 13).
HELD_UNTIL_GRADED = frozenset({'AU'})
EXPECTED_HOLDS_AT = 'data/outlines/world-expected-holds.approved.json'
KEY_CHECK_PREFIX = {'US': 'us', 'CA': 'ca', 'world': 'world'}
INDEX_AT = {'US': 'data/us-key/index.json', 'CA': 'data/ca-key/index.json', 'world': 'data/world-key/index.json'}
SHARED_REL = re.compile(r'(^|/)(layers|refs)\.json$')


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



def build_source_refuse_why(repo, area, sha, units=None):
    """Why this source commit must not be built for release, or ''.
    X3: the refuse-list (US-42797939226) and the key/outlines agree check (R4/U1)
    run here in build() so a blocked or disagreeing sha cannot be packed, even if
    a caller skipped why_not_promote."""
    if area not in ('US', 'CA', 'world', 'KY'):
        return ''
    kind = area
    try:
        idx = index_at(repo, sha, kind)
    except Exception as e:  # noqa: BLE001
        return f'cannot read the {kind} key index at {sha[:12]} ({type(e).__name__})'
    builds = set()
    if isinstance(idx, dict):
        if idx.get('build'):
            builds.add(str(idx.get('build')))
        rows = idx.get('states') if isinstance(idx.get('states'), dict) else {}
        for v in rows.values():
            if isinstance(v, dict) and v.get('build'):
                builds.add(str(v.get('build')))
    hit = sorted(builds & BLOCKED_BUILDS)
    if hit:
        return f'{hit[0]} is never released'
    if kind not in ('US', 'CA', 'world'):
        return ''
    want = {u.upper() for u in units} if units else None
    if want:
        check_units = sorted(want)
    else:
        # the units of this kind at this sha (the index), not every outline file that happens to be in the tree
        idx = index_at(repo, sha, kind)
        rows = (idx or {}).get({'US': 'states', 'CA': 'provinces', 'world': 'countries'}[kind]) or {}
        if kind == 'US':
            check_units = sorted(u if str(u).startswith('US-') else f'US-{u}' for u in rows)
        elif kind == 'CA':
            check_units = sorted(u if str(u).startswith('CA-') else f'CA-{u}' for u in rows)
        else:
            check_units = sorted(str(u) for u in rows)
    for u in check_units:
        why = outline_refuse_why(repo, kind, u, sha)
        if why:
            return why if why.startswith(u) else f'{u}: {why}'
    return ''


def build(repo, area, sha, missing=None, units=None):
    """{released rel name of the whole file: [(released rel name, bytes)]} for the area at the commit. A folder of a regex source
    that is not there at the commit adds nothing and is named in `missing` (release() refuses it when files from it were
    released before). A name of an exact list that is not there is an error.
    units= limits the copy to those areas (and skips shared layers/refs): a broken file in a neighbour is never read, so it
    cannot block the areas being promoted."""
    if area not in AREAS: raise ReleaseError(f"area must be one of {', '.join(AREAS)} (2-fers are not released from this repo)")
    if not re.fullmatch(r'[0-9a-f]{40}', sha or ''): raise ReleaseError('source_sha must be the full 40-character commit sha')
    git(repo, 'cat-file', '-e', f'{sha}^{{commit}}')
    why = build_source_refuse_why(repo, area, sha, units)
    if why: raise ReleaseError(why)
    want = {u.upper() for u in units} if units else None
    pmap = parks_to_ca_unit(repo, sha) if area == 'CA' else None
    out = {}
    for folder, pat, dest in sources(area):
        names = _ls(repo, sha, folder)
        if isinstance(pat, tuple):
            gone = [n for n in pat if n not in (names or [])]
            if gone and not want: raise ReleaseError(f"{area}: {' '.join(gone)} not at {sha[:12]} in {folder or 'the repo root'} (the reviewed list)")
            pick = sorted(n for n in pat if n in (names or [])) if want else sorted(pat)
        elif names is None:
            if missing is not None: missing.append(dest + '/')
            continue
        else: pick = sorted(n for n in names if re.fullmatch(pat, n))
        for name in pick:
            rel = f'{dest}/{name}'; src = f'{folder}/{name}' if folder else name
            if want is not None:
                u = rel_unit(area, rel, pmap)
                if u is None or u not in want: continue
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



def parse_areas(text):
    """Parse areas='DE FR US-KY' into [(kind, unit), ...]. 'KY' is the Kentucky map pack; the US state is US-KY."""
    out = []
    for tok in (text or '').replace(',', ' ').split():
        t = tok.strip().upper()
        if not t: continue
        if re.fullmatch(r'US-[A-Z]{2}', t): out.append(('US', t))
        elif re.fullmatch(r'CA-[A-Z]{2}', t): out.append(('CA', t))
        elif t == 'KY': out.append(('KY', 'KY'))
        elif re.fullmatch(r'[A-Z]{2}', t) and t not in ('US', 'CA'): out.append(('world', t))
        elif t in ('US', 'CA', 'WORLD'):
            raise ReleaseError(f'{t} is a kind, not one area: name the states, provinces or countries (e.g. US-KY, CA-AB, DE)')
        else:
            raise ReleaseError(f"not an area name: {tok!r} (use US-KY, CA-AB, DE, or KY for the Kentucky map pack)")
    if not out: raise ReleaseError('areas is empty: name at least one country, state or province')
    return out


def index_at(repo, sha, kind):
    """The key index at the commit, or None when it is not there / not JSON."""
    path = INDEX_AT.get(kind)
    if not path: return None
    try: return json.loads(git(repo, 'show', f'{sha}:{path}').decode('utf-8'))
    except (ReleaseError, ValueError, OSError): return None


def unit_row(idx, kind, unit):
    if not isinstance(idx, dict): return {}
    rows = idx.get('states') or idx.get('provinces') or idx.get('countries') or {}
    key = unit.split('-', 1)[-1] if kind in ('US', 'CA') and unit.startswith(kind + '-') else unit
    return rows.get(key) or rows.get(unit) or {}


def unit_build(idx, kind, unit):
    """The build id the area's live data should record (the key's build stamp)."""
    if not isinstance(idx, dict): return ''
    return str(idx.get('build') or '')



def key_dir_and_name(kind, unit):
    """(folder under data/, key file name) for the area, or ('','') if the kind has no key file."""
    if kind == 'US':
        u = unit if str(unit).startswith('US-') else f'US-{unit}'
        return 'data/us-key', f'{u}.json'
    if kind == 'CA':
        u = unit if str(unit).startswith('CA-') else f'CA-{unit}'
        return 'data/ca-key', f'{u}.json'
    if kind == 'world':
        u = str(unit).replace('W-', '')
        return 'data/world-key', f'{u}.json'
    return '', ''


def key_dir_at(repo, sha, kind, dest):
    """Write this kind's key files at sha into dest. None when the folder is missing."""
    folder, _ = key_dir_and_name(kind, 'x')
    if not folder: return None
    names = _ls(repo, sha, folder)
    if names is None: return None
    dest = pathlib.Path(dest); dest.mkdir(parents=True, exist_ok=True)
    rx = {'US': r'US-[A-Z]{2}\.json', 'CA': r'CA-[A-Z]{2}\.json', 'world': r'[A-Z]{2}\.json'}[kind]
    import re as _re
    for n in names:
        if _re.fullmatch(rx, n):
            (dest / n).write_bytes(git(repo, 'show', f'{sha}:{folder}/{n}'))
    return dest


def area_outline_recs_at(repo, sha, kind, unit):
    """Outline records for CA / world at sha, or None when there is no area outline file (canada-bounds are per-park, not checked here)."""
    import kpc_master as M
    if kind == 'world':
        name = unit if str(unit).startswith('W-') else f'W-{unit}'
    elif kind == 'CA':
        name = unit if str(unit).startswith('CA-') else f'CA-{unit}'
    else:
        return None
    def read(n):
        r = subprocess.run(['git', 'show', f'{sha}:data/outlines/{n}'], cwd=repo, capture_output=True)
        return r.stdout if r.returncode == 0 else None
    if read(f'{name}.geojson.gz') is None:
        return None
    return M.recs_of_doc(M.load_doc_parts(f'{name}.geojson.gz', read))


def us_key_dir_at(repo, sha, dest):
    """Write the US key files at sha into dest (for outline-key agreement). Returns dest."""
    dest = pathlib.Path(dest); dest.mkdir(parents=True, exist_ok=True)
    for n in _ls(repo, sha, 'data/us-key') or []:
        if re.fullmatch(r'US-[A-Z]{2}\.json', n):
            (dest / n).write_bytes(git(repo, 'show', f'{sha}:data/us-key/{n}'))
    return dest


def us_outline_recs_at(repo, sha, unit):
    """The outline records of US-XX at sha, including part files, or {} when there is no outline file."""
    import kpc_master as M
    def read(n):
        r = subprocess.run(['git', 'show', f'{sha}:data/outlines/{n}'], cwd=repo, capture_output=True)
        return r.stdout if r.returncode == 0 else None
    if read(f'{unit}.geojson.gz') is None: return {}
    return M.recs_of_doc(M.load_doc_parts(f'{unit}.geojson.gz', read))


def outline_refuse_why(repo, kind, unit, sha):
    """Why this area's outlines must not be released, or '' when they can be trimmed and shipped.
    PIN and not-in-key features are trimmed at release; an outline that still holds a record not in the key's m refuses the area
    (live data stays). Per-area: a dirty neighbour does not block a clean state."""
    import kpc_master as M
    # KY (the map pack) and other non-key kinds have no per-area key file: they are not refused here.
    key_dir, key_name = key_dir_and_name(kind, unit)
    if not key_dir:
        return ''
    with tempfile.TemporaryDirectory() as t:
        kd = key_dir_at(repo, sha, kind, pathlib.Path(t) / 'key')
        if kd is None or not (kd / key_name).is_file():
            return f'{unit}: no key file {key_name} at {sha[:12]}: refused'
        if kind == 'US':
            recs = us_outline_recs_at(repo, sha, unit)
            recs, _, _ = M.key_fix(unit, recs, kd)
            held = M.held_record_refs(unit, recs, kd)
            if not held: return ''
            bits = [f"{r} holds {', '.join(ids)}" for r, ids in sorted(held.items())]
            return 'outline holds record(s) the key did not join: ' + '; '.join(bits)
        # CA / world: missing key already refused; held-record check when an area outline exists
        recs = area_outline_recs_at(repo, sha, kind, unit)
        if recs is None:
            return ''
        recs, _, _ = M.key_fix(unit, recs, kd)
        held = M.held_record_refs(unit, recs, kd)
        if not held: return ''
        bits = [f"{r} holds {', '.join(ids)}" for r, ids in sorted(held.items())]
        return 'outline holds record(s) the key did not join: ' + '; '.join(bits)


def trim_built_outlines(repo, sha, built, units=None):
    """In a US build dict, drop PIN and not-in-key outline features and rewrite those files. Raises ReleaseError if a
    remaining feature still holds a record missing from the key's m (whole-kind release fail-closed). units limits the
    check to the areas being promoted."""
    import kpc_master as M
    want = {u.upper() for u in units} if units else None
    outline_rels = [rel for rel in list(built) if rel.startswith('outlines/') and rel.endswith('.geojson.gz')
                    and not M.is_part_file(pathlib.Path(rel).name) and rel_unit('US', rel) and (want is None or rel_unit('US', rel) in want)]
    if not outline_rels: return built
    with tempfile.TemporaryDirectory() as t:
        td = pathlib.Path(t); kd = us_key_dir_at(repo, sha, td / 'us-key')
        for rel in outline_rels:
            unit = rel_unit('US', rel)
            recs = us_outline_recs_at(repo, sha, unit)
            recs, drop, _ = M.key_fix(unit, recs, kd)
            held = M.held_record_refs(unit, recs, kd)
            if held:
                bits = [f"{r} holds {', '.join(ids)}" for r, ids in sorted(held.items())]
                raise ReleaseError(f'{unit}: outline holds record(s) the key did not join: ' + '; '.join(bits))
            if not drop:
                # still rewrite if the working bytes were already clean? leave them (byte-identical copy)
                continue
            root = td / 'outlines'; root.mkdir(exist_ok=True)
            M.save_area(unit, recs, root, key_dir=kd)
            # drop old parts for this unit from built, then insert the new files
            prefix = f'outlines/{unit}.'
            for k in [k for k in list(built) if k == f'outlines/{unit}.geojson.gz' or (k.startswith(f'outlines/{unit}.p') and k.endswith('.geojson.gz'))]:
                built.pop(k)
            for f in M.area_files(unit, root):
                raw = f.read_bytes()
                built[f'outlines/{f.name}'] = cut(f'outlines/{f.name}', raw)
    return built


def parks_to_ca_unit(repo, sha):
    """CA park ref -> CA-XX at the commit (for canada-bounds files of one province)."""
    out = {}
    names = _ls(repo, sha, 'data/ca-key') or []
    for n in names:
        if not re.fullmatch(r'CA-[A-Z]{2}\.json', n): continue
        unit = n[:-5]
        try: doc = json.loads(git(repo, 'show', f'{sha}:data/ca-key/{n}').decode('utf-8'))
        except (ReleaseError, ValueError): continue
        for ref in (doc.get('parks') or {}):
            out[str(ref)] = unit
    return out


def rel_unit(area, rel, pmap=None):
    """Which area a released name belongs to, or None for a shared file (layers.json, refs.json)."""
    if SHARED_REL.search(rel): return None
    if area == 'KY' or rel.startswith('ky/'): return 'KY'
    base = pathlib.PurePosixPath(rel).name
    m = re.match(r'((?:US|CA)-[A-Z]{2})(?:\.p\d+)?\.(?:json|geojson)', base)
    if m: return m.group(1)
    m = re.match(r'([A-Z]{2})(?:\.p\d+)?\.json$', base)
    if area == 'world' and m: return m.group(1)
    m = re.match(r'(CA-\d{4,5})\.json$', base)
    if m and pmap: return pmap.get(m.group(1))
    return None


def list_kind_units(repo, sha, kind):
    """Every area of a kind at the commit (from the index when it is there, else from the files)."""
    idx = index_at(repo, sha, kind)
    if kind == 'KY': return ['KY']
    if isinstance(idx, dict):
        rows = idx.get('states') or idx.get('provinces') or idx.get('countries') or {}
        if kind == 'US': return [f'US-{k}' if not str(k).startswith('US-') else str(k) for k in rows]
        if kind == 'CA': return [f'CA-{k}' if not str(k).startswith('CA-') else str(k) for k in rows]
        return [str(k) for k in rows]
    names = _ls(repo, sha, {'US': 'data/us-key', 'CA': 'data/ca-key', 'world': 'data/world-key'}.get(kind) or '') or []
    out = []
    for n in names:
        if kind == 'US' and re.fullmatch(r'US-[A-Z]{2}\.json', n): out.append(n[:-5])
        elif kind == 'CA' and re.fullmatch(r'CA-[A-Z]{2}\.json', n): out.append(n[:-5])
        elif kind == 'world' and re.fullmatch(r'[A-Z]{2}\.json', n): out.append(n[:-5])
    return out


def is_green(idx, kind, unit):
    """(ok, why). A held or failed area is not green. KY (the map pack) has no key index."""
    if kind == 'KY': return True, ''
    if not isinstance(idx, dict): return False, 'no key index at this commit: cannot tell if the area is green'
    key = unit.split('-', 1)[-1] if kind in ('US', 'CA') and unit.startswith(kind + '-') else unit
    failed = idx.get('failed') or []
    if key in failed or unit in failed: return False, 'this area failed in the build'
    held = idx.get('held_expected') or idx.get('held') or []
    if isinstance(held, dict): held = list(held)
    if key in held or unit in held: return False, 'this area is held'
    row = unit_row(idx, kind, unit)
    if not row: return False, 'this area is not in the key index'
    chk = str(row.get('check') or '').lower()
    if chk in ('red', 'fail', 'failed', 'hold', 'held'): return False, f'the area check is {chk}'
    return True, ''


def outlined_n(doc):
    """Parks that have an outline (not a pin-only / empty record)."""
    n = 0
    for p in (doc.get('parks') or {}).values() if isinstance(doc, dict) else []:
        if not isinstance(p, dict): continue
        if p.get('m') or p.get('c') or (p.get('g') and p.get('g') not in ('pin', 'none', 'missing')):
            n += 1
        elif p.get('g') in ('pin', 'none', 'missing'):
            continue
        elif p: n += 1
    return n


def no_worse_than_live(repo, kind, unit, sha):
    """(ok, why). An area with fewer outlined parks than the live released file is worse, unless there is no live file yet."""
    repo = pathlib.Path(repo)
    if kind == 'KY': return True, ''
    rel = {'US': f'us-key/{unit}.json', 'CA': f'ca-key/{unit}.json', 'world': f'world-key/{unit}.json'}.get(kind)
    src = {'US': f'data/us-key/{unit}.json', 'CA': f'data/ca-key/{unit}.json', 'world': f'data/world-key/{unit}.json'}.get(kind)
    if not rel or not src: return True, ''
    live_p = repo / 'data' / 'released' / rel
    if not live_p.is_file(): return True, 'no live file yet'
    try: live = load_doc(rel, live_p.read_bytes())
    except (OSError, ValueError, ReleaseError): return True, 'live file could not be read for a count'
    try: new = json.loads(git(repo, 'show', f'{sha}:{src}').decode('utf-8'))
    except (ReleaseError, ValueError): return False, 'the new key file is missing or unreadable'
    a, b = outlined_n(live), outlined_n(new)
    if b < a: return False, f'outlined parks {a} -> {b}: worse than live'
    return True, ''


def load_grade(path):
    """A Quality verdicts.json, or None when the path is empty / the file is not there."""
    if not path: return None
    f = pathlib.Path(path)
    if not f.is_file(): return None
    try:
        d = json.loads(f.read_text(encoding='utf-8'))
        return d if isinstance(d, dict) else None
    except ValueError: return None


def grade_allows(grade, unit, sha, build):
    """(ok, why). An area is promoted only when Quality marked it RELEASE-READY: YES. Fail closed with no grade."""
    if not isinstance(grade, dict): return False, 'no Quality grade (need a verdicts.json with RELEASE-READY: YES)'
    if build in BLOCKED_BUILDS or (grade.get('build') in BLOCKED_BUILDS):
        return False, f'{next(b for b in (build, grade.get("build")) if b in BLOCKED_BUILDS)} is never released'
    gsha = str(grade.get('sha') or grade.get('head_sha') or '')
    if not gsha:
        return False, 'the grade has no sha: refused'
    if sha and not sha.startswith(gsha) and not gsha.startswith(sha):
        return False, f'the grade is for another commit ({gsha[:12]})'
    gbuild = str(grade.get('build') or '')
    if gbuild and build and gbuild != build:
        return False, f'the grade is for build {gbuild}, not {build}'
    per = (grade.get('areas') or {}).get(unit) or (grade.get('per_area') or {}).get(unit)
    if isinstance(per, dict):
        ready = str(per.get('RELEASE-READY') or per.get('release_ready') or '').strip().upper()
        if ready != 'YES': return False, 'Quality did not mark this area RELEASE-READY: YES'
        if per.get('no_worse_than_live') is False: return False, 'Quality: worse than live'
        return True, ''
    top = str(grade.get('RELEASE-READY') or grade.get('release_ready') or '').strip().upper()
    if top != 'YES': return False, f"Quality RELEASE-READY is {top or 'missing'}, not YES"
    return True, ''


def _git_show(repo, sha, path):
    """Bytes at sha:path, or None when the path is not there."""
    r = subprocess.run(['git', 'show', f'{sha}:{path}'], cwd=repo, capture_output=True)
    return r.stdout if r.returncode == 0 else None


def key_check_why(repo, kind, unit, sha, build):
    """Refuse when this area has no key-check, or only an older / other-build check, for this build id.
    The per-area gate is the same-build index (is_green) plus an explicit gate: PASS on the check when present."""
    prefix = KEY_CHECK_PREFIX.get(kind)
    if not prefix or kind == 'KY': return ''
    if not build: return 'no build id on the key index: refused'
    path = f'data/status/key-check/{prefix}-{build}.json'
    raw = _git_show(repo, sha, path)
    if raw is None:
        last = _git_show(repo, sha, f'data/status/key-check/last-{prefix}.json')
        if last is not None:
            try:
                got = str((json.loads(last.decode('utf-8')) or {}).get('build') or '')
            except (ValueError, UnicodeDecodeError):
                got = ''
            if got and got != build:
                return f'key-check last-{prefix} is for {got}, not {build} (older or other check is refused)'
        return f'no key-check for {build} at {sha[:12]} (missing check is refused)'
    try:
        doc = json.loads(raw.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return f'key-check for {build} is unreadable'
    got = str((doc or {}).get('build') or '')
    if got != build:
        return f'key-check is for {got or "an empty build"}, not {build} (older or other check is refused)'
    gate = str((doc or {}).get('gate') or (doc or {}).get('GATE') or '').strip().upper()
    if not gate:
        return f'key-check has no gate field for {build}: refused'
    if gate not in ('PASS', 'OK', 'YES', 'ALL CLEAR'):
        return f'key-check gate is {gate}, not PASS, for {build}'
    return ''


def expected_hold_why(repo, kind, unit, sha):
    """Refuse expected-holds (MT) and AU until a graded world build. Other kinds are not affected."""
    if kind != 'world': return ''
    if unit in HELD_UNTIL_GRADED:
        return f'{unit} is not released until a graded world build'
    raw = _git_show(repo, sha, EXPECTED_HOLDS_AT)
    if raw is None: return f'expected-holds file is missing at {sha[:12]}: refused'
    try:
        doc = json.loads(raw.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return 'expected-holds file is unreadable: refused'
    holds = (doc or {}).get('holds') or {}
    if unit in holds or unit.replace('W-', '') in holds:
        return f'{unit} is an expected hold: live data stays'
    return ''


def why_not_promote(repo, kind, unit, sha, grade):
    """The reason an area is kept on live data, or '' when it may be promoted.
    Errors are returned as a why for THIS area only: a broken neighbour must not abort the others."""
    try:
        idx = index_at(repo, sha, kind)
        build = unit_build(idx, kind, unit)
        if build in BLOCKED_BUILDS: return f'{build} is never released'
        why = expected_hold_why(repo, kind, unit, sha)
        if why: return why
        why = key_check_why(repo, kind, unit, sha, build)
        if why: return why
        ok, why = is_green(idx, kind, unit)
        if not ok: return why
        ok, why = grade_allows(grade, unit, sha, build)
        if not ok: return why
        # Quality may already have said no_worse; still refuse a drop in outlined parks
        ok, why = no_worse_than_live(repo, kind, unit, sha)
        if not ok: return why
        why = outline_refuse_why(repo, kind, unit, sha)
        if why: return why
        return ''
    except Exception as e:  # noqa: BLE001  one area's broken file / outline must not stop the rest of the list
        return f'cannot judge this area ({type(e).__name__}: {str(e)[:160]})'


def stamp_live(idx, kind, units, sha, run, t, repo):
    """Record, for each promoted area, the commit and build its live files came from. Other areas stay as they were."""
    live = idx.get('live')
    if not isinstance(live, dict): live = {}
    idx_src = index_at(repo, sha, kind)
    for u in units:
        row = unit_row(idx_src, kind, u) or {}
        live[u] = {'kind': kind, 'sha': sha, 'build': unit_build(idx_src, kind, u),
                   'rules': str(row.get('rules') or ''), 'time': t, 'run': str(run or '')}
    idx['live'] = live
    return idx


def release(repo, area, sha, run='', now=None, dry_run=False, units=None):
    """Release one kind (US, CA, KY, world), or only the named units of that kind (Nov 13). Everything is built and checked
    in memory first; on any error nothing is written. Other kinds' (and, when units is set, other areas') rows and files are
    left byte for byte. dry_run=True writes nothing and returns the plan too. units=None = the whole kind, as before."""
    repo = pathlib.Path(repo); root = repo / 'data' / 'released'; ip = root / 'RELEASED.json'
    missing = []
    want = {u.upper() for u in units} if units else None
    new = build(repo, area, sha, missing, units=sorted(want) if want else None)  # only the units being promoted: a bad neighbour is not read
    pmap = parks_to_ca_unit(repo, sha) if area == 'CA' else None
    if area == 'US':
        new = trim_built_outlines(repo, sha, new, units=sorted(want) if want else None)
    if want:
        new = {rel: parts for rel, parts in new.items() if rel_unit(area, rel, pmap) in want}
        if not new: raise ReleaseError(f"no map file for {' '.join(sorted(want))} at {sha[:12]}")
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
    if want:
        # keep every other area of this kind (and every other kind) as it is
        files = {r: v for r, v in idx['files'].items() if rel_unit(area, r, pmap) not in want}
        old = {p for r, parts in rows_now.items() if rel_unit(area, r, pmap) in want for p, _ in parts}
        for pre, ix in mine.items():
            d = root / pre.rstrip('/')
            if d.is_dir():
                old |= {f.relative_to(root).as_posix() for f in d.rglob('*') if f.is_file()
                        and f.relative_to(root).as_posix() != ix and rel_unit(area, f.relative_to(root).as_posix(), pmap) in want}
    else:
        files = {r: v for r, v in idx['files'].items() if not r.startswith(prefixes)}
    t = now or time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    head = {'sha': sha, 'time': t, 'run': str(run or ''), 'files': len(new)}
    if not want:
        subs = {k: v for k, v in subs.items() if k not in mine}
    for rel, got in rows.items():
        if not any(rel.startswith(pre) for pre in mine): files[rel] = got
    dead = set()
    for pre, ix in mine.items():
        sr = {rel: got for rel, got in rows.items() if rel.startswith(pre)}
        if want:
            kept = {rel: got for rel, got in rows_now.items() if rel.startswith(pre) and rel_unit(area, rel, pmap) not in want}
            sr = dict(kept, **sr)
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
    if not want:
        idx['areas'][area] = head
    promoted = sorted({rel_unit(area, r, pmap) for r in new if rel_unit(area, r, pmap)})
    stamp_live(idx, area, promoted, sha, run, t, repo)
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


def release_areas(repo, sha, units, run='', now=None, dry_run=False, grade=None):
    """Promote every named area that is green, graded RELEASE-READY: YES, and no worse than live.
    Held, failed, ungraded, worse, or blocked areas keep their live data and do not block the others.
    units is a string (areas='DE FR US-KY') or a list of (kind, unit). grade is a path or a verdicts dict.
    Writes nothing until every kind has been built in memory. Returns {promoted, kept, kinds} and, when
    dry_run, the per-kind plans."""
    if isinstance(units, str): units = parse_areas(units)
    if not units: raise ReleaseError('areas is empty: name at least one country, state or province')
    if isinstance(grade, (str, pathlib.Path)): grade = load_grade(grade)
    repo = pathlib.Path(repo)
    kept, go = [], {}
    for kind, unit in units:
        why = why_not_promote(repo, kind, unit, sha, grade)
        if why:
            kept.append({'unit': unit, 'kind': kind, 'why': why})
        else:
            go.setdefault(kind, []).append(unit)
    # build every kind that has a unit to promote, in memory, before any write.
    # A kind that cannot be built keeps those areas live and does not block the other kinds.
    plans, go2 = {}, {}
    for kind, us in go.items():
        try:
            plans[kind] = release(repo, kind, sha, run, now=now, dry_run=True, units=us)
            go2[kind] = us
        except ReleaseError as e:
            for u in us:
                kept.append({'unit': u, 'kind': kind, 'why': f'this kind could not be built for release ({e})'})
    go = go2
    if dry_run:
        return {'promoted': [{'unit': u, 'kind': k} for k, us in go.items() for u in us],
                'kept': kept, 'kinds': plans, 'wrote': False}
    wrote = {}
    for kind, us in go.items():
        try:
            wrote[kind] = release(repo, kind, sha, run, now=now, dry_run=False, units=us)
        except ReleaseError as e:
            for u in us:
                kept.append({'unit': u, 'kind': kind, 'why': f'this kind could not be written ({e})'})
    return {'promoted': [{'unit': u, 'kind': k} for k, us in go.items() for u in us],
            'kept': kept, 'kinds': wrote, 'wrote': bool(wrote)}


RELEASE_LOGINS = ('KentuckyPortableClub',)   # Brandon, Nov 13 2026 8:34 AM CT (Quality regrade 3 LC)


def release_actor_ok(env=None):
    """(ok, why): only a run triggered by Brandon's login may release. Reads GITHUB_TRIGGERING_ACTOR; no variable."""
    actor = str((env if env is not None else __import__('os').environ).get('GITHUB_TRIGGERING_ACTOR') or '')
    if actor in RELEASE_LOGINS: return True, actor
    return False, f'{actor or "no triggering actor"} is not KentuckyPortableClub (the only release login): nothing was released'


def main():
    ok, why = release_actor_ok()
    if not ok:
        print(f'::error title=Release::{why}'); sys.exit(1)
    ap = argparse.ArgumentParser()
    ap.add_argument('--area', default='', help='US, CA, KY or world: every area of this kind is considered one by one when --areas is empty')
    ap.add_argument('--areas', default='', help='space-separated areas to consider (e.g. DE FR US-KY). A held area keeps its live data and does not block the others')
    ap.add_argument('--sha', required=True)
    ap.add_argument('--run', default='')
    ap.add_argument('--repo', default=str(pathlib.Path(__file__).resolve().parents[2]))
    ap.add_argument('--grade', default='', help='Quality verdicts.json (RELEASE-READY). Empty = data/status/quality/verdicts.json if it is there')
    ap.add_argument('--all-of-kind', action='store_true', help='the old whole-kind copy (no per-area grade). Not used by the owner-run workflow')
    ap.add_argument('--dry-run', action='store_true', help='build the release in memory and list what would be written; write nothing')
    a = ap.parse_args()
    grade_path = a.grade or str(pathlib.Path(a.repo) / 'data/status/quality/verdicts.json')
    try:
        if a.all_of_kind:
            if not a.area or a.area not in AREAS: raise ReleaseError(' --all-of-kind needs --area US|CA|KY|world')
            r = release(a.repo, a.area, a.sha, a.run, dry_run=a.dry_run)
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
        if a.areas.strip():
            units = parse_areas(a.areas)
        elif a.area in AREAS:
            units = [(a.area, u) for u in list_kind_units(a.repo, a.sha, a.area)]
            if not units: raise ReleaseError(f'no areas of kind {a.area} at {a.sha[:12]}')
        else:
            raise ReleaseError('name --areas (e.g. DE FR US-KY) or --area US|CA|KY|world')
        r = release_areas(a.repo, a.sha, units, a.run, dry_run=a.dry_run, grade=grade_path)
    except (ReleaseError, ValueError, OSError) as e:
        print(f'::error title=Release::{e}. Nothing was released.'); return 1
    for k in r['kept']:
        print(f"::notice title=Release::{k['unit']} kept live ({k['why']})")
    for p in r['promoted']:
        print(f"::notice title=Release::{p['unit']} promoted from {a.sha[:12]}")
    if a.dry_run:
        for kind, plan in (r.get('kinds') or {}).items():
            for path, n, how in plan.get('plan') or []: print(f'would write {how:7} {n:>9} data/released/{path}')
            for path in plan.get('gone') or []: print(f'would remove         data/released/{path}')
        print(f"DRY RUN from {a.sha[:12]}: {len(r['promoted'])} area(s) would be promoted, {len(r['kept'])} kept live. Nothing was written.")
        return 0
    if r['promoted']:
        print(f"::notice title=Release::{len(r['promoted'])} area(s) released from {a.sha[:12]}, {len(r['kept'])} kept live")
        return 0
    print('::error title=Release::no area was promoted (each was held, failed, ungraded, worse than live, or blocked). Nothing was released.')
    return 1


if __name__ == '__main__': sys.exit(main())
