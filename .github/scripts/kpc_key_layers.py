#!/usr/bin/env python3
"""BOT W: WIRE APPROVED LAYERS (chat 2, Oct 30 2026 8:15 AM; HQ 8:10 AM, Brandon 8:06 'automate all we can').
Chat 10's LAYER collector turns `LAYER | ref | agency | url | name field: X | note` lines from the Fable files into rows chat 11
answers. Every row chat 11 says YES to is added here to data/state-gis.json (the key's list of official state / province layers)
and its state goes into data/us-key/answers-states.txt, so the same night's key rebuild reads it. No hand step.

Reads  <DATA>/data/waiting/questions/layers.json (rows: {area or st, url, name_field, agency, kind?, answer, checked_by, ref?})
         (also accepts data/intake/queue.json rows with the same fields; whichever exists)
Writes data/state-gis.json (appends {kind, ag, nm, url, host:'agency', lic, note}); data/us-key/answers-states.txt (adds the state)
Rules (bookkeeping only): YES only; the URL must end in /MapServer/N or /FeatureServer/N (a polygon layer the key can page) or it is
listed as skipped; a URL already in the state's list is skipped; kind = the row's kind if it is one of park/wild/forest/preserve/land,
else 'land'. Canada areas (CA-XX / provinces) go under their province code like the existing entries. Exit 0 always.
"""
import json, os, pathlib, re, sys, datetime as dt

