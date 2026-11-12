#!/usr/bin/env python3
"""2-FER POST-LINE CHECK (Nov 4 2026; Brandon, directly (Mapping chat), 4:52 AM CST Nov 4: "2fer line review? Plan and install any pre and post line bots for the 2fer
system."). Runs AFTER a 2-fer run finished (KPC-Data kpc-fers-postline.yml: workflow_run, no cron). READ-ONLY on the 2-fer data,
never fails, releases nothing: it only writes a report for Quality to data/status/fers-postline/ (latest.json + latest.md).

For every 2-fer file HELD in the waiting room (data/waiting/in/data/fers/<area>.json[.gz] = the new, ungraded output) it compares
with the previous output (the live data/fers/<area>.json[.gz]):
  * pairs gained and lost (a 'live' pair = status candidate / very tight), with the new status of a lost pair
  * pairs touching HELD parks (the key outline used differs from the live key: still waiting for a grade) or PIN-ONLY parks
    (no outline in the key: the pair can only come from a pin)
  * water / bank cases (river rows, 'water' or 'bank' in the status or tier)
  * single-record same land (kind 'same land' rows kept live, or 'not sure: one record covers two parks')
  * overlap sizes near a threshold: wide_m within +-NEAR (default 20 %) of 22.86 m (25 yd, kept), 45.72 m (50 yd, very tight),
    91.44 m (100 yd, small)
  * stale inputs: the key (or its overrides.json) is newer than the output's last pass; no pre-line report, or a HOLD/FORCED one
env  DATA=. (KPC-Data)  LINKS=links (KPC-Links)  OUT=$DATA/data/status/fers-postline  NEAR=0.2  RUN_URL=..."""
import datetime, glob, gzip, json, os, pathlib, re, subprocess, sys, time

TH = [(22.86, '25 yd (kept)'), (45.72, '50 yd (very tight)'), (91.44, '100 yd (small)')]
LIVE = ('candidate', 'very tight')


def load(p):
    p = str(p)
    for q in (p, p + '.gz') if not p.endswith('.gz') else (p,):
        try: return json.load(gzip.open(q, 'rt', encoding='utf-8')) if q.endswith('.gz') else json.load(open(q, encoding='utf-8'))
        except Exception: continue  # noqa: BLE001
    return None


def kind_of(area): return 'ca-key' if area.startswith('CA-') else ('us-key' if area.startswith('US-') else 'world-key')


def pairs(d):
    out = {}
    for s in (d or {}).get('spots') or []:
        refs = s.get('refs') or []
        if len(refs) < 2: continue
        k = '+'.join(sorted(map(str, refs)))
        out.setdefault(k, []).append(s)
    return out


def is_live(spots): return any(str(s.get('status', '')).startswith(LIVE) for s in spots)


def day(s):
    try: return datetime.datetime.strptime(str(s)[:10], '%Y-%m-%d').replace(tzinfo=datetime.timezone.utc)
    except Exception: return None  # noqa: BLE001


def git_time(path, cwd):
    if subprocess.run(['git', 'rev-parse', '--is-shallow-repository'], cwd=cwd, capture_output=True, text=True).stdout.strip() != 'false': return None
    r = subprocess.run(['git', 'log', '-1', '--format=%ct', '--', path], cwd=cwd, capture_output=True, text=True)
    try: return datetime.datetime.fromtimestamp(int(r.stdout.strip()), datetime.timezone.utc)
    except Exception: return None  # noqa: BLE001


