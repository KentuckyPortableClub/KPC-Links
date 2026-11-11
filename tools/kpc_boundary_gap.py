#!/usr/bin/env python3
"""Why does a US key park have no outline? Sorts every park in data/us-key/US-XX.json that is missing from
data/outlines/US-XX.geojson.gz into one cause. Offline: reads files in the repo only, contacts nothing.

  python3 tools/kpc_boundary_gap.py [--out docs/boundary-gap-nov11.csv] [--history]

--history also walks `git log` for data/us-key and names, per park, the run that last had it joined as official.
That needs enough git history (a shallow clone only sees what it fetched). Run it again after a build to refresh the CSV.
Causes: joined_outline_not_built, join_failed_name, join_failed_pin, no_layer_record, trail_line_only, held_on_purpose,
joined_record_has_no_shape, outline_in_other_state_file.   KPC owner, 2026-11-11."""
import argparse, collections, csv, glob, gzip, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, ".github", "scripts"))
import kpc_master as M  # noqa: E402


def cand_text(v):
    return ' | '.join(str(x[3]) for k in ('c', 'a') for x in v.get(k) or [] if isinstance(x, list) and len(x) > 3)


def classify(v):
    ids = [str(x[0]) for x in v.get('m') or [] if isinstance(x, list) and x]
    nt = [i for i in ids if not i.startswith('trl')]
    ct = cand_text(v); g = v.get('g'); bk = v.get('bk') or []
    if v.get('held') or v.get('not_mine') or 'a person said NO' in ct or ct.startswith('held') or ' held' in ct[:40]:
        h = v.get('held')
        return 'held_on_purpose', (h.get('why') if isinstance(h, dict) else '') or ('a person said NO' if 'a person said NO' in ct else ct[:70])
    if ids and not nt: return 'trail_line_only', 'trail line, drawn by the trails layer'
    if nt and g == 'pin':
        return 'joined_record_has_no_shape', ('the joined agency record has no shape' if len(bk) > 4 and bk[4] == 'noshape' else 'joined but graded pin')
    if nt: return 'joined_outline_not_built', 'joined, %d rec, no outline built' % len(nt)
    if len(bk) > 4 and bk[4] in ('noshape', 'nopin', 'pin00', 'pinbad'):
        return 'joined_record_has_no_shape', {'noshape': 'the matched agency record has no shape', 'nopin': 'POTA has no pin',
                                              'pin00': 'POTA pin is 0,0', 'pinbad': 'impossible POTA pin (not moved)'}[bk[4]]
    if 'same name far' in ct and 'similar name' not in ct and 'different name' not in ct: return 'join_failed_pin', 'same-name record is far from the pin'
    if any(s in ct for s in ('similar name', 'different name', 'different kind', 'also joined')):
        return 'join_failed_name', ('a similar-name record exists but the rule did not accept it' if 'similar name' in ct else 'pin inside a record, no name agrees')
    return 'no_layer_record', 'no saved layer record near the pin' if len(bk) > 4 and bk[4] == 'nocand' else 'nothing joined and no candidate'


def sh(*a):
    return subprocess.run(a, capture_output=True, cwd=ROOT).stdout


def history():
    """ref -> 'MM-DD hash' of the first run after it was last joined official and then wasn't (still not back)."""
    last, lost = {}, {}
    for line in sh('git', 'log', '--format=%h %ad', '--date=format:%m-%d', '--reverse', '--', 'data/us-key').decode().split('\n'):
        if not line.strip(): continue
        h, d = line.split()
        cur = {}
        for f in sh('git', 'ls-tree', '-r', '--name-only', h, 'data/us-key').decode().split('\n'):
            if not (f.startswith('data/us-key/US-') and f.endswith('.json')) or 'overrides' in f: continue
            try: p = json.loads(sh('git', 'show', f'{h}:{f}'))['parks']
            except Exception: continue
            for r, v in p.items(): cur[r] = (v.get('g'), bool(v.get('m')))
        for r, (g, m) in cur.items():
            if g == 'official' and m: last[r] = h; lost.pop(r, None)
            elif r in last and r not in lost: lost[r] = f'{d} {h}'
    return lost


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default=os.path.join(ROOT, 'docs', 'boundary-gap-nov11.csv')); ap.add_argument('--history', action='store_true')
    a = ap.parse_args()
    keys, files, elsewhere = {}, {}, {}
    for kp in sorted(glob.glob(os.path.join(ROOT, 'data', 'us-key', 'US-??.json'))):
        st = os.path.basename(kp)[3:5]; keys[st] = json.load(open(kp))['parks']
    home = {r: st for st, p in keys.items() for r in p}
    for st in keys:
        files[st] = set(M.load_area(f'US-{st}', os.path.join(ROOT, 'data', 'outlines')))   # Nov 11: every part of a state in parts
    for st, refs in files.items():
        for r in refs:
            if home.get(r) not in (None, st): elsewhere.setdefault(r, set()).add(st)
    queue = collections.defaultdict(set)
    for f in glob.glob(os.path.join(ROOT, 'data', 'outlines', 'solver-queue', '*.csv')):
        rows = list(csv.reader(open(f, encoding='utf-8')))
        if rows and rows[0][:1] == ['ref']:
            for row in rows[1:]: queue[row[0]].add(os.path.basename(f)[:-4])
    lost = history() if a.history else {}
    out = []
    for st, parks in keys.items():
        for ref, v in parks.items():
            if ref in files[st]: continue
            b, why = classify(v)
            if ref in elsewhere and b in ('joined_outline_not_built', 'join_failed_name', 'no_layer_record', 'joined_record_has_no_shape'):
                b, why = 'outline_in_other_state_file', 'outline only in US-%s file' % ','.join(sorted(elsewhere[ref]))
            out.append([st, ref, (v.get('n') or '')[:60], v.get('t'), v.get('g'), b, why[:70], ';'.join(sorted(queue.get(ref, [])))[:30], lost.get(ref, '')])
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['state', 'ref', 'name', 'type', 'key_grade', 'cause', 'reason', 'solver_queue_layers', 'last_joined_then_dropped_(date_hash)']); w.writerows(out)
    print(len(out), 'of', sum(len(p) for p in keys.values()), 'key parks have no outline in their own state file')
    for k, n in collections.Counter(r[5] for r in out).most_common(): print(f'  {n:5d}  {k}')
    return 0


if __name__ == '__main__': sys.exit(main())
