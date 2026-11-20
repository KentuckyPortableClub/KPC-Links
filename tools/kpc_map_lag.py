#!/usr/bin/env python3
"""How far is the public map behind the key? (job C, N2, outside review finding F3; KPC owner, 2026-11-19). READ-ONLY, BY HAND ONLY.

One line per US state:
  released   the day the state's public files were released (data/released/RELEASED.json: live[US-XX].time, else areas.US.time)
  key        the day of today's key (data/us-key/index.json 'built' for a state the last build rebuilt, else the last commit of
             data/us-key/US-XX.json)
  days       key minus released, in whole days
  differ     parks that differ between the released key (data/released/us-key/US-XX.json, parts joined) and today's key
             (data/us-key/US-XX.json): a park in one key only, or a park whose grade (g) or joined record ids (the ids in m) differ.
             Names, acres, candidates and notes are not counted.
  row_only   released outlines (data/released/outlines/US-XX.geojson.gz, parts joined) with no real record id, only row numbers
             (row219): not built from the key (kpc_master.outline_record_ids)
Dates are Central time (America/Chicago, the owner's), shown as YYYY-MM-DD.

  python3 tools/kpc_map_lag.py [--repo .] [--rev REV] [--states "US-MT US-DE"] [--json] [--out FILE]

--rev reads every file at that commit (git show) instead of the working tree. --out writes the lines to FILE, which must be outside
the repo: the output belongs on the KPC-Data tools-out branch, never on main. Nothing else is written, nothing is fetched, no
workflow is started, and no timer runs this: building is stopped, so the gap grows every day and a daily line would only be noise.
The owner turns a timer on later and picks how many days counts as too far behind.
Before writing this the repo's own tools were read (see the pull request): none compares the released key with today's key."""
import argparse, datetime, json, os, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
STATE = re.compile(r'US-[A-Z]{2}')
ROW = re.compile(r'row[0-9]+')


def central(ts):
    """A UTC time text ('2026-11-11T22:10:22Z', '2026-11-19 21:52 UTC', '2026-11-19 21:52:12 +0000') -> the Central date, or ''."""
    s = str(ts or '').strip()
    if not s: return ''
    s = s.replace(' UTC', '+00:00').replace('Z', '+00:00')
    s = re.sub(r' ([+-]\d{2})(\d{2})$', r'\1:\2', s)
    try: d = datetime.datetime.fromisoformat(s.replace(' ', 'T', 1))
    except ValueError: return ''
    if d.tzinfo is None: d = d.replace(tzinfo=datetime.timezone.utc)
    try:
        from zoneinfo import ZoneInfo
        return d.astimezone(ZoneInfo('America/Chicago')).date().isoformat()
    except Exception:  # noqa: BLE001  (no tz database: CST, UTC-6)
        return (d.astimezone(datetime.timezone.utc) - datetime.timedelta(hours=6)).date().isoformat()


