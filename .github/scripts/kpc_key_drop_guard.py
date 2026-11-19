#!/usr/bin/env python3
"""Per-state drop guard for the US key (KPC owner, 2026-11-11): the run fails when a state loses more than 3% of its official parks.

Why: a short read can quietly cost joins (ND 2,168 -> 1,484 records and SD 1,797 -> 1,299 on Nov 10; WI 80,934 -> 1,585 on Nov 6).
The post-key check only warns, after the save. This runs BEFORE the save: it compares each data/us-key/US-XX.json in the working
tree with the copy on main (`git show <ref>:...`) and counts the parks graded official.
  drop = (official on main - official now) / official on main.   Over KPC_DROP_PCT (3) and more than KPC_DROP_MIN (1) park = FAIL.
A drop a person expects (a batch of signed NO answers, say) is let through for that run by naming the states in KPC_DROP_OK
("NV" or "NV UT"; the repo variable of the same name). Exit 1 on a failed state; the workflow then saves nothing from the run.
Nov 12 (KPC owner, 2026-11-12; each state stands alone): with --restore a failed state is put back to --ref byte for byte (key file,
tracts, outline files, index row), written to --failed-out (the stamp names it failed) and the guard exits 0: the other states are
saved and the run ends red. A state that cannot be put back = exit 1 and nothing is saved (as before).
The outline files are held to the same limit: data/outlines/US-XX.geojson.gz (with its parts) may not hold more than 3% fewer outlines than
main's; main's outlines of parks the key grades pin are not counted (the save leaves them out on purpose, Nov 11).
Offline. A state with no file on main (new) or no official park on main is skipped.
Nov 19 (Fable sitting 3 item 20 + owner 10:12 AM '1-4 I agree ... for now'; key-quality.md section 19 item 21c): NAMED PARKS. A
state in .github/key-drop-approved.json (or --approved / KPC_DROP_APPROVED) is judged park by park instead: every park that had an
outline on --ref (joined records) and has none now must be on that state's approved list, which a person wrote from the review
page (the lost outlines of the fact check, for the states the owner said yes to). One outline lost that is NOT on the list = the
state is held (restored, red), whatever its percent and whatever KPC_DROP_OK says. All lost outlines on the list = let through
for this run. An entry without decided_by is ignored (warning). Empty the file after the release run.

  python3 .github/scripts/kpc_key_drop_guard.py [--ref HEAD] [--key data/us-key] [--mark FILE] [--approved FILE]
  python3 .github/scripts/kpc_key_drop_guard.py approve --lost lost.json --states "AK MT" --decided-by "KPC owner, <date> (<words>)" [--out FILE]"""
import argparse, glob, gzip, json, os, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]


APPROVED_FILE = '.github/key-drop-approved.json'


def outlined(doc):
    """The parks of a key file that have an outline: joined records (the key's 'm'), whatever their grade."""
    return {r for r, p in (doc.get('parks') or {}).items() if isinstance(p, dict) and p.get('m')}


def load_approved(path):
    """{state: set of park numbers} from the approved file; an entry with no decided_by is ignored (printed)."""
    try: d = json.load(open(path, encoding='utf-8'))
    except FileNotFoundError: return {}
    except ValueError as e:
        print(f'::error title=Drop guard::{path} cannot be read ({e}): no state is let through by name this run'); return {}
    out = {}
    for st, v in sorted((d.get('states') or {}).items()):
        st = str(st).upper().replace('US-', '')
        if not str((v or {}).get('decided_by') or '').strip():
            print(f'::warning title=Drop guard US-{st}::approved list has no decided_by: ignored'); continue
        out[st] = {str(x) for x in (v.get('parks') or [])}
    return out


def judge_named(lost, approved):
    """lost: {state: set of parks that lost their outline}; approved: {state: set}. Only states on the approved list are judged.
    Returns (held rows, let-through rows); a row = (state, lost count, sorted parks NOT on the list)."""
    held, ok = [], []
    for st in sorted(approved):
        lo = lost.get(st, set()); extra = sorted(lo - approved[st])
        (held if extra else ok).append((st, len(lo), extra))
    return held, ok


def official(doc):
    return sum(1 for p in (doc.get('parks') or {}).values() if isinstance(p, dict) and p.get('g') == 'official')


