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
  - the shut door (shut_door): NO network request at all. pad_closed() (the live PAD-US closed-area read) asks nothing; an area
    spot whose closed-area check could not run is NOT SURE ('closed areas not checked'), never confirmed. Every fetch of
    kpc_fers.py / kpc_owned.py / the answer cache is refused before it is sent, and the process's sockets are shut;
  - the write guard (guard_write, at kpc_fers.py's write step _save_json_raw and on the store-missing list): the run FAILS
    (exit 89) rather than write a club_room_only row, a park whose outline came from unpublishable records, a world 2-fer or a
    never-released build (US-42797939226) to a public file. A PRIVATE store run writes every file into KPC_FERS_PRIVATE_OUT,
    which must be outside every git work tree (else exit 89 before anything is read): its files are club room only.
  - store format 4 (tool 3.5): only geometry_kind 'area' records make outlines; 'line' records give line parks their line for
    today's unchanged line rule (store_lines; trail_lines() in a store run); pins and unknown kinds are never used; water tiles
    from the store first (store_water); the river centre-line fallback behind KPC_FERS_RIVER_NO_BANK (default unchanged);
  Kentucky and world runs: install() returns False and the bot runs AS TODAY (downloads included): nothing here refuses them.
Settings: KPC_FERS_STORE_DIR (default 'store'), KPC_FERS_STORE_MAX_DAYS (45), KPC_FERS_STORE_KIND = public | private (default
public: a park with any record not marked publishable is held 'needs the private store'), KPC_FERS_PRIVATE_OUT (private only),
KPC_FERS_STORE_LIMIT_MB (3000, the whole process), KPC_FERS_STORE_BUDGET (2,000,000 unpacked points), KPC_FERS_STORE_NEIGHBOURS
(1.5: border parks from other areas).

The store: index contract 'kpc-outline-store-index/3' (outline store tool full 3; format 1 pieces). Only that version is read;
another is refused (the area is NOT READY). Only the per-area index-<AREA>.json is read (the combined index.json keeps one entry
for a park that sits in two areas), and each area file must match its sha256 and size in the index before it is used. A park
with tracts in two area files is assembled from both. Per record: publishable (true only with publish_basis verified-row or
owner-confirmed), licence_class, publish_basis, wdpa_derived (must be false; the text-value scan is a second check), private_reason.

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
STORE_FORMAT_VERSION = 'kpc-outline-store-index/3'   # the outline store tool 'full 3' index contract this reader was written for
STORE_FORMAT_VERSIONS = ('kpc-outline-store-index/3', 'kpc-outline-store-index/4')   # /4 = tool 3.5: records carry geometry_kind
PUBLISH_BASES = ('verified-row', 'owner-confirmed')
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
BLOCKED_BUILDS = frozenset({'US-42797939226'})   # = kpc_release.BLOCKED_BUILDS: never released, never in any file this run writes
EXIT_LEAK = 89     # the write guard refused a file (or a private store run has no safe private folder): nothing more is written
PRIVATE_OUT = None  # private store runs only: the one folder every file of the run goes to (outside any git work tree)
NET_TRIES = []     # store runs: every socket connection the shut door refused (the finder must make none)
ASKED = []         # store runs: every fetch kpc_fers.py asked for and the door refused before it was sent (never an outline)
CLOSED_NOT_CHECKED = {'n': 0}   # store runs: area spots whose PAD-US closed-area check could not run (no download)
PUBLIC_REF = re.compile(r'(US|CA)-\d+')
GEOM_SKIPPED = {}  # format 4: ref -> {geometry kind: records} left out of the park's AREA outline (lines, pins, unknown kinds)
STORE_LINES = {}   # format 4: ref -> the line entry (kpc_fers.py LN form) whose geometry came from the store
LINE_ROWS = {}     # area -> live trail / river rows (pairs that depend on the 100-ft line rule) in this run's files
WATER_READ = {'store': 0, 'not in store': 0, 'store tile damaged': 0}
RIVER_SWITCH = 'KPC_FERS_RIVER_NO_BANK'   # centreline (default: today's rule, unchanged) | tiers (PROVISIONAL, the owner's Nov 14 ruling)
RIVER_NO_BANK = {'mode': 'centreline', 'catch_m': 250.0, 'half_m': 150.0, 'along_m': 50.0}
RIVER_TIERS = {}   # tier -> stretches / rows this run (tiers mode)
RIVER_TODO = []    # tiers mode: river + park stretches the bank store must fetch (ids, distances, signs; no geometry)
TIER_BANK, TIER_CENTRE = 'bank', 'park reaches the river centre line'
TIER_ALONG, TIER_LINE = 'bank assumed from the park boundary (no official bank shape yet)', 'about 100 ft from the centre line'


def river_mode(env=None):
    env = os.environ if env is None else env
    v = str(env.get(RIVER_SWITCH) or '').strip().lower()
    for k, e in (('catch_m', 'KPC_FERS_RIVER_CATCH_M'), ('half_m', 'KPC_FERS_RIVER_HALF_M')):
        try: RIVER_NO_BANK[k] = float(env.get(e) or RIVER_NO_BANK[k])
        except ValueError: pass
    return 'tiers' if v == 'tiers' else 'centreline'


def kind_of(r):
    """A record's geometry kind (format 4). Absent = 'area' (every format-3 record); an unknown value is NOT an area."""
    k = r.get('geometry_kind') if isinstance(r, dict) else None
    return 'area' if k in (None, '') else str(k)


class NoDownload(OSError):
    """Store run: the outline store is the only door. Raised instead of any network request (an OSError, so every existing
    'the map did not answer' path in kpc_fers.py takes it: held / NOT SURE, never a guess)."""


class LeakRefused(SystemExit):
    """The write guard refused a file. A SystemExit (not an Exception) so no 'except Exception' in kpc_fers.py can swallow it:
    the run fails rather than write a club-room-only row, a private park, a world 2-fer or a blocked build to a public file."""
    def __init__(self, why):
        print(f'::error title=2-fer outline store: write refused::{why}. Nothing more is written; the area keeps its previous files.', flush=True)
        super().__init__(EXIT_LEAK)
        self.why = why


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
        p = d / f'index-{area}.json'   # the per-area index only: the combined index.json keeps one entry for a park in two areas
        if not p.is_file():
            raise StoreError(f'no per-area index index-{area}.json' + (' (the combined index.json is not read: it loses parks that span areas)' if (d / 'index.json').is_file() else ''))
        try: idx = json.loads(p.read_text(encoding='utf-8'))
        except Exception as e: raise StoreError(f'index {p.name} cannot be read ({_err(e)})')  # noqa: BLE001
        if not isinstance(idx, dict) or not isinstance(idx.get('parks'), dict): raise StoreError(f'index {p.name} is not a store index')
        if idx.get('store_format_version') not in STORE_FORMAT_VERSIONS:
            raise StoreError(f'store format version {idx.get("store_format_version")!r}; this reader reads {" and ".join(map(repr, STORE_FORMAT_VERSIONS))} only')
        if str(idx.get('format')) != str(FORMAT): raise StoreError(f'store format {idx.get("format")!r}; this reader reads {FORMAT}')
        if idx.get('area') not in (None, area): raise StoreError(f'index-{area}.json says it is area {idx.get("area")!r}')
        hit = sorted(b for b in BLOCKED_BUILDS if any(b in str(v) for k, v in idx.items() if k not in ('parks', 'files')))
        if hit: raise StoreError(f'the index names build {hit[0]}, which is never released')
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
        for f in sorted({str(e['file']) for e in self.entries.values()}):   # each area file checked whole against the index before any use
            want = files.get(f) if isinstance(files.get(f), dict) else None
            if not want or not want.get('sha256'): raise StoreError(f'the index gives no sha256 for {f}')
            h, n = hashlib.sha256(), 0
            with open(d / f, 'rb') as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b''): h.update(chunk); n += len(chunk)
            if h.hexdigest() != want['sha256'] or (want.get('bytes') is not None and int(want['bytes']) != n):
                raise StoreError(f'{f} does not match its sha256 / size in the index (changed or damaged)')
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
                if kind_of(r) == 'line':   # format 4: an open path, checked like a ring (never closed, never buffered here)
                    ls = r.get('lines') or []
                    if geometry_sha256(ls) != r.get('line_sha256') or sum(len(x) // 2 for x in ls) != int(r.get('line_points') or 0):
                        raise StoreError(f"record {r.get('key')} line checksum or point count does not match")
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

    def locate_all(self, ref, area):
        """Every area store that holds a piece of ref: the key's own state first, then every other per-area index in the folder
        (a park can have tracts in two area files, or be filed by the key under a neighbour's state). ([AreaStore], why)."""
        a = self.area(area)
        if not hasattr(self, '_names'): self._names = sorted(p.name[6:-5] for p in self.dir.glob('index-*.json'))
        found = [a] if a is not None and (ref in a.entries or ref in a.bad) else []
        for other in self._names:
            if other == area: continue
            b = self.area(other)
            if b is not None and (ref in b.entries or ref in b.bad): found.append(b)
        if not found and a is None: return [], self.why[area]
        return found, ''

    def _examine(self, ref, area, ids, clip, keep):
        stores, why = self.locate_all(ref, area)
        if not stores and why: return None, [], why, {}
        if not stores: return None, [], f'{ref} is not in the outline store for {area}', {}
        by = {}   # record key -> (record, its park piece): a park with tracts in two area files is assembled whole
        for a in stores:
            try: p = a.park(ref)
            except StoreError as e: return None, [], f'{ref} in the outline store ({a.area}) failed its check ({str(e)[:120]})', {}
            if p is None: continue
            if p.get('circle') or p.get('grade') == 'point-circle':
                return None, [], f'{ref} has only a point circle in the store (the 2-fer bot makes its own circle)', {}
            if wdpa_text(p): return None, [], f'{ref}: the store park looks WDPA / Protected Planet derived: never a 2-fer source', {}
            meta = (a.entries.get(ref) or {}).get('record_meta') if isinstance((a.entries.get(ref) or {}).get('record_meta'), dict) else {}
            for r in p.get('records') or []:
                if not isinstance(r, dict): continue
                m = meta.get(str(r.get('key')))
                if isinstance(m, dict) and any(m.get(k) != r.get(k) for k in ('publishable', 'licence_class', 'publish_basis', 'wdpa_derived')):
                    return None, [], f'record {r.get("key")} of {ref}: the index and the store disagree on its licence fields', {}
                by.setdefault(str(r.get('key')), (r, p))
        groups, left, private, pts, box, skipped = [], [], {}, 0, None, {}
        for rid in ids:
            r, p = by.get(str(rid), (None, None))
            if r is None: return None, [], f'the outline store has no record {rid} for {ref} (the key joins it)', {}
            if r.get('wdpa_derived') is not False:   # the store's own flag first (true, or not stated): never a 2-fer source
                return None, [], f'record {rid} of {ref} is marked WDPA derived by the store (or does not say): never a 2-fer source', {}
            if wdpa_text(r): return None, [], f'record {rid} of {ref} looks WDPA / Protected Planet derived: never a 2-fer source', {}
            k = kind_of(r)
            if k != 'area':   # format 4: only AREA records are outlines. A line is tested by the line rule (store_lines), a pin never
                skipped[k] = skipped.get(k, 0) + 1; continue
            if r.get('use') is False:
                left.append(f"{r.get('record_name') or rid}: {r.get('use_why') or 'not public land (store use flag)'}"); continue
            if not (r.get('publishable') is True and r.get('publish_basis') in PUBLISH_BASES):
                private[str(rid)] = {'licence_class': str(r.get('licence_class') or 'NOT RECORDED'), 'publish_basis': str(r.get('publish_basis') or 'none'),
                                     'private_reason': str(r.get('private_reason') or '')}
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
        if box is None:
            if skipped: return None, left, (f'{ref} has no area record in the outline store (' + ', '.join(f'{v} {k}' for k, v in sorted(skipped.items()))
                                             + '): a line is tested by the line rule, a pin is never a boundary'), {'skipped': skipped, 'no_area': True}
            return None, left, (f'every record of {ref} is left out by its use flag' if left else f'{ref} has no rings in the store'), {}
        if private and self.kind == 'public':
            return None, left, f'{ref} needs the private store (records not publishable: ' + ', '.join(f"{k} {v['licence_class']}" for k, v in sorted(private.items())[:4]) + ')', {}
        return (groups if keep else None), left, '', {'points': pts, 'box': box, 'private': private, 'skipped': skipped}

    def groups_for(self, ref, area, ids, clip=None):
        g, left, why, _ = self.examine(ref, area, ids, clip, keep=True)
        return g, left, why

    def read_date(self, ref, area):
        st = self.locate_all(ref, area)[0]
        return min((str((a.entries.get(ref) or {}).get('date') or a.made) for a in st), default='')


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
            s['club_room_only'] = True; s['club_room_why'] = {r: sorted({str(x.get('licence_class') if isinstance(x, dict) else x) for x in v.values()}) for r, v in pr.items()}; n += 1
    return n


def closed_status(doc):
    """Store run: an area spot whose closed-area check could not run is NOT SURE with that reason (land_check said 'not checked',
    which kpc_fers.py words as a water reason)."""
    n = 0
    for s in (doc or {}).get('spots') or []:
        if s.get('closed_check') and str(s.get('status') or '').startswith('not sure: water not checked'):
            s['status'] = 'not sure: closed areas not checked (' + s['closed_check'][len('not checked: '):] + '): the store must carry them first'; n += 1
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
        if info.get('skipped'): GEOM_SKIPPED[ref] = dict(info['skipped'])
        if why and info.get('no_area') and ref in STORE_LINES:   # a line park: tested by its store line (LN), not held
            FLAGS.pop(ref, None); continue
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


# ------------------------------------------------------------------ the write guard: club room only never reaches a public file
def _inside(p, root):
    try: pathlib.Path(p).resolve().relative_to(pathlib.Path(root).resolve()); return True
    except ValueError: return False


def in_git_tree(p):
    """True when p (or a folder above it) is a git work tree: a file there could be committed and pushed to a public repo."""
    p = pathlib.Path(p).resolve()
    return any((q / '.git').exists() for q in (p, *p.parents))


def _dicts(obj, depth=0):
    if depth > 14: return
    if isinstance(obj, dict):
        yield obj
        for v in obj.values(): yield from _dicts(v, depth + 1)
    elif isinstance(obj, (list, tuple)):
        for v in obj: yield from _dicts(v, depth + 1)


def guard_write(path, doc, private=None):
    """THE WRITE STEP of a store run: every file kpc_fers.py saves (spot files, reuse, report, looked, missing, same-outline ...)
    and the store-missing list pass here first. Raises LeakRefused (the run fails, nothing is written) when the file
      - names a build that is never released (BLOCKED_BUILDS), in any file;
      - is outside the private folder, on a private store run (every file of such a run is club room only);
      - is a public file and holds a row marked club_room_only, a 2-fer row with a park that is not US / Canada (world 2-fers
        stay off the public site), or ANY mention of a park whose outline came from records that are not publishable (with
        or without its shape, width, centre or area)."""
    private = PRIVATE if private is None else private
    txt = json.dumps(doc, default=str, ensure_ascii=False)
    hit = sorted(b for b in BLOCKED_BUILDS if b in txt)
    if hit: raise LeakRefused(f'{path}: it names {hit[0]}, which is never released')
    if PRIVATE_OUT is not None:
        if not _inside(path, PRIVATE_OUT): raise LeakRefused(f'{path}: a private store run writes only into its private folder')
        return
    for d in _dicts(doc):
        if d.get('club_room_only') or 'club_room_why' in d:
            raise LeakRefused(f"{path}: a row marked club_room_only ({'+'.join(map(str, d.get('refs') or [])) or '?'}) would go into a public file")
        refs = d.get('refs')
        if isinstance(refs, list) and d.get('kind') is not None and any(not PUBLIC_REF.fullmatch(str(r)) for r in refs):
            raise LeakRefused(f"{path}: a 2-fer row with a park outside the US and Canada ({'+'.join(map(str, refs))}) would go into a public file")
    for r in sorted(private):
        if re.search(r'(?<![\w-])' + re.escape(str(r)) + r'(?!\d)', txt):
            raise LeakRefused(f'{path}: it names {r}, whose outline came from records that are not publishable')


# ------------------------------------------------------------------ the shut door: a store run makes no network request at all
def _refuse_fetch(url='', *a, **k):
    ASKED.append(str(url)[:120])
    raise NoDownload(f'store run: no download of {str(url)[:60] or "anything"} (the outline store is the only door)')


def _refuse_socket(*a, **k):
    NET_TRIES.append(str(a[1:2] or a[:1])[:120])
    raise NoDownload('store run: no network connection (the outline store is the only door)')


CLOSED_WHY = ('PAD-US closed areas are not in the outline store and a store run downloads nothing, so rule 10 (no-entry areas) '
              'could not be checked here')


def shut_door(KF):
    """Store run: (1) pad_closed() asks nothing (it was a live PAD-US read inside the decide step); an area spot whose closed-area
    check could not run is 'not checked' -> NOT SURE, never confirmed; (2) every fetch kpc_fers.py, kpc_owned.py and the answer
    cache can make is refused before it is sent (live water, ownership tiles, trail status, layer dates, bundle answers); (3) the
    sockets of this process are shut as the last line. A refused fetch is listed in ASKED, a refused socket in NET_TRIES."""
    import socket
    def _no_closed(box):
        raise NoDownload('PAD-US closed areas are not in the outline store (no download)')
    KF.pad_closed = _no_closed
    orig_lc = getattr(KF, 'land_check', None)
    if orig_lc is not None and not getattr(orig_lc, '_store', False):
        def land_check(s, G, live=True):
            asked = []
            def no_closed(box): asked.append(1); raise NoDownload('PAD-US closed areas are not in the outline store (no download)')
            KF.pad_closed = no_closed
            try: r = orig_lc(s, G, live=live)
            finally: KF.pad_closed = _no_closed
            if asked:   # the overlap needed the closed-area check and it could not run: never confirmed
                CLOSED_NOT_CHECKED['n'] += 1
                s['closed_check'] = 'not checked: ' + CLOSED_WHY + ('; the water was not checked either' if r == 'not checked' else '')
                return 'not checked'
            return r
        land_check._store = True
        KF.land_check = land_check
    for mod in (KF, getattr(KF, 'KO', None)):
        if mod is not None and hasattr(mod, '_get'): mod._get = _refuse_fetch
    if hasattr(KF, '_wlive'): KF._wlive = lambda i, jt, *a, **k: _refuse_fetch(f'USGS water tile {i},{jt} (live)')
    for name in ('_wsave', 'live_save'):
        if hasattr(KF, name): setattr(KF, name, lambda *a, **k: None)
    hc = getattr(KF, 'HC', None)
    if hc is not None:
        hc.OFFLINE = True
        hc.cached = lambda url, params, fetch: _refuse_fetch(url)
    socket.socket.connect = lambda self, *a, **k: _refuse_socket(self, *a)
    socket.socket.connect_ex = lambda self, *a, **k: _refuse_socket(self, *a)
    socket.create_connection = _refuse_socket
    socket.getaddrinfo = _refuse_socket
    raw = getattr(KF, '_save_json_raw', None)
    if raw is not None and not getattr(raw, '_store', False):
        def guarded(p, d, *a, **k):
            if isinstance(d, dict) and pathlib.Path(p).name.startswith('report') and STORE_ON: d = dict(d, outline_store=store_counts())
            guard_write(p, d); out = raw(p, d, *a, **k)
            ks = sys.modules.get('kpc_save')   # its exit-time status file (data/status/<bot>.json) must not list private files
            if PRIVATE_OUT is not None and ks is not None and isinstance(getattr(ks, '_changed', None), dict): ks._changed.pop(str(pathlib.Path(p)), None); ks._changed.pop(str(p), None)
            return out
        guarded._store = True
        KF._save_json_raw = guarded


# ------------------------------------------------------------------ format 4: lines (trails, rivers) and water tiles from the store
def store_lines(KF, st, areas, base):
    """kpc_fers.trail_lines() in a store run. base = today's lines from data/trails ({ref: {'lines', 'kind', 'by', 'type',
    'water_parts'}}). The line GEOMETRY now comes from the store's line records; what the line rule needs to know about the
    park (trail or river, who drew it, NHT type, which pieces are water) still comes from data/trails as today, so the rule and
    its widths are unchanged (100 ft: 25.48 m from a centre line with the station 5 m inside the other park, 30.48 m from a
    river's bank; a 25 m stretch). A line park whose line is not in the store is HELD (one door in); a line park the store has
    and data/trails does not is added (kind from its record). Line records of a park that also has area records are not used:
    the park is tested as an area, as today."""
    out, seen = {}, set()
    names = sorted({a for a in areas} | {pp.name[6:-5] for pp in pathlib.Path(st.dir).glob('index-*.json')})
    cand = {}
    for ar in areas:
        a = st.area(ar)
        for ref, e in ((a.entries.items()) if a is not None else ()):
            if e.get('geometry_kind') == 'line': cand.setdefault(ref, ar)
    for ref in base: cand.setdefault(ref, (areas or names or [''])[0])
    for ref, ar in sorted(cand.items()):
        stores, why = st.locate_all(ref, ar)
        rec, park, bad = [], None, ''
        for a in stores:
            try: pk = a.park(ref)
            except StoreError as e: bad = f'{ref} in the outline store ({a.area}) failed its check ({str(e)[:100]})'; break
            if pk is None: continue
            park = park or pk
            if wdpa_text(pk): bad = f'{ref}: the store park looks WDPA / Protected Planet derived: never a 2-fer source'; break
            if any(kind_of(r) == 'area' and r.get('use') is not False for r in pk.get('records') or []): rec = None; break   # an area park: tested as an area
            for r in pk.get('records') or []:
                if kind_of(r) != 'line' or r.get('use') is False: continue
                if r.get('wdpa_derived') is not False or wdpa_text(r): bad = f'line record {r.get("key")} of {ref} is WDPA derived (or does not say): never a 2-fer source'; break
                rec.append(r)
            if bad: break
        if rec is None: continue
        if not bad and not rec: bad = (why or f'{ref}: its official line is not in the outline store') if ref in base else ''
        if not bad and rec:
            priv = {str(r.get('key')): {'licence_class': str(r.get('licence_class') or 'NOT RECORDED'), 'publish_basis': str(r.get('publish_basis') or 'none'),
                                        'private_reason': str(r.get('private_reason') or '')} for r in rec if not (r.get('publishable') is True and r.get('publish_basis') in PUBLISH_BASES)}
            if priv and st.kind == 'public': bad = f'{ref} needs the private store (line records not publishable: ' + ', '.join(f"{k} {v['licence_class']}" for k, v in sorted(priv.items())[:4]) + ')'
            elif priv: PRIVATE[ref] = priv
        if bad:
            FLAGS[ref] = bad; KF.LOG.append(f'outline store line: {bad[:120]}'); continue
        if not rec: continue
        ls = [ring_floats(e) for r in rec for e in (r.get('lines') or [])]
        ls = [x for x in ls if len(x) > 1]
        if not ls:
            if ref in base: FLAGS[ref] = f'{ref}: its line records in the outline store have no usable path'
            continue
        meta = base.get(ref) or {}
        txt = ' '.join(str(r.get(k) or '') for r in rec for k in ('record_name', 'boundary_kind', 'layer')) + ' ' + str((park or {}).get('name') or '')
        e = {'lines': ls, 'kind': meta.get('kind') or ('river' if re.search(r'river', txt, re.I) else 'trail'),
             'by': meta.get('by') or '; '.join(sorted({str(r.get('credit_line') or '') for r in rec} - {''})) or 'outline store',
             'type': meta.get('type') or str(rec[0].get('boundary_kind') or ''), 'date': min(str(r.get('date') or (park or {}).get('date') or '') for r in rec) or st.today,
             'from': 'outline store', **({'bank_missing': True} if any(r.get('bank_missing') is True for r in rec) else {}),   # kept for the reader; the tiers test the water itself
             **({'boundary_rule': str(rec[0].get('boundary_rule'))} if rec[0].get('boundary_rule') else {})}
        if meta.get('water_parts'):
            if len(meta['lines']) == len(ls): e['water_parts'] = meta['water_parts']
            else: KF.LOG.append(f'{ref}: the store line has {len(ls)} pieces, data/trails {len(meta["lines"])}: its water / land split is not carried (bank test only, not sure)')
        out[ref] = e; STORE_LINES[ref] = e; FLAGS.pop(ref, None); seen.add(ref)
    return out


def store_counts():
    """What the run report and the store-missing list say about format-4 records (counts and ids only, no geometry)."""
    tot = {}
    for v in GEOM_SKIPPED.values():
        for k, n in v.items(): tot[k] = tot.get(k, 0) + n
    return {'records left out of area outlines (not area)': dict(sorted(tot.items())), 'parks with records left out': len(GEOM_SKIPPED),
            'line parks read from the store': len(STORE_LINES), 'live pairs on the 100-ft line rule': dict(sorted(LINE_ROWS.items())),
            'water tiles': dict(WATER_READ), 'river rule with no bank data': dict(RIVER_NO_BANK), 'river tiers': dict(RIVER_TIERS),
            'river bank to-do (stretches)': len(RIVER_TODO)}


def river_bank_guard(KF, mode):
    """The river rule where there is NO bank data, behind ONE switch (KPC_FERS_RIVER_NO_BANK). Today (kpc_fers.line_spots) a
    US river stretch is measured 30.48 m from the BANK where a water area covers the line, and 25.48 m from the CENTRE LINE (100 ft
    less the 5 m station) where none does; Canada always from the centre line (no bank source wired).
    'centreline' (the default) = exactly today. 'tiers' = PROVISIONAL (the owner's Nov 14 ruling, store runs, US rivers only):
      1 bank: every point of the stretch lies in mapped water: today's bank test (solid);
      2 park reaches the river centre line: the other park's outline holds a centre-line point: certain whatever the width (counts);
      3 bank assumed from the park boundary / 4 about 100 ft from the centre line: no bank data and the park lies within the catch
        distance (KPC_FERS_RIVER_CATCH_M, 250 m) of the centre line: a CANDIDATE, never a 2-fer ('river candidate: needs bank
        shape', with the distance and the signs: 3 = a park edge runs along the river within KPC_FERS_RIVER_HALF_M, 150 m, for 50 m),
        and the stretch goes on the bank store's to-do list. A private strip between bank and park does not matter: only whether
        the 30.48 m-from-bank strip reaches the park, which needs the bank shape.
    Trails, Canada and pass 1 are untouched. Each row says which tier decided it (river_tier)."""
    RIVER_NO_BANK['mode'] = mode
    orig = getattr(KF, 'line_spots', None)
    if mode != 'tiers' or orig is None or getattr(orig, '_store', False): return
    def line_spots(lref, ls, oref, other, other_is_line, box, kind):
        got = orig(lref, ls, oref, other, other_is_line, box, kind)
        if kind != 'river' or other_is_line or not str(lref).startswith('US-') or int(getattr(KF, 'PASS', 3)) < 2: return got
        return river_tiers(KF, lref, ls, oref, other, box, got)
    line_spots._store = True
    KF.line_spots = line_spots


def _tier(t): RIVER_TIERS[t] = RIVER_TIERS.get(t, 0) + 1


def river_tiers(KF, lref, ls, oref, other, box, got):
    np = KF.np
    catch, half, along = RIVER_NO_BANK['catch_m'], RIVER_NO_BANK['half_m'], RIVER_NO_BANK['along_m']
    cell = float(KF.CELL)
    ob = KF.bbox_groups(other)
    if not ob: return got
    m = catch / 111000.0
    pts = [tuple(q[:2]) for l in ls for q in (KF.sample(l, cell) or l) if ob[0] - 2 * m <= q[0] <= ob[2] + 2 * m and ob[1] - 2 * m <= q[1] <= ob[3] + 2 * m]
    if not pts: return got
    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
    F = KF.Frame([min(xs), min(ys), max(xs), max(ys)], cell, catch + 2 * cell)
    park = F.area(other)
    dpark = np.minimum(KF.dt(1 - park, outside=1), 1e7) * cell        # metres from each pixel to the park (0 inside it)
    wg = KF.nhd_water(F.bounds(), rivers_only=True)
    wet = F.area(wg) if wg else np.zeros_like(park)
    P = F.px(pts).astype(int); P[:, 0] = P[:, 0].clip(0, F.W - 1); P[:, 1] = P[:, 1].clip(0, F.H - 1)
    dd, ww = dpark[P[:, 1], P[:, 0]], wet[P[:, 1], P[:, 0]] > 0
    dry = ~ww                                                     # no bank data at these centre-line points
    for x in got:
        sp = x.get('shape') or []
        if sp:
            Q = F.px(sp).astype(int); Q[:, 0] = Q[:, 0].clip(0, F.W - 1); Q[:, 1] = Q[:, 1].clip(0, F.H - 1)
            inw, inp = wet[Q[:, 1], Q[:, 0]] > 0, park[Q[:, 1], Q[:, 0]] > 0
        else: inw = inp = np.zeros(1, bool)
        x['river_tier'] = TIER_BANK if inw.all() else TIER_CENTRE if inp.any() else TIER_LINE
        _tier(x['river_tier'])
    if any(x['river_tier'] in (TIER_BANK, TIER_CENTRE) for x in got) or not dry.any(): return got
    dmin = float(dd[dry].min())
    if dmin > catch: return got
    run, best, prev = 0.0, 0.0, None   # sign of tier 3: a park edge along the river (within half_m of the centre line for along_m)
    for i, q in enumerate(pts):
        ok = dry[i] and dd[i] <= half
        if ok and prev is not None: run += KF.close_m(prev, q)
        elif not ok: run = 0.0
        prev = q if ok else None; best = max(best, run)
    signs = (['park reaches the river centre line'] if dmin == 0 else []) + ([f'a park edge runs along the river for {round(best)} m within {round(half)} m of the centre line'] if best >= along else [])
    tier = TIER_ALONG if best >= along else TIER_LINE
    k = int(np.argmin(np.where(dry, dd, 1e9)))
    near = [pts[i] for i in range(len(pts)) if dry[i] and dd[i] <= dmin + cell][:200] or [pts[k]]
    row = {'refs': sorted([lref, oref]), 'kind': 'river', 'center': [round(pts[k][1], 6), round(pts[k][0], 6)], 'len_m': 0,
           'shape': [[round(q[0], 6), round(q[1], 6)] for q in (near if len(near) > 1 else near * 2)], 'river_tier': tier,
           'river_candidate': {'centre_line_m': round(dmin), 'signs': signs, 'catch_m': catch}}
    for x in got: x['river_tier'] = tier
    _tier(tier)
    RIVER_TODO.append({'refs': row['refs'], 'river': lref, 'park': oref, 'centre_line_m': round(dmin), 'signs': signs, 'tier': tier,
                       'box': [round(min(q[0] for q in near), 4), round(min(q[1] for q in near), 4), round(max(q[0] for q in near), 4), round(max(q[1] for q in near), 4)]})
    return got if got else [row]


def bank_status(doc):
    """tiers mode: a live river row decided by tier 3 or 4 is a CANDIDATE, never a 2-fer, until a bank shape exists."""
    n = 0
    for s in (doc or {}).get('spots') or []:
        if s.get('river_tier') in (TIER_ALONG, TIER_LINE) and not str(s.get('status') or '').startswith(('dropped', 'merged')):
            c = s.get('river_candidate') or {}
            s['status'] = ('river candidate: needs bank shape (' + s['river_tier'] + (f"; {c['centre_line_m']} m from the centre line" if 'centre_line_m' in c else '')
                           + (('; ' + '; '.join(c['signs'])) if c.get('signs') else '') + ')')
            s.pop('list', None); n += 1
    return n


def store_water(st, areas, i, jt):
    """A 0.1-degree water tile from the store's water section (store/water/<AREA>/<i>_<jt>.json.gz, the SAME tile form as the
    bot's WATER_STORE: {'d': date, 'f': [[layer, rings], ...]}), or None. The run's areas first, then every other area folder."""
    root = pathlib.Path(st.dir) / 'water'
    if not root.is_dir(): return None
    dirs = [root / a for a in areas] + sorted(d for d in root.iterdir() if d.is_dir() and d.name not in areas)
    for d in dirs:
        f = d / f'{i}_{jt}.json.gz'
        if not f.is_file(): continue
        try:
            t = json.loads(gzip.decompress(f.read_bytes()))
            if isinstance(t, dict) and isinstance(t.get('f'), list) and t.get('d'): WATER_READ['store'] += 1; return t
        except Exception: pass  # noqa: BLE001
        WATER_READ['store tile damaged'] += 1   # a damaged tile is never 'no water': the next copy, else NOT SURE
    WATER_READ['not in store'] += 1
    return None


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
    global PRIVATE_OUT
    st = store or Store.from_env(env)
    if st.kind == 'private':
        # a private store holds records that are not publishable: every file of the run is club room only, so it goes to ONE
        # folder outside every git work tree (never the KPC-Data checkout); without one the run does not start
        po = str(env.get('KPC_FERS_PRIVATE_OUT') or '').strip()
        why = ('KPC_FERS_PRIVATE_OUT is not set' if not po else
               'KPC_FERS_PRIVATE_OUT is inside a git work tree' if in_git_tree(po) else
               'KPC_FERS_PRIVATE_OUT overlaps the working folder' if _inside(po, os.getcwd()) or _inside(os.getcwd(), po) else '')
        if why:
            print(f'::error title=2-fer outline store::private store run refused: {why}. A private store run writes only into a '
                  'private folder outside every git work tree (club room only); nothing was read or saved.', flush=True)
            raise SystemExit(EXIT_LEAK)
        PRIVATE_OUT = pathlib.Path(po).resolve(); PRIVATE_OUT.mkdir(parents=True, exist_ok=True)
        KF.OUT = PRIVATE_OUT
    out_dir = pathlib.Path(getattr(KF, 'OUT', 'data/fers')).resolve()
    tag = getattr(KF, 'area_name', lambda: 'run')()

    def write_rows():
        doc = {'about': 'Outline store use by the 2-fer bot: one row per area (ready / not ready / will not fit) and every held park with its reason. One door in: only the store filler fetches.',
               'date': st.today, 'store': str(st.dir), 'kind': st.kind, 'areas': dict(sorted(AREA_ROWS.items())), 'parks': dict(sorted(FLAGS.items())),
               **store_counts()}
        if st.kind == 'private': doc['private_records'] = dict(sorted(PRIVATE.items()))
        if RIVER_TODO: doc['river_bank_todo'] = RIVER_TODO   # the stretches the bank store must fetch (tiers mode)
        p = out_dir / f'store-missing-{tag}.json'
        guard_write(p, doc)
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding='utf-8')
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
                closed_status(d)
                if RIVER_NO_BANK['mode'] == 'tiers': bank_status(d)
                LINE_ROWS[d['st']] = sum(1 for x in d.get('spots') or [] if x.get('kind') in ('trail', 'river') and _live(x))
        except Exception as e: KF.LOG.append(f'outline store row carry: {str(e)[:80]}')  # noqa: BLE001  (the write guard still checks the file)
        return d

    shut_door(KF)
    river_bank_guard(KF, river_mode(env))
    orig_lines, orig_wload = getattr(KF, 'trail_lines', None), getattr(KF, '_wload', None)
    if orig_lines is not None: KF.trail_lines = lambda: store_lines(KF, st, areas, orig_lines())
    if orig_wload is not None:   # the store's water tile first; else the bot's own last good copy (WATER_STORE) as today; else None = NOT SURE
        KF._wload = lambda i, jt: store_water(st, areas, i, jt) or orig_wload(i, jt)
    KF.download, KF.saved_us, KF.saved_ca, KF.live_load, KF.pc_tag = download, (lambda parks: saved_corridors(KF)), saved_ca, live_load, pc_tag
    KF.STORE = st; STORE_ON = True
    def rows_at_exit():
        try: write_rows()
        except LeakRefused: sys.stdout.flush(); sys.stderr.flush(); os._exit(EXIT_LEAK)   # at exit too: the run fails, nothing written
    atexit.register(rows_at_exit)   # written on every run, so an old list never outlives a filled gap
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
