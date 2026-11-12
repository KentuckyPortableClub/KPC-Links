#!/usr/bin/env python3
"""kpc_layer_intake.py: the match-and-trim layer bot (KPC owner, 2026-11-11). One allowed raw layer in, two outputs out.
Plain words: data/outlines/README.md, "The layer intake bot".

  Input   a saved copy already in hand: release:layer-intake/<asset> (KPC-Archive), release:boundary-cache/<asset> (KPC-Links), a
          direct official file URL that live_ok and robots.txt allow, or (box runs and tests) a local path. A small sidecar JSON says
          what the file is (area, layer, source_url, license, expected = the layer's own full count, the match fields). The file
          must hold exactly that count: fewer is a short read (exit 2), more means the count is not this file's (exit 3).
  Output 1  ORIGINAL: the bytes untouched, on the KPC-Archive release `layer-originals` (parts under 2 GB when bigger) with a sidecar
          JSON (sha256, size, record count, source URL, licence, date). Never in git, never on a Pages site. The facts (no licence
          text) go to data/outlines/raw-manifest.json (raw_add_facts), except a US area: the master step records a US original
          when it merges a US hand file (same sha256 = already applied), as import-existing already does.
  Output 2  TRIMMED: the park-relevant records (matched to a POTA park, or holding a POTA pin / a same-name outline near one, so a
          later trim of the file cannot settle an ambiguity by omission; checked: the same trim of the trimmed file gives the very
          same parks and record ids, else nothing is kept), in the existing formats:
            - a checked hand file hand-<AREA>.<layer>.geojson.gz (meta trimmed: true, count_full);
            - W-XX: a world bundle W-XX.json.gz made with the world key's OWN record builder and source id (arcgis_rec, src_id,
              read from kpc_world_key.py, never edited) at the detail the release copies are saved at, stamped by
              `bundle-manifest`, and a proposal row in world-baselines.proposed.json (never the approved file). A country the
              world key reads several sources for: the bundle is the boundary-cache copy with only this layer's records
              replaced (never by a smaller set), so the other sources' saved records are not lost; no record ids = no bundle;
            - the master records, layers.json layer entry and solver-queue CSV from `kpc_master_cli.py trim` on the FULL original
              (so the layer's baseline is its full count, never the trimmed count);
            - research-inbox rows for the leftovers (docs/research-input-format.md). Never a guessed join.

Default is a dry run: everything is built in --out (the job's artifacts) and reported; nothing goes to a release or to the repo.
--write changes the repo checkout (the workflow commits it to a prep/ branch) and uploads the original to KPC-Archive.
--upload-hand (with --write) uploads a non-US hand file to boundary-cache, never over an existing asset. A US hand file is never
uploaded by this bot: the master step trims every US hand file against the layer's full baseline, so a trimmed one would be held
as a shrink (exit 6, the US job red) or would record the trimmed count as the layer's baseline.
--upload-first-world (with --write; the owner's OK for a first trimmed copy) uploads the W-XX bundle only when boundary-cache has
no W-XX.json.gz at all (no --clobber). An existing W-XX copy is never replaced by this bot (save-check's rule).

Exit codes (kpc_master_cli's): 0 ok | 1 refused / check failed | 2 SHORT read | 3 cannot verify (no expected count) | 4 licence
block (WDPA / redistribute=no) | 5 live read not allowed | 6 shrink held
"""
import argparse, ast, csv, datetime, io, json, os, pathlib, re, shutil, subprocess, sys, tempfile
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kpc_master as M        # noqa: E402  (installs kpc_net_guard: never-contact hosts are refused process-wide)
import kpc_master_cli as CLI  # noqa: E402
from kpc_scrub import scrub, clip   # Nov 12: every log line scrubbed first, then cut

REPO = HERE.parent.parent
ARCHIVE, LINKS = 'KentuckyPortableClub/KPC-Archive', 'KentuckyPortableClub/KPC-Links'
INTAKE_TAG, ORIGINALS_TAG, CACHE_TAG = 'layer-intake', 'layer-originals', 'boundary-cache'
RELEASE_REPO = {INTAKE_TAG: ARCHIVE, ORIGINALS_TAG: ARCHIVE, 'fers-saved-live': ARCHIVE, CACHE_TAG: LINKS}
TOKEN_ENV = {ARCHIVE: 'KPC_ARCHIVE_TOKEN', LINKS: 'GITHUB_TOKEN'}
ASSET_CAP = 2 * 1024 ** 3           # GitHub's limit per release asset
PART_SIZE = 1900 * 1024 ** 2        # parts stay well under it
MAX_DOWNLOAD = 6 * 1024 ** 3        # a direct official file larger than this is stopped (a split needs the same space again on the runner)
GH_URL_RE = re.compile(r'^https://github\.com/KentuckyPortableClub/(KPC-Archive|KPC-Links)/releases/download/([\w.-]+)/([^/?#]+)$')
WORLD_DETAIL, WORLD_THIN = '0.002', '250'   # the detail the release copies are saved at (kpc-world-cache.yml GEO_DETAIL / GEO_THIN; the test compares)
BY = 'KPC owner (layer intake)'
WHY_TRIMMED = 'the park-relevant records only: matched to a POTA park, or holding a POTA pin or a same-name outline near one'


class Refused(M.MasterError): pass


def notice(t, m): CLI.notice(t, m)
def err(t, m): CLI.err(t, m)


