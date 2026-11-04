#!/usr/bin/env python3
"""Offline test for .github/scripts/kpc_key_dropped.py (links-07, Nov 4 2026; per Brandon via Super Head Bot (relayed), 6:05 AM CST
Nov 4). A tiny git repo with two 'US answer key' builds; links-01's kpc_key_postcheck.py writes its report, then kpc_key_dropped.py
writes the dropped lists. Checks: one CSV per reason (header-only when empty) + no-boundary.csv + index.json; every reason the key
code uses lands in its own list; the first reason wins and all_reasons keeps the rest; each row carries the POTA name + pin, area,
official site, best candidate (name, id, layer, acres, kind, why, distance when the key says it), the pre-check's distance and kind
joined by ref (6:49 AM CST Nov 4 ask, relayed via Super Head Bot; blank + pre_blank_reason when it has none, is missing or is older
than the build), the flags and past person answers
(overrides, a person's signed sheet NO, NEEDS_RESEARCH); a multi-state park is one row per file; new this build; the .md count table
(once, even on a re-run); no per-park notices; a sudden jump / a whole area going to pins warns; never fails (exit 0); links-01's
report json is not changed; nothing outside the report folder is written."""
import csv, json, os, pathlib, re, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent.parent
PCK = HERE / '.github/scripts/kpc_key_postcheck.py'
TOOL = HERE / '.github/scripts/kpc_key_dropped.py'
sys.path.insert(0, str(HERE / '.github/scripts'))
import kpc_key_dropped as KD  # noqa: E402
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


def sh(root, *a): return subprocess.run(list(a), cwd=root, capture_output=True, text=True)
def wj(p, d): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(d, ensure_ascii=False))


def run(root, tool, **env):
    e = dict(os.environ, **{'KEY': 'us', 'OUT_DIR': 'out', 'ANSWER_SHEET': str(root / 'sheet'), 'PRECHECK_OUT': str(root / 'pre'), 'KPC_PERSONS': 'Brandon,KZ4CP', **env})
    for k in ('FORCE', 'KPC_DROP_JUMP_MIN', 'KPC_DROP_JUMP_PCT', 'WORKFLOW_NAME'):
        if k not in env: e.pop(k, None)
    return subprocess.run([sys.executable, '-B', str(tool)], cwd=root, env=e, capture_output=True, text=True)


def rows(base, f): return list(csv.DictReader(open(base / f, encoding='utf-8')))


OUTL = lambda i, nm: [[i, nm, 100, 'name']]   # noqa: E731
old_xx = {'US-0001': {'n': 'Alpha State Park', 'g': 'official', 'm': OUTL('1', 'Alpha State Park')},
          'US-0002': {'n': 'Bravo State Park', 'g': 'pin', 'm': [], 'c': [['sgxx2', 'Bravo Lake State Park', 40, 'similar name']]},
          'US-0012': {'n': 'Lima WMA', 'g': 'official', 'm': OUTL('12', 'Lima WMA')}}
