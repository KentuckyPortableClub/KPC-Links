#!/usr/bin/env python3
"""The club's answering bot for Discord (Brandon Oct 21: 'is they a discord bot we can ask questions and it answer?').

It reads the club's rooms and answers the things it can answer FOR CERTAIN, from the club's own files:

  * a park reference anywhere in a message (US-1271, K-1271, KFF-4521, W4K/BR-001) -> that park's card:
    name, county, kind of place, any live warning, nearest campground, and links to Park Control and Park Notes
  * the handful of questions that come up again and again (campout, joining, the guides, the map, park notes,
    campgrounds, events, who is on the air, contact, videos)
  * "who is on the air" -> the POTA spots we already hold

There is no language model in it. Every answer is built from kpc-ky-data.json, kpc-conditions.json and the rest
of the site's own data, so it cannot invent a park, a date or a rule in the club's name. If it is not sure, it
says nothing at all: silence is better than a confident wrong answer.

HOW FAST: these bots run on a timer, not a live connection, so an answer arrives within a few minutes rather
than instantly. It says so the first time it answers in a room.

PRIVACY: this repo is public. Only short one-way fingerprints of message ids are saved, never names or text.

Needs DISCORD_BOT_TOKEN, and the bot must have View Channel, Read Message History and Send Messages in the rooms
listed in data/discord-watch.json. DRY_RUN=1 prints the answers instead of posting them.
"""
import datetime
import hashlib
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

API = 'https://discord.com/api/v10/'
SITE = 'https://kentuckyportableclub.github.io/KPC-Links/'
CONF_F = pathlib.Path('data/discord-watch.json')
STATE_F = pathlib.Path('data/discord-ask-state.json')
TOKEN = (os.environ.get('DISCORD_BOT_TOKEN') or '').strip()
DRY = os.environ.get('DRY_RUN') == '1'
UA = {'User-Agent': 'KPC club bot (kentuckyportableclub.github.io)'}
MAX_REPLIES = 6          # never flood a room


def notice(msg):
    print(f"::notice title=Ask::{str(msg)[:800]}", flush=True)


def call(path, method='GET', body=None):
    h = {**UA, 'Authorization': 'Bot ' + TOKEN}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        h['Content-Type'] = 'application/json'
    try:
        req = urllib.request.Request(API + path, data=data, headers=h, method=method)
        with urllib.request.urlopen(req, timeout=60) as r:
            t = r.read().decode('utf-8', 'replace')
            return json.loads(t) if t.strip() else {}
    except urllib.error.HTTPError as e:
        return {'_error': f'HTTP {e.code} {e.read().decode("utf-8", "replace")[:160]}'}
    except Exception as e:  # noqa: BLE001
        return {'_error': str(e)[:160]}


def load(p, d):
    try:
        return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
    except Exception:  # noqa: BLE001
        return d


def fingerprint(s):
    return hashlib.sha256(('kpc-ask:' + str(s)).encode()).hexdigest()[:16]


# ---------------------------------------------------------------- what it knows
REF = re.compile(r'\b(?:US|K)-(\d{3,5})\b|\b(KFF-\d{1,4})\b|\b(W4K/[A-Z]{2}-\d{3})\b', re.I)

# Only ever answer something that is actually being asked. Members post park numbers all day long - spots,
# "worked US-1271 this morning", plans - and a bot that fires a park card at every one of those is a nuisance
# within a day (Brandon Oct 18: 'all your bots burning up my email'; same manners apply in the rooms).
ASKING = re.compile(r'\?|^\s*(kpc|bot)\b|\b(anyone|anybody|does any|how do i|how can i|where (is|do|can)|'
                    r'when (is|do|does)|what (is|are|do|about)|which|any (idea|info|notes|good|one been)|'
                    r'worth it|recommend|tell me|looking for|need (help|advice|info)|is there|are there|'
                    r'anything on|anything going|how (is|are) the|any (park|summit|ref|contest)|'
                    r'(park|summit)s? (near|around|close|in)\b)', re.I)

