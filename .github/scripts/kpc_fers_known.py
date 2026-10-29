#!/usr/bin/env python3
"""KNOWN ANSWERS for the 2-fer bot (chat 2, Oct 27 2026; HQ 3:21 PM after chat 8 found the river-trail bug). Kentucky's hand-checked
river and trail pairs (ky-trail-parks.json: Lewis and Clark + Trail of Tears) must come out of the bot's Kentucky file before any
big run. REQUIRED = the river-bank pairs ('within 100 ft of the water') and the trail stretches inside a park; the Park Service
'lists this site' / auto-tour entries are sites, not stretches (chat 8): listed for information only.
Writes data/fers/known-answers.json {date, pass, required, found, missing: [[refs, what, why]]}. kpc_fers.py refuses an all-US/Canada
run unless 'pass' is true and the check is from the last 7 days. Never fails."""
import json, os, pathlib, re, sys, time
OUT = pathlib.Path('data/fers/known-answers.json')
LINES = set()
LIVE = ('candidate', 'very tight', 'water only', 'merged into')

# Oct 29 (chat 8, KPC_Canada_KnownAnswers_Water_desk.md): CANADA'S known answers (grade C = chat 8's knowledge, maps not opened yet:
# REPORTED, not required, until chat 9 opens the official maps; then they become required like Kentucky's)
CA_SURE = [(['CA-0010', 'CA-5628'], 'Bruce Peninsula NP + Bruce Trail (trail inside)'), (['CA-0024', 'CA-0025'], 'Fundy Biosphere Reserve + Fundy NP'),
           (['CA-0052', 'CA-0053'], 'Long Point Biosphere Reserve + Long Point NWA'), (['CA-0052', 'CA-0279'], 'Long Point Biosphere Reserve + Long Point PP'),
           (['CA-3724', 'CA-4065'], 'Lanz and Cox Islands PP + Scott Islands MPA')]
CA_NOT_PLAIN = [(['CA-0040', 'CA-3167'], 'Jasper NP + Willmore Wilderness (shared border)'), (['CA-0021', 'CA-5628'], 'Fathom Five NP + Bruce Trail'),
                (['CA-0711', 'CA-4065'], 'Cape Scott PP + Scott Islands MPA')]


def canada():
    import glob
    rows = []
    for f in glob.glob('data/fers/CA-*.json'):
        try: rows += [(set(s.get('refs') or []), str(s.get('status', ''))) for s in json.load(open(f)).get('spots') or []]
        except Exception: pass  # noqa: BLE001
    if not rows: return
    live = lambda st: st.startswith(LIVE) or st.startswith('candidate')
    sure = [[r, w, 'found' if any(set(r) <= rs and live(st) for rs, st in rows) else (next((st[:80] for rs, st in rows if set(r) <= rs), 'no row'))] for r, w in CA_SURE]
    ctl = [[r, w, next((st[:80] for rs, st in rows if set(r) <= rs and st.startswith('candidate')), 'ok (not plain live)')] for r, w in CA_NOT_PLAIN]
    ok = all(x[2] == 'found' for x in sure) and all(x[2].startswith('ok') for x in ctl)
    pathlib.Path('data/fers/known-answers-ca.json').write_text(json.dumps({'about': "Canada's known answers (chat 8, grade C: reported, not required yet)", 'date': time.strftime('%Y-%m-%d'),
                                                                          'pass': ok, 'sure': sure, 'controls': ctl}, indent=1) + '\n')
    print(f"::notice title=2-fer known answers (Canada, reported only)::{'PASS' if ok else 'NOT YET'}: {sum(1 for x in sure if x[2] == 'found')} of {len(sure)} sure pairs live; "
          f"controls plain live: {sum(1 for x in ctl if not x[2].startswith('ok'))} of {len(ctl)}", flush=True)


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
    # Brandon Oct 28 8:35 PM: pairs he activates in person are PERMANENT known answers (live, the whole overlap)
    req += [(['US-0050', 'US-10105'], 'Mammoth Cave x Green River Wild River: Brandon activates it in person (live, river included)')]
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


if __name__ == '__main__' and os.environ.get('CANADA'):
    try: canada()
    except Exception as e: print(f'::notice title=2-fer known answers (Canada)::stopped: {e}')  # noqa: BLE001
    sys.exit(0)
if __name__ == '__main__':
    try: main()
    except Exception as e:  # noqa: BLE001
        print(f'::notice title=2-fer known answers::stopped: {e}', flush=True)
    sys.exit(0)
