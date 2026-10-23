#!/usr/bin/env python3
"""Daily bot check (Opus, Oct 23 2026; Brandon: 'I do want daily checks on bots'). Runs on GitHub, no Claude needed.

For every workflow that runs on a timer: did its last run fail, and has it run as often as its timer says it should?
Also checks that the files the bots keep fresh really are fresh (spots counts, park lists, search list, events).
Writes the whole picture into ONE GitHub issue (label bot-health; edits don't email). Only a NEW problem gets a comment
(which emails Brandon, per the house rule: email only for real issues). The issue closes itself when all is well.
Never fails (exit 0)."""
import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys

REPO = os.environ.get('GITHUB_REPOSITORY', 'KentuckyPortableClub/KPC-Links')
NOW = dt.datetime.now(dt.timezone.utc)
STATE = pathlib.Path('data/bot-health.json')
# files a bot keeps fresh: (file, most hours old before it is a problem, who keeps it)
FRESH = [('data/hunters/buckets.json', 4, 'KPC Hunters (saves once an hour)')]   # most bot files only change when the news does
SKIP = {'kpc-go-live.yml', 'kpc-chain.yml'}   # one-time jobs that are done


def gh(*a):
    r = subprocess.run(['gh', 'api', *a], capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None


def every_hours(crons):
    """roughly how often a workflow should run, from its cron lines (hours)"""
    best = 24 * 40
    for c in crons:
        f = c.split()
        if len(f) < 5: continue
        mi, ho, dom, mo, dow = f[:5]
        if dom != '*' and mo != '*': h = 24 * 370                   # once a year (go-live style)
        elif dom != '*': h = 24 * 32                              # monthly
        elif dow != '*': h = 24 * 7 / max(1, len(dow.split(',')))  # weekly
        elif ho == '*' or ho.startswith('*/'): h = max(0.1, (int(ho[2:]) if ho.startswith('*/') else 1) * (1 if not mi.startswith('*/') else int(mi[2:]) / 60))
        elif ',' in ho: h = 24 / len(ho.split(','))
        else: h = 24
        best = min(best, h)
    return best


def last_commit_age(path):
    r = subprocess.run(['git', 'log', '-1', '--format=%ct', '--', path], capture_output=True, text=True).stdout.strip()
    return (NOW.timestamp() - int(r)) / 3600 if r else None


def main():
    problems, ok = [], []
    for f in sorted(pathlib.Path('.github/workflows').glob('*.yml')):
        if f.name in SKIP: continue
        txt = f.read_text(encoding='utf-8')
        crons = re.findall(r"-\s*cron:\s*'([^']+)'", txt)
        if not crons: continue
        name = (re.search(r'^name:\s*(.+)$', txt, re.M) or [None, f.name])[1].strip()
        need = every_hours(crons)
        runs = gh(f'repos/{REPO}/actions/workflows/{f.name}/runs?per_page=5&event=schedule') or {}
        runs = runs.get('workflow_runs') or []
        done = [r for r in runs if r.get('status') == 'completed']
        fresh_file = last_commit_age(str(f))   # its timer was changed lately: give it time before calling it late
        grace = fresh_file is not None and fresh_file < max(need * 2.5, need + 26)
        if not done:
            if need < 24 * 30 and not grace: problems.append((f.name, f'{name}: no timed run found yet'))
            continue
        last = done[0]
        age = (NOW - dt.datetime.fromisoformat(last['created_at'].replace('Z', '+00:00'))).total_seconds() / 3600
        late = age > max(need * 2.5, need + 3)
        if last.get('conclusion') not in ('success', 'skipped', 'neutral', 'cancelled'):
            problems.append((f.name, f"{name}: last timed run ended '{last.get('conclusion')}' ({last['created_at'][:16]}Z) {last.get('html_url', '')}"))
        elif late and not grace:
            problems.append((f.name, f'{name}: has not run for {age:.0f} h (it should run about every {need:.0f} h)'))
        else:
            ok.append(f'{name} · last ran {age:.1f} h ago')
    for path, hrs, who in FRESH:
        a = last_commit_age(path)
        if a is None: problems.append((path, f'{path}: missing ({who})'))
        elif a > hrs: problems.append((path, f'{path}: last updated {a:.0f} h ago, should be under {hrs} h ({who})'))
    try:
        st = json.loads(STATE.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        st = {'open': []}
    keys = sorted({k for k, _ in problems})
    new = [k for k in keys if k not in st.get('open', [])]
    st['open'] = keys; st['checked'] = NOW.isoformat(timespec='minutes')
    STATE.write_text(json.dumps(st, indent=1) + '\n', encoding='utf-8')
    when = NOW.strftime('%b %d, %Y %H:%M UTC')
    body = (f'_Checked {when} by the daily bot check (.github/scripts/kpc_bot_health.py)._\n\n' +
            (('## ⚠ Needs a look (%d)\n' % len(problems)) + '\n'.join(f'- {m}' for _, m in problems) + '\n\n' if problems else '## ✅ Every bot ran on time and its last run worked.\n\n') +
            '<details><summary>Bots that are fine (%d)</summary>\n\n' % len(ok) + '\n'.join(f'- {x}' for x in ok) + '\n\n</details>\n')
    print(body)
    print(f'::notice title=Bot check::{len(problems)} problem(s), {len(new)} new, {len(ok)} bots fine', flush=True)
    if not os.environ.get('GITHUB_ACTIONS'): return
    iss = gh(f'repos/{REPO}/issues?labels=bot-health&state=all&per_page=1') or []
    title = ('⚠ Bot check: %d to look at' % len(problems)) if problems else '✅ Bot check: all bots fine'
    if iss:
        n = iss[0]['number']
        gh('-X', 'PATCH', f'repos/{REPO}/issues/{n}', '-f', f'title={title}', '-f', f'body={body}', '-f', 'state=' + ('open' if problems else 'closed'))
    elif problems:
        r = gh('-X', 'POST', f'repos/{REPO}/issues', '-f', f'title={title}', '-f', f'body={body}', '-f', 'labels[]=bot-health')
        n = r and r.get('number'); new = []   # a brand-new issue already emails once
    else:
        return
    if new and n:
        gh('-X', 'POST', f'repos/{REPO}/issues/{n}/comments', '-f', 'body=New problem(s) today:\n' + '\n'.join(f'- {m}' for k, m in problems if k in new))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f'::notice title=Bot check::stopped early: {e}')
    sys.exit(0)
