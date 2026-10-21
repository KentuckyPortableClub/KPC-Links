#!/usr/bin/env python3
"""Watches the club's Discord rooms for a question nobody has answered (Brandon Oct 21 2026: 'can discord also
notify us if someone needs something from us' — he meant the club's own rooms: somebody asks for help, everyone
is out at a park, and nobody sees it for days).

WHAT IT DOES: reads the rooms listed in data/discord-watch.json, finds a message that looks like somebody asking
for something, that nobody has replied to, and that is older than the quiet time (an hour by default). It posts
a nudge to the staff room with a link to the message. One nudge per message, ever.

MODES (the MODE environment variable):
  list   - print every room the bot can see, so the rooms to watch can be chosen. Posts the list to the staff room.
  watch  - the normal job.

PRIVACY: this repo is public. The state file keeps only short one-way fingerprints of message ids, never names
and never what anybody wrote.

Needs: DISCORD_BOT_TOKEN (the relay bot; it must have View Channel + Read Message History in those rooms) and
KPC_ADMIN_WEBHOOK (or KPC_DISCORD_WEBHOOK). DRY_RUN=1 prints instead of posting.
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
CONF_F = pathlib.Path('data/discord-watch.json')
STATE_F = pathlib.Path('data/discord-watch-state.json')
TOKEN = (os.environ.get('DISCORD_BOT_TOKEN') or '').strip()
HOOK = ((os.environ.get('KPC_ADMIN_WEBHOOK') or os.environ.get('KPC_DISCORD_WEBHOOK') or '').strip().split() or [''])[0]
MODE = (os.environ.get('MODE') or 'watch').strip().lower()
DRY = os.environ.get('DRY_RUN') == '1'
UA = {'User-Agent': 'KPC club bot (kentuckyportableclub.github.io)'}
MAX_NUDGES = 5          # never more than a handful in one go


def notice(msg):
    print(f"::notice title=Discord watch::{str(msg)[:800]}", flush=True)


def call(path, token=True):
    h = dict(UA)
    if token:
        h['Authorization'] = 'Bot ' + TOKEN
    try:
        with urllib.request.urlopen(urllib.request.Request(API + path, headers=h), timeout=60) as r:
            return json.loads(r.read().decode('utf-8', 'replace'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', 'replace')[:200]
        return {'_error': f'HTTP {e.code} {body}'}
    except Exception as e:  # noqa: BLE001
        return {'_error': str(e)[:200]}


def say(title, text):
    if not HOOK.startswith('https://'):
        notice('No staff webhook set; nothing posted.')
        print(title + '\n' + text)
        return
    body = json.dumps({'username': 'KPC', 'allowed_mentions': {'parse': []},
                       'embeds': [{'title': title[:250], 'color': 0x5865F2, 'description': text[:4000]}]}).encode()
    try:
        req = urllib.request.Request(HOOK, body, headers={**UA, 'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=60) as r:
            r.read()
    except Exception as e:  # noqa: BLE001
        notice(f'Could not post: {str(e)[:200]}')


def fingerprint(s):
    return hashlib.sha256(('kpc-dc:' + str(s)).encode()).hexdigest()[:16]


ASKS = re.compile(r'\?|(?i)\b(how do i|how can i|can (someone|somebody|anyone)|does anyone|anybody know|'
                  r'help|stuck|not working|won\'t work|any idea|question|where (is|do|can)|when (is|do)|'
                  r'what (is|are|do)|is there a?\s*way|need (help|a hand|advice))\b')


def main():
    if not TOKEN:
        notice('No Discord bot token; nothing to do.')
        return
    conf = {}
    try:
        conf = json.loads(CONF_F.read_text(encoding='utf-8'))
    except Exception:  # noqa: BLE001
        pass

    if MODE == 'list':
        gid = str(conf.get('guild') or os.environ.get('GUILD_ID') or '').strip()
        if not gid:
            notice('No server id. Put {"guild": "..."} in data/discord-watch.json or set GUILD_ID.')
            return
        chans = call(f'guilds/{gid}/channels')
        if isinstance(chans, dict):
            notice('Could not list the rooms: ' + str(chans.get('_error'))[:200])
            return
        kinds = {0: 'text', 2: 'voice', 4: 'category', 5: 'news', 15: 'forum'}
        rooms = [c for c in chans if c.get('type') in (0, 5, 15)]
        rooms.sort(key=lambda c: (c.get('position') or 0))
        L = ['These are the rooms I can see. Tell Claude which ones to watch and he will set them up.', '']
        for c in rooms:
            L.append(f"• **#{c.get('name')}** · `{c.get('id')}` · {kinds.get(c.get('type'), '?')}")
        L.append('')
        L.append('If a room is missing, the bot has not been given "View Channel" and "Read Message History" there.')
        text = '\n'.join(L)
        if DRY:
            print(text)
        else:
            say(f'Discord rooms I can see ({len(rooms)})', text)
        notice(f'Listed {len(rooms)} room(s).')
        return

    rooms = conf.get('rooms') or []
    if not rooms:
        notice('No rooms to watch yet (data/discord-watch.json "rooms" is empty).')
        return
    quiet = int(conf.get('quiet_minutes') or 60)
    state = {}
    try:
        state = json.loads(STATE_F.read_text(encoding='utf-8'))
    except Exception:  # noqa: BLE001
        pass
    done = set(state.get('flagged') or [])
    first_time = not state.get('updated')
    now = datetime.datetime.now(datetime.timezone.utc)
    found = []

    for room in rooms:
        rid = str(room.get('id') if isinstance(room, dict) else room)
        name = (room.get('name') if isinstance(room, dict) else '') or rid
        msgs = call(f'channels/{rid}/messages?limit=50')
        if isinstance(msgs, dict):
            notice(f'Cannot read #{name}: ' + str(msgs.get('_error'))[:160])
            continue
        msgs = sorted(msgs, key=lambda m: m.get('timestamp', ''))
        for i, m in enumerate(msgs):
            if (m.get('author') or {}).get('bot'):
                continue
            text = (m.get('content') or '').strip()
            if len(text) < 8 or not ASKS.search(text):
                continue
            try:
                when = datetime.datetime.fromisoformat(m['timestamp'].replace('Z', '+00:00'))
            except Exception:  # noqa: BLE001
                continue
            age = (now - when).total_seconds() / 60
            if age < quiet or age > 60 * 24 * 7:
                continue
            who = (m.get('author') or {}).get('id')
            answered = any(not (x.get('author') or {}).get('bot') and (x.get('author') or {}).get('id') != who
                           for x in msgs[i + 1:])
            if answered:
                continue
            fp = fingerprint(m.get('id'))
            if fp in done:
                continue
            done.add(fp)
            found.append({'room': name, 'who': ((m.get('author') or {}).get('global_name')
                                                or (m.get('author') or {}).get('username') or 'Someone'),
                          'text': re.sub(r'\s+', ' ', text)[:600], 'hours': round(age / 60, 1),
                          'link': f"https://discord.com/channels/{conf.get('guild')}/{rid}/{m.get('id')}"})

    if first_time:
        notice(f'First run: noted {len(found)} older message(s), nothing sent. New ones from now on.')
        found = []
    elif found:
        for f in found[:MAX_NUDGES]:
            body = (f"**{f['who']}** asked in **#{f['room']}** about {f['hours']} hour(s) ago and nobody has "
                    f"replied:\n> {f['text']}\n\n[Go and answer →]({f['link']})")
            if DRY:
                print(body + '\n---')
            else:
                say('Somebody asked and nobody answered', body)
        notice(f'Nudged about {min(len(found), MAX_NUDGES)} message(s).')
    else:
        notice('Nothing unanswered.')

    state['flagged'] = sorted(done)[-4000:]
    state['updated'] = now.strftime('%Y-%m-%d %H:%M')
    if not DRY:
        STATE_F.parent.mkdir(parents=True, exist_ok=True)
        STATE_F.write_text(json.dumps(state, indent=1) + '\n', encoding='utf-8')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:  # noqa: BLE001
        notice(f'stopped early: {type(e).__name__}: {str(e)[:300]}')
        sys.exit(0)          # never fail the job: a failed run emails Brandon
