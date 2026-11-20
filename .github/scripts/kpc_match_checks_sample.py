#!/usr/bin/env python3
"""kpc_match_checks_sample.py: re-score a graded sample against the match checks (kpc_match_checks.py). Counts only.

A graded sample is a folder holding answers-pass1/jobS-random-sample.answers.csv (one row per park: item, ref, area, name,
park_type, the grader's verdict, the record ids that are not the park, and the park's outline records) and
kit-keys/sample-answer-key.json (the planted items, left out). The sample itself is private and is never copied into this
repo: the folder is read at run time from wherever it is kept (--sample). This tool contacts nothing, builds nothing,
names no park and writes only the --out file.

For every state in the sample the whole state goes through the same pass the US key runs (kpc_match_checks_count), and then:
  wrong caught  = records the grader named as not the park that the pass sends to check (or that never draw the outline)
  right lost    = records of parks the grader called YES with no wrong record that the pass sends to check

  python3 kpc_match_checks_sample.py --sample DIR --cache DIR [--cache DIR] --facts park-facts.json.gz [--keys data/us-key]
"""
import argparse, collections, csv, gzip, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kpc_match_checks as MC  # noqa: E402
import kpc_match_checks_count as CNT  # noqa: E402

VERDICT = 'is_our_outline_the_park (YES / NO / PART / BIGGER / CANNOT TELL)'
WRONG = 'records_that_are_not_the_park (ids)'
RECS = 'our_outline_records (id | name | acres as the layer gives them)'


def read_sample(folder):
    plants = set(json.load(open(os.path.join(folder, 'kit-keys', 'sample-answer-key.json'))).get('plants') or [])
    rows = []
    with open(os.path.join(folder, 'answers-pass1', 'jobS-random-sample.answers.csv'), encoding='utf-8-sig') as fh:
        for x in csv.DictReader(fh):
            if x['item'] in plants: continue
            wrong = {t.strip() for t in (x.get(WRONG) or '').replace(';', ',').split(',') if t.strip()}
            recs = [t.split(' | ')[0].strip() for t in (x.get(RECS) or '').split(' ; ') if t.strip()]
            v = (x.get(VERDICT) or '').strip().upper()
            grp = 'wrong' if wrong else 'right' if v == 'YES' else 'cannot tell' if v == 'CANNOT TELL' else 'other'
            rows.append({'ref': x['ref'], 'st': x['area'][3:], 'group': grp, 'wrong': wrong, 'recs': recs})
    return rows


def score(rows, per_state):
    """per_state[st] = {'hits': [[park, what, record id], ...], 'parks': parks after the pass}."""
    c = collections.Counter()
    why_w, why_r = collections.Counter(), collections.Counter()
    lost_parks = 0
    for r in rows:
        S = per_state.get(r['st'])
        if S is None: c['state not scored'] += 1; continue
        moved = {}
        for ref, what, rid in S['hits']:
            if ref == r['ref'] and what != 'joined (id)': moved[str(rid)] = what
        after = {str(q[0]) for q in (S['parks'].get(r['ref']) or {}).get('m') or []}
        if r['group'] == 'right' and r['recs'] and not after: lost_parks += 1
        for rid in r['recs']:
            hit = rid in moved
            if r['group'] == 'wrong' and rid in r['wrong']:
                c['wrong records'] += 1; c['wrong caught'] += hit
                if hit: why_w[moved[rid]] += 1
            elif r['group'] == 'right':
                c['right records'] += 1; c['right lost'] += hit
                if hit: why_r[moved[rid]] += 1
    c['right parks'] = sum(1 for r in rows if r['group'] == 'right')
    c['wrong parks'] = sum(1 for r in rows if r['group'] == 'wrong')
    c['right parks left as a pin'] = lost_parks
    return {'counts': dict(c), 'wrong caught by reason': dict(why_w), 'right lost by reason': dict(why_r)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--sample', required=True)
    ap.add_argument('--keys', default='data/us-key')
    ap.add_argument('--cache', required=True, action='append')
    ap.add_argument('--facts', required=True)
    ap.add_argument('--units', default='data/nps-units.json')
    ap.add_argument('--out')
    a = ap.parse_args(argv)
    rows = read_sample(a.sample)
    facts = json.load(gzip.open(a.facts, 'rt') if a.facts.endswith('.gz') else open(a.facts))['parks']
    layers = json.load(open(os.path.join(a.keys, 'layers.json')))
    units = MC.load_nps_units(a.units)
    per = {}
    for st in sorted({r['st'] for r in rows}):
        kf = os.path.join(a.keys, f'US-{st}.json')
        recs = CNT.load_recs(a.cache, st)
        if not os.path.exists(kf) or recs is None: continue
        seen = {}
        CNT.predict_state(st, json.load(open(kf)), recs, facts, layers, units, seen)
        per[st] = seen
    rep = dict(score(rows, per), about='counts only; no park or record named')
    print(json.dumps(rep, sort_keys=True))
    if a.out:
        with open(a.out, 'w') as fh: json.dump(rep, fh, indent=1, sort_keys=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