# ---- gh: the only network this bot makes besides an allowed direct official file ----------------------------------------------
class Gh:
    """gh with the token for that repo (KPC-Archive: KPC_ARCHIVE_TOKEN; KPC-Links: GITHUB_TOKEN). Tests pass a stand-in."""
    def run(self, args, repo):
        env = dict(os.environ)
        tok = os.environ.get(TOKEN_ENV.get(repo, '')) or ''
        if tok: env['GH_TOKEN'] = tok
        r = subprocess.run(['gh', *args, '-R', repo], capture_output=True, text=True, env=env)
        return r.returncode, r.stdout, r.stderr

    def assets(self, tag, repo):
        """Asset names of a release; None when it cannot be read (the release missing, or no access): the caller fails closed."""
        rc, out, _ = self.run(['release', 'view', tag, '--json', 'assets'], repo)
        if rc != 0: return None
        try: return {a['name'] for a in json.loads(out).get('assets') or []}
        except Exception: return None  # noqa: BLE001

    def download(self, tag, asset, dest, repo):
        rc, _, e = self.run(['release', 'download', tag, '-p', asset, '-D', str(dest), '--clobber'], repo)
        if rc != 0: raise Refused(f'{tag}/{asset}: could not be downloaded from {repo} ({clip(e.strip(), 200)})')
        return pathlib.Path(dest) / asset

    def upload(self, tag, paths, repo):
        """Never --clobber: an asset of the same name already there makes gh fail, so nothing is replaced, even in a race."""
        rc, _, e = self.run(['release', 'upload', tag, *map(str, paths)], repo)
        if rc != 0: raise Refused(f'upload to {repo} {tag} failed (exit {rc}): {clip(e.strip(), 200)}')


# ---- the sidecar: what the file is ------------------------------------------------------------------------------------------------
def load_sidecar(spec, gh, work):
    """spec: inline JSON, a local path, or release:<tag>/<asset> (a sidecar next to the intake asset)."""
    s = str(spec or '').strip()
    if not s: raise Refused('no sidecar: say what the file is (area, layer, source_url, license, expected)')
    if s.startswith('{'): return json.loads(s)
    m = re.fullmatch(r'release:([\w.-]+)/(.+)', s)
    if m: return json.loads(fetch_input(s, work, gh).read_text(encoding='utf-8'))
    return json.loads(pathlib.Path(s).read_text(encoding='utf-8'))


def _list(v): return [x.strip() for x in (v.split(',') if isinstance(v, str) else (v or [])) if str(x).strip()]


def check_sidecar(sc, layers_doc):
    """-> the normalized sidecar. Raises Refused (exit 1) or, for a missing count, returns it with expected None (exit 3)."""
    sc = dict(sc or {})
    area, layer = str(sc.get('area') or ''), str(sc.get('layer') or '')
    if not M.AREA_RE.match(area): raise Refused(f'area {area!r} is not US-XX / CA-XX / CA-ALL / W-XX')
    if not re.fullmatch(r'\w+', layer, re.ASCII): raise Refused(f'layer {layer!r}: letters, digits and _ only (it is part of the hand file name)')
    for k in ('source_url', 'license'):
        if not str(sc.get(k) or '').strip(): raise Refused(f'the sidecar has no {k} (the original is recorded with its source and licence)')
    key = str(sc.get('layer_key') or f'{area}.{layer}')
    L = (layers_doc.get('layers') or {}).get(key) or {}
    exp = sc.get('expected', L.get('expected_count'))
    if exp is not None and (not isinstance(exp, int) or isinstance(exp, bool) or exp <= 0): raise Refused(f'expected {exp!r} is not a positive count')
    out = {'area': area, 'layer': layer, 'layer_key': key, 'source_url': str(sc['source_url']).strip(), 'page': str(sc.get('page') or ''),
           'license': str(sc['license']).strip(), 'label': str(sc.get('label') or L.get('agency') or ''), 'agency': str(sc.get('agency') or L.get('agency') or sc.get('label') or ''),
           'expected': exp, 'id_fields': _list(sc.get('id_fields') or L.get('id_fields')), 'name_fields': _list(sc.get('name_fields') or L.get('name_fields')),
           'record_id_field': str(sc.get('record_id_field') or L.get('record_id_field') or ''), 'oid_field': str(sc.get('oid_field') or sc.get('record_id_field') or 'OBJECTID'),
           'g': str(sc.get('g') or L.get('g') or 'official'), 'made_by': 'KPC owner',
           'layer_url': str(sc.get('layer_url') or L.get('url') or '')}   # the ArcGIS layer the file was saved from, when known (inbox rows)
    if out['g'] not in M.RANK: raise Refused(f"g {out['g']!r} is not one of {sorted(M.RANK)}")
    if not out['name_fields'] and not out['id_fields']: raise Refused('no name_fields and no id_fields: nothing to match a park by')
    return out


def licence_block(sc, *more, root=None):
    """'' or why the layer may not be stored or shared (WDPA / Protected Planet anywhere; redistribute=no in layers.json or
    download-sources.json). Checked before the file is even fetched, and again on the file's own name."""
    if M.is_wdpa(*[v for v in sc.values() if isinstance(v, str)], *more):
        return 'this looks like Protected Planet / WDPA: it is never stored here (not in git, not on KPC-Archive, which is public)'
    return M.share_block({'area': sc.get('area'), 'layer': sc.get('layer'), 'url': sc.get('source_url'), 'page': sc.get('page'), 'label': sc.get('label'),
                          'raw': {'name': ' '.join(str(x) for x in more)}}, root)