# Kentucky places people say that the shared town list does not carry. Kept here rather than added to
# kpc-ky-towns.json, which the trip planners read and which should stay as it is.
EXTRA_TOWNS = [['Berea', 37.5689, -84.2963], ['Corbin', 36.9487, -84.0969], ['Middlesboro', 36.6081, -83.7163],
               ['Florence', 38.9989, -84.6266], ['Erlanger', 39.0167, -84.6008], ['Fort Thomas', 39.0750, -84.4472],
               ['Oak Grove', 36.6648, -87.4411], ['Mount Washington', 37.9497, -85.5447],
               ['St. Matthews', 38.2545, -85.6413], ['Shelby County', 38.2120, -85.2236],
               ['Cave City', 37.1370, -85.9572], ['Berlin', 38.4570, -84.2400], ['Union', 38.9456, -84.6808],
               ['Lebanon Junction', 37.8342, -85.7325], ['Olive Hill', 38.3017, -83.1741],
               ['Jenkins', 37.1731, -82.6335], ['Hazel Green', 37.7859, -83.4149],
               ['Slade', 37.7901, -83.6865], ['Dawson Springs', 37.1670, -87.6919],
               ['Grand Rivers', 37.0106, -88.4792]]

FAQ = [
    (r'(?i)\bcampout\b|\bcamp out\b|taylorsville.*(when|date)|2027 camp',
     "**The 2nd Annual KY POTA Campout** is **24–26 September 2027** at Taylorsville Lake State Park (US-1271).\n"
     "Meet and greet, a fox hunt, park activations, a community meal and games. Group tent sites are reserved "
     "and open now.\n" + SITE + "campout.html"),
    (r'(?i)\bhow do i join\b|\bjoin the club\b|\bbecome a member\b|\bmembership\b',
     "Everything about joining is here: " + SITE + "join.html"),
    (r'(?i)\b(park control|which parks|what parks|park map|boundar|where are the parks)\b',
     "Park Control has every POTA park, KFF reference and SOTA summit in Kentucky on one map, with boundaries "
     "and parking: " + SITE + "kpc-park-control.html"),
    (r'(?i)\bpark notes?\b|\bwhere do i set up\b|\bparking at\b|\bgate\b.*\bpark\b',
     "Park notes are the practical stuff from people who have been there — parking, where to set up, gates, "
     "cell signal: " + SITE + "kpc-park-notes.html"),
    (r'(?i)\bcampground|\bcabin|\bcamping\b|\bwhere to stay\b|\blodge\b',
     "Campgrounds and cabins inside Kentucky parks, with booking links: " + SITE + "kpc-campgrounds.html"),
    (r'(?i)\bsota\b|\bsummit\b',
     "Our Kentucky SOTA guide: " + SITE + "kpc-guide-sota.html"),
    (r'(?i)\bwwff\b|\bkff\b',
     "Our Kentucky WWFF/KFF guide: " + SITE + "kpc-guide-wwff.html"),
    (r'(?i)\bnew to pota\b|\bhow do i (start|activate)\b|\bgetting started\b|\bfirst activation\b',
     "The Kentucky POTA guide walks through it from the beginning: " + SITE + "kpc-guide-pota.html"),
    (r'(?i)\bevents?\b.*\b(coming|when|calendar|next)\b|\bwhat.s coming up\b',
     "What's coming up: " + SITE + "events.html"),
    (r'(?i)\bwho is on the air\b|\bwho.s on\b|\bany ?one on\b|\bspots?\b.*\bnow\b',
     "Who's on the air right now: " + SITE + "kpc-spots.html"),
    (r'(?i)\bcontact\b|\bget in touch\b|\bemail the club\b',
     "The best way to reach us: " + SITE + "contact.html"),
    (r'(?i)\bvideos?\b|\byoutube\b|\bchannel\b',
     "Our videos: " + SITE + "videos.html"),
]


