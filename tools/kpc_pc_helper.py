#!/usr/bin/env python3
"""KPC PC helper (Nov 10): the downloads a bot may not make, done by a person on a Windows (or Mac / Linux) PC, one at a time.

One command, from the KPC-Links folder:   python tools\\kpc_pc_helper.py
Plain steps are in tools/README-pc-helper.md.

What it does:
  1. reads the ONE needs-download list (KPC-Data data/needs-download.json) and keeps the open rows marked who=person
     (a row marked who=never is never opened: nobody contacts that server). Only rows that are new, never downloaded, or
     whose official source looks CHANGED are open; a downloaded row comes back only when the change check sees a change.
     `--reminders` shows the rare list of sources a bot may not check (look at those pages about every 3 months);
  2. per row: opens the layer's OFFICIAL page in your normal browser and tells you in plain words what to download;
  3. watches your Downloads folder for the new file(s), counts the records (GeoJSON or Esri JSON, also inside a .zip),
     checks the count against the baseline (what the saved copy already holds), trims the shapes with the SAME tool the
     bots use (kpc_master.trim_geometry, then a dry run of `kpc_master_cli.py trim`, fail closed), and records the raw-add facts;
  4. writes one small checked file per layer (hand-US-XX.<layer>.geojson.gz) and uploads it to the boundary-cache release
     with `gh` when you are logged in, else packs ONE upload file (kpc-hand-upload.zip) to send to the bot.
The master step in the US key workflow merges a checked file into the saved copy on its next run (count check again,
trim, raw-add, keep-bigger merge). This helper never changes a saved copy itself.

Refused (never packed or uploaded): a layer that looks like Protected Planet / WDPA, or one whose layer or download source is marked
`redistribute: "no"` in data/outlines/layers.json or download-sources.json.

Safety: this script itself contacts only GitHub (raw.githubusercontent.com for the list, and `gh` for the upload). It never
fetches an agency server: YOUR browser opens the page. Python standard library only; no passwords or keys are stored here.
"""
import argparse, datetime, gzip, hashlib, io, json, os, pathlib, shutil, subprocess, sys, tempfile, time, urllib.request, webbrowser, zipfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / '.github' / 'scripts'))
import kpc_master as M  # noqa: E402  (standard library only)

LINKS = 'KentuckyPortableClub/KPC-Links'
RAW = 'https://raw.githubusercontent.com/KentuckyPortableClub/{repo}/main/{path}'
NEEDS_URL = RAW.format(repo='KPC-Data', path='data/needs-download.json')
PARKS_URL = RAW.format(repo='KPC-Data', path='locations-pota.json')
LAYERS_URL = RAW.format(repo='KPC-Links', path='data/us-key/layers.json')
FETCH_HOSTS = {'raw.githubusercontent.com'}   # the ONLY host this script reads; anything else is refused
OK_EXT = ('.geojson', '.json', '.zip')
REMIND_DAYS = 90   # a check=person source: look at its page about every 3 months
PARTIAL = ('.crdownload', '.part', '.partial', '.tmp', '.download')


def say(*a): print(*a, flush=True)


def fetch(url, dest=None):
    host = M.parts(url)[0]
    if host not in FETCH_HOSTS: raise SystemExit(f'refused: this helper only reads GitHub, not {host}')
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'KPC-pc-helper'}), timeout=60) as r: data = r.read()
    if dest: pathlib.Path(dest).write_bytes(data)
    return data


def downloads_dir(given=None):
    if given: return pathlib.Path(given).expanduser()
    if os.name == 'nt':
        try:   # the real Downloads folder, even when it was moved (Windows keeps it in the registry)
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders') as k:
                v = winreg.QueryValueEx(k, '{374DE290-123F-4565-9164-39C4925E467B}')[0]
                return pathlib.Path(os.path.expandvars(v))
        except Exception: pass  # noqa: BLE001
    return pathlib.Path.home() / 'Downloads'


