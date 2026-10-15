"""Weekly watch for NEW Kentucky public lands that could become POTA (or KFF) parks.

Brandon (Oct 15 2026): "have GitHub scan for new parks automatically and let me know if it finds one in KY".

Each Monday this compares this week's lists with last week's (data/ky-lands-seen.json):
  - Kentucky's own GIS layers: Fish & Wildlife hunting areas / WMAs, State Parks,
    State Nature Preserves and State Natural Areas (Office of Kentucky Nature Preserves, Energy & Environment Cabinet)
  - USGS PAD-US: federal and state land in Kentucky that is open to the public
  - POTA's own list of Kentucky parks (so brand-new POTA parks are reported too)
  - News headlines (Google News search) about new WMAs, nature preserves, state parks and land purchases in Kentucky
Anything new is posted as a COMMENT on one GitHub issue labelled "ky-new-lands" (a comment makes GitHub email
the people watching the repo). The issue body also keeps the full list of Kentucky federal/state lands that
are not in POTA yet, each with a link to check it in the Mapping Representative's Tool Box.
The first run only saves the starting lists (nothing is "new" yet). Nothing on the website is changed.
"""
import datetime as dt
import html
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = 'Mozilla/5.0 (compatible; KPC-new-lands; +https://kentuckyportableclub.github.io/KPC-Links/)'
SEEN = pathlib.Path('data/ky-lands-seen.json')
LABEL = 'ky-new-lands'
TOOL = 'https://kentuckyportableclub.github.io/KPC-Links/kpc-maprep.html?state=KY&name='
KYG = 'https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/'
LAYERS = [
    ('Fish & Wildlife (hunting areas / WMAs)', 'Ky_Public_Hunting_Areas_WGS84WM/MapServer/1', 'AREANAME', 'DETAIL', 'MANAGER'),   # MANAGER holds the owner: KDFWR / Private / U of Ky ...
    ('Kentucky State Parks', 'Ky_State_Parks_Features_WGS84WM/MapServer/8', 'PUBLIC_NAM|PARK_NAME', 'HYPERLINK', ''),
    ('State Nature Preserves (OKNP)', 'Ky_KNP_State_Nature_Preserves_WGS84WM/MapServer/0', 'MANAME', 'Webpage', 'MA_OWNER'),
    ('State Natural Areas (OKNP)', 'Ky_KNP_Natural_Areas_WGS84WM/MapServer/0', 'MANAME', 'Webpage', 'MA_OWNER'),
]
PADUS = 'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query'
NEWS_Q = [
    'Kentucky "wildlife management area" new',
    'Kentucky "nature preserve" new OR dedicated OR acquired',
    'Kentucky "state park" new OR opens OR acquired',
    'Kentucky Fish and Wildlife acres purchase public land',
    'Kentucky "state natural area" OR "state forest" new',
]


def get(url, tries=3, data=None, ua=None):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={'User-Agent': ua or UA})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(5 * (i + 1))
    raise last


def notice(title, msg):
    print('::notice title=%s::%s' % (title, str(msg).replace('%', '%25').replace('\n', '%0A')), flush=True)


TYPEW = r'wildlife management area|state nature preserve|state natural area|state resort park|state historic site|state recreation area|national wildlife refuge|national recreation area|national forest|state park|state forest|wma|snp|sna|nwr|the'


def norm(s):
    s = (s or '').lower().replace('&', ' and ')
    s = re.sub(TYPEW, ' ', s)
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()


def kind(s):
    s = (s or '').lower()
    for k, rx in [('wma', r'wildlife management area|\bwma\b|wildlife area|hunting area'), ('snp', r'nature preserve|natural area|\bsnp\b|\bsna\b'),
                  ('hist', r'historic site|historical park'), ('sp', r'state (resort )?park|recreation area'), ('nf', r'national forest'),
                  ('sf', r'state forest'), ('nwr', r'wildlife refuge|\bnwr\b'), ('nfh', r'hatchery')]:
        if re.search(rx, s):
            return k
    return ''


OWNERS = {}


