#!/usr/bin/env python3
"""Nov 11 (data-quality review): kpc_wwff_dir.py wrote whatever the WWFF download held. A 200 answer that was a web page, an empty file or a
cut-off list gave no programs, and the script then deleted every data/wwff/*.json file and tile (kpc_canada.py and kpc_northam.py read
them for their WWFF rows). A list under 80% of what is on file is now refused; a program under half its size, or missing, keeps its last
file. Offline: urlopen is replaced in this process."""
import contextlib, io, json, os, pathlib, runpy, sys, tempfile, urllib.request

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


def run(cwd):
    os.chdir(cwd)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try: runpy.run_path(str(SCR / 'kpc_wwff_dir.py'), run_name='__main__')
        except SystemExit: pass
    return buf.getvalue()


def files(d): return sorted(p.name for p in (d / 'data/wwff').glob('*.json'))


d = pathlib.Path(tempfile.mkdtemp(prefix='kpc-wwff-'))
ANSWER['body'] = csv_of({'KFF': 1000, 'VEFF': 100, 'XEFF': 100})
out = run(d)
check(files(d) == ['KFF.json', 'VEFF.json', 'XEFF.json', 'index.json'] and len(json.load(open(d / 'data/wwff/KFF.json'))) == 1000, 'first run (nothing on file): the files are written')
check(any((d / 'data/wwff/t').glob('*.json')), 'tiles are written')
snap = {p.name: p.read_text() for p in (d / 'data/wwff').glob('*.json')}

for label, body in (('a web page', b'<html><body>Maintenance</body></html>'), ('an empty file', b''), ('a cut-off list (200 of 1200 rows)', csv_of({'KFF': 200}))):
    ANSWER['body'] = body
    out = run(d)
    now = {p.name: p.read_text() for p in (d / 'data/wwff').glob('*.json')}
    check(now == snap, f'{label}: every program file is left exactly as it was (they used to be deleted)')
    check('::warning title=WWFF directory::' in out and 'Nothing was changed' in out, f'{label}: the log says it was refused')
    check(len(list((d / 'data/wwff/t').glob('*.json'))) > 0, f'{label}: the tiles stay')

ANSWER['body'] = csv_of({'KFF': 1000, 'VEFF': 40})      # VEFF fell from 100 to 40 (under half); XEFF is missing; total 1040 of 1200 = 87%
out = run(d)
check(len(json.load(open(d / 'data/wwff/VEFF.json'))) == 100 and len(json.load(open(d / 'data/wwff/XEFF.json'))) == 100, 'a program under half its size, or missing, keeps its last file')
check('VEFF' in out and 'XEFF' in out, 'and the log names them')
check(json.load(open(d / 'data/wwff/index.json')) == ['KFF', 'VEFF', 'XEFF'], 'the index still lists all three')

ANSWER['body'] = csv_of({'KFF': 1010, 'VEFF': 90, 'XEFF': 100})   # an ordinary change: a few added, a few gone
out = run(d)
check(len(json.load(open(d / 'data/wwff/KFF.json'))) == 1010 and len(json.load(open(d / 'data/wwff/VEFF.json'))) == 90, 'an ordinary change is saved')
ANSWER['body'] = csv_of({'KFF': 1010, 'VEFF': 90, 'XEFF': 100})
before = {p.name: p.stat().st_mtime_ns for p in (d / 'data/wwff').glob('*.json') if p.name != 'index.json'}
run(d)
check(before == {p.name: p.stat().st_mtime_ns for p in (d / 'data/wwff').glob('*.json') if p.name != 'index.json'}, 'the same answer again rewrites no program file')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
