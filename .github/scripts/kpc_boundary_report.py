#!/usr/bin/env python3
"""Reads the answer keys and writes up what the boundary check found (Brandon Oct 22 1:09 AM: 'Is the a bot
you can build and set up to be checking that on github? That way later you got more answers?').

It does no fetching of its own. kpc_us_key.py already asks, while it has the shapes in hand, whether each
joined park's pin falls inside the land it was joined to, and records one of:

  no shape to check against  the service gave the land no outline, so the check is blind here and the join
                             is NOT in question - this is the one that has to be ruled out before any number
                             from this report means anything
  edge                       the pin is just outside, within about a mile - boundary precision, or a pin put
                             at a gate or a parking spot outside the line
  well outside               the pin is nowhere near the land it was joined to
  swap                       ANOTHER area with the SAME NAME does contain the pin - two places share a name
                             and we joined the wrong one. These are the ones that can be fixed automatically.

The write-up goes in the BODY of one GitHub issue, which is edited rather than commented on, because an edit
does not email anybody (Brandon Oct 18: 'only have it send me emails for real issues'). Nothing is changed in
the keys; this only reports.
"""
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

REPO = os.environ.get('GITHUB_REPOSITORY') or 'KentuckyPortableClub/KPC-Links'
TOKEN = (os.environ.get('GITHUB_TOKEN') or '').strip()
KEYS = pathlib.Path('data/us-key')
OUT = pathlib.Path('data/boundary-report.json')
LABEL = 'boundary-check'
TITLE = '🗺 Boundary check: are the joins in the right place?'


def notice(msg):
    print(f"::notice title=Boundary report::{str(msg)[:800]}", flush=True)


