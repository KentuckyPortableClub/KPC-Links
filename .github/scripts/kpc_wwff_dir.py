#!/usr/bin/env python3
"""Slim copy of the WWFF directory for the Park Info Finder (kpc-park-info.html).
wwff.co's directory CSV can't be read by a web page (no CORS), so every week we save the active references,
split by program prefix: data/wwff/<PREFIX>.json = [[ref, name, lat, lon, website, state, county], ...].
"""
import csv, io, json, os, pathlib, subprocess, sys, urllib.request
import kpc_net_guard; kpc_net_guard.install()
UA = 'Mozilla/5.0 (compatible; KPC-Links WWFF directory copy)'
raw = urllib.request.urlopen(urllib.request.Request('https://wwff.co/wwff-data/wwff_directory.csv', headers={'User-Agent': UA}), timeout=120).read().decode('utf-8', 'replace')
out = {}
for r in csv.DictReader(io.StringIO(raw)):
    if (r.get('status') or '').lower() != 'active':
        continue
    ref = (r.get('reference') or '').strip().upper()
    if '-' not in ref:
        continue
    def f(k):
        v = (r.get(k) or '').strip()
        return '' if v in ('-', 'n/a', 'N/A') else v
    try:
        la, lo = round(float(r['latitude']), 5), round(float(r['longitude']), 5)
    except Exception:  # noqa: BLE001
        la = lo = None
    out.setdefault(ref.split('-')[0], []).append([ref, f('name'), la, lo, f('website'), f('state'), f('county')])
d = pathlib.Path('data/wwff'); d.mkdir(parents=True, exist_ok=True)
# Nov 11: the download comes back with status 200 even when it is a web page, an empty file or a cut-off list, and this script then
# DELETED every program file and tile that was not in the answer (and kpc_canada.py / kpc_northam.py read these files for their WWFF rows).
# Same rules as the world POTA bot: a list under 80% of what is on disk is refused (nothing is touched, and the log says so); a program
# with 10+ references that comes back under half its size, or not at all, keeps its last file.
# Nov 16: that "on disk" count used to be the working copy after the waiting-room resume. A held file that failed
# its checks is no longer resumed (KPC-Data #102), but a held file that passed still becomes the working copy. If
# that copy is smaller than live (a drop that stayed over 80%, so F-W2 did not fire), the next download is compared
# against the smaller number and the floor can creep down. The guard now compares against the LIVE file: WWFF_LIVE
# (a folder of live PREFIX.json files) or, in the weekly job, git HEAD of the KPC-Data checkout at $DATA or ./kpcdata.
# A longer working copy is still the floor, so a passed growth is not thrown away. If a cut-off download is refused,
# a working copy that had already shrunk is put back to that live (or longer) baseline so the shrink does not stick.
def _read_lists(folder):
    folder = pathlib.Path(folder)
    if (folder / 'data' / 'wwff').is_dir():
        folder = folder / 'data' / 'wwff'
    have = {}
    if not folder.is_dir():
        return have
    for fn in folder.glob('*.json'):
        if fn.name == 'index.json': continue
        try: have[fn.stem] = json.loads(fn.read_text(encoding='utf-8'))
        except Exception: pass  # noqa: BLE001
    return have
def _on_disk():
    return _read_lists(d)
def _live_from_git(repo):
    """Committed data/wwff/*.json from a KPC-Data checkout, even after resume has overwritten the working tree."""
    try:
        listing = subprocess.run(['git', '-C', str(repo), 'ls-tree', '--name-only', 'HEAD:data/wwff'],
                                 capture_output=True, text=True, check=False)
    except Exception:  # noqa: BLE001
        return {}
    if listing.returncode != 0:
        return {}
    have = {}
    for name in listing.stdout.splitlines():
        if '/' in name.replace('\\', '/') or not name.endswith('.json') or name == 'index.json':
            continue
        r = subprocess.run(['git', '-C', str(repo), 'show', f'HEAD:data/wwff/{name}'],
                           capture_output=True, check=False)
        if r.returncode != 0:
            continue
        try: have[pathlib.Path(name).stem] = json.loads(r.stdout.decode('utf-8'))
        except Exception: pass  # noqa: BLE001
    return have
def _live_lists():
    env = os.environ.get('WWFF_LIVE')
    if env:
        return _read_lists(env)
    for repo in (os.environ.get('DATA') or '', 'kpcdata'):
        got = _live_from_git(repo)
        if got:
            return got
    return {}
_have, _live = _on_disk(), _live_lists()
def _base(prog):
    live_rows, have_rows = _live.get(prog) or [], _have.get(prog) or []
    return have_rows if len(have_rows) > len(live_rows) else (live_rows or have_rows)
_programs = set(_have) | set(_live)
_old_n, _new_n = sum(len(_base(p)) for p in _programs), sum(len(v) for v in out.values())
def _put_back(prog, rows):
    fn = d / (prog + '.json')
    s = json.dumps(sorted(rows), ensure_ascii=False, separators=(',', ':'))
    if not fn.exists() or fn.read_text(encoding='utf-8') != s:
        fn.write_text(s, encoding='utf-8')
if _old_n >= 1000 and _new_n < 0.8 * _old_n:
    print('::warning title=WWFF directory::only %d active references read vs %d on file: the download looks cut off or is not the list. Nothing was changed; last week\'s files stay.' % (_new_n, _old_n))
    for _p in _programs:
        _rows = _base(_p)
        if _rows: _put_back(_p, _rows)
    sys.exit(0)
_kept = []
for _p in sorted(_programs):
    _rows = _base(_p)
    if len(_rows) >= 10 and len(out.get(_p, [])) < 0.5 * len(_rows):
        out[_p] = list(_rows); _kept.append(_p)
if _kept: print('::warning title=WWFF directory::program(s) %s came back much smaller or missing: last week\'s file kept.' % ', '.join(sorted(_kept)))
keep = set()
for p, rows in out.items():
    rows.sort()
    fn = d / (p + '.json'); keep.add(fn.name)
    s = json.dumps(rows, ensure_ascii=False, separators=(',', ':'))
    if not fn.exists() or fn.read_text(encoding='utf-8') != s:
        fn.write_text(s, encoding='utf-8')
for fn in d.glob('*.json'):
    if fn.name not in keep and fn.name != 'index.json':
        fn.unlink()
# location tiles (1 x 1 degree, by the floor of lat/lon) for "what's near me" lookups: data/wwff/t/<lat>_<lon>.json = [[ref, name, lat, lon], ...]
import math
t = d / 't'; t.mkdir(exist_ok=True); tiles = {}
for rows in out.values():
    for r in rows:
        if r[2] is None or r[3] is None: continue
        tiles.setdefault('%d_%d' % (math.floor(r[2]), math.floor(r[3])), []).append(r[:4])
tk = set()
for k, rows in tiles.items():
    rows.sort(); fn = t / (k + '.json'); tk.add(fn.name); s2 = json.dumps(rows, ensure_ascii=False, separators=(',', ':'))
    if not fn.exists() or fn.read_text(encoding='utf-8') != s2: fn.write_text(s2, encoding='utf-8')
for fn in t.glob('*.json'):
    if fn.name not in tk: fn.unlink()
(d / 'index.json').write_text(json.dumps(sorted(out), separators=(',', ':')), encoding='utf-8')
print('::notice title=WWFF directory::%d programs, %d active refs, KFF %d' % (len(out), sum(len(v) for v in out.values()), len(out.get('KFF', []))))