def park_card(num_refs):
    """Build the answer for a park reference, straight from the club's own files."""
    ky = load('kpc-ky-data.json', {})
    conds = {c['ref']: c for c in (load('kpc-conditions.json', {}).get('items') or [])}
    camps = load('kpc-campgrounds.json', {})
    stats = {r[0]: (r[1], r[2]) for r in (load('kpc-top25.json', {}).get('all') or [])
             if isinstance(r, list) and len(r) >= 3}
    camp_by = {}
    for p in (camps.get('parks') or []):
        cg = [c for c in (p.get('campgrounds') or []) if c.get('name')]
        if p.get('pota') and cg:
            camp_by[str(p['pota']).upper()] = cg
    out = []
    for ref in num_refs:
        p = next((x for x in (ky.get('parks') or []) if x.get('c', '').upper() == ref), None)
        if not p:
            p = next((x for x in (ky.get('kff') or []) + (ky.get('summits') or [])
                      if str(x.get('c', '')).upper() == ref), None)
        if not p:
            continue
        L = [f"**{ref} · {p.get('n')}**"]
        bits = [x for x in (p.get('t'), (p.get('co') + ' County' if p.get('co') and 'County' not in str(p.get('co')) else p.get('co'))) if x]
        if bits:
            L.append(' · '.join(bits))
        c = conds.get(ref)
        if c:
            L.append(f"⚠️ **{c.get('kind', 'Heads up')}** — {str(c.get('details'))[:220]}")
        if p.get('ft'):
            L.append(f"{p['ft']} ft · {p.get('pts')} point(s)")
        n = stats.get(ref)
        if n:
            acts, qs = n
            L.append("📻 " + ('**Never been activated** — you could be the first' if not acts
                              else f"{acts:,} activation{'s' if acts != 1 else ''}, {qs:,} contacts"
                                   + (' — a quiet one' if acts <= 3 else '')))
        cg = camp_by.get(ref) or []
        if cg:
            names = ', '.join(c['name'] for c in cg[:2]) + (' and more' if len(cg) > 2 else '')
            L.append(f"🏕 Camping: {names}")
        if p.get('web'):
            L.append(f"[The park's own page]({p['web']})")
        L.append(f"[Map and boundary]({SITE}kpc-park-control.html?ref={ref}) · "
                 f"[Park notes]({SITE}kpc-park-notes.html?ref={ref}) · "
                 f"[Activation kit]({SITE}kpc-kit.html?ref={ref})")
        out.append('\n'.join(L))
    return out


def km(a, b, c, d):
    from math import radians, sin, cos, asin, sqrt
    a, b, c, d = map(radians, (a, b, c, d))
    return 2 * 6371 * asin(sqrt(sin((c - a) / 2) ** 2 + cos(a) * cos(c) * sin((d - b) / 2) ** 2))


def near_a_town(text):
    """'any parks near Berea?' -> the five closest, with how far. Our own park list, our own town list."""
    if not re.search(r'(?i)\b(park|parks|summit|summits|activat|reference)\b', text or ''):
        return None
    ky = load('kpc-ky-data.json', {})
    # a county first ("any parks in Madison County?"), because that answer is a list, not a distance
    counties = sorted({c.strip() for p in (ky.get('parks') or [])
                       for c in str(p.get('co') or '').split('/') if c.strip()}, key=len, reverse=True)
    for co in counties:
        if re.search(r'\b' + re.escape(co) + r'\s+(county|co\b)', text or '', re.I):
            inco = [p for p in (ky.get('parks') or []) if co.lower() in str(p.get('co') or '').lower()]
            sums = [p for p in (ky.get('summits') or []) if co.lower() in str(p.get('co') or '').lower()]
            if not inco and not sums:
                return None
            L = [f"**{co} County** — {len(inco)} park reference(s)"
                 + (f" and {len(sums)} summit(s)" if sums else '')]
            for p in inco[:8]:
                L.append(f"• **{p['c']}** {p['n']}" + (f" · {p.get('t')}" if p.get('t') else ''))
            if len(inco) > 8:
                L.append(f"• …and {len(inco) - 8} more")
            L.append(f"\nOn the map: {SITE}kpc-park-control.html")
            return '\n'.join(L)

    towns = load('kpc-ky-towns.json', []) + EXTRA_TOWNS
    hit = None
    for t in sorted(towns, key=lambda t: -len(t[0])):
        if re.search(r'\b' + re.escape(t[0]) + r'\b', text or '', re.I):
            hit = t
            break
    if not hit:
        return None
    name, la, lo = hit[0], hit[1], hit[2]
    want_summits = bool(re.search(r'(?i)\bsummit', text or ''))
    pool = (ky.get('summits') or []) if want_summits else (ky.get('parks') or [])
    near = sorted(((km(la, lo, p['la'], p['lo']), p) for p in pool if p.get('la')), key=lambda x: x[0])[:5]
    if not near:
        return None
    L = [f"**{'Summits' if want_summits else 'Parks'} closest to {name}**"]
    for d, p in near:
        extra = f" · {p['ft']} ft" if p.get('ft') else (f" · {p.get('t')}" if p.get('t') else '')
        L.append(f"• **{p['c']}** {p['n']} — {round(d * 0.621, 1)} miles{extra}")
    L.append(f"\nAll of them on the map: {SITE}kpc-park-control.html")
    return '\n'.join(L)