def ky_layer(path, field, web, owner=''):
    out, off = {}, 0
    fields = field.split('|')
    while True:
        q = urllib.parse.urlencode({'where': '1=1', 'outFields': ','.join(fields + [web] + ([owner] if owner else [])), 'returnGeometry': 'false', 'f': 'json',
                                    'resultOffset': off, 'resultRecordCount': 1000, 'orderByFields': 'OBJECTID'})
        j = json.loads(get(KYG + path + '/query?' + q))
        fs = j.get('features', [])
        for f in fs:
            a = f.get('attributes', {})
            n = next((str(a.get(x)).strip() for x in fields if a.get(x) and len(str(a.get(x)).strip()) > 3), '')
            if n and 'PUBLIC_NAM' in fields and not re.search(r'park|site', n, re.I):
                h = a.get(web) or ''
                n += ' State Historic Site' if '/historic/' in h else ' State Resort Park' if '/resort/' in h else ' State Park'
            if n:
                out[n] = (a.get(web) or '').strip()
                if owner and a.get(owner):
                    OWNERS[n] = str(a.get(owner)).strip()
        if not j.get('exceededTransferLimit') or not fs:
            break
        off += len(fs)
    return out


def padus():
    out, off = {}, 0
    where = "State_Nm='KY' AND Pub_Access='OA'"   # (the server's firewall refuses longer WHERE clauses; the rest is filtered here)
    while off < 20000:
        q = urllib.parse.urlencode({'where': where, 'outFields': 'Unit_Nm,Loc_Mang,GIS_Acres,Mang_Type,Own_Type,Category', 'returnGeometry': 'false', 'f': 'json',
                                    'resultOffset': off, 'resultRecordCount': 1000, 'orderByFields': 'OBJECTID'})
        j = json.loads(get(PADUS + '?' + q, ua='KPC'))
        fs = j.get('features', [])
        for f in fs:
            a = f.get('attributes', {})
            n = (a.get('Unit_Nm') or '').strip()
            if not n or re.search(r'outstanding resource water', n, re.I) or re.search(r'division of water', a.get('Loc_Mang') or '', re.I) or a.get('Category') != 'Fee' or a.get('Mang_Type') not in ('FED', 'STAT') or a.get('Own_Type') not in ('FED', 'STAT'):
                continue
            m, ac = out.get(n, (a.get('Loc_Mang') or '', 0))
            out[n] = (m, ac + (a.get('GIS_Acres') or 0))
        if not fs or (not j.get('exceededTransferLimit') and len(fs) < 1000):
            break
        off += len(fs)
        time.sleep(1)
    return {n: '%s · %d acres' % (m, round(ac)) for n, (m, ac) in out.items() if ac >= 20}


def pota():
    rows = json.loads(get('https://api.pota.app/location/parks/US-KY'))
    return {r['reference']: r.get('name', '') for r in rows if str(r.get('reference', '')).startswith('US-')}


def news():
    items = {}
    for q in NEWS_Q:
        root = None
        for u in ('https://www.bing.com/news/search?' + urllib.parse.urlencode({'q': q, 'format': 'rss', 'qft': 'interval="8"'}),
                  'https://news.google.com/rss/search?' + urllib.parse.urlencode({'q': q + ' when:30d', 'hl': 'en-US', 'gl': 'US', 'ceid': 'US:en'})):
            try:
                root = ET.fromstring(get(u, tries=2))
                break
            except Exception as e:  # noqa: BLE001
                last = e
        if root is None:
            notice('News search failed', '%s: %s' % (q, last))
            continue
        for it in root.iter('item'):
            t = (it.findtext('title') or '').strip()
            link = (it.findtext('link') or '').strip()
            if not t or not re.search(r'kentucky|\bky\b', t, re.I):
                continue
            if not re.search(r'wildlife management area|\bwma\b|nature preserve|natural area|state park|state forest|acre|public land|hunting|refuge|preserve', t, re.I):
                continue
            items[re.sub(r'\W+', ' ', t.lower()).strip()[:120]] = {'title': html.unescape(t), 'link': link, 'date': (it.findtext('pubDate') or '')[:16]}
        time.sleep(2)
    return items


PARKISH = {'sp', 'hist', ''}


def in_pota(name, P, loose=False):
    n, k = norm(name), kind(name)
    for ref, pn in P.items():
        pk, pnn = kind(pn), norm(pn)
        kinds_ok = not k or not pk or pk == k or (k in PARKISH and pk in PARKISH)
        if pnn == n and kinds_ok:
            return ref
        if loose and n and pnn:
            # spelling differences: 'Horsemill' / 'Horse Mill', 'Sexton' / 'Sextons', 'Dr. William H. Martin' / 'William H. Martin',
            # combined names 'Knobs State Forest and WMA' / 'Knobs State Forest', 'Vernon-Douglas' / 'Hall-Hill/Vernon-Douglas'
            sq = lambda s: re.sub(r'\b(dr|the|and|county)\b', '', ' '.join(w[:-1] if len(w) > 4 and w.endswith('s') and not w.endswith('ss') else w for w in s.split())).replace(' ', '')  # noqa: E731
            a, b = sq(re.sub(r'\(.*?\)', '', n)), sq(pnn)
            s, l = sorted((a, b), key=len)
            if len(s) >= 6 and (s == l or (l.startswith(s) and len(s) / len(l) >= 0.6) or (len(s) >= 9 and s in l)) and (kinds_ok or ' and ' in name.lower() or '/' in pn):
                return ref
    return None


