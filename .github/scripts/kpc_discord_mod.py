#!/usr/bin/env python3
"""The club bot as a moderator (Brandon Oct 21 2026: 'make him be able to boot people in rare circumstances
basically be a mod also').

Deliberately split in two, because the two halves carry very different risk:

  AUTOMATIC (mode 'watch'): only the obvious junk, and only reversible things. A brand-new account with no role
  that drops a Discord invite, a 'free nitro' style scam link, or tries to ping @everyone gets the message
  deleted and a one-hour mute, and the staff room is told who it was and why. That is all it will ever do on
  its own. It never kicks and never bans, because a bot that is 99% right about a stranger is still 100% wrong
  about the member it mistakes for one, and a kick cannot be taken back from a phone at a picnic table.

  BY HAND (mode 'do'): Brandon picks the person and the action - mute, unmute, kick or ban - from the workflow
  page, on a phone if need be. Kick and ban need the confirm box ticked as well, so a mis-tap cannot throw
  somebody out.

  LOOKING (mode 'who'): lists who has posted lately with their user id, so there is something to paste into
  'do' without digging through Discord's menus.

GUARDS that hold in every mode: never touches anybody listed in never_touch in data/discord-mod.json, never
touches another bot, and the automatic half never touches a member who has any role at all - in this club the
members have roles and a stranger who just walked in does not.

WORTH KNOWING: Discord's own AutoMod (Server Settings -> AutoMod) blocks spam, invite links and bad words the
instant they are typed, for free, with no bot involved. These bots run on a timer, so this one arrives minutes
later. AutoMod is the front door; this is the club's own record of what happened and the hand on the controls.

PRIVACY: this repo is public. The state file keeps only short one-way fingerprints, never names or message text.

Needs DISCORD_BOT_TOKEN, and the bot's role needs: Manage Messages (to delete), Moderate Members (to mute),
and - only if kick/ban are ever to be used - Kick Members and Ban Members. Give it no more than that, and keep
its role BELOW the members' roles so it cannot act on them even by mistake.
DRY_RUN=1 says what it would do and does nothing.
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
CONF_F = pathlib.Path('data/discord-mod.json')
WATCH_F = pathlib.Path('data/discord-watch.json')
STATE_F = pathlib.Path('data/discord-mod-state.json')
TOKEN = (os.environ.get('DISCORD_BOT_TOKEN') or '').strip()
HOOK = ((os.environ.get('KPC_ADMIN_WEBHOOK') or os.environ.get('KPC_DISCORD_WEBHOOK') or '').strip().split() or [''])[0]
MODE = (os.environ.get('MODE') or 'watch').strip().lower()
DRY = os.environ.get('DRY_RUN') == '1'
UA = {'User-Agent': 'KPC club bot (kentuckyportableclub.github.io)'}
MUTE_MINUTES = 60
MAX_ACTIONS = 5          # if more than a handful trips at once it is a raid: tell the staff, do not fight it alone


def notice(msg):
    print(f"::notice title=Mod::{str(msg)[:800]}", flush=True)


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
        return {'_error': f'HTTP {e.code} {e.read().decode("utf-8", "replace")[:200]}'}
    except Exception as e:  # noqa: BLE001
        return {'_error': str(e)[:200]}


def say(title, text, colour=0xC0392B):
    if not HOOK.startswith('https://'):
        notice(f'No staff webhook set; nothing posted. Would have said: {title}')
        print(title + '\n' + text)
        return 0
    body = json.dumps({'username': 'KPC', 'allowed_mentions': {'parse': []},
                       'embeds': [{'title': title[:250], 'color': colour, 'description': text[:4000]}]}).encode()
    try:
        req = urllib.request.Request(HOOK, body, headers={**UA, 'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=60) as r:
            r.read()
            return r.status
    except urllib.error.HTTPError as e:
        notice(f'Discord refused the staff post: HTTP {e.code}')
        return e.code
    except Exception as e:  # noqa: BLE001
        notice(f'Could not post to the staff room: {str(e)[:160]}')
        return 0


def load(p, d):
    try:
        return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
    except Exception:  # noqa: BLE001
        return d


def fingerprint(s):
    return hashlib.sha256(('kpc-mod:' + str(s)).encode()).hexdigest()[:16]


# ---------------------------------------------------------------- the obvious junk
# Keep every flag in flags=, never an inline (?i) partway through a pattern: Python refuses that at import and
# the script dies before printing anything (cost an hour on Oct 21).
JUNK = [
    ('a Discord invite link', re.compile(r'(discord\.(gg|io|me|li)|discordapp\.com/invite)/\S+', re.I)),
    ('a "free nitro / free gift" scam link', re.compile(
        r'(free\s*(nitro|gift|steam)|nitro\s*(giveaway|free)|steamcommunity\.\w+/gift|'
        r'\bairdrop\b|claim\s+your\s+(prize|reward))', re.I)),
    ('a try at pinging everybody', re.compile(r'@(everyone|here)\b', re.I)),
    ('a crypto or trading pitch', re.compile(
        r'(crypto|bitcoin|forex|binary option|investment)\w*\b.{0,40}\b(profit|earn|dm me|whatsapp|telegram)', re.I)),
]


def junk_in(text):
    return [why for why, pat in JUNK if pat.search(text or '')]


def member_of(gid, uid):
    return call(f'guilds/{gid}/members/{uid}')


def protected(conf, uid, member):
    """True = leave this person alone. Erring towards leaving people alone on purpose."""
    if str(uid) in {str(x) for x in (conf.get('never_touch') or [])}:
        return 'on the never-touch list'
    if isinstance(member, dict) and (member.get('user') or {}).get('bot'):
        return 'another bot'
    if isinstance(member, dict) and member.get('_error'):
        return 'I could not look them up, so I left them alone'
    if isinstance(member, dict) and (member.get('roles') or []):
        return 'has a role in the server, so not a stranger'
    return None


def mute(gid, uid, minutes, why):
    until = (datetime.datetime.now(datetime.timezone.utc)
             + datetime.timedelta(minutes=minutes)).isoformat().replace('+00:00', 'Z')
    return call(f'guilds/{gid}/members/{uid}', 'PATCH',
                {'communication_disabled_until': until, 'reason': why[:400]})


HELP = ("**What I can do from this room**\n"
        "```\n"
        "who                     who has posted lately, with their id\n"
        "mute <id> [mins] [why]  stop them talking (default 60 minutes)\n"
        "unmute <id>             let them talk again\n"
        "kick <id> confirm       remove them; they can return on a new invite\n"
        "ban <id> confirm        remove them for good\n"
        "help                    this list\n"
        "```\n"
        "Kick and ban need the word **confirm** in the same line, so a slip of the thumb cannot throw "
        "somebody out. I check this room every 15 minutes, so give me a moment.\n\n"
        "For something urgent, Discord is quicker than I am: hold your finger on the person's name, "
        "then Kick or Timeout. I am better for keeping the record and for when you are not in the app.")

CMD = re.compile(r'^\s*(who|help|mute|unmute|kick|ban)\b(.*)$', re.I)


def do_command(gid, conf, line):
    """One line typed in the staff room. Returns what to say back."""
    m = CMD.match(line or '')
    if not m:
        return None
    what, rest = m.group(1).lower(), (m.group(2) or '').strip()
    if what == 'help':
        return HELP
    if what == 'who':
        return 'who'                                  # handled by the caller, which can list the rooms
    uid = (re.search(r'\b(\d{15,22})\b', rest) or [None, ''])[1] if re.search(r'\b\d{15,22}\b', rest) else ''
    if not uid:
        return (f"I need the person's id for `{what}`. Say `who` and I will list everybody with their id, "
                f"or in Discord hold their name → Copy User ID (Settings → Advanced → Developer Mode turns "
                f"that on).")
    if str(uid) in {str(x) for x in (conf.get('never_touch') or [])}:
        return f"`{uid}` is on the never-touch list in data/discord-mod.json, so I left them alone."
    mem = member_of(gid, uid)
    name = ((mem.get('user') or {}).get('global_name') or (mem.get('user') or {}).get('username')
            or uid) if isinstance(mem, dict) else uid
    if isinstance(mem, dict) and mem.get('_error'):
        return f"I cannot find `{uid}` in the server ({mem['_error']}). Check the id with `who`."
    why = re.sub(r'\b\d{15,22}\b|\bconfirm\b|^\s*\d+\s*', '', rest, flags=re.I).strip(' .,-') or 'No reason given'

    if what in ('kick', 'ban') and not re.search(r'\bconfirm\b', rest, re.I):
        return (f"That would **{what} {name}**. Say it again with the word `confirm` on the end if you mean it:\n"
                f"`{what} {uid} confirm`")
    if what == 'mute':
        mins = int((re.search(r'\b(\d{1,5})\b(?!\d)', re.sub(r'\b\d{15,22}\b', '', rest)) or [0, 60])[1] or 60)
        mins = max(1, min(mins, 40320))
        r = mute(gid, uid, mins, why)
        good = f"Muted **{name}** for {mins} minute(s). Reason: {why}. Say `unmute {uid}` to lift it early."
    elif what == 'unmute':
        r = call(f'guilds/{gid}/members/{uid}', 'PATCH', {'communication_disabled_until': None})
        good = f"**{name}** can talk again."
    elif what == 'kick':
        r = call(f'guilds/{gid}/members/{uid}', 'DELETE')
        good = f"Removed **{name}** from the server. Reason: {why}. They can come back on a new invite."
    else:
        r = call(f'guilds/{gid}/bans/{uid}', 'PUT', {'delete_message_seconds': 0})
        good = f"Banned **{name}**. Reason: {why}. Lift it in Server Settings → Bans."
    if isinstance(r, dict) and r.get('_error'):
        return (f"I tried to {what} **{name}** and Discord said: `{r['_error']}`\n\n"
                f"That is usually my role missing the permission, or my role sitting below theirs. "
                f"Server Settings → Roles.")
    return good


def who_list(gid, watch):
    """Everybody who has posted in the club rooms lately, with the id to paste into a command."""
    seen = {}
    for room in (watch.get('rooms') or []):
        rid = str(room.get('id') if isinstance(room, dict) else room)
        name = (room.get('name') if isinstance(room, dict) else '') or rid
        msgs = call(f'channels/{rid}/messages?limit=50')
        if isinstance(msgs, dict):
            continue
        for m in msgs:
            a = m.get('author') or {}
            if a.get('bot') or not a.get('id'):
                continue
            seen.setdefault(a['id'], {'who': a.get('global_name') or a.get('username'), 'rooms': set()})
            seen[a['id']]['rooms'].add(name)
    if not seen:
        return 'Nobody has posted in the watched rooms lately.'
    L = ['**Who has posted lately**', '']
    for uid, v in sorted(seen.items(), key=lambda kv: (kv[1]['who'] or '').lower()):
        mem = member_of(gid, uid)
        roles = len(mem.get('roles') or []) if isinstance(mem, dict) else 0
        L.append(f"• **{v['who']}** · `{uid}` · {'has a role' if roles else 'no role'} · "
                 f"in #{', #'.join(sorted(v['rooms']))}")
    L.append('')
    L.append('Copy an id and say e.g. `mute <id> 60 spam` — or `help` for the whole list.')
    return '\n'.join(L)


def main():
    if not TOKEN:
        notice('No Discord bot token; nothing to do.')
        return
    conf = load(CONF_F, {})
    watch = load(WATCH_F, {})
    gid = str(conf.get('guild') or watch.get('guild') or os.environ.get('GUILD_ID') or '').strip()
    if not gid:
        notice('No server id; nothing to do.')
        return

    # ------------------------------------------------------------ commands typed in the staff room
    if MODE == 'commands':
        croom = str(conf.get('command_room') or '').strip()
        if not croom:
            notice('No command_room set in data/discord-mod.json; nothing to read.')
            return
        state = load(STATE_F, {})
        ran = set(state.get('commands') or [])
        first = not state.get('commands_from')
        msgs = call(f'channels/{croom}/messages?limit=25')
        if isinstance(msgs, dict):
            notice(f'Cannot read the command room: {msgs.get("_error")}')
            return
        did = 0
        for m in sorted(msgs, key=lambda x: x.get('timestamp', '')):
            if (m.get('author') or {}).get('bot'):
                continue
            fp = fingerprint('cmd' + str(m.get('id')))
            if fp in ran:
                continue
            ran.add(fp)
            if first or did >= 3:
                continue
            line = (m.get('content') or '').strip()
            if not CMD.match(line):
                continue
            out = do_command(gid, conf, line)
            if out == 'who':
                out = who_list(gid, watch)
            if not out:
                continue
            if DRY:
                print(f'--- would answer "{line}" ---\n{out}\n')
            else:
                call(f'channels/{croom}/messages', 'POST',
                     {'content': out[:1900], 'message_reference': {'message_id': m['id']},
                      'allowed_mentions': {'parse': []}})
            did += 1
        state['commands'] = sorted(ran)[-2000:]
        state['commands_from'] = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M')
        if not DRY:
            STATE_F.parent.mkdir(parents=True, exist_ok=True)
            STATE_F.write_text(json.dumps(state, indent=1) + '\n', encoding='utf-8')
        notice('First look at the command room; nothing run. Commands work from here on.' if first
               else (f'Ran {did} command(s).' if did else 'No commands waiting.'))
        return

    # ------------------------------------------------------------ who has posted lately
    if MODE == 'who':
        text = who_list(gid, watch)
        print(text) if DRY else say('Who has posted lately', text, 0x5865F2)
        # Also report where Discord drops its "somebody joined" message, so the welcome lands in the right room.
        g = call(f'guilds/{gid}')
        sysid = g.get('system_channel_id') if isinstance(g, dict) else None
        chans = call(f'guilds/{gid}/channels')
        if isinstance(chans, list):
            byid = {c.get('id'): c.get('name') for c in chans}
            notice(f'Joins are announced in: #{byid.get(sysid, "nowhere - the setting is off")} ({sysid})')
        notice('Listed who has posted lately.')
        return

    # ------------------------------------------------------------ Brandon picks somebody
    if MODE == 'do':
        uid = (os.environ.get('USER_ID') or '').strip()
        action = (os.environ.get('ACTION') or '').strip().lower()
        why = (os.environ.get('WHY') or '').strip() or 'No reason given'
        minutes = int((os.environ.get('MINUTES') or MUTE_MINUTES) or MUTE_MINUTES)
        confirmed = (os.environ.get('CONFIRM') or '').strip().lower() in ('1', 'true', 'yes')
        if not uid.isdigit():
            notice('No user id given (run mode "who" to get it). Nothing done.')
            return
        if action not in ('mute', 'unmute', 'kick', 'ban'):
            notice(f'I do not know the action "{action}". Nothing done.')
            return
        mem = member_of(gid, uid)
        name = ((mem.get('user') or {}).get('global_name') or (mem.get('user') or {}).get('username')
                or uid) if isinstance(mem, dict) else uid
        stop = str(uid) in {str(x) for x in (conf.get('never_touch') or [])}
        if stop:
            notice(f'{name} is on the never-touch list. Nothing done.')
            say('I did not do that', f'**{name}** is on the never-touch list in data/discord-mod.json, '
                                     f'so I left them alone. Take that line out first if this is really meant.')
            return
        if action in ('kick', 'ban') and not confirmed:
            notice(f'{action} needs the confirm box ticked. Nothing done.')
            say('That needs confirming',
                f'Somebody asked me to **{action} {name}**, but the confirm box was not ticked, so I did nothing. '
                f'Run it again and tick "yes, I mean it".', 0xE67E22)
            return
        if DRY:
            notice(f'Practice run: would {action} {name} ({uid}) - {why}')
            return
        if action == 'mute':
            r = mute(gid, uid, minutes, why)
            done = f'muted **{name}** for {minutes} minute(s)'
        elif action == 'unmute':
            r = call(f'guilds/{gid}/members/{uid}', 'PATCH', {'communication_disabled_until': None})
            done = f'unmuted **{name}**'
        elif action == 'kick':
            r = call(f'guilds/{gid}/members/{uid}', 'DELETE')
            done = f'removed **{name}** from the server (they can come back with a new invite)'
        else:
            r = call(f'guilds/{gid}/bans/{uid}', 'PUT', {'delete_message_seconds': 0})
            done = f'banned **{name}** (they cannot come back until the ban is lifted)'
        if isinstance(r, dict) and r.get('_error'):
            notice(f'Could not {action} {name}: {r["_error"]}')
            say('That did not work',
                f"I tried to {action} **{name}** and Discord said: `{r['_error']}`\n\n"
                f"Usually that means my role needs the matching permission, or my role sits above theirs in "
                f"Server Settings → Roles. It has to be below the members and above whoever is being moderated.",
                0xE67E22)
            return
        notice(f'{action} done for {name}.')
        say('Done', f"I {done}.\n**Reason given:** {why}\n\n_Asked for by hand from the workflow page._", 0x95A5A6)
        return

    # ------------------------------------------------------------ the automatic half
    rooms = watch.get('rooms') or []
    if not rooms:
        notice('No rooms to watch.')
        return
    state = load(STATE_F, {})
    done_fp = set(state.get('acted') or [])
    first_time = not state.get('updated')
    hits = []

    for room in rooms:
        rid = str(room.get('id') if isinstance(room, dict) else room)
        name = (room.get('name') if isinstance(room, dict) else '') or rid
        msgs = call(f'channels/{rid}/messages?limit=50')
        if isinstance(msgs, dict):
            notice(f'Cannot read #{name}: {msgs.get("_error")}')
            continue
        for m in msgs:
            a = m.get('author') or {}
            if a.get('bot') or not a.get('id'):
                continue
            text = m.get('content') or ''
            why = junk_in(text)
            if not why:
                continue
            fp = fingerprint(m.get('id'))
            if fp in done_fp:
                continue
            done_fp.add(fp)
            mem = member_of(gid, a['id'])
            leave = protected(conf, a['id'], mem)
            hits.append({'room': name, 'rid': rid, 'mid': m.get('id'), 'uid': a['id'],
                         'who': a.get('global_name') or a.get('username') or 'Someone',
                         'why': why, 'leave': leave,
                         'link': f"https://discord.com/channels/{gid}/{rid}/{m.get('id')}"})

    if first_time:
        notice(f'First run: noted {len(hits)} older message(s), did nothing. It acts on new ones from here.')
    elif not hits:
        notice('Nothing worth acting on.')
    elif len(hits) > MAX_ACTIONS:
        say('This looks like a raid, not one person',
            f"{len(hits)} messages tripped the spam check at once, across "
            f"{len({h['room'] for h in hits})} room(s). I have NOT acted on any of them: that many at once is "
            f"something a person should look at.\n\nIf it is a raid, Server Settings → Moderation → raise the "
            f"verification level, and turn on AutoMod if it is off.\n\n"
            + '\n'.join(f"• #{h['room']} · [message]({h['link']})" for h in hits[:10]))
        notice(f'{len(hits)} hits at once: told the staff, acted on none.')
    else:
        for h in hits:
            if h['leave']:
                say('Something odd, but I left it alone',
                    f"**{h['who']}** posted what looks like {', '.join(h['why'])} in **#{h['room']}**, but I did "
                    f"nothing because they {h['leave']}.\n\n[Look at it →]({h['link']})", 0xE67E22)
                continue
            acts = []
            if DRY:
                acts = ['(practice run, nothing actually done)']
            else:
                d = call(f"channels/{h['rid']}/messages/{h['mid']}", 'DELETE')
                acts.append('deleted the message' if not d.get('_error') else f"could not delete it ({d['_error']})")
                r = mute(gid, h['uid'], MUTE_MINUTES, 'KPC bot: ' + ', '.join(h['why']))
                acts.append(f'muted them for {MUTE_MINUTES} minutes'
                            if not r.get('_error') else f"could not mute them ({r['_error']})")
            say('I stepped in',
                f"**{h['who']}** (`{h['uid']}`) posted {', '.join(h['why'])} in **#{h['room']}**.\n\n"
                f"What I did: {'; '.join(acts)}.\n\n"
                f"The mute wears off by itself in {MUTE_MINUTES} minutes. I never kick or ban on my own — if they "
                f"should go, run the **KPC Discord mod** workflow with mode `do`, their id above, and tick confirm. "
                f"To let them talk again sooner, same workflow with action `unmute`.")
        notice(f'Acted on {len([h for h in hits if not h["leave"]])}, left {len([h for h in hits if h["leave"]])} alone.')

    state['acted'] = sorted(done_fp)[-4000:]
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
