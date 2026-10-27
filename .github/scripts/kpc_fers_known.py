#!/usr/bin/env python3
"""KNOWN ANSWERS for the 2-fer bot (chat 2, Oct 27 2026; HQ 3:21 PM after chat 8 found the river-trail bug). Kentucky's hand-checked
river and trail pairs (ky-trail-parks.json: Lewis and Clark + Trail of Tears) must come out of the bot's Kentucky file before any
big run. REQUIRED = the river-bank pairs ('within 100 ft of the water') and the trail stretches inside a park; the Park Service
'lists this site' / auto-tour entries are sites, not stretches (chat 8): listed for information only.
Writes data/fers/known-answers.json {date, pass, required, found, missing: [[refs, what, why]]}. kpc_fers.py refuses an all-US/Canada
run unless 'pass' is true and the check is from the last 7 days. Never fails."""
import json, pathlib, re, sys, time
OUT = pathlib.Path('data/fers/known-answers.json')
LINES = set()
LIVE = ('candidate', 'very tight', 'water only', 'merged into')


def main():
    ky = json.load(open('data/fers/US-KY.json'))
    tp = json.load(open('ky-trail-parks.json'))
    rows = [(set(s.get('refs') or []), str(s.get('status', ''))) for s in ky.get('spots') or []]
    req, info = [], []
    LINES.update((tp.get(k) or {}).get('ref') for k in ('lewis', 'tears'))
    for key in ('lewis', 'tears'):
        t = tp.get(key) or {}
        for p in t.get('parks') or []:
            refs = sorted(set([t['ref']] + p['refs']))
            what = p.get('how') or ''
            (req if re.search(r'within 100 ft of the water|of (the )?(trail|route).*inside|mi of trail inside', what, re.I) else info).append((refs, what))
    seen, found, missing, notes = set(), 0, [], []
    for refs, what in req:
        k = tuple(refs)
        if k in seen: continue
        seen.add(k)
        hit = [st for rs, st in rows if set(refs) <= rs and st.startswith(LIVE)]
        # a 3-park entry also passes when each trail x park pair is there (e.g. Fort Donelson + Fort Heiman = same land, one shore)
        lines = [r for r in refs if r in LINES]; others = [r for r in refs if r not in LINES]
        pairs_ok = len(refs) > 2 and lines and all(any({l, o} <= rs and st.startswith(LIVE) for rs, st in rows) for l in lines for o in others)
        if hit or pairs_ok: found += 1; continue
        near = [st for rs, st in rows if set(refs) <= rs]
        missing.append([refs, what[:80], near[0][:120] if near else 'no row at all'])
    for refs, what in info:
        hit = [st for rs, st in rows if set(refs) <= rs and st.startswith(LIVE)]
        notes.append([refs, what[:80], 'shown' if hit else 'not a stretch on the line (site only)'])
    res = {'about': 'Known answers (kpc_fers_known.py): Kentucky\'s hand-checked river + trail pairs must come out before any big 2-fer run.',
           'date': time.strftime('%Y-%m-%d'), 'pass': not missing, 'required': len(seen), 'found': found, 'missing': missing, 'sites_info': notes}
    OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f"::notice title=2-fer known answers::{'PASS' if not missing else 'FAIL'}: {found} of {len(seen)} Kentucky river / trail pairs found"
          + ('; missing: ' + ' | '.join('+'.join(m[0]) + ' (' + m[2][:50] + ')' for m in missing[:12]) if missing else ''), flush=True)


if __name__ == '__main__':
    try: main()
    except Exception as e:  # noqa: BLE001
        print(f'::notice title=2-fer known answers::stopped: {e}', flush=True)
    sys.exit(0)
