"""New references watch (Brandon Oct 17 2026: 'bots look for new parks … post to park tips other states … a 7 day rotation').

Every day: compare today's lists with what we saw before (data/new-refs/seen.json):
  POTA  every US location (api.pota.app/locations -> /location/parks/US-XX)
  KFF   the WWFF directory (wwff.co/wwff-data/wwff_directory.csv), KFF- only
  SOTA  the SOTA summits list (storage.sota.org.uk/summitslist.csv), US associations only, valid today
New ones go in kpc-new-refs.json for 7 days:
  Kentucky   -> 'NEW THIS WEEK' box on Park Notes (kpc-park-notes.html) + ONE post a day to Discord, Facebook and Club News
                (kpc-announcements.json), plus a comment on the ky-new-lands issue so we remember to add the park to our files.
  Other states -> 'NEW THIS WEEK' box on Park Notes: Other States only (no Facebook, Brandon).
Posting starts 2026-10-21 5 PM Central (START). The first run only remembers the lists.
A list that comes back much shorter than last time is skipped that day (a broken download must not look like 'everything is new').
DRY=1 prints what would happen without writing or posting.
"""
import csv, datetime, io, json, os, pathlib, re, subprocess, sys, time, urllib.parse, urllib.request

UA = 'KPC-NewRefs/1.0 (+https://kentuckyportableclub.github.io/KPC-Links/)'
SITE = 'https://kentuckyportableclub.github.io/KPC-Links/'
START = datetime.datetime(2026, 10, 21, 22, 0, tzinfo=datetime.timezone.utc)   # 5 PM Central (CDT)
DRY = os.environ.get('DRY') == '1'
NOW = datetime.datetime.now(datetime.timezone.utc)
TODAY = NOW.date().isoformat()
KEEP_DAYS = 7
SEEN, OUT, ANN = pathlib.Path('data/new-refs/seen.json'), pathlib.Path('kpc-new-refs.json'), pathlib.Path('kpc-announcements.json')
DISCORD = (os.environ.get('DISCORD_WEBHOOK_URL') or '').strip()
FB_ID, FB_TOKEN = (os.environ.get('FB_PAGE_ID') or '').strip(), (os.environ.get('FB_PAGE_TOKEN') or '').strip()


def notice(t, m=''):
    m = str(m).replace('%', '%25').replace('\r', '').replace('\n', '%0A')
    print(f'::notice title={t}::{m}', flush=True)


