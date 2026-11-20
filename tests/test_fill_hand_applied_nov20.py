"""20 Nov 2026 (Opus found it, Fable fixed it): the master step skipped a hand file whenever its fingerprint, or the fingerprint of
the download it was cut from, was in raw-manifest.json. One national download cut into a file per state carries the same raw
fingerprint in every piece, so the Army Corps recreation areas were skipped in 22 states whose saved copy held none of them
(measured on the real release files the same day: 35 hand files, 13 copies hold the layer, 22 do not, 2,696 areas never applied).
Now a hand file counts as applied only when the saved copy still holds rows of its layer. INVENTED files only in this test; the
count on the real files is in .claude/inbox/REPAIRS.md."""
import gzip, json, pathlib, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_master as M, kpc_master_fill as F  # noqa: E402

ok = True
def check(what, cond):
    global ok
    ok = ok and bool(cond); print(('PASS ' if cond else 'FAIL ') + what, flush=True)

def copy(d, area, ids):
    with gzip.open(d / f'{area}.json.gz', 'wt', encoding='utf-8') as f:
        json.dump({'st': area[3:], 'recs': [{'OBJECTID': i, 'Unit_Nm': 'x'} for i in ids]}, f)

with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t)
    copy(d, 'US-ZA', ['sgzaa1', 'sgzaa2', '77'])            # holds its own state layer, none of the national one
    copy(d, 'US-ZB', ['sgide5', 'sgzba1'])                  # holds the national layer
    applied = {'RAW-NATIONAL', 'FILE-ZB'}
    check('the helper reads a saved copy the way the fill step does (M.load_saved + M.prefix_counts)',
          M.prefix_counts(M.load_saved(d / 'US-ZB.json.gz')).get('sgide') == 1)
    check('a fingerprint that is not recorded is never "applied"', F.hand_already_applied('NEW', applied, d, 'US-ZA', 'sgide') is False)
    check('recorded, but the copy holds NO row of the layer: not applied (the 22-state fault)',
          F.hand_already_applied('RAW-NATIONAL', applied, d, 'US-ZA', 'sgide') is False)
    check('recorded and the copy holds the layer: applied, skipped as before', F.hand_already_applied('RAW-NATIONAL', applied, d, 'US-ZB', 'sgide') is True)
    check('the same raw fingerprint is judged state by state', [F.hand_already_applied('RAW-NATIONAL', applied, d, a, 'sgide') for a in ('US-ZA', 'US-ZB')] == [False, True])
    check('no cache folder given: the old answer stands (recorded = applied)', F.hand_already_applied('RAW-NATIONAL', applied, None, 'US-ZA', 'sgide') is True)
    check('no saved copy of that area: the old answer stands', F.hand_already_applied('RAW-NATIONAL', applied, d, 'US-ZC', 'sgide') is True)
    (d / 'US-ZD.json.gz').write_bytes(b'not a gzip file')
    check('an unreadable copy: the old answer stands (the copy is reported by the checks further down)', F.hand_already_applied('RAW-NATIONAL', applied, d, 'US-ZD', 'sgide') is True)
src = (ROOT / '.github/scripts/kpc_master_fill.py').read_text(encoding='utf-8')
check('both skips in fill() go through the new test', src.count('hand_already_applied(') == 3 and "in applied: continue" not in src)
import kpc_key_freeze as KF
check('kpc_master_fill.py is not a rule file of any key', not any('kpc_master_fill.py' in f for fs in KF.RULE_FILES.values() for f in fs))
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