def rows_for_person(doc, only=None, layers_table=None):
    """The rows a person downloads: OPEN rows for who=person only. A row is open when it is new, was never downloaded, or its
    official source looks CHANGED (the change check reopened it). A done row is never listed again until its source changes.
    who=never is NEVER returned (nobody contacts that server)."""
    out = []
    for r in doc.get('rows') or []:
        if r.get('status') != 'open' or r.get('who') != 'person': continue
        if M.who_for(r.get('url') or '')[0] == 'never': continue   # belt and braces: the host rules say never
        if only and r.get('area') not in only and r.get('id') not in only: continue
        if not is_fillable(r, layers_table): continue
        out.append(r)
    return sorted(out, key=lambda r: (r.get('area') or '', r.get('layer') or ''))


def is_fillable(r, layers_table=None):
    """A row the US key can take a hand file for: a state (US-XX) and a layer the key reads (not url:<hash> and not a bare
    source id h<n>, which is a lead with no saved layer yet). Nov 10: with the key's layer table (data/us-key/layers.json) the
    layer must also be IN it: a hand file for a layer the key has no entry for is never merged, so it is not asked for."""
    lay = str(r.get('layer') or '')
    if not str(r.get('area') or '').startswith('US-') or lay.startswith('url:') or (lay[:1] == 'h' and lay[1:].isdigit()): return False
    return layers_table is None or not layers_table or lay in layers_table


def why_tag(r):
    if r.get('source') == 'change check': return 'CHANGED at the source'
    return 'never downloaded' if not int(r.get('have') or 0) else 'new / short'


def groups(rows):
    """One download serves every row with the same source (e.g. one national file for several states): -> [[row, ...], ...]."""
    g = {}
    for r in rows: g.setdefault(r.get('src') or r.get('page') or r.get('id'), []).append(r)
    return list(g.values())


def reminders(doc, today=None, days=None):
    """The rare reminder list: rows a bot may NOT check for a change (check=person), downloaded more than `days` days ago."""
    today = datetime.date.fromisoformat(today or datetime.date.today().isoformat()); days = days or REMIND_DAYS
    out = []
    for r in doc.get('rows') or []:
        if r.get('check') != 'person' or r.get('status') != 'done' or r.get('who') == 'never': continue
        try: age = (today - datetime.date.fromisoformat(str(r.get('added'))[:10])).days
        except ValueError: age = days
        if age >= days: out.append(r)
    return sorted(out, key=lambda r: (r.get('area') or '', r.get('layer') or ''))


def snapshot(folder):
    try: return {p.name: p.stat().st_mtime for p in folder.iterdir() if p.is_file()}
    except FileNotFoundError: return {}


def new_files(folder, before):
    """Finished new (or replaced) layer files since the snapshot; waits while a download is still running."""
    for _ in range(300):
        now = snapshot(folder)
        if any(n.lower().endswith(PARTIAL) for n in now if n not in before): time.sleep(2); continue
        got = [folder / n for n, t in now.items() if (n not in before or t > before[n]) and n.lower().endswith(OK_EXT)]
        sizes = {p: p.stat().st_size for p in got}
        time.sleep(1)
        if all(p.exists() and p.stat().st_size == s for p, s in sizes.items()): return sorted(got)
    return []


def read_features(path):
    """GeoJSON / Esri JSON features from a file or a .zip of them -> [GeoJSON Feature]."""
    p = pathlib.Path(path)
    if p.suffix.lower() == '.zip':
        out = []
        with zipfile.ZipFile(p) as z:
            for n in z.namelist():
                if n.lower().endswith(('.geojson', '.json')): out += _feats(json.loads(z.read(n).decode('utf-8-sig')))
                elif n.lower().endswith('.shp'): raise ValueError('this zip holds a Shapefile: please download the GeoJSON version instead')
        return out
    return _feats(json.loads(p.read_text(encoding='utf-8-sig')))


