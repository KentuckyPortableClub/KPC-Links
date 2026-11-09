#!/usr/bin/env python3
"""Nov 8 (Quality NO on US-42446831487): Brandon's 15 signed Nov 7 overrides (Links 2c9315eb) must come out as OUTLINES.

1. The 15 km join check never holds a join that a signed override (decided_by) names, by id or by name.
2. Every one of the 15 has a signed 'join' in overrides.json naming the override ids.
3. KPC_CHECK_BUILT=1 (after the US rebuild): every one of the 15 is an outline in data/us-key carrying an override id.
4. kpc_save never writes data/status/-.json; the key check also compares with the RELEASED key."""
import json, os, pathlib, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_join_check as J
import kpc_save as S
import kpc_key_postcheck as KC

ok = True
def check(cond, msg):
    global ok
    print(('PASS ' if cond else 'FAIL ') + msg); ok = ok and bool(cond)

FIFTEEN = ['US-0150', 'US-10281', 'US-11401', 'US-12028', 'US-13039', 'US-4894', 'US-4933', 'US-4934', 'US-4955',
           'US-5789', 'US-5869', 'US-6197', 'US-6202', 'US-3917', 'US-9678']
ov = json.load(open(ROOT / 'data/us-key/overrides.json', encoding='utf-8'))['parks']
okmap, _ = J.approvals(str(ROOT), 'us', {'ANSWER_SHEET': '/nonexistent'})
for r in FIFTEEN:
    v = ov.get(r) or {}
    check(bool(v.get('join')) and str(v.get('decided_by') or '').startswith('Brandon'), f'{r}: signed join in overrides.json ({v.get("join")})')
    # a far join (no 'reviewed' tag: the name test joined it) on the override ids: the join check must not hold it
    p = {'n': r, 'g': 'official', 'm': [[x, (v.get('fp') or {}).get(x, ['?'])[0], 0, 'name'] for x in v.get('join') or []]}
    why = J.exempt(r, p, okmap)
    check(why.startswith('signed override'), f'{r}: far join on {v.get("join")} is not held ({why or "HELD"})')
    # by name only (record renumbered, same signed name)
    nm = next(iter((v.get('fp') or {}).values()), [None])[0]
    if nm:
        p2 = {'n': r, 'g': 'official', 'm': [['renumbered-1', nm, 0, 'name']]}
        check(J.exempt(r, p2, okmap).startswith('signed override'), f'{r}: a join on the signed NAME {nm!r} is not held')
# an unsigned far join is still held (park not in overrides)
p = {'n': 'x', 'g': 'official', 'm': [['zz-nobody-signed', 'Nowhere', 0, 'name']]}
check(J.exempt('US-99999', p, okmap) == '', 'an unsigned far join is still held')

# Gap closed (#53 / Quality): an UNSIGNED overrides.json join must NOT exempt a far piece
# (Links #77's test above did not cover this — US-99999 had no override entry).
# Together with the builder's ~0.6° override box, that gap let unsigned joins past 5 km survive.
import tempfile, json as _json
with tempfile.TemporaryDirectory() as _td:
    _td = pathlib.Path(_td); (_td / 'data/us-key').mkdir(parents=True)
    _json.dump({'parks': {
        'US-88888': {'join': ['far-piece-1'], 'why': 'unsigned apply', 'when': '2026-11-08'},
        'US-88887': {'join': ['signed-piece-1'], 'fp': {'signed-piece-1': ['Signed Land', 10]},
                     'why': 'signed', 'decided_by': 'Brandon (KZ4CP), Nov 8 2026'},
    }}, open(_td / 'data/us-key/overrides.json', 'w'))
    _ok, _ = J.approvals(str(_td), 'us', {'ANSWER_SHEET': '/nonexistent'})
    check('far-piece-1' not in (_ok.get('US-88888') or set()), 'unsigned override ids are not loaded into ok/exempt map')
    check(J.exempt('US-88888', {'n': 'u', 'g': 'official', 'm': [['far-piece-1', 'Far', 0, 'name']]}, _ok) == '',
          'unsigned override far join is still held (beyond 5 km band)')
    check(J.exempt('US-88887', {'n': 's', 'g': 'official', 'm': [['signed-piece-1', 'Signed Land', 0, 'name']]}, _ok).startswith('signed override'),
          'decided_by override far join still passes (signed exemption)')

if os.environ.get('KPC_CHECK_BUILT') == '1':
    N = KC.parks_of(KC.load_tree('us', None, str(ROOT)))
    for r in FIFTEEN:
        p = N.get(r) or {}; ids = {str(x[0]) for x in p.get('m') or [] if x}
        check(KC.has_outline(p) and ids & {str(x) for x in ov[r]['join']}, f'{r}: built key is an outline on the override ids (g={p.get("g")}, m={sorted(ids)[:4]})')

# kpc_save: an inline 'python3 -' never names its status file '-'
check(S.status_name('-', {}) == 'inline', "status_name('-') -> inline")
check(S.status_name('-', {'GITHUB_WORKFLOW': 'KPC world answer key'}) == 'inline-kpc-world-answer-key', 'inline script named after its workflow')
check(S.status_name('.github/scripts/kpc_us_key.py', {}) == 'kpc_us_key', 'a script keeps its own name')
check(S.status_name('-', {'KPC_STATUS_NAME': 'us key/stamp'}) == 'us-key-stamp', 'KPC_STATUS_NAME wins (made safe)')
check(not (ROOT / 'data/status/-.json').exists(), 'the stray data/status/-.json is gone')

# key check: released comparison
with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t, 'data/us-key'); d.mkdir(parents=True)
    json.dump({'parks': {'US-0001': {'g': 'official', 'm': [[1, 'A', 5, 'name']]}}}, open(d / 'US-ZZ.json', 'w'))
    json.dump({'build': 'US-1'}, open(d / 'index.json', 'w'))
    rel, f = KC.released_tree('us', {'RELEASED_DIR': t})
    check(f and 'US-ZZ' in rel, 'released_tree reads RELEASED_DIR/data/us-key')
    _, _, ch = KC.compare({'US-ZZ': {'parks': {'US-0001': {'g': 'pin', 'm': []}}}}, rel)
    check(ch['outline_to_pin'] == ['US-0001'], 'outline -> pin is measured against the released key')
    check(KC.released_tree('us', {'RELEASED_DIR': '/nonexistent'}, cwd=t)[1] is None, 'no released folder -> None (note only)')

print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
