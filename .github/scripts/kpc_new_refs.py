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
# New parks and references belong with the park news (Brandon Oct 21)
DISCORD = ((os.environ.get('KPC_PARKS_WEBHOOK') or os.environ.get('DISCORD_WEBHOOK_URL') or os.environ.get('KPC_DISCORD_WEBHOOK') or '').strip().split() or [''])[0]
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
POTA_FAILED = set()   # states whose list could not be read today (Kentucky must be read for the retired check)
LOCN = {}             # parks per state read today (saved as seen['locn'] for tomorrow's short-state check)


def pota():
    locs = sorted({l['locationDesc'] for l in get('https://api.pota.app/locations') if str(l.get('locationDesc', '')).startswith('US-')})
    out, bad, failed = {}, 0, []

    def one(d):
        try: return get(f'https://api.pota.app/location/parks/{d}')
        except Exception: return None  # noqa: BLE001
    got = {}
    for d in locs:
        got[d] = one(d)
        if got[d] is None: failed.append(d)
        time.sleep(.2)
    if failed:   # Oct 28: one more try for a state that timed out, so one hiccup does not trip the gate
        time.sleep(20)
        for d in failed: got[d] = one(d); time.sleep(1)
    prevn = seen.get('locn', {})   # parks per state yesterday: a state that comes back short counts as not read
    for d in locs:
        L = got[d]
        n0 = prevn.get(d, 0)
        if not isinstance(L, list) or (n0 >= 10 and len(L) < 0.9 * n0):
            bad += 1; POTA_FAILED.add(d)
            if isinstance(L, list): notice('New references: POTA', f'{d} came back short ({len(L)} vs {n0} yesterday): treated as not read today.')
            continue
        LOCN[d] = len(L)
        for p in L:
            ref = p.get('reference') if isinstance(p, dict) else None
            if not ref: continue
            r = out.setdefault(ref, {'name': p.get('name', ''), 'st': [], 'la': p.get('latitude'), 'lo': p.get('longitude')})
            st = d.split('-', 1)[1]
            if st not in r['st']: r['st'].append(st)
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
    body = {'username': 'KPC-N4KPC-Bot', 'allowed_mentions': {'parse': []},
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
    # Oct 24 (Brandon: 'new park ... ky post should be daily if a new park appears and yes'): 'be the first' wording
    only_pota = len(groups) == 1 and groups[0][0] == 'pota'
    title = (f"🆕 New park{'s' if n > 1 else ''} to activate in Kentucky: be the first!" if only_pota else
             f"🆕 New in Kentucky: {n} new {PROG_NAME[groups[0][0]] + ('s' if n > 1 else '') if len(groups) == 1 else 'references'}: be the first!")
    parts = []
    for p, g in groups:
        head = {'pota': 'Parks on the Air just added', 'kff': 'WWFF (KFF) just added', 'sota': 'SOTA just added'}[p]
        L = [line(i) + (f"\n   https://pota.app/#/park/{i['ref']}" if p == 'pota' and len(g) <= 6 else '') for i in g[:25]]
        parts.append(head + ':\n' + '\n'.join(L) + (f'\n…and {len(g) - 25} more' if len(g) > 25 else ''))
    text = '\n\n'.join(parts) + ("\n\nWho's going to be first to put it on the air? Find it on Kentucky Park Control: " + SITE + "kpc-park-control.html"
                                  "\nBeen there? Share a tip on Park Notes. 73, KPC")
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
TODAYS = {}   # today's official lists that passed the checks (search lists + retired check)
# Oct 28 GATE (HQ tune pass): POTA API hiccup guard. Yesterday's exact list = everything seen minus seen['off'] (refs that were
# missing yesterday). FAIL (nothing saved for that program today, one notice): the 3 known Kentucky parks missing, or more than
# 2% of yesterday's list gone at once. More than 1% gone = read the whole list a second time; only refs missing BOTH times leave.
KNOWN = ('US-1264', 'US-8144', 'US-4484')
DROP_MAX, RETIRE_MAX = 0.02, 0.01
CONFIRMED = set()   # programs whose losses were confirmed by a second read today
LOCPFX = {'pota': ('POTA', re.compile(r'^US-')), 'kff': ('WWFF', re.compile(r'^KFF-')), 'sota': ('SOTA', re.compile(r'^(W\d|K[HLP]\d)'))}


def yesterday(prog):
    if prog in seen.get('off', {}): return set(seen.get(prog, [])) - set(seen['off'][prog])
    try:   # first run with the gate: the Finder's search list is yesterday's list
        k, rx = LOCPFX[prog]
        return {r[1] for r in json.loads(pathlib.Path('locations.json').read_text(encoding='utf-8')) if r[0] == k and rx.match(str(r[1]))}
    except Exception: return set()  # noqa: BLE001


def gate(prog, fn, cur, floor):
    """Returns today's list (maybe merged with a second read) or None = do not use it today."""
    global POTA_FAILED
    P = prog.upper()
    prev = yesterday(prog)
    miss = [k for k in KNOWN if k not in cur] if prog == 'pota' else []
    gone = prev - set(cur)
    why = (f'only {len(cur)} read (floor {floor})' if len(cur) < floor else
           f'known parks missing: {", ".join(miss)}' if miss else
           f'{len(gone)} of {len(prev)} gone at once (> {DROP_MAX:.0%})' if prev and len(gone) > DROP_MAX * len(prev) else '')
    if why:
        notice(f'New references: {P}', f'GATE FAIL {why}; nothing saved for {P} today (POTA/WWFF/SOTA hiccup guard).'); return None
    if prev and len(gone) > RETIRE_MAX * len(prev):
        f1 = set(POTA_FAILED); POTA_FAILED.clear()
        time.sleep(60)
        try: cur2 = fn()
        except Exception as e:  # noqa: BLE001
            notice(f'New references: {P}', f'GATE FAIL {len(gone)} gone and the confirming read failed ({e}); nothing saved for {P} today.'); return None
        POTA_FAILED = f1 & POTA_FAILED if prog == 'pota' else f1
        for k, v in cur2.items(): cur.setdefault(k, v)
        CONFIRMED.add(prog)
        notice(f'New references: {P}', f'GATE PASS {len(cur)} read; {len(gone)} gone on the first read, {len(prev - set(cur))} still gone on the second read.')
    else:
        notice(f'New references: {P}', f'GATE PASS {len(cur)} read (yesterday {len(prev)}, {len(gone)} gone, known parks present).')
    return cur


for prog, fn, floor in (('pota', pota, 10000), ('kff', kff, 4000), ('sota', sota, 25000)):
    try: cur = fn()
    except Exception as e:  # noqa: BLE001
        notice(f'New references: {prog.upper()}', f'Could not read today ({e}); skipped.'); continue
    old = set(seen.get(prog, []))
    cur = gate(prog, fn, cur, floor)
    if cur is None: continue
    TODAYS[prog] = cur
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
    seen.setdefault('off', {})[prog] = sorted(set(seen[prog]) - set(cur))   # missing today (yesterday's list for the gate)
    if prog == 'pota': seen['locn'] = {**seen.get('locn', {}), **LOCN}
    changed = True
notice('New references', '\n'.join(summary) or 'Nothing read.')

# Oct 23 (Brandon: 'Should we fix the search?'): the Finder's search lists follow the official lists every day
sys.path.insert(0, str(pathlib.Path(__file__).parent))
if TODAYS and not DRY:
    try:
        import kpc_search_lists as SL
        notice('Search lists', json.dumps(SL.update(None if POTA_FAILED else TODAYS.get('pota'), TODAYS.get('kff'), TODAYS.get('sota'))))
        if 'POTA' in SL.GONE:   # a US park POTA took off its list: the card says 'Retired by POTA' (data/retired-refs.json)
            import kpc_retired_refs as RR
            RR.record(SL.GONE['POTA'], set(TODAYS['pota']), 'us', TODAY)
    except Exception as e:  # noqa: BLE001
        notice('Search lists', f'not updated: {e}')

# Oct 23 (Brandon: 'since we pulling daily can that send a message that a park was removed to go ahead and make the
# changes?'): a Kentucky park that left POTA's list is taken off every site list (kpc_retired_sweep.py) and the club is
# told on Discord; one that came back comes off the retired list and is flagged to add back. Only when Kentucky itself
# was read and the Kentucky list looks whole, so a bad download can never remove parks.
RETIRED_NOW, BACK_NOW = [], []
if 'pota' in TODAYS and 'US-KY' not in POTA_FAILED:
    try:
        import kpc_retired_sweep as SW
        kyd = json.loads(pathlib.Path('kpc-ky-data.json').read_text(encoding='utf-8'))
        mine = {p['c']: p['n'] for p in kyd['parks']}
        offky = {r: c for r, c in TODAYS['pota'].items() if 'KY' in c.get('st', [])}
        if len(offky) >= max(150, 0.9 * len(mine)):
            RETIRED_NOW = sorted(set(mine) - set(offky))
            if len(RETIRED_NOW) > RETIRE_MAX * len(mine) and 'pota' not in CONFIRMED:
                # GATE (Oct 28): more than 1% of Kentucky's parks at once needs a second read of Kentucky before anything leaves
                time.sleep(30)
                try:
                    ky2 = {p.get('reference') for p in get('https://api.pota.app/location/parks/US-KY') if isinstance(p, dict)}
                    if len(ky2) < 0.9 * len(offky): raise RuntimeError(f'second read short ({len(ky2)})')
                    RETIRED_NOW = [c for c in RETIRED_NOW if c not in ky2]
                    notice('Retired parks', f'GATE PASS second read of Kentucky: {len(RETIRED_NOW)} still gone')
                except Exception as e:  # noqa: BLE001
                    notice('Retired parks', f'GATE FAIL {len(RETIRED_NOW)} Kentucky parks gone but the confirming read failed ({e}): nothing removed')
                    RETIRED_NOW = []
            BACK_NOW = sorted(set(SW.retired()) & set(offky))
            if BACK_NOW and not DRY: SW.drop_retired(BACK_NOW)
            if RETIRED_NOW and not DRY:
                SW.add_retired([(c, mine[c]) for c in RETIRED_NOW], TODAY)
                fixed = SW.fix(set(SW.retired()))
                notice('Retired parks', 'taken out of: ' + ', '.join(fixed))
            for f, hits in SW.leftovers(set(SW.retired())):
                print(f'::warning title=Retired park still listed::{f}: {", ".join(hits)}', flush=True)
        else:
            notice('Retired parks', f'Kentucky list looked short today ({len(offky)} vs {len(mine)}): nothing removed')
    except Exception as e:  # noqa: BLE001
        notice('Retired parks', f'check failed: {e}')
if RETIRED_NOW or BACK_NOW:
    rl = ['• %s %s' % (c, mine.get(c, '')) for c in RETIRED_NOW]
    bl = ['• %s %s' % (c, TODAYS['pota'][c].get('name', '')) for c in BACK_NOW]
    if RETIRED_NOW and not DRY:
        post_discord('📍 Retired by POTA: ' + ', '.join(RETIRED_NOW),
                     'Parks on the Air took ' + ('this Kentucky park' if len(RETIRED_NOW) == 1 else 'these Kentucky parks') + ' off its list:\n' + '\n'.join(rl) +
                     '\n\nThey are off our maps, guides and lists now. Contacts you already made still count. 73, KPC', SITE + 'kentucky-parks.html')
    if os.environ.get('GITHUB_ACTIONS') and not DRY:
        num = json.loads(gh('issue', 'list', '--label', 'ky-new-lands', '--state', 'open', '--json', 'number', '--limit', '1') or '[]')
        if num:
            body = ''
            if RETIRED_NOW: body += '📍 **Retired by POTA today, taken off every site list by the bot** (map files, outlines, guides, Top 25, search; the guide PDFs reprint on Monday):\n\n' + '\n'.join(rl) + '\n\n'
            if BACK_NOW: body += '↩️ **Back on POTA\'s list today** (taken off data/ky-retired.json; add it back to kpc-ky-data.json and the guides, see .claude/build/mapfiles/retired-parks.md):\n\n' + '\n'.join(bl)
            gh('issue', 'comment', str(num[0]['number']), '--body-file', '-', input_text=body)
    if RETIRED_NOW and os.environ.get('GITHUB_ACTIONS') and not DRY:
        pathlib.Path('/tmp/kpc-reprint').write_text('1')   # the workflow reprints the guide PDFs after it has saved

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
