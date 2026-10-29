#!/usr/bin/env python3
"""Three small posts for the club, in one job (Brandon Oct 20: 'park of the week but leave out the bands that
work there ...maybe tell a brief history if it has it or why it is a place to see and lonely parks'; and
'event weather just for kpc events').

  park     Park of the Week. A Kentucky park worth going to see, with a short note about why. The note comes
           from data/kpc-park-stories.json and NOTHING ELSE - if a park has no entry there it is never
           featured, so the bot cannot make up a history in the club's name. No bands, no antenna advice:
           Brandon asked for the place, not the radio.
  lonely   The references hardly anybody has activated, from the POTA figures in kpc-top25.json.
  weather  The forecast for one of the CLUB'S OWN events (data/kpc-club-events.json) when it is close enough
           to be useful. Never for somebody else's hamfest, never for a POTA weekend.

NOT A LEAGUE TABLE. There are four members and they all get out, so nothing here counts anybody's activations,
ranks members or asks why somebody has not been out lately (Brandon Oct 20: 'I dont want to guilt someone for
not activating').

WHEN: run daily. Park of the Week goes out on POST_DAY (Thursday), lonely parks on LONELY_DAY (Monday), and the
weather only in the few days before a club event. Anything already sent is remembered in the state file, so a
late or repeated run never posts twice.

Secrets: KPC_PARKS_WEBHOOK / KPC_GENERAL_WEBHOOK / KPC_CAMPOUT_WEBHOOK / KPC_DISCORD_WEBHOOK, and
FB_PAGE_ID + FB_PAGE_TOKEN for the Facebook side of Park of the Week. DRY_RUN=1 prints instead of posting.
ONLY=park|lonely|weather|contests forces one of them, for testing (contests = the busy-bands post for the coming weekend, sent now).
"""
import datetime
import json
import os
import pathlib
import random
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

SITE = 'https://kentuckyportableclub.github.io/KPC-Links/'
INFO = ('ℹ️ Maps and park info are a planning aid, not a guarantee. Always check the official agency map and rules before you go. '
        'About our information: ' + SITE + 'kpc-about-info.html')      # house rule: posts with park details carry it
STATE_F = pathlib.Path('data/kpc-club-posts-state.json')
UA = {'User-Agent': 'KPC club bot (kentuckyportableclub.github.io)'}
DRY = os.environ.get('DRY_RUN') == '1'
ONLY = (os.environ.get('ONLY') or '').strip().lower()
POST_DAY = 3          # Thursday (Monday is 0)
LONELY_DAY = 0        # Monday
WEATHER_DAYS = 4      # start posting a forecast this many days out
FB_ID = (os.environ.get('FB_PAGE_ID') or '').strip()
FB_TOKEN = (os.environ.get('FB_PAGE_TOKEN') or '').strip()


def hook(*names):
    for n in names:
        v = ((os.environ.get(n) or '').strip().split() or [''])[0]
        if v.startswith('https://'):
            return v
    return ''


def notice(msg):
    print(f"::notice title=Club posts::{str(msg)[:800]}", flush=True)


def load(p, d):
    try:
        return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
    except Exception:  # noqa: BLE001
        return d


def http(url, data=None, headers=None, timeout=45):
    try:
        req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:  # noqa: BLE001
        return 0, str(e)


def to_discord(where, title, body, colour=0x2E7D32, url=None):
    h = hook(*where)
    if not h:
        notice('No webhook for this post; nothing sent to Discord.')
        return False
    embed = {'title': title[:250], 'color': colour, 'description': body[:4000]}
    if url:
        embed['url'] = url
    c, r = http(h, json.dumps({'username': 'KPC-N4KPC-Bot', 'allowed_mentions': {'parse': []},
                               'embeds': [embed]}).encode(), {'Content-Type': 'application/json'})
    if c >= 300:
        notice(f'Discord said HTTP {c}: {r[:160]}')
        return False
    return True


