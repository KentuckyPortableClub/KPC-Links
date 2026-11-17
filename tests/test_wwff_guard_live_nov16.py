#!/usr/bin/env python3
"""Nov 16: kpc_wwff_dir.py compared a new download with whatever was in data/wwff/ after the
waiting-room resume. A held copy that passed its checks (or, before KPC-Data #102, one that
failed) could be smaller than the live file, and the shrink guard then used that smaller
number as the floor. The guard now compares against the live file (WWFF_LIVE, or git HEAD of
the KPC-Data checkout). Offline: urlopen is replaced in this process."""
import contextlib, io, json, os, pathlib, runpy, subprocess, sys, tempfile, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCR = ROOT / '.github' / 'scripts'
sys.path.insert(0, str(SCR))
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


ANSWER = {'body': b''}


class Resp:
    def read(self): return ANSWER['body']


def fake(req, *a, **k):
    u = req.full_url if hasattr(req, 'full_url') else str(req)
    assert u == 'https://wwff.co/wwff-data/wwff_directory.csv', 'unexpected request ' + u
    return Resp()


urllib.request.urlopen = fake


def csv_of(counts, status='active'):
    L = ['reference,status,name,latitude,longitude,website,state,county']
    for prog, n in counts.items():
        for i in range(n): L.append(f'{prog}-{i:04d},{status},Area {prog} {i},{30 + (i % 20) + .123456},{-100 + (i % 30) + .5},,,')
    return '\n'.join(L).encode()


def rows(prog, n):
    return [[f'{prog}-{i:04d}', f'Area {prog} {i}', round(30 + (i % 20) + .123456, 5), round(-100 + (i % 30) + .5, 5), '', '', ''] for i in range(n)]


def write_lists(folder, counts):
    folder = pathlib.Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for prog, n in counts.items():
        (folder / (prog + '.json')).write_text(json.dumps(rows(prog, n), ensure_ascii=False, separators=(',', ':')), encoding='utf-8')


def run(cwd, live=None, env=None):
    os.chdir(cwd)
    saved = {k: os.environ.get(k) for k in ('WWFF_LIVE', 'DATA')}
    if live is not None:
        os.environ['WWFF_LIVE'] = str(live)
    elif 'WWFF_LIVE' in os.environ:
        del os.environ['WWFF_LIVE']
    if env:
        os.environ.update(env)
    elif 'DATA' in os.environ:
        del os.environ['DATA']
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try: runpy.run_path(str(SCR / 'kpc_wwff_dir.py'), run_name='__main__')
        except SystemExit:
            pass
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    return buf.getvalue()


def n_of(cwd, prog):
    p = pathlib.Path(cwd) / 'data/wwff' / (prog + '.json')
    return len(json.loads(p.read_text(encoding='utf-8'))) if p.exists() else None


# (a) the hole: the working copy is the smaller resumed file (CTFF 702 -> 280). The live
# file is still 702. A download of 280 used to pass the guard (280 is not under half of 280)
# and overwrite the working copy. Compared with live, it is under half of 702, so 702 is kept.
d = pathlib.Path(tempfile.mkdtemp(prefix='kpc-wwff-live-a-'))
live = pathlib.Path(tempfile.mkdtemp(prefix='kpc-wwff-live-src-'))
write_lists(d / 'data/wwff', {'CTFF': 280, 'KFF': 100})
write_lists(live, {'CTFF': 702, 'KFF': 100})
ANSWER['body'] = csv_of({'CTFF': 280, 'KFF': 100})
out = run(d, live=live)
check(n_of(d, 'CTFF') == 702, f'the CTFF-shaped hole: a 280-row download is not kept when live still has 702 (got {n_of(d, "CTFF")})')
check(n_of(d, 'KFF') == 100, 'the unchanged program is left as it was')
check('CTFF' in out and 'last week' in out, 'the log says the smaller program was kept from last week')

