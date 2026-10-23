#!/usr/bin/env python3
"""The list of parks POTA has RETIRED anywhere (Opus, Oct 23 2026): data/retired-refs.json.

Brandon Oct 23: 'if France removes 10 parks … would it be easier on the boundary bot just to add a note to the card that
the park is retired until the monthly update?' Yes: the nightly pin bots (US search list, Canada pins, world pins) take a
retired park's PIN off the map the same night and write it here; the tools read this file and say 'Retired by POTA' on
the park's card (a saved trip, a link, a typed number, Am I in the Park). The heavy outline lists (data/us-key,
ca-key, world-key) are left alone and drop it at their monthly rebuild. Kentucky retirements also go to
data/ky-retired.json, which takes them off every Kentucky list at once (kpc_retired_sweep.py).

  {"updated": "...", "refs": {"FR-1234": {"n": "name", "d": "2026-10-23", "src": "world"}}}
A park that is back on POTA's list is taken out again. Entries are kept a year."""
import datetime
import json
import pathlib

F = pathlib.Path('data/retired-refs.json')
NOTE = ("Parks POTA has taken off its list, noticed by the nightly pin bots. The tools show 'Retired by POTA' on these "
        "cards; the monthly outline rebuild drops them for good. See .github/scripts/kpc_retired_refs.py.")


def record(gone, present, src, today=None):
    """gone = {ref: name} that left POTA's list tonight; present = every ref on the list tonight for this source.
    Returns (added, back) lists."""
    today = today or datetime.date.today().isoformat()
    try:
        d = json.loads(F.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        d = {'refs': {}}
    R = d.setdefault('refs', {})
    back = sorted(r for r in R if r in present)
    for r in back:
        R.pop(r, None)
    added = sorted(r for r in gone if r not in R and r not in present)
    for r in added:
        R[r] = {'n': gone[r] or '', 'd': today, 'src': src}
    cut = (datetime.date.fromisoformat(today) - datetime.timedelta(days=365)).isoformat()
    for r in [r for r, v in R.items() if v.get('d', today) < cut]:
        R.pop(r, None)
    if added or back or not F.exists():
        d['note'] = NOTE
        d['updated'] = today
        d['refs'] = dict(sorted(R.items()))
        F.parent.mkdir(parents=True, exist_ok=True)
        F.write_text(json.dumps(d, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    if added or back:
        print(f'::notice title=Retired parks ({src})::retired tonight: {", ".join(added[:30]) or "none"}; back on the list: {", ".join(back[:30]) or "none"}', flush=True)
    return added, back
