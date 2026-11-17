#!/usr/bin/env python3
"""kpc_layer_refresh.py: the one wire between the keeper's layer requests and the old saved-shapes bots (Handoff 3, third job).

Plan: .claude/notes/layer-refresh.md. The keeper (KPC-Store) walks the layers; when a layer's ETag or lastEditDate moved it adds
one row to a small request file. This script READS that file and says which areas the existing cache jobs
(kpc-geo-cache.yml, kpc-world-cache.yml) should re-read. It never fetches anything itself, it imports no network module, and it
writes no saved copy: the fetch code, the per-host pacing, the release upload and the save-check guard stay the cache jobs' own.

  python3 kpc_layer_refresh.py plan --requests FILE --job us|world [--want 'KY TN'] [--known 'AL AK ...'] [--asset-dates FILE]
                                    [--receipt OUT.json] [--summary OUT.md] [--output-key groups|list] [--group 5]

stdout: '<output-key>=<json list>' for $GITHUB_OUTPUT (us: groups of --group state codes; world: country codes, CA = all of
Canada), then 'full=<json list>': the areas that get their one full-detail save (R-LR2 'full'; kpc_layer_full_save.sh).
No request file, an unreadable one, or no row that may be served = empty lists = nothing is fetched.

The request file (format 1; written by the keeper, read only here):
  {"format": 1, "written": "<UTC time>",
   "requests": [{"layer": "<layer address>", "area": "US-KY", "moved": ["etag", "lastEditDate"], "date": "YYYY-MM-DD",
                 "by": "keeper", "dying": false}],
   "walked":   [{"layer": "...", "area": "US-KY"}],     every layer the keeper has a first reading for
   "unwalked": [{"layer": "...", "area": "US-KY"}]}     layers on its list with no first reading yet: UNKNOWN, never 'unchanged'
A layer address is never printed, never written to the receipt and never used to fetch: the cache jobs re-read the whole area
file they already own (US-XX.json.gz, W-XX.json.gz, CA-ALL.json.gz). Only area codes and counts reach a log.

The owner ruled the four questions on 17 Nov 2026. Both cache workflows pass the rulings as the knobs' DEFAULTS
(`${{ vars.X || '<ruling>' }}`): KPC_LR_STALE_DAYS=180, KPC_LR_DYING=full, KPC_LR_CHANGED_READ=whole, KPC_LR_WHO=keeper+hand.
A repo variable still overrides each one. The wire stays OFF: by-hand button only, 'from_requests' unticked by default.
This script itself has no defaults: a knob that reaches it empty counts as unset (the safe behaviour, nothing extra fetched).
  KPC_LR_STALE_DAYS    R-LR1  live default 180. A whole number of days N: an area of this job whose saved copy on the release
                              is older than N days is re-read even with no request (an ETag that never moves). 'never' or
                              unset: no staleness re-read.
  KPC_LR_DYING         R-LR2  live default 'full'. A row marked dying (dying: true, or moved holds 'gone' / 'retiring'):
                              'full'  = the area gets ONE full-detail save (~1 m, kpc_layer_full_save.sh) as the separate
                                        release asset full-<area>.json.gz, uploaded once and never replaced; the ~110 m copy is
                                        left as it is. An area that already has its full save, or when the release asset list
                                        could not be read, is held.
                              'saved' = served like any other row (the ~110 m saved copy is the permanent record).
                              Unset: held (our last copy is never touched).
  KPC_LR_CHANGED_READ  R-LR3  live default 'whole' = a changed layer's area is re-read whole by the old bot;
                              'records' = held: a re-read of only the changed record ids needs a key-script change (rules hash).
                              Unset: every changed-layer row is held.
  KPC_LR_WHO           R-LR4  live default 'keeper+hand'. Whose rows may be served: only the keeper's own walk ('keeper'), or also a row added by
                              hand (by: chat / report / hand / owner). Unset: only the keeper's rows (a hand row is held).
A knob with any other value counts as unset (and says so).
"""
import argparse, datetime, json, os, pathlib, re, sys

