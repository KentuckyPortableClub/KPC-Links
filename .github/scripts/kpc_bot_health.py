#!/usr/bin/env python3
"""KPC CHECK-UP report (was the daily bot check: Opus, Oct 23 2026; grown into the nightly check-up by chat 5, Oct 26 2026,
Brandon GO 11:50 AM). Runs on GitHub, no Claude needed.

The other parts (kpc_checkup.py guard / refs / links, kpc_site_test.js) run first as their own steps and leave
checkup-out/<part>.json; this script adds the bot check and writes ONE issue body, GROUPED BY CHAT. The Sunday parts
(site, refs, links) are kept in data/bot-health.json and shown all week, so a problem does not vanish on Monday and
come back 'new' next Sunday. A link that fails is only a problem when it also failed the Sunday before.

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
FRESH = [('kpc-hunters.json', 7, 'KPC Hunters (saves every ~3 hours)')]   # most bot files only change when the news does
SKIP = {'kpc-go-live.yml', 'kpc-chain.yml'}   # one-time jobs that are done
CHATS = {1: 'Chat 1 · Website', 2: 'Chat 2 · Maps & park data', 3: 'Chat 3 · Lounges & Logger', 4: 'Chat 4 · App',
         5: 'Chat 5 · Bots (posting, schedule)', 6: 'Chat 6 · Campout & events'}
OWNER = [(2, r'key|boundary|canada|state-|trail|access|fers|world|nwr|new-lands|ky-|sota-land|wwff|closures|camps|geo-|outline|official|new-refs|ref-check|top25|land|usace|parkinfo|map-'),
         (3, r'hunters|campground|park-notes|activation'), (6, r'ses\.yml|events|contests|youtube'), (4, r'app'),
         (1, r'guide|approvals|boards|reports|community|whats-new')]
PARTS = ('guard', 'site', 'refs', 'links')
WEEKLY = ('site', 'refs', 'links')


# G22 (Brandon Oct 27): issue #17 and data/bot-health.json are PUBLIC, so members-only pages are never named there:
# each gets a short code (M-1a2b); the code list goes to the private staff room only, and only with a NEW problem.
def _public():
    try:
        g = pathlib.Path('kpc-gate.js').read_text(encoding='utf-8')
        return set(re.findall(r"'([\w.-]+\.html)'", re.search(r'var PUBLIC = \[(.*?)\];', g, re.S).group(1)))
    except Exception:  # noqa: BLE001
        return set()
PUB = _public()
CODES = {}


def mask(text):
    import hashlib
    def sub(mt):
        f = mt.group(0)
        if f in PUB or not pathlib.Path(f).is_file():
            return f
        c = 'M-' + hashlib.sha1(f.encode()).hexdigest()[:4]
        CODES[c] = f
        return f'{c} (members page)'
    return re.sub(r'(?<![\w/.-])[\w-]+\.html\b', sub, text) if PUB else text


def owner(wf):
    for c, rx in OWNER:
        if re.search(rx, wf):
            return c
    return 5


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
    # Oct 27 (storage step B5): bots that moved to KPC-Data are checked too (the workflow checks its files out into kpcdata-wf/)
    srcs = [(f, REPO, '') for f in sorted(pathlib.Path('.github/workflows').glob('*.yml'))]
    srcs += [(f, 'KentuckyPortableClub/KPC-Data', 'KPC-Data/') for f in sorted(pathlib.Path('kpcdata-wf/.github/workflows').glob('*.yml'))]
    for f, repo, tag in srcs:
        if f.name in SKIP: continue
        txt = f.read_text(encoding='utf-8')
        crons = re.findall(r"-\s*cron:\s*'([^']+)'", txt)
        if not crons: continue
        name = tag + (re.search(r'^name:\s*(.+)$', txt, re.M) or [None, f.name])[1].strip()
        need = every_hours(crons)
        runs = gh(f'repos/{repo}/actions/workflows/{f.name}/runs?per_page=5&event=schedule') or {}
        runs = runs.get('workflow_runs') or []
        done = [r for r in runs if r.get('status') == 'completed']
        fresh_file = last_commit_age(str(f)) if not tag else None   # its timer was changed lately: give it time before calling it late
        grace = fresh_file is not None and fresh_file < max(need * 2.5, need + 26)
        if tag and not [r for r in runs if r.get('status') == 'completed']:
            grace = True              # a bot that just moved to KPC-Data and has not had a timed run yet
        if not done:
            if need < 24 * 30 and not grace: problems.append((tag + f.name, f'{name}: no timed run found yet'))
            continue
        last = done[0]
        age = (NOW - dt.datetime.fromisoformat(last['created_at'].replace('Z', '+00:00'))).total_seconds() / 3600
        late = age > max(need * 2.5, need + 3)
        if last.get('conclusion') not in ('success', 'skipped', 'neutral', 'cancelled'):
            problems.append((tag + f.name, f"{name}: last timed run ended '{last.get('conclusion')}' ({last['created_at'][:16]}Z) {last.get('html_url', '')}"))
        elif late and not grace:
            problems.append((tag + f.name, f'{name}: has not run for {age:.0f} h (it should run about every {need:.0f} h)'))
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
    items = [{'key': k, 'chat': owner(k), 'msg': m} for k, m in problems]      # bot check
    notes, oks = [], ['Bot check: %d timed bots fine' % len(ok)]
    weekly = st.setdefault('weekly', {})
    for part in PARTS:
        f = pathlib.Path('checkup-out') / f'{part}.json'
        try:
            d = json.loads(mask(f.read_text(encoding='utf-8')))
        except (OSError, ValueError):
            d = weekly.get(part) if part in WEEKLY else None        # not run today: last Sunday's result
            if not d: continue
            d = json.loads(mask(json.dumps(d)))                   # older saves may still name pages
        else:
            if part in WEEKLY: weekly[part] = d
        if part == 'links' and f.is_file():
            prev = set(st.get('link_fail_prev') or [])
            st['link_fail_prev'] = [x['key'] for x in d.get('problems', []) if x.get('twice')]
            for x in d.get('problems', []):
                if x.get('twice'): x['confirmed'] = x['key'] in prev
        for x in d.get('problems', []):
            if x.get('twice') and not x.get('confirmed'):
                notes.append({'chat': x['chat'], 'msg': x['msg'] + ' (first time; a problem if it fails again next Sunday)'})
            else:
                items.append(x)
        notes += d.get('notes', [])
        oks += [f"{part} ({d.get('date', '')}): {o}" for o in d.get('ok', [])]
    keys = sorted({x['key'] for x in items})
    new = [k for k in keys if k not in st.get('open', [])]
    st['open'] = keys; st['checked'] = NOW.isoformat(timespec='minutes')
    STATE.write_text(json.dumps(st, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    when = NOW.strftime('%b %d, %Y %H:%M UTC')
    body = (f'_Checked {when} by the KPC check-up (.github/workflows/kpc-bot-health.yml). Daily: bot check + public-list guard. '
            'Sundays: site test as a guest (390 px + desktop), reference check for every state, data link check. '
            'Each chat fixes what is under its name. Only a NEW problem emails._\n\n')
    body += (f'## ⚠ {len(items)} to look at\n\n' if items else '## ✅ Nothing to fix.\n\n')
    for c in sorted({x['chat'] for x in items} | {x['chat'] for x in notes}):
        pi = [x for x in items if x['chat'] == c]
        ni = [x for x in notes if x['chat'] == c]
        body += f"### {CHATS.get(c, f'Chat {c}')}\n"
        body += ''.join(f"- {'🆕 ' if x['key'] in new else ''}{x['msg']}\n" for x in pi[:60])
        if len(pi) > 60: body += f'- … and {len(pi) - 60} more\n'
        if ni:
            body += f'<details><summary>{len(ni)} note(s), nothing to fix yet</summary>\n\n' + ''.join(f"- {x['msg']}\n" for x in ni[:60]) + '\n</details>\n'
        body += '\n'
    body += '<details><summary>What was checked</summary>\n\n' + '\n'.join(f'- {x}' for x in oks) + '\n\n' + '\n'.join(f'- {x}' for x in ok) + '\n\n</details>\n'
    problems = [(x['key'], x['msg']) for x in items]
    body = body[:60000]
    print(body)
    print(f'::notice title=Check-up::{len(problems)} problem(s), {len(new)} new, {len(notes)} note(s)', flush=True)
    if not os.environ.get('GITHUB_ACTIONS'): return
    iss = gh(f'repos/{REPO}/issues?labels=bot-health&state=all&per_page=1') or []
    title = ('⚠ KPC check-up: %d to look at' % len(problems)) if problems else '✅ KPC check-up: all fine'
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
        used = sorted({c for k, m in problems if k in new for c in re.findall(r'M-[0-9a-f]{4}', m) if c in CODES})
        hook = (os.environ.get('KPC_ADMIN_WEBHOOK') or '').strip().split()
        if used and hook and hook[0].startswith('https://'):
            import urllib.request
            msg = 'KPC check-up: members-only page codes in the new problem(s) on issue #17: ' + ', '.join(f'{c} = {CODES[c]}' for c in used)
            try:
                urllib.request.urlopen(urllib.request.Request(hook[0], data=json.dumps({'username': 'KPC Check-up', 'content': msg[:1900],
                                       'allowed_mentions': {'parse': []}}).encode(), headers={'Content-Type': 'application/json'}), timeout=30)
            except Exception as e:  # noqa: BLE001
                print(f'::notice title=Check-up::staff room not reached ({e})')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f'::notice title=Check-up::stopped early: {e}')
    sys.exit(0)