def get(url, tries=3, timeout=90, raw=False):
    for i in range(tries):
        try:
            b = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': '*/*'}), timeout=timeout).read()
            return b if raw else json.loads(b)
        except Exception as e:  # noqa: BLE001
            if i == tries - 1: raise
            time.sleep(3 + 5 * i)


def load(p, d):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return d  # noqa: BLE001


# ---------------------------------------------------------------- today's lists
def pota():
    locs = sorted({l['locationDesc'] for l in get('https://api.pota.app/locations') if str(l.get('locationDesc', '')).startswith('US-')})
    out, bad = {}, 0
    for d in locs:
        try: L = get(f'https://api.pota.app/location/parks/{d}')
        except Exception: bad += 1; continue  # noqa: BLE001
        for p in L:
            ref = p.get('reference')
            if not ref: continue
            r = out.setdefault(ref, {'name': p.get('name', ''), 'st': [], 'la': p.get('latitude'), 'lo': p.get('longitude')})
            st = d.split('-', 1)[1]
            if st not in r['st']: r['st'].append(st)
        time.sleep(.2)
    if bad > 2: raise RuntimeError(f'{bad} POTA states failed')
    return out


def kff():
    raw = get('https://wwff.co/wwff-data/wwff_directory.csv', raw=True, timeout=180).decode('utf-8', 'replace')
    out = {}
    for r in csv.DictReader(io.StringIO(raw)):
        ref = (r.get('reference') or '').strip().upper()
        if not ref.startswith('KFF-') or (r.get('status') or '').lower() != 'active': continue
        try: la, lo = round(float(r['latitude']), 5), round(float(r['longitude']), 5)
        except Exception: la = lo = None  # noqa: BLE001
        st = (r.get('state') or '').strip().upper()
        out[ref] = {'name': (r.get('name') or '').strip(), 'st': [st] if re.fullmatch(r'[A-Z]{2}', st) else [], 'la': la, 'lo': lo}
    return out


ST_NAMES = {'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT',
            'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
            'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI',
            'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH',
            'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
            'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD', 'Tennessee': 'TN',
            'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI',
            'Wyoming': 'WY', 'Puerto Rico': 'PR'}


def sota_state(code, assoc):
    if code.startswith('W4K/'): return ['KY']
    m = re.search(r'\(([^)]+)\)', assoc or '')
    names = re.split(r'\s*(?:,|&|\band\b|-)\s*', m.group(1)) if m else []
    return [ST_NAMES[n] for n in names if n in ST_NAMES]


def sota():
    raw = get('https://storage.sota.org.uk/summitslist.csv', raw=True, timeout=240).decode('utf-8', 'replace')
    lines = raw.splitlines()
    if lines and lines[0].startswith('SOTA Summits List'): lines = lines[1:]
    today = NOW.date(); out = {}

    def dt(s):
        try: d, m, y = s.split('/'); return datetime.date(int(y), int(m), int(d))
        except Exception: return None  # noqa: BLE001
    for r in csv.DictReader(io.StringIO('\n'.join(lines))):
        code = (r.get('SummitCode') or '').strip()
        if not re.match(r'^(W\d|K[HLP]\d)', code): continue
        vt, vf = dt(r.get('ValidTo', '')), dt(r.get('ValidFrom', ''))
        if (vt and vt < today) or (vf and vf > today): continue
        try: la, lo = round(float(r['Latitude']), 5), round(float(r['Longitude']), 5)
        except Exception: la = lo = None  # noqa: BLE001
        st = sota_state(code, r.get('AssociationName', ''))
        out[code] = {'name': (r.get('SummitName') or '').strip(), 'st': st, 'la': la, 'lo': lo,
                     'ft': int(float(r.get('AltFt') or 0)), 'pts': int(float(r.get('Points') or 0))}
    return out


# ---------------------------------------------------------------- posting (Kentucky only)
def http(url, data=None, headers=None, method=None):
    req = urllib.request.Request(url, data=data, headers={'User-Agent': UA, **(headers or {})}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e: return e.code, e.read().decode('utf-8', 'replace')


def post_discord(title, text, link):
    if not DISCORD.startswith('https://'): notice('New references', 'No Discord webhook; skipped Discord.'); return True
    body = {'username': 'KPC', 'allowed_mentions': {'parse': []},
            'embeds': [{'title': title[:250], 'url': link, 'color': 0xd5a63a, 'description': (text + f'\n\n[See them on our site →]({link})')[:4000]}]}
    c, r = http(DISCORD, json.dumps(body).encode(), {'Content-Type': 'application/json'})
    if c >= 300: notice('New references', f'Discord HTTP {c}: {r[:200]}'); return False
    return True


def post_facebook(title, text, link):
    if not FB_ID or not FB_TOKEN: notice('New references', 'No Facebook secrets; skipped Facebook.'); return True
    data = urllib.parse.urlencode({'access_token': FB_TOKEN, 'message': f'{title}\n\n{text}', 'link': link}).encode()
    c, r = http(f'https://graph.facebook.com/{FB_ID}/feed', data)
    if c >= 300: notice('New references', f'Facebook HTTP {c}: {r[:200]}'); return False
    return True


PROG_NAME = {'pota': 'POTA park', 'kff': 'KFF (WWFF) reference', 'sota': 'SOTA summit'}


def line(it):
    s = f"{it['ref']} {it['name']}"
    if it['prog'] == 'sota' and it.get('ft'): s += f" ({it['ft']:,} ft, {it.get('pts', 0)} pt{'s' if it.get('pts') != 1 else ''})"
    return '• ' + s


def ky_post(items):
    groups = [(p, [i for i in items if i['prog'] == p]) for p in ('pota', 'kff', 'sota')]
    groups = [(p, g) for p, g in groups if g]
    n = len(items)
    title = f"🆕 New in Kentucky: {n} new {PROG_NAME[groups[0][0]] + ('s' if n > 1 else '') if len(groups) == 1 else 'references'}!"
    parts = []
    for p, g in groups:
        head = {'pota': 'Parks on the Air just added', 'kff': 'WWFF (KFF) just added', 'sota': 'SOTA just added'}[p]
        parts.append(head + ':\n' + '\n'.join(line(i) for i in g[:25]) + (f'\n…and {len(g) - 25} more' if len(g) > 25 else ''))
    text = '\n\n'.join(parts) + "\n\nWho's going to be first to put it on the air? Park tips welcome on our Park Notes page. 73, KPC"
    return title, text


def gh(*args, input_text=None):
    r = subprocess.run(['gh', *args], input=input_text, text=True, capture_output=True)
    if r.returncode != 0: print('gh error:', r.stderr.strip())
    return r.stdout


# ---------------------------------------------------------------- main
seen = load(SEEN, {})
feed = load(OUT, {'items': []})
items = [i for i in feed.get('items', []) if i.get('found', '') >= (NOW.date() - datetime.timedelta(days=KEEP_DAYS - 1)).isoformat()]
have = {(i['prog'], i['ref']) for i in items}
changed, summary = False, []
for prog, fn, floor in (('pota', pota, 10000), ('kff', kff, 4000), ('sota', sota, 30000)):
    try: cur = fn()
    except Exception as e:  # noqa: BLE001
        notice(f'New references: {prog.upper()}', f'Could not read today ({e}); skipped.'); continue
    old = set(seen.get(prog, []))
    if len(cur) < floor or (old and len(cur) < 0.9 * len(old)):
        notice(f'New references: {prog.upper()}', f'Only {len(cur)} read (last time {len(old)}); skipped today.'); continue
    new = sorted(set(cur) - old)
    if not old:
        summary.append(f'{prog.upper()}: first run, remembered {len(cur)}')
    else:
        for ref in new:
            if (prog, ref) in have: continue
            c = cur[ref]
            it = {'ref': ref, 'prog': prog, 'name': c['name'], 'st': c['st'], 'la': c['la'], 'lo': c['lo'], 'found': TODAY}
            if prog == 'sota': it.update(ft=c.get('ft'), pts=c.get('pts'))
            items.append(it)
        summary.append(f'{prog.upper()}: {len(cur)} today, {len(new)} new' + (f" ({', '.join(new[:8])}{'…' if len(new) > 8 else ''})" if new else ''))
    # keep refs that dropped off too (a park that comes back is not 'new')
    seen[prog] = sorted(old | set(cur))
    changed = True
notice('New references', '\n'.join(summary) or 'Nothing read.')

items.sort(key=lambda i: (i['found'], i['prog'], i['ref']), reverse=True)
feed = {'updated': NOW.isoformat(timespec='seconds'), 'start': START.isoformat(), 'days': KEEP_DAYS, 'items': items}

# Kentucky posts: once a day, only after START, only items not posted yet
posted = set(seen.get('posted', []))
ky = [i for i in items if 'KY' in i.get('st', []) and f"{i['prog']}|{i['ref']}" not in posted]
if ky and NOW >= START:
    title, text = ky_post(ky)
    link = SITE + 'kpc-park-notes.html#new'
    if DRY:
        notice('New references (dry run): Kentucky post', f'{title}\n{text}')
    else:
        ok = post_discord(title, text, link) & post_facebook(title, text, link)
        ann = load(ANN, {'items': []})
        aid = 'nr-' + TODAY
        ann['items'] = [a for a in ann.get('items', []) if a.get('id') != aid]
        ann['items'].insert(0, {'id': aid, 'date': NOW.isoformat(timespec='seconds'), 'pages': ['news'], 'text': f'{title}\n\n{text}', 'photos': []})
        ann['items'].sort(key=lambda a: a.get('date', ''), reverse=True)
        ann['items'] = ann['items'][:150]; ann['updated'] = NOW.isoformat(timespec='seconds')
        ANN.write_text(json.dumps(ann, indent=1, ensure_ascii=False), encoding='utf-8')
        if os.environ.get('GITHUB_ACTIONS'):
            num = json.loads(gh('issue', 'list', '--label', 'ky-new-lands', '--state', 'open', '--json', 'number', '--limit', '1') or '[]')
            if num:
                gh('issue', 'comment', str(num[0]['number']), '--body-file', '-', input_text=
                   '🆕 **New Kentucky references today** (add them to kpc-ky-data.json and the guides):\n\n' + '\n'.join(line(i) for i in ky))
        seen['posted'] = sorted(posted | {f"{i['prog']}|{i['ref']}" for i in ky})
        notice('New references: Kentucky post', f'{title} ({"sent" if ok else "some places failed"})')
elif ky:
    notice('New references', f'{len(ky)} Kentucky item(s) waiting for the start ({START.isoformat()}).')
# forget posted marks older than the 7-day window
keep = {f"{i['prog']}|{i['ref']}" for i in items}
seen['posted'] = sorted(set(seen.get('posted', [])) & keep)

if DRY:
    notice('New references (dry run)', f'{len(items)} item(s) in the 7-day list; nothing written.')
    sys.exit(0)
SEEN.parent.mkdir(parents=True, exist_ok=True)
SEEN.write_text(json.dumps(seen, separators=(',', ':')), encoding='utf-8')
s = json.dumps(feed, indent=1, ensure_ascii=False)
old = OUT.read_text(encoding='utf-8') if OUT.exists() else ''
if json.loads(old or '{}').get('items') != items or not old:
    OUT.write_text(s, encoding='utf-8')
