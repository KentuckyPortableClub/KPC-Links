#!/usr/bin/env python3
"""2-fer outlines from the OUTLINE STORE instead of downloads (KPC owner, 2026-11-13). PREP ONLY: OFF by default, wired into nothing.

Why: the 2-fer bot runs out of memory in its download passes (Southeast, Great Lakes). Owner decision 'one door in': bots stop
downloading boundaries; a park the store does not have is HELD and listed, and only the store filler fetches.

NOT a rule file (kpc_key_freeze.NOT_RULES): nothing calls it yet, so no 2-fer answer can change and no rules hash moves. The
switch-over PR adds the hook to kpc_fers.py and moves this file into the 2-fer RULE_FILES (one declared hash move).

Switch: KPC_FERS_FROM_STORE = on | off (default off; anything but 1 / on / yes / true is off). Off: install() does nothing and
returns False. On, US + Canada runs (REGION na) only: for one process,
  - before anything is read, the area gate: every member state needs a readable, fresh store (else exit 87, nothing saved) and
    the run must fit its memory limit by the store index's own point counts (else exit 88, nothing loaded); one row per area
    goes to data/fers/store-missing-<tag>.json either way;
  - download()  -> store_download(): verified record by record, kept PACKED (LazyOutlines: unpacked on use, a points budget);
  - saved_us()  -> only the Wild and Scenic corridor records (wsrc) of the saved key copy, nothing else (the whole national copy
                   is about 2.4 GB in memory); a corridor park is read from that saved copy until the store holds the corridors;
  - saved_ca()  -> the store; live_load() -> nothing (no second door);
  - pc_tag()    -> today's pc_tag, then: every live row of the previous file that this run did not make again comes back as a
                   row (held park: 'not sure: held: <why>'; otherwise 'dropped: not found again ...'), so no live pair vanishes
                   without a row; a row is tagged club_room_only when an outline it used is not publishable.
  Kentucky and world runs: install() returns False and the bot runs AS TODAY (downloads included): nothing here refuses them.
Settings: KPC_FERS_STORE_DIR (default 'store'), KPC_FERS_STORE_MAX_DAYS (45), KPC_FERS_STORE_KIND = public | private (default
public: a park with any record not marked publishable is held 'needs the private store'), KPC_FERS_STORE_LIMIT_MB (3000, the
whole process), KPC_FERS_STORE_BUDGET (2,000,000 unpacked points), KPC_FERS_STORE_NEIGHBOURS (1.5: border parks from other areas).

What the store gives, record by record, as download() would after its own read-time rules: only the record ids the KEY joins;
use=false records left out and listed; rings of 2 points or fewer dropped; the park's part boxes applied (clip, rule B12).
The park is HELD with its reason, never half a park and never a download, when: it is not in the store; a joined record is
missing; a joined record has no usable ring; any text of the record or park looks WDPA / Protected Planet derived; the area
store is missing, stale, of another format, or damaged (bad gzip, cut-off JSON, a bad index entry: every error is caught).
Point circles and picture traces are made by kpc_fers.py exactly as today.

Command line (no network in any of them):
  kpc_fers_store.py check <store_dir> <AREA> [...]          read + verify every park; points, memory estimate, age
  kpc_fers_store.py fit <store_dir> <AREA> [...]            the memory gate alone (exit 88 when it will not fit)
  kpc_fers_store.py diff --old FILE --new FILE [--out STEM] the reviewed change list (ids, names and statuses only)
  kpc_fers_store.py run                                     KPC_FERS_FROM_STORE=on only: install, then kpc_fers.main()
"""
import array, atexit, collections.abc, datetime, gzip, hashlib, json, math, os, pathlib, re, sys

FORMAT = 1
SCALE = 10 ** 6
SWITCH = 'KPC_FERS_FROM_STORE'
EXIT_NOT_READY, EXIT_WONT_FIT = 87, 88
LIST_BYTES_PER_POINT = 154     # measured (synthetic Southeast-sized area): an outline unpacked to lists, as kpc_fers.py holds it
PACKED_BYTES_PER_POINT = 9     # measured on the real NH store: the gzip piece per park kept as bytes (geometry + metadata)
RECORD_META_BYTES = 1200       # measured on NH: per-record bookkeeping (key, box, licence)
BOT_BASE_MB = 400              # measured: Python + numpy + cv2 + kpc_fers + pins + every key's parks + trail lines = 362 MB (Southeast run)
TILE_FLOOR_MB = 500            # water + ownership tiles kept near the pair in hand when the process is at its limit
WDPA_RX = re.compile(r'wdpa|protectedplanet|protected.?planet|unep-?wcmc|world_database_of_protected', re.I)   # = kpc_fers.WDPA_RX
STORE_ON = False   # set True by install() (the switch-over hook in kpc_fers.main() reads it)
FLAGS = {}         # ref -> why the park is held
PRIVATE = {}       # ref -> the licence classes of the records it used that are not publishable
AREA_ROWS = {}     # area -> {'verdict', 'why', 'points', 'estimate_mb', 'limit_mb'}


