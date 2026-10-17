"""North America pins outside the US and Canada for the KPC US Trip Planner (Brandon Oct 17: 'drop pins in Mexico next,
finish all pins in North America'). Writes data/northam.json in the same row format as locations.json / canada.json:
  ['POTA', 'MX-0001', name, lat, lon, url]    from api.pota.app: every location of the programs in NA below (/locations
                                              lists them with their locationDesc, then /location/parks/<desc>)
  ['WWFF', 'XEFF-0001', name, lat, lon, url]  from our weekly WWFF copy (data/wwff/*.json)
  ['SOTA', 'XE1/BC-001', ...]                 from our weekly SOTA tiles
Mexico, Central America, the Caribbean, Bermuda, Greenland and Saint Pierre et Miquelon. Keeps last week's POTA rows for
a program POTA doesn't answer for."""
import json, glob, time, urllib.request, datetime

UA = {'User-Agent': 'KPC North America pins (kentuckyportableclub.github.io)'}
# POTA program prefixes (ISO codes since POTA's 2025 change) for North America outside US + Canada
POTA_NA = ('MX GT BZ SV HN NI CR PA CU JM HT DO PR VI BS BB TT AG DM GD KN LC VC AI AW CW SX BQ MF BL GP MQ KY TC VG MS BM GL PM UM').split()
# WWFF programs that are wholly North American, and mixed ones filtered to the NA box
WWFF_NA = 'XEFF TGFF V3FF YSFF HRFF YNFF TIFF HPFF COFF 6YFF HHFF HIFF C6FF 8PFF V2FF J7FF V4FF J6FF P4FF ZFFF'.split()
WWFF_MIX = 'VPFF FFF OZFF PAFF'.split()
SOTA_NA = ('XE', 'TI', 'TG', 'HR', 'YN', 'YS', 'HP', 'V3', 'CO', 'CM', 'HI', '6Y', 'KP4', 'KP2', 'C6', '8P', '9Y', 'J3', 'J6', 'J7', 'J8',
           'V2', 'V4', 'FG', 'FM', 'PJ', 'VP2', 'VP5', 'VP9', 'OX', 'FP', 'ZF', 'P4', 'HH')


def note(t, m):
    print(f'::notice title={t}::{m}', flush=True)


def get(u):
    err = None
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as f:
                return json.loads(f.read().decode('utf-8', 'replace'))
        except Exception as e:
            err = e; time.sleep(3 + 4 * i)
    raise err


def in_na(la, lo):  # North America box, east to Greenland, south to Panama
    return 5 <= la <= 84 and -180 <= lo <= -10


try:
    old = json.load(open('data/northam.json'))
except Exception:
    old = {'rows': []}
oldpota = {r[1]: r for r in old.get('rows', []) if r[0] == 'POTA'}

pota, byprog, failed = {}, {}, set()
try:
    locs = get('https://api.pota.app/locations')
except Exception as e:
    locs = []; note('POTA locations', f'failed: {str(e)[:100]}')
want = [l['locationDesc'] for l in locs if str(l.get('locationDesc', '')).split('-')[0] in POTA_NA
        or l.get('locationDesc') in ('US-PR', 'US-VI')]  # Puerto Rico + US Virgin Islands sit in POTA's US program
for desc in sorted(set(want)):
    pre = desc if desc.startswith('US-') else desc.split('-')[0]
    try:
        for p in get(f'https://api.pota.app/location/parks/{desc}'):
            ref = p.get('reference', '')
            try:
                la, lo = round(float(p['latitude']), 5), round(float(p['longitude']), 5)
            except Exception:
                continue
            if ref and ref not in pota:
                pota[ref] = ['POTA', ref, (p.get('name') or '').strip(), la, lo, 'https://pota.app/#/park/' + ref]
                byprog[pre] = byprog.get(pre, 0) + 1
        time.sleep(.4)
    except Exception as e:
        failed.add(pre); note(desc, f'failed: {str(e)[:100]}')
for ref, r in oldpota.items():  # keep last week's parks for a program that failed this time
    if ref not in pota and (ref.split('-')[0] in failed or any(f.startswith('US-') for f in failed) and ref.startswith('US-')):
        pota[ref] = r
rows = sorted(pota.values(), key=lambda r: r[1])

nw = 0
for f in WWFF_NA + WWFF_MIX:
    try:
        for x in json.load(open(f'data/wwff/{f}.json')):
            try:
                la, lo = round(float(x[2]), 5), round(float(x[3]), 5)
            except Exception:
                continue
            if f in WWFF_MIX and not in_na(la, lo):
                continue
            rows.append(['WWFF', x[0], x[1], la, lo, 'https://wwff.co/directory/?showRef=' + x[0]]); nw += 1
    except FileNotFoundError:
        pass
    except Exception as e:
        note('WWFF ' + f, str(e)[:100])

seen = set()
for f in glob.glob('data/sota/t/*.json'):
    for r in json.load(open(f)):
        a = r[0].split('/')[0]
        if a.startswith(SOTA_NA) and not a.startswith(('VE', 'VA', 'VY', 'VO', 'W', 'K', 'N')) or a.startswith(('KP4', 'KP2')):
            if r[0] not in seen and in_na(r[4], r[5]):
                seen.add(r[0]); nm = r[1] if r[1] and r[1] != r[0] else f'Unnamed summit, {r[3]:,} m ({r[2]:,} ft)'  # most Mexican summits have no name
                rows.append(['SOTA', r[0], nm, r[4], r[5], 'https://sotl.as/summits/' + r[0], r[3], r[6]])

json.dump({'updated': datetime.date.today().isoformat(), 'rows': rows}, open('data/northam.json', 'w'), separators=(',', ':'), ensure_ascii=False)
note('North America pins', f"{len(pota)} POTA parks ({', '.join(f'{k} {v}' for k, v in sorted(byprog.items()))}), {nw} WWFF, {len(seen)} SOTA")