def _feats(doc):
    fs = doc.get('features') if isinstance(doc, dict) else doc
    out = []
    for ft in fs or []:
        if 'attributes' in ft: out.append({'type': 'Feature', 'properties': ft.get('attributes') or {}, 'geometry': M.esri_to_geojson(ft.get('geometry'))})
        else: out.append({'type': 'Feature', 'properties': ft.get('properties') or {}, 'geometry': ft.get('geometry')})
    return out


def dedupe(feats, oid_field=None):
    seen, out = set(), []
    for f in feats:
        pr = f.get('properties') or {}
        k = next((pr[x] for x in pr if oid_field and x.lower() == oid_field.lower()), None)
        if k is None: k = hashlib.sha1(json.dumps(f.get('geometry'), sort_keys=True).encode()).hexdigest()
        if k in seen: continue
        seen.add(k); out.append(f)
    return out


def state_box(st):
    try: B = json.load(open(REPO / 'kpc-us-states.json', encoding='utf-8'))
    except Exception: return None  # noqa: BLE001
    x = next((b for b in B if b.get('a') == st), None)
    if not x: return None
    xs = [q[0] for pl in x['p'] for q in pl[0]]; ys = [q[1] for pl in x['p'] for q in pl[0]]
    return [min(xs), min(ys), max(xs), max(ys)]


def in_box(g, box):
    if not box or not g: return bool(g)
    pts = [g['coordinates']] if g.get('type') == 'Point' else [pt for poly in M.polys_of(g) for ring in poly for pt in ring]
    if not pts: return False
    x0, y0 = min(p[0] for p in pts), min(p[1] for p in pts); x1, y1 = max(p[0] for p in pts), max(p[1] for p in pts)
    return not (x1 < box[0] or x0 > box[2] or y1 < box[1] or y0 > box[3])


def field(props_list, want):
    if not want: return None
    for pr in props_list:
        for k in pr:
            if k.lower() == str(want).lower(): return k
    return None


def check_and_pack(row, files, parks_path, out_dir, layers_table, today=None):
    """-> (ok, message, hand file path or None). Fail closed: short / unreadable / trim refused = nothing written."""
    today = today or datetime.date.today().isoformat()
    area, pre = row['area'], row['layer']; st = area[3:]
    blk = M.share_block(dict(row, raw={'name': ' '.join(pathlib.Path(f).name for f in files)}), REPO / 'data' / 'outlines')
    if blk: return False, 'refused: ' + blk, None   # WDPA / redistribute=no: never packed
    feats = []
    for f in files:
        try: feats += read_features(f)
        except Exception as e: return False, f'{f.name}: could not read it ({e})', None  # noqa: BLE001
    lt = layers_table.get(pre) or []
    nf = lt[1] if len(lt) > 1 else ''
    oidf = field([f['properties'] for f in feats[:50]], 'OBJECTID') or field([f['properties'] for f in feats[:50]], 'FID')
    feats = dedupe(feats, oidf)
    box = state_box(st)
    feats = [f for f in feats if in_box(f.get('geometry'), box)]
    exp = int(row.get('expected') or row.get('have') or 0)
    if not feats: return False, 'the download has no records for this state (was the right layer downloaded?)', None
    if exp and len(feats) < exp:
        return False, f'SHORT: the download has {len(feats)} records in {st}, the saved copy already has {exp}. Nothing saved (fail closed). Try the full download (no filter / all records).', None
    for f in feats: f['geometry'] = M.trim_geometry(f.get('geometry'))   # the same trim the bots use: 5 decimals, the master's detail
    nf_real = field([f['properties'] for f in feats[:50]], nf) or nf
    raw = files[0] if len(files) == 1 else None
    rawinfo = {'name': '+'.join(p.name for p in files), 'size': sum(p.stat().st_size for p in files),
               'sha256': M.sha256_file(raw) if raw else hashlib.sha256(b''.join(M.sha256_file(p).encode() for p in files)).hexdigest(),
               'source': row.get('page') or row.get('url'), 'date': today}
    meta = {'area': area, 'layer': pre, 'url': row.get('url') or '', 'label': lt[2] if len(lt) > 2 else '', 'name_field': nf_real, 'oid_field': oidf or 'OBJECTID',
            'count_expected': max(exp, 1), 'raw': rawinfo, 'page': row.get('page') or '', 'by': 'KPC owner (PC helper)', 'read': today, 'source': 'hand'}
    out = pathlib.Path(out_dir) / f'hand-{area}.{pre}.geojson.gz'
    M.write_layer_file(out, meta, feats)
    with tempfile.TemporaryDirectory() as t:   # the same trim tool, as a dry run: it must pass (count check, no WDPA) or nothing is kept
        shutil.copy(REPO / 'data' / 'outlines' / 'layers.json', pathlib.Path(t) / 'layers.json') if (REPO / 'data' / 'outlines' / 'layers.json').exists() else None
        rc = subprocess.run([sys.executable, str(REPO / '.github' / 'scripts' / 'kpc_master_cli.py'), 'trim', '--layer-key', f'{area}.{pre}', '--input', str(out),
                             '--expected', str(max(exp, 1)), '--parks', str(parks_path), '--area', area, '--root', t, '--dry-run',
                             *(['--name-fields', nf_real] if nf_real else [])], capture_output=True, text=True)
        if rc.returncode != 0:
            out.unlink(missing_ok=True)
            return False, 'the trim tool refused it (exit %d): %s' % (rc.returncode, (rc.stdout + rc.stderr).strip()[-300:]), None
        M.raw_add(out, rawinfo['source'], root=t)   # raw-add: the facts go with the file (meta.raw); the master step records them
    return True, f'OK: {len(feats)} records in {st} (baseline {exp}); checked file {out.name} ({out.stat().st_size // 1024} KB)', out


