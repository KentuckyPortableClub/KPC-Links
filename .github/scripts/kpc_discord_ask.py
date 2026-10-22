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
    live = {p['c'] for p in (load('kpc-ky-data.json', {}).get('parks') or [])}
    # a reference POTA has retired is still in the figures file until it is refreshed - never suggest one
    rows = [r for r in (d.get('acts') or [])
            if str(r.get('c', '')).upper() not in held and r.get('c') in live]
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
    rows = [r for r in rows if r[0] in byref]          # drop anything POTA has retired
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


CALL = re.compile(r'\b([A-Z]{1,2}[0-9][A-Z]{1,4})(?:/[A-Z0-9]+)?\b')
MINE = re.compile(r"(?i)\b(do i|have i|i have|i need|i still|my parks|i've|ive)\b")


def call_parks(text, who=''):
    """'how many parks does K4XYZ need to activate all of Kentucky?' (Brandon Oct 22: 'teach it to look up peoples
    calls'). From POTA's public activation lists, which data/leaders/KY-calls.json adds up every day. 'Do I need' uses
    the call in the asker's Discord name. An activation counts at 10+ contacts, POTA's rule."""
    if not re.search(r'(?i)\b(activat|need|parks? (has|have|did)|how many)', text or ''):
        return None
    calls = [c for c in CALL.findall((text or '').upper()) if not re.match(r'^(US|KFF|KY)\d', c)]
    if not calls and MINE.search(text or ''):
        calls = CALL.findall(str(who or '').upper())
    if not calls:
        return None
    c = calls[0]
    d = load('data/leaders/KY-calls.json', {})
    if not d.get('calls'):
        return None
    live = {p['c']: p for p in (load('kpc-ky-data.json', {}).get('parks') or [])}
    held = {str(h.get('ref')).upper() for h in (load('data/kpc-post-holds.json', {}).get('hold') or []) if h.get('ref')}
    done = [r for r in d['calls'].get(c, []) if r in live]
    need = [r for r in sorted(live) if r not in done and r not in held]
    tot = len(live)
    if not done:
        L = [f"**{c}** has no Kentucky park activations in POTA's records yet (an activation counts at 10 contacts). "
             f"That leaves all {tot} to go — plenty of choice: {SITE}kpc-park-control.html"]
    elif not need:
        L = [f"**{c}** has activated **every one** of Kentucky's {tot} POTA parks. 🎉"]
    else:
        L = [f"**{c}** has activated **{len(done)} of {tot}** Kentucky POTA parks — **{len(need)} to go**."]
        quiet = {r.get('c'): (r.get('a') or 0) for r in (load('kpc-top25.json', {}).get('acts') or [])}
        pick = sorted(need, key=lambda r: (quiet.get(r, 999), r))[:5]
        L.append('A few still to do: ' + ', '.join(f"**{r}** {live[r]['n']}" for r in pick))
        L.append(f"Map of every park: {SITE}kpc-park-control.html")
    L.append(f"_From POTA's activation lists, updated {str(d.get('updated'))[:10]}. Activations only: POTA does not share who hunted each park._")
    return '\n'.join(L)


# ---------------------------------------------------------------- Oct 22 (Brandon: '1,2,3,4,5,7,8')
def web(url, timeout=20):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={**UA, 'Accept': 'application/json'}), timeout=timeout) as r:
            return json.loads(r.read().decode('utf-8', 'replace'))
    except Exception:  # noqa: BLE001
        return None


def refs_in(text):
    out = []
    for m in REF.finditer(text or ''):
        if m.group(1): out.append('US-' + m.group(1).zfill(4))
        elif m.group(2): out.append('KFF-' + m.group(2).split('-')[1].zfill(4))
        elif m.group(3): out.append(m.group(3).upper())
    return list(dict.fromkeys(out))


def place(ref):
    """Name and spot of a reference: the club's own file for Kentucky, POTA for anywhere else."""
    ky = load('kpc-ky-data.json', {})
    for x in (ky.get('parks') or []) + (ky.get('kff') or []) + (ky.get('summits') or []):
        if str(x.get('c', '')).upper() == ref and x.get('la') is not None:
            return {'n': x.get('n'), 'la': float(x['la']), 'lo': float(x['lo'])}
    if ref.startswith('US-'):
        j = web('https://api.pota.app/park/' + ref)
        if j and j.get('latitude') is not None:
            return {'n': j.get('name'), 'la': float(j['latitude']), 'lo': float(j['longitude'])}
    return None


