#!/usr/bin/env python3
"""Ledger 59 (KPC owner, 2026-11-17): a public side file written BEFORE a park was held is redacted again at exit against the
final withheld set (refs and names), carried rows kept, and a file with nothing secret is left alone."""
import json, os, pathlib, sys, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / '.github/scripts'))
import kpc_fers_store as S
import kpc_save

fails = 0
def check(ok, what):
    global fails
    print(('PASS ' if ok else 'FAIL ') + what); fails += 0 if ok else 1

def reset():
    S.PUBLIC_WRITTEN.clear(); S.HELD_PRIVATE.clear(); S.PRIVATE.clear(); S.READ_OK.clear(); S.READ_OK_RUN.clear()
    S.NAMES.clear(); S._NAME_CACHE.clear(); S.CARRIED_JSON.clear(); S.PRIVATE_OUT = None

tmp = pathlib.Path(tempfile.mkdtemp())
os.chdir(tmp)  # kpc_save writes data/status/<this test>.json in the working directory; keep that out of the repo
def write(name, doc):
    p = tmp / name; kpc_save.save_json(p, doc); S.PUBLIC_WRITTEN[str(p)] = (kpc_save.save_json, (), {}); return p

# 1. looked- file written before US-9001 was held: the ref goes at exit
reset()
p = write('looked-zz.json', {'about': 'x', 'parks': ['US-9001', 'US-9002'], 'by': {'US-9001': 1, 'US-9002': 2}})
check(S.final_redact() == 0, 'nothing held yet: no file rewritten')
S.HELD_PRIVATE.add('US-9001')
check(S.final_redact() == 1, 'held later: the file is redacted again')
d = json.loads(p.read_text())
check(d['parks'] == ['US-9002'] and 'US-9001' not in d['by'], 'the held ref is gone from list and keys, the other stays')
check('US-9001' not in p.read_text(), 'no mention of the held ref is left')

# 2. a held park's distinctive NAME in a text is masked; a public namesake does not stop it, a common name is never looked for
reset()
S.NAMES.update({'US-9001': 'Zxquill Hollow Preserve', 'US-9002': 'Lake Park'})
S.HELD_PRIVATE.add('US-9001')
p = write('missing-zz.json', {'parks': [{'ref': 'US-9002', 'note': 'inside Zxquill Hollow Preserve'}, {'ref': 'US-9003', 'note': 'fine'}],
                              'why': 'near zxquill-hollow  preserve'})
S.final_redact()
t = p.read_text()
check('xquill' not in t.lower(), 'the held name is gone in any spelling')
check('US-9003' in t, 'rows that do not name it stay')

# 3. carried rows of a spot file are kept exactly
reset()
S.HELD_PRIVATE.add('US-9001')
row = {'refs': ['US-9001', 'US-9004'], 'store_held': S.HELD_TAG}
S.CARRIED_JSON['US-ZZ'] = {S._canon(row)}
p = write('US-ZZ.json', {'spots': [row, {'refs': ['US-9001', 'US-9005']}, {'refs': ['US-9006', 'US-9007']}]})
S.final_redact()
sp = json.loads(p.read_text())['spots']
check(row in sp and len(sp) == 2 and all('US-9005' not in json.dumps(x) for x in sp), 'carried row kept, other row naming the park left out')

# 4. a private run does nothing here
reset(); S.PRIVATE_OUT = tmp; S.HELD_PRIVATE.add('US-9001')
p = write('report-zz.json', {'x': 'US-9001'})
check(S.final_redact() == 0 and 'US-9001' in p.read_text(), 'private store run: untouched (every file is private already)')

# 5. read-ok parks may be named
reset(); S.HELD_PRIVATE.add('US-9001'); S.READ_OK.add('US-9001')
p = write('report-zz.json', {'x': 'US-9001'})
check(S.final_redact() == 0, 'a park read from publishable records only is not redacted')

print('ALL PASS' if not fails else f'{fails} FAILED - SOME FAILED'); sys.exit(1 if fails else 0)