# (b) a cut-off download against a already-shrunk working copy: live KFF=2000, working KFF=1600
# (a passed drop that stayed over 80%). The download has 200 rows. The whole-list 80% guard
# must use live (200 < 0.8 * 2000) and put the live file back, not leave 1600 on disk.
d = pathlib.Path(tempfile.mkdtemp(prefix='kpc-wwff-live-b-'))
live = pathlib.Path(tempfile.mkdtemp(prefix='kpc-wwff-live-src-b-'))
write_lists(d / 'data/wwff', {'KFF': 1600})
write_lists(live, {'KFF': 2000})
ANSWER['body'] = csv_of({'KFF': 200})
out = run(d, live=live)
check(n_of(d, 'KFF') == 2000, f'a cut-off download puts the live file back, not the already-shrunk working copy (got {n_of(d, "KFF")})')
check('Nothing was changed' in out and '200' in out and '2000' in out, 'the log names the live count, not only the working-copy count')

# (c) a longer passed working copy is still the floor: live 100, working 140, download 40.
d = pathlib.Path(tempfile.mkdtemp(prefix='kpc-wwff-live-c-'))
live = pathlib.Path(tempfile.mkdtemp(prefix='kpc-wwff-live-src-c-'))
write_lists(d / 'data/wwff', {'OAFF': 140})
write_lists(live, {'OAFF': 100})
ANSWER['body'] = csv_of({'OAFF': 40})
out = run(d, live=live)
check(n_of(d, 'OAFF') == 140, f'a longer passed working copy is kept when the download shrinks (got {n_of(d, "OAFF")})')

# (d) an ordinary change against live is still saved.
d = pathlib.Path(tempfile.mkdtemp(prefix='kpc-wwff-live-d-'))
live = pathlib.Path(tempfile.mkdtemp(prefix='kpc-wwff-live-src-d-'))
write_lists(d / 'data/wwff', {'OAFF': 100})
write_lists(live, {'OAFF': 100})
ANSWER['body'] = csv_of({'OAFF': 95})
out = run(d, live=live)
check(n_of(d, 'OAFF') == 95, f'an ordinary change against the live file is saved (got {n_of(d, "OAFF")})')

# (e) the weekly job path: no WWFF_LIVE. Live is git HEAD of ./kpcdata; resume has already
# overwritten that checkout's working tree (and the overlaid data/wwff) with 280 rows.
d = pathlib.Path(tempfile.mkdtemp(prefix='kpc-wwff-live-e-'))
write_lists(d / 'data/wwff', {'CTFF': 280})
repo = d / 'kpcdata'
write_lists(repo / 'data/wwff', {'CTFF': 702})
subprocess.run(['git', 'init', '-q'], cwd=repo, check=True)
subprocess.run(['git', 'add', 'data/wwff/CTFF.json'], cwd=repo, check=True)
subprocess.run(['git', '-c', 'user.name=test', '-c', 'user.email=test@test', 'commit', '-qm', 'live'], cwd=repo, check=True)
write_lists(repo / 'data/wwff', {'CTFF': 280})  # resume already copied the held file over live
ANSWER['body'] = csv_of({'CTFF': 280})
out = run(d)  # no WWFF_LIVE; DATA unset; ./kpcdata is the Data checkout
check(n_of(d, 'CTFF') == 702, f'weekly job: git HEAD of ./kpcdata is used even after resume overwrote the working tree (got {n_of(d, "CTFF")})')

# (f) no live source (a local run with only the working copy): same as today, 280 stays 280.
d = pathlib.Path(tempfile.mkdtemp(prefix='kpc-wwff-live-f-'))
write_lists(d / 'data/wwff', {'CTFF': 280})
ANSWER['body'] = csv_of({'CTFF': 280})
out = run(d)
check(n_of(d, 'CTFF') == 280, f'with no live file the working copy is still the floor (got {n_of(d, "CTFF")})')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