new_xx = {
    'US-0001': {'n': 'Alpha State Park', 'g': 'official', 'm': OUTL('1', 'Alpha State Park')},
    'US-0002': {'n': 'Bravo State Park', 'g': 'pin', 'm': [], 'c': [['sgxx2', 'Bravo Lake State Park', 40, 'similar name']]},
    'US-0003': {'n': 'Charlie Wild and Scenic River', 'g': 'pin', 'm': [], 'c': [['33', 'Charlie River Conservation Area', 15, 'same name, different kind of place']]},
    'US-0004': {'n': 'Delta WMA', 'g': 'pin', 'm': [], 'c': [['arw4', 'Delta WMA', 0, 'same name far from the pin, no join at the pin (Nov 1: check, never an outline)']]},
    'US-0005': {'n': 'Echo State Forest', 'g': 'pin', 'm': [], 'c': [['55', 'Echo State Forest', 900, 'held (rule G-1): a similar-name piece more than 2 km from the pin and from every passed piece']]},
    'US-0006': {'n': 'Foxtrot State Park', 'g': 'pin', 'm': [], 'c': [['66', 'Foxtrot Park', 10, 'similar name']]},
    'US-0007': {'n': 'Golf Preserve', 'g': 'pin', 'm': []},
    'US-0008': {'n': 'Hotel Natural Area', 'g': 'pin', 'm': [], 'a': [['88', 'Big National Forest', 500000, 'the POTA pin is inside it (different name)']]},
    'US-0009': {'n': 'India Fishing Lake', 'g': 'pin', 'm': []},
    'US-0010': {'n': 'Juliet Historic Site', 'g': 'pin', 'm': [], 'joined_in': ['US-YY']},
    'US-0011': {'n': 'Kilo National Forest', 'g': 'pin', 'm': []},
    'US-0012': {'n': 'Lima WMA', 'g': 'pin', 'm': []},
    'US-0013': {'n': 'Mike State Park', 'g': 'pin', 'm': []},
    'US-0014': {'n': 'November Lake', 'g': 'pin', 'm': []},
    'US-0015': {'n': 'Oscar Wildlife Area', 'g': 'pin', 'm': []},
    'US-0016': {'n': 'Papa Trail', 'g': 'official', 'line': 1, 'm': [['trl16', 'Papa Trail', 0, 'official trail line']]},
}
yy = {'US-0011': {'n': 'Kilo National Forest', 'g': 'official', 'm': OUTL('11', 'Kilo National Forest')}}
pins = {r: (p['n'], 37.0, -85.0) for r, p in new_xx.items()}
pins['US-0007'] = ('Golf Preserve', 0, 0)

