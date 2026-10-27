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
# Oct 24 (Brandon: 'the nightly boundary check only covers the US so far. Add Canada and the world'): the Canada
# and world keys now run the same check whenever THEY are rebuilt (monthly, or by hand), so their files are read
# here too. One table per place.
PLACES = [('United States', pathlib.Path('data/us-key'), 'st'), ('Canada', pathlib.Path('data/ca-key'), 'prov'), ('World', pathlib.Path('data/world-key'), 'cc')]
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


# Oct 25 (round 5 hand checks): parks a person already looked at and found fine (the outline is right and only POTA's
# pin is off, or the park has no single outline). They leave the lists while the key still joins the SAME land;
# if a later run joins something else, the park comes back.
try:
    CHECKED = json.loads(pathlib.Path('data/boundary-checked.json').read_text(encoding='utf-8')).get('parks', {})
except Exception:  # noqa: BLE001
    CHECKED = {}
OKV = ('OUTLINE RIGHT, PIN OFF', 'NOT A LAND PARK')
HIDDEN = {'n': 0}


def checked_ok(ref, joined):
    c = CHECKED.get(ref)
    if c and c.get('v') in OKV and str(c.get('j', '')).strip().lower() == str(joined or '').strip().lower():
        HIDDEN['n'] += 1
        return True
    return False


def gather(keys, field, tag):
    states, tot = [], {'matched': 0, 'far': 0, 'noshape': 0, 'edge': 0, 'out': 0, 'swap': 0}
    swaps, outs = [], []
    for f in sorted(keys.glob('*.json')):
        if f.name in ('index.json', 'overrides.json', 'layers.json') or not f.name[:2].isupper():
            continue
        try:
            d = json.loads(f.read_text(encoding='utf-8'))
        except Exception:  # noqa: BLE001
            continue
        c = d.get('counts') or {}
        if 'pin_outside' not in c:
            continue                       # built before the check existed; it will fill in on its next run
        st = d.get(field) or f.stem
        if tag: st = f'{tag}-{st}' if not str(st).startswith(tag) else st
        # A key built before the 'no shape' and 'swap' parts existed has pin_outside but not those. Saying 0
        # there would be a lie of exactly the kind this report is meant to prevent, so it is marked stale and
        # left out of the totals until that state is rebuilt.
        stale = 'pin_no_shape' not in c
        det = c.get('detail') or 1
        row = {'st': st, 'matched': c.get('matched', 0), 'far': c.get('pin_outside', 0),
               'noshape': c.get('pin_no_shape', 0), 'out': c.get('pin_well_outside', 0),
               'swap': c.get('pin_swap', 0), 'stale': stale,
               'detail': '~110 m' if det < 0.01 else '~1.1 km' if det < 0.02 else '~2.2 km',
               'thin': c.get('thin')}
        row['edge'] = row['far'] - row['noshape'] - row['out']
        states.append(row)
        if stale:
            continue
        for k in tot:
            tot[k] += row.get(k, 0)
        for ref, v in (d.get('parks') or {}).items():
            if checked_ok(ref, v['m'][0][1] if v.get('m') else ''):
                continue
            if v.get('swap'):
                swaps.append((st, ref, v.get('n', ''), v['m'][0][1] if v.get('m') else '', v['swap'][0][1]))
            elif v.get('far') == 'well outside':
                outs.append((st, ref, v.get('n', ''), v['m'][0][1] if v.get('m') else ''))
    return states, tot, swaps, outs