FORMAT = 1
KEEPER = 'keeper'
HAND = {'chat', 'report', 'hand', 'owner'}
MOVED_OK = {'etag', 'lasteditdate', 'last_modified', 'count', 'gone', 'retiring'}
DYING_WORDS = {'gone', 'retiring'}
NEVER_SOURCE = re.compile(r'wdpa|protected[ _-]?planet|world[ _-]?database[ _-]?of[ _-]?protected|unep-?wcmc', re.I)   # WDPA / Protected Planet is never a source
US_RE, CA_RE, W_RE = re.compile(r'^US-([A-Z]{2})$'), re.compile(r'^CA-([A-Z]{2}|ALL)$'), re.compile(r'^W-([A-Z]{2})$')
KNOBS = {'R-LR1': 'KPC_LR_STALE_DAYS', 'R-LR2': 'KPC_LR_DYING', 'R-LR3': 'KPC_LR_CHANGED_READ', 'R-LR4': 'KPC_LR_WHO'}
CHOICES = {'KPC_LR_DYING': {'saved', 'full'}, 'KPC_LR_CHANGED_READ': {'whole', 'records'}, 'KPC_LR_WHO': {'keeper', 'keeper+hand'}}


def knobs(env=None):
    """{var: value or None}; a value that is not one of the ruled choices counts as unset (None), with a note."""
    env = os.environ if env is None else env
    out, notes = {}, []
    for rule, var in KNOBS.items():
        v = (env.get(var) or '').strip().lower()
        if not v: out[var] = None; continue
        if var == 'KPC_LR_STALE_DAYS':
            if v == 'never' or (v.isdigit() and int(v) > 0): out[var] = v
            else: out[var] = None; notes.append(f'{rule} {var}: {v!r} is not a whole number of days or never: counted as unset')
        elif v in CHOICES[var]: out[var] = v
        else: out[var] = None; notes.append(f'{rule} {var}: {v!r} is not one of {sorted(CHOICES[var])}: counted as unset')
    return out, notes


def area_unit(area, job, known):
    """The cache job's own save unit for an area ('KY' for US-KY, 'JP' for W-JP, 'CA' for any CA-..), or None if not this job's."""
    a = str(area or '').strip().upper()
    if job == 'us':
        m = US_RE.match(a)
        return m.group(1) if m and (not known or m.group(1) in known) else None
    if CA_RE.match(a): return 'CA'
    m = W_RE.match(a)
    return m.group(1) if m else None


def read_requests(path):
    """(doc, state): state 'none' (no file), 'unreadable' (bad JSON / wrong format), 'found'."""
    p = pathlib.Path(path) if path else None
    if p is None or not p.is_file(): return None, 'none'
    try: doc = json.loads(p.read_text(encoding='utf-8'))
    except Exception: return None, 'unreadable'  # noqa: BLE001
    if not isinstance(doc, dict) or doc.get('format') != FORMAT or not isinstance(doc.get('requests', []), list): return None, 'unreadable'
    return doc, 'found'


def _rows(doc, key):
    v = (doc or {}).get(key) or []
    return [r for r in v if isinstance(r, dict)] if isinstance(v, list) else []


def _date_ok(s):
    try: datetime.date.fromisoformat(str(s)[:10]); return True
    except ValueError: return False


