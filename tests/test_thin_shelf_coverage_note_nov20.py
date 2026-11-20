#!/usr/bin/env python3
"""Nov 20: the 17 Nov thin-shelf 85.2% note must not be presented as a current undated coverage figure."""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
log = (ROOT / 'docs' / 'key-rules-change.txt').read_text(encoding='utf-8')
FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok:
        FAILS.append(what)


lines = [x for x in log.splitlines() if '85.2%' in x]
check(len(lines) == 1, 'the 85.2% figure appears on one changelog line')
line = lines[0] if lines else ''
check('thin-shelf' in line or 'thin public shelf' in log.split('85.2%')[0][-400:],
      'the figure sits on the thin-shelf changelog entry')
check('17 Nov 2026' in line or '2026-11-17' in line,
      'the figure is dated to 17 Nov 2026, the day of that change')
check('not a current' in line and 'coverage block' in line,
      'the line says it is not a current public coverage number and points at each area\'s coverage block')

print('ALL PASS' if not FAILS else 'SOME FAILED')
sys.exit(1 if FAILS else 0)
