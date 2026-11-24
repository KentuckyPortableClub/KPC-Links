#!/usr/bin/env python3
"""24 Nov 2026 (owner approved D): report-only clean-up stage. Collapse check rows
to one row per park per reason (with a count and the IDs); pre-sort the five
buckets; do not rewrite key `c` rows; not a rules file. Invented parks only.
No network. Prints PASS / FAIL, ends ALL PASS or SOME FAILED."""
import copy, pathlib, socket, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))


def _no_net(*a, **k):
    raise RuntimeError('no network in tests')


socket.socket.connect = _no_net
import kpc_cleanup_report as CR  # noqa: E402
import kpc_key_freeze as KF  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


# 304 compilation copies of the same already-joined invented park, plus one other reason
copies = [{'park': 'US-9001', 'reason': 'compilation: a copy of land already joined',
           'record': f'sgzza{i}', 'state': 'ZZ'} for i in range(304)]
copies.append({'park': 'US-9001', 'reason': 'trail: a copy of land already joined',
               'record': 'sgzzb1', 'state': 'ZZ'})
# same park, same reason, a second state — folds unless piece is set
copies.append({'park': 'US-9001', 'reason': 'compilation: a copy of land already joined',
               'record': 'sgxxa1', 'state': 'YY'})
# a second park, one row
copies.append({'park': 'US-9002', 'reason': 'county: the park\'s own page names Otter County; this land lies outside it',
               'record': 'sgyya1', 'state': 'YY'})
# a distinct piece in a third state keeps its own row
copies.append({'park': 'US-9002', 'reason': 'county: the park\'s own page names Otter County; this land lies outside it',
               'record': 'sgwwa1', 'state': 'WW', 'piece': 'WW-own-land'})

before = copy.deepcopy(copies)
collapsed = CR.collapse_check_rows(copies)
check('the input check rows are not modified', copies == before)
by = {(r['park'], r['reason'], r.get('piece')): r for r in collapsed}
a = by[('US-9001', 'compilation: a copy of land already joined', None)]
check('304 compilation copies plus one cross-state copy become one row with count 305 and the IDs kept',
      a['count'] == 305 and len(a['records']) == 305 and a['records'][0] == 'sgzza0'
      and a['records'][-1] == 'sgxxa1' and a['states'] == ['ZZ', 'YY'])
b = by[('US-9001', 'trail: a copy of land already joined', None)]
check('a second reason on the same park stays its own row', b['count'] == 1 and b['records'] == ['sgzzb1'])
c = by[('US-9002', 'county: the park\'s own page names Otter County; this land lies outside it', None)]
d = by[('US-9002', 'county: the park\'s own page names Otter County; this land lies outside it', 'WW-own-land')]
check('a second state\'s own piece of land (piece set) stays its own row',
      c['count'] == 1 and c['states'] == ['YY'] and d['count'] == 1 and d['states'] == ['WW'])
check('two invented parks with 308 raw rows collapse to four report rows',
      len(collapsed) == 4 and len(copies) == 308)

# Pre-sort: five buckets, counts add up, leftover not hidden
items = [
    {'park': 'US-9001', 'bucket': 'sure'},
    {'park': 'US-9002', 'bucket': 'needs a person'},
    {'park': 'US-9003', 'bucket': 'pin wrong'},
    {'park': 'US-9004', 'bucket': 'land wrong'},
    {'park': 'US-9005', 'bucket': 'needs a layer'},
    {'park': 'US-9006', 'bucket': 'needs a person'},
]
ps = CR.presort(items)
check('the five buckets are sure / needs a person / pin wrong / land wrong / needs a layer, in that order',
      list(ps['buckets']) == list(CR.BUCKETS))
check('bucket counts add up (2 + 1 + 1 + 1 + 1 = 6, leftover 0)',
      ps['counts'] == {'sure': 1, 'needs a person': 2, 'pin wrong': 1, 'land wrong': 1,
                       'needs a layer': 1, 'leftover': 0, 'all': 6})
ps2 = CR.presort(items + [{'park': 'US-9007', 'bucket': 'something-else'}])
check('an unknown bucket is leftover, not hidden',
      ps2['counts']['leftover'] == 1 and ps2['leftover'][0]['park'] == 'US-9007'
      and ps2['counts']['all'] == 7)