def plan(doc, state, job, want=(), known=(), asset_dates=None, env=None, today=None):
    """The receipt (dict). receipt['fetch'] = the sorted save units to re-read. Pure: no file, no network."""
    k, notes = knobs(env)
    want, known = {w.upper() for w in want}, {x.upper() for x in known}
    today = today or datetime.datetime.now(datetime.timezone.utc).date()
    rows = _rows(doc, 'requests')
    rc = {'job': job, 'file': state, 'requests_read': len(rows), 'for_this_job': 0, 'served': 0, 'held': {}, 'refused': {},
          'fetch': [], 'full_save': [], 'stale': [], 'unknown_layers': {}, 'unknown_areas': [], 'unchanged_areas': [],
          'knobs': {r: (k[v] or 'unset') for r, v in KNOBS.items()}, 'notes': notes}
    if state == 'unreadable': rc['notes'].append('the request file could not be read (bad JSON or not format 1): nothing is fetched')

    def hold(why): rc['held'][why] = rc['held'].get(why, 0) + 1
    def refuse(why): rc['refused'][why] = rc['refused'].get(why, 0) + 1
    fetch, asked, full = set(), set(), set()
    names = set(asset_dates) if isinstance(asset_dates, dict) else None   # the release's asset names (None = the list was not read)
    for r in rows:
        moved = r.get('moved')
        moved = [str(m).strip().lower() for m in (moved if isinstance(moved, list) else [moved]) if str(m or '').strip()]
        if NEVER_SOURCE.search(str(r.get('layer') or '')) or NEVER_SOURCE.search(str(r.get('area') or '')):
            refuse('WDPA / Protected Planet is never a source'); continue
        if not str(r.get('layer') or '').strip() or not moved or not set(moved) <= MOVED_OK or not _date_ok(r.get('date')) \
                or not (US_RE.match(str(r.get('area') or '').upper()) or CA_RE.match(str(r.get('area') or '').upper()) or W_RE.match(str(r.get('area') or '').upper())):
            refuse('row not in the request format'); continue
        u = area_unit(r.get('area'), job, known)
        if u is None:
            if job == 'us' and US_RE.match(str(r['area']).upper()):   # a US area this job does not save (Kentucky has its own key)
                rc['for_this_job'] += 1; hold('a US area this job has no saved copy for (not in its state list)')
            continue   # else the other cache job's row
        rc['for_this_job'] += 1; asked.add(str(r['area']).upper())
        if want and u not in want: hold('not asked for this run (the states / countries box)'); continue
        by = str(r.get('by') or '').strip().lower()
        if by != KEEPER:
            if by in HAND and k['KPC_LR_WHO'] == 'keeper+hand': pass
            elif by in HAND: hold('R-LR4 (who may ask): a row added by hand' + (' is not allowed' if k['KPC_LR_WHO'] else ' waits for the ruling')); continue
            else: refuse('row not in the request format'); continue
        if r.get('dying') is True or set(moved) & DYING_WORDS:
            if k['KPC_LR_DYING'] == 'saved': pass
            elif k['KPC_LR_DYING'] == 'full':
                fn = f'full-{save_stem(u, job)}.json.gz'
                if names is None: hold('R-LR2 (dying layer): the release asset list was not read, so a full-detail save already made cannot be ruled out'); continue
                if fn in names: hold('R-LR2 (dying layer): its one full-detail save is already on the release; our copies are left as they are'); continue
                full.add(u); continue
            else: hold('R-LR2 (dying layer): waits for the ruling; our last copy is left as it is'); continue
        if k['KPC_LR_CHANGED_READ'] == 'whole': pass
        elif k['KPC_LR_CHANGED_READ'] == 'records': hold('R-LR3 (changed layer): a records-only re-read is not built (it needs a key-script change)'); continue
        else: hold('R-LR3 (changed layer: whole or part?) waits for the ruling'); continue
        rc['served'] += 1; fetch.add(u)
    # R-LR1: an area whose saved copy has not been refreshed for N days (an ETag that never moves)
    sd = k['KPC_LR_STALE_DAYS']
    if sd and sd != 'never' and isinstance(asset_dates, dict):
        for name, when in sorted(asset_dates.items()):
            m = re.match(r'^(US-([A-Z]{2})|W-([A-Z]{2})|CA-ALL)\.json\.gz$', str(name))
            if not m: continue
            area = m.group(1) if not m.group(1).startswith('CA') else 'CA-ALL'
            u = area_unit(area, job, known)
            if u is None or (want and u not in want): continue
            try: d = datetime.date.fromisoformat(str(when)[:10])
            except ValueError: continue
            if (today - d).days > int(sd): rc['stale'].append(area); fetch.add(u)
    # unknown is not unchanged: a layer with no first reading, or an area the keeper's file does not cover
    walked, unwalked = {}, {}
    for key, into in (('walked', walked), ('unwalked', unwalked)):
        for r in _rows(doc, key):
            a = str(r.get('area') or '').upper()
            if area_unit(a, job, known) is not None: into[a] = into.get(a, 0) + 1
    rc['unknown_layers'] = dict(sorted(unwalked.items()))
    if job == 'us': universe = {f'US-{s}' for s in known}
    else: universe = set()   # the world list is the workflow's; only areas seen in the file are judged
    seen = set(walked) | set(unwalked) | asked
    rc['unknown_areas'] = sorted(universe - seen) if state == 'found' else sorted(universe)
    rc['unchanged_areas'] = sorted(a for a in walked if a not in unwalked and a not in asked) if state == 'found' else []
    rc['fetch'] = sorted(fetch)
    rc['full_save'] = sorted(full)
    return rc


