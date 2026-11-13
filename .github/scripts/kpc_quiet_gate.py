#!/usr/bin/env python3
"""Nov 10 2026 (quiet runs): skip a save that only carries BOOKKEEPING when this bot saved a little while ago.

Run inside the repo after 'git add' and the stamp filter, before 'git diff --cached --quiet' / 'git commit'.
Exit code 0 = go on and save as before. Exit code 3 = skip this save (everything staged is put back).
Nothing here ever fails a run: any doubt = save as before.

A staged change is BOOKKEEPING when it is only:
  - a file under data/status/ (boards, bot lines, grade queue, inbox lists),
    except data/status/key-check/last-<key>.json and data/status/key-check/<key>-<build>.json/.md
    (the key-check save the 2-fer run waits on; these always land)
  - data/waiting/heartbeat.json, verdicts-last.json, held-since.json (the waiting room's own notes; NOT the append-only verdicts log)
  - data/waiting/verdicts.json when no file's verdict changed (same path -> same verdict; only the check time / re-test counts moved)
Anything else staged (data, answer keys, waiting-room files, a new or deleted file) is MATERIAL: the save goes ahead at once,
and the bookkeeping rides along.
An ALARM also goes at once: a board line / bot line that turns red or amber.
The skip only happens when the same bot (the commit message up to the first ':') already saved within KPC_QUIET_HOURS hours
(default 3; 0 = off). The recent-save look is 'git log --since' on a shallow-since fetch; if it cannot be read, the save goes ahead.
Env: KPC_QUIET_MSG = the commit message, KPC_QUIET_HOURS."""
import json, os, re, subprocess, sys

# data/waiting/verdicts.jsonl(.gz) is NOT on this list: it is an append-only log, a skipped save would lose its new lines
BOOK = re.compile(r'^data/status/|^data/waiting/(heartbeat|verdicts-last|held-since)\.json$')
# Nov 13: last-<key>.json and the <key>-<build> report must always save. Yesterday the 3-hour
# bookkeeping skip dropped last-us.json for US-43293787778 and the US 2-fers sat waiting.
# Other key-check files (pin-cover, also-in, health, dropped) stay bookkeeping.
KEY_CHECK_MUST_SAVE = re.compile(
    r'^data/status/key-check/(last-(?:us|ca|world)\.json|(?:us|ca|world)-[^/]+\.(?:json|md))$')



def git(*a):
    r = subprocess.run(['git', *a], capture_output=True)
    return r.returncode, r.stdout.decode('utf-8', 'replace')


def load(spec):
    rc, out = git('show', spec)
    try: return json.loads(out) if rc == 0 else None
    except ValueError: return None


def verdicts(d):
    if not isinstance(d, dict): return None
    return {r.get('path'): r.get('verdict') for r in d.get('results') or [] if isinstance(r, dict)}


def is_book(f):
    if KEY_CHECK_MUST_SAVE.match(f): return False
    if BOOK.match(f): return True
    if f == 'data/waiting/verdicts.json':
        a, b = verdicts(load(f'HEAD:{f}')), verdicts(load(f':{f}'))
        return a is not None and a == b
    return False


def alarm(files):
    for f in files:
        if not (f.endswith('board.json') or '/status/bots/' in f): continue
        old, new = load(f'HEAD:{f}') or {}, load(f':{f}') or {}
        ro = old.get('bots', {'_': old}) if isinstance(old, dict) else {}
        rn = new.get('bots', {'_': new}) if isinstance(new, dict) else {}
        for k, r in rn.items():
            if isinstance(r, dict) and r.get('result') in ('red', 'amber') and (ro.get(k) or {}).get('result') != r.get('result'):
                return k
    return ''


def saved_recently(prefix, hours):
    if not prefix: return False
    rc, _ = git('fetch', '-q', f'--shallow-since={int(__import__("time").time() - hours * 3600)}', 'origin', 'main')
    if rc != 0: return False
    # the bot's own saves only: a subject that IS the prefix or starts with '<prefix>:' ('board' must not match 'flow board' / 'scoreboard')
    rc, out = git('log', '--format=%s', f'--since={int(hours * 3600)} seconds ago', 'FETCH_HEAD')
    if rc != 0: return False
    return any(s == prefix or s.startswith(prefix + ':') for s in out.splitlines())


def main():
    try: hours = float(os.environ.get('KPC_QUIET_HOURS', '3'))
    except ValueError: hours = 3.0
    if hours <= 0: return 0
    rc, out = git('diff', '--cached', '--name-only', '-z')
    files = [f for f in out.split('\0') if f] if rc == 0 else []
    if not files: return 0
    rc, other = git('diff', '--cached', '--name-only', '-z', '--diff-filter=ADRCT')
    if rc != 0: return 0
    # a new or deleted file is only bookkeeping when it is itself on the bookkeeping list
    if not all(is_book(f) for f in files): return 0
    a = alarm(files)
    if a:
        print(f'quiet gate: bookkeeping with an alarm ({a} turned amber/red): saved at once')
        return 0
    msg = os.environ.get('KPC_QUIET_MSG', '')
    prefix = msg.split(':', 1)[0].strip()
    if not saved_recently(prefix, hours): return 0
    print(f"::notice title=Quiet save::only bookkeeping changed ({len(files)} file(s)) and '{prefix}' saved within {hours:g} h: not saved this time")
    return 3


if __name__ == '__main__':
    try: rc = main()
    except Exception as e:  # noqa: BLE001
        print(f'quiet gate: left everything alone ({type(e).__name__}: {str(e)[:120]})'); rc = 0
    sys.exit(rc)