def area_report(area, new, old, data, links, near):
    kind = kind_of(area); np_, op = pairs(new), pairs(old)
    lk = (load(pathlib.Path(links) / f'data/{kind}/{area}.json') or {}).get('parks') or {}
    live_k = (load(pathlib.Path(data) / f'data/{kind}/{area}.json') or {}).get('parks') or {}
    mids = lambda p: sorted(str(x[0]) for x in (p or {}).get('m') or [])
    pin_only = {r for r, p in lk.items() if not p.get('m')}
    held = {r for r, p in lk.items() if r in live_k and mids(p) != mids(live_k[r])} | {r for r in lk if r not in live_k}
    gained = sorted(k for k, v in np_.items() if is_live(v) and not is_live(op.get(k, [])))
    lost = [{'pair': k, 'now': str((np_.get(k) or [{}])[0].get('status', 'gone'))[:90]} for k in sorted(op) if is_live(op[k]) and not is_live(np_.get(k, []))]
    R = {'gained': gained, 'lost': lost, 'live_before': sum(1 for v in op.values() if is_live(v)), 'live_now': sum(1 for v in np_.values() if is_live(v))}
    R['touch_held'] = sorted(k for k, v in np_.items() if is_live(v) and set(k.split('+')) & held)
    R['touch_pin_only'] = sorted(k for k, v in np_.items() if is_live(v) and set(k.split('+')) & pin_only)
    wb, sl, nr = [], [], []
    for k, v in np_.items():
        for s in v:
            st, tier = str(s.get('status', '')), str(s.get('tier', ''))
            if st.startswith('dropped') or st.startswith('merged'): continue
            if s.get('kind') == 'river' or re.search(r'water|bank', st + ' ' + tier, re.I): wb.append({'pair': k, 'kind': s.get('kind'), 'status': st[:90]})
            if s.get('kind') == 'same land' and (st.startswith(LIVE) or 'one record covers two parks' in st): sl.append({'pair': k, 'status': st[:90]})
            w = s.get('wide_m')
            if st.startswith(LIVE + ('not sure',)) and isinstance(w, (int, float)):
                for t, name in TH:
                    if abs(w - t) <= t * near: nr.append({'pair': k, 'wide_m': round(w, 1), 'near': name, 'status': st[:40]}); break
    R.update(water_bank=wb, same_land_one_record=sl, near_threshold=nr)
    # stale inputs
    stale = []
    last = max([d for d in (day(new.get(p)) for p in ('pass1', 'pass2', 'pass3', 'pass5')) if d] or [None], key=lambda x: x or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)) if isinstance(new, dict) else None
    idx = load(pathlib.Path(links) / f'data/{kind}/index.json') or {}
    try: kb = datetime.datetime.strptime(str(idx.get('built')), '%Y-%m-%d %H:%M UTC').replace(tzinfo=datetime.timezone.utc)
    except Exception: kb = None  # noqa: BLE001
    if last and kb and kb.date() > last.date(): stale.append(f"the key build {idx.get('build')} ({idx.get('built')}) is newer than this output's last pass ({last:%Y-%m-%d})")
    # Nov 12 2026 (KPC-Links #151): the US overrides are a manifest + parts; the newest of them counts
    ot = max([t for t in (git_time(f'data/{kind}/{n}', links) for n in ['overrides.json'] + sorted(p.name for p in (pathlib.Path(links) / f'data/{kind}').glob('overrides-parks-*.json'))) if t] or [None],
             key=lambda t: t or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc))
    if last and ot and ot.date() > last.date(): stale.append(f'the key answers (overrides.json, {ot:%Y-%m-%d}) are newer than this output')
    pre = [json.load(open(f, encoding='utf-8')) for f in glob.glob(str(pathlib.Path(data) / 'data/status/fers-preline/*.json'))]
    pre = [p for p in pre if area in (p.get('states') or [])]
    if not pre: stale.append('no pre-line report for this area')
    else:
        p = max(pre, key=lambda x: x.get('checked') or '')
        R['preline'] = {'tag': p.get('tag'), 'verdict': p.get('verdict'), 'key_source': p.get('key_source'), 'held_key': p.get('held_key')}
        if p.get('verdict') != 'GO': stale.append(f"the last pre-line check ({p.get('tag')}) said {p.get('verdict')}")
    R['stale_inputs'] = stale
    return R