def to_facebook(message, link=None):
    if not (FB_ID and FB_TOKEN):
        notice('No Facebook secrets; skipped Facebook.')
        return False
    q = {'access_token': FB_TOKEN, 'message': message.replace('**', '')}
    if link:
        q['link'] = link
    c, r = http(f'https://graph.facebook.com/{FB_ID}/feed', urllib.parse.urlencode(q).encode())
    if c >= 300:
        notice(f'Facebook said HTTP {c}: {r[:160]}')
        return False
    return True


def on_hold():
    """References to keep out of 'go and activate this' suggestions (data/kpc-post-holds.json)."""
    return {str(h.get('ref')).upper() for h in (load('data/kpc-post-holds.json', {}).get('hold') or [])
            if h.get('ref')}


def park_by_ref():
    ky = load('kpc-ky-data.json', {})
    return {p['c']: p for p in (ky.get('parks') or [])}


# ------------------------------------------------------------------ park of the week
def park_of_the_week(state):
    stories = (load('data/kpc-park-stories.json', {}).get('parks') or [])
    if not stories:
        notice('No park stories file; nothing to feature.')
        return False
    done = state.get('featured') or []
    left = [s for s in stories if s.get('ref') not in done] or stories   # all used once -> start again
    if left is stories and done:
        done = []
        notice('Every park with a story has been featured; starting the list again.')
    pool = [x for x in left if x.get('first')] or left        # state parks and national sites first
    pick = random.Random(datetime.date.today().isoformat()).choice(pool)
    parks = park_by_ref()
    p = parks.get(pick['ref'])
    if not p:
        notice(f"{pick['ref']} is in the stories file but not in kpc-ky-data.json; skipped.")
        return False
    stats = {r[0]: (r[1], r[2]) for r in (load('kpc-top25.json', {}).get('all') or [])
             if isinstance(r, list) and len(r) >= 3}
    conds = {c['ref']: c for c in (load('kpc-conditions.json', {}).get('items') or [])}

    L = [pick['story'], '']
    bits = [x for x in (p.get('t'), (str(p.get('co')) + ' County') if p.get('co') else None) if x]
    if bits:
        L.append('📍 ' + ' · '.join(bits))
    n = stats.get(pick['ref'])
    if n:
        L.append('📻 ' + ('nobody has activated it yet' if not n[0]
                          else f"{n[0]:,} activation{'s' if n[0] != 1 else ''} so far"))
    c = conds.get(pick['ref'])
    if c:
        L.append(f"⚠️ **Before you go:** {str(c.get('details'))[:200]}")
    L.append('')
    L.append(f"[Map, boundary and parking]({SITE}kpc-park-control.html?ref={pick['ref']}) · "
             f"[What people have noted]({SITE}kpc-park-notes.html?ref={pick['ref']})"
             + (f" · [The park's own page]({p['web']})" if p.get('web') else ''))
    body = '\n'.join(L)
    title = f"Park of the Week — {p['n']} ({pick['ref']})"

    if DRY:
        print(f'--- {title} ---\n{body}\n')
        return True
    ok = to_discord(('KPC_PARKS_WEBHOOK', 'KPC_GENERAL_WEBHOOK', 'KPC_DISCORD_WEBHOOK'),
                    title, body, 0x2E7D32, f"{SITE}kpc-park-control.html?ref={pick['ref']}")
    fb = [title, '', pick['story'], '']
    if bits:
        fb.append(' · '.join(bits))
    fb.append('')
    fb.append('Map, boundary and parking on our Park Control page.')
    to_facebook('\n'.join(fb), f"{SITE}kpc-park-control.html?ref={pick['ref']}")
    if ok:
        state['featured'] = (done + [pick['ref']])[-40:]
    return ok


