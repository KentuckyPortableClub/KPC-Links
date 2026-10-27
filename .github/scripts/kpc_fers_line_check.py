#!/usr/bin/env python3
"""ASSEMBLY LINE, stage 3 = the CHECKER (chat 2, Oct 27 2026; HQ 5:23 PM). Reads what the fetcher + worker made for one area and
writes data/fers/line-<tag>.json = the verdict: READY FOR CHAT 8 only when (1) the Kentucky known-answers test passes (the engine
guard: every required river / trail pair found), (2) the missing check passes (every expected pair FOUND, or DROPPED / NEVER LOOKED AT
with a reason), (3) every state file of the area was saved by pass 3 and 5 (no 'waiting for pass N'). Else STOPPED + why.
TAG=<area tag>, STATES='US-MI'. Never fails."""
import json, os, pathlib, sys, time
OUT = pathlib.Path('data/fers')


def load(p):
    try: return json.load(open(p))
    except Exception: return None  # noqa: BLE001


def main():
    tag = os.environ.get('TAG') or 'area'
    sts = [x if '-' in x else 'US-' + x for x in (os.environ.get('STATES') or '').upper().replace(',', ' ').split()]
    why, info = [], {}
    k = load(OUT / 'known-answers.json') or {}
    info['known_answers'] = f"{k.get('found', '?')}/{k.get('required', '?')}" if k else 'no test file'
    if not k.get('pass'): why.append(f"Kentucky known-answers test not passing ({info['known_answers']})")
    e = load(OUT / f'expected-{tag}.json') or load(OUT / f"expected-{'-'.join(sorted(sts))}.json") or {}
    info['missing_check'] = e.get('counts') or 'no file'
    if not e: why.append('no missing-check file')
    elif not e.get('pass'): why.append('missing check: some expected pairs have no reason')
    for st in sts:
        d = load(OUT / f'{st}.json')
        if not d: why.append(f'{st}: no 2-fer file'); continue
        spots = d.get('spots') or []
        wait = sum(1 for s in spots if str(s.get('status', '')).startswith('waiting'))
        live = sum(1 for s in spots if str(s.get('status', '')).startswith(('candidate', 'very tight', 'water only')))
        info[st] = {'rows': len(spots), 'live': live, 'waiting': wait}
        if wait: why.append(f'{st}: {wait} rows still waiting for a pass (out of time: run the worker again)')
    res = {'about': 'Assembly-line verdict for one area (fetcher -> worker -> checker).', 'tag': tag, 'states': sts,
           'date': time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime()), 'verdict': 'READY FOR CHAT 8' if not why else 'STOPPED',
           'why': why, **info}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f'line-{tag}.json').write_text(json.dumps(res, indent=1) + '\n')
    print(f"::notice title=2-fer line::{tag}: {res['verdict']}" + (': ' + '; '.join(why)[:600] if why else f" · known {info['known_answers']} · missing check {info['missing_check']}"), flush=True)


if __name__ == '__main__':
    try: main()
    except Exception as x:  # noqa: BLE001
        print(f'::notice title=2-fer line::stopped: {x}', flush=True)
    sys.exit(0)