# ---- input -----------------------------------------------------------------------------------------------------------------------
def fetch_input(source, dest, gh):
    """A saved copy already in hand. Never a live layer read: a URL must be a direct file that live_ok and robots.txt allow."""
    s = str(source or '').strip(); dest = pathlib.Path(dest); dest.mkdir(parents=True, exist_ok=True)
    g = GH_URL_RE.match(s)
    if g: s = f'release:{g.group(2)}/{g.group(3)}'   # a release asset link: read through gh (signed in), not as a web page
    m = re.fullmatch(r'release:([\w.-]+)/(.+)', s)
    if m:
        tag, asset = m.group(1), m.group(2)
        if tag not in RELEASE_REPO: raise Refused(f'release {tag!r} is not one this bot reads ({", ".join(sorted(RELEASE_REPO))})')
        return gh.download(tag, asset, dest, RELEASE_REPO[tag])
    if s.startswith(('http://', 'https://')):
        ok, why = M.live_ok(s)
        if not ok: raise M.LiveNotAllowed(why + ': give a saved copy instead (release:layer-intake/<asset>)')
        if re.search(r'/(MapServer|FeatureServer|ImageServer)(/|$)|/query\b', s, re.I):
            raise M.LiveNotAllowed(f'{s[:100]}: a live layer service, not a saved file: this bot never reads a layer live')
        name = re.sub(r'[^A-Za-z0-9._-]+', '_', M.parts(s)[1].rstrip('/').split('/')[-1] or 'layer')[:150]
        M.download_official_file(s, dest / name, max_bytes=MAX_DOWNLOAD)   # live_ok + robots.txt + pacing, every redirect hop
        return dest / name
    p = pathlib.Path(s)
    if not p.is_file(): raise Refused(f'{s}: not a release asset, an allowed URL or a file here')
    return p


# ---- matching: kpc_master.trim, the one trim -------------------------------------------------------------------------------------
def area_prefix(area): return (area[2:] if area.startswith('W-') else area[:2]) + '-'


def area_parks(parks, area):
    """This area's POTA parks only (W-AS -> AS-####; CA-XX / CA-ALL -> CA-####; US-XX -> US-####, then the state box below)."""
    pre = area_prefix(area)
    return [p for p in parks if p[0].startswith(pre)]


def us_box(area, feats):
    """A US area: only the records in the state's box, the PC helper's own step (tools/kpc_pc_helper.py state_box / in_box)."""
    import importlib.util
    sp = importlib.util.spec_from_file_location('kpc_pc_helper', REPO / 'tools' / 'kpc_pc_helper.py'); H = importlib.util.module_from_spec(sp); sp.loader.exec_module(H)
    box = H.state_box(area[3:])
    if box is None: raise Refused(f'{area}: no state box (kpc-us-states.json): the records cannot be kept to the state')
    return [f for f in feats if H.in_box(f.get('geometry'), box)]


def trim_cfg(sc, layer_url):
    return {'id_fields': sc['id_fields'], 'name_fields': sc['name_fields'], 'record_id_field': sc['record_id_field'] or None, 'g': sc['g'],
            'agency': sc['agency'], 'layer_url': layer_url, 'license': sc['license'], 'detail': M.DEFAULT_DETAIL, 'circle_m': None}


IDX = '_kpc_intake_i'


def indexed_trim(parks, feats, cfg):
    """kpc_master.trim, unchanged, with each record's position as its record id: (records, queue, {ref: [positions]}). The record
    id is only a label, so the matching is exactly the real one."""
    tagged = [{'properties': dict(CLI_props(f), **{IDX: i}), 'geometry': f.get('geometry')} for i, f in enumerate(feats)]
    recs, queue = M.trim(parks, tagged, dict(cfg, record_id_field=IDX), source_count=len(feats))
    return recs, queue, {ref: sorted(int(x) for x in r['record_ids']) for ref, r in recs.items()}


def CLI_props(f): return (f.get('properties') if 'properties' in f else f.get('attributes')) or {}


def relevant(parks, feats, cfg, matched):
    """Positions of the park-relevant records: every matched record, every record holding a POTA pin, and every record with a
    park's name within ~0.1 degree of its pin (the trim's own 'nearby' reach). A later trim of only these records sees, for every
    park, the same outlines the full trim saw, so it cannot settle an ambiguity by leaving a rival out."""
    geoms = [f.get('geometry') for f in feats]; grid = M.Grid(geoms); fields = cfg.get('name_fields') or []
    keep = {i for ix in matched.values() for i in ix}
    for ref, name, lat, lon in parks:
        for i in grid.near(lon, lat):
            if M.contains(geoms[i], lon, lat): keep.add(i)
        for i in grid.near(lon, lat, 0.1):
            if any(M.names_agree(name, CLI_props(feats[i]).get(nf)) for nf in fields): keep.add(i)
    for i, f in enumerate(feats):   # a record naming a POTA ref by the layer's own id field
        for fld in cfg.get('id_fields') or []:
            if M.REF_RE.match(str(CLI_props(f).get(fld) or '').strip().upper().replace(' ', '')): keep.add(i)
    return sorted(keep)


def same_trim(parks, feats, cfg, keep, matched):
    """'' when the trim of only the kept records joins exactly the same parks to exactly the same records; else what differs."""
    sub = [feats[i] for i in keep]
    _, _, m2 = indexed_trim(parks, sub, cfg)
    m2 = {ref: [keep[j] for j in ix] for ref, ix in m2.items()}
    if m2 == matched: return ''
    diff = sorted(set(m2) ^ set(matched)) + sorted(r for r in set(m2) & set(matched) if m2[r] != matched[r])
    return 'the trim of the trimmed records does not give the same joins (' + ', '.join(diff[:10]) + ')'


