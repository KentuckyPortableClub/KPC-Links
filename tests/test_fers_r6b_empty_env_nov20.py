#!/usr/bin/env python3
"""R6b / C-F13 (20 Nov). A run with an empty environment uses the one switch file.

The switch file, receipts, and the PC runner (it no longer sets near-line metres,
carry max, summary-approx or strip-held) are already on main. This test locks
that. The 2-fer rules hash must not move.
"""
import os, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
S = ROOT / '.github/scripts'
sys.path.insert(0, str(S))

# The environment is empty of 2-fer rule settings, including leftovers the PC
# used to pass (NEAR_LINE_M, CARRY_MAX). Store / cache knobs are left alone.
for k in list(os.environ):
    if k.startswith('KPC_FERS_') and k not in {
        'KPC_FERS_FROM_STORE', 'KPC_FERS_STORE_KIND', 'KPC_FERS_STORE_DIR',
        'KPC_FERS_WORLD_STORE', 'KPC_FERS_LIVE_DIR', 'KPC_FERS_PRIVATE_LOG',
        'KPC_FERS_PRIVATE_OUT', 'KPC_FERS_NOT_SHOWN_DIR', 'KPC_FERS_PARK_S',
    }:
        os.environ.pop(k)
os.environ['PASS'] = '3'
os.environ['REGION'] = 'na'

import kpc_fers as K
import kpc_fers_switches as SW
import kpc_key_freeze as F

FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok:
        FAILS.append(what)


# One value each, from the file, when the environment is quiet.
want = {
    'KPC_FERS_SUMMARY_APPROX': '1',
    'KPC_FERS_NEAR_LINE': '1',
    'KPC_FERS_CARRY_MADE_ON': '1',
    'KPC_FERS_FINE_ONLY': 'count',
    'KPC_FERS_STRIP_HELD': '1',
}
for name, exp in want.items():
    v, src = SW.value(name)
    check(v == exp and src == 'file', f'{name} is {exp} from the file when the environment is quiet ({v}, {src})')

check(K._switch_on('KPC_FERS_SUMMARY_APPROX') is True, 'summary-approx is on from the file')
check(K.near_line_on() is True, 'near-line is on from the file')
check(K.CELL == 5.0, f'the usual pass (3) band is one 5 m cell ({K.CELL})')

pc = (ROOT / 'tools/pc-runner/kpc_pc_run.py').read_text(encoding='utf-8')
for old in ('KPC_FERS_NEAR_LINE_M', 'KPC_FERS_CARRY_MAX', 'KPC_FERS_SUMMARY_APPROX', 'KPC_FERS_STRIP_HELD'):
    check(old not in pc, f'the PC runner does not set {old}')

got = subprocess.check_output(
    [sys.executable, str(S / 'kpc_key_freeze.py'), 'rules', 'fers'],
    cwd=str(ROOT), text=True,
).strip()
check(got == '4830230a591f', f'2-fer rules hash is unchanged since review F16, 22 Nov ({got})')

if FAILS:
    print(f'{len(FAILS)} FAIL', flush=True)
    sys.exit(1)
print('OK', flush=True)
