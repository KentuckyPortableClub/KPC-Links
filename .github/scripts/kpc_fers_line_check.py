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
import json, math, os, pathlib, re, sys, time
OUT = pathlib.Path('data/fers')
LIVE = ('candidate', 'very tight', 'water only')
# Nov 2 bot fixes (Mapping #8): the missing check passed when every NEVER LOOKED AT pair had ANY reason (US-ND: READY with 662 of
# 710 expected pairs never looked at). READY now also needs the pairs never looked at, NOT counting the ones where a park has no
# official outline, to be at most this share of the expected pairs. (The 10% is Mapping's example: a question for Brandon.)
NEVER_LOOKED_MAX = 0.10
NO_OUTLINE = re.compile(r'no official (boundary|outline)|approximate outline only', re.I)


def never_looked(e):
    """-> (counted, no_outline, total expected, {reason: n} for the counted ones) from an expected-<tag>.json"""
    nla = e.get('NEVER LOOKED AT') if isinstance(e.get('NEVER LOOKED AT'), list) else []
    tot = sum(len(e.get(k)) for k in ('FOUND', 'DROPPED', 'NEVER LOOKED AT') if isinstance(e.get(k), list))
    if not tot: tot = sum(int(v or 0) for v in (e.get('counts') or {}).values())
    no_out, why = 0, {}
    for x in nla:
        parts = [q.split(':', 1)[-1].strip() for q in str(x.get('reason') or 'unknown').split(';') if q.strip()]
        if parts and all(NO_OUTLINE.search(q) for q in parts): no_out += 1; continue
        k = re.sub(r'\bUS-\d+|\bCA-\d+', '<park>', str(x.get('reason') or 'unknown'))[:90]
        why[k] = why.get(k, 0) + 1
    if not nla and (e.get('counts') or {}).get('NEVER LOOKED AT'):   # a file without the lists: count them all
        return int(e['counts']['NEVER LOOKED AT']), 0, tot, {'(the file has no list: reasons unknown)': int(e['counts']['NEVER LOOKED AT'])}
    return sum(why.values()), no_out, tot, dict(sorted(why.items(), key=lambda kv: -kv[1]))


def load(p):
    for q in (str(p), str(p) + '.gz'):   # Oct 28 (chat 8, Midwest): big files are kept gzipped (US-MN.json.gz)
        try:
            if q.endswith('.gz'):
                import gzip
                return json.loads(gzip.decompress(open(q, 'rb').read()))
            return json.load(open(q))
        except Exception: pass  # noqa: BLE001
    return None