c_rows = [['sgzza1', 'Invented Marsh', 500, 'compilation: a copy of land already joined'] for _ in range(3)]
c_before = copy.deepcopy(c_rows)
report = CR.cleanup_report(
    [{'park': 'US-9001', 'reason': c_rows[0][3], 'record': 'sgzza1', 'state': 'ZZ'}] * 3,
    solver_verdicts={'US-9001': {'bucket': 'sure'}, 'US-9008': {'bucket': 'needs a person'}},
)
check('the report says key c rows were not rewritten, and a caller-held c list is unchanged',
      report['c_rows_rewritten'] is False and c_rows == c_before
      and report['input_count'] == 3 and report['collapsed_count'] == 1
      and report['counts']['sure'] == 1 and report['counts']['needs a person'] == 1)

check('the clean-up report is listed as not a rules file, and is in no RULE_FILES',
      'kpc_cleanup_report.py' in KF.NOT_RULES
      and not any('kpc_cleanup_report.py' in f for fs in KF.RULE_FILES.values() for f in fs))


# Reason class: numbers and units fold; a named county folds; a person-NO tail folds.
check('size: 15.01 times and size: 5.25 times are the same reason class',
      CR.reason_class('size: 15.01 times the agency\'s own figure')
      == CR.reason_class('size: 5.25 times the agency\'s own figure')
      != '')
check('county reasons that differ only by the county name are the same class',
      CR.reason_class("county: the park's own page names Otter County; this land lies outside it")
      == CR.reason_class("county: the park's own page names Bear County; this land lies outside it"))
check('a person-NO reason is one class even when the rest of the line differs',
      CR.reason_class('a person said no to this record: Invented Marsh Wildlife Area')
      == CR.reason_class('a person said no to this record: Invented Pond State Park'))
size_rows = [
    {'park': 'US-9003', 'reason': 'size: 15.01 times the agency\'s own figure', 'record': 'sgzza1', 'state': 'ZZ'},
    {'park': 'US-9003', 'reason': 'size: 5.25 times the agency\'s own figure', 'record': 'sgzza2', 'state': 'ZZ'},
]
sc = CR.collapse_check_rows(size_rows)
check('two size reasons with different numbers on the same park collapse to one row',
      len(sc) == 1 and sc[0]['count'] == 2 and set(sc[0]['records']) == {'sgzza1', 'sgzza2'})

# Command: read US-*.json c rows, write the report, do not rewrite the key
import json, tempfile
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    key = {
        'parks': {
            'US-9004': {'c': [
                ['sgzza1', 'Invented Marsh', 500, 'size: 15.01 times the agency\'s own figure'],
                ['sgzza2', 'Invented Marsh', 80, 'size: 5.25 times the agency\'s own figure'],
            ]}
        }
    }
    keys_dir = td / 'us-key'
    keys_dir.mkdir()
    (keys_dir / 'US-ZZ.json').write_text(json.dumps(key), encoding='utf-8')
    key_before = (keys_dir / 'US-ZZ.json').read_text(encoding='utf-8')
    out = td / 'collapsed.json'
    public, line = CR.write_collapsed_report(keys_dir, out)
    check('the command reports 2 rows collapsing to 1 by reason class, and does not rewrite the key',
          public['input_count'] == 2 and public['collapsed_count'] == 1
          and public['c_rows_rewritten'] is False
          and (keys_dir / 'US-ZZ.json').read_text(encoding='utf-8') == key_before
          and '2' in line and '1' in line and 'reason class' in line
          and out.is_file() and 'name' not in json.loads(out.read_text())['rows'][0])
    # hook text for REPORT.txt
check('the REPORT.txt hook line names the before and after row counts',
      '16,853' in CR.report_line({'input_count': 16853, 'collapsed_count': 2309, 'exact_reasons': 491, 'reason_classes': 70})
      and '2,309' in CR.report_line({'input_count': 16853, 'collapsed_count': 2309, 'exact_reasons': 491, 'reason_classes': 70}))

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