# ---- the world bundle: the world key's own record builder, read from its file ----------------------------------------------------
_WK = {}


def world_key_ns():
    """kpc_world_key.py's definitions up to and including arcgis_rec, run from the file as it is (its build runs at module level,
    so it is never imported). The file is only read: no rules hash moves. Its config (SRC, the sheet's name fields) is read from
    data/world-key/, so the cwd is the repo root while it runs."""
    if _WK: return _WK
    path = HERE / 'kpc_world_key.py'; src = path.read_text(encoding='utf-8'); tree = ast.parse(src)
    end = next(n.end_lineno for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'arcgis_rec')
    body = [n for n in tree.body if n.end_lineno <= end] + [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'src_id']   # + its source id rule
    ns = {'__file__': str(path), '__name__': 'kpc_world_key_defs'}
    cwd, hook = os.getcwd(), sys.excepthook
    env = {k: os.environ.get(k) for k in ('GEO_DETAIL', 'GEO_THIN')}
    try:
        os.environ.update(GEO_DETAIL=WORLD_DETAIL, GEO_THIN=WORLD_THIN)   # a bundle is as fine as the copies kpc-world-cache.yml saves
        os.chdir(REPO); exec(compile(ast.Module(body=body, type_ignores=[]), str(path), 'exec'), ns)   # noqa: S102
    finally:
        os.chdir(cwd); sys.excepthook = hook
        for k, v in env.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v
    _WK.update(ns); return _WK


def world_source(cc, label):
    """The world key's arcgis source row for this country with exactly this label; else Refused. A label two of the country's
    sources share is refused too: the sidecar could mean either."""
    W = world_key_ns(); rows = W['SRC'].get(cc, [])
    hit = [s for s in rows if s[0] == label and s[1] == 'arcgis']
    if len(hit) == 1 and sum(1 for s in rows if s[0] == label) == 1: return hit[0]
    if hit: raise Refused(f'W-{cc}: more than one world key source is labelled {label!r}: no bundle (a person makes that one)')
    have = [s[0] for s in rows if s[1] == 'arcgis']
    raise Refused(f'W-{cc}: no arcgis source labelled {label!r} in the world key (its labels: {"; ".join(have[:8]) or "none"}): no bundle, the world key would not read it')


def world_key_ids(cc):
    """Record ids the published world key joins (m) or lists as candidates (c) for this country: kept in the bundle too."""
    try: d = json.load(open(REPO / 'data' / 'world-key' / f'{cc}.json', encoding='utf-8'))
    except Exception: return set()  # noqa: BLE001
    return {str(q[0]) for p in (d.get('parks') or {}).values() for k in ('m', 'c') for q in (p.get(k) or []) if isinstance(q, list) and q}


def world_bundle(area, sc, feats, keep, out, gh, work):
    """W-XX.json.gz in the world key's own saved-copy form (wsave: cc, saved, detail, thin, recs; rings at 5 decimals), from the
    park-relevant records and every record the published key joins or lists. Each record is built as a live read builds it:
    the outline simplified to the saved detail, then arcgis_rec, then the source id (sid).
    A country with more than one source: the copy on boundary-cache holds the other sources' records too, so the bundle is that
    copy with ONLY this layer's records replaced (and never by a smaller set: the keep-bigger rule). No copy there yet = a first
    copy of this layer alone, said so. The asset list unreadable = no bundle (fail closed).
    -> (path, total, extra, layer records, note) or raises Refused."""
    cc = area[2:]; W = world_key_ns(); src = world_source(cc, sc['label']); label, url, sid = src[0], src[2], W['src_id'](src)
    ids = world_key_ids(cc); oidf = sc['oid_field']; today = datetime.date.today().isoformat()
    extra = [i for i, f in enumerate(feats) if i not in set(keep) and str(CLI_props(f).get(oidf)) in ids]
    use = sorted(set(keep) | set(extra))
    if not use: raise Refused(f'{area}: no park-relevant records: no bundle')
    oids = [CLI_props(feats[i]).get(oidf) for i in use]
    none = sum(1 for v in oids if v in (None, ''))
    if none: raise Refused(f"{area}: {none} of {len(use)} records have no {oidf!r}: the world key joins by record id, so no bundle (name the file's id field in the sidecar: oid_field)")
    if len({str(v) for v in oids}) != len(oids): raise Refused(f'{area}: {oidf!r} is not unique in the file: the world key joins by record id, so no bundle')
    rows = []
    for i in use:
        g = feats[i].get('geometry')
        if g and g.get('type') in ('Polygon', 'MultiPolygon'): g = M.trim_geometry(g, W['DETAIL'])
        r = W['arcgis_rec'](label, url, oidf, {'attributes': CLI_props(feats[i]), 'geometry': g}); r['sid'] = sid
        r['_r'] = [[[round(pt[0], 5), round(pt[1], 5)] for pt in ring if len(pt) >= 2] for ring in (r.get('_r') or [])]
        rows.append(r)
    blob = {'cc': cc, 'saved': today, 'detail': W['DETAIL'], 'thin': W['THIN_N'], 'recs': rows}
    full, note = {label: sc['expected']}, ''
    others = [x for x in W['SRC'].get(cc, []) if W['src_id'](x) != sid]
    if others:
        name = f'{area}.json.gz'; have = gh.assets(CACHE_TAG, LINKS)
        if have is None:
            raise Refused(f'{area}: the world key reads {len(others) + 1} sources for {cc}, and the {CACHE_TAG} asset list could not be read, so this layer '
                          f'cannot be put together with the copy already there: no bundle (fail closed)')
        if name in have:
            old = M.load_saved(gh.download(CACHE_TAG, name, pathlib.Path(work) / 'release', LINKS))
            is_mine = lambda r: r.get('sid') == sid or ('sid' not in r and r.get('src') == label)
            was = [r for r in old.get('recs') or [] if is_mine(r)]; rest = [r for r in old.get('recs') or [] if not is_mine(r)]
            if len(rows) < len(was):
                raise Refused(f'{area}: the release copy holds {len(was)} records of {label}, this trim {len(rows)}: a smaller set never replaces a saved layer: no bundle')
            full = dict((old.get('manifest') or {}).get('source_full') or {}, **full)
            blob = dict({k: v for k, v in old.items() if k != 'manifest'}, saved=today, recs=rest + rows)
            note = f"put together with the release copy: {len(rest)} records of its other source(s) kept as they are; {label}: {len(was)} replaced by {len(rows)}"
        else:
            note = f"a first copy: it holds {label} only; the world key's other {len(others)} source(s) for {cc} are not in it"
    p = pathlib.Path(out) / f'{area}.json.gz'
    M.save_saved(p, blob)
    rc = CLI.main(['bundle-manifest', str(p), '--by', 'KPC owner', *[x for k, v in sorted(full.items()) for x in ('--source-full', f'{k}={v}')],
                   '--note', f'layer intake: {sc["layer_key"]}, {len(rows)} of {sc["expected"]} records ({WHY_TRIMMED}; and every record the published key joins or lists)'
                             + (f'; {note}' if note else '')])
    if rc != 0:
        p.unlink(missing_ok=True); raise Refused(f'{p.name}: bundle-manifest refused it (exit {rc})')
    return p, len(blob['recs']), len(extra), len(rows), note


