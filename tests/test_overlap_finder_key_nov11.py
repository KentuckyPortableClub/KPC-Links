#!/usr/bin/env python3
"""Nov 11 2026 (KPC owner): the overlap finder grades every region by the CURRENT answer key (read from the KPC-Data site the
way the map reads it), never lists a bare pin, marks approximate parks not official, holds trail / river rows under 25 m, and
shows nothing when a key does not load. Runs tests/overlap_finder_key_nov11.js in node (fake fetch, no network, no browser)."""
import pathlib, shutil, subprocess, sys
HERE = pathlib.Path(__file__).resolve().parent
node = shutil.which('node')
if not node:
    print('SKIP node is not installed here'); sys.exit(0)
r = subprocess.run([node, str(HERE / 'overlap_finder_key_nov11.js')], capture_output=True, text=True, timeout=120)
print(r.stdout.strip())
if r.stderr.strip(): print(r.stderr.strip()[-2000:])
ok = r.returncode == 0 and r.stdout.strip().endswith('ALL PASS')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