def outlined(st):
    """How many of the state's parks have an official outline in the answer key (the near-empty test)."""
    try: return sum(1 for p in json.load(open(f'data/us-key/{st}.json'))['parks'].values() if p.get('m'))
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
    if e:
        n_nl, n_noout, n_tot, by = never_looked(e)
        info['never_looked_at'] = {'counted': n_nl, 'no_official_outline': n_noout, 'expected': n_tot, 'limit': f'{NEVER_LOOKED_MAX:.0%}', 'by_reason': dict(list(by.items())[:6])}
        if n_tot and n_nl > NEVER_LOOKED_MAX * n_tot:
            why.append(f"missing check: {n_nl} of {n_tot} expected pairs were never looked at ({n_nl / n_tot:.0%}; {n_noout} more have no official outline and are not counted); "
                       f"READY needs {NEVER_LOOKED_MAX:.0%} or less. Most: " + '; '.join(f'{k} ({v})' for k, v in list(by.items())[:3]))
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
        info.setdefault('files', {})[st] = f'data/fers/{st}.json' + ('' if (OUT / f'{st}.json').exists() else '.gz')
        # Oct 28 (HQ + chat 8: Minnesota / Iowa): a near-empty result next to many outlined parks is never READY by itself
        no = outlined(st)
        if no and no >= 30 and len(spots) < max(2, no // 100): why.append(f'{st}: only {len(spots)} rows from {no} outlined parks (near-empty: check the run)')
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
        # Oct 28 10:29 PM (Brandon): any 'not checked' row = STOPPED, never READY (a quiet water map must never give a false READY).
        # 'Keep running' (8:53 PM) still holds: the other areas go on, the rows are on the review list as 'water map weak here'.
        if wnc:
            info.setdefault('water_weak', {})[st] = wnc
            why.append(f'water not checked: {st}: {wnc} rows (the USGS water map / files had no answer there): never READY with one')
        if stuck: why.append(f'{st}: {stuck} rows stuck at a pass status (a pass was killed before its save)')
        # Oct 29 (Fable + chat 8): a LIVE 'same land' row whose two pins are over 30 km apart is a wrong join in the key (two
        # places with one name in one multipart record): hold the state (parkinfo pins = the ones chat 8 grades with)
        pins = {}
        pf = 'CA' if st.startswith('CA-') else st   # Canada's pins are one file (parkinfo/CA.json)
        for pi in (pathlib.Path(f'data/parkinfo/{pf}.json'), pathlib.Path(f'../kpc-data/data/parkinfo/{pf}.json')):
            # Nov 4 (Mapping 2-fer review #1; rule: never move POTA pins): no swap guess. A 0,0 / impossible POTA pin is not used
            # for the distance test (that row is then judged by the 2-fer finder's own 'bad POTA pin' list instead)
            pins = {r: (v[5], v[6]) for r, v in ((load(pi) or {}).get('parks') or {}).items() if len(v) > 6 and isinstance(v[5], (int, float)) and isinstance(v[6], (int, float))
                    and not (v[5] == 0 and v[6] == 0) and -90 <= v[5] <= 90 and -180 <= v[6] <= 180}
            if pins: break
        def _km(a, b): return math.hypot((pins[a][1] - pins[b][1]) * 111.32 * math.cos(math.radians(pins[a][0])), (pins[a][0] - pins[b][0]) * 110.57)
        far = [s['id'] for s in spots if s.get('kind') == 'same land' and st_of(s).startswith(LIVE) and len(s.get('refs') or []) > 1
               and all(r in pins for r in s['refs'][:2]) and _km(*s['refs'][:2]) > 30]
        if far: why.append(f"{st}: {len(far)} live 'same land' rows with pins over 30 km apart (a wrong join in the key): {' '.join(far[:4])}")
    res = {'about': 'Assembly-line verdict for one area (fetcher -> worker -> checker). READY only when every pass finished in this run, nothing was cut short, the known answers + missing check pass.',
           'tag': tag, 'states': sts, 'since': since, 'date': time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime()),
           'verdict': 'READY FOR CHAT 8' if not why else 'STOPPED', 'why': why, **info}
    # Oct 28 10:31 PM (Brandon: 'the stopped file go to the list of reviews and we rerun them later, the good files go out'):
    # the verdict is also given PER STATE. A state named in a reason is HELD (review list + a later rerun); when nothing is wrong
    # with the area as a whole (known answers, missing check, passes not cut short), the other states are READY = PART READY.
    held = sorted({st for st in sts for w in why if re.search(r'(^|: )' + re.escape(st) + r'(:|\b)', w)})
    area_why = [w for w in why if not any(re.search(r'(^|: )' + re.escape(st) + r'(:|\b)', w) for st in sts)]
    res['states_ready'] = [] if area_why else [st for st in sts if st not in held]
    res['states_held'] = sts if area_why else held
    if why and not area_why and res['states_ready']: res['verdict'] = 'PART READY FOR CHAT 8'
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f'line-{tag}.json').write_text(json.dumps(res, indent=1) + '\n')
    ns = '; '.join(f"{st}: live {v['live']}, not sure {sum(v['not_sure'].values())}" for st, v in info.items() if isinstance(v, dict) and 'live' in v)
    print(f"::notice title=2-fer line::{tag}: {res['verdict']}" + (f" (ready: {' '.join(res['states_ready'])}; held: {' '.join(res['states_held'])})" if res['verdict'].startswith('PART') else '') + (': ' + '; '.join(why)[:600] if why else f" · known {info['known_answers']} · missing check {info['missing_check']} · {ns}"), flush=True)


if __name__ == '__main__':
    try: main()
    except Exception as x:  # noqa: BLE001
        print(f'::notice title=2-fer line::stopped: {x}', flush=True)
    sys.exit(0)
