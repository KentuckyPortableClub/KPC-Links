#!/usr/bin/env python3
"""'Something new on the website' post (Brandon Oct 21 2026: 'add a new pages post if something big gets added…
not small changes but larger things').

A bot cannot judge whether a change is big, so it does not try. Whoever adds something worth telling people about
writes one line into data/kpc-whats-new.json, and this posts it once, to Discord and the club's Facebook Page.
Nothing waiting = no post, ever. Typos, tweaks and tidying never go in the file, so they are never announced.

THE FILE: {"items": [{"id", "title", "text", "link", "added", "posted"}]}
  id     short name, e.g. "park-control-2026-10"   (must be unique; it is what stops a repeat post)
  title  what it is, in a few words: "A new map of every Kentucky park"
  text   one or two plain sentences about why someone would care
  link   the page, full address
  added  YYYY-MM-DD
  posted left out or false = still to post. The bot sets it to true once it has gone out.

Run with DRY_RUN=1 to see what it would say. Secrets: KPC_DISCORD_WEBHOOK, FB_PAGE_ID, FB_PAGE_TOKEN.
"""
import datetime
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

SITE = 'https://kentuckyportableclub.github.io/KPC-Links/'
F = pathlib.Path('data/kpc-whats-new.json')
UA = {'User-Agent': 'KPC club bot (kentuckyportableclub.github.io)'}
DRY = os.environ.get('DRY_RUN') == '1'
DISCORD = (os.environ.get('KPC_DISCORD_WEBHOOK') or '').strip()
FB_ID = (os.environ.get('FB_PAGE_ID') or '').strip()
FB_TOKEN = (os.environ.get('FB_PAGE_TOKEN') or '').strip()
MAX_AT_ONCE = 4          # more than a handful at once reads like a changelog, not news


def notice(msg):
    print(f"::notice title=What's new::{str(msg)[:800]}", flush=True)


def http(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:  # noqa: BLE001
        return 0, str(e)


def main():
    try:
        data = json.loads(F.read_text(encoding='utf-8'))
    except Exception:  # noqa: BLE001
        notice('No data/kpc-whats-new.json yet; nothing to post.')
        return
    items = data.get('items') or []
    todo = [i for i in items if not i.get('posted') and i.get('title')]
    if not todo:
        notice('Nothing new waiting; no post.')
        return
    todo.sort(key=lambda i: str(i.get('added') or ''))
    if len(todo) > MAX_AT_ONCE:
        notice(f'{len(todo)} waiting; posting the oldest {MAX_AT_ONCE}, the rest follow next time.')
        todo = todo[:MAX_AT_ONCE]

    one = len(todo) == 1
    title = 'New on the KPC website' if one else f'{len(todo)} new things on the KPC website'
    L = []
    for i in todo:
        L.append(f"**{i['title']}**")
        if i.get('text'):
            L.append(i['text'])
        if i.get('link'):
            L.append(i['link'])
        L.append('')
    L.append('Everything we build is free and works on a phone at the picnic table. 73, KPC')
    body = '\n'.join(L).strip()

    ok = True
    if DRY:
        print('WOULD POST:\n' + title + '\n' + body)
    else:
        if DISCORD.startswith('https://'):
            d = json.dumps({'username': 'KPC', 'allowed_mentions': {'parse': []},
                            'embeds': [{'title': title[:250], 'color': 0xd5a63a, 'description': body[:4000],
                                        'url': todo[0].get('link') or SITE}]}).encode()
            c, r = http(DISCORD, d, {'Content-Type': 'application/json'})
            if c >= 300:
                notice(f'Discord HTTP {c}: {r[:200]}')
                ok = False
        else:
            notice('No Discord webhook set; skipped Discord.')
        if FB_ID and FB_TOKEN:
            msg = body.replace('**', '')
            q = {'access_token': FB_TOKEN, 'message': f'{title}\n\n{msg}'}
            if one and todo[0].get('link'):
                q['link'] = todo[0]['link']
            c, r = http(f'https://graph.facebook.com/{FB_ID}/feed', urllib.parse.urlencode(q).encode())
            if c >= 300:
                notice(f'Facebook HTTP {c}: {r[:200]}')
                ok = False
        else:
            notice('No Facebook secrets; skipped Facebook.')

    if ok and not DRY:
        ids = {i.get('id') for i in todo}
        for i in items:
            if i.get('id') in ids:
                i['posted'] = True
                i['posted_on'] = datetime.date.today().isoformat()
        data['items'] = items
        F.write_text(json.dumps(data, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
        notice(f'Posted {len(todo)} thing(s).')
    elif not ok:
        notice('Something did not send, so nothing was marked as posted; it will try again next time.')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:  # noqa: BLE001
        notice(f'stopped early: {type(e).__name__}: {str(e)[:300]}')
        sys.exit(0)          # never fail the job: a failed run emails Brandon
