#!/usr/bin/env python3
"""26 Nov 2026 (owner 5:30 PM: 'Confirmed-park fast path against the store room (agency-ID proof only)'; switch KPC_ID_LOCK).
  A  a park confirmed BY a stable agency id is saved as a lock (layer, id kind and value, names, acres); a park confirmed by a
     name rule, a page or a size, a row with no agency id, and an outer line are never saved.
  B  the lock HOLDS in today's layer file: the park takes all of today's records with that id, even when the agency renumbered
     its rows (same id, new row number), and is confirmed by id with no further matching.
  C  renamed, resized past 5%, dropped from the layer file, or held by two parks: the lock is broken, listed, and not used.
  F  (kit 26i, NY Bear Swamp 5,294 -> 1,748 acres) a lock is written only when the id rows are the whole park: a park that also
     holds a PAD-US copy or another parcel is matched as usual, so a lock never drops land; lock files from before this rule are
     not read; the build checks its new locks at once against the same day's layer files (one run, not two).
  D  the build skips locked parks in the matching loop, the match checks and the gate; switch on for MN and NY only.
Prints PASS / FAIL and ends ALL PASS or SOME FAILED."""
import gzip, json, os, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_same_land as SL  # noqa: E402
import kpc_key_rules as KR  # noqa: E402
import kpc_match_checks as MC  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
ns = {'os': os, 're': re, 'json': json, 'gzip': gzip, 'math': __import__('math'), 'KR': KR, 'MC': MC, 'SL': SL, 'notice': lambda *a: None,
      'OUT': pathlib.Path('/tmp')}
exec(src[src.index('def _oid(a)'):src.index('\n', src.index('def _oid(a)'))], ns)
exec(src[src.index('def _sl_layer(k):'):src.index('def _sl_index():')], ns)
exec(src[src.index('OUTER_LINE = {'):src.index('CARRY_ST = [')], ns)
check_, write_ = ns['lock_check'], ns['lock_write']


def wma(oid, uid, name, ac, fresh=True):
    return {'OBJECTID': oid, 'Unit_Nm': name, 'GIS_Acres': ac, 'SA': {'uniqueid': uid}, '_fresh': fresh}


a1 = wma('sgmna038200', 'WMA0038200', 'Smith WMA', 300)
a2 = wma('sgmna038201', 'WMA0038200', 'Smith WMA', 100)   # a second tract with the same agency id
b = wma('sgmna012900', 'WMA0012900', 'Jones WMA', 50)
named = {'OBJECTID': 'sgmna099', 'Unit_Nm': 'Name WMA', 'GIS_Acres': 10, 'SA': {}, '_fresh': True}
forest = {'OBJECTID': 'sgmnb06', 'Unit_Nm': 'Big Fork', 'GIS_Acres': 9, 'SA': {'sft': 'SFT00006'}, '_fresh': True}
parks = {'US-1': {'m': [['sgmna038200', 'Smith WMA', 300, 'id: x'], ['sgmna038201', 'Smith WMA', 100, 'id: x']],
                  'match': {'status': 'confirmed', 'by': 'id', 'id': 'MN DNR unit id WMA0038200'}},
         'US-2': {'m': [['sgmna099', 'Name WMA', 10, 'name']], 'match': {'status': 'confirmed', 'by': 'held name and pin'}},
         'US-3': {'m': [['sgmnb06', 'Big Fork', 9, 'id: x']], 'match': {'status': 'confirmed', 'by': 'id', 'id': 'MN DNR unit id SFT00006'}},
         'US-4': {'m': [['sgmna012900', 'Jones WMA', 50, 'id: x']], 'match': {'status': 'confirmed', 'by': 'id', 'id': 'MN DNR unit id WMA0012900'}}}
byid = {x['OBJECTID']: x for x in (a1, a2, b, named, forest)}
doc = write_('MN', parks, byid)
L = doc['parks']
check(f"A: agency-id parks are locked, name-confirmed parks and outer lines are not ({sorted(L)})",
      sorted(L) == ['US-1', 'US-4'] and L['US-1'] == {'layer': 'sgmna', 'kind': 'MN DNR unit id', 'value': 'WMA0038200', 'names': ['Smith WMA'], 'acres': 400})

