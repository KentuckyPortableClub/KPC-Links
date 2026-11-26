#!/usr/bin/env python3
"""25 Nov 2026, #380 round 15 (the owner's MN + NY 2:28 PM test, rules 03c3525be24b: Minnesota Valley SRA US-7145 lost 339
pieces; check rows 426 -> 1,424). Invented records only.
  A  the store reads a layer's own acres field by the live reader's rule (first field with 'acre': MN DNR 'su_acres').
  B  the website key's old rows follow their PROVEN fresh record (old row numbers are not ids); no D1 check rows from numbers.
  C  the old-size proof compares like with like (the builder's twins counted on both sides, or left out on both).
  D  the per-row proof list reads 'left the map' after the gate.
Prints PASS / FAIL and ends ALL PASS or SOME FAILED."""
import gzip, json, os, pathlib, re, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_store_attrs as SA  # noqa: E402
import kpc_same_land as SL  # noqa: E402
import kpc_key_rules as KR  # noqa: E402
import kpc_match_checks as MC  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


# ---- A ----------------------------------------------------------------------------------------------------------------------
ra = SA.record_acres
check("A: a Minnesota DNR parcel's own 'su_acres' is its size (not its section-sized outline)",
      ra({'attributes': {'objectid': 15, 'su_id': 340056, 'su_acres': 16.4, 'su_pctforty': 100}}) == 16.4)
check("A: GIS_Acres still wins when a record has it; a FWS 'SUM_GISACRES' is read; no acres field = None",
      ra({'attributes': {'GIS_Acres': 40, 'su_acres': 16.4}}) == 40 and ra({'attributes': {'SUM_GISACRES': 779.5}}) == 779.5
      and ra({'attributes': {'NAME': 'X'}}) is None and ra({'attributes': {'su_acres': 0}}) is None and ra({'attributes': {'su_acres': 'n/a'}}) is None)
check('A: the id file is format 11 and the PC test remakes an older one',
      "'format': 11" in (ROOT / '.github/scripts/kpc_store_attrs.py').read_text(encoding='utf-8')
      and 'fmt < 11' in (ROOT / 'tools/pc-keys/kpc_test_keys.py').read_text(encoding='utf-8'))

# ---- B ----------------------------------------------------------------------------------------------------------------------
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
ns = {'os': os, 're': re, 'json': json, 'gzip': gzip, 'math': __import__('math'), 'KR': KR, 'MC': MC, 'notice': lambda *a: None}
exec(src[src.index('def _oid(a)'):src.index('\n', src.index('def _oid(a)'))], ns)
exec(src[src.index('RA_USED = {}'):src.index('\ndef _maiden6')], ns)
fop = ns['fresh_old_parks']
recs = [{'OBJECTID': 'sgzze3033', 'Unit_Nm': 'MINNESOTA VALLEY', 'GIS_Acres': 16.4, '_fresh': True},
        {'OBJECTID': 'sgzze3045', 'Unit_Nm': 'OTHER LAND', 'GIS_Acres': 80.0, '_fresh': True},     # took the old number 3045
        {'OBJECTID': 'sgzze3050', 'Unit_Nm': 'MINNESOTA VALLEY', 'GIS_Acres': 12.0, '_fresh': True},
        {'OBJECTID': 'sgzze9001~old', 'Unit_Nm': 'GONE', 'GIS_Acres': 5, '_hint': True},
        {'OBJECTID': 237576, 'Unit_Nm': 'Some Park', 'GIS_Acres': 900.0, '_fresh': True}]
old = {'US-9200': {'n': 'Minnesota Valley State Recreation Area', 'ac': 30,
                   'm': [['sgzze3045', 'MINNESOTA VALLEY', 16, 'name'], ['sgzze3046', 'MINNESOTA VALLEY', 12, 'name'],
                         ['sgzze3047', 'MINNESOTA VALLEY', 12, 'name'], ['sgzze9001', 'GONE', 5, 'name'], [237576, 'Some Park', 899, 'name']],
                   'twin': ['sgzze3047']},
       'US-9201': {'n': 'Pin Park', 'm': []}}
