#!/usr/bin/env python3
"""SKIPPED-RUN WATCHDOG (chat 10, Nov 2 2026; chat 2 + Brandon 7:18 AM: GitHub skipped most of last night's scheduled runs, so
things kept stalling; 'everything implements now'). Every 2 hours, for every ACTIVE workflow of THIS repo with a schedule:
the latest time its cron should have fired (in the last 26 h, at least 25 min ago) must have a run (scheduled, by hand or by
another bot) started within 15 min before / any time after it. No run = GitHub skipped it: the watchdog starts it once by hand
(workflow_dispatch; inputs: the workflow's defaults, plus WATCHDOG_INPUTS below where a default would change what the scheduled
run does). (Its own 2-hourly look covers the frequent ones too: GitHub skipped most of the every-2-hours waiting-room runs.) Each restart is
remembered in data/status/watchdog.json (never twice for the same missed time) and listed on the status board. Never fails.
  python3 .github/scripts/kpc_watchdog.py        env GH_TOKEN, GITHUB_REPOSITORY"""
import datetime as dt, json, os, pathlib, re, subprocess, sys

REPO = os.environ.get('GITHUB_REPOSITORY') or 'KentuckyPortableClub/KPC-Data'
STATE = pathlib.Path('data/status/watchdog.json')
NOW = dt.datetime.now(dt.timezone.utc)
SELF = 'kpc-watchdog.yml'
WATCHDOG_INPUTS = {'kpc-new-refs.yml': {'dry_run': 'false'}}   # its dispatch default is a dry run; the scheduled run is not


def gh(*a):
    r = subprocess.run(['gh', 'api', *a], capture_output=True, text=True)
    return r.returncode, r.stdout


def field(spec, lo, hi):
    out = set()
    for part in spec.split(','):
        step = 1
        if '/' in part: part, step = part.split('/'); step = int(step)
        if part == '*': a, b = lo, hi
        elif '-' in part: a, b = map(int, part.split('-'))
        else: a = b = int(part)
        out.update(range(a, b + 1, step))
    return out


def fires(cron):
    """-> function(datetime) True when the 5-field cron (UTC) fires at that minute."""
    m, h, dom, mon, dow = cron.split()[:5]
    M, H, D, MO = field(m, 0, 59), field(h, 0, 23), field(dom, 1, 31), field(mon, 1, 12)
    W = {x % 7 for x in field(dow, 0, 7)}
    dom_any, dow_any = dom == '*', dow == '*'

    def ok(t):
        if t.minute not in M or t.hour not in H or t.month not in MO: return False
        d_ok, w_ok = t.day in D, (t.isoweekday() % 7) in W
        if dom_any and dow_any: return True
        if dom_any: return w_ok
        if dow_any: return d_ok
        return d_ok or w_ok
    return ok


def last_fire(cron, back_h=26, min_age_min=25):
    ok = fires(cron)
    t = (NOW - dt.timedelta(minutes=min_age_min)).replace(second=0, microsecond=0)
    end = NOW - dt.timedelta(hours=back_h)
    times = []
    while t > end:
        if ok(t): times.append(t)
        t -= dt.timedelta(minutes=1)
    return times


def crons(path):
    txt = pathlib.Path(path).read_text(encoding='utf-8')
    if not re.search(r'^\s*workflow_dispatch\s*:', txt, re.M): return None, []
    return True, re.findall(r"^\s*-\s*cron:\s*['\"]([^'\"]+)['\"]", txt, re.M)


def main():
    st = json.load(open(STATE)) if STATE.exists() else {}
    done = st.setdefault('restarted', {})
    rc, out = gh(f'repos/{REPO}/actions/workflows', '--paginate', '--jq', '.workflows[] | [.path, .state, .id] | @tsv')
    active = {l.split('\t')[0]: l.split('\t')[2] for l in out.splitlines() if '\tactive\t' in l}
    started, checked = [], 0
    for path, wid in sorted(active.items()):
        name = os.path.basename(path)
        if name == SELF or not os.path.exists(path): continue
        can, cs = crons(path)
        if not can or not cs: continue
        ts = sorted({t for c in cs for t in last_fire(c)}, reverse=True)
        if not ts: continue
        t = ts[0]; key = f'{name}|{t.isoformat()}'   # the newest time ANY of its crons should have fired
        if key in done: continue
        checked += 1
        since = (t - dt.timedelta(minutes=15)).strftime('%Y-%m-%dT%H:%M:%SZ')
        rc, runs = gh(f'repos/{REPO}/actions/workflows/{wid}/runs?created=>={since}&per_page=5', '--jq', '.total_count')
        if rc != 0 or not runs.strip() or int(runs.strip() or 0) > 0: continue
        args = [f'repos/{REPO}/actions/workflows/{wid}/dispatches', '-X', 'POST', '-f', 'ref=main']
        for k, v in (WATCHDOG_INPUTS.get(name) or {}).items(): args += ['-f', f'inputs[{k}]={v}']
        rc, _ = (0, '') if os.environ.get('DRY') else gh(*args)
        done[key] = NOW.isoformat(timespec='minutes') + (' started' if rc == 0 else ' could not start')
        started.append(f"{name} (missed {t.strftime('%b %d %H:%M')} UTC{'' if rc == 0 else ', start FAILED'})")
    cut = (NOW - dt.timedelta(days=7)).isoformat()
    st['restarted'] = {k: v for k, v in done.items() if v >= cut}
    st['last'] = NOW.isoformat(timespec='minutes'); st['last_restarted'] = started
    STATE.parent.mkdir(parents=True, exist_ok=True)
    if not os.environ.get('DRY'): json.dump(st, open(STATE, 'w'), indent=1)
    msg = (f'{len(started)} skipped run(s) started again: ' + '; '.join(started)) if started else f'nothing skipped ({checked} scheduled times checked)'
    print(f'::notice title=Watchdog::{msg}', flush=True)
    if os.path.exists('.github/scripts/kpc_status.py') and not os.environ.get('DRY'):
        subprocess.run([sys.executable, '.github/scripts/kpc_status.py', 'board', 'Skipped-run watchdog', 'amber' if started else 'green',
                        f"{NOW.strftime('%Y-%m-%d %H:%M')} UTC: {msg}"[:300], 'nobody (it restarts them itself)'], check=False)


if __name__ == '__main__':
    try: main()
    except Exception as e: print(f'::notice title=Watchdog::stopped ({type(e).__name__}: {e})')  # noqa: BLE001
    sys.exit(0)
