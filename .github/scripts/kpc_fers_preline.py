#!/usr/bin/env python3
"""2-FER PRE-LINE CHECK (Nov 4 2026; Brandon, directly (Mapping chat), 4:52 AM CST Nov 4: "2fer line review? Plan and install any pre and post line bots for the 2fer
system."). Runs BEFORE the 2-fer finder builds lines (KPC-Data kpc-fers-line.yml, job 'preline'; the fetcher / worker / checker need it).
READ-ONLY: no web request, never moves a pin, never edits a key. It writes one report and says GO or HOLD:

  HOLD (the line does not build) when, for a state of the batch:
    * its key file is missing, unreadable or has no parks; or the key's outline count fell by more than 20 % against the live key
    * the key is not fresh: the build named this state as FAILED, or the state is still on the key's 'rebuild tonight' list
      (answers-states.txt / answers-provinces.txt), or the key's overrides.json was changed AFTER the key was built (answers not in it)
    * the key is frozen or held the wrong way: KEY_SOURCE=build (the chain) and the build is not on the current rules
      (kpc_key_freeze.rules_hash), or the links-01 post-key check has not run on this build, or Quality / Brandon graded it NO / FAIL;
      KEY_SOURCE=live (by hand, the small batches) and a NEWER key file for the state still waits in KPC-Data's waiting room
      ('keys first', as kpc-fers-pending.yml)
    * the key still joins a record a person said NO to (overrides 'no')
  WARN (reported, the line still builds; the finder and its guards treat these rows as 'not sure'):
    * bad POTA pins (0,0 / impossible), listed, never moved
    * the pre-check review pile and rule 18 rows of the post-key check for this state
    * outlines with no area
  An ungraded build on the current rules is GO, marked HELD KEY: the 2-fers measured on it go to the waiting room and are graded with it.

env  STATES='US-TN US-NC'  TAG=se  KEY_SOURCE=live|build (default live)  DATA=kpcdata (KPC-Data checkout)
     OUT=<dir> (default $DATA/data/status/fers-preline)  FORCE=yes (by hand only: GO even on HOLD; the report says so)
     KPC_PRELINE_DROP=0.2
Writes $OUT/<TAG>.json + .md and 'go=yes|no', 'verdict=GO|HOLD|FORCED' to $GITHUB_OUTPUT. Never fails (exit 0); an error = HOLD."""
import json, os, pathlib, re, subprocess, sys, time, datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
KIND = lambda st: 'ca-key' if st.startswith('CA-') else ('world-key' if st.startswith('W-') or not re.match(r'^(US|CA)-', st) else 'us-key')
LIST = {'us-key': 'answers-states.txt', 'ca-key': 'answers-provinces.txt', 'world-key': 'answers-countries.txt'}


def load(p, d=None):
    try: return json.load(open(p, encoding='utf-8'))
    except Exception: return d  # noqa: BLE001


def built_at(s):
    try: return datetime.datetime.strptime(str(s or ''), '%Y-%m-%d %H:%M UTC').replace(tzinfo=datetime.timezone.utc)
    except Exception: return None  # noqa: BLE001


def git_time(path, cwd='.'):
    sh = subprocess.run(['git', 'rev-parse', '--is-shallow-repository'], cwd=cwd, capture_output=True, text=True).stdout.strip()
    if sh != 'false': return None   # a shallow checkout has no file history: the time test is skipped (the report says so)
    r = subprocess.run(['git', 'log', '-1', '--format=%ct', '--', path], cwd=cwd, capture_output=True, text=True)
    try: return datetime.datetime.fromtimestamp(int(r.stdout.strip()), datetime.timezone.utc)
    except Exception: return None  # noqa: BLE001


def pin_bad(la, lo):
    try: la, lo = float(la), float(lo)
    except (TypeError, ValueError): return True
    return (abs(la) < 1e-9 and abs(lo) < 1e-9) or not (-90 <= la <= 90 and -180 <= lo <= 180)


def override_no(path):
    try:
        import kpc_fers_guard as FG   # links-02's reader when it is there
        return FG.override_no(path)
    except Exception: pass  # noqa: BLE001
    out = {}
    for ref, o in ((load(path, {}) or {}).get('parks') or {}).items():
        no = [x for x in (o or {}).get('no') or [] if x is not None]
        if no: out[ref] = ({str(x) for x in no}, {str(x).strip().lower() for x in no})
    return out


def key_area(st): return st if KIND(st) != 'world-key' else st.replace('W-', '')


