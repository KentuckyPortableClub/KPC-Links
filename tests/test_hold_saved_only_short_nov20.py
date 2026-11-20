#!/usr/bin/env python3
"""Job 9 (R6; outside review F10, 'layers on saved-copy-only hosts are never short-checked'; DRAFT, switch KPC_HOLD_ON_PASS_ERROR,
OFF): the US key builder's short check skips every layer whose host is saved-copy only (no live count may be asked of it).
Switch OFF = skipped, as before. Switch ON = the saved copy is compared with that layer's baseline in data/outlines/layers.json
(expected_count of 'US-<state>.<prefix>'); under 97% of it holds the state (kpc_key_rules.PassError), since it cannot be re-read.
At or above 97%, or no baseline, = no change. A live host is never checked here (its live count is, as before).
Runs on INVENTED data: the builder's own lines and its baseline helper, taken from the source, an invented baseline file and
invented records. No shapely, no network.
Run:  python3 tests/test_hold_saved_only_short_nov20.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import json, pathlib, sys, tempfile, textwrap
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_rules as KR  # noqa: E402
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)

SRC = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
a = SRC.index('                if saved_only(url):\n', SRC.index('            short = set()\n'))
b = SRC.index('                opt = x[8] if len(x) > 8 else {}\n', a)
loop = 'def f():\n    for x in XS:\n        pre, url = x[0], x[1]\n' + textwrap.indent(textwrap.dedent(SRC[a:b]), '        ') + '        LIVE.append(pre)\n'
helper = ''
if 'def outline_baseline(' in SRC:
    h0 = SRC.index("OUTLINE_LAYERS = 'data/outlines/layers.json'\n"); h1 = SRC.index('\ndef rule_data_files(', h0); helper = SRC[h0:h1]
check(bool(helper), 'the builder has a baseline helper (outline_baseline) for saved-copy-only layers')

tmp = pathlib.Path(tempfile.mkdtemp(prefix='j9-', dir='/tmp/j9' if pathlib.Path('/tmp/j9').is_dir() else None))
lay = tmp / 'layers.json'
json.dump({'format': 1, 'layers': {'US-NH.sgnha': {'expected_count': 100}, 'US-NH.sgnhb': {'expected_count': 100}, 'US-VT.sgnha': {'expected_count': 5}}}, open(lay, 'w'))

def run(hold, have):
    live = []
    recs = [{'OBJECTID': f'{p}{i}'} for p, n in have.items() for i in range(n)]
    g = {'json': json, 'XS': [('sgnha', 'https://services9.arcgis.com/x/FeatureServer/0/query'), ('sgnhb', 'https://services9.arcgis.com/y/FeatureServer/0/query'),
                              ('sgnhc', 'https://services9.arcgis.com/z/FeatureServer/0/query'), ('sgnhl', 'https://gis.example.gov/MapServer/0/query')],
         'saved_only': lambda u: 'arcgis.com' in u, 'recs': recs, 'st': 'NH', 'LIVE': live,
         'KR': type('K', (), {'PassError': KR.PassError, 'hold_state': staticmethod(getattr(KR, 'hold_state', lambda *a: None)),
                              'on': staticmethod(lambda n, env=None, area=None, path=None: hold and n == 'KPC_HOLD_ON_PASS_ERROR' and area == 'NH')})}
    if helper: exec(compile(helper, 'kpc_us_key.py (baseline helper)', 'exec'), g); g['OUTLINE_LAYERS'] = str(lay)
    exec(compile(loop, 'kpc_us_key.py (short check)', 'exec'), g)
    try: g['f'](); return live, None
    except Exception as x: return live, x  # noqa: BLE001

l, x = run(False, {'sgnha': 50, 'sgnhb': 100})
check(x is None and l == ['sgnhl'], f'switch OFF: saved-copy-only layers are skipped, a short one too, as before ({l}, {x})')
l, x = run(True, {'sgnha': 96, 'sgnhb': 100})
check(isinstance(x, KR.PassError) and 'NH' in str(x) and 'sgnha' in str(x) and '96' in str(x) and '100' in str(x),
      f'switch ON: a saved-copy-only layer at 96 of its baseline 100 holds the state ({x})')
l, x = run(True, {'sgnha': 97, 'sgnhb': 100, 'sgnhc': 0})
check(x is None and l == ['sgnhl'], f'switch ON: 97 of 100 passes, and a layer with no baseline (sgnhc) is not checked ({l}, {x})')
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed')
import shutil; shutil.rmtree(tmp, ignore_errors=True)
sys.exit(0 if n == len(RESULTS) else 1)
