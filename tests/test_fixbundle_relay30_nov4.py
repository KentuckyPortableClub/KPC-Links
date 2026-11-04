#!/usr/bin/env python3
"""Offline test, Nov 4 PM fix bundle item 12 (Brandon's yes relayed via Super Head Bot, 4:53 PM CST Nov 4): the Discord relay
runs about every 30 min instead of ~10-15: its own schedule (the same one schedule, changed), the quick look's full-run gap, and
the Apps Script watcher's gap (the copy in the repo; it takes effect only when pasted into Apps Script). No new cron."""
import os, pathlib, re, subprocess, sys
HERE = pathlib.Path(__file__).resolve().parent.parent
os.chdir(HERE)
sys.path.insert(0, '.github/scripts')
ok = True
def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)
wf = open('.github/workflows/kpc-discord-relay.yml', encoding='utf-8').read()
crons = re.findall(r"^\s*-\s*cron:\s*'([^']+)'", wf, re.M)
check(crons == ['5,35 * * * *'], f'one schedule, every 30 min: {crons}')
import kpc_relay_peek as P   # noqa: E402
check(P.FULL_EVERY_MIN == 29, f'the quick look does the full run when the last one is 29+ min old ({P.FULL_EVERY_MIN})')
gs = open('.claude/build/relay/kpc-mailer.gs', encoding='utf-8').read()
check(re.search(r'var MIN_GAP_MIN = 28;', gs) and re.search(r'var QUIET_GAP_MIN = 28;', gs), 'the watcher starts the relay only when its newest run is 28+ min old (day and night)')
base = 'origin/main' if subprocess.run(['git', 'rev-parse', '-q', '--verify', 'origin/main'], capture_output=True).returncode == 0 else 'HEAD~1'
allc = lambda txt: set(re.findall(r"^\s*-\s*cron:\s*['\"]([^'\"]+)", txt, re.M))
new = [(p.name, sorted(allc(p.read_text(encoding='utf-8')) - allc(subprocess.run(['git', 'show', f'{base}:{p.as_posix()}'], capture_output=True, text=True).stdout)))
       for p in sorted(pathlib.Path('.github/workflows').glob('*.yml')) if p.name != 'kpc-discord-relay.yml']
new = [x for x in new if x[1]]
check(new == [], f'no new cron elsewhere (vs {base}): {new}')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