def check_state(st, src, data, links='.'):
    kind = KIND(st); hold, warn, info = [], [], {}
    if st == 'US-KY':
        info['key'] = 'Kentucky: its own key from the official files (kpc-ky-key.yml), not checked here'; return hold, warn, info
    base = pathlib.Path(links) if src == 'build' else pathlib.Path(data)
    kf = base / f'data/{kind}/{key_area(st)}.json'
    key = load(kf)
    idx = load(base / f'data/{kind}/index.json', {}) or {}
    info.update(key_file=str(kf), build=idx.get('build'), built=idx.get('built'), rules=idx.get('rules'))
    parks = (key or {}).get('parks') if isinstance(key, dict) else None
    if not parks:
        hold.append(f'key file {kf} is missing, unreadable or has no parks'); return hold, warn, info
    joined = {r: p for r, p in parks.items() if p.get('m')}
    info.update(parks=len(parks), outlines=len(joined))
    # freshness
    if st in (idx.get('failed') or []) or key_area(st) in (idx.get('failed') or []): hold.append(f"the key build {idx.get('build')} names {st} as FAILED")
    try: todo = open(pathlib.Path(links) / f'data/{kind}/{LIST[kind]}', encoding='utf-8').read().split()
    except Exception: todo = []  # noqa: BLE001
    if key_area(st).replace('US-', '') in todo or st in todo: hold.append(f'{st} is still on the key\'s rebuild list ({LIST[kind]}): new answers are not in this key yet')
    bt, ot = built_at(idx.get('built')), git_time(f'data/{kind}/overrides.json', links)
    if not ot: info['inputs_time'] = 'not checked (shallow checkout or no git history)'
    if bt and ot and ot > bt + datetime.timedelta(minutes=5):
        hold.append(f"the key's overrides.json changed at {ot:%Y-%m-%d %H:%M} UTC, after the key was built ({idx.get('built')}): the 2-fer inputs are newer than the key")
    # frozen / held
    if src == 'build':
        try:
            import kpc_key_freeze as KF
            cur = KF.rules_hash(kind, links)
            if str(idx.get('rules') or '') != cur: hold.append(f"the key build {idx.get('build')} is not a full build on the current rules ({idx.get('rules') or 'no rules hash'} vs {cur}): wait for the rebuild")
            items = (load(pathlib.Path(data) / 'data/waiting/approved.json', {}) or {}).get('items')
            no = KF.graded_no(kind, str(idx.get('build') or ''), items, links)   # FINAL-v2: a person's, Quality's or old chat 11 NO holds
            if no: hold.append(f"the key build {idx.get('build')} was graded {no[0][:30]} by {no[1]}: no 2-fers on it")
            elif not KF.verdict(kind, str(idx.get('build') or ''), items, links):   # no person's sign-off yet (Brandon / KZ4CP)
                info['held_key'] = f"HELD KEY: build {idx.get('build')} has no person's sign-off yet; the 2-fers measured on it are held with it"
        except (ImportError, AttributeError): hold.append('kpc_key_freeze.py has no rules hash (links-04 not merged): KEY_SOURCE=build cannot be checked')
        short = {'us-key': 'us', 'ca-key': 'ca', 'world-key': 'world'}[kind]
        last = load(pathlib.Path(links) / f'data/status/key-check/last-{short}.json', {}) or {}
        if str(last.get('build') or '') != str(idx.get('build') or '-'):
            hold.append(f"the post-key check (links-01, data/status/key-check/last-{short}.json) has not run on build {idx.get('build')} (it says {last.get('build')})")
        else:
            rep = load(pathlib.Path(links) / 'data/status/key-check' / str(last.get('report') or ''), {}) or {}
            pc = rep.get('precheck') or {}
            pile = [x for x in pc.get('hold_still_outline') or [] if x.get('area') == st]
            r18 = [x for x in pc.get('rule18') or [] if x.get('area') == st]
            if pile: warn.append(f"{len(pile)} review-pile HOLD row(s) still outlines: {' '.join(x['park'] for x in pile[:10])} (their 2-fers are 'not sure')")
            if r18: warn.append(f"{len(r18)} rule 18 row(s): {' '.join(x['park'] for x in r18[:10])} (a person decides)")
            info['postcheck'] = last.get('report')
        live = load(pathlib.Path(data) / f'data/{kind}/{key_area(st)}.json', {}) or {}
        lj = sum(1 for p in (live.get('parks') or {}).values() if p.get('m'))
        drop = float(os.environ.get('KPC_PRELINE_DROP') or 0.2)
        if lj and len(joined) < lj * (1 - drop): hold.append(f'outline sanity: {len(joined)} outlines vs {lj} in the live key (more than {drop:.0%} fewer)')
    else:
        if (pathlib.Path(data) / f'data/waiting/in/data/{kind}/{key_area(st)}.json').exists() or (pathlib.Path(data) / f'data/waiting/in/data/{kind}/{key_area(st)}.json.gz').exists():
            hold.append(f'a newer key file for {st} still waits in the waiting room: keys first (it would change the outlines)')
    # overrides 'no'
    no = override_no(pathlib.Path(links) / f'data/{kind}/overrides.json')
    still = [r for r, p in joined.items() if r in no and any(str(x[0]) in no[r][0] or (len(x) > 1 and str(x[1]).strip().lower() in no[r][1]) for x in p['m'])]
    if still: hold.append(f"the key still joins a record a person said NO to (overrides 'no'): {' '.join(sorted(still)[:15])}")
    # pins
    locs = {}
    for row in load(pathlib.Path(links) / 'locations.json', []) or []:
        if isinstance(row, list) and len(row) > 4: locs[str(row[1])] = (row[3], row[4])
    bad = sorted(r for r in parks if r in locs and pin_bad(*locs[r]))
    bad += sorted(r for r, p in parks.items() if p.get('pin_may_be_wrong') and r not in bad)
    flat = sorted(r for r, p in joined.items() if isinstance(p.get('ac'), (int, float)) and p['ac'] <= 0)
    if bad: warn.append(f"{len(bad)} bad POTA pin(s) (0,0, impossible or 'pin may be wrong'; listed, never moved): {' '.join(bad[:15])}")
    if flat: warn.append(f"{len(flat)} outline(s) with no area: {' '.join(flat[:10])}")
    info.update(bad_pins=len(bad), overrides_no_still=len(still))
    return hold, warn, info


