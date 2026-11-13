#!/usr/bin/env python3
"""Offline: W-AU baseline is the current-layer count of the saved copy (365,915 minus the eight
#135 dropped layers = 65,838). The gate counts only layers the key still reads, so it passes."""
import json, sys, pathlib, tempfile, gzip

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_master as M  # noqa: E402
import kpc_world_hand as WH  # noqa: E402

ok = True
def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)

DROPPED = {
    'Surface_HydroLines_National': 276000,
    'Protected Areas (CAPAD)': 14492,
    'Walking track': 5992,
    'Beach Names': 1035,
    'Beach Presence': 818,
    'Forest Blocks (DBCA-025)': 772,
    'Great walk': 716,
    'Beach': 252,
}
check('eight dropped layers add up to 300,077', sum(DROPPED.values()) == 300077)
check('365,915 - 300,077 = 65,838', 365915 - 300077 == 65838)

exp = (json.loads((ROOT / 'data/outlines/layers.json').read_text()).get('caches') or {}).get('W-AU') or {}
check('layers.json caches.W-AU expected_count is 65,838', exp.get('expected_count') == 65838)

labs = set(WH.world_source_labels('AU', ROOT))
check('the world key currently reads 19 AU sources (built-in + extra, including the QLD split rest, minus dropped)',
      len(labs) == 19 and 'CAPAD (DCCEEW)' in labs and 'QLD State Forest (Queensland Government)' in labs
      and 'Protected areas and forests of Queensland' in labs
      and 'Surface_HydroLines_National' not in labs and 'Protected Areas (CAPAD)' not in labs)

# a tiny copy with mixed current + dropped labels
recs = ([{'src': 'CAPAD (DCCEEW)', 'n': f'c{i}'} for i in range(10)]
        + [{'src': 'Surface_HydroLines_National', 'n': f'h{i}'} for i in range(50)]
        + [{'src': 'Protected areas and forests of Queensland', 'n': f'q{i}'} for i in range(5)])
blob = {'cc': 'AU', 'recs': recs}
check('world_current_rec_count ignores dropped hydro and keeps CAPAD + QLD rest (15)',
      WH.world_current_rec_count('W-AU.json.gz', blob, ROOT) == 15)
check('a US copy is still counted in full', WH.world_current_rec_count('US-KY.json.gz', {'recs': recs}, ROOT) == 65)

# The short-read gate in kpc_master.check_saved_cache is unchanged (that module is a READER
# input of every area hash). Current-layer counting lives in kpc_world_hand and is used by
# the CLI gate and save-check, so a refresh that drops hydro can upload.
got = WH.world_current_rec_count('W-AU.json.gz', blob, ROOT)
try:
    M.check_complete(15, got, 'W-AU')
    check('CLI-style current-layer gate on a complete W-AU copy passes (15 of 15)', True)
except M.ShortRead:
    check('CLI-style current-layer gate on a complete W-AU copy passes (15 of 15)', False)
try:
    M.check_complete(16, got, 'W-AU')
    check('a short current-layer count raises ShortRead', False)
except M.ShortRead:
    check('a short current-layer count raises ShortRead', True)
# padding: the unfiltered rec list would hide a short current-layer count
check('the unfiltered rec list is 65 and would hide a shortfall against 16; current-layer count does not',
      len(recs) == 65 and got == 15)

holds = json.loads((ROOT / 'data/outlines/world-expected-holds.approved.json').read_text())
check('AU and MT are off the expected-holds list', not (holds.get('holds') or {}))

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
