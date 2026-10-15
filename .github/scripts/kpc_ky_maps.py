#!/usr/bin/env python3
"""Official boundary-map links for Kentucky public lands -> data/ky-official-maps.json (read by the Map Rep Tool Box).

Reads each agency page listed in data/ky-lands-seen.json (made by kpc_new_lands.py from the KY GIS layers):
  - Fish & Wildlife WMA pages (app.fw.ky.gov Public_Lands_Search): the "View Detailed Map" PDF (fw.ky.gov/More/Documents/...)
    plus the location-map picture and fact sheet.
  - Kentucky State Parks pages: the "Park Map" / "Trail Map" / "Campground Map" documents the park page lists.
  - Office of Kentucky Nature Preserves pages: any PDF/picture link with "map" in it.
Saves the maps AND the other documents (fact sheets, brochures, guides) the page links. Only links that are ON the agency's page are saved (never guessed). Browsers can't read those pages (no CORS), so this runs in Actions.
"""
import datetime as dt, html, json, pathlib, re, sys, time, urllib.request

SEEN, OUT = pathlib.Path('data/ky-lands-seen.json'), pathlib.Path('data/ky-official-maps.json')
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/129 Safari/537.36 (KPC map-link check)'
def notice(t, m=''): print('::notice title=%s::%s' % (t, str(m).replace('\n', '%0A')), flush=True)
def get(u):
    for i in range(3):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': UA}), timeout=45).read().decode('utf8', 'replace')
        except Exception as e:  # noqa: BLE001
            if i == 2: raise
            time.sleep(4 * (i + 1))

def kdfwr(t):
    out, seen = [], set()
    for u in re.findall(r"""href=['"](https?://fw\.ky\.gov/More/Documents/[^'"]+?\.pdf)['"]""", t, re.I):
        if u in seen: continue
        seen.add(u); f = u.rsplit('/', 1)[-1].lower()
        lab = 'Boundary map (PDF)' if re.search(r'wma_?all|_all\.pdf|map', f) else 'Fact sheet (PDF)' if 'fact' in f else 'Brochure (PDF)' if 'brochure' in f else 'Document (PDF)'
        out.append([lab, u])
    for u in re.findall(r"""src=['"](https?://app\.fw\.ky\.gov/kfwis/Map_Images/[^'"]+)['"]""", t, re.I)[:1]:
        out.append(['Location map (picture)', u])
    out.sort(key=lambda x: (0 if x[0].startswith('Boundary') else 1 if 'Location' in x[0] else 2))
    return out

def parks(t):
    out, seen = [], set()
    for lab, u in re.findall(r'"title":"([^"]{2,80}?)","content":"(https?://[^"]+?\.pdf[^"]*)"', t, re.I):
        u = u.replace('\\/', '/')
        if u in seen: continue
        seen.add(u); out.append([lab.strip() + (' (PDF)' if '.pdf' in u.lower() else ''), u])
    out.sort(key=lambda x: (0 if re.match(r'(?i)park map', x[0]) else 1 if 'trail' in x[0].lower() else 2))
    return out

def oknp(t, base):
    out, seen = [], set()
    for h, x in re.findall(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', t, re.S | re.I):
        x = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', x))).strip(); h = html.unescape(h).replace('&#58;', ':')
        if not re.search(r'\.(pdf|jpe?g|png)(\?|$)', h, re.I) or re.search(r'Title%20VI|GIS/Pages|Data-Maps', h): continue
        if not (re.search(r'map|boundar', h + ' ' + x, re.I) or re.search(r'/Nature-Preserves/', h, re.I)): continue
        if h.startswith('/'): h = 'https://eec.ky.gov' + h
        if h in seen: continue
        seen.add(h); out.append([(x or 'Map')[:60] + (' (PDF)' if '.pdf' in h.lower() else ''), h])
    return out

def main():
    if not SEEN.exists(): notice('No ky-lands-seen.json yet'); return
    L = json.loads(SEEN.read_text()).get('lists', {})
    old = json.loads(OUT.read_text()).get('items', {}) if OUT.exists() else {}
    items, n_ok, n_fail = {}, 0, 0
    for label, kind in [('Fish & Wildlife (hunting areas / WMAs)', 'kdfwr'), ('Kentucky State Parks', 'parks'), ('State Nature Preserves (OKNP)', 'oknp'), ('State Natural Areas (OKNP)', 'oknp')]:
        for name, page in sorted((L.get(label) or {}).items()):
            if not str(page).startswith('http'): continue
            try:
                t = get(page)
                maps = kdfwr(t) if kind == 'kdfwr' else parks(t) if kind == 'parks' else oknp(t, page)
                n_ok += 1
            except Exception as e:  # noqa: BLE001
                n_fail += 1; maps = (old.get(name) or {}).get('maps', [])   # keep last week's on a hiccup
            items[name] = {'page': page, 'agency': label, 'maps': maps}
            time.sleep(0.35)
    if n_ok < 20: notice('Too few pages read; not saving', '%d ok, %d failed' % (n_ok, n_fail)); sys.exit(1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({'updated': dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'), 'source': 'Map links found on each agency page (KDFWR, Kentucky State Parks, Office of Kentucky Nature Preserves)', 'items': items}, indent=1, sort_keys=True, ensure_ascii=False))
    notice('KY official map links', '%d pages read (%d failed); %d with a map link' % (n_ok, n_fail, sum(1 for v in items.values() if v['maps'])))

if __name__ == '__main__': main()
