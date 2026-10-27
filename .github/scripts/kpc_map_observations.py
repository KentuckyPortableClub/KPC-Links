#!/usr/bin/env python3
"""OBSERVATIONS LOG (chat 2, Oct 27 2026; HQ, MAP DATA RULE SHEET in notes/mapping.md). Run at the end of every import or
nightly run, BEFORE its save step: compares the data files as this run left them with the last saved version (git HEAD)
and appends what is worth a human look to data/map-observations.json:
  possible overlap     a 2-fer spot newly decided (candidate / very tight / not sure / water only)
  outline size         a park's joined outline became half or double its size
  outline lost         a park had an outline and now has none
  pin outside          a park's POTA pin is newly WELL outside its outline
  layer problem        a map that did not answer / was not found (from this run's *.log files)
  name mismatch        a new near-miss lead that shares a name word (data/outline-leads/near-miss.json)
Each item {kind, ref, name, place, what, first, last}; an item seen again only moves 'last'; items not seen for 90 days
drop off. 'last_run' holds this run's counts (the boundary-check issue shows them). Changes nothing else. Chat 8 reviews.
Never fails."""
import glob, json, os, pathlib, re, subprocess, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from kpc_save import save_json

OUT = pathlib.Path('data/map-observations.json')
RUN = os.environ.get('OBS_RUN') or 'run'
TODAY = time.strftime('%Y-%m-%d')
KEEP_DAYS = 90


def head(path):
    try:
        r = subprocess.run(['git', 'show', f'HEAD:{path}'], capture_output=True, text=True, timeout=60)
        return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None
    except Exception: return None  # noqa: BLE001


def now(path):
    try: return json.load(open(path))
    except Exception: return None  # noqa: BLE001


def acres(m): return sum(float(x[2] or 0) for x in m if len(x) > 2 and isinstance(x[2], (int, float)))


def keys(found):
    for pat in ('data/us-key/US-??.json', 'data/ca-key/CA-??.json', 'data/world-key/??.json'):
        for f in sorted(glob.glob(pat)):
            new, old = now(f), head(f)
            if not new or not old: continue
            place = pathlib.Path(f).stem
            for ref, p in (new.get('parks') or {}).items():
                o = (old.get('parks') or {}).get(ref)
                if not o: continue
                nm, om = p.get('m') or [], o.get('m') or []
                name = p.get('n') or ref
                if om and not nm: found.append(('outline lost', ref, name, place, 'had an official outline, now none'))
                elif om and nm:
                    a, b = acres(om), acres(nm)
                    if a > 0 and b > 0 and (b >= 2 * a or b <= a / 2):
                        found.append(('outline size', ref, name, place, f'{round(a):,} → {round(b):,} acres'))
                if p.get('far') == 'well outside' and o.get('far') != 'well outside' and nm:
                    found.append(('pin outside', ref, name, place, "POTA pin newly well outside its outline (POTA pin off, or a wrong join?)"))


def fers(found):
    for f in sorted(glob.glob('data/fers/*-*.json')):
        if not re.fullmatch(r'(US|CA)-[A-Z]{2}|W-[A-Z]{2}', pathlib.Path(f).stem): continue
        new, old = now(f), head(f) or {}
        if not new: continue
        before = {s.get('id'): str(s.get('status', '')) for s in old.get('spots') or []}
        for s in new.get('spots') or []:
            st = str(s.get('status', ''))
            if not st.startswith(('candidate', 'very tight', 'not sure', 'water only')): continue
            if before.get(s.get('id')) == st: continue
            names = s.get('names') or {}
            label = ' + '.join(names.get(r, r) for r in s.get('refs') or [])
            found.append(('possible overlap', '+'.join(s.get('refs') or []), label, pathlib.Path(f).stem,
                          f"{st[:60]}{' · ' + s['small'] if s.get('small') else ''} (hidden; chat 8 checks both official maps)"))


def layers(found):
    seen = set()
    for f in glob.glob('*.log') + glob.glob('logs/*.log'):
        try: txt = open(f, encoding='utf-8', errors='replace').read()
        except Exception: continue  # noqa: BLE001
        for line in txt.splitlines():
            m = re.search(r'(not read|layer not found|did not answer|answered \d{3}|saved copy was used|stopped)', line, re.I)
            if not m: continue
            msg = re.sub(r'::notice title=[^:]*::', '', line).strip()[:160]
            if msg in seen: continue
            seen.add(msg)
            found.append(('layer problem', '', msg[:80], pathlib.Path(f).stem, msg))


def near(found):
    new, old = now('data/outline-leads/near-miss.json'), head('data/outline-leads/near-miss.json') or {}
    if not new: return
    had = set((old.get('parks') or {}).keys())
    for ref, x in (new.get('parks') or {}).items():
        if ref in had: continue
        l = next((l for l in x.get('leads') or [] if str(l.get('why', '')).startswith('shares')), None)
        if l: found.append(('name mismatch', ref, x.get('n') or ref, x.get('st') or '', f"no outline; '{l['name']}' ({l['layer']}) holds the pin, {l['why']}"))


def main():
    found = []
    for f in (keys, fers, layers, near):
        try: f(found)
        except Exception as e: found.append(('layer problem', '', f'observations: {f.__name__} stopped', '', str(e)[:120]))  # noqa: BLE001
    d = now(OUT) or {}
    items = {f"{i['kind']}|{i['ref']}|{i['what'][:60]}": i for i in d.get('items') or []}
    counts = {}
    for kind, ref, name, place, what in found:
        k = f'{kind}|{ref}|{what[:60]}'
        counts[kind] = counts.get(kind, 0) + 1
        if k in items: items[k]['last'] = TODAY
        else: items[k] = {'kind': kind, 'ref': ref, 'name': name, 'place': place, 'what': what, 'first': TODAY, 'last': TODAY, 'run': RUN}
    cut = time.strftime('%Y-%m-%d', time.localtime(time.time() - KEEP_DAYS * 86400))
    keep = sorted((i for i in items.values() if i['last'] >= cut), key=lambda i: (i['last'], i['kind'], i['ref']), reverse=True)[:5000]
    save_json(OUT, {'about': 'OBSERVATIONS LOG (kpc_map_observations.py; MAP DATA RULE SHEET, notes/mapping.md): what the map bots saw that is worth a '
                             'human look. Chat 8 reviews; nothing changes because of this file. Items drop off 90 days after they were last seen.',
                    'last_run': {'date': TODAY, 'run': RUN, 'counts': counts, 'new': sum(1 for i in keep if i['first'] == TODAY)},
                    'items': keep}, indent=1)
    print(f"::notice title=Map observations::{RUN}: {json.dumps(counts)} ({len(keep)} kept)", flush=True)


if __name__ == '__main__':
    try: main()
    except Exception as e:  # noqa: BLE001
        print(f'::notice title=Map observations::stopped: {e}', flush=True)
    sys.exit(0)
