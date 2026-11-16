#!/usr/bin/env python3
"""KPC owner, 2026-11-16 (handoff 'proof of work', item 5): key checks at join time. A record whose own TYPE is a conservation
easement: a NEW join by name alone is refused in every state (kpc_us_key.easement_record / name_only, applied after matching: the
piece goes to CHECK with its reason). An EXISTING one (saved record ids kept through a rules change) is not removed: it is listed in
data/us-key/review/easement-name-joins.csv (ref, record, state); New York re-checks its existing ones too. A person's join
(overrides, 'reviewed') still stands. Made-up records only. Also: this change's own changelog
line and scope entry are found by their id (not 'the newest line')."""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCR = ROOT / '.github' / 'scripts'
sys.path.insert(0, str(SCR))
FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok: FAILS.append(what)


# kpc_us_key.py runs the whole key when imported, so its item-5 helpers are read from the source and run alone
import re, types  # noqa: E402
_src = (SCR / 'kpc_us_key.py').read_text(encoding='utf-8')
_a = _src.index('# KPC owner, 2026-11-16 (handoff item 5, v4 answer 1)'); _b = _src.index('\ndef ', _src.index('def name_only'))
U = types.SimpleNamespace(); _ns = {'re': re}; exec(_src[_a:_b], _ns); U.__dict__.update(_ns)

# the record's own type
check(U.rec_type({'name': 'Test Mountain', 'category': 'Conservation Easement'}) == 'Conservation Easement', "a state layer's CATEGORY field is the record's type")
check(U.rec_type({'name': 'Test Park', 'acres': 12}) == '', 'a layer with no type field gives no type')
for a, want in (({'Category': 'Easement'}, True), ({'Des_Tp': 'CONE'}, True), ({'d_Des_Tp': 'Conservation Easement'}, True),
                ({'Category': 'Fee', 'Rec_Type': 'Conservation Easement'}, True), ({'SA': {'INTEREST': 'Easement'}}, True),
                ({'Category': 'Fee', 'Des_Tp': 'SP'}, False), ({'Category': 'Fee', 'Rec_Type': 'State Park'}, False),
                ({'SA': {'OWNER': 'Easement Holders Inc'}}, False), ({'Unit_Nm': 'Easement Road Park'}, False)):
    check(U.easement_record(a) is want, f'easement type {a} -> {want}')
for how, want in (('name', True), ('words', True), ('name (designation code ignored)', True), ('name · second name', True),
                  ('override', False), ('reviewed', False), ('saved id', False), ('', False)):
    check(U.name_only(how) is want, f"join '{how}' is a name-alone join: {want}")

# the hold runs at join time, before the other name checks, and moves the piece to CHECK (never drops it silently)
src = (SCR / 'kpc_us_key.py').read_text(encoding='utf-8')
i, j = src.find('_ce = [x for x in m if name_only(x[3]) and easement_record('), src.find("weak = [x for x in m if str(x[3]).split(' · ')[0] in WEAK")
check(0 < i < j, 'the easement check runs on the matched pieces before the shared-words checks')
check("'check: a conservation easement record is never joined by name alone" in src and 'EASEMENT_HELD.extend' in src,
      'a held easement piece goes to the CHECK list with its reason and is counted in the notice')
check("**({'Rec_Type': _rt} if _rt else {})" in src, "the state layer read keeps the record's own type (a record with no type field is unchanged)")

# existing joins (v4 answer 1): kept and listed, not removed; New York re-checks them
check(U.EASEMENT_RECHECK_STATES == {'NY'}, 'only New York re-checks its existing name-alone easement joins')
k0 = src.find("keep['kept_ids'] = 'saved record ids kept through a rules change"); k1 = src.find('parks[ref] = keep; carried += 1')
blk = src[k0:k1]
check(0 < k0 < k1 and 'EASEMENT_KEPT.extend' in blk and 'st in EASEMENT_RECHECK_STATES' in blk,
      'the saved-id keep lists an existing name-alone easement join (and only NY moves it to CHECK)')
check("'easement_name_joins': sorted(EASEMENT_KEPT)" in src, "each state file carries its existing easement joins for the review file")
import contextlib, io, tempfile  # noqa: E402
import kpc_join_check as JC  # noqa: E402
check(JC.EASEMENT_CSV == 'data/us-key/review/easement-name-joins.csv', 'the review file is data/us-key/review/easement-name-joins.csv')
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); (t / 'data/us-key').mkdir(parents=True)
    json.dump({'st': 'NY', 'parks': {}, 'easement_name_joins': []}, open(t / 'data/us-key/US-NY.json', 'w'))
    json.dump({'st': 'VT', 'parks': {}, 'easement_name_joins': [['US-9991', 'sgvta12']]}, open(t / 'data/us-key/US-VT.json', 'w'))
    with contextlib.redirect_stdout(io.StringIO()): per = JC.easement_review(t)
    check(per == {'US-VT': 1} and (t / JC.EASEMENT_CSV).read_text() == 'ref,record,state\nUS-9991,sgvta12,US-VT\n', 'the review file: ref, record, state; count per state')
rv = (ROOT / 'data/us-key/review/easement-name-joins.csv').read_text(encoding='utf-8')
check(rv.splitlines()[:1] == ['ref,record,state'], 'the review file is in the repo with its header (rows come with each state\'s next key build)')

# bookkeeping, by this change's own id
sc = next((c for c in json.loads((ROOT / '.github/us-key-rule-scope.json').read_text())['changes'] if c.get('id') == '2026-11-16-easement-not-by-name'), {})
check(sc.get('from') == 'd4ebfafce438' and sc.get('scope', {}).get('all') is True and not sc.get('scope', {}).get('saved_ids') and 'WAITING' in str(sc.get('approved')),
      'scope entry 2026-11-16-easement-not-by-name (from d4ebfafce438, every US state, saved ids kept, waiting for the owner)')
log = (ROOT / 'docs/key-rules-change.txt').read_text(encoding='utf-8')
own = next((x for x in log.splitlines() if 'branch prep/2026-11-16-easement-rule' in x and 'US rules d4ebfafce438 -> ' in x), '')
check(bool(own) and "waiting for the KPC owner's approval" in own, "this change's own changelog line is there, waiting for the owner")

print('ALL PASS' if not FAILS else 'SOME FAILED')
sys.exit(1 if FAILS else 0)
