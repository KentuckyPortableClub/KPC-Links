#!/usr/bin/env python3
"""2-fer outlines from the OUTLINE STORE instead of downloads (KPC owner, 2026-11-13). PREP ONLY: OFF by default, wired into nothing.

Why: the 2-fer bot runs out of memory in its download passes (Southeast, Great Lakes). Owner decision 'one door in': bots stop
downloading boundaries; a park the store does not have is FLAGGED, and only the store filler fetches. This module reads the store,
hands kpc_fers.py the same {ref: [rings per record]} it gets from download() today, and never asks a map server for anything.

NOT a rule file (kpc_key_freeze.NOT_RULES): nothing calls it yet, so no 2-fer answer can change and no rules hash moves. The
switch-over PR adds the hook line to kpc_fers.py and moves this file into the 2-fer RULE_FILES (one hash move, declared then).

Switch: KPC_FERS_FROM_STORE = on | off (default off; anything but 1 / on / yes / true is off).
  off  install() does nothing and returns False: kpc_fers.py runs exactly as today.
  on   install(kpc_fers) replaces, for that one process:
         download()   -> store_download(): the store's outline of every record the key joins, or the park is held (flagged);
         saved_us()   -> {} (the national saved key copy, about 2.4 GB in memory, is not loaded);
         saved_ca()   -> the store, for Canadian parks;
         live_load()  -> nothing (the bot's own saved-live copy is not read or written: no second door).
       US + Canada (REGION na) only: the Kentucky run (own files) and the world run (owner decision: world 2-fers wait) refuse.
Other settings: KPC_FERS_STORE_DIR (default 'store': per-area 'index-<AREA>.json' or one 'index.json', plus the area files the
index names), KPC_FERS_STORE_MAX_DAYS (default 45: an older area is stale = flagged, never downloaded).

Store format 1 (the outline store tool's kpc_store_read.py): one gzip member per park, the index holds each park's byte offset
and length, so one park is read without unpacking the area; rings are integer micro-degrees, first point absolute, then
differences. A record may carry "rings": null + "same_geometry_as": <key> (same land under two layer ids, stored once).

What the store gives, record by record, exactly as download() would after its own read-time rules:
  - only the record ids the KEY joins for the park (the key decides membership; extra store records are ignored);
  - a record marked use=false (easement, closed, proclamation) is left out and listed (download's pad_use / LEFT);
  - rings of 2 points or fewer are dropped (esri_rings); the park's own part boxes are applied (clip, rule B12);
  - a record that looks WDPA / Protected Planet derived is refused: the park is held (WDPA never feeds 2-fers);
  - a missing record, a park not in the store, a missing or stale area store: the park is HELD with the reason (never half a
    park, never a download). The list goes to data/fers/store-missing-<tag>.json for the store filler.
Point circles (100 ft around the agency's official point, data/point-circles.json) and picture traces stay exactly as today:
kpc_fers.py makes them itself (pc_ring / the approximate outlines), never from a download and never from this module.

Command line (no network in any of them):
  kpc_fers_store.py check <store_dir> <AREA> [<AREA> ...]   read + verify every park; points, memory estimate, age
  kpc_fers_store.py diff --old <file> --new <file> [--out <stem>]   the reviewed change list for one area (ids and names only)
  kpc_fers_store.py run                                     KPC_FERS_FROM_STORE=on: install, then kpc_fers.main() (same env as kpc_fers.py)
"""
import array, atexit, collections, datetime, gzip, hashlib, json, math, os, pathlib, re, sys

FORMAT = 1
SCALE = 10 ** 6
SWITCH = 'KPC_FERS_FROM_STORE'
NESTED_BYTES_PER_POINT = 132   # measured: an outline held as kpc_fers.py holds it (lists of [lon, lat] floats), tracemalloc
PACKED_BYTES_PER_POINT = 9     # measured: the store's own gzip member per park, kept as bytes (geometry + its metadata)
WDPA_RX = re.compile(r'wdpa|protectedplanet|protected.?planet|unep-?wcmc|world_database_of_protected', re.I)   # = kpc_fers.WDPA_RX
STORE_ON = False   # set by the switch-over hook in kpc_fers.main() (True only when install() switched this process on)
FLAGS = {}   # ref -> why the park is held (missing from the store, stale, a record missing, WDPA ...): for the store filler