def api(path, method='GET', body=None):
    req = urllib.request.Request(
        'https://api.github.com/' + path.lstrip('/'), method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Authorization': 'Bearer ' + TOKEN, 'Accept': 'application/vnd.github+json',
                 'User-Agent': 'KPC boundary report', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        t = r.read().decode('utf-8', 'replace')
        return json.loads(t) if t.strip() else {}


def main():
    if not KEYS.exists():
        notice('No answer keys yet.')
        return
    states, tot = [], {'matched': 0, 'far': 0, 'noshape': 0, 'edge': 0, 'out': 0, 'swap': 0}
    fresh_mode = False
    swaps, outs = [], []
    for f in sorted(KEYS.glob('*.json')):
        if f.name == 'index.json':
            continue
        try:
            d = json.loads(f.read_text(encoding='utf-8'))
        except Exception:  # noqa: BLE001
            continue
        c = d.get('counts') or {}
        if 'pin_outside' not in c:
            continue                       # built before the check existed; it will fill in on its next run
        st = d.get('st') or f.stem
        # A key built before the 'no shape' and 'swap' parts existed has pin_outside but not those. Saying 0
        # there would be a lie of exactly the kind this report is meant to prevent, so it is marked stale and
        # left out of the totals until that state is rebuilt.
        stale = 'pin_no_shape' not in c
        row = {'st': st, 'matched': c.get('matched', 0), 'far': c.get('pin_outside', 0),
               'noshape': c.get('pin_no_shape', 0), 'out': c.get('pin_well_outside', 0),
               'swap': c.get('pin_swap', 0), 'stale': stale}
        row['edge'] = row['far'] - row['noshape'] - row['out']
        if stale:
            states.append(row)
            continue
        states.append(row)
        for k in tot:
            tot[k] += row.get(k, 0)
        fresh_mode = True
        for ref, v in (d.get('parks') or {}).items():
            if v.get('swap'):
                swaps.append((st, ref, v.get('n', ''), v['m'][0][1] if v.get('m') else '', v['swap'][0][1]))
            elif v.get('far') == 'well outside':
                outs.append((st, ref, v.get('n', ''), v['m'][0][1] if v.get('m') else ''))

    if not states:
        notice('No state has been rebuilt with the check yet; nothing to report.')
        return

    judged = tot['matched'] - tot['noshape']
    if not fresh_mode:
        pass
    L = [f"_Written by `.github/scripts/kpc_boundary_report.py`. Nothing here has been changed in the keys._", '']
    fresh = [r for r in states if not r.get('stale')]
    stale = [r for r in states if r.get('stale')]
    L.append(f"**{len(fresh)} states fully checked.**")
    if stale:
        L.append('')
        L.append(f"⏳ {len(stale)} more ({', '.join(r['st'] for r in stale)}) were measured before the "
                 f"'no outline' and 'same name' parts existed, so they are **left out of everything below** "
                 f"until the nightly job rebuilds them.")
    if not fresh:
        L.append('')
        L.append('_Nothing fully checked yet, so there are no numbers worth quoting. Check back after the '
                 'nightly run._')
        body0 = '\n'.join(L)
        notice('Nothing fully checked yet; wrote the holding note only.')
        _publish(body0)
        return
    L.append('')
    if tot['noshape']:
        L.append(f"⚠️ **{tot['noshape']} joins could not be checked at all** — the land came back with no "
                 f"outline, so the pin test is blind for those. They are NOT in question; they are simply "
                 f"unmeasured, and they must be taken out of any percentage.")
        L.append('')
    L.append(f"Of **{judged}** joins that could actually be checked:")
    L.append('')
    L.append(f"- **{tot['edge']}** sit just outside the line (within about a mile) — boundary precision, or a "
             f"pin put at a gate or a parking spot. Not a wrong join.")
    L.append(f"- **{tot['out']}** are well outside.")
    L.append(f"- **{tot['swap']}** of those have another area *with the same name* that does contain the pin — "
             f"**these are wrong joins and the right land is already identified.**")
    L.append('')
    if judged:
        L.append(f"So the part that looks genuinely wrong is **{tot['swap']} certain + up to {tot['out'] - tot['swap']} "
                 f"to look at**, out of {judged} checkable joins ({100 * tot['out'] / judged:.1f}% at the very worst).")
        L.append('')
    L.append('| State | joined | not checkable | just outside | well outside | same-name swap |')
    L.append('|---|---|---|---|---|---|')
    for r in sorted(fresh, key=lambda r: -r['out']):
        L.append(f"| {r['st']} | {r['matched']} | {r['noshape']} | {r['edge']} | {r['out']} | {r['swap']} |")
    if swaps:
        L.append('')
        L.append(f'### Wrong land, right name — {len(swaps)} found')
        L.append('These joined one place and the pin is inside a different place of the same name.')
        L.append('')
        for st, ref, n, joined, better in swaps[:40]:
            L.append(f"- **{ref}** {n} ({st}) — joined to *{joined}*, but the pin is inside *{better}*")
        if len(swaps) > 40:
            L.append(f'- …and {len(swaps) - 40} more in `data/boundary-report.json`')
    if outs:
        L.append('')
        L.append(f'<details><summary>Well outside, no same-name alternative ({len(outs)}) — mostly very large '
                 f'scattered areas where one pin cannot sit inside every piece</summary>')
        L.append('')
        for st, ref, n, joined in outs[:40]:
            L.append(f"- {ref} {n} ({st}) → {joined}")
        L.append('')
        L.append('</details>')
    body = '\n'.join(L)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({'totals': tot, 'states': states,
                               'swaps': [list(x) for x in swaps], 'well_outside': [list(x) for x in outs]},
                              indent=1) + '\n', encoding='utf-8')
    notice(f"{len(states)} states; {tot['noshape']} unmeasurable, {tot['edge']} just outside, "
           f"{tot['out']} well outside, {tot['swap']} wrong-land-right-name")

    _publish(body)


def _publish(body):
    if not TOKEN:
        print(body)
        return
    try:
        found = api(f'repos/{REPO}/issues?state=all&labels={LABEL}&per_page=1')
        if found:
            api(f"repos/{REPO}/issues/{found[0]['number']}", 'PATCH', {'body': body, 'state': 'open'})
            notice(f"Updated issue #{found[0]['number']} (an edit, so nobody is emailed).")
        else:
            n = api(f'repos/{REPO}/issues', 'POST', {'title': TITLE, 'body': body, 'labels': [LABEL]})
            notice(f"Opened issue #{n.get('number')}.")
    except urllib.error.HTTPError as e:
        notice(f'GitHub said HTTP {e.code}; the report is in data/boundary-report.json either way.')
    except Exception as e:  # noqa: BLE001
        notice(f'Could not write the issue: {str(e)[:160]}')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:  # noqa: BLE001
        notice(f'stopped early: {type(e).__name__}: {str(e)[:300]}')
        sys.exit(0)          # never fail the job: a failed run emails Brandon