def on_air():
    """1. 'who's on the air in Kentucky right now?' - POTA's live activator spots for Kentucky parks."""
    sp = web('https://api.pota.app/spot/activator')
    if sp is None:
        return f"POTA's spot list did not answer just now. Live spots: {SITE}kpc-spots.html"
    ky = [x for x in sp if 'US-KY' in str(x.get('locationDesc') or '')]
    seen, rows = set(), []
    for x in sorted(ky, key=lambda x: str(x.get('spotTime') or ''), reverse=True):
        k = (str(x.get('activator') or '').upper(), x.get('reference'))
        if k in seen: continue
        seen.add(k); rows.append(x)
    if not rows:
        return f"Nobody is spotted at a Kentucky park right now. Be the first: {SITE}kpc-park-control.html"
    L = ["**On the air in Kentucky right now**"]
    for x in rows[:10]:
        f = str(x.get('frequency') or '')
        try: f = f"{float(f) / 1000:.3f}"
        except ValueError: pass
        L.append(f"• **{x.get('activator')}** at **{x.get('reference')}** {str(x.get('name') or '')[:40]} — {f} {x.get('mode') or ''}".rstrip())
    L.append(f"Live list: {SITE}kpc-spots.html")
    return '\n'.join(L)


def last_activation(ref):
    """2. 'when was US-1271 last activated?' / 'has it been done this year?'"""
    a = web(f'https://api.pota.app/park/activations/{ref}?count=all')
    if a is None:
        return None
    ok = sorted([x for x in a if int(x.get('totalQSOs') or 0) >= 10], key=lambda x: str(x.get('qso_date') or ''), reverse=True)
    pl = place(ref) or {}
    nm = f"**{ref}** {pl.get('n') or ''}".strip()
    if not ok:
        return f"{nm} has **never been activated** in POTA's records (10 contacts makes it count). You could be the first."
    y = str(datetime.date.today().year)
    last, yr = ok[0], [x for x in ok if str(x.get('qso_date') or '').startswith(y)]
    d = str(last.get('qso_date') or '')
    d = f"{d[4:6]}/{d[6:8]}/{d[:4]}" if len(d) >= 8 else d
    return (f"{nm} was last activated on **{d}** by **{last.get('activeCallsign')}** ({last.get('totalQSOs')} contacts).\n"
            + (f"{len(yr)} activation{'s' if len(yr) != 1 else ''} so far in {y}; {len(ok):,} in all."
               if yr else f"Not yet in {y} — {len(ok):,} activations in all."))


def open_and_weather(ref):
    """3. 'is US-xxxx open?' - any closure the park-alert bot has found, then the National Weather Service forecast."""
    pl = place(ref)
    L = [f"**{ref} {(pl or {}).get('n') or ''}**".strip()]
    c = [x for x in (load('kpc-conditions.json', {}).get('items') or []) if x.get('ref') == ref]
    if c:
        for x in c[:2]:
            L.append(f"⚠️ **{x.get('kind', 'Heads up')}** — {str(x.get('details'))[:260]}")
    else:
        L.append("No closures or alerts we know of. Gates and hours can still change, so check the park's own page before a long drive.")
    if pl:
        pt = web(f"https://api.weather.gov/points/{pl['la']:.4f},{pl['lo']:.4f}")
        fc = web(pt['properties']['forecast']) if pt and (pt.get('properties') or {}).get('forecast') else None
        per = ((fc or {}).get('properties') or {}).get('periods') or []
        if per:
            L.append('🌤 ' + ' · '.join(f"**{x.get('name')}**: {x.get('shortForecast')}, {x.get('temperature')}°{x.get('temperatureUnit')}" for x in per[:3]))
        al = web(f"https://api.weather.gov/alerts/active?point={pl['la']:.4f},{pl['lo']:.4f}")
        for f in ((al or {}).get('features') or [])[:2]:
            L.append(f"🚨 {(f.get('properties') or {}).get('headline')}")
    L.append(f"[Activation kit with the full forecast]({SITE}kpc-kit.html?ref={ref})")
    return '\n'.join(L)