with tempfile.TemporaryDirectory() as t:
    R = pathlib.Path(t)
    sh(R, 'git', 'init', '-q'); sh(R, 'git', 'config', 'user.email', 't@t'); sh(R, 'git', 'config', 'user.name', 't')
    wj(R / 'locations.json', {'rows': [['POTA', r, n, la, lo] for r, (n, la, lo) in pins.items()]})
    wj(R / 'data/us-key/US-XX.json', {'parks': old_xx}); wj(R / 'data/us-key/US-YY.json', {'parks': yy})
    wj(R / 'data/us-key/index.json', {'build': 'US-100', 'built': '2026-11-03 10:00 UTC'})
    sh(R, 'git', 'add', '-A'); sh(R, 'git', 'commit', '-qm', 'US answer key')
    wj(R / 'data/us-key/US-XX.json', {'parks': new_xx})
    wj(R / 'data/us-key/index.json', {'build': 'US-200', 'built': '2026-11-04 10:00 UTC'})
    wj(R / 'data/us-key/overrides.json', {'parks': {'US-0006': {'no': ['66'], 'when': '2026-11-02', 'why': 'Nov 2: Brandon NO on 66'}}})
    wj(R / 'data/us-key/layers.json', {'sgxx': ['https://example.gov/q', 'NAME', 'Example state lands (official)'], 'arw': ['u', 'f', 'Arkansas WMAs']})
    wj(R / 'data/us-key/why-not.json', {'parks': {'US-0015': {'st': 'XX', 'tag': 'private'}, 'US-0009': {'st': 'XX', 'tag': 'no-layer'}}})
    wj(R / 'data/parkinfo-web.json', {'parks': {'US-0009': {'web': 'https://wildlife.example.gov/india-lake'}}})
    sh(R, 'git', 'add', '-A'); sh(R, 'git', 'commit', '-qm', 'US answer key')
    (R / 'sheet').mkdir(); (R / 'pre').mkdir()
    cols = ['ref', 'pota_name', 'area', 'key_id', 'record_name', 'status', 'approved_by', 'approved_date', 'note']
    with open(R / 'sheet/US.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader()
        w.writerow({'ref': 'US-0013', 'key_id': '13', 'record_name': 'Mike Park', 'status': 'NO', 'approved_by': 'Brandon', 'approved_date': '2026-11-03'})
        w.writerow({'ref': 'US-0014', 'key_id': '14', 'record_name': 'November Lake', 'status': 'NO', 'approved_by': 'Quality', 'approved_date': '2026-11-03'})
        # FINAL-v2 self-check (person-answer rule): Brandon's sign-offs before the 9:37 AM CST Nov 2 restart never count
        w.writerow({'ref': 'US-0014', 'key_id': '14', 'record_name': 'November Lake', 'status': 'NO', 'approved_by': 'Brandon', 'approved_date': '2026-11-01'})
        w.writerow({'ref': 'US-0014', 'key_id': '14', 'record_name': 'November Lake', 'status': 'PIN', 'approved_by': 'Brandon', 'approved_date': '2026-11-02'})
        w.writerow({'ref': 'US-0009', 'key_id': '', 'record_name': '', 'status': 'PROPOSED', 'note': 'NEEDS_RESEARCH: find the official record'})
    with open(R / 'pre/review-pile.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh); w.writerow(['park', 'area', 'name', 'flags', 'why', 'action'])
        w.writerow(['US-0014', 'US-XX', 'November Lake', 'RULE18', 'rule 18: North / South piece', 'HOLD'])
    with open(R / 'pre/BAD_POTA_PIN_FLAGS.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh); w.writerow(['park', 'area', 'flag']); w.writerow(['US-0007', 'US-XX', 'BAD_POTA_PIN_NO_OUTLINE'])
    H = ['park', 'area', 'name', 'type', 'outline', 'check', 'flags', 'why', 'joined ids', 'pota_lat', 'pota_lon']   # kpc_precheck.py scorecard.csv
    with open(R / 'pre/scorecard.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh); w.writerow(H)
        w.writerow(['US-0003', 'US-XX', 'Charlie Wild and Scenic River', 'Wild and Scenic River', 'pin', 'full', 'WRONG_KIND NO_OFFICIAL_BOUNDARY',
                    'layer kind: Charlie River Conservation Area is another kind of place than a Wild and Scenic River | no official boundary', '33', '37.0', '-85.0'])
        w.writerow(['US-0004', 'US-XX', 'Delta WMA', '', 'pin', 'full', 'PIN_WAY_OUT', 'the POTA pin is well outside the joined land', '', '37.0', '-85.0'])
        w.writerow(['US-0005', 'US-XX', 'Echo State Forest', '', 'pin', 'full', 'NO_OFFICIAL_BOUNDARY', 'no official boundary', '', '37.0', '-85.0'])
        w.writerow(['US-0002', 'US-XX', 'Bravo State Park', '', 'pin', 'full', 'NO_OFFICIAL_BOUNDARY', 'no official boundary', '', '37.0', '-85.0'])
    with open(R / 'pre/county.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh); w.writerow(['park', 'area', 'name', 'county check', 'WWFF listed counties', 'pin is in', 'km to listed', 'reading', 'check'])
        w.writerow(['US-0005', 'US-XX', 'Echo State Forest', 'pin outside listed', 'Adair', 'Green', '3.4', 'near', 'full'])
    keyfiles = {p: p.read_bytes() for p in (R / 'data').rglob('*') if p.is_file()}

    p1 = run(R, PCK)
    check(p1.returncode == 0 and (R / 'out/last-us.json').exists(), 'links-01 post-key check wrote its report')
    rep_f = R / 'out' / json.load(open(R / 'out/last-us.json'))['report']
    rep_before = rep_f.read_bytes()
    p2 = run(R, TOOL)
    check(p2.returncode == 0, f'exit 0: {p2.stderr[-300:]}')
    D = R / 'out/us-US-200/dropped'
    names = sorted(x.name for x in D.iterdir()) if D.exists() else []
    want = sorted([c.replace('_', '-') + '.csv' for c, _ in KD.REASONS] + ['no-boundary.csv', 'index.json'])
    check(names == want, f'one CSV per reason + no-boundary.csv + index.json under <key>-<build>/dropped/: {names}')
    hdr = next(csv.reader(open(D / 'wrong-kind.csv'))) if D.exists() else []
    check(hdr == KD.COLUMNS and open(D / 'pota-bad-pin.csv').read().count('\n') == 2, 'every CSV has the same columns; header-only file when a reason has none (here 1 row)')
    I = json.load(open(D / 'index.json'))
    by = {c: [x['ref'] for x in rows(D, f)] for c, f in I['files'].items()}
    exp = {'joined_in_other_area': ['US-0010', 'US-0011'], 'pota_bad_pin': ['US-0007'], 'override_no': ['US-0006', 'US-0013'], 'rule18_doubt': ['US-0005', 'US-0014'],
           'pin_too_far': ['US-0004'], 'wrong_kind': ['US-0003'], 'name_mismatch': ['US-0002'], 'inside_other_land': ['US-0008'],
           'private_or_picture_map': ['US-0015'], 'no_boundary': ['US-0009', 'US-0012']}
    for c, v in exp.items(): check(by.get(c) == v, f'{c}: {v} (got {by.get(c)})')
    check(I['counts'] == {c: len(v) for c, v in exp.items()} and I['total'] == 14, f"index counts + total 14 (the trail line and the outlines are not drops): {I['counts']} {I['total']}")
    allr = {x['ref']: x for f in I['files'].values() for x in rows(D, f)}
    x = allr['US-0006']
    check(x['all_reasons'] == 'override_no;name_mismatch' and '66' in x['detail'] and 'Brandon NO on 66' in x['override'], f"first reason wins, all_reasons keeps the rest, override shown: {x['all_reasons']} | {x['override']}")
    x = allr['US-0013']
    check(x['reason'] == 'override_no' and x['person_answer'] == 'yes' and 'NO Mike Park (13) by Brandon 2026-11-03' in x['sheet_answer'], f"a person's signed sheet NO counts as a person's no: {x['sheet_answer']}")
    x = allr['US-0014']
    check(x['reason'] == 'rule18_doubt' and x['rule18_flag'] == 'yes' and x['person_answer'] == '' and 'HOLD RULE18' in x['precheck_flags'], f"a Quality NO is shown but is not a person's answer; pre-check HOLD RULE18 = doubt: {x['precheck_flags']}")
    check(all(KD.after_restart(d) == want for d, want in (('2026-11-02', False), ('2026-11-01', False), ('2026-11-02 15:36 UTC', False),
                                                         ('2026-11-02 15:37 UTC', True), ('2026-11-02 09:37 CST', True), ('2026-11-02 09:36 CST', False),
                                                         ('2026-11-03', True), ('', False), ('soon', False))),
          'after_restart(): a bare Nov 2 date and anything before 9:37 AM CST Nov 2 is before the restart')
    x = allr['US-0002']
    check((x['pota_name'], x['pota_lat'], x['pota_lon'], x['area'], x['pota_kind']) == ('Bravo State Park', '37.0', '-85.0', 'US-XX', ''), 'POTA name + POTA pin + area on the row')
    check((x['cand_name'], x['cand_id'], x['cand_layer'], x['cand_acres'], x['cand_kind'], x['cand_why']) == ('Bravo Lake State Park', 'sgxx2', 'sgxx: Example state lands (official)', '40', 'state park', 'similar name'),
          f"best candidate: name, record id, layer (layers.json), acres, kind, why: {x['cand_layer']} {x['cand_kind']}")
    check(allr['US-0005']['cand_distance_km'] == '>2' and allr['US-0004']['cand_distance_km'] == '', 'distance only when the key says it (">2" km), blank otherwise')
    pj = {r: {c: allr[r][c] for c in KD.PRE_COLS} for r in ('US-0002', 'US-0003', 'US-0004', 'US-0005', 'US-0009')}
    check(pj['US-0003']['pre_kind'] == 'wrong kind' and pj['US-0003']['pre_kind_why'].startswith('layer kind: Charlie River Conservation Area')
          and 'distance: the pre-check row has no distance' in pj['US-0003']['pre_blank_reason'], f"kind joined by ref from the pre-check WRONG_KIND row (its layer-kind reason): {pj['US-0003']}")
    check(pj['US-0005']['pre_km'] == '3.4' and 'WWFF-listed county' in pj['US-0005']['pre_km_what'] and 'kind:' in pj['US-0005']['pre_blank_reason'],
          f"distance joined by ref from the pre-check county check (km to listed): {pj['US-0005']}")
    check(pj['US-0004']['pre_km'] == '' and 'PIN_WAY_OUT' in pj['US-0004']['pre_km_what'] and 'keeps no km for PIN_WAY_OUT' in pj['US-0004']['pre_blank_reason'],
          f"PIN_WAY_OUT has no km: blank, with the reason: {pj['US-0004']}")
    check(pj['US-0002']['pre_km'] == pj['US-0002']['pre_kind'] == '' and pj['US-0002']['pre_blank_reason'].count(';') == 1, f"a pre-check row with neither: both blank, both reasons: {pj['US-0002']}")
    check(pj['US-0009'] == {'pre_km': '', 'pre_km_what': '', 'pre_kind': '', 'pre_kind_why': '', 'pre_blank_reason': 'no precheck row'}, "no pre-check row for the ref: blank, 'no precheck row'")
    check(all(allr[r]['pre_blank_reason'] for r in allr if not (allr[r]['pre_km'] and allr[r]['pre_kind'])), 'every row with a blank pre-check cell has a pre_blank_reason')
    check(I['precheck_join'] == {'state': 'used', 'rows': 14, 'rows_with_km': 1, 'rows_with_kind': 1, 'blank_reasons': I['precheck_join']['blank_reasons']}
          and I['precheck_join']['blank_reasons'].get('no precheck row') == 10, f"index.json counts the join: {I['precheck_join']}")
    check(allr['US-0003']['cand_kind'] == KD.kind_of('Charlie River Conservation Area') != 'wrong kind' and allr['US-0005']['cand_distance_km'] == '>2',
          "the key's own cand_kind / cand_distance_km are kept as they were (the pre-check values go in their own columns)")
    pc = {'c': [['91', 'Clear Creek Serpentine', 50, 'similar name'], ['92', 'Clear Creek', 70, 'same name far from the pin, no join at the pin']]}
    b1, m1 = KD.best_cand(pc, 'us', {}, 'Clear Creek (92): same name far from the pin, no join at the pin')
    b2, _ = KD.best_cand(pc, 'us', {}, 'no record named')
    check(b1['cand_id'] == '92' and m1 == 1 and b2['cand_id'] == '91', f"best candidate = the record the main reason names, else the builders' first: {b1['cand_id']} {b2['cand_id']}")
    check(allr['US-0003']['cand_layer'] == 'PAD-US' and allr['US-0004']['cand_layer'] == 'arw: Arkansas WMAs', 'a plain number = PAD-US; a layers.json prefix = that layer')
    x = allr['US-0009']
    check(x['official_site'] == 'https://wildlife.example.gov/india-lake' and 'NEEDS_RESEARCH' in x['needs_research'] and x['why_not_tag'] == 'no-layer', f"official site, NEEDS_RESEARCH row, why-not tag: {x['needs_research']}")
    x = allr['US-0007']
    check(x['bad_pin_flag'] == 'BAD_POTA_PIN_NO_OUTLINE' and '0,0' in x['detail'] and x['pota_lat'] == '0', "0,0 pin: POTA's own pin kept on the row (never moved), flag shown")
    check('US-YY' in allr['US-0011']['detail'] and allr['US-0011']['area'] == 'US-XX', 'a multi-state park with an outline in another state file = joined_in_other_area, one row per file')
    check(allr['US-0012']['new_this_build'] == 'yes' and allr['US-0012']['before'] == 'outline' and allr['US-0002']['new_this_build'] == 'no' and allr['US-0009']['before'] == 'absent' and I['new_this_build']['no_boundary'] == 2,
          'new this build: outline before -> pin now, or a new park that came in as a pin (an old pin is not new)')
    check(all(v['build'] == 'US-200' and v['checked'] for v in allr.values()), 'build id + date checked on every row')
    md = (R / 'out/us-US-200.md').read_text()
    check('## Dropped parks' in md and '| pin too far (`pin_too_far`) | 1 | 1 |' in md and '| **total** | **14** | **13** |' in md, 'count table added to the .md report')
    notes = [ln for ln in p2.stdout.splitlines() if ln.startswith('::')]
    check(len(notes) == 1 and notes[0].startswith('::notice'), f'no per-park notices: one summary notice ({len(notes)})')
    check(rep_f.read_bytes() == rep_before, "links-01's report json is not changed (the gate reads its summary)")
    p3 = run(R, TOOL)
    check(p3.returncode == 0 and 'already written' in p3.stdout, 'a re-run on the same report writes nothing')
    p4 = run(R, TOOL, FORCE='yes')
    check(p4.returncode == 0 and (R / 'out/us-US-200.md').read_text().count('## Dropped parks') == 1, 'FORCE re-run: the .md table is replaced, not added twice')
    check({p: p.read_bytes() for p in (R / 'data').rglob('*') if p.is_file()} == keyfiles, 'no key file / POTA pin / data file is changed')
    check(sorted(str(p.relative_to(R)) for p in (R / 'out').iterdir()) == ['out/last-us.json', 'out/us-US-200', 'out/us-US-200.json', 'out/us-US-200.md'], 'only the report folder is written')
    p5 = run(R, TOOL, FORCE='yes', KPC_DROP_JUMP_MIN='0', KPC_DROP_JUMP_PCT='1')
    w = [ln for ln in p5.stdout.splitlines() if ln.startswith('::warning')]
    check(len(w) == 1 and 'sudden jump' in w[0] and json.load(open(D / 'index.json'))['jump_check']['new_drops'] == 1, f'a sudden jump in drops warns once (a system problem): {w}')
    os.utime(R / 'pre/scorecard.csv', (1762000000, 1762000000))   # Nov 1 2025: older than the build's 'built' (2026-11-04 10:00 UTC)
    run(R, TOOL, FORCE='yes')
    st = [x['pre_blank_reason'] for f in json.load(open(D / 'index.json'))['files'].values() for x in rows(D, f)]
    check(set(st) == {'precheck older than build'} and json.load(open(D / 'index.json'))['precheck_join']['state'] == 'precheck older than build'
          and not any(x['pre_kind'] for f in json.load(open(D / 'index.json'))['files'].values() for x in rows(D, f)), "a stale pre-check (older than the build) is not used: blank, 'precheck older than build'")
    (R / 'pre/scorecard.csv').rename(R / 'pre/scorecard.off')
    run(R, TOOL, FORCE='yes')
    st = [x['pre_blank_reason'] for f in json.load(open(D / 'index.json'))['files'].values() for x in rows(D, f)]
    check(set(st) == {'no precheck output'} and json.load(open(D / 'index.json'))['precheck_join']['state'] == 'no precheck output', "no pre-check output: blank, 'no precheck output'")
    (R / 'pre/scorecard.off').rename(R / 'pre/scorecard.csv'); os.utime(R / 'pre/scorecard.csv'); run(R, TOOL, FORCE='yes', KPC_DROP_JUMP_MIN='0', KPC_DROP_JUMP_PCT='1')
    check(KD.built_ts('2026-11-04 10:00 UTC') == 1793786400 and KD.built_ts('2026-11-04T10:00:00Z') == 1793786400 and KD.built_ts('') is None, 'built_ts reads the build stamp (UTC)')
    check('Pre-check join by ref (used): distance (pre_km) on 1 and kind (pre_kind) on 1 of 14 rows' in (R / 'out/us-US-200.md').read_text(), 'the .md says how many rows the join filled')
    check(json.load(open(D / 'index.json'))['system_warnings'] and '**System check:**' in (R / 'out/us-US-200.md').read_text(), 'the warning is in the index and the .md')

# a whole area going to pins; no report; a broken input never fails
with tempfile.TemporaryDirectory() as t:
    R = pathlib.Path(t)
    sh(R, 'git', 'init', '-q'); sh(R, 'git', 'config', 'user.email', 't@t'); sh(R, 'git', 'config', 'user.name', 't')
    p0 = run(R, TOOL)
    check(p0.returncode == 0 and 'no post-key report yet' in p0.stdout, 'no report yet: a notice, exit 0')
    A = {f'US-{i:04d}': {'n': f'Park {i} State Park', 'g': 'official', 'm': OUTL(str(i), f'Park {i} State Park')} for i in range(12)}
    wj(R / 'data/us-key/US-ZZ.json', {'parks': A}); wj(R / 'data/us-key/index.json', {'build': 'US-1'})
    sh(R, 'git', 'add', '-A'); sh(R, 'git', 'commit', '-qm', 'US answer key')
    wj(R / 'data/us-key/US-ZZ.json', {'parks': {r: {'n': p['n'], 'g': 'pin', 'm': []} for r, p in A.items()}}); wj(R / 'data/us-key/index.json', {'build': 'US-2'})
    sh(R, 'git', 'add', '-A'); sh(R, 'git', 'commit', '-qm', 'US answer key')
    run(R, PCK); p = run(R, TOOL)
    w = [ln for ln in p.stdout.splitlines() if ln.startswith('::warning')]
    check(p.returncode == 0 and any('US-ZZ: every park is a pin now' in x for x in w), f'a whole area going to pins warns: {w}')
    (R / 'out/last-us.json').write_text('{"report": "us-US-2.json"}'); (R / 'out/us-US-2.json').write_text('not json')
    p = run(R, TOOL)
    check(p.returncode == 0, 'a broken report never fails (exit 0)')
    p = run(R, TOOL, KEY='', WORKFLOW_NAME='KPC US answer key', FORCE='yes')
    check(p.returncode == 0, 'WORKFLOW_NAME picks the key like links-01')

# the workflow step
Y = (HERE / '.github/workflows/kpc-key-postcheck.yml').read_text()
i1, i2 = Y.find('kpc_key_postcheck.py\n'), Y.find('run: python3 .github/scripts/kpc_key_dropped.py')
step = Y[Y.rfind('- name:', 0, i2):i2]
check(0 < i1 < i2 < Y.find('- name: Save the report'), 'the dropped step runs after the compare step and before the one save (data/status/key-check)')
check('continue-on-error: true' in step and 'ANSWER_SHEET: kpcdata/data/answer-sheet' in step and 'PRECHECK_OUT: /tmp/kpc-precheck' in step and 'per Brandon via Super Head Bot (relayed), 6:05 AM CST Nov 4' in step,
      'the step never fails a run, reads the same inputs, carries the provenance')
check(not re.search(r'^\s*schedule:|cron:', Y, re.M), 'no schedule / no cron')
src = TOOL.read_text()
check(not re.search(r'urlopen|requests\.|http\.client|socket', src) and 'os.remove' not in src and 'unlink' not in src, 'no web request, no deletion')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
