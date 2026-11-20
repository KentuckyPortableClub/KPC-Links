#!/usr/bin/env python3
"""Nov 20: a no-re-read layer baseline whose hand count is slightly below the file is not a 'suspect' warning.
A cap leftover (no such how-text) is still suspect. A SHORT baseline is still a failure."""
import json, pathlib, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLIP = str(ROOT / '.github' / 'scripts' / 'kpc_master_cli.py')
FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok:
        FAILS.append(what)


def run_check(root):
    return subprocess.run([sys.executable, '-B', CLIP, 'check', '--root', str(root)],
                          capture_output=True, text=True)


with tempfile.TemporaryDirectory() as td:
    root = pathlib.Path(td)
    layers = {
        'format': 1,
        'caches': {},
        'layers': {
            'US-ZZ.sgzza': {
                'expected_count': 317, 'source_count': 324,
                'baseline_how': 'hand count, no re-read this month',
                'url': 'https://example.gov/a', 'areas': ['US-ZZ'],
            },
            'US-YY.sgzyb': {
                'expected_count': 200, 'source_count': 227,
                'baseline_how': 'count query capped at 200',
                'url': 'https://example.gov/b', 'areas': ['US-YY'],
            },
        },
    }
    (root / 'layers.json').write_text(json.dumps(layers))
    r = run_check(root)
    check(r.returncode == 0, 'check exits 0 when nothing is SHORT')
    check('US-ZZ.sgzza' not in r.stdout, 'a no-re-read hand count slightly below the file is not listed as suspect')
    check('suspect baseline' in r.stdout and 'US-YY.sgzyb' in r.stdout,
          'a cap leftover without no-re-read is still a suspect warning')

    layers['layers']['US-WW.sgzwc'] = {
        'expected_count': 228, 'source_count': 227,
        'baseline_how': 'hand count, no re-read this month',
        'url': 'https://example.gov/c', 'areas': ['US-WW'],
    }
    (root / 'layers.json').write_text(json.dumps(layers))
    r = run_check(root)
    check(r.returncode == 1 and 'SHORT' in r.stdout and 'US-WW.sgzwc' in r.stdout,
          'a SHORT baseline still fails, even with no re-read in how')

print('ALL PASS' if not FAILS else 'SOME FAILED')
sys.exit(1 if FAILS else 0)