def judge(before, now, pct=3.0, min_parks=1, ok_states=()):
    """before / now: {state: official count}. Returns (failed rows, allowed rows); a row = (state, before, now, percent)."""
    failed, allowed = [], []
    for st in sorted(before):
        b, n = before[st], now.get(st)
        if n is None or b <= 0 or n >= b: continue
        lost = b - n; p = 100.0 * lost / b
        if p > pct and lost > min_parks: (allowed if st in ok_states else failed).append((st, b, n, round(p, 1)))
    return failed, allowed


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--ref', default='HEAD'); ap.add_argument('--key', default='data/us-key')
    ap.add_argument('--repo', default=str(ROOT)); ap.add_argument('--mark')
    ap.add_argument('--restore', action='store_true', help='Nov 12: put a failed state back to --ref byte for byte and go on (the others are saved)')
    ap.add_argument('--failed-out', help='with --restore: write the kept states here (one per line), for the stamp')
    ap.add_argument('--approved', help='Nov 19: the named-parks list (default .github/key-drop-approved.json, or KPC_DROP_APPROVED)')
    a = ap.parse_args()
    pct = float(os.environ.get('KPC_DROP_PCT') or 3); mn = int(os.environ.get('KPC_DROP_MIN') or 1)
    ok = set((os.environ.get('KPC_DROP_OK') or '').replace(',', ' ').upper().split())
    apath = a.approved or os.environ.get('KPC_DROP_APPROVED') or os.path.join(a.repo, APPROVED_FILE)
    named = load_approved(apath)
    before, now, unread, lost = {}, {}, [], {}
    for f in sorted(glob.glob(os.path.join(a.repo, a.key, 'US-??.json'))):
        st = os.path.basename(f)[3:5]
        r = subprocess.run(['git', 'show', f'{a.ref}:{a.key}/US-{st}.json'], cwd=a.repo, capture_output=True)
        if r.returncode != 0: continue                       # not on main yet: a new state has nothing to drop from
        try:
            db, dn = json.loads(r.stdout), json.load(open(f, encoding='utf-8'))
            before[st] = official(db); now[st] = official(dn); lost[st] = outlined(db) - outlined(dn)
        except ValueError: unread.append(st)
    failed, allowed = judge(before, now, pct, mn, ok - set(named))
    ob, on = {}, {}
    # Nov 11 (KPC owner, 2026-11-11): an area may be in parts (US-AK.geojson.gz + US-AK.p2.geojson.gz ...): every part is counted.
    # Main's outlines of parks the key (this run's) grades pin are not counted: the save leaves them out on purpose
    # (kpc_master.pin_drops), so a pin clean-up is not a drop. Any other lost outline still counts.
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import kpc_master as M  # noqa: E402
    key_dir = pathlib.Path(a.repo) / a.key
    for f in sorted(glob.glob(os.path.join(a.repo, 'data', 'outlines', 'US-??.geojson.gz'))):
        st = os.path.basename(f)[3:5]; name = os.path.basename(f)

        def main_read(n):
            r = subprocess.run(['git', 'show', f'{a.ref}:data/outlines/{n}'], cwd=a.repo, capture_output=True)
            return r.stdout if r.returncode == 0 else None
        if main_read(name) is None: continue
        try:
            before_refs = set(M.recs_of_doc(M.load_doc_parts(name, main_read)))
            now_refs = set(M.load_area(f'US-{st}', os.path.dirname(f)))
            ob[st] = len(before_refs - M.pin_drops(f'US-{st}', before_refs, key_dir)); on[st] = len(now_refs)
            if st in named: lost[st] = lost.get(st, set()) | (before_refs - now_refs)   # Nov 19: an outline gone from the file counts too
        except Exception: unread.append(st)  # noqa: BLE001
    of, oa = judge(ob, on, pct, mn, ok - set(named))
    # Nov 19 NAMED PARKS: a state on the approved list stands or falls by its list alone
    nheld, nok = judge_named(lost, {st: v for st, v in named.items() if st in before})
    for st, n_, extra in nok:
        print(f'::warning title=Drop guard US-{st}::{n_} outline(s) lost, every one on the approved list ({len(named[st])} named): let through for this run')
    for st, n_, extra in nheld:
        print(f'::error title=Drop guard US-{st}::{len(extra)} outline(s) lost that are NOT on the approved list: {", ".join(extra[:12])}'
              f'{" ..." if len(extra) > 12 else ""}. The state is held.')
    failed = [r for r in failed if r[0] not in named]; of = [r for r in of if r[0] not in named]
    allowed = [r for r in allowed if r[0] not in named]
    held_named = [st for st, _, _ in nheld]
    for st, b, n, p in oa: print(f'::warning title=Drop guard US-{st}::outlines {b} -> {n} (-{p}%), let through by KPC_DROP_OK for this run')
    for st, b, n, p in of:
        print(f'::error title=Drop guard US-{st}::outlines {b} -> {n} (-{p}%, limit {pct:g}%). The run saves nothing.')
    failed += [r for r in of if r[0] not in {x[0] for x in failed}]; unread = sorted(set(unread))
    for st, b, n, p in allowed:
        print(f'::warning title=Drop guard US-{st}::official parks {b} -> {n} (-{p}%), let through by KPC_DROP_OK for this run')
    for st in unread: print(f'::error title=Drop guard US-{st}::the key file could not be read: counted as a failed state')
    for st, b, n, p in failed:
        print(f'::error title=Drop guard US-{st}::official parks {b} -> {n} (-{p}%, limit {pct:g}%). The run saves nothing. '
              f'If the drop is expected, set the repo variable KPC_DROP_OK to "{st}" for one run.')
    print(f'drop guard: {len(before)} state(s) compared with {a.ref}; {len(set([r[0] for r in failed] + unread + held_named))} failed, '
          f'{len(allowed) + len(nok)} let through ({len(nok)} by the named-parks list)')
    if failed or unread or held_named:
        bad = sorted(set([r[0] for r in failed] + unread + held_named))
        if a.restore:   # Nov 12 (KPC owner, 2026-11-12): each state stands alone
            try:
                restore(a.repo, a.key, a.ref, bad)
            except Exception as e:  # noqa: BLE001  a state that cannot be put back = the old rule: nothing is saved
                print(f'::error title=Drop guard::could not keep {" ".join(bad)} from {a.ref} ({type(e).__name__}: {str(e)[:160]}): the run saves nothing')
                if a.mark: pathlib.Path(a.mark).write_text(' '.join(bad) + '\n')
                return 1
            if a.failed_out: pathlib.Path(a.failed_out).write_text(''.join(st + '\n' for st in bad))
            print(f'::error title=Drop guard::{" ".join(bad)} kept from {a.ref} byte for byte (key file, tracts, outlines, index row) and named failed; '
                  'the other states are saved; the run ends red')
            return 0
        if a.mark: pathlib.Path(a.mark).write_text(' '.join(bad) + '\n')
        return 1
    return 0


