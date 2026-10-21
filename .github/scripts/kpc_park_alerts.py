#!/usr/bin/env python3
"""KPC park alert watcher (Brandon Oct 21 2026: 'monitor ky state parks and announce if a park closes… or opens back up').

Watches the official alert lists for Kentucky's parks and tells the club when something changes.

HOW IT DECIDES (the bit that matters):
  - Parks announce a CLOSING. They almost never announce the REOPENING. So this does not listen for announcements:
    it keeps its own copy of the alert list and compares. A new alert = something closed or needs care.
    An alert that has GONE from the official list is the reopening, worded carefully because a notice being taken
    down is good evidence, not a promise.
  - Websites flicker, so nothing is announced on first sight: a change has to show up on TWO checks in a row.
  - Nothing is posted overnight. Anything found after 9 PM Kentucky time waits for the morning check.
  - A quiet check posts nothing, anywhere. No emails, ever (club rule).

WHERE IT GOES: a post to Discord and the club's Facebook Page, and a red warning on the park's own pages through
kpc-conditions.json (Park Notes, Campgrounds, the POTA guide cards and the Activation Kit all read that file).
Our items there have ids starting 'pa-' and clear themselves when the park reopens.

SOURCES
  1. Kentucky State Parks: https://parks.ky.gov/api/default/alerts  (official, structured, no key needed)
  2. National Park Service: https://developer.nps.gov/api/v1/alerts?stateCode=KY  (needs the free key NPS_API_KEY;
     skipped quietly when there is no key, so adding the key later is the only thing needed to turn it on)
  3. US Forest Service: https://www.fs.usda.gov/alerts/dbnf/alerts-notices  (plain HTML, no key)

STATE: data/park-alerts-state.json. Secrets: KPC_DISCORD_WEBHOOK, FB_PAGE_ID, FB_PAGE_TOKEN, NPS_API_KEY (optional).
Run with DRY_RUN=1 to see what it would say and change nothing.
"""
import datetime
import html as _html
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

SITE = 'https://kentuckyportableclub.github.io/KPC-Links/'
STATE_F = pathlib.Path('data/park-alerts-state.json')
COND_F = pathlib.Path('kpc-conditions.json')
KY_F = pathlib.Path('kpc-ky-data.json')
UA = {'User-Agent': 'KPC club bot (kentuckyportableclub.github.io)'}
DRY = os.environ.get('DRY_RUN') == '1'
# Where park news goes (Brandon Oct 21: not the spots room, and not the staff room either - somewhere the
# members can see it). Make a webhook for that room and save it as KPC_PARKS_WEBHOOK; until then it falls
# back to the staff room, then to the usual bot room.
DISCORD = ((os.environ.get('KPC_PARKS_WEBHOOK') or os.environ.get('KPC_ADMIN_WEBHOOK')
           or os.environ.get('KPC_DISCORD_WEBHOOK') or '').strip().split() or [''])[0]
FB_ID = (os.environ.get('FB_PAGE_ID') or '').strip()
FB_TOKEN = (os.environ.get('FB_PAGE_TOKEN') or '').strip()
NPS_KEY = (os.environ.get('NPS_API_KEY') or '').strip()
QUIET_FROM, QUIET_TO = 21, 6          # no posting between 9 PM and 6 AM Kentucky time
# Routine stuff the forests list constantly (Brandon Oct 21: 'they a lot of control burns so I dont want to
# flood page with control burns'). These never go to Facebook, only reach Discord when they name one of our
# own parks, show on the park page as their own kind, and clear themselves sooner. They are also never
# announced as 'open again': a burn ending is not news.
ROUTINE = re.compile(r'(?i)prescribed burn|controlled burn|pile burn|burn unit|burning operation|'
                     r'smoke (may|is|could)|hazard tree|timber (sale|harvest)|routine maintenance')
ROUTINE_DAYS = 14
BURN_DIGEST_HOUR = 17     # burns reach Facebook once a day, in the late-afternoon check, all in one post
CONFIRM = 2                            # a change must be seen this many checks in a row


def notice(title, msg):
    print(f"::notice title={title}::{str(msg)[:800]}", flush=True)