def rare_parks():
    """'what needs activating?' -> the ones hardly anybody has done. Straight from the POTA figures we keep."""
    d = load('kpc-top25.json', {})
    held = {str(h.get('ref')).upper() for h in (load('data/kpc-post-holds.json', {}).get('hold') or [])
            if h.get('ref')}
    rows = [r for r in (d.get('acts') or []) if str(r.get('c', '')).upper() not in held]
    if not rows:
        return None
    L = ["**Kentucky parks hardly anybody has activated**"]
    for p in rows[:6]:
        n = p.get('a') or 0
        L.append(f"• **{p['c']}** {p['n']} ({p.get('co')} Co.) — "
                 + ('never been activated' if not n else f"{n} activation{'s' if n != 1 else ''}"))
    L.append(f"\nFigures from POTA, updated {str(d.get('updated'))[:10]}. "
             f"Pick one and you may well be the first: {SITE}kpc-park-control.html")
    return '\n'.join(L)


def busy_parks():
    """'which Kentucky park is the most activated?' - the other end of the same POTA figures."""
    d = load('kpc-top25.json', {})
    rows = [r for r in (d.get('all') or []) if isinstance(r, list) and len(r) >= 3]
    if not rows:
        return None
    ky = load('kpc-ky-data.json', {})
    byref = {p['c']: p for p in (ky.get('parks') or [])}
    rows.sort(key=lambda r: -(r[1] or 0))
    # A handful of references (the Trail of Tears, Lewis and Clark, the national forests) run through several
    # states, and POTA counts every activation of them anywhere. Quoting those as Kentucky's busiest would be
    # wrong, so they are kept out of the list and mentioned separately.
    here = [r for r in rows if 'multiple' not in str((byref.get(r[0]) or {}).get('co', '')).lower()]
    wide = [r for r in rows[:6] if 'multiple' in str((byref.get(r[0]) or {}).get('co', '')).lower()]
    L = ["**The most activated parks in Kentucky**"]
    for ref, acts, qs in here[:6]:
        p = byref.get(ref) or {}
        L.append(f"• **{ref}** {p.get('n', '')}"
                 + (f" ({p.get('co')} Co.)" if p.get('co') else '')
                 + f" — {acts:,} activations, {qs:,} contacts")
    if wide:
        names = ', '.join((byref.get(r[0]) or {}).get('n', r[0]) for r in wide[:3])
        L.append(f"\n_Left out: {names} — those run through several states and POTA counts every activation "
                 f"anywhere, so the numbers are not Kentucky's._")
    L.append(f"\nFigures from POTA, updated {str(d.get('updated'))[:10]}. "
             f"Busy is not always better — the quiet ones are at {SITE}kpc-park-control.html")
    return '\n'.join(L)


