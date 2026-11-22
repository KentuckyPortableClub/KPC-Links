#!/usr/bin/env python3
"""Review F9 / N3 (KPC owner, 22 Nov 2026): when no official sizes file is found or readable, the US key builder says so once (a
notice) instead of skipping it without a word. A found file says nothing. Offline; invented parks only."""
import json, os, pathlib, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_rules as KR  # noqa: E402
bad = 0
def check(ok, msg):
    global bad; bad += not ok; print(('PASS ' if ok else 'FAIL ') + msg, flush=True)
said = []
# kpc_us_key.py runs the builder at import. Exec only the helpers (same rule as test_size_check_nov20.py).
_src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
_ns = {'KR': KR, 'os': os, 'json': json, 'P_ALL': {}, 'notice': lambda t, m: said.append((t, m)), '_tags': lambda t: set(), '_kr': lambda name: False}
exec(compile(_src[_src.find('ACRES_OFF = None'):_src.find('P_ALL = {}')], 'kpc_us_key.py', 'exec'), _ns)
td = pathlib.Path(tempfile.mkdtemp()); cwd = os.getcwd(); os.chdir(td)
os.environ.pop('DATA', None)
try:
    os.environ['OFFICIAL_ACRES'] = str(td / 'missing.json'); _ns['ACRES_OFF'] = None
    got = _ns['_official_acres'](); _ns['_official_acres']()
    check(got == {} and len(said) == 1 and 'no official sizes file' in said[0][1], f'no acres file: one notice ({said})')
    (td / 'bad.json').write_text('{', encoding='utf-8'); os.environ['OFFICIAL_ACRES'] = str(td / 'bad.json'); _ns['ACRES_OFF'] = None; said.clear()
    _ns['_official_acres']()
    check(len(said) == 1, 'an unreadable acres file: one notice')
    (td / 'ok.json').write_text(json.dumps({'US-9001': 12}), encoding='utf-8'); os.environ['OFFICIAL_ACRES'] = str(td / 'ok.json'); _ns['ACRES_OFF'] = None; said.clear()
    check(_ns['_official_acres']() == {'US-9001': 12.0} and not said, 'a readable acres file: no notice')
finally:
    os.environ.pop('OFFICIAL_ACRES', None); os.chdir(cwd)
print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