used, broken = check_('MN', [a1, a2, b], doc)
check(f'B: the lock holds: the park takes all records with its agency id, confirmed by id ({used.get("US-1")})',
      sorted(x[0] for x in used['US-1']) == ['sgmna038200', 'sgmna038201'] and used['US-1'][0][3].startswith('id: lock: MN DNR unit id WMA0038200')
      and MC.row_class(used['US-1'][0]) == 'code' and not broken)
ren = [dict(a1, OBJECTID='sgmna077777'), dict(a2, OBJECTID='sgmna077778'), b]   # the agency renumbered its rows; the id is the same
used, broken = check_('MN', ren, doc)
check('B: an agency renumbering its rows changes nothing (same agency id, new row numbers)',
      sorted(x[0] for x in used.get('US-1') or []) == ['sgmna077777', 'sgmna077778'] and not broken)
used, broken = check_('MN', [dict(a1, Unit_Nm='Other WMA'), dict(a2, Unit_Nm='Other WMA'), b], doc)
check(f'C: renamed: the lock is broken and listed ({broken})', 'US-1' not in used and broken and 'renamed' in broken[0][5])
used, broken = check_('MN', [dict(a1, GIS_Acres=600), a2, b], doc)
check('C: resized past 5%: broken', 'US-1' not in used and 'resized' in broken[0][5])
used, broken = check_('MN', [dict(a1, GIS_Acres=310), a2, b], doc)
check('C: a small change within 5% still holds', 'US-1' in used and not broken)
used, broken = check_('MN', [b], doc)
check("C: dropped from today's layer file: broken", 'US-1' not in used and "not in today's layer file" in broken[0][5])
used, broken = check_('MN', [dict(a1, _fresh=False), dict(a2, _hint=True), b], doc)
check('C: an old copy or a hint never satisfies a lock', 'US-1' not in used)
two = {'v': 2, 'parks': dict(L, **{'US-9': dict(L['US-1'])})}
used, broken = check_('MN', [a1, a2, b], two)
check('C: two parks holding one agency id: neither lock is used', 'US-1' not in used and 'US-9' not in used and 'US-4' in used
      and all('another park holds' in x[5] for x in broken))

# 26 Nov (grade of #390): an agency id in the record's own web address (NY DEC page number), zero-size records, all tracts
dec = {'OBJECTID': 'sgnya72140', 'Unit_Nm': 'Carlton Hill Mua', 'GIS_Acres': 1346, 'SA': {'URL': 'https://www.dec.ny.gov/lands/82684.html'}, '_fresh': True}
dec2 = dict(dec, OBJECTID='sgnya74176', GIS_Acres=614)
pk = {'US-8622': {'m': [['sgnya72140', 'Carlton Hill Mua', 1346, 'id: x'], ['sgnya74176', 'Carlton Hill Mua', 614, 'id: x']],
                  'match': {'status': 'confirmed', 'by': 'id', 'id': 'NY DEC page number 82684'}}}
d2 = write_('NY', pk, {x['OBJECTID']: x for x in (dec, dec2)}, [dec, dec2])
check(f"E: a NY DEC page number in the record's own address locks; both tracts held ({d2['parks']})",
      d2['parks'].get('US-8622', {}).get('kind') == 'NY DEC page number' and d2['parks']['US-8622']['acres'] == 1960)
