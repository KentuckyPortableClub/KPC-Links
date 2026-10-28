#!/usr/bin/env python3
"""Boundary bot queue (kpc-bot-queue.yml; moved out of the workflow Oct 28 2026, HQ tune pass).

  pick   when no boundary bot is running and a job is due: take it off data/bot-queue.json (a repeating job goes to the
         back with its next date) and remember it in /tmp/kpc-next.json. The workflow saves the queue next.
  start  only after that save went through: start the remembered job. If GitHub refuses, the job goes back on the
         queue for tomorrow (it never blocks the jobs behind it) and the workflow saves that.
Never fails (no emails)."""
import datetime
import json
import os
import pathlib
import subprocess
import sys

Q, NEXT = pathlib.Path('data/bot-queue.json'), pathlib.Path('/tmp/kpc-next.json')
# the boundary bots; kpc-boundary-check.yml shares the US answer-key lock with kpc-us-key.yml, so it counts as busy too
BOTS = ('kpc-us-key.yml', 'kpc-ca-key.yml', 'kpc-world-key.yml', 'kpc-state-trails.yml', 'kpc-canada-bounds.yml', 'kpc-boundary-check.yml')
NOW = datetime.datetime.now(datetime.timezone.utc)


def notice(m):
    print('::notice title=Bot queue::' + m.replace('%', '%25').replace('\n', '%0A'), flush=True)


def gh(*a):
    return subprocess.run(['gh', *a], capture_output=True, text=True)


def when(s):
    try:
        return datetime.datetime.fromisoformat(str(s).replace('Z', '+00:00'))
    except ValueError:
        return NOW


def busy():
    """Names of boundary bots with a run not finished yet, or None when GitHub could not be asked."""
    out = set()
    for st in ('queued', 'in_progress', 'waiting', 'pending', 'requested'):
        r = gh('api', f"repos/{os.environ['REPO']}/actions/runs?status={st}&per_page=100", '-q', '.workflow_runs[].path')
        if r.returncode:
            return None
        out |= {p.rsplit('/', 1)[-1] for p in r.stdout.split() if p.rsplit('/', 1)[-1] in BOTS}
    return out


def save(q):
    Q.write_text(json.dumps(q, indent=1) + '\n', encoding='utf-8')


def pick():
    q = json.loads(Q.read_text(encoding='utf-8'))
    if not q['jobs'] or NOW > when(q['until']):
        return notice('nothing to do')
    due = [i for i, x in enumerate(q['jobs']) if when(x.get('next', '')) <= NOW]
    if not due:
        return notice('nothing due yet')
    b = busy()
    if b is None:
        return notice('could not read which bots are running; waiting an hour (never start blind)')
    if b:
        return notice('waiting, running: ' + ', '.join(sorted(b)))
    j = q['jobs'].pop(due[0])
    NEXT.write_text(json.dumps(j), encoding='utf-8')
    if j.get('every'):   # Oct 23: a repeating job goes to the back with its next date
        k = dict(j, next=(NOW + datetime.timedelta(days=j['every'])).isoformat(timespec='minutes'))
        k.pop('fails', None)
        q['jobs'].append(k)
    save(q)
    notice(f"picked {j['wf']} {j['inputs']} ({j.get('why', '')}); {len(q['jobs'])} on the queue")


def start():
    if not NEXT.exists():
        return
    j = json.loads(NEXT.read_text(encoding='utf-8'))
    cmd = ['api', '-X', 'POST', f"repos/{os.environ['REPO']}/actions/workflows/{j['wf']}/dispatches", '-f', 'ref=main']
    for k, v in j.get('inputs', {}).items():
        cmd += ['-f', f'inputs[{k}]={v}']
    r = gh(*cmd)
    if not r.returncode:
        return notice(f"started {j['wf']} {j['inputs']} ({j.get('why', '')})")
    # refused: back on the queue for tomorrow, behind the others (a repeating job's copy with its later date is dropped)
    q = json.loads(Q.read_text(encoding='utf-8'))
    q['jobs'] = [x for x in q['jobs'] if not (x['wf'] == j['wf'] and x.get('inputs') == j.get('inputs'))]
    j['next'] = (NOW + datetime.timedelta(days=1)).isoformat(timespec='minutes')
    j['fails'] = j.get('fails', 0) + 1
    q['jobs'].append(j)
    save(q)
    notice(f"start failed for {j['wf']} {j['inputs']} (try {j['fails']}), moved to tomorrow: {r.stderr.strip()[:250]}")


if __name__ == '__main__':
    try:
        {'pick': pick, 'start': start}[sys.argv[1]]()
    except Exception as e:  # noqa: BLE001
        notice(f'problem: {e}')
