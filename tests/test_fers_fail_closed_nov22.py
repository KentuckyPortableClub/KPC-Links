#!/usr/bin/env python3
"""Review M8 / F14 (KPC owner, 22 Nov 2026): the 2-fer bot fails CLOSED on its two rule-data files.
1 .github/fers-rule-scope.json missing or unreadable = the bot stops (exit 4); it used to mean 'no declared change' (reuse every pair)
2 the D10 not-sure list missing or unreadable = the bot stops (exit 4); it used to turn D10 off with a warning
3 KPC_FERS_NOT_SURE=none is the one explicit way to run without D10 (no row held, a notice)
4 main() checks the list before any work
Offline, no network, invented parks only."""
import contextlib, io, json, os, pathlib, shutil, subprocess, sys, tempfile, types
HERE = pathlib.Path(__file__).resolve().parent.parent
S = HERE / '.github/scripts'
ok = True
def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg, flush=True); ok = ok and bool(c)

TD = pathlib.Path(tempfile.mkdtemp())
IMPORT = ("import sys, types, os; os.environ.setdefault('PASS', '3'); os.environ['HTTP_CACHE'] = ''\n"
          "try:\n import cv2\nexcept Exception:\n sys.modules['cv2'] = types.ModuleType('cv2')\n"
          "sys.path.insert(0, sys.argv[1]); import kpc_fers; print('IMPORTED')")
def import_with(scope_text):
    t = pathlib.Path(tempfile.mkdtemp(dir=TD)); (t / '.github').mkdir()
    shutil.copytree(S, t / '.github/scripts', ignore=shutil.ignore_patterns('__pycache__'))
    for f in (HERE / '.github').glob('*.json'):
        if f.name != 'fers-rule-scope.json': shutil.copy(f, t / '.github' / f.name)
    if scope_text is not None: (t / '.github/fers-rule-scope.json').write_text(scope_text, encoding='utf-8')
    return subprocess.run([sys.executable, '-c', IMPORT, str(t / '.github/scripts')], capture_output=True, text=True, cwd=str(t), timeout=300)

r = import_with(None)
check(r.returncode == 4 and 'fers-rule-scope.json is missing or unreadable' in r.stdout, f'1 no scope file: the bot stops (exit {r.returncode})')
r = import_with('{"changes": [')
check(r.returncode == 4 and '::error' in r.stdout, f'1 an unreadable scope file: the bot stops (exit {r.returncode})')
r = import_with('{"changes": "all"}')
check(r.returncode == 4, f'1 a scope file of the wrong shape: the bot stops (exit {r.returncode})')
r = import_with('{"changes": []}')
check(r.returncode == 0 and 'IMPORTED' in r.stdout, f'1 a readable scope file with no change is a real, empty scope (exit {r.returncode})')

sys.path.insert(0, str(S))
os.environ.setdefault('PASS', '3'); os.environ['HTTP_CACHE'] = ''; os.environ.pop('KPC_FERS_NOT_SURE', None)
try: import cv2  # noqa: F401
except Exception: sys.modules['cv2'] = types.ModuleType('cv2')  # noqa: BLE001
_cwd = os.getcwd(); os.chdir(TD)
import kpc_fers as K  # noqa: E402

def stops(fn):
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf): fn()
    except SystemExit as e: return e.code == 4 and '::error' in buf.getvalue()
    return False

rows = [{'refs': ['US-0001', 'US-0002'], 'kind': 'area', 'status': 'candidate', 'list': True}]
K._TRIPWIRE.clear()
check(stops(K.tripwire_parks), '2 no not-sure list anywhere: the bot stops (exit 4)')
check(stops(lambda: K.hold_tripwire([dict(x) for x in rows])), '2 ... also from the hold step')
(TD / 'bad.json').write_text('{"parks": {', encoding='utf-8'); os.environ['KPC_FERS_NOT_SURE'] = str(TD / 'bad.json'); K._TRIPWIRE.clear()
check(stops(K.tripwire_parks), '2 an unreadable not-sure list: the bot stops (exit 4)')
(TD / 'list.json').write_text(json.dumps({'parks': {}}), encoding='utf-8'); os.environ['KPC_FERS_NOT_SURE'] = str(TD / 'list.json'); K._TRIPWIRE.clear()
check(K.tripwire_parks() == {}, '2 an empty list {"parks": {}} is a real list: the run goes on, no park held')
os.environ['KPC_FERS_NOT_SURE'] = 'none'; K._TRIPWIRE.clear(); buf = io.StringIO(); a = [dict(x) for x in rows]
with contextlib.redirect_stdout(buf): n = K.hold_tripwire(a)
check(n == 0 and a == rows and 'on purpose' in buf.getvalue(), '3 KPC_FERS_NOT_SURE=none: D10 off on purpose, no row held, and the run says so')
os.environ.pop('KPC_FERS_NOT_SURE'); K._TRIPWIRE.clear(); os.chdir(_cwd)
src = (S / 'kpc_fers.py').read_text(encoding='utf-8')
body = src[src.index('def main():'):]
check(body.index('tripwire_parks()') < body.index('_run_areas ='), '4 main() reads the list before choosing any area (stops before any work)')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