def gh(*args, input_text=None):
    r = subprocess.run(['gh', *args], input=input_text, text=True, capture_output=True)
    if r.returncode != 0:
        print('gh error:', r.stderr.strip())
    return r.stdout


def main():
    old = json.loads(SEEN.read_text()) if SEEN.exists() else None
    now = {'updated': dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'), 'lists': {}, 'news': {}}
    for label, path, field, web, owner in LAYERS:
        try:
            now['lists'][label] = ky_layer(path, field, web, owner)
            notice('Read ' + label, '%d places' % len(now['lists'][label]))
        except Exception as e:  # noqa: BLE001
            notice('Could not read ' + label, e)
            if old and label in old.get('lists', {}):
                now['lists'][label] = old['lists'][label]   # keep last week's so a hiccup isn't reported as "removed"
    try:
        now['lists']['USGS PAD-US (federal + state, open to the public)'] = padus()
    except Exception as e:  # noqa: BLE001
        notice('Could not read PAD-US', e)
        if old and old['lists'].get('USGS PAD-US (federal + state, open to the public)'):
            now['lists']['USGS PAD-US (federal + state, open to the public)'] = old['lists']['USGS PAD-US (federal + state, open to the public)']
    try:
        P = pota()
        now['pota'] = P
    except Exception as e:  # noqa: BLE001
        notice('Could not read POTA', e)
        P = (old or {}).get('pota', {})
        now['pota'] = P
    try:
        now['news'] = news()
    except Exception as e:  # noqa: BLE001
        notice('News failed', e)
    if old:   # keep news we've already seen so it's only reported once
        for k, v in old.get('news', {}).items():
            now['news'].setdefault(k, v)

    # ---------- what's new since last week ----------
    new_lands, new_pota, new_news = [], [], []
    if old:
        for label, L in now['lists'].items():
            if not old.get('lists', {}).get(label):
                continue   # a list we couldn't read last time: this week is its starting point
            before = old['lists'][label]
            for n, info in L.items():
                if n not in before and not any(norm(n) == norm(b) for b in before):
                    new_lands.append((label, n, info, in_pota(n, P)))
        for ref, n in P.items():
            if ref not in old.get('pota', {}):
                new_pota.append((ref, n))
        for k, v in now['news'].items():
            if k not in old.get('news', {}):
                new_news.append(v)

    # ---------- the standing list: KY state/federal lands not in POTA ----------
    gap = {}
    for label, L in now['lists'].items():
        for n, info in L.items():
            if not in_pota(n, P, loose=True):
                key = norm(n) + '|' + kind(n)
                gap.setdefault(key, (n, label, info))
    SEEN.parent.mkdir(parents=True, exist_ok=True)
    SEEN.write_text(json.dumps(now, indent=1, sort_keys=True, ensure_ascii=False))

    link = lambda n: '[%s](%s%s)' % (n, TOOL, urllib.parse.quote(n))  # noqa: E731
    when = dt.date.today().isoformat()
    if not old:
        notice('Starting lists saved', 'First run: %d lands across %d lists. New ones will be reported from next week.' % (sum(len(v) for v in now['lists'].values()), len(now['lists'])))
    lines = ['Weekly watch for new Kentucky public lands (federal and state) that could become POTA parks.',
             'Updated %s. Each name opens the **Mapping Representative\'s Tool Box** (password) already filled in.' % now['updated'],
             '', 'Watched: ' + ', '.join('%s (%d)' % (k, len(v)) for k, v in now['lists'].items()) + ', POTA US-KY (%d parks), news headlines.' % len(P), '']
    now['owners'] = OWNERS

    def why_not(n, label, info):
        o = OWNERS.get(n, '') + ' ' + (info if not info.startswith('http') else '')
        if re.search(r'\bprivate\b|fiscal court|college|school|sanctuary|conservancy|foundation', o, re.I) and not re.search(r'office of kentucky|kdfwr|department of fish', OWNERS.get(n, ''), re.I):
            return 'owner is not federal/state (%s)' % OWNERS.get(n, info).strip()
        if re.search(r'hunting access area', n, re.I):
            return 'hunting access area (usually private land leased for hunting)'
        if re.search(r'military|army depot|training area|\bfort (knox|campbell)', n, re.I):
            return 'military land'
        if re.search(r'state park state nature preserve', n, re.I):
            return 'a preserve inside a state park the parks department owns (same-agency sub-park)'
        if re.search(r'\blake (wma|wildlife)', n, re.I) or re.search(r'^(barren river|buckhorn|carr creek|dale hollow|grayson|green river|nolin|paintsville|rough river|taylorsville|lake barkley|lake cumberland|martins fork) lake', n, re.I):
            return 'probably Army Corps of Engineers lake land (few are exceptions)'
        if re.search(r'universit|college|u of ky', o, re.I):
            return 'university land (CHECK: University of the Cumberlands WMA was added)'
        if re.search(r'(lake|lakes|pond)$', n, re.I) and 'PAD-US' in label:
            return 'small agency fishing lake (usually not added unless public land surrounds it)'
        if re.search(r'outstanding resource water|mussel sanctuary|education center|fish access|purchase unit|recreation area', n, re.I):
            return 'special-use area or not a park on its own'
        return ''
    good, maybe = [], []
    for key in sorted(gap, key=lambda k: gap[k][0].lower()):
        n, label, info = gap[key]
        line = '- %s · %s%s%s' % (link(n), label, (' · owner: ' + OWNERS[n]) if n in OWNERS else '', (' · ' + info) if info and not info.startswith('http') else (' · [official page](%s)' % info if info else ''))
        w = why_not(n, label, info)
        (maybe if w else good).append(line + ((' · _%s_' % w) if w else ''))
    lines += ['### ⭐ Look promising (%d)' % len(good), 'Federal/state owned, open, no POTA park of that name yet. Check each one in the Tool Box before emailing the Mapping Representative.', ''] + good + ['']
    lines += ['<details><summary><b>%d more that probably will not qualify</b> (reason shown on each)</summary>' % len(maybe), ''] + maybe + ['', '</details>', '', 'This issue stays open; each week with something new adds a comment (GitHub emails you about comments).']
    body = '\n'.join(lines)

    gh('label', 'create', LABEL, '--color', '2C9A55', '--description', 'New Kentucky public lands watch (weekly)', '--force')
    found = json.loads(gh('issue', 'list', '--label', LABEL, '--state', 'open', '--json', 'number', '--limit', '1') or '[]')
    title = '🌲 Kentucky new public lands watch (POTA candidates)'
    if found:
        num = str(found[0]['number'])
        gh('issue', 'edit', num, '--title', title, '--body-file', '-', input_text=body)
    else:
        out = gh('issue', 'create', '--title', title, '--label', LABEL, '--body-file', '-', input_text=body).strip()
        num = out.rstrip('/').split('/')[-1] if out else ''
    if new_lands or new_pota or new_news:
        c = ['### New this week (%s)' % when, '']
        if new_pota:
            c += ['**New POTA parks in Kentucky** (add them to the site data):', ''] + ['- [%s %s](https://pota.app/#/park/%s)' % (r, n, r) for r, n in new_pota] + ['']
        if new_lands:
            c += ['**New names in the state / federal land lists:**', '']
            for label, n, info, ref in new_lands:
                c.append('- %s · %s%s%s' % (link(n), label, (' · ' + info) if info and not info.startswith('http') else (' · [official page](%s)' % info if info else ''), (' · already POTA %s' % ref) if ref else ' · **not in POTA**'))
            c.append('')
        if new_news:
            c += ['**News headlines (last 30 days):**', ''] + ['- [%s](%s) %s' % (x['title'], x['link'], x['date']) for x in new_news[:15]] + ['']
        c.append('Check each one with the Tool Box before emailing the Map Rep: news and new map entries are leads, not proof.')
        if num:
            gh('issue', 'comment', num, '--body-file', '-', input_text='\n'.join(c))
        notice('New this week', '%d new POTA parks, %d new land names, %d news items' % (len(new_pota), len(new_lands), len(new_news)))
    else:
        notice('Nothing new', 'No new lands, POTA parks or news this week.')


if __name__ == '__main__':
    sys.exit(main())