# ------------------------------------------------------------------ WMA closure heads-up (Wednesday before)
def _wma_scan(sat, sun, asks):
    """Short (10 days or less) quota-hunt closures in chat 2's 'hc-' items that touch this Sat-Sun.
    An item whose dates can't be read is never guessed: it goes to `asks` for the staff room."""
    names = {c: p.get('n') for c, p in park_by_ref().items()}
    rows = []
    for it in (load('kpc-conditions.json', {}).get('items') or []):
        if not str(it.get('id', '')).startswith('hc-'):
            continue
        try:
            a = datetime.date.fromisoformat(str(it['id'])[-10:])                       # hc-US-4687-2026-11-07
            b = datetime.date.fromisoformat(str(it.get('expires'))[:10]) - datetime.timedelta(days=1)
            if b < a:
                raise ValueError('ends before it starts')
        except (ValueError, KeyError, TypeError):
            asks.append(it)
            continue
        if (b - a).days > 10:        # season-long closures stay on the park cards; this post is the one-weekend quota hunts
            continue
        if a <= sun and b >= sat:
            rows.append((names.get(it.get('ref')) or it.get('name') or it.get('ref'), a, b, it))
    rows.sort(key=lambda r: str(r[0]))
    return rows


def _fmt(d):
    return f'{d:%b} {d.day}'


def _wma_line(n, a, b, it, md=True):
    """Whole WMA: '• X: Nov 7 to Nov 8'. Part of one (Brandon Oct 27, G3): '• Part of X (Tract 1A) is closed: ...',
    the part named in KDFWR's own words."""
    span = _fmt(a) if a == b else f'{_fmt(a)} to {_fmt(b)}'
    first = re.sub(r'^[^:]*?:\s*[A-Z][a-z]{2}[^:]*?:\s*', '', str(it.get('details') or ''), count=1).split(';')[0].strip()
    part = re.match(r'(?i)^(.{3,80}?)\s+(?:is |are )?closed\b', first)
    nm = f'**{n}**' if md else n
    quote = first.rstrip('.')[:160]
    if quote.count('(') > quote.count(')'):        # the record split inside brackets: drop the broken bracket
        quote = quote[:quote.rfind('(')].rstrip(' ,')
    if part and re.search(r'(?i)\b(unit|tract|area|zone|section|portion|field|parts? of)\b', part.group(1)):
        line = f'• Part of {nm} ({part.group(1).strip()}) is closed: {span}'
    else:
        line = f'• {nm}: {span}'
    if quote:                # G9 (Brandon Oct 27): Fish & Wildlife's own words, not our template
        line += f' — KDFWR: “{quote}”'
    if it.get('link'):
        line += f" · [KDFWR page]({it['link']})" if md else f" · {it['link']}"
    return line


def _staff(title, body):
    """Staff room only (KPC_ADMIN_WEBHOOK); never falls back to a public room. No email."""
    return to_discord(('KPC_ADMIN_WEBHOOK',), title, body, 0x8a8a8a) if not DRY else print(f'--- STAFF: {title} ---\n{body}\n')


