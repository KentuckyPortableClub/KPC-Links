#!/usr/bin/env python3
"""OBSERVATIONS LOG (chat 2, Oct 27 2026; HQ, MAP DATA RULE SHEET in notes/mapping.md). Run at the end of every import or
nightly run, BEFORE its save step: compares the data files as this run left them with the last saved version (git HEAD)
and appends what is worth a human look to data/map-observations.json:
  possible overlap     a 2-fer spot newly decided (candidate / very tight / not sure / water only)
  outline size         a park's joined outline changed by 25% or 500 acres, or its number of pieces changed (G-M5)
  outline lost         a park had an outline and now has none
  pin outside          a park's POTA pin is newly WELL outside its outline
  layer problem        a map that did not answer / was not found (from this run's *.log files)
  name mismatch        a new near-miss lead that shares a name word (data/outline-leads/near-miss.json)
  far place            a park's joined land includes a same-name place far from the rest (boundary review #4)
Each item {kind, ref, name, place, what, first, last}; an item seen again only moves 'last'; items not seen for 90 days
drop off. 'last_run' holds this run's counts (the boundary-check issue shows them). Changes nothing else. Chat 8 reviews.
Never fails."""
import glob, json, os, pathlib, re, subprocess, sys, time  # noqa: F401
sys.path.insert(0, os.path.dirname(__file__))
from kpc_save import save_json

OUT = pathlib.Path(os.environ.get('OBS_FILE') or 'data/map-observations.json')   # Oct 27: each data bot writes its own file (no push clashes)
RUN = os.environ.get('OBS_RUN') or 'run'
TODAY = time.strftime('%Y-%m-%d')
KEEP_DAYS = 90


BASE = os.environ.get('OBS_BASE') or 'HEAD'      # Oct 27 (storage Stage 2): the KPC-Links commit to compare with (the daily watch: ~25 h ago)
DATA_DIR = os.environ.get('OBS_DATA_DIR') or ''   # the KPC-Data clone: the hidden files (2-fers, leads) are compared with ITS last save
DATA_PATHS = ('data/fers/', 'data/outline-leads/', 'data/access-leads/')


def head(path):
    try:
        cmd = ['git', '-C', DATA_DIR, 'show', f'HEAD:{path}'] if DATA_DIR and path.startswith(DATA_PATHS) else ['git', 'show', f'{BASE}:{path}']
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode != 0 and DATA_DIR and path.startswith(DATA_PATHS):   # a big file is kept gzipped in KPC-Data
            import gzip as _gz
            g = subprocess.run(['git', '-C', DATA_DIR, 'show', f'HEAD:{path}.gz'], capture_output=True, timeout=120)
            return json.loads(_gz.decompress(g.stdout)) if g.returncode == 0 and g.stdout else None
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
                    # G-M5 (Brandon Oct 27 6:45 AM, boundary review #6): a change of 25% or 500 acres, or a different number of pieces
                    if a > 0 and b > 0 and (abs(b - a) >= .25 * a or abs(b - a) >= 500):
                        found.append(('outline size', ref, name, place, f'{round(a):,} → {round(b):,} acres'))
                    elif len(om) != len(nm):
                        found.append(('outline size', ref, name, place, f'{len(om)} → {len(nm)} pieces'))
                if p.get('kept') and p.get('read') and p['read'] < time.strftime('%Y-%m-%d', time.localtime(time.time() - 90 * 86400)):
                    found.append(('outline lost', ref, name, place, f"kept from an old read only: last read {p['read']} (renamed or removed by the agency?)"))   # boundary review #3.2
                if p.get('far_place') and p.get('far_place') != o.get('far_place'):   # boundary review #4: a same-name place far from the rest, kept joined
                    found.append(('far place', ref, name, place, 'joined land far from the rest: ' + '; '.join(p['far_place'])[:120] + ' (same park, or another place?)'))
                if p.get('far') == 'well outside' and o.get('far') != 'well outside' and nm:
                    found.append(('pin outside', ref, name, place, "POTA pin newly well outside its outline (POTA pin off, or a wrong join?)"))


def fers(found):
    for f in sorted(glob.glob('data/fers/*-*.json')):
        if not re.fullmatch(r'(US|CA)-[A-Z]{2}' + (r'|W-[A-Z]{2}' if os.environ.get('OBS_WORLD') else ''), pathlib.Path(f).stem): continue   # the world is parked
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


def old_days(d, n):
    return bool(d) and d < time.strftime('%Y-%m-%d', time.localtime(time.time() - n * 86400))


# Oct 27 (Fable's research-bots review #3, HQ 12:20 PM: ONE change-detection helper, shared with boundary B6): the data bots'
# files compared with the last saved version the same way as the outlines
def closures(found):
    new, old = now('data/alerts/us-parks.json'), head('data/alerts/us-parks.json') or {}
    if not new: return
    for sid, m in (new.get('sources') or {}).items():
        o = (old.get('sources') or {}).get(sid) or {}
        if m.get('ok') and m.get('n') == 0 and (o.get('n') or m.get('n_prev') or 0) > 0:
            found.append(('feed went to zero', sid, m.get('agency') or sid, m.get('st') or '', f"closures feed answered with 0 park items (was {o.get('n') or m.get('n_prev')}): really nothing closed, or a changed feed? {m.get('page', '')}"))
        if old_days(m.get('kept_since'), 60):
            found.append(('feed stale', sid, m.get('agency') or sid, m.get('st') or '', f"feed not read since {m['kept_since']}: its last closures are still shown"))


def access(found):
    for f in sorted(glob.glob('data/access/*.json')):
        if f.endswith('index.json'): continue
        new, old = now(f), head(f)
        if not new or not old: continue
        place = pathlib.Path(f).stem
        a = sum(len(v) for v in (old.get('parks') or {}).values()); b = sum(len(v) for v in (new.get('parks') or {}).values())
        if a >= 20 and abs(b - a) >= .25 * a:
            found.append(('access points', '', place, place, f'{a:,} → {b:,} parking / access points (a layer gone, renamed or added?)'))


def camps(found):
    for f in sorted(glob.glob('data/campstate/US-??.json')):
        new, old = now(f), head(f)
        if not new or not old: continue
        a, b = len(old.get('camps') or []), len(new.get('camps') or [])
        if a and (b == 0 or abs(b - a) >= max(5, .25 * a)):
            found.append(('campgrounds', '', pathlib.Path(f).stem, pathlib.Path(f).stem, f'{a} → {b} state campgrounds ({str(new.get("source", ""))[:90]})'))


def links(found):
    new, old = now('data/parkinfo-web.json'), head('data/parkinfo-web.json') or {}
    if not new: return
    for ref, e in (new.get('parks') or {}).items():
        o = (old.get('parks') or {}).get(ref) or {}
        for k in ('map', 'web'):
            if o.get(k) and not e.get(k): found.append(('link lost', ref, ref, '', f"official {k} link removed: {o[k][:100]}"))
        mc, oc = (e.get('map_check') or {}).get('map'), (o.get('map_check') or {}).get('map')
        if e.get('map') and oc == 'ok' and mc and mc != 'ok':
            found.append(('link broken', ref, ref, '', f"map link stopped loading ({mc}): {e['map'][:100]} (re-find on the agency page)"))


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
    for f in (keys, fers, layers, near, closures, access, camps, links):
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
