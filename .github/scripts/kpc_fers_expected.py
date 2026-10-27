#!/usr/bin/env python3
"""MISSING CHECK (chat 2, Oct 27 2026; HQ 3:46 PM, Brandon: 'chat 8 can't verify what's missing'). For each area of a 2-fer run, every
pair of parks we have an OUTSIDE reason to expect, with what the bot did with it:
  FOUND            a live row (candidate / very tight / water only, or folded into one)
  DROPPED          a row with the exact reason + the rule, or 'looked, no shared ground on the official outlines (rule 4)'
  NEVER LOOKED AT  the bot never tested the pair, with why (no official outline, a line park with no line, not in the run…)
Sources (why each pair is expected): 'hand list' = ky-trail-parks.json (Kentucky's river / trail pairs) · 'old guide' = the
Oct 13 Kentucky 2-fers guide (ky-overlaps.geojson, 76 pairs) · 'activated together' = POTA activation history, same call same day
(data/fers/pota-pairs-<st>.json, counts only) · 'near-touching' = outlines within 100 m (pass 1's looked file) · 'member report'
(data/fers/member-reports.json, later). Writes data/fers/expected-<area>.json; 'pass' = no NEVER LOOKED AT without a reason and
every DROPPED with a reason. Chat 8 reviews the DROPPED + NEVER LOOKED AT lists. AREA='ky' or STATES='US-OH'. Never fails."""
import itertools, json, os, pathlib, re, sys, time
OUT = pathlib.Path('data/fers')
LIVE = ('candidate', 'very tight', 'water only', 'merged into')
RULES = [(r'^dropped: side by side|two owners side by side', 'rule 14 (ownership: side by side, not layered)'),
         (r'^dropped: private', 'rule 2 + B-G2 (private land counts only for its own number)'),
         (r'^dropped: only inside an area closed', 'rule 10 (closed to the public)'),
         (r'^dropped in pass', 'rule 4 (the shared patch did not hold up on the fresher, finer official outlines)'),
         (r'ruling Oct 27', 'Kentucky ruling (Brandon / HQ Oct 27)'),
         (r'^not sure', 'rule 7 (NOT SURE is kept out)'),
         (r'^dropped', 'see the reason')]


def rule_of(st):
    return next((r for rx, r in RULES if re.search(rx, st, re.I)), '')


def load(p, d=None):
    try: return json.load(open(p))
    except Exception: return d  # noqa: BLE001


def build(area, files, tag='', sts=()):
    rows = []
    for f in files:
        for s in (load(f, {}) or {}).get('spots') or []: rows.append((set(s.get('refs') or []), str(s.get('status', '')), s.get('id', '')))
    looked = load(OUT / f'looked-{tag or area}.json', {}) or {}
    tested = {tuple(sorted(p.split('+'))) for p in looked.get('tested') or []}
    noout = looked.get('no_outline') or {}
    inrun = set(looked.get('parks') or [])
    exp = {}
    def add(refs, why):
        refs = tuple(sorted(set(refs)))
        if len(refs) < 2: return
        exp.setdefault(refs, set()).add(why)
    if area == 'ky':
        tp = load('ky-trail-parks.json', {}) or {}
        for t in tp.values():
            for p in t.get('parks') or []: add([t['ref']] + p['refs'], 'hand list (ky-trail-parks.json)')
        g = load('ky-overlaps.geojson', {}) or {}
        for ft in g.get('features') or []:
            refs = sorted({r for r, _ in (ft.get('properties') or {}).get('pota') or []})
            for a, b in itertools.combinations(refs, 2): add([a, b], 'old guide (Oct 13 Kentucky 2-fers guide)')
    sts = ['US-KY'] if area == 'ky' else list(sts)
    for st in sts:
        pp = load(OUT / f'pota-pairs-{st}.json', {}) or {}
        for k, n in (pp.get('pairs') or {}).items(): add(k.split('+'), f'activated together by the same call on the same day ({n}x, POTA history)')
    for a, b, m in looked.get('near100') or []: add([a, b], f'outlines come within {m} m of each other')
    for x in (load(OUT / 'member-reports.json', {}) or {}).get('reports') or []:
        if x.get('area') in (area, None): add(x.get('refs') or [], 'member report: ' + str(x.get('what', ''))[:60])
    out = {'FOUND': [], 'DROPPED': [], 'NEVER LOOKED AT': []}
    for refs, why in sorted(exp.items()):
        rs = set(refs)
        live = [r for r in rows if rs <= r[0] and r[1].startswith(LIVE)]
        pairs_live = len(refs) > 2 and all(any({a, b} <= r[0] and r[1].startswith(LIVE) for r in rows) for a, b in itertools.combinations(refs, 2) if not ({a, b} <= {x for x in refs if x not in inrun}))
        e = {'refs': list(refs), 'why_expected': sorted(why)}
        if live or pairs_live:
            e['row'] = (live[0][2] if live else 'each pair has a row'); out['FOUND'].append(e); continue
        dead = [r for r in rows if rs <= r[0]]
        if dead:
            st = dead[0][1]; e['reason'] = st[:200]; e['rule'] = rule_of(st); out['DROPPED'].append(e); continue
        if not looked:
            e['reason'] = 'unknown'; out['NEVER LOOKED AT'].append(e); continue
        miss = [r for r in refs if r in noout or r not in inrun]
        if miss:
            e['reason'] = '; '.join(f"{r}: {noout.get(r) or 'not in this run (another state, retired, or no POTA pin)'}" for r in miss)
            out['NEVER LOOKED AT'].append(e); continue
        pairs = list(itertools.combinations(refs, 2))
        if all(p in tested for p in pairs):
            e['reason'] = 'looked: no shared ground on the official outlines (no patch 25 yards across; not within 100 ft of a trail / river line)'
            e['rule'] = 'rule 4 / rule 5'; out['DROPPED'].append(e); continue
        e['reason'] = 'not tested: the outlines\' boxes do not touch (the parks are apart on the official maps)' if inrun >= rs else 'unknown'
        out['NEVER LOOKED AT'].append(e)
    bad = [e for e in out['NEVER LOOKED AT'] if e.get('reason') == 'unknown'] + [e for e in out['DROPPED'] if not e.get('reason')]
    if not looked: print(f'::notice title=2-fer missing check::{area}: no pass-1 list (looked-{area}.json): run pass 1 first', flush=True)
    res = {'about': __doc__.split('\n')[0] + ' See kpc_fers_expected.py. Chat 8 reviews DROPPED + NEVER LOOKED AT.', 'area': area,
           'date': time.strftime('%Y-%m-%d'), 'pass': not bad, 'counts': {k: len(v) for k, v in out.items()}, **out}
    (OUT / f'expected-{tag or area}.json').write_text(json.dumps(res, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f"::notice title=2-fer missing check::{area}: {res['counts']} expected pairs" + ('' if res['pass'] else f' · {len(bad)} with no reason'), flush=True)


def main():
    area = os.environ.get('AREA') or ''
    if area == 'ky': return build('ky', [OUT / 'US-KY.json'])
    raw = (os.environ.get('STATES') or '').upper().replace(',', ' ').split()
    sts = sorted(x if '-' in x else 'US-' + x for x in raw)
    if sts: build('-'.join(sorted(raw)), [OUT / f'{s}.json' for s in sts], os.environ.get('RUN_TAG') or '', sts)


if __name__ == '__main__':
    try: main()
    except Exception as e:  # noqa: BLE001
        print(f'::notice title=2-fer missing check::stopped: {e}', flush=True)
    sys.exit(0)