def wma_closures(state, today, force=False, wait=False):
    """Wednesday: which Kentucky WMAs are closed to non-hunters THIS coming weekend (Brandon Oct 25), from chat 2's
    'hc-' items in kpc-conditions.json. Rules (Brandon Oct 27): part-closures worded 'Part of X (unit) is closed';
    an item with unreadable dates is asked about in the staff room, never guessed; when the dates change after the
    Wednesday post, ONE short correction goes out, only before that weekend starts; on a holiday Wednesday the
    heads-up waits for the afternoon run so the two posts are hours apart. Never posts twice; no closures = no post."""
    did = False
    asks = []
    sent = state.setdefault('wma_sent', {})            # weekend (Saturday) -> {item id: 'start|end'} as posted
    # 1) corrections for a weekend already announced (any day, only before that weekend starts)
    for key in list(sent):
        sat = datetime.date.fromisoformat(key)
        if today >= sat:
            sent.pop(key, None)
            continue
        rows = _wma_scan(sat, sat + datetime.timedelta(days=1), asks)
        cur = {it['id']: f'{a}|{b}' for _, a, b, it in rows}
        if cur == sent[key]:
            continue
        old = sent[key]
        L = [f'Correction to the WMA closures for {_fmt(sat)}-{(sat + datetime.timedelta(days=1)).day} (KDFWR changed the list):', '']
        for n, a, b, it in rows:
            if it['id'] not in old:
                L.append(_wma_line(n, a, b, it) + ' (added)')
            elif old[it['id']] != cur[it['id']]:
                L.append(_wma_line(n, a, b, it) + ' (new dates)')
        names = {c: p.get('n') for c, p in park_by_ref().items()}
        for iid in old:
            if iid not in cur:
                ref = re.sub(r'^hc-|-\d{4}-\d{2}-\d{2}$', '', iid)
                L.append(f'• {names.get(ref) or ref}: no longer listed for this weekend')
        L += ['', 'Check the KDFWR page before you drive.', INFO]
        title = f'Correction: WMA closures {_fmt(sat)}-{(sat + datetime.timedelta(days=1)).day}'
        if DRY:
            print(f'--- {title} ---\n' + '\n'.join(L) + '\n')
        else:
            if to_discord(('KPC_PARKS_WEBHOOK', 'KPC_GENERAL_WEBHOOK', 'KPC_DISCORD_WEBHOOK'), title, '\n'.join(L), 0xE65100):
                to_facebook('\n'.join([title, ''] + [re.sub(r'\[KDFWR page\]\((.*?)\)', r'\1', x.replace('**', '')) for x in L[2:]]))
                sent[key] = cur
        did = True
    # 2) the Wednesday heads-up
    if force or today.weekday() == 2:
        sat = today + datetime.timedelta(days=(5 - today.weekday()) % 7 or 7)
        sun = sat + datetime.timedelta(days=1)
        key = sat.isoformat()
        if wait and not force:
            notice('Holiday post went out this morning: the WMA heads-up waits for the afternoon run.')
        elif force or state.get('wma_for') != key:
            rows = _wma_scan(sat, sun, asks)
            if not rows:
                notice(f'No WMA closures for {_fmt(sat)}-{sun.day}; no heads-up post.')
            else:
                L = [f'Kentucky WMA hunt closures this weekend, {_fmt(sat)}-{sun.day} (in Fish & Wildlife\'s own words):', '']
                L += [_wma_line(n, a, b, it) for n, a, b, it in rows]
                L += ['', 'Hunters may be in the woods: wear blaze orange if you are anywhere near a hunt, and check the '
                          'KDFWR page before you drive.', INFO]
                title = f'WMA closures this weekend ({_fmt(sat)}-{sun.day})'
                if DRY:
                    print(f'--- {title} ---\n' + '\n'.join(L) + '\n')
                    did = True
                else:
                    ok = to_discord(('KPC_PARKS_WEBHOOK', 'KPC_GENERAL_WEBHOOK', 'KPC_DISCORD_WEBHOOK'), title, '\n'.join(L),
                                    0xE65100, f'{SITE}kpc-spots.html')
                    to_facebook('\n'.join([title, ''] + [re.sub(r'\[KDFWR page\]\((.*?)\)', r'\1', x.replace('**', '')) for x in L[2:]]))
                    if ok:
                        state['wma_for'] = key
                        sent[key] = {it['id']: f'{a}|{b}' for _, a, b, it in rows}
                        did = True
    # 3) items with dates we can't read: ask the staff room once each (never guessed, never public)
    asked = state.setdefault('wma_asked', [])
    new = [it for it in {i.get('id'): i for i in asks}.values() if it.get('id') not in asked]
    if new:
        _staff('WMA closure: dates unclear, not posted',
               'These KDFWR closure items have dates the bot could not read, so they were left out of the heads-up. '
               'Check them and post by hand if needed:\n' + '\n'.join(f"• {it.get('id')}: {str(it.get('details'))[:200]} {it.get('link', '')}" for it in new))
        if not DRY:
            state['wma_asked'] = (asked + [it.get('id') for it in new])[-200:]
    return did


# ------------------------------------------------------------------ holiday post (HQ Oct 26, Brandon: GO for Halloween only)
def _valid(y, m, d):
    try:
        datetime.date(y, m, d)
        return True
    except ValueError:
        return False