class Files:
    """Read repo files from the working tree, or at one commit (rev)."""
    def __init__(self, repo, rev=None):
        self.repo, self.rev = pathlib.Path(repo), rev

    def read(self, path):
        if self.rev:
            r = subprocess.run(['git', 'show', f'{self.rev}:{path}'], cwd=self.repo, capture_output=True)
            return r.stdout if r.returncode == 0 else None
        f = self.repo / path
        return f.read_bytes() if f.is_file() else None

    def json(self, path):
        b = self.read(path)
        if b is None: return None
        try: return json.loads(b.decode('utf-8'))
        except ValueError: return None

    def doc(self, folder, name):
        """A document that may be cut into parts (the release part scheme), joined; None when there is none."""
        import kpc_master as M
        return M.load_doc_parts(name, lambda n: self.read(f'{folder}/{n}'))

    def last_commit_time(self, path):
        r = subprocess.run(['git', 'log', '-1', '--format=%cI', self.rev or 'HEAD', '--', path], cwd=self.repo, capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else ''


def park_view(p):
    """What counts as a difference for one park: its grade and its joined record ids."""
    if not isinstance(p, dict): return None
    return (p.get('g'), frozenset(str(x[0]) for x in (p.get('m') or []) if isinstance(x, list) and x))


def parks_differ(old, new):
    old, new = old or {}, new or {}
    return sum(1 for r in set(old) | set(new) if park_view(old.get(r)) != park_view(new.get(r)))


def row_only(doc):
    import kpc_master as M
    n = 0
    for ft in (doc or {}).get('features') or []:
        pr = ft.get('properties') or {}
        ids = [str(i) for i in (pr.get('record_ids') or [])]
        if not M.outline_record_ids(pr) and any(ROW.fullmatch(i) for i in ids): n += 1
    return n


def lag(repo='.', rev=None, states=None):
    """[{state, released, key, days, differ, row_only}] for every US state with a key file (or the named states)."""
    F = Files(repo, rev)
    rel = F.json('data/released/RELEASED.json') or {}
    idx = F.json('data/us-key/index.json') or {}
    if states: want = sorted(states)
    else:
        if rev:
            r = subprocess.run(['git', 'ls-tree', '--name-only', f'{rev}:data/us-key'], cwd=F.repo, capture_output=True, text=True)
            names = r.stdout.split()
        else:
            names = [p.name for p in (F.repo / 'data/us-key').glob('US-??.json')]
        want = sorted(n[:-5] for n in names if re.fullmatch(r'US-[A-Z]{2}\.json', n))
    rebuilt = set(idx.get('areas_rebuilt') or [])
    out = []
    for st in want:
        live = (rel.get('live') or {}).get(st) if isinstance(rel.get('live'), dict) else None
        rtime = (live or {}).get('time') or (((rel.get('areas') or {}).get('US') or {}).get('time') if f'us-key/{st}.json' in (rel.get('files') or {}) else '')
        ktime = idx.get('built') if st[3:] in rebuilt else F.last_commit_time(f'data/us-key/{st}.json')
        new = F.json(f'data/us-key/{st}.json')
        old = F.doc('data/released/us-key', f'{st}.json') if rtime else None
        outl = F.doc('data/released/outlines', f'{st}.geojson.gz') if rtime else None
        r_day, k_day = central(rtime), central(ktime)
        days = (datetime.date.fromisoformat(k_day) - datetime.date.fromisoformat(r_day)).days if r_day and k_day else None
        out.append({'state': st, 'released': r_day or 'never', 'key': k_day or '?', 'days': days,
                    'differ': parks_differ((old or {}).get('parks'), (new or {}).get('parks')) if new is not None else None,
                    'row_only': row_only(outl)})
    return out


def line(r):
    return (f"{r['state']}  released {r['released']}  key {r['key']}  "
            f"{'?' if r['days'] is None else r['days']} day(s) behind  {'?' if r['differ'] is None else r['differ']} park(s) differ  "
            f"{r['row_only']} row-only outline(s)")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--repo', default='.')
    ap.add_argument('--rev', default='')
    ap.add_argument('--states', default='')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--out', default='')
    a = ap.parse_args(argv)
    states = [s.upper() for s in a.states.replace(',', ' ').split()]
    bad = [s for s in states if not STATE.fullmatch(s)]
    if bad: print(f"not a US state: {' '.join(bad)} (use US-MT US-DE)", file=sys.stderr); return 2
    if a.out:
        o = pathlib.Path(a.out).resolve(); r = pathlib.Path(a.repo).resolve()
        if o == r or r in o.parents:
            print(f'--out {a.out} is inside the repo: the lines go to the KPC-Data tools-out branch, never to main', file=sys.stderr); return 2
    rows = lag(a.repo, a.rev or None, states or None)
    text = json.dumps(rows, indent=1) + '\n' if a.json else ''.join(line(r) + '\n' for r in rows)
    if a.out: pathlib.Path(a.out).write_text(text, encoding='utf-8')
    else: sys.stdout.write(text)
    return 0


if __name__ == '__main__': sys.exit(main())