def mode(env=None):
    v = str((os.environ if env is None else env).get(SWITCH) or '').strip().lower()
    return 'on' if v in ('1', 'on', 'yes', 'true') else 'off'


class StoreError(Exception):
    pass


class StoreChanged(BaseException):
    """A park that passed its check failed when it was unpacked later (the file changed under the run). Not an Exception on
    purpose: kpc_fers.py's pair test catches Exception, and a missing outline must never become a silent 'no overlap'."""


# ------------------------------------------------------------------ format 1 codec
def ring_abs(enc):
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
        raise StoreError(f"record {rec.get('key')} names a same_geometry_as record the park does not have")
    return rec.get('rings') or []


def geometry_sha256(rings):
    canon = json.dumps([[[a[i], a[i + 1]] for i in range(0, len(a) - 1, 2)] for a in (ring_abs(e) for e in rings)], separators=(',', ':'))
    return hashlib.sha256(canon.encode('ascii')).hexdigest()


def _member(raw):
    txt = gzip.decompress(raw).decode('utf-8').strip()
    if txt.startswith(','): txt = txt[1:].strip()
    if txt.endswith(','): txt = txt[:-1].strip()
    p = json.loads(txt)
    if not isinstance(p, dict): raise StoreError('a park piece is not a JSON object')
    return p


def wdpa_text(obj, _depth=0):
    """True when ANY text VALUE of a record or park (attributes, owner, request, notes ... everything but the rings) looks WDPA
    derived. Field NAMES are not read: PAD-US carries a 'WDPA_Cd' cross-reference field on every record, which is not WDPA data."""
    if _depth > 8: return False
    if isinstance(obj, str): return bool(WDPA_RX.search(obj))
    if isinstance(obj, dict): return any(wdpa_text(v, _depth + 1) for k, v in obj.items() if k not in ('rings', 'records'))
    if isinstance(obj, (list, tuple)): return any(wdpa_text(v, _depth + 1) for v in obj[:200])
    return False


def _err(e): return f'{type(e).__name__}: {str(e)[:100]}'