def mode(env=None):
    v = str((os.environ if env is None else env).get(SWITCH) or '').strip().lower()
    return 'on' if v in ('1', 'on', 'yes', 'true') else 'off'


class StoreError(Exception):
    pass


# ------------------------------------------------------------------ format 1 codec
def ring_abs(enc):
    """flat delta list -> flat absolute integer list [x0, y0, x1, y1, ...]"""
    out = list(enc)
    for i in range(2, len(out) - 1, 2):
        out[i] += out[i - 2]; out[i + 1] += out[i - 1]
    return out


def ring_floats(enc):
    a = ring_abs(enc)
    return [[a[i] / SCALE, a[i + 1] / SCALE] for i in range(0, len(a) - 1, 2)]


def enc_rings(rec, park):
    if rec.get('rings') is None and rec.get('same_geometry_as'):
        for r in park.get('records') or []:
            if r.get('key') == rec['same_geometry_as'] and r.get('rings') is not None: return r['rings']
        raise StoreError(f"{park.get('ref')}: record {rec.get('key')} names a same_geometry_as record the park does not have")
    return rec.get('rings') or []


def geometry_sha256(rings):
    canon = json.dumps([[[a[i], a[i + 1]] for i in range(0, len(a) - 1, 2)] for a in (ring_abs(e) for e in rings)], separators=(',', ':'))
    return hashlib.sha256(canon.encode('ascii')).hexdigest()


def _member(raw):
    txt = gzip.decompress(raw).decode('utf-8').strip()
    if txt.startswith(','): txt = txt[1:].strip()
    if txt.endswith(','): txt = txt[:-1].strip()
    return json.loads(txt)


def wdpa_record(rec):
    """True when a stored record looks WDPA / Protected Planet derived (the same words kpc_fers.is_wdpa_outline looks for)."""
    txt = ' '.join(str(rec.get(k) or '') for k in ('layer', 'layer_url', 'agency_label', 'licence', 'licence_from', 'source', 'source_detail', 'record_name'))
    return bool(WDPA_RX.search(txt))