def ky_now():
    """Kentucky time (most of the state is Eastern, but the club works in Central; Central is the safer clock
    for 'is it too late to post'). No tz database needed on the runner: work it out from UTC."""
    u = datetime.datetime.now(datetime.timezone.utc)
    # US DST: second Sunday in March to first Sunday in November
    y = u.year
    mar = datetime.datetime(y, 3, 8, 7, tzinfo=datetime.timezone.utc)
    mar += datetime.timedelta(days=(6 - mar.weekday()) % 7)
    nov = datetime.datetime(y, 11, 1, 6, tzinfo=datetime.timezone.utc)
    nov += datetime.timedelta(days=(6 - nov.weekday()) % 7)
    off = -5 if mar <= u < nov else -6
    return u + datetime.timedelta(hours=off)


def fetch(url, headers=None, timeout=60):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8', 'replace')


def load(path, default):
    try:
        return json.loads(pathlib.Path(path).read_text(encoding='utf-8'))
    except Exception:  # noqa: BLE001
        return default


def clean(s, cap=400):
    s = _html.unescape(re.sub(r'<[^>]+>', ' ', str(s or '')))
    s = re.sub(r'&nbsp;?', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s[:cap]


# ---------------------------------------------------------------- sources
def ky_state_parks():
    """Kentucky State Parks' own alert list."""
    out = {}
    try:
        j = json.loads(fetch('https://parks.ky.gov/api/default/alerts?$top=100'))
    except Exception as e:  # noqa: BLE001
        notice('Park alerts', f'Kentucky State Parks did not answer: {str(e)[:200]}')
        return None
    for a in j.get('value') or []:
        aid = str(a.get('Id') or a.get('UrlName') or '')
        if not aid:
            continue
        title, text = clean(a.get('Title'), 160), clean(a.get('Text'))
        if not title and not text:
            continue
        link = clean(a.get('CtaLink'), 300) or 'https://parks.ky.gov/'
        out['ky-' + aid] = {'who': 'Kentucky State Parks', 'title': title, 'text': text, 'link': link}
    return out


def nps_alerts():
    """National Park Service alerts for Kentucky. Needs the free key; skipped quietly without one."""
    if not NPS_KEY:
        return {}
    out = {}
    try:
        j = json.loads(fetch('https://developer.nps.gov/api/v1/alerts?stateCode=KY&limit=200',
                             headers={'X-Api-Key': NPS_KEY}))
    except Exception as e:  # noqa: BLE001
        notice('Park alerts', f'National Park Service did not answer: {str(e)[:200]}')
        return None
    for a in j.get('data') or []:
        aid = str(a.get('id') or '')
        if not aid:
            continue
        cat = clean(a.get('category'), 40).lower()
        out['nps-' + aid] = {'who': clean(a.get('parkCode'), 20).upper() or 'National Park Service',
                             'title': clean(a.get('title'), 160),
                             'text': clean(a.get('description')),
                             'link': clean(a.get('url'), 300) or 'https://www.nps.gov/',
                             # the park says what kind it is: only Closure/Danger/Caution is 'before you drive out'
                             # news. 'Information' is standing advice (drones, bears, firewood, opening hours) and
                             # must not be dressed up as a heads-up (Brandon saw a list of those on Oct 21).
                             'routine': cat in ('information', '') or not cat,
                             'cat': cat}
    return out


def forest_alerts():
    """US Forest Service alerts for Kentucky's national forests. Their alerts page is plain HTML: each alert is a
    <li class="usa-card … wfs-alert-flag LEVEL"> with the title in an <h3><a><span> and the text in usa-card__body.
    Levels: critical, caution (real problems) and information, fire-restriction (routine, grouped)."""
    FORESTS = [('dbnf', 'Daniel Boone National Forest')]
    out, ok = {}, False
    for code, who in FORESTS:
        try:
            html = fetch(f'https://www.fs.usda.gov/alerts/{code}/alerts-notices', timeout=90)
        except Exception as e:  # noqa: BLE001
            notice('Park alerts', f'{who} did not answer: {str(e)[:160]}')
            continue
        ok = True
        n = 0
        for m in re.finditer(r'<li class="usa-card[^"]*wfs-alert-flag ([a-z\-]+)">(.*?)</li>', html, re.S):
            level, block = m.group(1), m.group(2)
            head = re.search(r'<h3[^>]*>\s*<a href="([^"]+)"[^>]*>\s*<span>(.*?)</span>', block, re.S)
            body = re.search(r'<div class="usa-card__body">(.*?)</div>', block, re.S)
            if not head:
                continue
            path = head.group(1)
            out['fs-' + re.sub(r'[^a-z0-9\-]+', '', path.rstrip('/').split('/')[-1].lower())[:60]] = {
                'who': who,
                'title': clean(head.group(2), 160),
                'text': clean(body.group(1) if body else ''),
                'link': 'https://www.fs.usda.gov' + path,
                # 'information' and fire restrictions are standing notices, not news: treat them like forest work
                'routine': level in ('information', 'fire-restriction'),
            }
            n += 1
        notice('Park alerts', f'{who}: {n} alert(s) listed')
    return out if ok else None


# ---------------------------------------------------------------- our parks
def ky_parks():
    """[(ref, name, short)] for every Kentucky POTA park, so an alert can be pinned to the right park."""
    d = load(KY_F, {})
    out = []
    for p in d.get('parks') or []:
        ref, name = p.get('c'), clean(p.get('n'), 120)
        if not ref or not name:
            continue
        short = re.sub(r'(?i)\s*(state resort park|state historic site|state nature preserve|state park|'
                       r'national historical park|national park|national historic site|wildlife management area|'
                       r'state forest|lake|wma)\s*', ' ', name)
        out.append((ref, name, re.sub(r'\s+', ' ', short).strip()))
    return out


# a one-word short name only counts when a park-ish word follows it ('Taylorsville Lake'), so the
# system-wide 'Kentucky State Parks' notice can't land on Kentucky Lake WMA
NEXTW = ('lake', 'park', 'parks', 'wma', 'forest', 'trail', 'trails', 'campground', 'preserve', 'area', 'site', 'river', 'creek', 'falls')
TOOCOMMON = {'kentucky', 'general', 'national', 'federal', 'county', 'state', 'western', 'eastern', 'northern', 'southern'}
MAXREFS = 4          # an alert that seems to be about half the state is general news, not one park

# Place words. If one of these follows the bit of name we matched, and it is NOT part of our park's own name,
# then the text is talking about a different place that happens to start the same way (Oct 21: the Green River
# Ferry notice at Mammoth Cave landed on Green River State Forest AND Green River Lake State Park, and
# 'Beaver Creek Wilderness' in the Daniel Boone forest landed on Beaver Lake up in Anderson County).
PLACEN = ('ferry', 'lake', 'river', 'creek', 'fork', 'branch', 'run', 'falls', 'forest', 'park', 'wilderness',
          'wma', 'bridge', 'trail', 'trails', 'campground', 'preserve', 'mountain', 'gorge', 'ridge', 'hollow',
          'cave', 'dam', 'reservoir', 'island', 'spring', 'springs', 'bend', 'knob', 'valley', 'county')


def _really_ours(phrase, hay, full):
    """True if 'phrase' appears in the text as our park, not as the start of some other place's name."""
    for m in re.finditer(r' ' + re.escape(phrase) + r' ([a-z0-9]+)', hay):
        nxt = m.group(1)
        if nxt not in PLACEN or re.search(r'\b' + re.escape(nxt) + r'\b', full):
            return True
    # the phrase at the very end of the text, with nothing following it, still counts
    return bool(re.search(r' ' + re.escape(phrase) + r' *$', hay))


def match_parks(alert, parks):
    """Which of our parks does this alert talk about? Name match only, and only when it is unmistakable."""
    hay = ' ' + re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]+', ' ', (alert['title'] + ' ' + alert['text']).lower())) + ' '
    hits = []
    for ref, name, short in parks:
        full = re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]+', ' ', name.lower())).strip()
        if len(full) >= 8 and f' {full} ' in hay:
            hits.append(ref)
            continue
        sh = re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]+', ' ', short.lower())).strip()
        if not sh or sh in TOOCOMMON or len(sh) < 6:
            continue
        if ' ' in sh:                                     # two words or more: specific enough on its own
            if f' {sh} ' in hay and _really_ours(sh, hay, full):
                hits.append(ref)
        elif (re.search(r' ' + re.escape(sh) + r' (?:' + '|'.join(NEXTW) + r') ', hay)
                and _really_ours(sh, hay, full)):
            hits.append(ref)
    hits = sorted(set(hits))
    return hits if len(hits) <= MAXREFS else []


