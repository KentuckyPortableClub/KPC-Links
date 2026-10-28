#!/usr/bin/env python3
"""ASSEMBLY LINE, stage 3 = the CHECKER (chat 2, Oct 27 2026; HQ 5:23 PM; Fable's review A3 Oct 27 7:30 PM). Reads what the
fetcher + worker made for one area and writes data/fers/line-<tag>.json = the verdict. READY FOR CHAT 8 only when
  (1) the Kentucky known-answers test passes and is recent (every required river / trail pair found; ≤ 30 days old),
  (2) the missing check passes (every expected pair FOUND, or DROPPED / NEVER LOOKED AT with a reason),
  (3) every state file carries pass1, pass2, pass3 AND pass5 stamps from THIS run (SINCE = the run's start date),
  (4) pass 1 and pass 2 were not cut short ('stopped for time' in report-<tag>.json; pass 1 tested every pair whose boxes touch),
  (5) no row is still 'waiting for pass N' or stuck at 'pass N' (a pass killed before its save).
Else STOPPED + every reason. The verdict also COUNTS what is parked as NOT SURE (water not checked, ownership map did not answer,
two owners…) so chat 8 sees how much is unresolved. TAG=<area tag>, STATES='US-MI', SINCE=YYYY-MM-DD (default: 36 h ago). Never fails."""
import json, os, pathlib, re, sys, time
OUT = pathlib.Path('data/fers')
LIVE = ('candidate', 'very tight', 'water only')


def load(p):
    try: return json.load(open(p))
    except Exception: return None  # noqa: BLE001


def main():
    tag = os.environ.get('TAG') or 'area'
    sts = [x if '-' in x else 'US-' + x for x in (os.environ.get('STATES') or '').upper().replace(',', ' ').split()]
    since = os.environ.get('SINCE') or time.strftime('%Y-%m-%d', time.gmtime(time.time() - 36 * 3600))
    why, info = [], {}
    # (1) known answers
    k = load(OUT / 'known-answers.json') or {}
    info['known_answers'] = f"{k.get('found', '?')}/{k.get('required', '?')} on {k.get('date', '?')}" if k else 'no test file'
    if not k.get('pass'): why.append(f"Kentucky known-answers test not passing ({info['known_answers']})")
    elif str(k.get('date', '')) < time.strftime('%Y-%m-%d', time.gmtime(time.time() - 30 * 86400)): why.append(f"Kentucky known-answers test older than 30 days ({k.get('date')}): run Kentucky through the line again")
    # (2) missing check
    e = load(OUT / f'expected-{tag}.json') or load(OUT / f"expected-{'-'.join(sorted(sts))}.json") or {}
    info['missing_check'] = e.get('counts') or 'no file'
    if not e: why.append('no missing-check file')
    elif not e.get('pass'): why.append('missing check: some expected pairs have no reason')
    elif str(e.get('date', '')) < since: why.append(f"missing check is from {e.get('date')}, before this run")
    # (4) the passes were not cut short
    rep = load(OUT / f'report-{tag}.json') or {}
    for p in ('pass1', 'pass2'):
        c = rep.get(p) or {}
        if c.get('stopped for time'): why.append(f'{p} stopped for time: not every pair was looked at (run the fetcher again with more minutes)')
    c1 = rep.get('pass1') or {}
    if c1 and c1.get('pairs tested', 0) < c1.get('pairs whose boxes touch', 0):
        why.append(f"pass 1 tested {c1.get('pairs tested')} of {c1.get('pairs whose boxes touch')} pairs whose boxes touch")
    info['report'] = {p: {k2: v for k2, v in (rep.get(p) or {}).items() if k2 in ('date', 'pairs tested', 'pairs whose boxes touch', 'stopped for time', 'agree with the pass before', 'checked', 'still not checked')} for p in ('pass1', 'pass2', 'pass3', 'pass5')}
    # (3) + (5) every state file finished every pass in this run
    for st in sts:
        d = load(OUT / f'{st}.json')
        if not d: why.append(f'{st}: no 2-fer file'); continue
        for p in ('pass1', 'pass2', 'pass3', 'pass5'):
            if str(d.get(p, '')) < since: why.append(f"{st}: {p} not run in this run (stamp {d.get(p) or 'none'}, run started {since})")
        spots = d.get('spots') or []
        st_of = lambda s: str(s.get('status', ''))
        wait = sum(1 for s in spots if st_of(s).startswith('waiting'))
        stuck = sum(1 for s in spots if re.fullmatch(r'pass [1-5]', st_of(s)))
        live = sum(1 for s in spots if st_of(s).startswith(LIVE))
        notsure = {}
        for s in spots:
            m = re.match(r'not sure: ([^(:]{3,60})', st_of(s))
            if m: notsure[m.group(1).strip()] = notsure.get(m.group(1).strip(), 0) + 1
        info[st] = {'rows': len(spots), 'live': live, 'waiting': wait, 'unfinished': stuck, 'not_sure': notsure,
                    'dropped': sum(1 for s in spots if st_of(s).startswith('dropped')), 'merged': sum(1 for s in spots if st_of(s).startswith('merged'))}
        if wait: why.append(f'{st}: {wait} rows still waiting for a pass (out of time: run the worker again)')
        # Oct 28 (HQ + chat 8, Michigan): a row the USGS water map never answered for is not a result: never READY with one
        wnc = sum(1 for s in spots if re.search(r'water not checked|water map did not answer', st_of(s)))
        if wnc: why.append(f'water service: {st}: {wnc} rows not checked because the USGS water map did not answer (run the worker again)')
        if stuck: why.append(f'{st}: {stuck} rows stuck at a pass status (a pass was killed before its save)')
    res = {'about': 'Assembly-line verdict for one area (fetcher -> worker -> checker). READY only when every pass finished in this run, nothing was cut short, the known answers + missing check pass.',
           'tag': tag, 'states': sts, 'since': since, 'date': time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime()),
           'verdict': 'READY FOR CHAT 8' if not why else 'STOPPED', 'why': why, **info}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f'line-{tag}.json').write_text(json.dumps(res, indent=1) + '\n')
    ns = '; '.join(f"{st}: live {v['live']}, not sure {sum(v['not_sure'].values())}" for st, v in info.items() if isinstance(v, dict) and 'live' in v)
    print(f"::notice title=2-fer line::{tag}: {res['verdict']}" + (': ' + '; '.join(why)[:600] if why else f" · known {info['known_answers']} · missing check {info['missing_check']} · {ns}"), flush=True)


if __name__ == '__main__':
    try: main()
    except Exception as x:  # noqa: BLE001
        print(f'::notice title=2-fer line::stopped: {x}', flush=True)
    sys.exit(0)