# ------------------------------------------------------------------ one area of the store
class AreaStore:
    """The index of one area plus its file(s). Parks are read one at a time by offset; with hold=True the packed bytes of every
    park are kept in memory (about 9 bytes per point) so the area file is read once."""

    def __init__(self, store_dir, area, hold=False):
        d = pathlib.Path(store_dir)
        idx = None
        for p in (d / f'index-{area}.json', d / 'index.json'):
            if p.is_file():
                j = json.loads(p.read_text(encoding='utf-8'))
                if j.get('area') == area or any((e.get('file') or '').startswith(area + '.') for e in (j.get('parks') or {}).values()):
                    idx = j; break
        if idx is None: raise StoreError(f'no outline store index for {area} in {d}')
        if int(idx.get('format') or 0) != FORMAT: raise StoreError(f'{area}: store format {idx.get("format")!r}, this reader reads {FORMAT}')
        self.dir, self.area, self.idx = d, area, idx
        self.entries = {r: e for r, e in (idx.get('parks') or {}).items() if (e.get('file') or '').startswith(area + '.')} or dict(idx.get('parks') or {})
        for f in {e['file'] for e in self.entries.values()}:
            if not (d / f).is_file(): raise StoreError(f'{area}: the index names {f}, which is not in {d}')
        self.made = str(idx.get('made') or (next(iter((idx.get('files') or {}).values()), {}) or {}).get('date') or '')[:10]
        self.packed = {r: self._read(r) for r in self.entries} if hold else {}

    def _read(self, ref):
        e = self.entries[ref]
        with open(self.dir / e['file'], 'rb') as f:
            f.seek(int(e['o'])); raw = f.read(int(e['n']))
        if len(raw) != int(e['n']): raise StoreError(f'{ref}: the store file is shorter than the index says')
        return raw

    def age_days(self, today):
        try: return (datetime.date.fromisoformat(today[:10]) - datetime.date.fromisoformat(self.made)).days
        except ValueError: return None

    def points(self, refs=None):
        return sum(int(self.entries[r].get('points') or 0) for r in (self.entries if refs is None else refs) if r in self.entries)

    def park(self, ref, check=True):
        """One park, verified: every record's geometry checksum and point count are recomputed (never a silently wrong line)."""
        if ref not in self.entries: return None
        p = _member(self.packed.get(ref) or self._read(ref))
        if p.get('ref') != ref: raise StoreError(f'{ref}: the index points at {p.get("ref")!r}')
        if check:
            for r in p.get('records') or []:
                rs = enc_rings(r, p)
                if geometry_sha256(rs) != r.get('sha256'): raise StoreError(f"{ref}: record {r.get('key')} checksum does not match")
                if sum(len(x) // 2 for x in rs) != int(r.get('points') or 0): raise StoreError(f"{ref}: record {r.get('key')} point count does not match")
            fp = hashlib.sha256('|'.join(str(r.get('sha256')) for r in p.get('records') or []).encode()).hexdigest()
            if self.entries[ref].get('fp') and fp != self.entries[ref]['fp']: raise StoreError(f'{ref}: park fingerprint differs from the index')
        return p


class Store:
    """Every area the run needs, opened on first use; an area that cannot be opened is remembered with its reason."""

    def __init__(self, store_dir, max_days=45, today=None, hold=False):
        self.dir, self.max_days, self.hold = pathlib.Path(store_dir), max_days, hold
        self.today = today or datetime.date.today().isoformat()
        self.areas, self.why = {}, {}

    def area(self, area):
        if area in self.areas or area in self.why: return self.areas.get(area)
        try:
            a = AreaStore(self.dir, area, self.hold)
            age = a.age_days(self.today)
            if age is None: self.why[area] = f'the outline store for {area} has no build date'; return None
            if age > self.max_days: self.why[area] = f'the outline store for {area} is {age} days old (limit {self.max_days})'; return None
            self.areas[area] = a; return a
        except (StoreError, OSError, ValueError) as e:
            self.why[area] = f'the outline store for {area} cannot be read ({str(e)[:120]})'; return None

    def groups_for(self, ref, area, ids, clip=None):
        """(groups, left, why): the park's outline as download() returns it (one group of rings per joined record, in the key's
        order), the records left out by their use flag, and why the park is held ('' when it is not)."""
        a = self.area(area)
        if a is None: return None, [], self.why[area]
        try: p = a.park(ref)
        except StoreError as e: return None, [], f'{ref} in the outline store failed its check ({str(e)[:100]})'
        if p is None: return None, [], f'{ref} is not in the outline store for {area}'
        if p.get('circle') or p.get('grade') == 'point-circle':
            return None, [], f'{ref} has only a point circle in the store (the 2-fer bot makes its own circle)'
        by = {str(r.get('key')): r for r in p.get('records') or []}
        groups, left = [], []
        for rid in ids:
            r = by.get(str(rid))
            if r is None: return None, [], f'the outline store has no record {rid} for {ref} (the key joins it)'
            if wdpa_record(r): return None, [], f'record {rid} of {ref} looks WDPA / Protected Planet derived: never a 2-fer source'
            if r.get('use') is False:
                left.append(f"{r.get('record_name') or rid}: {r.get('use_why') or 'not public land (store use flag)'}"); continue
            rs = [ring_floats(e) for e in enc_rings(r, p)]
            rs = [x for x in rs if len(x) > 2]
            if clip is not None: rs = clip(rid, rs)
            if rs: groups.append(rs)
        if not groups: return None, left, (f'every record of {ref} is left out by its use flag' if left else f'{ref} has no rings in the store')
        return groups, left, ''

    def read_date(self, ref, area):
        a = self.areas.get(area)
        return str((a.entries.get(ref) or {}).get('date') or a.made) if a else ''


# ------------------------------------------------------------------ compact holding (for the switch-over: packed + a small unpacked cache)
class LazyOutlines(collections.abc.Mapping):
    """{ref: groups} that keeps every park packed and unpacks on use, holding at most `budget` unpacked points (least recently
    used out first; the pair loop runs in map order, so neighbours stay). kpc_fers.find_spots can use it once its CURG copy is a
    reference (switch-over PR): memory = packed store + the budget, instead of every outline as Python lists."""

    def __init__(self, loader, refs, budget=2_000_000):
        self.load, self.refs, self.budget = loader, list(refs), int(budget)
        self.cache, self.pts, self.unpacks = collections.OrderedDict(), 0, 0

    def __getitem__(self, ref):
        if ref in self.cache:
            self.cache.move_to_end(ref); return self.cache[ref][0]
        if ref not in self._set(): raise KeyError(ref)
        g = self.load(ref); self.unpacks += 1
        n = sum(len(r) for gr in g for r in gr)
        self.cache[ref] = (g, n); self.pts += n
        while self.pts > self.budget and len(self.cache) > 2:
            _, (_, m) = self.cache.popitem(last=False); self.pts -= m
        return g

    def _set(self):
        if not hasattr(self, '_s'): self._s = set(self.refs)
        return self._s

    def __iter__(self): return iter(self.refs)

    def __len__(self): return len(self.refs)

    def __contains__(self, ref): return ref in self._set()


def compact_rings(rings):
    """The store's own delta integers as array('i'), one per ring (about 11.5 bytes per point held, against 132 as lists)."""
    return [array.array('i', e) for e in rings]


def grid_pairs(boxes, cell=0.5):
    """Pairs whose boxes touch, found on a grid (never every pair): the same test as kpc_fers.grid_pairs."""
    cells = {}
    for ref, b in boxes.items():
        for i in range(int(math.floor(b[0] / cell)), int(math.floor(b[2] / cell)) + 1):
            for j in range(int(math.floor(b[1] / cell)), int(math.floor(b[3] / cell)) + 1):
                cells.setdefault((i, j), []).append(ref)
    pairs = set()
    for refs in cells.values():
        for x in range(len(refs)):
            a = boxes[refs[x]]
            for y in range(x + 1, len(refs)):
                c = boxes[refs[y]]
                if a[0] <= c[2] and c[0] <= a[2] and a[1] <= c[3] and c[1] <= a[3]: pairs.add(tuple(sorted((refs[x], refs[y]))))
    return pairs


def memory_estimate(points, held_unpacked=2_000_000):
    """Bytes for outlines: (today's way: every point as lists, the packed way: packed area + the unpacked budget)."""
    return points * NESTED_BYTES_PER_POINT, points * PACKED_BYTES_PER_POINT + min(points, held_unpacked) * NESTED_BYTES_PER_POINT


# ------------------------------------------------------------------ the kpc_fers.py side
def store_download(KF, store, parks, refs):
    """download()'s contract ({ref: groups}, bad) from the store. Never a network request. Circles and picture traces exactly as
    kpc_fers.download makes them; a held park goes into KF.MISSING_SAVED with its reason, so kpc_fers.py lists it as held (the
    existing 'known reason' path) and never counts it as an agency map that did not answer."""
    _pc = {r: [[KF.pc_ring(*KF.PC[r]['pt'])]] for r in refs if r in KF.PCT}
    _apx = {r: [parks[r]['rings']] for r in refs if (parks.get(r) or {}).get('rings') and (parks.get(r) or {}).get('approx') and not KF.has_official_outline(r, parks)}
    got, bad = {}, set()
    for ref in [r for r in refs if r not in KF.PCT and r not in _apx]:
        p = parks[ref]
        if 'm' in p:   # a world park: not this module's (world 2-fers wait)
            bad.add(ref); FLAGS[ref] = 'world park: not read from the outline store'; KF.MISSING_SAVED[ref] = 'the outline store (world parks are not read from it)'; continue
        gs, left, why = store.groups_for(ref, p['st'], p['ids'], clip=lambda rid, rs, _r=ref: KF.clip(_r, rid, rs))
        if left: KF.LEFT.setdefault(ref, []).extend(left)
        if why:
            bad.add(ref); FLAGS[ref] = why
            KF.MISSING_SAVED[ref] = f'the outline store ({why}; flagged for the store filler)'
            continue
        got[ref] = gs
        KF.MAPDATE[ref] = f'outline store (read from the agency {store.read_date(ref, p["st"])})'
    for r in [r for r in KF.MISSING_SAVED if r in got]: KF.MISSING_SAVED.pop(r)
    got.update(_pc); got.update(_apx)
    KF.inject_apx_geom(got, parks)
    return got, bad


def install(KF, env=None, store=None):
    """Switch the 2-fer bot (the imported kpc_fers module) to the store for this process. False (nothing changed) when the switch
    is off, or for the Kentucky / world runs."""
    env = os.environ if env is None else env
    if mode(env) != 'on': return False
    if getattr(KF, 'REGION', 'na') != 'na':
        print(f'::notice title=2-fer outline store::{SWITCH} is on, but the {KF.REGION} run keeps its own outlines (US + Canada only)', flush=True)
        return False
    st = store or Store(env.get('KPC_FERS_STORE_DIR') or 'store', int(env.get('KPC_FERS_STORE_MAX_DAYS') or 45), hold=False)

    def download(parks, refs, det, prec):   # det / prec are ignored: the store's detail (about 2 m, 6 decimals) in every pass
        return store_download(KF, st, parks, refs)

    def saved_ca(parks):
        got, _ = store_download(KF, st, {r: p for r, p in parks.items() if str(p.get('st', '')).startswith('CA-')}, [r for r, p in parks.items() if str(p.get('st', '')).startswith('CA-')])
        return got

    def live_load(area):
        KF.LIVE_FILE = None; KF.LIVE = {}
        return KF.LIVE

    KF.download, KF.saved_us, KF.saved_ca, KF.live_load = download, (lambda parks: {}), saved_ca, live_load
    KF.STORE = st

    out_dir = pathlib.Path(getattr(KF, 'OUT', 'data/fers')).resolve()   # fixed now: a later chdir never moves the list

    def _flags():
        if not FLAGS and not st.why: return
        tag = getattr(KF, 'area_name', lambda: 'run')()
        out = out_dir / f'store-missing-{tag}.json'
        try:
            out.write_text(json.dumps({'about': 'Parks the 2-fer bot held because the outline store does not have them (one door in: only the store filler fetches).',
                                       'areas': dict(sorted(st.why.items())), 'parks': dict(sorted(FLAGS.items()))}, indent=1, ensure_ascii=False), encoding='utf-8')
        except OSError: pass
    atexit.register(_flags)
    print(f"::notice title=2-fer outline store::{SWITCH}=on: outlines from {st.dir} (no boundary downloads; a missing park is held and flagged)", flush=True)
    return True


# ------------------------------------------------------------------ the reviewed change list (old answers stay until it is signed)
def _rows(doc):
    out = {}
    for s in (doc or {}).get('spots') or []:
        if str(s.get('status') or '').startswith(('dropped', 'merged')): continue
        out.setdefault((tuple(sorted(s.get('refs') or [])), s.get('kind')), []).append(s)
    return out


def _km(a, b):
    return math.hypot((a[0] - b[0]) * 110.574, (a[1] - b[1]) * 111.32 * math.cos(math.radians(a[0])))


def diff_rows(old, new, moved_km=0.2):
    """Live rows (not dropped / merged) of one area: same / new / gone / moved (closest spot centre over moved_km) / status changed.
    Ids, names, kinds and statuses only: no shapes."""
    o, n = _rows(old), _rows(new)
    names = {}
    for d in (old, new):
        for s in (d or {}).get('spots') or []:
            for r, nm in (s.get('names') or {}).items(): names.setdefault(r, nm)
    def row(k, extra=None): return {'refs': list(k[0]), 'kind': k[1], 'names': [names.get(r, '') for r in k[0]], **(extra or {})}
    res = {'same': [], 'new': [], 'gone': [], 'moved': [], 'status_changed': []}
    for k in sorted(set(o) | set(n)):
        if k in o and k not in n: res['gone'].append(row(k, {'old_status': o[k][0].get('status')})); continue
        if k in n and k not in o: res['new'].append(row(k, {'new_status': n[k][0].get('status')})); continue
        res['same'].append(row(k))
        oc = [s['center'] for s in o[k] if s.get('center')]; nc = [s['center'] for s in n[k] if s.get('center')]
        if oc and nc:
            d = max(min(_km(a, b) for b in nc) for a in oc)
            if d > moved_km: res['moved'].append(row(k, {'km': round(d, 2)}))
        so, sn = sorted(str(s.get('status')) for s in o[k]), sorted(str(s.get('status')) for s in n[k])
        if so != sn: res['status_changed'].append(row(k, {'old_status': so, 'new_status': sn}))
    res['counts'] = {k: len(v) for k, v in res.items() if isinstance(v, list)}
    return res


def _load(p):
    p = pathlib.Path(p)
    op = gzip.open if p.suffix == '.gz' else open
    with op(p, 'rt', encoding='utf-8') as f: return json.load(f)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ('-h', '--help'): print(__doc__); return 0
    cmd = argv.pop(0)
    if cmd == 'check':
        if len(argv) < 2: print('usage: kpc_fers_store.py check <store_dir> <AREA> [...]'); return 2
        st = Store(argv[0], hold=False); rc = 0
        for area in argv[1:]:
            a = st.area(area)
            if a is None: print(f'{area}: HELD: {st.why[area]}'); rc = 1; continue
            bad = []
            for ref in a.entries:
                try: a.park(ref)
                except StoreError as e: bad.append(str(e))
            pts = a.points(); now, packed = memory_estimate(pts)
            print(f'{area}: {len(a.entries)} parks, {pts} points, built {a.made} ({a.age_days(st.today)} days old); outlines held as lists '
                  f'about {now / 1e6:.0f} MB, packed + 2 M unpacked points about {packed / 1e6:.0f} MB; checks: {"PASS" if not bad else "FAIL " + bad[0]}')
            rc = rc or (1 if bad else 0)
        return rc
    if cmd == 'diff':
        a = {argv[i]: argv[i + 1] for i in range(0, len(argv) - 1, 2)}
        if '--old' not in a or '--new' not in a: print('usage: kpc_fers_store.py diff --old FILE --new FILE [--out STEM]'); return 2
        d = diff_rows(_load(a['--old']), _load(a['--new']))
        if a.get('--out'):
            stem = pathlib.Path(a['--out'])
            stem.with_suffix('.json').write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding='utf-8')
            md = ['# 2-fer change list (store outlines against today\'s answers)', '', 'Nothing is published until a person signs this list; the old answers stay.', '',
                  ' | '.join(f'{k}: {v}' for k, v in d['counts'].items()), '']
            for k in ('new', 'gone', 'moved', 'status_changed'):
                md += [f'## {k} ({len(d[k])})', ''] + [f"- {' + '.join(r['refs'])} ({' / '.join(x for x in r['names'] if x)}) {r['kind']}"
                                                       + (f" {r.get('km')} km" if 'km' in r else '') for r in d[k]] + ['']
            stem.with_suffix('.md').write_text('\n'.join(md), encoding='utf-8')
        print(json.dumps(d['counts']))
        return 0
    if cmd == 'run':
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import kpc_fers as KF
        install(KF)
        KF.main()
        return 0
    print(f'unknown command {cmd!r}'); return 2


if __name__ == '__main__':
    sys.exit(main())