def _rule_date(rule, year):
    """'MM-DD' is handled by the caller. Rules: easter | 'last monday of 05' | 'second sunday of 05'."""
    r = str(rule).strip().lower()
    if r == 'easter':
        a, b, c = year % 19, year // 100, year % 100
        d, e = b // 4, b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i, k = c // 4, c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        mo, da = divmod(h + l - 7 * m + 114, 31)
        return datetime.date(year, mo, da + 1)
    fw = re.fullmatch(r'(first|second|third|fourth|last) full weekend of (\d\d)', r)
    if fw:                   # ARRL Field Day = the fourth FULL weekend of June: its Saturday (Sunday in the same month)
        mo = int(fw.group(2))
        sats = [datetime.date(year, mo, d) for d in range(1, 31) if _valid(year, mo, d) and datetime.date(year, mo, d).weekday() == 5
                and (datetime.date(year, mo, d) + datetime.timedelta(days=1)).month == mo]
        n = fw.group(1)
        return sats[-1] if n == 'last' else sats[['first', 'second', 'third', 'fourth'].index(n)]
    m = re.fullmatch(r'(first|second|third|fourth|last) (monday|tuesday|wednesday|thursday|friday|saturday|sunday) of (\d\d)', r)
    if not m:
        return None            # e.g. 'fourth full weekend of 06' (Field Day): not wired yet, never posts
    n, wd, mo = m.group(1), ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].index(m.group(2)), int(m.group(3))
    days = [datetime.date(year, mo, 1) + datetime.timedelta(days=i) for i in range(31)]
    days = [d for d in days if d.month == mo and d.weekday() == wd]
    return days[-1] if n == 'last' else days[['first', 'second', 'third', 'fourth'].index(n)]


def _multipart(fields, fname, data):
    b = 'kpcb' + os.urandom(8).hex()
    out = b''
    for k, v in fields.items():
        out += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    out += (f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="{fname}"\r\n'
            f'Content-Type: image/jpeg\r\n\r\n').encode() + data + f'\r\n--{b}--\r\n'.encode()
    return out, {'Content-Type': 'multipart/form-data; boundary=' + b}


def holiday_post(state, today, force=False):
    """The morning of a holiday: ONE post, the -post.jpg picture + the text in data/holidays.json, to Discord + the
    Facebook Page. Behind a switch: only holidays listed in data/holiday-post-go.json ({"go": ["halloween"]}) post.
    Never emails. Never twice (state 'holidays_done')."""
    go = {str(x) for x in (load('data/holiday-post-go.json', {}).get('go') or [])}
    done = state.get('holidays_done') or []
    for h in (load('data/holidays.json', {}).get('holidays') or []):
        try:
            if h.get('date'):
                mo, da = h['date'].split('-')
                d = datetime.date(today.year, int(mo), int(da))
            else:
                d = _rule_date(h.get('rule'), today.year)
        except (ValueError, TypeError):
            d = None
        if not d or d != today or not ('all' in go or h['id'] in go):
            continue
        key = f"{h['id']}-{today.year}"
        if key in done and not force:
            return False
        img = pathlib.Path(h.get('post_img') or '')
        text = str(h.get('post') or '').strip()
        if not text or not img.is_file():
            notice(f"{h['id']}: the post text or picture is missing; nothing posted.")
            return False
        data = img.read_bytes()
        title = h.get('name') or h['id']
        if DRY:
            print(f'--- {title} ---\n{text}\n(picture {img}, {len(data)//1024} KB)\n')
            return True
        ok = False
        dh = hook('KPC_GENERAL_WEBHOOK', 'KPC_DISCORD_WEBHOOK', 'KPC_PARKS_WEBHOOK')
        if dh:
            body, hd = _multipart({'payload_json': json.dumps({'username': 'KPC-N4KPC-Bot', 'content': text,
                                  'allowed_mentions': {'parse': []}})}, img.name, data)
            c, r = http(dh, body, hd)
            ok = c < 300
            if not ok:
                notice(f'Discord said HTTP {c}: {r[:160]}')
        else:
            notice('No webhook for the holiday post; nothing sent to Discord.')
        if FB_ID and FB_TOKEN:
            body, hd = _multipart({'access_token': FB_TOKEN, 'caption': text, 'published': 'true'}, img.name, data)
            body = body.replace(b'name="file"', b'name="source"')
            c, r = http(f'https://graph.facebook.com/{FB_ID}/photos', body, hd)
            if c >= 300:
                notice(f'Facebook said HTTP {c}: {r[:160]}')
            ok = ok or c < 300
        else:
            notice('No Facebook secrets; skipped Facebook.')
        if ok:
            state['holidays_done'] = (done + [key])[-30:]
            state['holiday_on'] = today.isoformat()
        return ok
    return False


