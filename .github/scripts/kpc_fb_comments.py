#!/usr/bin/env python3
"""KPC Facebook comment watcher (Brandon Oct 21 2026: 'if someone comments on your post can discord bot alert us').

Reads new comments on the club's Facebook Page posts and sends them to Discord, with a link to reply and,
when the comment looks like a question we answer often, a ready-to-paste reply underneath. It never replies
on Facebook itself: a person does that, so the club always sounds like a person.

PRIVACY: this repo is public, so nothing a visitor wrote is ever saved here. The state file keeps only
short one-way fingerprints of the comment ids it has already sent, never names, never text.

NEEDS: the Page token must have pages_read_user_content (reading what visitors wrote is a different
permission from posting). Without it this says so once in Discord and then stays quiet.
Secrets: FB_PAGE_ID, FB_PAGE_TOKEN, KPC_DISCORD_WEBHOOK. DRY_RUN=1 prints instead of sending.
"""
import datetime
import hashlib
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

SITE = 'https://kentuckyportableclub.github.io/KPC-Links/'
STATE_F = pathlib.Path('data/fb-comments-state.json')
GRAPH = 'https://graph.facebook.com/v21.0/'
UA = {'User-Agent': 'KPC club bot (kentuckyportableclub.github.io)'}
DRY = os.environ.get('DRY_RUN') == '1'
FB_ID = (os.environ.get('FB_PAGE_ID') or '').strip()
FB_TOKEN = (os.environ.get('FB_PAGE_TOKEN') or '').strip()
# Posts here are for whoever looks after the club, not general chat, so they go to KPC_ADMIN_WEBHOOK when
# there is one (make a webhook for a staff room and save it under that name); otherwise the usual room.
DISCORD = ((os.environ.get('KPC_ADMIN_WEBHOOK') or os.environ.get('KPC_DISCORD_WEBHOOK') or '')).strip()
LOOK_BACK_DAYS = 21          # only watch posts from the last few weeks
MAX_PER_RUN = 10             # if something goes viral, don't flood the channel

# What we get asked, and what to say back. First match wins, so put the specific ones first.
ANSWERS = [
    (r'campout|camp out|camping trip|2027|taylorsville',
     "The 2nd Annual KY POTA Campout is September 24-26, 2027 at Taylorsville Lake State Park (US-1271). "
     "Group tent sites are reserved and spots are open now - all the details, including how to reserve, are here: "
     + SITE + "campout.html"),
    (r'\bjoin\b|become a member|sign up|membership|how do i get in',
     "We'd love to have you. Everything about joining is on this page: " + SITE + "join.html"),
    (r'\bmap\b|where (is|are) the park|what parks|park control|boundar',
     "Our park map shows every POTA park, KFF reference and SOTA summit in Kentucky on one map, with boundaries "
     "and parking: " + SITE + "kpc-park-control.html"),
    (r'park note|access|gate|parking|where do i set up|cell signal',
     "Park notes have the practical stuff - parking, where to set up, gates and cell signal - written by people "
     "who have been there: " + SITE + "kpc-park-notes.html"),
    (r'campground|camping|cabin|lodge|stay overnight|where to stay',
     "Campgrounds and cabins inside Kentucky parks, with booking links: " + SITE + "kpc-campgrounds.html"),
    (r'\bsota\b|summit',
     "Here's our Kentucky SOTA guide: " + SITE + "kpc-guide-sota.html"),
    (r'\bwwff\b|\bkff\b',
     "Here's our Kentucky WWFF/KFF guide: " + SITE + "kpc-guide-wwff.html"),
    (r'\bpota\b|parks on the air|how do i (start|activate)|get started|new to',
     "Our Kentucky POTA guide walks through it from the beginning: " + SITE + "kpc-guide-pota.html"),
    (r'event|hamfest|when is|calendar|meet ?up',
     "Our events calendar has what's coming up: " + SITE + "events.html"),
    (r'who is on|on the air|spots?\b|activat(ing|or) now',
     "You can see who's on the air right now here: " + SITE + "kpc-spots.html"),
    (r'contact|email|phone|get in touch|talk to someone',
     "The best way to reach us is here: " + SITE + "contact.html"),
    (r'video|youtube|channel',
     "Our videos are on the site here: " + SITE + "videos.html"),
]


def notice(msg):
    print(f"::notice title=Facebook comments::{str(msg)[:800]}", flush=True)