def main(env=os.environ):
    data = env.get('DATA') or '.'; links = env.get('LINKS') or 'links'; near = float(env.get('NEAR') or 0.2)
    out = pathlib.Path(env.get('OUT') or f'{data}/data/status/fers-postline')
    rep = {'checked': time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime()), 'run': env.get('RUN_URL', ''), 'areas': {},
           'about': '2-fer post-line check (Brandon, directly (Mapping chat), 4:52 AM CST Nov 4): read-only report for Quality. The 2-fers stay HELD in the waiting room; this releases nothing.'}
    try:
        held = sorted(glob.glob(str(pathlib.Path(data) / 'data/waiting/in/data/fers/*.json*')))
        # Nov 9 (Quality must-fix 4, run 42594981324: no post-line after a hand-started kpc-fers.yml run, which saves LIVE with no
        # waiting-room divert): PREV_DIR = a copy of the PREVIOUS save's data/fers; then the live files are the new output and
        # PREV_DIR's are the old ones (kpc-fers-postline.yml sets it for a 'KPC 2-fer bot (hidden)' run).
        prev = env.get('PREV_DIR') or ''
        if prev and not held:
            held = sorted(glob.glob(str(pathlib.Path(data) / 'data/fers/*.json*')))
            rep['mode'] = f'live save compared with the save before it ({prev})'
        for f in held:
            area = re.sub(r'\.json(\.gz)?$', '', os.path.basename(f))
            if not re.match(r'^(US|CA|W)-[A-Z0-9]+$', area): continue
            new = load(f); old = load(pathlib.Path(prev if prev and rep.get('mode') else data) / f'data/fers/{area}.json')
            try: rep['areas'][area] = area_report(area, new or {}, old or {}, data, links, near)
            except Exception as e: rep['areas'][area] = {'error': str(e)[:200]}  # noqa: BLE001
    except Exception as e:  # noqa: BLE001
        rep['error'] = str(e)[:200]
    out.mkdir(parents=True, exist_ok=True)
    json.dump(rep, open(out / 'latest.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    md = ['# 2-fer post-line check (for Quality)', '', f"{rep['checked']} · {rep['about']}", '']
    if not rep['areas']: md.append('No held 2-fer output in the waiting room.')
    for a, r in rep['areas'].items():
        if 'error' in r: md += [f'## {a}: could not compare ({r["error"]})', '']; continue
        md += [f"## {a}: live pairs {r['live_before']} -> {r['live_now']} (+{len(r['gained'])} / -{len(r['lost'])})",
               f"- gained: {' '.join(r['gained'][:30]) or '-'}", f"- lost: {'; '.join(x['pair'] + ' (' + x['now'] + ')' for x in r['lost'][:20]) or '-'}",
               f"- touching held parks: {' '.join(r['touch_held'][:20]) or '-'}", f"- touching pin-only parks: {' '.join(r['touch_pin_only'][:20]) or '-'}",
               f"- water / bank: {len(r['water_bank'])}", f"- one-record same land: {' '.join(x['pair'] for x in r['same_land_one_record'][:20]) or '-'}",
               f"- near a size threshold: {'; '.join(x['pair'] + ' ' + str(x['wide_m']) + ' m ~ ' + x['near'] for x in r['near_threshold'][:20]) or '-'}",
               f"- stale inputs: {'; '.join(r['stale_inputs']) or '-'}", '']
    open(out / 'latest.md', 'w', encoding='utf-8').write('\n'.join(md) + '\n')
    print(f"::notice title=2-fer post-line check::{len(rep['areas'])} held area(s) compared; report data/status/fers-postline/latest.md")
    return rep


if __name__ == '__main__':
    try: main()
    except Exception as e: print(f'::warning title=2-fer post-line check::stopped ({str(e)[:200]}); nothing changed')  # noqa: BLE001
    sys.exit(0)