def bands():
    """4. 'how are the bands?' - NOAA's planetary K index and today's solar flux, in plain words."""
    k = web('https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json')
    f = web('https://services.swpc.noaa.gov/products/summary/10cm-flux.json')
    kv = sfi = None
    try: kv = float((k[-1].get('Kp') if isinstance(k[-1], dict) else k[-1][1]))
    except Exception: pass  # noqa: BLE001
    try: sfi = int(float((f or {}).get('Flux')))
    except Exception: pass  # noqa: BLE001
    if kv is None and sfi is None:
        return None
    L = ["**Band conditions right now**"]
    if sfi is not None:
        L.append(f"☀️ Solar flux **{sfi}** — " + ('the high bands (15–10 m) should be open in daylight' if sfi >= 150
                 else 'fair: 20 m in the day, 40 m any time, the higher bands now and then' if sfi >= 100
                 else 'low: stick to 40 m and 20 m, the higher bands will be quiet'))
    if kv is not None:
        L.append(f"🧲 K index **{kv:g}** — " + ('quiet, good for the low bands' if kv <= 2 else 'unsettled, a bit noisy'
                 if kv <= 4 else 'a geomagnetic storm: noisy, and the high bands may fade out'))
    L.append("From NOAA's Space Weather Prediction Center. Best times by band are in the Friday post.")
    return '\n'.join(L)


def next_events():
    """5. 'when's the next event?' - the club's events, members' submitted events and the recurring ones."""
    t = datetime.date.today().isoformat()
    ev = list(load('data/kpc-club-events.json', {}).get('events') or [])
    ev += list(load('kpc-events-submitted.json', {}).get('events') or [])
    a = load('kpc-events-auto.json', {})
    ev += list(a.get('recurring') or []) + list(a.get('found') or [])
    ev = sorted([e for e in ev if str(e.get('end') or e.get('start') or '') >= t and e.get('name')], key=lambda e: str(e.get('start')))
    if not ev:
        return f"Nothing on the calendar yet: {SITE}events.html"
    seen, L = set(), ["**Coming up**"]
    for e in ev:
        k = (e['name'], e.get('start'))
        if k in seen: continue
        seen.add(k)
        d1 = datetime.date.fromisoformat(str(e['start'])[:10])
        d = d1.strftime('%b %d, %Y').replace(' 0', ' ')
        if e.get('end') and str(e['end'])[:10] != str(e['start'])[:10]:
            d += ' – ' + datetime.date.fromisoformat(str(e['end'])[:10]).strftime('%b %d').replace(' 0', ' ')
        L.append(f"• **{e['name']}** — {d}" + (f" · {e['where']}" if e.get('where') and len(str(e['where'])) < 60 else ''))
        if len(L) > 5: break
    L.append(f"The whole calendar: {SITE}events.html")
    return '\n'.join(L)


