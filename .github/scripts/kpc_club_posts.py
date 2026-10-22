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
ONLY=park|lonely|weather forces one of them, for testing.
"""
import datetime
import json
import os
import pathlib
import random
import sys
import urllib.error
import urllib.parse
import urllib.request

SITE = 'https://kentuckyportableclub.github.io/KPC-Links/'
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
    c, r = http(h, json.dumps({'username': 'KPC', 'allowed_mentions': {'parse': []},
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
    pick = random.Random(datetime.date.today().isoformat()).choice(left)
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


def main():
    today = datetime.date.today()
    state = load(STATE_F, {})
    did = []

    want_park = ONLY == 'park' or (not ONLY and today.weekday() == POST_DAY
                                   and state.get('park_on') != today.isoformat())
    want_lonely = ONLY == 'lonely' or (not ONLY and today.weekday() == LONELY_DAY
                                       and state.get('lonely_on') != today.isoformat())
    want_wx = ONLY == 'weather' or not ONLY

    if want_park and park_of_the_week(state):
        state['park_on'] = today.isoformat()
        did.append('Park of the Week')
    if want_lonely and lonely_parks(state):
        state['lonely_on'] = today.isoformat()
        did.append('the quiet ones')
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