alias = {'sgzze3045': 'sgzze3033', 'sgzze3046': 'sgzze3050', 'sgzze3047': 'sgzze3050', '237576': '237576'}
new = fop(old, alias, recs)
m = new['US-9200']['m']
check(f"B: an old row follows its PROVEN fresh record (3045 -> 3033), never the fresh record that now carries its number ({m[0]})",
      m[0][:3] == ['sgzze3033', 'MINNESOTA VALLEY', 16] and m[0][3] == 'name')
check('B: two old rows proven to ONE fresh record are the land once; the fresh record brings its own size',
      [x[0] for x in m].count('sgzze3050') == 1 and next(x for x in m if x[0] == 'sgzze3050')[2] == 12)
check("B: an old row with no proven twin names its old HINT ('~old' when a fresh record took its number): never drawn",
      any(x[0] == 'sgzze9001~old' for x in m))
check('B: a PAD-US id stays a number; the twin ids follow the same way; a park with no rows is left alone',
      any(x[0] == 237576 and x[2] == 900 for x in m) and new['US-9200']['twin'] == ['sgzze3050'] and new['US-9201'] == old['US-9201'])
check('B: nothing moves when there is no fresh source (no alias)', fop(old, {}, recs) is old)
run_ = src[src.index('def run(st):'):]
check('B: the keep-last-good guard and the saved-id carry both read the website key through fresh_old_parks',
      run_.count('fresh_old_parks(old, _alias, recs)') == 2 and '_alias = {}' in run_[:run_.index("recs, _alias = fresh_records(")])
check("B: with the fresh source the D1 number check never runs (no 'this saved record id now holds other land' rows from row numbers)",
      "if _kr('KPC_SAVED_ID_LAND') and not _fresh_map:" in run_)

# ---- C ----------------------------------------------------------------------------------------------------------------------
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    ns['OUT'] = td
    bx = lambda x, y, d: [x, y, x + d, y + d]
    # the website key: 10 parcels of 100 acres; 3 are the builder's twins (same land again); its 'ac' counted all 10 (1,000)
    om = [[f'sgzze{i}', 'MINNESOTA VALLEY', 100, 'name'] for i in range(10)]
    (td / 'US-ZZ.json').write_text(json.dumps({'parks': {'US-9300': {'n': 'Minnesota Valley State Recreation Area', 't': 'State Recreation Area',
                                                                     'ac': 1000, 'm': om, 'twin': ['sgzze7', 'sgzze8', 'sgzze9']}}}))
    ns['OLD_BOX'].clear(); ns['OLD_BOX'].update({f'sgzze{i}': bx(-93.5 + i * 0.01, 44.7, 0.01) for i in range(10)})
    byid = {f'sgzze{i + 100}': {'Unit_Nm': 'MINNESOTA VALLEY', 'GIS_Acres': 100, '_bb': bx(-93.5 + i * 0.01, 44.7, 0.01), '_fresh': True} for i in range(10)}
    p = {'n': 'Minnesota Valley State Recreation Area', 't': 'State Recreation Area', 'twin': ['sgzze107', 'sgzze108', 'sgzze109'],
         'm': [[f'sgzze{i + 100}', 'MINNESOTA VALLEY', 100, 'name'] for i in range(10)]}
    r, st_ = ns['park_name_and_size']('US-9300', p, byid, {}, 'ZZ')
    check(f"C: twins left out of the fresh sum (700) and counted in the website's 'ac' (1,000): compared like with like, proven ({r})",
          st_ == 'ok' and r.startswith('name and old joined size'))
    p_off = dict(p, m=[[f'sgzze{i + 100}', 'MINNESOTA VALLEY', 100, 'name'] for i in range(5)], twin=[])
    check('C: half the land (500 of 1,000, or of 700): still not proven', ns['park_name_and_size']('US-9300', p_off, byid, {}, 'ZZ')[1] != 'ok')
    byf = {k: dict(v, _bb=bx(-80.0, 30.0, 0.01)) for k, v in byid.items()}
    check('C: the right size on other ground: not proven', ns['park_name_and_size']('US-9300', p, byf, {}, 'ZZ')[1] != 'ok')

# ---- D ----------------------------------------------------------------------------------------------------------------------
g = src[src.index('def proven_only_gate('):src.index('\nFRESH = {}')]
check("D: the proof list's 'left the map' is read from the gate's own answer (not before the park's rows were emptied)",
      "or not keep or (tr_.get('level') and str(tr_.get('best') or '') in _gone_ids)" in g and "or not p['m']) else 'n'" not in g)

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