KINDS = {'park', 'wild', 'forest', 'preserve', 'land'}
US = set('AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split())


def data_dir():
    for d in (os.environ.get('DATA'), '../kpcdata', '../kpc-data', 'kpcdata'):
        if d and pathlib.Path(d, 'data').is_dir(): return pathlib.Path(d)
    return None


def load(p, d):
    try: return json.load(open(p))
    except Exception: return d  # noqa: BLE001


def rows_of(j):
    q = j.get('questions') or j.get('rows') or j.get('items') if isinstance(j, dict) else j
    if isinstance(q, dict): q = list(q.values())
    return [r for r in (q or []) if isinstance(r, dict)]


def st_of(r):
    a = str(r.get('st') or r.get('area') or r.get('state') or '').upper().replace('US-', '').replace('CA-', '')
    return a[:2] if re.fullmatch(r'[A-Z]{2}', a[:2] or '') else ''


def main():
    D = data_dir()
    if D is None: print('::notice title=Layer wiring::no KPC-Data checkout: nothing wired'); return
    src = [p for p in (D / 'data/waiting/questions/layers.json', D / 'data/intake/queue.json', D / 'data/intake/ready.json') if p.exists()]
    rows = []
    for p in src:
        for r in rows_of(load(p, {})):
            r['_intake'] = 'intake' in str(p); rows.append(r)
    # Oct 30 9:45 AM (chat 10 AUTO-2): an intake READY row with approved: true counts as a YES; its name field is in probe.name_field
    for r in rows:
        # Oct 30 10:35 PM (HQ 5:30 PM): only an approval that SAYS who approved it (AUTO-2's own stamp or a person) counts; a bare
        # 'approved: true' (the GB SSSI test row: a land-class layer AUTO-2 must not approve) is ignored
        if r.get('approved') is True and r.get('approved_by') and not r.get('answer'): r['answer'] = 'YES'; r['checked_by'] = r['approved_by']
        if not r.get('name_field') and isinstance(r.get('probe'), dict): r['name_field'] = r['probe'].get('name_field') or r['probe'].get('nameField') or ''
    sg = load('data/state-gis.json', {}); S = sg.setdefault('states', {})
    have = {str(x.get('url', '')).rstrip('/').lower() for v in S.values() for x in v}
    # a layer the keys already read another way (US layers.json, the Canada builder's own EXTRA list) is never added twice
    known = ''
    for f in ('data/us-key/layers.json', 'data/ca-key/layers.json', '.github/scripts/kpc_canada_bounds.py', '.github/scripts/kpc_us_key.py'):
        try: known += open(f).read().lower()
        except Exception: pass  # noqa: BLE001
    WX = load('data/world-key/extra-layers.json', {}); WC = WX.setdefault('countries', {})
    wknown = (open('.github/scripts/kpc_world_key.py').read().lower() if os.path.exists('.github/scripts/kpc_world_key.py') else '')
    added, skipped, states, provs, ccs = [], [], set(), set(), set()
    for r in rows:
        if str(r.get('answer') or '').strip().upper() != 'YES': continue
        url = str(r.get('url') or r.get('layer') or '').strip().rstrip('/')
        area = str(r.get('area') or '').strip().upper()
        # Oct 30 (Brandon 9:48 'Yes'): an intake row whose area is a bare country code (GB, AU, NZ…) is a WORLD layer
        if area.startswith('W-') and re.fullmatch(r'[A-Z]{2}', area[2:]): area = area[2:]; r = dict(r, _world=True)   # Oct 31 (Fable review #4): a layer-collector world row (area W-MX): 894 YES were skipped as 'no state'
        if (r.get('_intake') and re.fullmatch(r'[A-Z]{2}', area) and not r.get('st')) or r.get('_world'):
            if not re.search(r'/(MapServer|FeatureServer)/\d+$', url, re.I): skipped.append(f"{area} not a layer URL: {url[:80]}"); continue
            if url.lower().split('://')[-1] in wknown or any(str(x.get('url')).rstrip('/').lower() == url.lower() for x in WC.get(area, [])): continue
            WC.setdefault(area, []).append({'label': str(r.get('title') or r.get('publisher') or r.get('agency') or area + ' official layer')[:80], 'url': url,
                                            'name_field': str(r.get('name_field') or ''), 'credit': str((r.get('terms') or {}).get('credit') or '')[:200],
                                            'note': f"wired by kpc_key_layers.py {dt.date.today()}: {r.get('checked_by') or 'chat 11'} YES"})
            added.append(f'{area} (world) {url[-50:]}'); ccs.add(area); continue
        st = st_of(r)
        if area.startswith('US-') and st not in US: st = ''
        if not st: skipped.append(f"{r.get('ref') or area} no state"); continue
        if not re.search(r'/(MapServer|FeatureServer)/\d+$', url, re.I): skipped.append(f"{st} not a layer URL: {url[:80]}"); continue
        if url.lower() in have: continue
        if url.lower().split('://')[-1] in known: skipped.append(f"{st} already read by the key: {url[-50:]}"); continue
        nm = str(r.get('name_field') or r.get('nm') or '').replace('name field:', '').strip()
        if not nm: skipped.append(f"{st} {url[-40:]} no name field"); continue
        kind = str(r.get('kind') or '').lower(); kind = kind if kind in KINDS else 'land'
        S.setdefault(st, []).append({'kind': kind, 'ag': str(r.get('agency') or f'{st} official layer')[:120], 'nm': nm, 'url': url,
                                     'host': 'agency', 'lic': str(r.get('licence') or r.get('lic') or 'see layer'),
                                     'note': f"wired by kpc_key_layers.py {dt.date.today()}: chat 11 YES ({r.get('checked_by') or 'chat 11'}); park {r.get('ref') or '-'}"})
        have.add(url.lower()); added.append(f'{st} {url[-50:]}')
        if st in US and not area.startswith('CA-'): states.add(st)
        else: provs.add(st)
    if added:
        json.dump(sg, open('data/state-gis.json', 'w'), indent=1, ensure_ascii=False)
        # each key's 'rebuild tonight' list: US states (BOT B), Canada provinces (nightly Canada run), world countries (nightly world run)
        for f, new in (('data/us-key/answers-states.txt', states), ('data/ca-key/answers-provinces.txt', provs), ('data/world-key/answers-countries.txt', ccs)):
            if not new: continue
            p = pathlib.Path(f); old = set(p.read_text().split()) if p.exists() else set()
            p.write_text(' '.join(sorted(old | new)) + '\n')
        if ccs: json.dump(WX, open('data/world-key/extra-layers.json', 'w'), indent=1, ensure_ascii=False)
    print(f"::notice title=Layer wiring::{len(added)} layer(s) wired" + (f": {'; '.join(added[:6])}" if added else '') +
          (f"; skipped {len(skipped)}: {'; '.join(skipped[:4])}" if skipped else ''))


if __name__ == '__main__':
    try: main()
    except Exception as e: print(f'::notice title=Layer wiring::stopped: {str(e)[:200]}')  # noqa: BLE001
    sys.exit(0)