def how_many():
    """'how many parks are there in Kentucky?'"""
    ky = load('kpc-ky-data.json', {})
    return (f"Kentucky has **{len(ky.get('parks') or [])} POTA park references**, "
            f"**{len(ky.get('kff') or [])} KFF references** and **{len(ky.get('summits') or [])} SOTA summits**.\n"
            f"Every one of them, with boundaries and parking: {SITE}kpc-park-control.html")


def contests_soon():
    """'anything on this weekend?' -> contests inside the next week, from the calendar we already keep."""
    d = load('kpc-contests.json', {})
    now = datetime.datetime.now(datetime.timezone.utc)
    soon = []
    for c in (d.get('week') or []) + (d.get('big') or []):
        for seg in (c.get('segs') or []):
            try:
                s = datetime.datetime.fromisoformat(str(seg[0]).replace('Z', '+00:00'))
                e = datetime.datetime.fromisoformat(str(seg[1]).replace('Z', '+00:00'))
            except Exception:  # noqa: BLE001
                continue
            if e > now and (s - now).days <= 8:
                soon.append((s, c))
                break
    if not soon:
        return "Nothing much on the contest calendar for the next week. The bands should be nice and quiet."
    seen, L = set(), ["**On the air over the next few days**"]
    for s, c in sorted(soon, key=lambda x: x[0])[:6]:
        if c['name'] in seen:
            continue
        seen.add(c['name'])
        L.append(f"• **{c['name']}** — {c.get('when') or s.strftime('%a %d %b %H%MZ')}"
                 + (f" · {', '.join(c.get('modes') or [])}" if c.get('modes') else ''))
    L.append("\nWorth knowing if you are heading to a park: the bands get busy and a park contact is still a "
             "park contact.")
    return '\n'.join(L)


def utc_now():
    n = datetime.datetime.now(datetime.timezone.utc)
    return (f"**{n.strftime('%H%M')} UTC** · {n.strftime('%a %d %b %Y')}\n"
            f"That is {(n - datetime.timedelta(hours=5)).strftime('%I:%M %p').lstrip('0')} Central "
            f"and {(n - datetime.timedelta(hours=4)).strftime('%I:%M %p').lstrip('0')} Eastern.")


def answer_for(text):
    """What to say, or None to stay quiet."""
    if not ASKING.search(text or ''):
        return None
    if re.search(r'(?i)\b(utc|zulu|z time|what time)\b', text or ''):
        return utc_now()
    if re.search(r'(?i)\b(most activated|most popular|busiest|most active|top park|activated the most|'
                 r'activated most)\b', text or ''):
        b = busy_parks()
        if b:
            return b
    if re.search(r'(?i)\bhow many\b.{0,20}\b(park|parks|summit|summits|reference)', text or ''):
        return how_many()
    if re.search(r'(?i)\b(rare|rarest|lonely|never been|nobody|no ?one has|needs? activating|unactivated|'
                 r'not been activated|first activation of|least activated)\b', text or ''):
        r = rare_parks()
        if r:
            return r
    if re.search(r'(?i)\b(contest|contests|on the air this|bands busy|anything on)\b', text or ''):
        c = contests_soon()
        if c:
            return c
    n = near_a_town(text)
    if n:
        return n
    refs = []
    for m in REF.finditer(text or ''):
        if m.group(1):
            refs.append('US-' + m.group(1).zfill(4))
        elif m.group(2):
            refs.append('KFF-' + m.group(2).split('-')[1].zfill(4))
        elif m.group(3):
            refs.append(m.group(3).upper())
    cards = park_card(sorted(set(refs))[:3]) if refs else []
    if cards:
        return '\n\n'.join(cards)
    for pat, ans in FAQ:
        if re.search(pat, text or ''):
            return ans
    return None