def gh_ok():
    g = shutil.which('gh')
    if not g: return None
    return g if subprocess.run([g, 'auth', 'status'], capture_output=True).returncode == 0 else None


def upload(paths, out_dir):
    keep = []
    for p in paths:   # the same refusal again, from each file's own facts: a restricted layer is never uploaded or packed
        why = M.share_block(M.read_layer_file(p)[0], REPO / 'data' / 'outlines')
        if why: say(f'Not uploaded: {pathlib.Path(p).name}: {why}')
        else: keep.append(p)
    paths = keep
    if not paths: say('Nothing left to upload.'); return None
    g = gh_ok()
    if g:
        r = subprocess.run([g, 'release', 'upload', 'boundary-cache', *map(str, paths), '-R', LINKS, '--clobber'])
        if r.returncode == 0: say(f'Uploaded {len(paths)} checked file(s) to the boundary-cache release. The next US key run merges them.'); return 'gh'
        say('The gh upload did not work; packing one upload file instead.')
    z = pathlib.Path(out_dir) / 'kpc-hand-upload.zip'
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_STORED) as zf:
        for p in paths: zf.write(p, p.name)
    say(f'Packed ONE upload file: {z}\nSend that file to the bot in chat; it uploads it for you.'); return str(z)


def main(argv=None):
    ap = argparse.ArgumentParser(description='Download the layers a bot may not fetch, one at a time (see tools/README-pc-helper.md).')
    ap.add_argument('--downloads', help='your Downloads folder (default: found automatically)')
    ap.add_argument('--only', nargs='*', help='only these areas or rows, e.g. US-AZ or US-AZ|fsod')
    ap.add_argument('--list', action='store_true', help='only show the list, open nothing')
    ap.add_argument('--needs', help='a local needs-download.json (default: the one on GitHub)')
    ap.add_argument('--out', default=str(pathlib.Path.home() / 'kpc-hand'), help='where the checked files go (default: kpc-hand in your home folder)')
    ap.add_argument('--no-upload', action='store_true')
    ap.add_argument('--reminders', action='store_true', help='show the rare reminder list (sources a bot cannot check for a change), open nothing')
    a = ap.parse_args(argv)
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    doc = json.loads(pathlib.Path(a.needs).read_text(encoding='utf-8')) if a.needs else json.loads(fetch(NEEDS_URL))
    if a.reminders:
        rem = reminders(doc)
        say(f'{len(rem)} source(s) to look at (a bot may not check them; last downloaded over {REMIND_DAYS} days ago).')
        for r in rem: say(f'  {r["area"]} {r["layer"]:8} last {str(r.get("added"))[:10]}  {r.get("page") or r.get("url")}')
        say('If a page shows a newer date or a different record count, run this helper with --only <area> after the next key run reopens it,\nor tell the bot which one changed.')
        return 0
    try: layers_table = json.loads(fetch(LAYERS_URL))
    except Exception: layers_table = {}  # noqa: BLE001
    rows = rows_for_person(doc, a.only, layers_table)
    # Nov 10: the tally counts only the rows this helper can use (open, a person's, a US layer the key reads); the rest are named
    # once as 'not asked here', never added to the count
    scope = [r for r in doc.get('rows') or [] if r.get('status') == 'open' and (not a.only or r.get('area') in a.only or r.get('id') in a.only)]
    never = sum(1 for r in scope if r.get('who') == 'never')
    other = sum(1 for r in scope if r.get('who') == 'person' and r not in rows)
    gs = groups(rows)
    say(f'{len(rows)} layer(s) to download by hand, {len(gs)} download(s).')
    if other or never:
        say('  Not asked here: ' + ', '.join(x for x in (f'{other} open row(s) this helper cannot use (Canada, world, or a layer the US key has no entry for)' if other else '',
                                                         f'{never} never-contact row(s)' if never else '') if x) + '.')
    for i, r in enumerate(rows, 1): say(f'  {i:3}. {r["area"]} {r["layer"]:8} {r["host"]}  ({why_tag(r)}; the saved copy has {r.get("have") or 0})')
    if a.list or not rows: return 0
    parks = out / 'locations-pota.json'; fetch(PARKS_URL, parks)
    dl = downloads_dir(a.downloads); say(f'Watching your Downloads folder: {dl}')
    made = []
    for i, grp in enumerate(gs, 1):
        r = grp[0]
        say('\n' + '=' * 70 + f'\n{i} of {len(gs)}: ' + ', '.join(f'{x["area"]} {x["layer"]}' for x in grp) + f' ({r["host"]})\nWhy: {why_tag(r)}: {r.get("why")}')
        hint = [x for x in str(r.get('note') or '').split() if x.startswith('http')]
        say('Your browser opens the official page now. On it:\n'
            '  - find the layer (the page shows its name),\n'
            '  - choose Download (or Export / Query) and pick GeoJSON (or JSON), ALL records, no filter,\n'
            '  - save it to your Downloads folder as usual.' + (f'\n  (the direct file, if the page links it: {hint[0]})' if hint else '') +
            ('\n  ONE download serves all the states listed above.' if len(grp) > 1 else ''))
        say(f'Page: {r.get("page") or r.get("url")}')
        ans = input('Press Enter to open the page (s = skip this one, q = stop): ').strip().lower()
        if ans == 'q': break
        if ans == 's': continue
        before = snapshot(dl); webbrowser.open(r.get('page') or r.get('url'))
        while True:
            ans = input('When the download has FINISHED press Enter (s = skip, q = stop): ').strip().lower()
            if ans in ('s', 'q'): break
            files = new_files(dl, before)
            if not files: say('No new GeoJSON / JSON / zip file in Downloads yet.'); continue
            say('Found: ' + ', '.join(p.name for p in files))
            good = 0
            for x in grp:
                ok, msg, path = check_and_pack(x, files, parks, out, layers_table)
                say(f'  {x["area"]} {x["layer"]}: {msg}')
                if ok: made.append(path); good += 1
            if good: break
            if input('Try another download for this layer? (y / n): ').strip().lower() != 'y': break
        if ans == 'q': break
    if not made: say('\nNothing checked to upload.'); return 0
    say(f'\n{len(made)} checked file(s) in {out}.')
    if not a.no_upload: upload(made, out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
