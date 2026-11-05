#!/usr/bin/env python3
"""Nov 6 improvements 4 (v2): join acreage + distance check (kpc_join_check.py). Its rule-18 style selftest (32 frozen cases), it is
not a key rules file (no rules hash change), far joins are HELD by default, and each of the three key builds runs it after the
build and before the stamp, with the answer sheet read for exemptions."""
import pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_freeze as KZ
import kpc_join_check as JC
ok = True
def check(msg, cond):
    global ok
    ok &= bool(cond); print(('PASS ' if cond else 'FAIL ') + msg)
r = subprocess.run([sys.executable, '-B', str(ROOT / '.github/scripts/kpc_join_check.py'), '--selftest'], capture_output=True, text=True, timeout=120, cwd=ROOT)
check('kpc_join_check.py --selftest: ' + (r.stdout.strip().splitlines() or ['?'])[-1], r.returncode == 0 and 'SELFTEST PASS' in r.stdout)
check('not a rules file of any key (adding it changes no rules hash)', all('kpc_join_check' not in ' '.join(v) for v in KZ.RULE_FILES.values()))
check("decided_by is Brandon's verify-then-fix rule (evidence only)", JC.DECIDED_BY == 'Brandon standing rule 2026-11-05 verify-then-fix')
for wf, key in (('kpc-us-key.yml', 'us'), ('kpc-ca-key.yml', 'ca'), ('kpc-world-key.yml', 'world')):
    y = (ROOT / '.github/workflows' / wf).read_text()
    i, j = y.find('- name: Join check (Nov 6 improvements 4'), y.find('- name: BUILD STAMP')
    st = y[i:].split('\n      - name:', 1)[0] if i >= 0 else ''
    check(f'{wf}: the join check runs after the build and before the build stamp', 0 <= i < j)
    check(f'{wf}: KEY={key}, never fails the build', f'KEY: {key}' in st and 'continue-on-error: true' in st)
    check(f'{wf}: v2.1 answer-sheet read is anonymous + read-only (no token / secrets / push) and loud on failure',
          'credential.helper= clone' in st and 'GIT_TERMINAL_PROMPT=0' in st and 'secrets.' not in st and 'token' not in st.lower().replace('no token', '') and 'git push' not in st and 'kpc_push' not in st and '::error title=Join check::' in st)
    check(f'{wf}: v2 holds by default (no KPC_JOIN_HOLD=mark) and reads the answer sheet', 'KPC_JOIN_HOLD: mark' not in st and 'ANSWER_SHEET:' in st and 'rm -rf .as' in st)
check('hold is the default mode', JC.run.__code__ is not None and "(env.get('KPC_JOIN_HOLD') or 'hold')" in (ROOT / '.github/scripts/kpc_join_check.py').read_text())
check('the far bar is 15 km, measured to the nearest part', JC.FAR_KM == 15.0)
check('linear features are exempt (US-9905/9906 trail lines)', JC.linear({'line': 1, 'm': [['trl9905', 'x', 0, 'official trail line']]}) and JC.linear({'n': 'Katy Trail', 't': 'State Trail', 'm': [[1, 'x', 5, 'name']]}))
import os
dk = os.environ.get('DATA')
if dk and os.path.isfile(os.path.join(dk, '.github/scripts/kpc_agreement_ledger.py')):
    sys.path.insert(0, os.path.join(dk, '.github/scripts')); import kpc_agreement_ledger as AL
    check('the pile-enter proposal file uses the ledger columns (KPC-Data kpc_agreement_ledger.FIELDS)', list(AL.FIELDS) == JC.LEDGER_FIELDS)
    print('INFO the ledger kind pile-enter is ' + ('there' if 'pile-enter' in AL.KINDS else 'added by KPC-Data improvements 2 (apply both)'))
# v2.1 (Quality should-fix): the three area parks with 'River' in the name are HELD (synthetic, frozen), and not linear by name
for nm, t in (('Owyhee River Wilderness Area', 'Wilderness Area'), ('Great River National Wildlife Refuge', 'National Wildlife Refuge'), ('Merrimack River State Forest', 'State Forest')):
    p = {'n': nm, 't': t, 'g': 'official', 'm': [[1, nm, 9, 'name']], 'c': [], 'bk': [1, 28.0]}
    check(f'v2.1: {nm} (far, not approved) must be HELD', not JC.linear(p) and JC.exempt('US-X', p, {}) == '')
check("v2.1: a 'chat 11 YES' how is no exemption", JC.exempt('X', {'m': [[1, 'X', 9, 'name (chat 11 YES)']]}, {}) == '')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
