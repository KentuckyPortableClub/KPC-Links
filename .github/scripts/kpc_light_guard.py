#!/usr/bin/env python3
"""LIGHT GUARD before a bot saves a site file (chat 10, Oct 30 2026; Brandon 6:07 AM 'Yes' to the hold list, HQ 6:10 AM step C).
For bots whose rows are already approved (park + campground notes: Brandon's YES on the form) or are public dates that fix
themselves next run (special events, contests, events). A file passes when, for every list in it:
  - it did not shrink by half or more (only judged when the saved copy had 4+ rows: removing one note is normal), and
  - no row appears twice (same id, or the same name + start / when).
A file that fails is put back to the saved copy (the site keeps yesterday's list) and ONE line goes to chat 11's inbox
(.claude/inbox/chat-11.md, once per file per day). Run before `git add`:
  python3 .github/scripts/kpc_light_guard.py kpc-special-events.json kpc-contests.json
Never fails (any doubt = the file is left alone)."""
import datetime as dt, json, pathlib, subprocess, sys

INBOX = pathlib.Path('.claude/inbox/chat-11.md')


def key(r):
    if not isinstance(r, dict): return json.dumps(r, sort_keys=True)
    if r.get('id'): return 'id:' + str(r['id'])
    return '|'.join(str(r.get(k) or '') for k in ('name', 'title', 'ref', 'call', 'start', 'when', 'date', 'url', 'segs'))


def lists(d):
    return {k: v for k, v in d.items() if isinstance(v, list)} if isinstance(d, dict) else {'': d} if isinstance(d, list) else {}


def check(f):
    old = subprocess.run(['git', 'show', f'HEAD:{f}'], capture_output=True, text=True)
    if old.returncode != 0: return []
    try: o, n = json.loads(old.stdout), json.load(open(f, encoding='utf-8'))
    except ValueError: return [f'{f} does not read as JSON']
    bad = []
    lo, ln = lists(o), lists(n)
    for k, rows in lo.items():
        new = ln.get(k, [])
        if len(rows) >= 4 and len(new) <= len(rows) / 2: bad.append(f"'{k}' {len(rows)} -> {len(new)} rows (shrank by half)")
    for k, rows in ln.items():
        ks = [key(r) for r in rows]
        d = len(ks) - len(set(ks))
        if d: bad.append(f"'{k}' has {d} row(s) twice")
    return bad


def main():
    today = dt.date.today().isoformat()
    for f in sys.argv[1:]:
        try:
            if not pathlib.Path(f).exists(): continue
            bad = check(f)
            if not bad: continue
            subprocess.run(['git', 'checkout', 'HEAD', '--', f], check=False)
            why = '; '.join(bad)[:300]
            print(f'::notice title=Light guard::{f} HELD (the saved copy stays): {why}')
            line = f"- FROM LIGHT GUARD ({today}): `{f}` held, the site keeps the last good copy: {why}. Look at the bot's last run; the next clean run saves again."
            if INBOX.exists():
                t = INBOX.read_text(encoding='utf-8')
                if f"LIGHT GUARD ({today}): `{f}`" not in t:
                    i = t.find('\n- ')
                    INBOX.write_text(t[:i] + '\n' + line + t[i:] if i >= 0 else t + '\n' + line + '\n', encoding='utf-8')
        except Exception as e:  # noqa: BLE001
            print(f'::notice title=Light guard::{f}: not checked ({type(e).__name__})')
    sys.exit(0)


if __name__ == '__main__':
    main()