def save_stem(u, job):
    """The release file stem of a save unit: 'TN' -> US-TN (us job), 'JP' -> W-JP, 'CA' -> CA-ALL (world job)."""
    if job == 'us': return f'US-{u}'
    return 'CA-ALL' if u == 'CA' else f'W-{u}'


def summary_md(rc):
    held = sum(rc['held'].values()); ref = sum(rc['refused'].values()); unk = sum(rc['unknown_layers'].values())
    L = [f"### Layer requests ({rc['job']})", '',
         f"- request file: **{rc['file']}**; rows read: **{rc['requests_read']}** (for this job: {rc['for_this_job']})",
         f"- served: **{rc['served']}**; held: **{held}**; refused: **{ref}**",
         f"- areas to re-read: **{len(rc['fetch'])}** ({' '.join(rc['fetch']) or 'none: nothing is fetched'})"]
    if rc['full_save']: L.append(f"- R-LR2 one full-detail save before the layer goes away: {' '.join(save_stem(u, rc['job']) for u in rc['full_save'])}")
    if rc['stale']: L.append(f"- R-LR1 stale copies re-read: {' '.join(rc['stale'])}")
    for why, n in sorted(rc['held'].items()): L.append(f'- held {n}: {why}')
    for why, n in sorted(rc['refused'].items()): L.append(f'- refused {n}: {why}')
    L.append(f"- layers never walked by the keeper (UNKNOWN, not unchanged): **{unk}**" + (' (' + ', '.join(f'{a} {n}' for a, n in rc['unknown_layers'].items()) + ')' if unk else ''))
    if rc['unknown_areas']: L.append(f"- areas the keeper's file does not cover (UNKNOWN): {len(rc['unknown_areas'])}")
    L.append('- rulings: ' + ', '.join(f'{r} {v}' for r, v in rc['knobs'].items()))
    for n in rc['notes']: L.append(f'- note: {n}')
    return '\n'.join(L) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0]); sp = ap.add_subparsers(dest='cmd', required=True)
    p = sp.add_parser('plan'); p.add_argument('--requests', default=''); p.add_argument('--job', choices=('us', 'world'), required=True)
    p.add_argument('--want', default=''); p.add_argument('--known', default=''); p.add_argument('--asset-dates')
    p.add_argument('--receipt'); p.add_argument('--summary'); p.add_argument('--output-key', default=None); p.add_argument('--group', type=int, default=5)
    a = ap.parse_args(argv)
    doc, state = read_requests(a.requests)
    dates = None
    if a.asset_dates:
        try:
            d = json.loads(pathlib.Path(a.asset_dates).read_text(encoding='utf-8'))
            dates = {x.get('name'): x.get('updatedAt') for x in d} if isinstance(d, list) else d
        except Exception: dates = None  # noqa: BLE001
    rc = plan(doc, state, a.job, a.want.upper().replace(',', ' ').split(), a.known.upper().replace(',', ' ').split(), dates)
    if a.receipt: pathlib.Path(a.receipt).write_text(json.dumps(rc, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    md = summary_md(rc)
    if a.summary:
        with open(a.summary, 'a', encoding='utf-8') as f: f.write(md)
    sys.stderr.write(md)
    if a.job == 'us':
        out = [' '.join(rc['fetch'][i:i + a.group]) for i in range(0, len(rc['fetch']), a.group)]
        key = a.output_key or 'groups'
    else:
        out = [c for c in rc['fetch'] if c != 'CA'] + (['CA'] if 'CA' in rc['fetch'] else [])   # CA stays last, as in the full list
        key = a.output_key or 'list'
    print(f'{key}=' + json.dumps(out))
    full = rc['full_save'] if a.job == 'us' else [c for c in rc['full_save'] if c != 'CA'] + (['CA'] if 'CA' in rc['full_save'] else [])
    print('full=' + json.dumps(full))
    return 0


if __name__ == '__main__':
    sys.exit(main())