# ------------------------------------------------------------------ the quiet ones
def lonely_parks(state):
    rows = (load('kpc-top25.json', {}).get('acts') or [])
    if not rows:
        notice('No POTA figures yet; nothing to post.')
        return False
    held = on_hold()
    live = {x['c'] for x in (load('kpc-ky-data.json', {}).get('parks') or [])}
    gone = [r['c'] for r in rows if r.get('c') not in live]
    if gone:
        notice('Left out, no longer on the official list: ' + ', '.join(gone[:6]))
    rows = [r for r in rows
            if str(r.get('c', '')).upper() not in held and r.get('c') in live]
    if held:
        notice(f'Left out {len(held)} reference(s) on hold: ' + ', '.join(sorted(held)))
    if not rows:
        notice('Everything quiet is on hold; no post.')
        return False
    parks = park_by_ref()
    L = ["Nobody has to go to any of these. They are just sitting there, and somebody has to be first.", '']
    for r in rows[:6]:
        p = parks.get(r['c']) or {}
        a = r.get('a') or 0
        L.append(f"• **{r['c']}** {r.get('n')} ({r.get('co')} Co.) — "
                 + ('never activated' if not a else f"{a} activation{'s' if a != 1 else ''}")
                 + (f" · {p.get('t')}" if p.get('t') else ''))
    L.append('')
    L.append(f"Boundaries, parking and access notes for every one of them: {SITE}kpc-park-control.html")
    body = '\n'.join(L)
    if DRY:
        print(f'--- The quiet ones ---\n{body}\n')
        return True
    return to_discord(('KPC_PARKS_WEBHOOK', 'KPC_GENERAL_WEBHOOK', 'KPC_DISCORD_WEBHOOK'),
                      'The quiet ones', body, 0x6D4C41, f'{SITE}kpc-park-control.html')


# ------------------------------------------------------------------ weather for a club event
WX_WORDS = {'rain': '🌧', 'shower': '🌧', 'storm': '⛈', 'thunder': '⛈', 'snow': '🌨', 'sleet': '🌨',
            'sunny': '☀️', 'clear': '☀️', 'cloud': '☁️', 'fog': '🌫', 'wind': '💨'}


def forecast(la, lo):
    """National Weather Service, no key needed. Returns a list of (name, detail) or None."""
    c, r = http(f'https://api.weather.gov/points/{la:.4f},{lo:.4f}',
                headers={'Accept': 'application/geo+json'})
    if c != 200:
        notice(f'Weather service said HTTP {c} for the grid lookup.')
        return None
    try:
        url = json.loads(r)['properties']['forecast']
    except Exception:  # noqa: BLE001
        return None
    c, r = http(url, headers={'Accept': 'application/geo+json'})
    if c != 200:
        notice(f'Weather service said HTTP {c} for the forecast.')
        return None
    try:
        return [(p.get('name'), p.get('detailedForecast'), p.get('shortForecast'))
                for p in json.loads(r)['properties']['periods']]
    except Exception:  # noqa: BLE001
        return None


