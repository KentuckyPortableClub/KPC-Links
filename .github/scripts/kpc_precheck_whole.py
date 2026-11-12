#!/usr/bin/env python3
"""Run kpc_precheck.py with every override read WHOLE (Nov 12 2026, KPC-Links #151 readers; KPC owner, 2026-11-12).

data/us-key/overrides.json is a manifest now: it keeps only the parks that have a 'no' list, and the parts list names the files
that hold the other parks. kpc_precheck.overrides() reads the file by name, so on its own it would see only the manifest's parks
and treat a join a person signed in a part file as unreviewed. kpc_precheck.py is not edited here on purpose: the per-area 2-fer
design hash counts it as 2-fer code (kpc_area_hash.CLOSURE_ADD), so an edit would make every 2-fer area due. This runner swaps in
a reader that follows the parts through kpc_overrides.load (a missing or bad part stops the pre-check red, never an empty set),
then does exactly what `python3 kpc_precheck.py [--apply-hold]` does. Not a rule file; decides no join.

  OUT=/tmp/kpc-precheck DATA=kpcdata python3 .github/scripts/kpc_precheck_whole.py [--apply-hold]
"""
import json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kpc_overrides  # noqa: E402
import kpc_precheck as PC  # noqa: E402


def overrides():
    """kpc_precheck.overrides(), the US and Canada overrides, each read whole (manifest + parts) or a loud error."""
    ov = {}
    for f in ('data/us-key/overrides.json', 'data/ca-key/overrides.json'):
        ov.update(kpc_overrides.load(f, missing_ok=True).get('parks') or {})
    return ov


PC.overrides = overrides

if __name__ == '__main__':
    try:
        PC.main()
        if '--apply-hold' in sys.argv: PC.apply_hold()
    except Exception as e:  # noqa: BLE001  (as kpc_precheck.py: a crash must not look like a clean run)
        print(f'::error title=Pre-check::stopped, the review pile is NOT complete: {type(e).__name__}: {str(e)[:200]}')
        try:
            PC.OUT.mkdir(parents=True, exist_ok=True)
            json.dump({'status': 'red', 'error': f'{type(e).__name__}: {str(e)[:300]}', 'made': time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}, open(PC.OUT / 'counts.json', 'w'), indent=1)
        except Exception: pass  # noqa: BLE001
        sys.exit(1)
    sys.exit(0)