def welcome(name):
    """Said once to each person who joins. Short, friendly, and it does not pretend to be a person."""
    return (f"Welcome to the Kentucky Portable Club, {name}! 👋\n\n"
            f"A few things worth having:\n"
            f"• New to parks on the air? Start here: {SITE}kpc-guide-pota.html\n"
            f"• Every Kentucky park, reference and summit on one map: {SITE}kpc-park-control.html\n"
            f"• Who is on the air right now: {SITE}kpc-spots.html\n"
            f"• The big one — our campout, 24–26 September 2027: {SITE}campout.html\n\n"
            f"Ask away in the rooms; somebody usually knows. You can ask me things too — a park number "
            f"(\"anyone been to US-1271?\"), \"what needs activating?\", \"any parks near Berea?\", "
            f"\"any contests this weekend?\" or \"what's UTC?\" — and I will look it up on the website.")


def main():
    if not TOKEN:
        notice('No Discord bot token; nothing to do.')
        return
    conf = load(CONF_F, {})
    rooms = conf.get('rooms') or []
    # Where to say hello. Discord drops a "somebody joined" message in the server's system channel; we greet in
    # whichever of our rooms that lands in. greet_rooms in data/discord-watch.json can point somewhere else
    # (the welcome room, say), and "greet": false turns it off altogether.
    greet_rooms = conf.get('greet_rooms')
    greeting_on = conf.get('greet') is not False
    if not rooms:
        notice('No rooms set up yet.')
        return
    state = load(STATE_F, {})
    done = set(state.get('answered') or [])
    first_time = not state.get('updated')
    said_hello = set(state.get('hello') or [])
    replies = 0

    look_in = list(rooms)
    for extra in (greet_rooms or []):
        if str(extra.get('id') if isinstance(extra, dict) else extra) not in \
                {str(r.get('id') if isinstance(r, dict) else r) for r in rooms}:
            look_in.append(extra)

    greeted = 0
    for room in look_in:
        rid = str(room.get('id') if isinstance(room, dict) else room)
        name = (room.get('name') if isinstance(room, dict) else '') or rid
        msgs = call(f'channels/{rid}/messages?limit=25')
        if isinstance(msgs, dict):
            notice(f'Cannot read #{name}: {msgs.get("_error")}')
            continue
        for m in sorted(msgs, key=lambda x: x.get('timestamp', '')):
            if (m.get('author') or {}).get('bot'):
                continue
            fp = fingerprint(m.get('id'))
            if fp in done:
                continue
            done.add(fp)
            if first_time or replies >= MAX_REPLIES:
                continue
            # type 7 is Discord's own "somebody joined the server" message
            if m.get('type') == 7:
                who = ((m.get('author') or {}).get('global_name')
                       or (m.get('author') or {}).get('username') or 'friend')
                if not greeting_on or greeted >= 3:
                    continue
                ans = welcome(who)
                greeted += 1
            else:
                ans = answer_for(m.get('content') or '')
            if not ans:
                continue
            if rid not in said_hello and m.get('type') != 7:
                ans += ("\n\n_I'm the club's helper. I only answer what I can look up in the club's own pages, "
                        "and I check every few minutes rather than straight away._")
                said_hello.add(rid)
            if DRY:
                print(f'--- would reply in #{name} ---\n{ans}\n')
            else:
                r = call(f'channels/{rid}/messages', 'POST',
                         {'content': ans[:1900], 'message_reference': {'message_id': m['id']},
                          'allowed_mentions': {'parse': []}})
                if r.get('_error'):
                    notice(f'Could not reply in #{name}: {r["_error"]}')
                    continue
            replies += 1

    if first_time:
        notice('First run: noted what is already there, answered nothing. It starts answering from now on.')
    else:
        notice(f'Answered {replies} message(s)' + (f', {greeted} of them a welcome.' if greeted else '.')
               if replies else 'Nothing to answer.')
    state.update({'answered': sorted(done)[-4000:], 'hello': sorted(said_hello),
                  'updated': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M')})
    if not DRY:
        STATE_F.parent.mkdir(parents=True, exist_ok=True)
        STATE_F.write_text(json.dumps(state, indent=1) + '\n', encoding='utf-8')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:  # noqa: BLE001
        notice(f'stopped early: {type(e).__name__}: {str(e)[:300]}')
        sys.exit(0)          # never fail the job: a failed run emails Brandon