def event_weather(state, today):
    evs = (load('data/kpc-club-events.json', {}).get('events') or [])
    parks = park_by_ref()
    sent = state.get('weather') or {}
    for e in evs:
        try:
            start = datetime.date.fromisoformat(str(e.get('start')))
        except Exception:  # noqa: BLE001
            continue
        days = (start - today).days
        if days < 0 or days > WEATHER_DAYS:
            continue
        if sent.get(e.get('id')) == today.isoformat():
            continue
        la, lo = e.get('lat'), e.get('lon')
        if la is None and e.get('ref'):
            p = parks.get(e['ref']) or {}
            la, lo = p.get('la'), p.get('lo')
        if la is None:
            notice(f"No place to get a forecast for {e.get('name')}; skipped.")
            continue
        per = forecast(float(la), float(lo))
        if not per:
            return False
        when = ('today' if days == 0 else 'tomorrow' if days == 1 else f'in {days} days')
        L = [f"**{e.get('name')}** starts {when} at {e.get('where') or 'the park'}.", '']
        for name, detail, short in per[:4]:
            icon = next((v for k, v in WX_WORDS.items() if k in str(short).lower()), '•')
            L.append(f"{icon} **{name}** — {detail}")
        L.append('')
        L.append('Forecast from the National Weather Service. Pack for the worst line in it.')
        if e.get('url'):
            L.append(e['url'])
        body = '\n'.join(L)
        if DRY:
            print(f'--- weather: {e.get("name")} ---\n{body}\n')
            return True
        ok = to_discord(('KPC_CAMPOUT_WEBHOOK', 'KPC_GENERAL_WEBHOOK', 'KPC_DISCORD_WEBHOOK'),
                        f"Weather for {e.get('name')}", body, 0x1565C0, e.get('url'))
        if ok:
            sent[e['id']] = today.isoformat()
            state['weather'] = sent
        return ok
    return None          # nothing close enough; not a failure


# ------------------------------------------------------------------ busy bands this weekend
def _ct(z):
    from zoneinfo import ZoneInfo
    t = datetime.datetime.strptime(z, '%Y-%m-%dT%H:%MZ').replace(tzinfo=datetime.timezone.utc)
    return t, t.astimezone(ZoneInfo('America/Chicago'))


def _when(c):
    s, sc = _ct(c['segs'][0][0]); e, ec = _ct(c['segs'][-1][1])
    f = lambda d: d.strftime('%a %-I:%M %p').replace(':00 ', ' ')
    return f"{f(sc)} – {f(ec)} Central ({s.strftime('%H%MZ %a')} – {e.strftime('%H%MZ %a')})"


def busy_bands(state, today, force=False):
    """Oct 23 (Brandon: 'send out messages prepare for busy bands this weekend like couple days before and list what
    contest it is'): on Thursday, the big contests + QSO parties of the coming weekend, in ONE post (Discord + the
    Facebook Page). The Kentucky QSO Party also gets its own reminder a week ahead. Contests come from the same rules as
    the Events calendar (kpc_contests.big()) plus this week's state QSO parties near Kentucky from the WA7BNM feed."""
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    import kpc_contests as KC
    sat = today + datetime.timedelta(days=(5 - today.weekday()) % 7) if today.weekday() != 6 else today - datetime.timedelta(days=1)
    lo = datetime.datetime(sat.year, sat.month, sat.day, tzinfo=datetime.timezone.utc) - datetime.timedelta(hours=12)
    hi = lo + datetime.timedelta(days=2, hours=24)
    inwin = lambda c: lo <= _ct(c['segs'][0][0])[0] < hi
    L = [c for c in KC.big() if inwin(c) and 'vhf' not in c['name'].lower()]
    try:
        wk = load('kpc-contests.json', {}).get('week', [])
        near = re.compile(r'(kentucky|tennessee|ohio|indiana|illinois|missouri|west virginia|virginia) qso party', re.I)
        have = {c['name'].lower() for c in L}
        L += [dict(c, exch=c.get('exch') or KC.exch_for(c['name'])) for c in wk if near.search(c['name']) and inwin(c) and c['name'].lower() not in have]
    except Exception as e:  # noqa: BLE001
        notice(f'busy bands: WA7BNM list not read ({e})')
    out = []
    key = 'busy_' + sat.isoformat()
    if L and (force or not state.get(key)):
        L.sort(key=lambda c: c['segs'][0][0])
        lines = []
        for c in L:
            modes = ', '.join({'PHONE': 'SSB'}.get(m, m) for m in c.get('modes', [])) or ''
            lines.append(f"**{c['name']}**" + (f' · {modes}' if modes else '') + f"\n{_when(c)}" +
                         (f"\nIf you work them, give: {c['exch']}" if c.get('exch') else '') + f"\nRules: {c['url']}")
        body = ('\n\n'.join(lines) + '\n\nHeading to a park? Contest weekends mean fast contacts: spot yourself early and find a clear '
                'frequency before you call CQ. Want quiet? 30, 17 and 12 m never have contests. Full list on our Events page. 73, KPC')
        title = '📻 Busy bands this weekend'
        link = SITE + 'events.html#contests'
        if DRY:
            notice(f'(dry run) {title}\n{body}')
        else:
            d = to_discord(('KPC_GENERAL_WEBHOOK', 'KPC_DISCORD_WEBHOOK'), title, body, 0xD5A63A, link)
            f = to_facebook(f'{title}\n\n{body}', link)
            notice(f'busy bands: Discord {"sent" if d else "not sent"}, Facebook {"sent" if f else "not sent"}')
        state[key] = today.isoformat(); out.append('busy bands')
    # the Kentucky QSO Party, one week ahead
    for c in KC.big():
        if 'kentucky qso' not in c['name'].lower(): continue
        s0 = _ct(c['segs'][0][0])[0].date(); k = 'kyqp_' + s0.isoformat()
        if 6 <= (s0 - today).days <= 8 and not state.get(k):
            title = '📻 Kentucky QSO Party is one week out'
            body = (f"{_when(c)}\nKentucky stations give RS(T) + county, so a park in a rare county is gold that day. "
                    f"Plan a park, check the county, and get on the air!\nRules: {c['url']}\n73, KPC")
            if DRY: notice(f'(dry run) {title}\n{body}')
            else: to_discord(('KPC_GENERAL_WEBHOOK', 'KPC_DISCORD_WEBHOOK'), title, body, 0xD5A63A, SITE + 'events.html#contests'); to_facebook(f'{title}\n\n{body}', SITE + 'events.html#contests')
            state[k] = today.isoformat(); out.append('KY QSO Party reminder')
    return out


