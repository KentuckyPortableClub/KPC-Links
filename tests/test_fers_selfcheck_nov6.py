#!/usr/bin/env python3
"""Nov 6 improvements 5: 2-fer self-check after every key build (kpc_fers_selfcheck.py). Its rule-18 style selftest (13 frozen
cases: pin / approximate half IN THAT STATE, river rows left alone, gz files, Canada, world, hold list, nothing deleted), and the
same hold wording family as the far-spot hold ('not sure: ...' + 'was')."""
import pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_fers_selfcheck as SC
ok = True
def check(msg, cond):
    global ok
    ok &= bool(cond); print(('PASS ' if cond else 'FAIL ') + msg)
r = subprocess.run([sys.executable, '-B', str(ROOT / '.github/scripts/kpc_fers_selfcheck.py'), '--selftest'], capture_output=True, text=True, timeout=120, cwd=ROOT)
check('kpc_fers_selfcheck.py --selftest: ' + (r.stdout.strip().splitlines() or ['?'])[-1], r.returncode == 0 and 'SELFTEST PASS' in r.stdout)
check('W-DE reads the DE world key; US / CA stems unchanged', (SC.key_area('W-DE'), SC.key_area('US-KY'), SC.key_area('CA-ON')) == ('DE', 'US-KY', 'CA-ON'))
check('the live statuses match the far-spot hold', SC.LIVE == ('candidate', 'very tight', 'water only'))
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
