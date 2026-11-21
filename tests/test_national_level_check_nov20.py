#!/usr/bin/env python3
"""Job 4 national-layer level check, invented parks only (KPC owner, 20 Nov 2026). The tool is
read-only: it flags a name-only national-layer join whose manager level disagrees with the park,
unless size_pick keeps it as a copy. A reviewed join still stands. No real park is named."""
import io, json, gzip, os, pathlib, sys, tempfile, zipfile, contextlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCR = ROOT / '.github' / 'scripts'
sys.path.insert(0, str(SCR))
import kpc_national_level_check as C  # noqa: E402
import kpc_key_freeze as KF  # noqa: E402

FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok:
        FAILS.append(what)


def write_key(folder, st, parks):
    p = pathlib.Path(folder) / f'US-{st}.json'
    p.write_text(json.dumps({'st': st, 'parks': parks}))
    return p


def write_cache(folder, st, recs):
    p = pathlib.Path(folder) / f'US-{st}.json.gz'
    with gzip.open(p, 'wt', encoding='utf-8') as fh:
        json.dump({'st': st, 'recs': recs}, fh)
    return p


def rec(oid, mang, acres=100, des='SP'):
    return {'OBJECTID': oid, 'Mang_Type': mang, 'Mang_Name': 'TEST', 'Des_Tp': des, 'GIS_Acres': acres, 'Unit_Nm': 'Invented Record'}


def park(name, typ, rows):
    return {'n': name, 't': typ, 'g': 'official', 'm': rows, 'ac': sum(r[2] for r in rows)}


