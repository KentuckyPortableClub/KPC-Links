#!/usr/bin/env python3
"""Nov 6 improvements 3: daily key health diff (kpc_key_health.py). Its rule-18 style selftest (16 frozen cases), the ledger
columns match KPC-Data's agreement ledger (when DATA is set), and the workflow step is OPTIONAL and workflow_dispatch only."""
import os, pathlib, re, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_health as KH
ok = True
def check(msg, cond):
    global ok
    ok &= bool(cond); print(('PASS ' if cond else 'FAIL ') + msg)
r = subprocess.run([sys.executable, '-B', str(ROOT / '.github/scripts/kpc_key_health.py'), '--selftest'], capture_output=True, text=True, timeout=120, cwd=ROOT)
check('kpc_key_health.py --selftest: ' + (r.stdout.strip().splitlines() or ['?'])[-1], r.returncode == 0 and 'SELFTEST PASS' in r.stdout)
D = os.environ.get('DATA')
if D and (pathlib.Path(D) / '.github/scripts/kpc_agreement_ledger.py').exists():
    sys.path.insert(0, str(pathlib.Path(D) / '.github/scripts')); import kpc_agreement_ledger as AL
    check("ledger-proposals.csv columns = KPC-Data's agreement ledger columns", KH.FIELDS == AL.FIELDS)
else: print('SKIP ledger columns (DATA not set)')
y = (ROOT / '.github/workflows/kpc-key-postcheck.yml').read_text()
st = y.split('- name: Key health diff', 1)[1].split('\n      - name:', 1)[0] if '- name: Key health diff' in y else ''
check('the post-key check has a key health step', bool(st))
check("the step runs only on workflow_dispatch with health=yes", "github.event_name == 'workflow_dispatch' && inputs.health == 'yes'" in st)
check('the step never fails the check (continue-on-error)', 'continue-on-error: true' in st)
check('the workflow has no schedule (no new cron)', not re.search(r'^\s*schedule:', y, re.M))
check('the step writes nothing outside data/status/key-check (no OUT_DIR / LEDGER_DATA set)', 'OUT_DIR' not in st and 'LEDGER_DATA' not in st)
check('v2: far joins and held joins are report-only by default (no pile proposal); lost outlines / acres still propose',
      KH.REPORT_ONLY == {'join over 15 km', 'join held'} and [p['park'] for p in KH.proposals([{'park': 'US-1', 'area': 'US-AA', 'flag': 'join over 15 km', 'detail': ''},
      {'park': 'US-2', 'area': 'US-AA', 'flag': 'outline lost', 'detail': ''}, {'park': 'US-3', 'area': 'US-AA', 'flag': 'acres off', 'detail': ''}], 'us', 'x', False)] == ['US-2', 'US-3'])
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