# ------------------------------------------------------------------ one area of the store
class AreaStore:
    """The index of one area plus its file(s). Every damage is caught: the area (bad index) or the park (bad entry / piece) is
    held with a reason. Parks are read one at a time by offset."""

    def __init__(self, store_dir, area):
        d = pathlib.Path(store_dir)
        idx = None
        for p in (d / f'index-{area}.json', d / 'index.json'):
            if not p.is_file(): continue
            try: j = json.loads(p.read_text(encoding='utf-8'))
            except Exception as e: raise StoreError(f'index {p.name} cannot be read ({_err(e)})')  # noqa: BLE001
            if not isinstance(j, dict) or not isinstance(j.get('parks'), dict): raise StoreError(f'index {p.name} is not a store index')
            if j.get('area') == area or any(isinstance(e, dict) and str(e.get('file') or '').startswith(area + '.') for e in j['parks'].values()):
                idx = j; break
        if idx is None: raise StoreError(f'no outline store index for {area}')
        if str(idx.get('format')) != str(FORMAT): raise StoreError(f'store format {idx.get("format")!r}; this reader reads {FORMAT}')
        self.dir, self.area, self.idx = d, area, idx
        allp = idx['parks']
        mine = {r: e for r, e in allp.items() if isinstance(e, dict) and str(e.get('file') or '').startswith(area + '.')}
        self.entries, self.bad = {}, {}
        for r, e in (mine or allp).items():
            try:
                if not isinstance(e, dict): raise StoreError('index entry is not an object')
                o, n, f = int(e['o']), int(e['n']), str(e['file'])
                if o < 0 or n <= 0 or '/' in f or '\\' in f or f.startswith('.'): raise StoreError('bad offset, length or file name')
                if not (d / f).is_file(): raise StoreError(f'the index names {f}, which is not there')
                self.entries[r] = e
            except Exception as ex: self.bad[r] = f'index entry damaged ({_err(ex)})'  # noqa: BLE001
        if not self.entries: raise StoreError('no readable park in the index')
        files = idx.get('files') if isinstance(idx.get('files'), dict) else {}
        self.made = str(idx.get('made') or (next(iter(files.values()), {}) or {}).get('date') or '')[:10]

    def age_days(self, today):
        try: return (datetime.date.fromisoformat(today[:10]) - datetime.date.fromisoformat(self.made)).days
        except (TypeError, ValueError): return None

    def points(self, refs=None):
        def pt(e):
            try: return int(e.get('points') or 0)
            except (TypeError, ValueError): return 0
        return sum(pt(self.entries[r]) for r in (self.entries if refs is None else refs) if r in self.entries)

    def biggest(self, n=2):
        return sorted((self.points([r]) for r in self.entries), reverse=True)[:n]

    def park(self, ref):
        """One park, verified (checksums, point counts, fingerprint recomputed). StoreError for ANY damage."""
        if ref in self.bad: raise StoreError(self.bad[ref])
        if ref not in self.entries: return None
        e = self.entries[ref]
        try:
            with open(self.dir / e['file'], 'rb') as f:
                f.seek(int(e['o'])); raw = f.read(int(e['n']))
            if len(raw) != int(e['n']): raise StoreError('the store file is shorter than the index says')
            p = _member(raw)
            if p.get('ref') != ref: raise StoreError(f'the index points at {p.get("ref")!r}')
            for r in p.get('records') or []:
                rs = enc_rings(r, p)
                if geometry_sha256(rs) != r.get('sha256'): raise StoreError(f"record {r.get('key')} checksum does not match")
                if sum(len(x) // 2 for x in rs) != int(r.get('points') or 0): raise StoreError(f"record {r.get('key')} point count does not match")
            fp = hashlib.sha256('|'.join(str(r.get('sha256')) for r in p.get('records') or []).encode()).hexdigest()
            if e.get('fp') and fp != e['fp']: raise StoreError('park fingerprint differs from the index')
            return p
        except StoreError: raise
        except Exception as ex: raise StoreError(_err(ex))  # noqa: BLE001  bad gzip, cut-off JSON, wrong types ...


class Store:
    """Every area the run needs, opened on first use; an area that cannot be opened is remembered with its reason."""

    def __init__(self, store_dir, max_days=45, today=None, kind='public'):
        self.dir, self.max_days, self.kind = pathlib.Path(store_dir), int(max_days), (kind if kind in ('public', 'private') else 'public')
        self.today = today or datetime.date.today().isoformat()
        self.areas, self.why = {}, {}

    @classmethod
    def from_env(cls, env):
        return cls(env.get('KPC_FERS_STORE_DIR') or 'store', int(env.get('KPC_FERS_STORE_MAX_DAYS') or 45), kind=str(env.get('KPC_FERS_STORE_KIND') or 'public').strip().lower())

    def area(self, area):
        if area in self.areas or area in self.why: return self.areas.get(area)
        try:
            a = AreaStore(self.dir, area)
            age = a.age_days(self.today)
            if age is None: self.why[area] = f'the outline store for {area} has no build date'; return None
            if age > self.max_days: self.why[area] = f'the outline store for {area} is {age} days old (limit {self.max_days})'; return None
            self.areas[area] = a; return a
        except Exception as e:  # noqa: BLE001
            self.why[area] = f'the outline store for {area} cannot be read ({str(e)[:140]})'; return None

    def examine(self, ref, area, ids, clip=None, keep=False):
        """-> (groups or None, left, why, info). groups only with keep=True; info = {'points', 'box', 'private'}. Never raises."""
        try: return self._examine(ref, area, ids, clip, keep)
        except Exception as e:  # noqa: BLE001
            return None, [], f'{ref} in the outline store failed its check ({_err(e)})', {}

    def locate(self, ref, area):
        """The area store that holds ref: the key's own state first, then any other area store in the folder (a park the key
        files under one state can sit in a neighbour's store, e.g. a forest across a state line). (AreaStore, '') or (None, why)."""
        a = self.area(area)
        if a is not None and (ref in a.entries or ref in a.bad): return a, ''
        if not hasattr(self, '_names'):
            names = {p.name[6:-5] for p in self.dir.glob('index-*.json')}
            try:   # a combined index.json names its area(s) itself
                j = json.loads((self.dir / 'index.json').read_text(encoding='utf-8')) if (self.dir / 'index.json').is_file() else {}
                if isinstance(j, dict) and j.get('area'): names.add(str(j['area']))
            except Exception: pass  # noqa: BLE001
            self._names = sorted(names)
        for other in self._names:
            if other == area: continue
            b = self.area(other)
            if b is not None and (ref in b.entries or ref in b.bad): return b, ''
        if a is None: return None, self.why[area]
        return a, ''

    def _examine(self, ref, area, ids, clip, keep):
        a, why = self.locate(ref, area)
        if a is None: return None, [], why, {}
        try: p = a.park(ref)
        except StoreError as e: return None, [], f'{ref} in the outline store failed its check ({str(e)[:120]})', {}
        if p is None: return None, [], f'{ref} is not in the outline store for {area}', {}
        if p.get('circle') or p.get('grade') == 'point-circle':
            return None, [], f'{ref} has only a point circle in the store (the 2-fer bot makes its own circle)', {}
        if wdpa_text(p): return None, [], f'{ref}: the store park looks WDPA / Protected Planet derived: never a 2-fer source', {}
        by = {str(r.get('key')): r for r in p.get('records') or [] if isinstance(r, dict)}
        groups, left, private, pts, box = [], [], {}, 0, None
        for rid in ids:
            r = by.get(str(rid))
            if r is None: return None, [], f'the outline store has no record {rid} for {ref} (the key joins it)', {}
            if wdpa_text(r): return None, [], f'record {rid} of {ref} looks WDPA / Protected Planet derived: never a 2-fer source', {}
            if r.get('use') is False:
                left.append(f"{r.get('record_name') or rid}: {r.get('use_why') or 'not public land (store use flag)'}"); continue
            if r.get('publishable') is not True: private[str(rid)] = str(r.get('licence_class') or 'NOT RECORDED')
            rs = [ring_floats(e) for e in enc_rings(r, p)]
            rs = [x for x in rs if len(x) > 2]
            if clip is not None and rs: rs = clip(rid, rs)
            if not rs: return None, [], f'record {rid} of {ref} has no usable ring: half a park is not the park', {}
            for x in rs:
                xs = [q[0] for q in x]; ys = [q[1] for q in x]
                b = (min(xs), min(ys), max(xs), max(ys))
                box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
                pts += len(x)
            if keep: groups.append(rs)
        if box is None: return None, left, (f'every record of {ref} is left out by its use flag' if left else f'{ref} has no rings in the store'), {}
        if private and self.kind == 'public':
            return None, left, f'{ref} needs the private store (records not publishable: ' + ', '.join(f'{k} {v}' for k, v in sorted(private.items())[:4]) + ')', {}
        return (groups if keep else None), left, '', {'points': pts, 'box': box, 'private': private}

    def groups_for(self, ref, area, ids, clip=None):
        g, left, why, _ = self.examine(ref, area, ids, clip, keep=True)
        return g, left, why

    def read_date(self, ref, area):
        a = self.locate(ref, area)[0]
        return str((a.entries.get(ref) or {}).get('date') or a.made) if a else ''


# ------------------------------------------------------------------ compact holding
class LazyOutlines(collections.abc.MutableMapping):
    """{ref: groups} for the bot's passes: store parks stay packed and are unpacked on use, at most `budget` unpacked points kept
    (least recently used out first; pairs run in map order, so neighbours stay). Entries SET on it (circles, picture traces, a
    saved corridor) are kept as given. box(ref) needs no unpacking. A park that fails when unpacked raises StoreChanged."""

    def __init__(self, loader, refs, budget=2_000_000, boxes=None):
        self.load, self.lazy, self.budget = loader, dict.fromkeys(refs), int(budget)
        self.extra, self.cache, self.pts, self.unpacks, self.boxes = {}, collections.OrderedDict(), 0, 0, dict(boxes or {})

    def __getitem__(self, ref):
        if ref in self.extra: return self.extra[ref]
        if ref not in self.lazy: raise KeyError(ref)
        if ref in self.cache:
            self.cache.move_to_end(ref); return self.cache[ref][0]
        g = self.load(ref)
        if not g: raise StoreChanged(f'{ref}: its store outline passed its check but could not be unpacked now (the store changed during the run)')
        self.unpacks += 1
        n = sum(len(r) for gr in g for r in gr)
        self.cache[ref] = (g, n); self.pts += n
        while self.pts > self.budget and len(self.cache) > 2:
            _, (_, m) = self.cache.popitem(last=False); self.pts -= m
        return g

    def __setitem__(self, ref, v):
        self.extra[ref] = v; self.lazy.pop(ref, None)
        if ref in self.cache: self.pts -= self.cache.pop(ref)[1]

    def __delitem__(self, ref):
        if ref in self.extra: del self.extra[ref]
        elif ref in self.lazy:
            del self.lazy[ref]
            if ref in self.cache: self.pts -= self.cache.pop(ref)[1]
        else: raise KeyError(ref)

    def __iter__(self):
        yield from list(self.lazy)
        yield from list(self.extra)

    def __len__(self): return len(self.lazy) + len(self.extra)

    def __contains__(self, ref): return ref in self.lazy or ref in self.extra

    def box(self, ref): return self.boxes.get(ref)


def compact_rings(rings):
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


# ------------------------------------------------------------------ the memory gate ('refuse if it will not fit')
def estimate_mb(points, records, biggest_two, budget=2_000_000, lazy=True):
    """Whole-process memory of a run, from the index alone: the bot's own base + a tile floor + the packed store + per-record
    bookkeeping + the unpacked outlines (lazy: the budget or the two biggest parks, whichever is more; not lazy: every point,
    which is what kpc_fers.py holds until the switch-over keeps its passes lazy)."""
    unpacked = max(int(budget), int(biggest_two)) if lazy else int(points)
    return round(BOT_BASE_MB + TILE_FLOOR_MB + (points * PACKED_BYTES_PER_POINT + records * RECORD_META_BYTES + unpacked * LIST_BYTES_PER_POINT) / 1e6)


def fit_check(store, areas, limit_mb=3000, budget=2_000_000, neighbours=1.5, lazy=True):
    """-> (ok, rows): one row per area (verdict READY / NOT READY / WILL NOT FIT, why, points, estimate). The run as a whole
    (all member areas together, times `neighbours` for border parks) is checked against limit_mb."""
    rows, tot_pts, tot_rec, big = {}, 0, 0, []
    for ar in areas:
        a = store.area(ar)
        if a is None:
            rows[ar] = {'verdict': 'NOT READY', 'why': store.why[ar]}; continue
        pts = a.points(); rec = sum(len(e.get('records') or []) for e in a.entries.values() if isinstance(e.get('records'), list))
        tot_pts += pts; tot_rec += rec; big += a.biggest(2)
        rows[ar] = {'verdict': 'READY', 'why': '', 'points': pts, 'records': rec, 'built': a.made, 'held_entries': len(a.bad)}
    if any(r['verdict'] != 'READY' for r in rows.values()): return False, rows
    pts = int(tot_pts * neighbours); rec = int(tot_rec * neighbours)
    est = estimate_mb(pts, rec, sum(sorted(big, reverse=True)[:2]), budget, lazy)
    ok = est <= limit_mb
    for r in rows.values():
        r.update(estimate_mb=est, limit_mb=limit_mb, lazy=lazy, verdict='READY' if ok else 'WILL NOT FIT',
                 why='' if ok else (f'this run would need about {est} MB (store points x{neighbours} for border parks, '
                                    f"{'packed + ' + str(budget) + ' unpacked points' if lazy else 'every outline unpacked'}) against {limit_mb} MB: cut the area smaller"))
    return ok, rows


# ------------------------------------------------------------------ rows: no live pair vanishes, club-room tags, join review
def _live(s): return not str(s.get('status') or '').startswith(('dropped', 'merged'))


def _pk(s): return (tuple(sorted(s.get('refs') or [])), s.get('kind'))


def carry_rows(new, old, held, today=None):
    """Every LIVE row of the previous file whose pair + kind this run did not make again comes back as a row, so the post-line
    check never sees a live pair vanish: a park of it held -> 'not sure: held: <why>' (old answer kept for a person); otherwise
    -> 'dropped: not found again ...' (it goes on the change list as gone). passes [0, 0, 0]: no later pass tests it again.
    Returns the number of rows added."""
    if not isinstance(new, dict) or not isinstance(old, dict): return 0
    have = {_pk(s) for s in new.get('spots') or [] if isinstance(s, dict)}
    add = []
    for s in old.get('spots') or []:
        if not isinstance(s, dict) or not _live(s) or _pk(s) in have: continue
        x = {k: v for k, v in s.items() if k not in ('passes', 'status')}
        hr = {r: held[r] for r in s.get('refs') or [] if r in held}
        was = f"{str(s.get('status'))[:80]} on {old.get('pass3') or old.get('pass1') or 'the last run'}"
        x['passes'] = [0, 0, 0]; x['carried'] = today or True
        if hr:
            x['status'] = 'not sure: held: ' + '; '.join(f'{r}: {w}' for r, w in sorted(hr.items())) + f' (last answer: {was})'
            x['held'] = hr
        else:
            x['status'] = f'dropped: not found again on the outline store outlines (last answer: {was}); on the change list for a person'
        add.append(x); have.add(_pk(s))
    new.setdefault('spots', []).extend(add)
    return len(add)


def tag_club_room(doc, private):
    """club_room_only on every row that used an outline whose record is not publishable (the licence classes are named)."""
    n = 0
    for s in (doc or {}).get('spots') or []:
        pr = {r: private[r] for r in s.get('refs') or [] if r in private}
        if pr:
            s['club_room_only'] = True; s['club_room_why'] = {r: sorted(set(v.values())) for r, v in pr.items()}; n += 1
    return n


def join_review(row, flags, joined):
    """The matcher-flag rule (a proposal for the owner; not wired): a row with a park whose join the matcher doubts
    ('bigger-park-record' / 'bigger_place') is KEPT and tagged 'join under review' with the reason; it is HELD only when the two
    parks share joined record ids or identical record geometry (the overlap exists only because one park was given the other's
    outline). flags = {ref: reason}; joined = {ref: set of record ids and geometry checksums}. Returns 'kept' / 'tagged' / 'held'."""
    refs = row.get('refs') or []
    fl = {r: flags[r] for r in refs if r in flags and re.search(r'bigger', str(flags[r]))}
    if not fl: return 'kept'
    shared = set.intersection(*[set(joined.get(r) or ()) for r in refs]) if refs else set()
    row['join_review'] = fl
    if shared:
        row['status'] = ('not sure: join under review: the two parks share the same official record(s) ' + ', '.join(sorted(shared)[:4])
                         + ' (' + '; '.join(f'{r}: {w}' for r, w in sorted(fl.items())) + '): fix the join, then run again')
        return 'held'
    row['join_note'] = 'join under review: ' + '; '.join(f'{r}: {w}' for r, w in sorted(fl.items()))
    return 'tagged'


# ------------------------------------------------------------------ the kpc_fers.py side
def saved_corridors(KF):
    """saved_us() in store mode: ONLY the Wild and Scenic corridor records (wsrc<n>) of the saved key copy, so wsr_corridors()
    works as today; nothing else of the national copy is held."""
    if getattr(KF, '_STORE_CORR', None) is not None: return {}
    KF._STORE_CORR = 0
    for f in sorted(pathlib.Path(KF.CACHE_US).glob('US-*.json.gz')):
        if f.name.startswith('prev-'): continue
        try:
            with gzip.open(f, 'rt', encoding='utf-8') as fh: blob = json.load(fh)
        except Exception: continue  # noqa: BLE001
        for r in blob.get('recs') or []:
            oid = str(r.get('OBJECTID'))
            if r.get('_r') and re.fullmatch(r'wsrc\d+', oid):
                KF.SAVED_STR[oid] = r['_r']; KF.SAVED_DATE[oid] = r.get('rd') or blob.get('saved') or ''; KF.SAVED_NAME[oid] = r.get('Unit_Nm') or ''
                KF._STORE_CORR += 1
        del blob
    return {}


def store_download(KF, store, parks, refs, budget=2_000_000):
    """download()'s contract from the store: (LazyOutlines, bad). Nothing is unpacked here beyond one check per park (no rings
    kept). A held park goes into KF.MISSING_SAVED with its reason (kpc_fers.py's 'known reason' path)."""
    _pc = {r: [[KF.pc_ring(*KF.PC[r]['pt'])]] for r in refs if r in KF.PCT}
    _apx = {r: [parks[r]['rings']] for r in refs if (parks.get(r) or {}).get('rings') and (parks.get(r) or {}).get('approx') and not KF.has_official_outline(r, parks)}
    ok, bad, boxes, corr, clips = [], set(), {}, {}, {}
    for ref in [r for r in refs if r not in KF.PCT and r not in _apx]:
        p = parks[ref]
        if 'm' in p:
            bad.add(ref); FLAGS[ref] = 'world park: not read from the outline store'; KF.MISSING_SAVED[ref] = 'the outline store (world parks are not read from it)'; continue
        ids = list(p['ids'])
        if ids and all(re.fullmatch(r'wsrc\d+', str(i)) and str(i) in KF.SAVED_STR for i in ids):   # a corridor park: the saved copy, as today
            corr[ref] = [KF.clip(ref, i, KF.SAVED_STR[str(i)]) for i in ids]; KF.MAPDATE[ref] = 'saved copy (answer key)'; KF.SAVED_USE.add(ref); continue
        clips[ref] = (lambda rid, rs, _r=ref: KF.clip(_r, rid, rs))
        _, left, why, info = store.examine(ref, p['st'], ids, clips[ref], keep=False)
        if left: KF.LEFT.setdefault(ref, []).extend(left)
        if why:
            bad.add(ref); FLAGS[ref] = why
            KF.MISSING_SAVED[ref] = f'the outline store ({why}; flagged for the store filler)'
            continue
        FLAGS.pop(ref, None)
        ok.append(ref); boxes[ref] = list(info['box'])
        if info.get('private'): PRIVATE[ref] = info['private']
        KF.MAPDATE[ref] = f'outline store (read from the agency {store.read_date(ref, p["st"])})'
    for r in [r for r in KF.MISSING_SAVED if r in ok]: KF.MISSING_SAVED.pop(r)

    def load(ref):
        g, _, why = store.groups_for(ref, parks[ref]['st'], parks[ref]['ids'], clips[ref])
        return g if not why else None
    got = LazyOutlines(load, ok, budget, boxes)
    for r, v in {**corr, **_pc, **_apx}.items(): got[r] = v
    KF.inject_apx_geom(got, parks)
    return got, bad


def install(KF, env=None, store=None):
    """Switch the imported kpc_fers module to the store for this process. False (nothing changed; the bot runs as today) when
    the switch is off or the run is not US + Canada. Exits 87 / 88 (after writing the area rows) when an area is not ready or
    will not fit. Nothing is unpacked here."""
    global STORE_ON
    env = os.environ if env is None else env
    if mode(env) != 'on': return False
    if getattr(KF, 'REGION', 'na') != 'na':
        print(f'::notice title=2-fer outline store::{SWITCH} is on, but this is the {KF.REGION} run: the outline store is not used and the bot runs as today', flush=True)
        return False
    st = store or Store.from_env(env)
    out_dir = pathlib.Path(getattr(KF, 'OUT', 'data/fers')).resolve()
    tag = getattr(KF, 'area_name', lambda: 'run')()

    def write_rows():
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / f'store-missing-{tag}.json').write_text(json.dumps({
                'about': 'Outline store use by the 2-fer bot: one row per area (ready / not ready / will not fit) and every held park with its reason. One door in: only the store filler fetches.',
                'date': st.today, 'store': str(st.dir), 'kind': st.kind, 'areas': dict(sorted(AREA_ROWS.items())), 'parks': dict(sorted(FLAGS.items())),
                'club_room_only': dict(sorted(PRIVATE.items()))}, indent=1, ensure_ascii=False), encoding='utf-8')
        except OSError: pass
    areas = sorted(a for a in (getattr(KF, 'ONLY', None) or ()) if re.fullmatch(r'(US|CA)-[A-Z]{2}', a))
    lazy = bool(getattr(KF, 'FERS_LAZY_OK', False))   # set by the switch-over in kpc_fers.py once every pass keeps G lazy
    budget = int(env.get('KPC_FERS_STORE_BUDGET') or 2_000_000)
    ok, rows = fit_check(st, areas, int(env.get('KPC_FERS_STORE_LIMIT_MB') or 3000), budget,
                         float(env.get('KPC_FERS_STORE_NEIGHBOURS') or 1.5), lazy) if areas else (True, {})
    AREA_ROWS.update(rows)
    if not areas: print('::warning title=2-fer outline store::no member states named (STATES): the memory gate could not run', flush=True)
    bad_area = {a: r for a, r in rows.items() if r['verdict'] == 'NOT READY'}
    if bad_area or not ok:
        write_rows()
        for a, r in sorted(rows.items()):
            if r['verdict'] != 'READY': print(f"::error title=2-fer outline store::{a}: {r['verdict']}: {r['why']}. Nothing of this run is read or saved; the area keeps its previous files.", flush=True)
        raise SystemExit(EXIT_NOT_READY if bad_area else EXIT_WONT_FIT)
    orig_tag = KF.pc_tag

    def download(parks, refs, det, prec):   # det / prec are ignored: the store's detail (about 2 m, 6 decimals) in every pass
        return store_download(KF, st, parks, refs, budget)

    def saved_ca(parks):
        ca = {r: p for r, p in parks.items() if str(p.get('st', '')).startswith('CA-')}
        return store_download(KF, st, ca, list(ca), budget)[0]

    def live_load(area):
        KF.LIVE_FILE = None; KF.LIVE = {}
        return KF.LIVE

    def pc_tag(d):
        d = orig_tag(d)
        try:
            if isinstance(d, dict) and d.get('st'):
                f = pathlib.Path(KF.file_of(d['st']))
                old = json.loads(f.read_text(encoding='utf-8')) if f.is_file() else None
                n = carry_rows(d, old, FLAGS, st.today)
                if n: KF.LOG.append(f"{d['st']}: {n} live rows of the last file carried with their reason (held park or not found again)")
                tag_club_room(d, PRIVATE)
        except Exception as e: KF.LOG.append(f'outline store row carry: {str(e)[:80]}')  # noqa: BLE001
        return d

    KF.download, KF.saved_us, KF.saved_ca, KF.live_load, KF.pc_tag = download, (lambda parks: saved_corridors(KF)), saved_ca, live_load, pc_tag
    KF.STORE = st; STORE_ON = True
    atexit.register(write_rows)   # written on every run, so an old list never outlives a filled gap
    print(f"::notice title=2-fer outline store::{SWITCH}=on: outlines from {st.dir} ({st.kind} store); no boundary downloads; memory gate "
          + ', '.join(f"{a} {r.get('estimate_mb')} MB" for a, r in sorted(rows.items())) + ('' if lazy else ' (outlines all unpacked until the bot keeps them lazy)'), flush=True)
    return True


