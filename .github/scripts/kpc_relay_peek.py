#!/usr/bin/env python3
"""RELAY QUICK LOOK (PR3, Nov 2 2026; Brandon: 'a lot of these bots dont have to run that much').
The KPC Mailer Apps Script starts the Discord relay every few minutes so a club post goes out fast. Most of those starts find
nothing new, but each one still installed tools, read 100 Discord messages and ran three more Discord bots. This look runs
first on STARTED (workflow_dispatch) runs only and decides in a few seconds:
  FULL run  when the relay channel has a message newer than the last one shared (Discord's last_message_id), an email is
            waiting in the queue (6 AM-9 PM Central), a scheduled post is due, the last FULL run is 14+ minutes old (so edits,
            deletes and the club-room helpers still run at least every ~15 min even when GitHub skips the relay's own timer),
            the run was started with full=true, or anything here cannot be read (when in doubt, do the full run);
  QUICK end otherwise (writes skip=1 for the workflow; the heartbeat and the report still run).
Scheduled runs never call this: they always do the full run. Never prints a secret. Never fails (any error = full run).
  env DISCORD_BOT_TOKEN, KPC_RELAY_CHANNEL, GH_TOKEN, GITHUB_REPOSITORY, GITHUB_OUTPUT, FULL"""
import datetime as dt, json, os, subprocess, sys, urllib.request
from zoneinfo import ZoneInfo

CT = ZoneInfo('America/Chicago')
NOW = dt.datetime.now(dt.timezone.utc)
FULL_EVERY_MIN = 14
UA = 'KPC-Relay (https://kentuckyportableclub.github.io/KPC-Links/, 2.0)'


def out(skip, why):
    print(f"::notice title=Relay quick look::{'nothing new: quick end' if skip else 'full run'} ({why})", flush=True)
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f: f.write(f"skip={'1' if skip else '0'}\n")
    sys.exit(0)


def last_full_age_min():
    """Minutes since the newest relay run whose 'Share new posts' step really ran (not skipped by this look)."""
    repo = os.environ.get('GITHUB_REPOSITORY', 'KentuckyPortableClub/KPC-Links')
    me = os.environ.get('GITHUB_RUN_ID', '')
    r = subprocess.run(['gh', 'api', f'repos/{repo}/actions/workflows/kpc-discord-relay.yml/runs?per_page=8', '--jq',
                        '.workflow_runs[] | [.id, .created_at, .status] | @tsv'], capture_output=True, text=True, timeout=30)
    if r.returncode != 0: return None
    for line in r.stdout.splitlines():
        rid, created, status = line.split('\t')
        if rid == me: continue
        j = subprocess.run(['gh', 'api', f'repos/{repo}/actions/runs/{rid}/jobs', '--jq',
                            '[.jobs[].steps[]? | select(.name == "Share new posts") | .conclusion // .status] | first // ""'],
                           capture_output=True, text=True, timeout=30)
        c = j.stdout.strip()
        if c in ('success', 'failure', 'in_progress', 'queued', 'pending'):   # a run that did (or is doing) the full work
            return (NOW - dt.datetime.fromisoformat(created.replace('Z', '+00:00'))).total_seconds() / 60
    return 9999.0   # none of the last 8 did the full work


def main():
    if (os.environ.get('FULL') or '').lower() in ('1', 'true', 'yes'): out(False, 'started with full=true')
    try: st = json.load(open('kpc-relay-state.json', encoding='utf-8'))
    except Exception: out(False, 'relay state not readable')  # noqa: BLE001
    ct = NOW.astimezone(CT)
    if st.get('queue') and 6 <= ct.hour < 21: out(False, f"{len(st['queue'])} email(s) waiting")
    due = st.get('due') or ''
    if due:
        try:
            d = dt.datetime.fromisoformat(due)
            if d.tzinfo is None: d = d.replace(tzinfo=CT)
            if d <= NOW + dt.timedelta(minutes=2): out(False, f'a scheduled post is due ({due})')
        except ValueError: out(False, f'scheduled time not readable ({due!r})')
    age = last_full_age_min()
    if age is None: out(False, 'could not read the last runs')
    if age >= FULL_EVERY_MIN: out(False, f'last full run {age:.0f} min ago')
    tok, chan = (os.environ.get('DISCORD_BOT_TOKEN') or '').strip(), (os.environ.get('KPC_RELAY_CHANNEL') or '').strip()
    if not tok or not chan: out(False, 'Discord secrets not set here')
    try:
        req = urllib.request.Request(f'https://discord.com/api/v10/channels/{chan}',
                                     headers={'Authorization': f'Bot {tok}', 'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=20) as r: newest = str(json.load(r).get('last_message_id') or '0')
    except Exception as e: out(False, f'Discord not readable ({type(e).__name__})')  # noqa: BLE001
    last = str(st.get('last_id') or '0')
    if newest.isdigit() and last.isdigit() and int(newest) <= int(last):
        out(True, f'no new message since the last one shared; last full run {age:.0f} min ago')
    out(False, 'a new message in the relay channel')


if __name__ == '__main__':
    try: main()
    except SystemExit: raise
    except Exception as e: out(False, f'look stopped ({type(e).__name__})')  # noqa: BLE001