def restore(repo, key, ref, states):
    """Nov 12 (KPC owner, 2026-11-12): put each dropped state back to `ref` byte for byte: data/us-key/US-XX.json, tracts/US-XX.json,
    data/outlines/US-XX*.geojson.gz (every part), and its index row. A file that is not on ref is removed (a new state's short read)."""
    repo = pathlib.Path(repo)
    def show(rel):
        r = subprocess.run(['git', 'show', f'{ref}:{rel}'], cwd=repo, capture_output=True)
        return r.stdout if r.returncode == 0 else None
    for st in states:
        rels = [f'{key}/US-{st}.json', f'{key}/tracts/US-{st}.json']
        ls = subprocess.run(['git', 'ls-tree', '--name-only', ref, 'data/outlines/'], cwd=repo, capture_output=True, text=True).stdout.split()
        rels += [x for x in ls if os.path.basename(x).startswith(f'US-{st}.') and x.endswith('.geojson.gz')]
        rels += [os.path.relpath(f, repo) for f in glob.glob(str(repo / 'data' / 'outlines' / f'US-{st}.*geojson.gz'))]
        for rel in sorted(set(rels)):
            b = show(rel); f = repo / rel
            if b is None: f.unlink(missing_ok=True)
            else: f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(b)
    ip = repo / key / 'index.json'
    old = json.loads(show(f'{key}/index.json') or b'{}')
    d = json.load(open(ip, encoding='utf-8'))
    for st in states:
        if st in (old.get('states') or {}): d.setdefault('states', {})[st] = old['states'][st]
        else: (d.get('states') or {}).pop(st, None)
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    from kpc_save import save_json   # the join's own writer (same bytes as the join wrote the index)
    save_json(str(ip), d)


def approve(argv):
    """Write the named-parks list from a fact check's lost.json ([{area, ref, ...}]) for the states the owner said yes to."""
    ap = argparse.ArgumentParser(prog='kpc_key_drop_guard.py approve'); ap.add_argument('--lost', required=True)
    ap.add_argument('--states', required=True); ap.add_argument('--decided-by', required=True)
    ap.add_argument('--out', default=str(ROOT / APPROVED_FILE)); ap.add_argument('--source', default='')
    a = ap.parse_args(argv)
    sts = {s.upper().replace('US-', '') for s in a.states.replace(',', ' ').split()}
    rows = json.load(open(a.lost, encoding='utf-8'))
    try: doc = json.load(open(a.out, encoding='utf-8'))
    except FileNotFoundError: doc = {}
    doc['note'] = ('Named parks the owner let lose their outline in ONE key run (kpc_key_drop_guard.py, key-quality.md section 19 item 21c). '
                   'A state listed here is held if it loses any outline NOT named. Empty "states" after the release run.')
    doc.setdefault('states', {})
    for st in sorted(sts):
        parks = sorted({str(r['ref']) for r in rows if str(r.get('area', '')).upper().replace('US-', '') == st})
        doc['states'][st] = {'parks': parks, 'decided_by': a.decided_by, 'source': a.source or os.path.basename(a.lost)}
        print(f'{st}: {len(parks)} park(s)')
    pathlib.Path(a.out).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    return 0


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'approve': sys.exit(approve(sys.argv[2:]))
    sys.exit(main())