u2, b2 = check_('NY', [dict(dec, OBJECTID='sgnya90001'), dict(dec2, OBJECTID='sgnya90002')], d2)
check('E: the NY DEC lock holds after renumbering', sorted(x[0] for x in u2.get('US-8622') or []) == ['sgnya90001', 'sgnya90002'] and not b2)
pk1 = {'US-8622': dict(pk['US-8622'], m=[pk['US-8622']['m'][0]])}
d3 = write_('NY', pk1, {x['OBJECTID']: x for x in (dec, dec2)}, [dec, dec2])
check('E: a park holding only one of two tracts with its id is not locked (the other went elsewhere for a reason)', 'US-8622' not in d3['parks'])
nps0 = {'OBJECTID': 4447, 'Unit_Nm': 'Federal Hall National Memorial', 'GIS_Acres': 0, 'SA': {'UNIT_CODE': 'FEHA'}, '_fresh': True}
d4 = {'v': 2, 'parks': {'US-0773': {'layer': 'padus', 'kind': 'NPS unit code', 'value': 'FEHA', 'names': ['Federal Hall National Memorial'], 'acres': 0}}}
u4, b4 = check_('NY', [nps0], d4)
check(f'E: a record with no size on file both times is unchanged: the lock holds ({b4})', 'US-0773' in u4 and not b4)
u5, b5 = check_('NY', [dict(nps0, GIS_Acres=50)], d4)
check(f'E: 0 acres saved, 50 today: the lock breaks ({b5})', 'US-0773' not in u5 and b5 and 'resized' in b5[0][5])
u6, b6 = check_('NY', [dict(dec, SA={'URL': 'https://www.dec.ny.gov/lands/99999.html'}), dict(dec2, SA={'URL': 'https://www.dec.ny.gov/lands/99999.html'})], d2)
check(f"E: the agency page id in the record's address changed: the lock breaks ({b6})", 'US-8622' not in u6 and b6 and "not in today's layer file" in b6[0][5])
pad = {'OBJECTID': 9001, 'Unit_Nm': 'Smith WMA', 'GIS_Acres': 900, 'SA': {}, '_fresh': True}
pk7 = {'US-1': dict(parks['US-1'], m=parks['US-1']['m'] + [[9001, 'Smith WMA', 900, 'name']])}
d7 = write_('MN', pk7, {**byid, '9001': pad}, [a1, a2, b, pad])
check(f"F: a park that also holds a row with no agency id and no outline to measure is not locked: a lock never drops land ({sorted(d7['parks'])})",
      'US-1' not in d7['parks'])
sq = lambda x0, y0, x1, y1: {'rings': [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]}
g1, g2 = dict(a1, _g=sq(0, 0, .02, .02)), dict(a2, _g=sq(.02, 0, .03, .02))
byg = {**byid, 'sgmna038200': g1, 'sgmna038201': g2}
cp = dict(pad, _g=sq(.001, .001, .029, .019))        # a PAD-US copy of the same ground
big = dict(pad, _g=sq(0, 0, .05, .02))               # a PAD-US row covering more land (Bear Swamp, Lost Nation)
d10 = write_('MN', pk7, {**byg, '9001': cp}, [g1, g2, b, cp])
check(f"F: a PAD-US copy lying on the id rows' own ground rides along: the park is locked ({sorted(d10['parks'])})", 'US-1' in d10['parks'])
d11 = write_('MN', pk7, {**byg, '9001': big}, [g1, g2, b, big])
check(f"F: a PAD-US row covering more land than the id rows stops the lock ({sorted(d11['parks'])})", 'US-1' not in d11['parks'])
pk8 = {'US-1': dict(parks['US-1'], m=parks['US-1']['m'] + [['9001~old', 'Smith WMA', 900, 'name']])}
d8 = write_('MN', pk8, {**byid, '9001~old': dict(pad, _hint=True, _fresh=False)}, [a1, a2, b])
check('F: an old hint row (never drawn) does not stop a lock', 'US-1' in d8['parks'] and d8.get('v') == 2)
u9, b9 = check_('MN', [a1, a2, b], {'parks': doc['parks']})
check(f'F: a lock file from before the whole-park rule (no version) is not read ({sorted(u9)})', not u9 and not b9)
run_ = src[src.index('def run(st):'):]
check('F: the build checks its new locks against the same day\'s layer files and says so',
      '_su, _sb = lock_check(st, recs, _doc)' in run_ and 'same-day check of the new locks' in run_)
check('D: locked parks skip the matching loop, the match checks and the gate',
      "if ref in LOCK_ROWS:" in run_ and 'set(TRL) | set(LOCK_ROWS)' in src and src.count('set(TRL) | set(LOCK_ROWS)') == 2)
sw = json.load(open(ROOT / '.github/key-switches.json'))['switches'].get('KPC_ID_LOCK') or {}
check('D: the switch is on for MN, NY and the nine spread-test states (owner 26 Nov 8:20 PM)', sw.get('on') == ['CA', 'CO', 'FL', 'GA', 'ME', 'MN', 'NY', 'PA', 'TX', 'WA', 'WI'])
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