def grid(la, lo):
    lo, la = lo + 180, la + 90
    A = 'ABCDEFGHIJKLMNOPQRSTUVWX'
    return (A[int(lo // 20)] + A[int(la // 10)] + str(int(lo % 20 // 2)) + str(int(la % 10))
            + A[int(lo % 2 * 12)].lower() + A[int(la % 1 * 24)].lower())


def grid_of(ref):
    """7. 'what grid is US-xxxx in?'"""
    pl = place(ref)
    if not pl:
        return None
    return f"**{ref} {pl.get('n') or ''}** is in grid **{grid(pl['la'], pl['lo'])}** (from the park's map pin; a big park can cross into the next square)."


FT8 = {'160': '1.840', '80': '3.573', '60': '5.357', '40': '7.074', '30': '10.136', '20': '14.074', '17': '18.100',
       '15': '21.074', '12': '24.915', '10': '28.074', '6': '50.313', '2': '144.174'}
FT4 = {'80': '3.575', '40': '7.0475', '30': '10.140', '20': '14.080', '17': '18.104', '15': '21.140', '12': '24.919', '10': '28.180', '6': '50.318'}
QCODES = {'73': 'best regards — the usual sign-off', '88': 'love and kisses (friendly sign-off)', 'qrt': 'stopping, going off the air',
          'qrp': 'low power (5 W or less on CW/digital, 10 W SSB)', 'qsy': 'change frequency', 'qsl': 'I confirm / a confirmation card',
          'qth': 'my location', 'qrz': 'who is calling me?', 'qrm': 'interference from other stations', 'qrn': 'static, natural noise',
          'qso': 'a contact', 'cq': 'calling anyone', 'p2p': 'park to park: both stations are activating a park',
          'dx': 'a distant station', 'qrq': 'send faster', 'qrs': 'send slower', 'qrl': 'is this frequency in use?'}


def quick(text):
    """8. Quick ham answers: FT8/FT4 frequencies, Q-codes and lingo, how many contacts each program needs."""
    t = text or ''
    m = re.search(r'(?i)\b(ft8|ft4)\b', t)
    if m and re.search(r"(?i)\b(freq\w*|where|dial|what)\b", t):
        tab = FT8 if m.group(1).lower() == 'ft8' else FT4
        b = re.search(r'\b(160|80|60|40|30|20|17|15|12|10|6|2)\s*(m|meters?)\b', t, re.I)
        if b and b.group(1) in tab:
            return f"{m.group(1).upper()} on {b.group(1)} m: **{tab[b.group(1)]} MHz** (USB dial)."
        return f"**{m.group(1).upper()} dial frequencies (USB):** " + ' · '.join(f"{k} m {v}" for k, v in tab.items())
    if re.search(r'(?i)\bhow many (contacts|qsos)\b|\bcontacts? (do i need|to count)\b|\bvalid activation\b|\bto count\b', t):
        return ("**Contacts needed:**\n• **POTA**: 10 in one UTC day (park-to-park counts like any other)\n"
                "• **WWFF/KFF**: 44 for the activation to count worldwide (can be added up over visits); fewer still count for the hunters\n"
                "• **SOTA**: 4 to get the summit's points, 1 to log it")
    m = re.search(r'(?i)\bwhat (does|is|do) (a |an )?["\']?(73|88|qr[a-z]|qs[a-z]|qth|cq|p2p|dx)["\']?\b', t)
    if m and m.group(3).lower() in QCODES:
        return f"**{m.group(3).upper()}** = {QCODES[m.group(3).lower()]}."
    return None


def answer_for(text, who=''):
    """What to say, or None to stay quiet."""
    if not ASKING.search(text or ''):
        return None
    cp = call_parks(text, who)
    if cp:
        return cp
    t = text or ''
    q = quick(t)
    if q:
        return q
    if re.search(r"(?i)\bwho.?s on\b|\bwho is on\b|\bon the air (now|right now|in kentucky)\b|\bany ?(one|body) (on|out|activating)\b|\bspots?\b.{0,20}\b(now|kentucky|right now)\b", t):
        return on_air()
    if re.search(r'(?i)\b(band conditions|how are the bands|bands? (good|bad|open|today)|solar|sfi|k.?index|propagation|conditions today)\b', t):
        b = bands()
        if b:
            return b
    rs = refs_in(t)
    if rs:
        if re.search(r'(?i)\b(grid|maidenhead|locator)\b', t):
            g = grid_of(rs[0])
            if g:
                return g
        if re.search(r'(?i)\b(last activat|last time|been activated|activated (this|last) year|recent(ly)? activ|when was)\b', t):
            la = last_activation(rs[0])
            if la:
                return la
        if re.search(r'(?i)\b(open|closed|closure|alerts?|weather|forecast|rain|storm|flood)\b', t):
            return open_and_weather(rs[0])
    if not re.search(r'(?i)\bcamp ?out\b', t) and re.search(r"(?i)\b(next|upcoming|coming up)\b.{0,20}\b(event|events|meet|weekend|activation day)\b|\bwhat.?s (coming up|on the calendar)\b|\bany events\b", t):
        return next_events()
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
                ans = answer_for(m.get('content') or '', ' '.join(str((m.get('author') or {}).get(k) or '') for k in ('global_name', 'username')))
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