# ------------------------------------------------------------------ the reviewed change list
def _rows(doc):
    out = {}
    for s in (doc or {}).get('spots') or []:
        if not _live(s): continue
        out.setdefault(_pk(s), []).append(s)
    return out


def _km(a, b):
    return math.hypot((a[0] - b[0]) * 110.574, (a[1] - b[1]) * 111.32 * math.cos(math.radians(a[0])))


def diff_rows(old, new, moved_km=0.2):
    """Live rows of one area: same / new / gone / moved / status changed. Ids, names, kinds and statuses only: no shapes."""
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
    if cmd in ('check', 'fit'):
        if len(argv) < 2: print(f'usage: kpc_fers_store.py {cmd} <store_dir> <AREA> [...]'); return 2
        st = Store(argv[0], kind=str(os.environ.get('KPC_FERS_STORE_KIND') or 'public'))
        if cmd == 'fit':
            ok, rows = fit_check(st, argv[1:], int(os.environ.get('KPC_FERS_STORE_LIMIT_MB') or 3000), lazy=os.environ.get('KPC_FERS_STORE_LAZY', '1') != '0')
            for a, r in rows.items(): print(f"{a}: {r['verdict']} {r.get('estimate_mb', '')} MB {r['why']}")
            return 0 if ok else (EXIT_NOT_READY if any(r['verdict'] == 'NOT READY' for r in rows.values()) else EXIT_WONT_FIT)
        rc = 0
        for area in argv[1:]:
            a = st.area(area)
            if a is None: print(f'{area}: NOT READY: {st.why[area]}'); rc = 1; continue
            bad = dict(a.bad)
            for ref in a.entries:
                try: a.park(ref)
                except StoreError as e: bad[ref] = str(e)
            pts = a.points()
            print(f'{area}: {len(a.entries)} parks, {pts} points, built {a.made} ({a.age_days(st.today)} days old); outlines unpacked about '
                  f'{pts * LIST_BYTES_PER_POINT / 1e6:.0f} MB, packed about {pts * PACKED_BYTES_PER_POINT / 1e6:.0f} MB; checks: '
                  + ('PASS' if not bad else f'{len(bad)} parks held, e.g. {next(iter(bad))}: {next(iter(bad.values()))}'))
            rc = rc or (1 if bad else 0)
        return rc
    if cmd == 'diff':
        a = {argv[i]: argv[i + 1] for i in range(0, len(argv) - 1, 2)}
        if '--old' not in a or '--new' not in a: print('usage: kpc_fers_store.py diff --old FILE --new FILE [--out STEM]'); return 2
        d = diff_rows(_load(a['--old']), _load(a['--new']))
        if a.get('--out'):
            stem = pathlib.Path(a['--out'])
            stem.with_suffix('.json').write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding='utf-8')
            md = ['# 2-fer change list (store outlines against the last answers)', '', 'Nothing is published until a person signs this list; the old answers stay.', '',
                  ' | '.join(f'{k}: {v}' for k, v in d['counts'].items()), '']
            for k in ('new', 'gone', 'moved', 'status_changed'):
                md += [f'## {k} ({len(d[k])})', ''] + [f"- {' + '.join(r['refs'])} ({' / '.join(x for x in r['names'] if x)}) {r['kind']}"
                                                       + (f" {r.get('km')} km" if 'km' in r else '') for r in d[k]] + ['']
            stem.with_suffix('.md').write_text('\n'.join(md), encoding='utf-8')
        print(json.dumps(d['counts']))
        return 0
    if cmd == 'run':
        if mode() != 'on': print(f'{SWITCH} is not on: this command runs only the store path (use kpc_fers.py for the normal run)'); return 2
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import kpc_fers as KF
        if KF.REGION != 'na': print(f'the {KF.REGION} run does not use the outline store: use kpc_fers.py'); return 2
        install(KF)
        KF.main()
        return 0
    print(f'unknown command {cmd!r}'); return 2


if __name__ == '__main__':
    sys.exit(main())