def http(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:  # noqa: BLE001
        return 0, str(e)


def graph(path, **q):
    q['access_token'] = FB_TOKEN
    c, body = http(GRAPH + path + '?' + urllib.parse.urlencode(q))
    try:
        return c, json.loads(body)
    except Exception:  # noqa: BLE001
        return c, {'error': {'message': body[:200]}}


def fingerprint(s):
    return hashlib.sha256(('kpc-fb:' + str(s)).encode()).hexdigest()[:16]


def suggest(text):
    t = (text or '').lower()
    for pat, ans in ANSWERS:
        if re.search(pat, t):
            return ans
    return None


def discord(title, text):
    if not DISCORD.startswith('https://'):
        notice('No Discord webhook set; nothing sent.')
        return
    body = {'username': 'KPC Facebook', 'allowed_mentions': {'parse': []},
            'embeds': [{'title': title[:250], 'color': 0x4267B2, 'description': text[:4000]}]}
    c, r = http(DISCORD, json.dumps(body).encode(), {'Content-Type': 'application/json'})
    if c >= 300:
        notice(f'Discord HTTP {c}: {r[:200]}')


def main():
    if not FB_ID or not FB_TOKEN:
        notice('No Facebook secrets set; nothing to do.')
        return
    state = {}
    try:
        state = json.loads(STATE_F.read_text(encoding='utf-8'))
    except Exception:  # noqa: BLE001
        pass
    done = set(state.get('sent') or [])
    first_time = not state.get('updated')

    since = int((datetime.datetime.now(datetime.timezone.utc)
                 - datetime.timedelta(days=LOOK_BACK_DAYS)).timestamp())
    c, j = graph(f'{FB_ID}/posts', fields='id,created_time,permalink_url', limit='25', since=str(since))
    posts = j.get('data') or []
    if not posts:
        notice('Could not read the Page posts: ' + str(j.get('error', {}).get('message'))[:200])
        return

    fresh = []
    blocked = None
    for p in posts:
        c, j = graph(f"{p['id']}/comments", fields='id,created_time,from,message,permalink_url',
                     limit='50', order='reverse_chronological', filter='stream')
        if 'data' not in j:
            e = j.get('error') or {}
            if e.get('code') in (10, 200, 190):
                blocked = str(e.get('message'))[:300]
                break
            continue
        for cm in j['data']:
            fp = fingerprint(cm.get('id'))
            if fp in done:
                continue
            done.add(fp)
            who = ((cm.get('from') or {}).get('name') or 'Someone').strip()
            if who.lower() == 'kentucky portable club':
                continue
            fresh.append({'who': who, 'msg': re.sub(r'\s+', ' ', cm.get('message') or '').strip(),
                          'link': cm.get('permalink_url') or p.get('permalink_url') or '',
                          'when': cm.get('created_time', '')})

    if blocked:
        if not state.get('told_blocked'):
            state['told_blocked'] = True
            if not DRY:
                discord('Facebook comments: one permission short',
                        "I can post to the Page, but Facebook won't let me read what people write underneath, so "
                        "comments can't be passed on yet.\n\n"
                        "The Page token needs **pages_read_user_content** added, then the `FB_PAGE_TOKEN` secret "
                        "updated in GitHub. After that, new comments will show up here.\n\n"
                        "Nothing else is affected: posting to Facebook carries on as normal. "
                        "This message is only sent once.")
        notice('Cannot read comments yet: ' + blocked)
    elif first_time:
        notice(f'First run: noted {len(fresh)} existing comment(s). New ones from now on will go to Discord.')
        fresh = []
    else:
        fresh.sort(key=lambda x: x['when'])
        if len(fresh) > MAX_PER_RUN:
            notice(f'{len(fresh)} new comments; sending the first {MAX_PER_RUN}.')
            fresh = fresh[:MAX_PER_RUN]
        for f in fresh:
            body = f"**{f['who']}** wrote:\n> {f['msg'][:900] or '(a photo or sticker)'}\n"
            tip = suggest(f['msg'])
            if tip:
                body += f"\n**Something you could say back:**\n{tip}\n"
            if f['link']:
                body += f"\n[Reply on Facebook →]({f['link']})"
            if DRY:
                print('WOULD SEND:\n' + body + '\n---')
            else:
                discord('New comment on our Facebook post', body)
        if fresh:
            notice(f'Sent {len(fresh)} new comment(s) to Discord.')
        else:
            notice('No new comments.')

    state['sent'] = sorted(done)[-4000:]
    state['updated'] = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M')
    if not DRY:
        STATE_F.parent.mkdir(parents=True, exist_ok=True)
        STATE_F.write_text(json.dumps(state, indent=1) + '\n', encoding='utf-8')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:  # noqa: BLE001
        notice(f'stopped early: {type(e).__name__}: {str(e)[:300]}')
        sys.exit(0)          # never fail the job: a failed run emails Brandon