def propose_row(path, stem, total, sha, sc, dry, note=''):
    """A proposal row in world-baselines.proposed.json (never the approved file). An entry already there is not changed."""
    doc = json.loads(pathlib.Path(path).read_text(encoding='utf-8'))
    if stem in (doc.get('baselines') or {}): return f'{stem}: already proposed: not changed (a person edits that entry)'
    row = {'expected_count': total, 'kind': 'trimmed',
           'reason': f"Layer intake bundle trimmed to park features ({sc['label']}, the layer's own total {sc['expected']}); the copy carries its own manifest. "
                     + (f"{note[0].upper() + note[1:]}. " if note else '')
                     + "copy_sha256 is the stamped bundle in the job's artifacts: re-check it against the release asset before approving.",
           'copy_sha256': sha}
    if not dry:
        doc.setdefault('baselines', {})[stem] = row
        pathlib.Path(path).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    return f'{stem}: proposal row ' + ('would be added' if dry else 'added') + f' (expected_count {total}, kind trimmed)'


# ---- leftovers --------------------------------------------------------------------------------------------------------------------
INBOX_FIELDS = ['pota_ref', 'park_name', 'layer_url', 'record_id', 'official_name', 'owner', 'confidence', 'notes', 'source', 'pin_lat', 'pin_lon']


def inbox_rows(queue, parks, feats, cfg, sc, original_asset):
    """One research-inbox row per (queued park, candidate record): the records holding its pin, or with its name nearby. A queued
    park with no candidate record (a ref the park list does not hold) stays in the solver queue only."""
    by_ref = {p[0]: p for p in parks}; geoms = [f.get('geometry') for f in feats]; grid = M.Grid(geoms); out = []
    nf = (cfg.get('name_fields') or [None])[0]; rid = sc['record_id_field'] or sc['oid_field']
    for q in queue:
        p = by_ref.get(q['ref'])
        if not p: continue
        _, name, lat, lon = p
        cand = [i for i in grid.near(lon, lat) if M.contains(geoms[i], lon, lat)]
        cand += [i for i in grid.near(lon, lat, 0.1) if i not in cand and any(M.names_agree(name, CLI_props(feats[i]).get(f)) for f in cfg.get('name_fields') or [])]
        for i in cand[:6]:
            a = CLI_props(feats[i])
            out.append({'pota_ref': q['ref'], 'park_name': name, 'layer_url': sc.get('layer_url') or sc['source_url'], 'record_id': '' if a.get(rid) in (None, '') else str(a.get(rid)),
                        'official_name': str(a.get(nf) or '') if nf else '', 'owner': sc['agency'], 'confidence': '', 'notes': f"layer intake: {q['why']}",
                        'source': f"layer intake {datetime.date.today().isoformat()} (original: KPC-Archive {ORIGINALS_TAG}/{original_asset})", 'pin_lat': '', 'pin_lon': ''})
    return out


def write_csv_if_changed(path, fields, rows):
    b = io.StringIO(); w = csv.DictWriter(b, fields, lineterminator='\n'); w.writeheader(); w.writerows(rows)
    p = pathlib.Path(path)
    if p.is_file() and p.read_text(encoding='utf-8') == b.getvalue(): return False
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(b.getvalue(), encoding='utf-8'); return True


