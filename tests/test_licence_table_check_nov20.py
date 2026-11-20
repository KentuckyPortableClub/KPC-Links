#!/usr/bin/env python3
"""Licence-table CI check (row 16): the public table uses the keeper's coded form, never a layer address.

data/outlines/licence-verdicts.csv lands with KPC-Links #313 (head 38ddad4c) in the same coded form
(layer,key id,publish,licence class,credit line,date read; layer = sha256: + 16 hex). This test checks
the format against fixtures and, when the live file is present, against that file too. A release-file
compare uses a fixture stand-in (CI has gh logged out).
"""
import pathlib, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCR = ROOT / '.github' / 'scripts'
sys.path.insert(0, str(SCR))
import kpc_licence_table_check as C  # noqa: E402

FAILS = []
FX = ROOT / 'tests' / 'fixtures' / 'licence-verdicts'


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok:
        FAILS.append(what)


c1 = C.licence_code('https://x.example/a/FeatureServer/0')
check(c1 == 'sha256:' + __import__('hashlib').sha256(b'x.example/a/featureserver/0').hexdigest()[:16],
      'licence_code is sha256: plus 16 hex of host + lower-case path')
check(C.licence_code('https://X.example/a/FeatureServer/0/query') == c1
      and C.licence_code('https://x.example/a/featureserver/0/') == c1,
      'the code ignores case, /query and a trailing slash, as the keeper does')

sample, same, disagree, bad = FX / 'sample.csv', FX / 'release-same.csv', FX / 'release-disagree.csv', FX / 'bad-address.csv'
check(sample.is_file() and same.is_file() and disagree.is_file() and bad.is_file(), 'fixtures are checked in')
check(C.problems_in(sample) == [], 'a coded fixture has no problems')
bad_p = C.problems_in(bad)
check(any('sha256:' in x or 'not a sha256' in x or 'address' in x for x in bad_p),
      'a table with a raw layer address is rejected')
check(all('x.example' not in line for f in (sample, same, disagree)
          for line in f.read_text(encoding='utf-8').splitlines()),
      'checked-in good fixtures contain no layer addresses')
check(C.compare(sample, same) == [], 'a matching release copy compares clean')
dis = C.compare(sample, disagree)
check(any('publish=' in x for x in dis), 'a disagreeing release publish answer is reported')

# CLI: fixture table
rc = C.main(['--table', str(sample)])
check(rc == 0, 'CLI accepts a coded table')
rc = C.main(['--table', str(sample), '--release', str(same)])
check(rc == 0, 'CLI accepts a matching --release copy')
rc = C.main(['--table', str(sample), '--release', str(disagree)])
check(rc == 1, 'CLI exits 1 when the release publish answer disagrees')
rc = C.main(['--table', str(bad)])
check(rc == 1, 'CLI exits 1 on a table that has a layer address')

live = ROOT / 'data' / 'outlines' / 'licence-verdicts.csv'
if live.is_file():
    live_p = C.problems_in(live)
    check(live_p == [], 'the live licence-verdicts.csv is in the coded public form (no addresses)')
    check('http://' not in live.read_text(encoding='utf-8').lower()
          and 'https://' not in live.read_text(encoding='utf-8').lower(),
          'the live table file contains no http(s) addresses')
else:
    with tempfile.TemporaryDirectory() as td:
        rc = C.main(['--root', td])
        check(rc == 0, 'CLI exits 0 with a notice when the live table is not in the tree yet (#313)')

print('ALL PASS' if not FAILS else 'SOME FAILED')
sys.exit(1 if FAILS else 0)
