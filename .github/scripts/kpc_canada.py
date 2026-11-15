"""Canadian pins for the KPC US Trip Planner (Brandon Oct 16: 'Canada you can go ahead and drop the pins, we work on
boundaries later'). Writes data/canada.json in the same row format as locations.json:
  ['POTA', 'CA-0001', name, lat, lon, url]   from api.pota.app (all Canadian POTA parks, by province)
  ['WWFF', 'VEFF-0001', name, lat, lon, url, None, potaRef] from our weekly WWFF copy (data/wwff/VEFF.json); potaRef = the
    confirmed link of data/wwff-xref-VEFF.json ('' when none)
  ['SOTA', 'VE7/..', name, lat, lon, url, altM, points] from our weekly SOTA tiles (VE/VA/VY/VO associations)
Keeps last week's POTA rows if POTA can't be reached."""
import json, os, glob, time, urllib.request, datetime
from kpc_save import save_json, save_text  # Oct 25 storage plan: write only when the content changed
import kpc_net_guard; kpc_net_guard.install()
import kpc_pin_guard as PG   # Nov 11: a POTA pin that changed is recorded; an unusable one keeps the last good pin
UA = {'User-Agent': 'KPC Canada pins (kentuckyportableclub.github.io)'}
def note(t, m): print(f'::notice title={t}::{m}')
def get(u):
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as f: return json.loads(f.read().decode('utf-8', 'replace'))
        except Exception as e: err = e; time.sleep(3 + 4 * i)
    raise err
try: old = json.load(open('data/canada.json'))
except Exception: old = {'rows': []}
oldp = {r[1]: r for r in old.get('rows', []) if r[0] == 'POTA'}
pota, prov, bad, events = {}, {}, [], []
for pv in 'AB BC MB NB NL NS NT NU ON PE QC SK YT'.split():
    try:
        L = get(f'https://api.pota.app/location/parks/CA-{pv}')
        for p in L:
            ref = p.get('reference', '')
            if not ref.startswith('CA-') or ref in pota: continue
            name = (p.get('name') or '').strip()
            try: raw = (round(float(p['latitude']), 5), round(float(p['longitude']), 5))
            except Exception: raw = None   # POTA listed the park without a number: still listed (never 'retired'); the guard keeps the last good pin
            o = oldp.get(ref)
            pin, ev = PG.decide(ref, (o[3], o[4]) if o else None, raw, 'canada', name)   # the pin follows POTA; a change is recorded, junk keeps the last good pin
            if ev: events.append(ev)
            if pin is None: pin = raw          # no earlier pin: as before (a 0,0 is passed on for the key to mark pin00; nothing at all = skipped)
            if pin is None: continue
            pota[ref] = ['POTA', ref, name, pin[0], pin[1], 'https://pota.app/#/park/' + ref]; prov[pv] = prov.get(pv, 0) + 1
        time.sleep(.5)
    except Exception as e: bad.append(pv); note(f'CA-{pv}', f'failed: {str(e)[:100]}')
if not pota:
    pota = dict(oldp); note('POTA', 'no answer: kept last copy')
elif bad or len(pota) < 0.9 * len(oldp):
    # Oct 23 (nightly now): a province that failed, or a short answer, keeps last night's pins and retires nothing
    for r, row in oldp.items(): pota.setdefault(r, row)
    note('POTA', f'part of the list missing ({", ".join(bad) or "short answer"}): kept last pins, nothing retired tonight')
elif oldp:
    import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import kpc_retired_refs as RR
    RR.record({r: row[2] for r, row in oldp.items() if r not in pota}, set(pota), 'canada')
rows = sorted(pota.values(), key=lambda r: r[1])
# Nov 14 (KPC owner, 2026-11-14): a VEFF row also gets [None, potaRef] like locations.json, potaRef = the CONFIRMED link of
# data/wwff-xref-VEFF.json (kpc_wwff_links.py; '' when none). Every reader of this file reads POTA rows only, or columns 1-6.
# No file = the rows stay 6 long, as before.
import kpc_wwff_links as WL   # same folder as this script (like kpc_save)
XR = WL.load_confirmed('VEFF')
if XR is None: note('WWFF links', 'data/wwff-xref-VEFF.json missing or unreadable: VEFF rows without a POTA link')
try:
    for x in json.load(open('data/wwff/VEFF.json')):
        try: rows.append(['WWFF', x[0], x[1], round(float(x[2]), 5), round(float(x[3]), 5), 'https://wwff.co/directory/?showRef=' + x[0]]
                         + ([None, WL.pick_link('', XR.get(x[0]))] if XR is not None else []))
        except Exception: pass
except Exception as e: note('WWFF', str(e)[:100])
seen = set()
for f in glob.glob('data/sota/t/*.json'):
    for r in json.load(open(f)):
        a = r[0].split('/')[0]
        if a[:2] in ('VE', 'VA', 'VY', 'VO') and r[0] not in seen:
            seen.add(r[0]); rows.append(['SOTA', r[0], r[1], r[4], r[5], 'https://sotl.as/summits/' + r[0], r[3], r[6]])
if rows != old.get('rows'):   # nightly: no commit when nothing changed
    save_json('data/canada.json', {'rows': rows})
PG.record(events)
note('Canada pins', f"{len(pota)} POTA parks ({', '.join(f'{k} {v}' for k, v in sorted(prov.items()))}), {sum(1 for r in rows if r[0]=='WWFF')} WWFF, {len(seen)} SOTA")