def main():
    L = [f"_Written by `.github/scripts/kpc_boundary_report.py`. Nothing here has been changed in the keys._", '',
         'The US keys are rebuilt with this check 14 states a night; the Canada and world keys run it whenever they are '
         'rebuilt (monthly, or by hand from Actions), so their rows change less often. World and Canada outlines are '
         'coarser than the US ones, so their "just outside" column means less there.', '']
    saved = {}
    any_rows = False
    for place, keys, field in PLACES:
        if not keys.exists():
            continue
        got = gather(keys, field, '' if place == 'United States' else ('CA' if place == 'Canada' else ''))
        states, tot, swaps, outs = got
        if not states:
            L.append(f'## {place}')
            L.append('')
            L.append('_Not rebuilt with the check yet._')
            L.append('')
            continue
        any_rows = True
        L += section(place, states, tot, swaps, outs)
        saved[place] = {'totals': tot, 'states': states, 'swaps': [list(x) for x in swaps], 'well_outside': [list(x) for x in outs]}
    if not any_rows:
        notice('No key has been rebuilt with the check yet; nothing to report.')
        return
    try:   # Oct 26 (HQ plan 2b): the second-witness score
        sc = json.loads(pathlib.Path('data/boundary-score.json').read_text(encoding='utf-8'))
        t = sc['totals']
        L += ['## How sure are we? (second witness)', '',
              f"Each US outline scored on evidence that is NOT POTA's pin: its name, its managing agency, a second map. "
              f"**{t['high']} high, {t['medium']} medium, {t['low']} low** of {t['outlines']} outlines; "
              f"{t['no_outline']} parks have none yet.", '',
              f"**{t['pota_pin_off']} look like POTA PIN OFF**: the pin is well outside, but the name and a second witness say "
              f"our outline is right. We keep the outline; these pins can be reported to POTA.", '']
        if sc.get('pota_pin_off'):
            L.append('<details><summary>POTA pin off, busiest first</summary>'); L.append('')
            for ref, n, st, far, j, acts in sc['pota_pin_off'][:40]: L.append(f"- {ref} {n} ({st}, {acts} activations) → {j}")
            L += ['', '</details>', '']
        if sc.get('low_busiest_first'):
            L.append('<details><summary>Low confidence, busiest first (worklist for the outside bot)</summary>'); L.append('')
            for ref, n, st, j, acts, why in sc['low_busiest_first'][:40]: L.append(f"- {ref} {n} ({st}, {acts} activations) → {j}: {why}")
            L += ['', '</details>', '']
    except Exception: pass  # noqa: BLE001
    try:   # Oct 26 (HQ): NEAR MISSES, parks with no outline + official areas around their pin (chat 8 reviews; no email)
        nm = json.loads(pathlib.Path('data/outline-leads/near-miss.json').read_text(encoding='utf-8'))
        t = nm.get('totals') or {}
        L += ['## Near misses (no outline yet, but an official area sits around the pin)', '',
              f"**{t.get('parks', 0)} parks** ({t.get('us', 0)} US, {t.get('canada', 0)} Canada; {t.get('name_word', 0)} share a main name word). "
              "Not joined. Chat 8 reviews; an approved one goes into the key's overrides.json as a reviewed join. File: data/outline-leads/near-miss.json.", '']
        rows = sorted(nm.get('parks', {}).items(), key=lambda kv: (not any(l['why'].startswith('shares') for l in kv[1]['leads']), -(kv[1].get('acts') or 0)))
        if rows:
            L.append('<details><summary>Busiest first (name-word leads first)</summary>'); L.append('')
            for ref, x in rows[:60]:
                l = x['leads'][0]
                L.append(f"- {ref} {x['n']} ({x['st']}, {x.get('acts', 0)} activations) → {l['name']} [{l['layer']}, id {l['id']}, {l['km']} km, {l['why']}]")
            L += ['', '</details>', '']
    except Exception: pass  # noqa: BLE001
    if HIDDEN['n']:
        L.append(f"_{HIDDEN['n']} parks already checked by hand and found fine (pin off, or no single outline) are left out: data/boundary-checked.json._")
    body = '\n'.join(L)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(saved, indent=1) + '\n', encoding='utf-8')
    notice('; '.join(f"{p}: {v['totals']['noshape']} unmeasurable, {v['totals']['edge']} just outside, {v['totals']['out']} well outside, "
                     f"{v['totals']['swap']} wrong-land-right-name" for p, v in saved.items()))
    _publish(body)


def section(place, states, tot, swaps, outs):
    judged = tot['matched'] - tot['noshape']
    L = [f'## {place}', '']
    fresh = [r for r in states if not r.get('stale')]
    stale = [r for r in states if r.get('stale')]
    unit = 'states' if place == 'United States' else 'provinces' if place == 'Canada' else 'countries'
    L.append(f"**{len(fresh)} {unit} fully checked.**")
    if stale:
        L.append('')
        L.append(f"⏳ {len(stale)} more ({', '.join(r['st'] for r in stale)}) were measured before the "
                 f"'no outline' and 'same name' parts existed, so they are **left out of everything below** "
                 f"until the nightly job rebuilds them.")
    if not fresh:
        L.append('')
        L.append('_Nothing fully checked yet, so there are no numbers worth quoting. Check back after the '
                 'next run._')
        L.append('')
        return L
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
    coarse = [r['st'] for r in fresh if r.get('detail') != '~110 m']
    if coarse:
        L.append(f"_Outline detail matters: {', '.join(coarse)} were checked against outlines smoothed to about "
                 f"**1.1 km or more**, so many of their 'just outside' pins are the smoothing, not the join._"
                 + (' _US states are being redone from ~110 m outlines._' if place == 'United States' else ''))
        L.append('')
    L.append(f'| {("Country" if unit == "countries" else unit[:-1].title())} | outline detail | joined | not checkable | just outside | well outside | same-name swap |')
    L.append('|---|---|---|---|---|---|---|')
    for r in sorted(fresh, key=lambda r: -r['out']):
        L.append(f"| {r['st']} | {r.get('detail')} | {r['matched']} | {r['noshape']} | {r['edge']} | {r['out']} | {r['swap']} |")
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
    L.append('')
    return L


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