def main(env=os.environ, links='.'):
    states = (env.get('STATES') or '').split(); tag = env.get('TAG') or 'x'; src = (env.get('KEY_SOURCE') or 'live').lower()
    data = env.get('DATA') or 'kpcdata'; out = pathlib.Path(env.get('OUT') or f'{data}/data/status/fers-preline')
    rep = {'tag': tag, 'states': states, 'key_source': src, 'checked': time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime()), 'areas': {},
           'about': "2-fer pre-line check (Brandon, directly (Mapping chat), 4:52 AM CST Nov 4). HOLD = the line does not build. Read-only; nothing is moved or released."}
    try:
        if not states: raise ValueError('no STATES given')
        for st in states:
            h, w, i = check_state(st, src, data, links); rep['areas'][st] = {'hold': h, 'warn': w, **i}
    except Exception as e:  # noqa: BLE001
        rep['error'] = f'the pre-line check could not run: {str(e)[:200]}'
    holds = [f'{st}: {h}' for st, a in rep['areas'].items() for h in a['hold']] + ([rep['error']] if rep.get('error') else [])
    verdict = 'HOLD' if holds else 'GO'
    if holds and (env.get('FORCE') or '').lower() == 'yes': verdict = 'FORCED'
    rep.update(verdict=verdict, holds=holds, held_key=any(a.get('held_key') for a in rep['areas'].values()))
    out.mkdir(parents=True, exist_ok=True)
    json.dump(rep, open(out / f'{tag}.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    md = [f"# 2-fer pre-line check: {tag} ({' '.join(states)}): {verdict}", '', f"Key source: {src} · checked {rep['checked']}", '']
    for st, a in rep['areas'].items():
        md.append(f"## {st}: {'HOLD' if a['hold'] else 'GO'}" + (f" ({a['held_key']})" if a.get('held_key') else ''))
        md += [f'- HOLD: {x}' for x in a['hold']] + [f'- warn: {x}' for x in a['warn']] + ['']
    if rep.get('error'): md.append(f"- HOLD: {rep['error']}")
    open(out / f'{tag}.md', 'w', encoding='utf-8').write('\n'.join(md) + '\n')
    go = verdict in ('GO', 'FORCED')
    if env.get('GITHUB_OUTPUT'):
        with open(env['GITHUB_OUTPUT'], 'a') as f: f.write(f"go={'yes' if go else 'no'}\nverdict={verdict}\n")
    print(f"::notice title=2-fer pre-line check::{tag}: {verdict}" + (f": {'; '.join(holds)[:600]}" if holds else ''))
    return rep


if __name__ == '__main__':
    try: main()
    except Exception as e:  # noqa: BLE001
        print(f'::warning title=2-fer pre-line check::stopped ({str(e)[:200]}): HOLD')
        if os.environ.get('GITHUB_OUTPUT'):
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f: f.write('go=no\nverdict=HOLD\n')
    sys.exit(0)