def main():
    today = datetime.date.fromisoformat(os.environ['HOLIDAY_DATE']) if os.environ.get('HOLIDAY_DATE') else datetime.date.today()   # HOLIDAY_DATE: tests only
    state = load(STATE_F, {})
    did = []

    want_park = ONLY == 'park' or (not ONLY and today.weekday() == POST_DAY
                                   and state.get('park_on') != today.isoformat())
    want_lonely = ONLY == 'lonely' or (not ONLY and today.weekday() == LONELY_DAY
                                       and state.get('lonely_on') != today.isoformat())
    want_wx = ONLY == 'weather' or not ONLY
    if ONLY in ('wma', 'holiday'):
        want_wx = False

    if want_park and park_of_the_week(state):
        state['park_on'] = today.isoformat()
        did.append('Park of the Week')
    if want_lonely and lonely_parks(state):
        state['lonely_on'] = today.isoformat()
        did.append('the quiet ones')
    if ONLY in ('contests', 'busy') or (not ONLY and today.weekday() == POST_DAY):
        did += busy_bands(state, today, force=ONLY in ('contests', 'busy'))
    if holiday_post(state, today, force=ONLY == 'holiday'):
        did.append('holiday post')
    try:
        from zoneinfo import ZoneInfo
        ct_hour = datetime.datetime.now(ZoneInfo('America/Chicago')).hour
    except Exception:  # noqa: BLE001
        ct_hour = 9
    wait = state.get('holiday_on') == today.isoformat() and ct_hour < 12     # G6: holiday + closure posts hours apart
    # PAUSE (Brandon Oct 29 10:18 AM): no WMA closure heads-up posts before 2026-11-05.
    if today.isoformat() < '2026-11-05':
        notice('WMA closure heads-up paused until 2026-11-05 (Brandon): closures are being fixed.')
    elif wma_closures(state, today, force=ONLY == 'wma', wait=wait):
        did.append('WMA closure heads-up')
    if want_wx:
        r = event_weather(state, today)
        if r:
            did.append('event weather')

    notice('Posted: ' + ', '.join(did) if did else 'Nothing due today.')
    if not DRY:
        STATE_F.parent.mkdir(parents=True, exist_ok=True)
        STATE_F.write_text(json.dumps(state, indent=1) + '\n', encoding='utf-8')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:  # noqa: BLE001
        notice(f'stopped early: {type(e).__name__}: {str(e)[:300]}')
        sys.exit(0)          # never fail the job: a failed run emails Brandon