# ---- output 1: the original -------------------------------------------------------------------------------------------------------
def original_plan(path, facts, sc, count):
    """Asset names on layer-originals (parts when over 2 GB) and the sidecar. The asset name carries the sha256, so two different
    files of one layer never share a name."""
    stem = f"{sc['area']}.{sc['layer']}.{facts['sha256'][:12]}.{re.sub(r'[^A-Za-z0-9._-]+', '_', facts['name'])}"[:200]
    parts = [stem] if facts['size'] <= ASSET_CAP else [f'{stem}.part{i + 1:02d}' for i in range((facts['size'] + PART_SIZE - 1) // PART_SIZE)]
    side = {'format': 1, 'area': sc['area'], 'layer': sc['layer'], 'layer_key': sc['layer_key'], 'name': facts['name'], 'size': facts['size'], 'sha256': facts['sha256'],
            'count': count, 'expected': sc['expected'], 'source_url': sc['source_url'], 'page': sc['page'], 'license': sc['license'], 'date': facts['date'],
            'made_by': sc['made_by'], 'asset': stem, 'parts': parts,
            'about': 'An original layer file, byte for byte (KPC layer intake). Parts, when listed, are joined in order (cat) and must give sha256.'}
    return stem, side


def split(path, side, work):
    if len(side['parts']) == 1:
        p = pathlib.Path(work) / side['parts'][0]
        try: os.link(path, p)   # the asset name carries the sha256; a link needs no second copy on the runner's disk
        except OSError: shutil.copy(path, p)
        side['part_sha256'] = [side['sha256']]; return [p]
    out, shas = [], []
    with open(path, 'rb') as f:
        for name in side['parts']:
            p = pathlib.Path(work) / name; n = 0
            with open(p, 'wb') as o:
                while n < PART_SIZE:
                    b = f.read(min(1 << 24, PART_SIZE - n))
                    if not b: break
                    o.write(b); n += len(b)
            out.append(p); shas.append(M.sha256_file(p))
    side['part_sha256'] = shas
    return out


def store_original(path, side, gh, work):
    """Upload the original (and its sidecar) to KPC-Archive layer-originals. The same sha256 already there = done; another file
    under the name, or a release that cannot be read = refused (fail closed: then nothing trimmed is written either)."""
    have = gh.assets(ORIGINALS_TAG, ARCHIVE)
    if have is None: raise Refused(f'{ARCHIVE} release {ORIGINALS_TAG}: cannot be read (create the release first: ROLLOUT.md)')
    sname = side['asset'] + '.json'
    if sname in have:
        old = json.loads(gh.download(ORIGINALS_TAG, sname, pathlib.Path(work) / 'old', ARCHIVE).read_text(encoding='utf-8'))
        if old.get('sha256') == side['sha256']: return f'{side["asset"]}: already on {ORIGINALS_TAG} (same sha256): not uploaded again'
        raise Refused(f'{sname} on {ORIGINALS_TAG} names another file (sha256 {str(old.get("sha256"))[:12]}): refused')
    clash = [p for p in side['parts'] if p in have]
    if clash: raise Refused(f'{ORIGINALS_TAG} already has {", ".join(clash)} without its sidecar: refused (a person looks)')
    files = split(path, side, work)
    sp = pathlib.Path(work) / sname; sp.write_text(json.dumps(side, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    gh.upload(ORIGINALS_TAG, files, ARCHIVE)
    gh.upload(ORIGINALS_TAG, [sp], ARCHIVE)   # the sidecar last: a sidecar on the release means the parts are all there
    return f'{side["asset"]}: uploaded to {ARCHIVE} {ORIGINALS_TAG} ({len(files)} file(s) + sidecar)'


# ---- the run ----------------------------------------------------------------------------------------------------------------------
def run(a, gh=None):
    gh = gh or Gh(); dry = not a.write
    root = pathlib.Path(a.root) if a.root else M.OUTLINES
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True); work = out / '.work'; work.mkdir(exist_ok=True)
    rep = {'mode': 'dry run (nothing goes to a release or to the repo)' if dry else 'write', 'steps': []}
    say = lambda m: (rep['steps'].append(scrub(m)), print(scrub(m), flush=True))   # Nov 12: scrubbed (archive token)
    try:
        sc = check_sidecar(load_sidecar(a.sidecar, gh, work), M.load_layers(root))
        rep['sidecar'] = sc
        blk = licence_block(sc, a.source, root=root)
        if blk: raise M.LicenseBlocked(blk)
        if sc['expected'] is None:
            err('layer intake', f"{sc['layer_key']}: no expected count (the sidecar's expected = the layer's own total): a read that cannot be checked is refused"); return 3, rep
        src = fetch_input(a.source, work / 'in', gh)
        blk = licence_block(sc, src.name, root=root)
        if blk: raise M.LicenseBlocked(blk)
        facts = {'name': src.name, 'size': src.stat().st_size, 'sha256': M.sha256_file(src), 'source': sc['source_url'], 'date': datetime.date.today().isoformat()}
        feats, how = CLI.read_file(src)
        M.check_complete(sc['expected'], len(feats), src.name)   # a short read fails closed: nothing stored, nothing trimmed
        if len(feats) != sc['expected']:   # more records than the count: the count is not this file's, and it would become the layer's baseline
            err('layer intake', f"{src.name}: {len(feats)} records, but the layer's own total is given as {sc['expected']}: they must agree "
                                f"(correct expected in the sidecar): a read that cannot be checked is refused"); return 3, rep
        facts['count'] = len(feats)
        say(f"original: {facts['name']}, {facts['size']} bytes, sha256 {facts['sha256']}, {len(feats)} records ({how}; the layer's own total {sc['expected']})")
        asset, side = original_plan(src, facts, sc, len(feats))
        rep['original'] = side
        say(f"output 1: KPC-Archive {ORIGINALS_TAG}: {', '.join(side['parts'])} + {asset}.json (sidecar: sha256, size, count, source, licence, date)")

        area = sc['area']; cfg = trim_cfg(sc, sc['source_url'])
        mine = feats if not area.startswith('US-') else us_box(area, feats)
        if area.startswith('US-'): say(f'{area}: {len(mine)} of {len(feats)} records lie in the state box (the PC helper\'s step)')
        parks = area_parks(CLI.read_parks(a.parks), area)
        recs, queue, matched = indexed_trim(parks, mine, cfg)
        keep = relevant(parks, mine, cfg, matched)
        why = same_trim(parks, mine, cfg, keep, matched)
        if why: raise Refused(f'{area}: {why}: nothing trimmed is kept (fail closed)')
        nid = sum(1 for r in recs.values() if r['via'] == 'id')
        say(f"match: {len(recs)} parks ({nid} by id, {len(recs) - nid} by name + pin), {len(queue)} to the solver queue; "
            f"{len(keep)} park-relevant records of {len(mine)} kept; the trim of those gives the same joins")
        rep['match'] = {'parks': len(recs), 'by_id': nid, 'queue': len(queue), 'kept': len(keep), 'of': len(mine)}

        # output 2a: the checked hand file
        hf = out / f"hand-{area}.{sc['layer']}.geojson.gz"
        meta = {'area': area, 'layer': sc['layer'], 'url': sc['source_url'], 'label': sc['label'], 'name_field': (sc['name_fields'] or [''])[0], 'oid_field': sc['oid_field'],
                'count_expected': len(keep), 'count_full': len(mine), 'trimmed': True, 'trimmed_to': WHY_TRIMMED, 'raw': {k: facts[k] for k in ('name', 'size', 'sha256', 'source', 'date')},
                'original': f'KPC-Archive {ORIGINALS_TAG}/{asset}', 'page': sc['page'], 'by': BY, 'read': facts['date'], 'source': 'hand'}
        M.write_layer_file(hf, meta, [{'type': 'Feature', 'properties': CLI_props(mine[i]), 'geometry': M.trim_geometry(mine[i].get('geometry'))} for i in keep])
        prob = M.hand_file_problem(hf, area, sc['layer']) if M.parse_hand_name(hf.name) else f'{hf.name}: not a hand file name'
        if prob: raise Refused(prob)
        say(f'output 2: {hf.name}: {len(keep)} records ({hf.stat().st_size} bytes), checked like fill checks it')
        rep['hand'] = {'file': hf.name, 'records': len(keep), 'sha256': M.sha256_file(hf)}

        # output 2b: a world bundle
        if area.startswith('W-'):
            try:
                bp, tot, extra, nlayer, note = world_bundle(area, sc, mine, keep, out, gh, work)
                sha = M.sha256_file(bp)
                rep['bundle'] = {'file': bp.name, 'records': tot, 'layer_records': nlayer, 'sha256': sha, 'key_records_added': extra, 'note': note}
                say(f'output 2: {bp.name}: {tot} records ({nlayer} of this layer, {extra} of them only because the published key joins or lists them), '
                    f'manifest stamped, sha256 {sha}' + (f'; {note}' if note else ''))
                say(propose_row(root / 'world-baselines.proposed.json', area, tot, sha, sc, dry=True, note=note))
            except Refused as e:
                rep['bundle'] = {'refused': scrub(e)}; say(f'no world bundle: {e}')

        # leftovers
        rows = inbox_rows(queue, parks, mine, cfg, sc, asset)
        ib = out / f"layer-intake-{sc['layer_key']}.csv"; write_csv_if_changed(ib, INBOX_FIELDS, rows)
        rep['inbox'] = {'file': ib.name, 'rows': len(rows)}
        say(f'leftovers: {len(queue)} solver-queue row(s) ({sc["layer_key"]}.csv, written by trim), {len(rows)} research-inbox row(s) ({ib.name})')

        # what fill would do with a trimmed US hand file
        if area.startswith('US-'):
            say(f'{hf.name}: NOT uploaded to {CACHE_TAG} by this bot (a US area): the master step trims every US hand file against the layer\'s full '
                f'baseline, so a trimmed one would be held as a shrink or would record the trimmed count. The full original stays on KPC-Archive; '
                f'the master records come from trim on the full read (next step).')

        if dry:
            rc = trim_master(sc, src if not area.startswith('US-') else None, mine, a.parks, root, work, dry=True)
            if rc: return rc, rep
            say('dry run: nothing was uploaded and nothing in the repo was changed; the files above are in ' + str(out))
            return 0, rep

        # --write: the trim is tried first as a dry run, so a refusal (a shrink held, exit 6) stops BEFORE anything is stored;
        # then the original; nothing trimmed is written unless the original is stored
        rc = trim_master(sc, src if not area.startswith('US-') else None, mine, a.parks, root, work, dry=True)
        if rc: return rc, rep
        say(store_original(src, side, gh, work))
        if not area.startswith('US-'):   # the row is named as the asset on layer-originals: two layers' files of one name never share a row
            M.raw_add_facts(dict(facts, name=asset), root=root); say(f"raw-manifest.json: {asset} (facts only)")
        else: say('raw-manifest.json: not written for a US area (the master step records a US original when it merges a hand file)')
        rc = trim_master(sc, src if not area.startswith('US-') else None, mine, a.parks, root, work, dry=False)
        if rc: return rc, rep
        if (rep.get('bundle') or {}).get('file'):
            say(propose_row(root / 'world-baselines.proposed.json', area, rep['bundle']['records'], rep['bundle']['sha256'], sc, dry=False, note=rep['bundle'].get('note') or ''))
        if rows:
            dest = pathlib.Path(a.inbox or (REPO / 'data' / 'research-inbox')) / ib.name
            say(f'{dest.name}: ' + ('written' if write_csv_if_changed(dest, INBOX_FIELDS, rows) else 'unchanged'))
        if a.upload_hand:
            if area.startswith('US-'): say(f'{hf.name}: --upload-hand ignored for a US area (see above)')
            else:
                have = gh.assets(CACHE_TAG, LINKS)
                if have is None: say(f'{hf.name}: the {CACHE_TAG} asset list could not be read: not uploaded')
                elif hf.name in have: say(f'{hf.name}: {CACHE_TAG} has one already: not replaced (a person decides)')
                else: gh.upload(CACHE_TAG, [hf], LINKS); say(f'{hf.name}: uploaded to {CACHE_TAG}')
        b = rep.get('bundle') or {}
        if area.startswith('W-') and b.get('file'):
            if not a.upload_first_world: say(f"{b['file']}: left in the job's artifacts for Quality (upload after sign-off)")
            else:
                have = gh.assets(CACHE_TAG, LINKS)
                if have is None: say(f"{b['file']}: the {CACHE_TAG} asset list could not be read: not uploaded (a first copy cannot be told from a failed read)")
                elif b['file'] in have: say(f"{b['file']}: {CACHE_TAG} has a copy already: never replaced by a bot (save-check's rule); left in the artifacts")
                else: gh.upload(CACHE_TAG, [out / b['file']], LINKS); say(f"{b['file']}: first trimmed copy uploaded to {CACHE_TAG} (the owner's OK)")
        return 0, rep
    except M.ShortRead as e: err('layer intake SHORT READ', e); rep['error'] = scrub(e); return 2, rep
    except M.LicenseBlocked as e: err('layer intake licence', e); rep['error'] = scrub(e); return 4, rep
    except M.LiveNotAllowed as e: err('layer intake live read', e); rep['error'] = scrub(e); return 5, rep
    except (Refused, M.MasterError, ValueError) as e: err('layer intake refused', e); rep['error'] = scrub(e); return 1, rep
    finally:
        (out / 'REPORT.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=str) + '\n', encoding='utf-8')
        shutil.rmtree(work, ignore_errors=True)


def trim_master(sc, original, mine, parks_path, root, work, dry):
    """The master records, the layer's layers.json entry and its solver-queue CSV: `kpc_master_cli.py trim` on the FULL read (a
    US area: every record in the state box, the file fill itself would trim), with the full count, so the layer's baseline is
    never the trimmed count. A shrink is held for a person (exit 6)."""
    src = original
    if src is None:
        src = pathlib.Path(work) / f"{sc['area']}.{sc['layer']}.box.geojson"
        src.write_text(json.dumps({'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': CLI_props(f), 'geometry': f.get('geometry')} for f in mine]}), encoding='utf-8')
    exp = sc['expected'] if original is not None else len(mine)
    pp = pathlib.Path(work) / 'parks.json'
    pp.write_text(json.dumps([r for r in M.load_json(parks_path, []) if isinstance(r, list) and len(r) >= 2 and str(r[1]).startswith(area_prefix(sc['area']))]), encoding='utf-8')
    args = ['trim', '--layer-key', sc['layer_key'], '--input', str(src), '--expected', str(exp), '--parks', str(pp), '--area', sc['area'], '--root', str(root),
            '--agency', sc['agency'], '--license', sc['license'], '--g', sc['g']]
    if sc['id_fields']: args += ['--id-fields', ','.join(sc['id_fields'])]
    if sc['name_fields']: args += ['--name-fields', ','.join(sc['name_fields'])]
    if sc['record_id_field']: args += ['--record-id-field', sc['record_id_field']]
    if dry: args.append('--dry-run')
    rc = CLI.main(args)
    if rc: err('layer intake', f"trim {'(dry run) ' if dry else ''}refused the full read (exit {rc}): nothing more is written")
    return rc


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--source', required=True, help='release:layer-intake/<asset> | release:boundary-cache/<asset> | an allowed direct file URL | a local file')
    ap.add_argument('--sidecar', required=True, help='inline JSON, a local file, or release:layer-intake/<asset>.intake.json')
    ap.add_argument('--parks', required=True, help="KPC-Data locations-pota.json (read only; pins are never moved)")
    ap.add_argument('--out', required=True, help="the job's artifact folder: the hand file, a world bundle, the inbox rows, REPORT.json")
    ap.add_argument('--root', help='data/outlines (default: the repo\'s)'); ap.add_argument('--inbox', help='data/research-inbox (default: the repo\'s)')
    ap.add_argument('--write', action='store_true', help='not a dry run: store the original on KPC-Archive and change the repo checkout')
    ap.add_argument('--upload-hand', action='store_true', help='with --write: upload a non-US hand file to boundary-cache (never over one)')
    ap.add_argument('--upload-first-world', action='store_true', help='with --write and the owner\'s OK: upload the W-XX bundle when boundary-cache has none')
    a = ap.parse_args(argv)
    if (a.upload_hand or a.upload_first_world) and not a.write: ap.error('--upload-hand / --upload-first-world need --write')
    rc, _ = run(a)
    return rc


if __name__ == '__main__': sys.exit(main())