def capture(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = C.main(argv)
    return rc, buf.getvalue()


# --- park and record level, name-alone, national id ---
check(C.park_level('Zed State Park') == 'STAT', 'a park named State ... is state level')
check(C.park_level('Zed National Wildlife Refuge') == 'FED', 'a park named National ... is federal level')
check(C.park_level('Zed NWR') == 'FED', 'a park named NWR is federal level')
check(C.park_level('BLM Zed Dunes') == 'FED', 'a park named BLM ... is federal level')
check(C.park_level('Zed Federal Wildlife Area') == 'FED', 'a park named Federal ... is federal level')
check(C.park_level('Zed Wildlife Area') is None, 'a park whose name names no level is unset')
check(C.park_level('Zed State National Test Grounds') == 'STAT', 'a state word wins when the name also has a national word')
check(C.is_national(4242) and C.is_national('4242') and C.is_national('fsod9') and C.is_national('fws12') and C.is_national('trl3'),
      'PAD-US ids and the 13 federal prefixes are national-layer records')
check(not C.is_national('sgzza1') and not C.is_national('arw4'), 'a state-layer prefix is not a national-layer record')
check(C.name_alone('name') and C.name_alone('name (second name field)') and C.name_alone('words'),
      'name and words joins are name-alone')
check(not C.name_alone('reviewed') and not C.name_alone('alias name (pin inside): Invented')
      and not C.name_alone('official trail line (agency)') and not C.name_alone('NPS unit code ABCD (POTA website nps.gov/abcd)'),
      'reviewed, alias, trail-line and unit-code joins are not name-alone')

# --- invented keys: one state file, one cache ---
with tempfile.TemporaryDirectory() as tmp:
    keys = pathlib.Path(tmp) / 'keys'
    cache = pathlib.Path(tmp) / 'cache'
    keys.mkdir(); cache.mkdir()
    # US-ZZ invented parks (refs are not real POTA numbers)
    parks = {
        'ZZ-1': park('Zed State Park', 'State Park', [
            [11, 'Zed State Park', 500, 'name'],          # STAT, the park's own size
            [12, 'Zed National Recreation Area', 300000, 'name'],  # FED, far bigger: to check
        ]),
        'ZZ-2': park('Zed State Fishing Lake', 'State Fishing Lake', [
            [21, 'Zed State Fishing Lake', 8000, 'name'],  # STAT
            [22, 'Zed BLM plot', 8000, 'name'],            # FED, same acres: a copy, counts
        ]),
        'ZZ-3': park('Zed National Wildlife Refuge', 'National Wildlife Refuge', [
            [31, 'Zed special use', 90000, 'name'],        # STAT on a national refuge: to check
        ]),
        'ZZ-4': park('Zed Wildlife Area', 'Wildlife Area', [
            [41, 'Zed federal tract', 1200, 'name'],       # FED, but the park names no level: no flag
        ]),
        'ZZ-5': park('Zed State Park East', 'State Park', [
            [51, 'Zed State Park East', 400, 'name'],      # STAT, levels match: no flag
        ]),
        'ZZ-6': park('Zed State Park West', 'State Park', [
            [61, 'Zed huge federal', 20000, 'reviewed'],   # FED, but a person's saved yes: still stands
        ]),
        'ZZ-7': park('Zed State Park South', 'State Park', [
            ['sgzza1', 'Zed state layer', 15000, 'name'],  # state-layer id, ignored even if STAT
        ]),
        'ZZ-8': park('Zed State National Test Grounds', 'National Test Grounds', [
            [81, 'Zed NPS unit', 889, 'name'],             # FED on a name where the state word wins: to check
        ]),
        'ZZ-9': park('Zed State Park North', 'State Park', [
            [91, 'Zed Corps rec', 7000, 'words'],          # FED, words join, not a copy of 5000: to check
            [92, 'Zed State Park North', 5000, 'name'],
        ]),
    }
    write_key(keys, 'ZZ', parks)
    write_cache(cache, 'ZZ', [
        rec(11, 'STAT', 500, 'SP'), rec(12, 'FED', 300000, 'REC'),
        rec(21, 'STAT', 8000, 'SCA'), rec(22, 'FED', 8000, 'RST'),
        rec(31, 'STAT', 90000, 'SCA'),
        rec(41, 'FED', 1200, 'REC'),
        rec(51, 'STAT', 400, 'SP'),
        rec(61, 'FED', 20000, 'REC'),
        rec('sgzza1', 'STAT', 15000, 'SP'),
        rec(81, 'FED', 889, 'HCA'),
        rec(91, 'FED', 7000, 'REC'), rec(92, 'STAT', 5000, 'SP'),
    ])
    attrs = C.load_attrs(cache)
    counts = C.scan_keys(keys, attrs)
    check(counts['national_records'] == 11, f"invented national-layer joins: {counts['national_records']} (11: all except the state-layer row)")
    check(counts['name_records'] == 10, f"invented name-alone joins: {counts['name_records']} (10: the reviewed one is out)")
    # flagged mismatches: ZZ-1 rec 12, ZZ-2 rec 22 (copy), ZZ-3 rec 31, ZZ-8 rec 81, ZZ-9 rec 91
    # ZZ-4 no level, ZZ-5 match, ZZ-6 reviewed, ZZ-7 not national
    check(counts['flag_records'] == 5 and counts['copy_records'] == 1 and counts['check_records'] == 4,
          f"invented flags {counts['flag_records']} of which 1 copy and {counts['check_records']} to check")
    check(counts['check_parks'] == 4 and counts['flag_parks'] == 5,
          f"invented check parks {counts['check_parks']} of {counts['flag_parks']} flagged")
    rc, out = capture(['--keys', str(keys), '--cache', str(cache)])
    check(rc == 0 and 'would go to check 4 records on 4 parks' in out, 'the command prints the invented check count')
    leaked = [tok for tok in ('Zed', 'ZZ-1', 'ZZ-2', 'ZZ-3', 'sgzza1') if tok in out]
    check(not leaked, 'the command prints no invented park name or number')

    # sample answers: wrong caught / right taken away, counts only
    ans = pathlib.Path(tmp) / 'answers.csv'
    ans.write_text(
        'ref,record,verdict\n'
        'ZZ-1,12,NO\n'       # wrong, to check: caught
        'ZZ-3,31,NO\n'       # wrong, to check: caught
        'ZZ-2,22,YES\n'      # right, but a copy so it still counts: not taken away
        'ZZ-5,51,YES\n'      # right, levels match: not taken away
        'ZZ-9,91,YES\n'      # right, to check: taken away
        'ZZ-4,41,YES\n'      # right, no level word so the rule says nothing: not taken away
        'ZZ-6,61,YES\n'      # right reviewed: not taken away
        'ZZ-8,81,NO\n'       # wrong, to check: caught
    )
    rc, out = capture(['--keys', str(keys), '--cache', str(cache), '--answers', str(ans)])
    check(rc == 0 and 'wrong records caught 3 of 3' in out and 'right records taken away 1 of 5' in out,
          f'sample counts on invented answers: {out.strip()!r}')
    leaked = [tok for tok in ('Zed', 'ZZ-1', 'ZZ-9', 'Invented') if tok in out]
    check(not leaked, 'the sample run prints no park name or number')

    # packet form: candidate letters + a key.json, also as a zip
    pkt = pathlib.Path(tmp) / 'packet'
    pkt.mkdir()
    (pkt / 'grader.csv').write_text('ref,candidate,verdict,source,note\nZZ-1,A,NO,packet: acres, \nZZ-5,B,YES,packet: acres,\n')
    (pkt / 'packet.key.json').write_text(json.dumps({
        'ZZ-1': {'cands': {'A': {'joined': True, 'ids': ['12']}, 'B': {'joined': False, 'ids': ['99']}}},
        'ZZ-5': {'cands': {'B': {'joined': True, 'ids': ['51']}}},
    }))
    rc, out = capture(['--keys', str(keys), '--cache', str(cache), '--answers', str(pkt)])
    check(rc == 0 and 'wrong records caught 1 of 1' in out and 'right records taken away 0 of 1' in out,
          f'packet answers with letters map to record ids: {out.strip()!r}')
    zpath = pathlib.Path(tmp) / 'answers.zip'
    with zipfile.ZipFile(zpath, 'w') as z:
        z.write(pkt / 'grader.csv', 'grader.csv')
        z.write(pkt / 'packet.key.json', 'packet.key.json')
    rc, out = capture(['--keys', str(keys), '--cache', str(cache), '--answers', str(zpath)])
    check(rc == 0 and 'wrong records caught 1 of 1' in out and 'right records taken away 0 of 1' in out,
          'a zip of the same packet prints the same counts')

# --- this tool is not a rule file: no rules hash moves ---
check('kpc_national_level_check.py' in KF.NOT_RULES,
      'kpc_national_level_check.py is on the NOT_RULES list')
check(not any(os.path.basename(f) == 'kpc_national_level_check.py' for fs in KF.RULE_FILES.values() for f in fs),
      'kpc_national_level_check.py is in no RULE_FILES list')
# the check itself is not in the hash: every rules hash on this tree is the one the newest changelog line names
# (a later approved hash move updates the changelog, not this test)
import kpc_preflight as _PF  # noqa: E402
for _k in ('us-key', 'ca-key', 'world-key', 'fers'):
    check(KF.rules_hash(_k) == _PF.newest_hash(_k), f"{_k} rules hash is the newest changelog hash {_PF.newest_hash(_k)} (got {KF.rules_hash(_k)})")

print('ALL PASS' if not FAILS else 'SOME FAILED')
sys.exit(0 if not FAILS else 1)