# ---------------------------------------------------------------- posting
def http(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:  # noqa: BLE001
        return 0, str(e)


def post_discord(title, text):
    if not DISCORD.startswith('https://'):
        notice('Park alerts', 'No Discord webhook set; nothing sent to Discord.')
        return
    body = {'username': 'KPC Park Watch', 'allowed_mentions': {'parse': []},
            'embeds': [{'title': title[:250], 'color': 0xd5a63a, 'description': text[:4000]}]}
    c, r = http(DISCORD, json.dumps(body).encode(), {'Content-Type': 'application/json'})
    if c >= 300:
        notice('Park alerts', f'Discord HTTP {c}: {r[:200]}')


def post_facebook(title, text):
    if not FB_ID or not FB_TOKEN:
        notice('Park alerts', 'No Facebook secrets; nothing sent to Facebook.')
        return
    msg = f'{title}\n\n{text}'
    data = urllib.parse.urlencode({'access_token': FB_TOKEN, 'message': msg[:5000]}).encode()
    c, r = http(f'https://graph.facebook.com/{FB_ID}/feed', data)
    if c >= 300:
        notice('Park alerts', f'Facebook HTTP {c}: {r[:200]}')


# ---------------------------------------------------------------- the run
def main():
    now = ky_now()
    today = now.strftime('%Y-%m-%d')
    state = load(STATE_F, {})
    seen = state.get('seen') or {}
    pending = state.get('pending') or []
    burn_q = state.get('burn_queue') or []      # burns waiting for their once-a-day Facebook post

    live = {}
    broke = False
    for src in (ky_state_parks, nps_alerts, forest_alerts):
        got = src()
        if got is None:          # the source itself failed: do not treat its alerts as 'gone'
            broke = True
            continue
        live.update(got)
    if broke and not live:
        notice('Park alerts', 'No source answered this time; nothing changed.')
        return

    parks = ky_parks()
    opened, closed = [], []
    # A source being read for the first time (a new one added, or the NPS key finally set) arrives with everything
    # it has ever posted still live. Note those quietly: only what changes AFTER today is news.
    # when 'sources' has not been written yet, work out what we already knew from the alerts we are tracking,
    # otherwise the guard does nothing on the very run that needs it (Oct 21: 10 NPS notices went out that way)
    known = set(state.get('sources') or []) or {aid.split('-')[0] for aid in seen}
    fresh_src = {aid.split('-')[0] for aid in live} - known
    if fresh_src and known:
        for aid, a in live.items():
            if aid.split('-')[0] in fresh_src and aid not in seen:
                seen[aid] = {**a, 'first': today, 'runs': CONFIRM, 'missing': 0, 'announced': True,
                             'routine': bool(a.get('routine')) or bool(ROUTINE.search(a['title'] + ' ' + a['text'])),
                             'refs': match_parks(a, parks)}
        notice('Park alerts', 'New source(s) ' + ', '.join(sorted(fresh_src))
               + ': noted what is already up, nothing posted. Changes from now on will be.')
    state['sources'] = sorted(known | {aid.split('-')[0] for aid in live})

    # First ever run: just remember what is already up. Otherwise the club's first message from this bot would
    # be a list of notices that have been sitting on parks.ky.gov for months (the other KPC bots do the same).
    if not seen and not state.get('updated'):
        state.update({'updated': now.strftime('%Y-%m-%d %H:%M'), 'pending': [],
                      'sources': sorted({aid.split('-')[0] for aid in live}),
                      'seen': {aid: {**a, 'first': today, 'runs': CONFIRM, 'missing': 0, 'announced': True,
                                     'routine': bool(a.get('routine')),
                                     'refs': match_parks(a, parks)} for aid, a in live.items()}})
        if not DRY:
            STATE_F.parent.mkdir(parents=True, exist_ok=True)
            STATE_F.write_text(json.dumps(state, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
        notice('Park alerts', f'First run: noted {len(live)} alert(s) already up. Changes from now on will be posted.')
        return

    # 1. alerts that are up now
    for aid, a in live.items():
        rec = seen.get(aid)
        if not rec:
            seen[aid] = {**a, 'first': today, 'runs': 1, 'missing': 0, 'announced': False,
                         'routine': bool(a.get('routine')) or bool(ROUTINE.search(a['title'] + ' ' + a['text'])),
                         'refs': match_parks(a, parks)}
            continue
        rec.update({k: a[k] for k in ('title', 'text', 'link', 'who') if k in a})
        rec['runs'] = int(rec.get('runs', 0)) + 1
        rec['missing'] = 0
        if not rec.get('refs'):
            rec['refs'] = match_parks(a, parks)
        rec['routine'] = bool(a.get('routine')) or bool(ROUTINE.search(a['title'] + ' ' + a['text']))
        if not rec.get('announced') and rec['runs'] >= CONFIRM:
            rec['announced'] = True
            closed.append((aid, rec))

    # 2. alerts that have gone (the reopening nobody announces)
    for aid in list(seen):
        if aid in live:
            continue
        rec = seen[aid]
        if broke and aid.split('-')[0] in {k.split('-')[0] for k in live}:
            continue            # that source answered, so 'gone' is real; otherwise leave it alone
        rec['missing'] = int(rec.get('missing', 0)) + 1
        if rec['missing'] >= CONFIRM:
            if rec.get('announced') and not rec.get('routine'):
                opened.append((aid, rec))      # a burn finishing is not news
            seen.pop(aid, None)

    # 3. the red warnings on our own park pages
    if closed or opened:
        cond = load(COND_F, {'updated': today, 'items': []})
        items = [c for c in cond.get('items', []) if not str(c.get('id', '')).startswith('pa-')]
        for aid, rec in seen.items():
            days = ROUTINE_DAYS if rec.get('routine') else 30
            exp = (now + datetime.timedelta(days=days)).strftime('%Y-%m-%d')
            kind = 'Burn or forest work' if rec.get('routine') else 'Park alert'
            for ref in rec.get('refs') or []:
                items.append({'id': f'pa-{aid}-{ref}', 'ref': ref, 'kind': kind,
                              'details': (rec['title'] + ' — ' + rec['text'])[:400].strip(' —'),
                              'seen': rec.get('first', today), 'call': 'KPC BOT', 'expires': exp})
        items.sort(key=lambda c: (c['seen'], c['id']), reverse=True)
        cond['items'], cond['updated'] = items, today
        if not DRY:
            COND_F.write_text(json.dumps(cond, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')

    # 4. say something, unless it is the middle of the night
    for aid, rec in closed:
        # routine forest work only reaches the club when it is about one of OUR parks, and never Facebook
        if rec.get('routine') and not (rec.get('refs') or []):
            continue
        pending.append({'kind': 'closed', 'who': rec.get('who', ''), 'title': rec.get('title', ''),
                        'text': rec.get('text', ''), 'link': rec.get('link', ''),
                        'refs': rec.get('refs') or [], 'routine': bool(rec.get('routine'))})
    for aid, rec in opened:
        pending.append({'kind': 'open', 'who': rec.get('who', ''), 'title': rec.get('title', ''),
                        'refs': rec.get('refs') or []})

    quiet = now.hour >= QUIET_FROM or now.hour < QUIET_TO
    if pending and not quiet:
        shut = [p for p in pending if p['kind'] == 'closed' and not p.get('routine')]
        burns = [p for p in pending if p['kind'] == 'closed' and p.get('routine')]
        back = [p for p in pending if p['kind'] == 'open']
        L = []
        if shut:
            L.append('⚠️ **Heads up before you drive out:**' if len(shut) > 1 else '⚠️ **Heads up before you drive out**')
            for p in shut:
                where = ', '.join(p['refs']) + ' · ' if p['refs'] else ''
                L.append(f"• {where}**{p['title']}** ({p['who']})\n  {p['text']}" + (f"\n  {p['link']}" if p['link'] else ''))
        if burns:
            if L:
                L.append('')
            if len(burns) > 2:
                L.append(f'🔥 **{len(burns)} prescribed burns or forest jobs** listed at: '
                         + ', '.join(sorted({r for p in burns for r in p['refs']})))
            else:
                L.append('🔥 **Burning or forest work**')
                for p in burns:
                    L.append(f"• {', '.join(p['refs'])} · {p['title']} — {p['text'][:180]}")
        if back:
            if L:
                L.append('')
            L.append('✅ **Looks open again**')
            for p in back:
                where = ', '.join(p['refs']) + ' · ' if p['refs'] else ''
                L.append(f"• {where}**{p['title']}** ({p['who']}) — the notice has been taken down. "
                         f"Worth a quick check before you set off.")
        L.append('')
        L.append(f'Park notes and conditions: {SITE}kpc-park-notes.html')
        title = 'Kentucky park alert' + ('s' if len(pending) > 1 else '')
        text = '\n'.join(L)
        # Facebook gets the real news only: closures and reopenings. Burning and forest work are a club
        # detail, not something to put in front of the public every week.
        fb = []
        for p in shut:
            where = ', '.join(p['refs']) + ' · ' if p['refs'] else ''
            fb.append(f"- {where}{p['title']} ({p['who']})\n  {p['text']}" + (f"\n  {p['link']}" if p['link'] else ''))
        for p in back:
            where = ', '.join(p['refs']) + ' · ' if p['refs'] else ''
            fb.append(f"- {where}{p['title']} ({p['who']}) looks open again: the closure notice has been taken "
                      f"down. Worth a quick check before you set off.")
        burn_q += [{'refs': p['refs'], 'title': p['title'], 'text': p['text']} for p in burns]
        if DRY:
            print('WOULD POST (Discord):\n' + title + '\n' + text)
            print('WOULD POST (Facebook):\n' + ('\n'.join(fb) if fb else '(nothing: routine work only)'))
        else:
            post_discord(title, text)
            if fb:
                post_facebook(title, '\n'.join(fb) + f'\n\nPark notes and conditions: {SITE}kpc-park-notes.html')
        notice('Park alerts', f'posted {len(shut)} closed, {len(burns)} routine, {len(back)} reopened')
        pending = []
    elif pending:
        notice('Park alerts', f'{len(pending)} change(s) waiting for the morning (it is {now:%H:%M} in Kentucky)')

    # Burns on Facebook: once a day, all together (Brandon Oct 21: 'the burns can go to fb but maybe once a
    # day notices grouped together'). Still only burns that name one of our own parks, so it stays worth reading.
    if burn_q and not quiet and now.hour >= BURN_DIGEST_HOUR and state.get('burns_posted_on') != today:
        byref = {}
        for b in burn_q:
            for r in (b['refs'] or ['Kentucky parks']):
                byref.setdefault(r, []).append(b['title'])
        L = ['Burning and forest work going on at Kentucky parks. Smoke, closed roads and crews can all be part '
             'of it, so it is worth a look before you head out.', '']
        for r in sorted(byref):
            L.append(f'- {r}: ' + '; '.join(sorted(set(byref[r]))[:3]))
        L += ['', f'Park notes and conditions: {SITE}kpc-park-notes.html']
        msg = '\n'.join(L)
        if DRY:
            print('WOULD POST (Facebook, daily burn list):\n' + msg)
        else:
            post_facebook('Burning and forest work at Kentucky parks', msg)
            state['burns_posted_on'] = today
        notice('Park alerts', f'daily burn list posted to Facebook ({len(burn_q)} item(s))')
        burn_q = []

    state.update({'updated': now.strftime('%Y-%m-%d %H:%M'), 'seen': seen, 'pending': pending,
                  'burn_queue': burn_q[-40:]})
    if not DRY:
        STATE_F.parent.mkdir(parents=True, exist_ok=True)
        STATE_F.write_text(json.dumps(state, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    if not closed and not opened and not pending and not burn_q:
        notice('Park alerts', f'{len(live)} alert(s) up, nothing changed')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:  # noqa: BLE001
        notice('Park alerts', f'stopped early: {type(e).__name__}: {str(e)[:300]}')
        sys.exit(0)           # never fail the job: a failed run emails Brandon
