#!/usr/bin/env python3
"""2-fer outlines from the OUTLINE STORE instead of downloads (KPC owner, 2026-11-13). OFF by default.

Why: the 2-fer bot runs out of memory in its download passes (Southeast, Great Lakes). Owner decision 'one door in': bots stop
downloading boundaries; a park the store does not have is HELD and listed, and only the store filler fetches.

Switch-over (KPC owner, 2026-11-15; fers rules d0064c860cba -> the next declared hash, scope 2026-11-15-store-switch): kpc_fers.main()
calls install() right after the hard-end clock is armed when the switch is on, and this file and .github/fers-store-areas.json are
2-fer RULE_FILES (kpc_key_freeze.py), so a later edit to either moves the 2-fer rules hash. Switch off: the hook imports nothing and
kpc_fers.py runs exactly as before.
Which areas (.github/fers-store-areas.json): "areas": "all-us-ca" = every US state and Canadian province area the store holds
(or a list of area codes), minus "except" (an area pulled back to the old path without a code change). US-KY never: the Kentucky
run reads Kentucky's own files (REGION ky). An area of a store run that is on the except list, or that the store does not hold
(no index, another format, stale, damaged), is left out of THIS run with a plain reason (its row in store-missing-<tag>.json) and
keeps its previous files; the other areas go on. No area left = exit 87. Parks filed under such an area are held, never downloaded.
Keep the old row (DEFAULT, owner question 1): a live candidate row that the store run would turn NOT SURE only because the PAD-US
closed areas or the ownership map could not be checked (a store run downloads nothing) keeps its old row, tagged
'kept: not checked in a store run', only when the old row is the same spot (same_spot: place and size); a row the store run
positively decides (water only, dropped, any other not-sure reason, water not checked too) is never kept. The good copies wait
between passes in a side file outside the data folder (store_prev_file), never in a row. Saved PAD-US answers are not used yet.
Rule scope 'none': a switch-off run re-tests nothing; a store run stamps its own areas' parks (STORE_STAMP) so they are re-tested once.
Never worse (OWNER RULE, KPC owner 2026-11-15, rule R12; scope 2026-11-15-store-fixes): on a PUBLIC store run a withheld park (a record
of it, or its line record, not publishable) keeps its rows of the previous public file UNCHANGED, marked 'not re-checked (outline held
privately)' and counted per area (carry_held_rows); nothing else names it. withheld_refs() is the whole set every public file is guarded
with, and secret_refs() (the KPC-Store push check's list) is the same whole set (grade of #204, D3): the push check lets a carried row
through only as the exact row of the previous public file, and scans for the park everywhere else. Each process writes its whole list
to <private folder>/store-withheld/ (kpc_fers_expected.py reads it; store-missing gives the run's total).

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
  Every area named for the run must be on the store list or be left out with its reason; a run that names no area (STATES) is
  refused (exit 87): a whole-region store run could rewrite the files of an area that is pulled back to the old path.
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
  kpc_fers_store.py run                                     KPC_FERS_FROM_STORE=on only: kpc_fers.main() (its hook installs the store)
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
MAIN_LINES = {}    # ref -> why its line is taken from data/trails exactly as on main (the coarse NPS water routes)
LINE_SKIPPED = {}  # ref -> why its store line is not used (by-name, coarse route, unknown bank status): counted, listed privately
GEOM_SKIPPED = {}  # format 4: ref -> {geometry kind: records} left out of the park's AREA outline (lines, pins, unknown kinds)
STORE_LINES = {}   # format 4: ref -> the line entry (kpc_fers.py LN form) whose geometry came from the store
LINE_ROWS = {}     # area -> live trail / river rows (pairs that depend on the 100-ft line rule) in this run's files
WATER_READ = {'store': 0, 'not in store': 0, 'store tile refused': 0}
RIVER_SWITCH = 'KPC_FERS_RIVER_NO_BANK'   # centreline (default: today's rule, unchanged) | tiers (PROVISIONAL, the owner's Nov 14 ruling)
RIVER_NO_BANK = {'mode': 'centreline', 'catch_m': 250.0, 'half_m': 150.0, 'along_m': 50.0}
RIVER_TIERS = {}   # tier -> stretches / rows this run (tiers mode)
# KPC owner, 2026-11-15 (switch-over): which areas use the store. A 2-fer rule file (kpc_key_freeze.RULE_FILES['fers']).
STORE_AREAS_FILE = pathlib.Path(__file__).resolve().parents[1] / 'fers-store-areas.json'
STORE_AREA_RX = re.compile(r'(US|CA)-[A-Z]{2}')
STORE_ALL = 'all-us-ca'
NEVER_STORE = {'US-KY': 'Kentucky runs on its own files (the REGION ky run), never on the outline store'}
KEPT_TAG = 'kept: not checked in a store run'
STORE_STAMP = '2026-11-15-store-switch'   # the declared rule change (.github/fers-rule-scope.json): stamped only in a store run
KEPT = {'n': 0}    # rows kept by the keep-the-old-row rule this run
AREA_FILE = re.compile(r'((?:US|CA|W)-[A-Z]{2})\.json(?:\.gz)?')
AREA_OFF = {'fn': None}    # install(): area -> '' or why it does not use the store in this run (its spot file is never written)
SKIPPED_FILES = {}         # area -> why its spot file was left as it was (a border area that does not use the store)
WORLD_ON = {'on': False}   # a world store run ("world": "on" in .github/fers-store-areas.json, a private store run only)
RIVER_TODO = []    # tiers mode: river + park stretches the bank store must fetch (ids, distances, signs; no geometry)
TIER_BANK, TIER_CENTRE = 'bank', 'park reaches the river centre line'
TIER_ALONG, TIER_LINE = 'bank assumed from the park boundary (no official bank shape yet)', 'about 100 ft from the centre line'


def river_mode(env=None):
    env = os.environ if env is None else env
    v = str(env.get(RIVER_SWITCH) or '').strip().lower()
    for k, e in (('catch_m', 'KPC_FERS_RIVER_CATCH_M'), ('half_m', 'KPC_FERS_RIVER_HALF_M')):
        RIVER_NO_BANK[k] = env_float(env, e, RIVER_NO_BANK[k])
    return 'tiers' if v == 'tiers' else 'centreline'


def env_float(env, name, default, hi=1e7):
    """A positive, finite number from the environment; anything else (nan, inf, 0, negative, text) keeps the default."""
    try: v = float(str(env.get(name) or '').strip() or default)
    except ValueError: return default
    return v if math.isfinite(v) and 0 < v <= hi else default


def kind_of(r):
    """A record's geometry kind (format 4). Absent = 'area' (every format-3 record); an unknown value is NOT an area."""
    k = r.get('geometry_kind') if isinstance(r, dict) else None
    return 'area' if k in (None, '') else str(k)


class NoDownload(OSError):
    """Store run: the outline store is the only door. Raised instead of any network request (an OSError, so every existing
    'the map did not answer' path in kpc_fers.py takes it: held / NOT SURE, never a guess)."""


class LeakRefused(SystemExit):
    """The write guard refused a file. A SystemExit (not an Exception) so no 'except Exception' in kpc_fers.py can swallow it:
    the run fails rather than write a club-room-only row, a private park, a world 2-fer or a blocked build to a public file.
    The message names NO park, record, licence or path detail: Actions logs of a public repo are public. Only the number of
    problems and their kinds are printed; the details go to the private log (private folder) when there is one."""
    def __init__(self, why, kinds=None):
        whys = why if isinstance(why, list) else [why]
        kinds = sorted(set(kinds or ['refused']))
        private_note('write refused', whys)
        msg = (f'{len(whys)} problem(s) would have gone into a public file ({", ".join(kinds)}); the details are only in the private log'
               if PRIVATE_LOG_DIR else f'{len(whys)} problem(s) would have gone into a public file ({", ".join(kinds)}); no private log is set, so no detail is kept')
        public_print(f'::error title=2-fer outline store: write refused::{msg}. Nothing more is written; the area keeps its previous files.')
        super().__init__(EXIT_LEAK)
        self.why, self.kinds = whys, kinds


PRIVATE_LOG_DIR = None   # the private folder (private run) or KPC_FERS_PRIVATE_LOG (public run): details that must never be printed
_REAL_OUT = {'out': sys.stdout, 'err': sys.stderr}


def public_print(text):
    """The only printing this module does in a run: counts and generic reasons, never a park (see install: private runs send
    every other line of the process to the private log)."""
    try: print(text, file=_REAL_OUT['out'], flush=True)
    except Exception: pass  # noqa: BLE001


def private_note(what, lines):
    """Details (refs, reasons, licence classes) into the private log only; nowhere when there is no private folder."""
    if not PRIVATE_LOG_DIR: return
    try:
        with open(pathlib.Path(PRIVATE_LOG_DIR) / 'private-log.txt', 'a', encoding='utf-8') as fh:
            for x in lines: fh.write(f'{datetime.datetime.now().isoformat(timespec="seconds")} {what}: {x}\n')
    except OSError: pass


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
        self.allow = None   # install(): area -> '' (the store may be read) or the plain reason it is not (.github/fers-store-areas.json)

    @classmethod
    def from_env(cls, env):
        return cls(env.get('KPC_FERS_STORE_DIR') or 'store', int(env.get('KPC_FERS_STORE_MAX_DAYS') or 45), kind=str(env.get('KPC_FERS_STORE_KIND') or 'public').strip().lower())

    def area(self, area):
        if area in self.areas or area in self.why: return self.areas.get(area)
        no = self.allow(area) if self.allow is not None else ''
        if no: self.why[area] = f'the outline store for {area} is not used ({no})'; return None
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
        if not hasattr(self, '_names'): self._names = sorted(n for n in (p.name[6:-5] for p in self.dir.glob('index-*.json')) if self.allow is None or not self.allow(n))
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
            if isinstance(p.get('name'), str): NAMES.setdefault(ref, p['name'])
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
        if not str(s.get('status') or '').startswith('not sure: water not checked'): continue
        if s.get('check_failed'): s['status'] = 'not sure: ' + s['check_failed'] + ': run again'; n += 1
        elif s.get('closed_check'):
            s['status'] = 'not sure: closed areas not checked (' + s['closed_check'][len('not checked: '):] + '): the store must carry them first'; n += 1
            if s.get('closed_check_water') == 'ok': s['store_not_checked'] = 'closed areas'   # land, open, water checked: only rule 10 could not run
    return n


OWNER_NOT_CHECKED = ('not sure: the agency ownership map did not answer',)   # kpc_fers.decide(): a store run asks no ownership map


def owner_status(doc):
    """Store run: a row NOT SURE only because the ownership map could not be read (the shut door refuses it) is marked for the
    keep-the-old-row rule. decide() stops at that check, so nothing else decided the row."""
    n = 0
    for s in (doc or {}).get('spots') or []:
        if str(s.get('status') or '').startswith(OWNER_NOT_CHECKED) and not s.get('store_not_checked'): s['store_not_checked'] = 'ownership'; n += 1
    return n


def _good(s):
    st = str(s.get('status') or '')
    return st.startswith(('candidate', 'very tight'))


def _old_match(s, by_id, by_pk):
    o = by_id.get(s.get('id')) if s.get('id') else None
    if o is None or _pk(o) != _pk(s):
        c = by_pk.get(_pk(s)) or []
        o = c[0] if len(c) == 1 else None
    return o


def _prev_of(o):
    """The good copy an old row stands for: the row itself when it is a live candidate (never a club-room row)."""
    if o is None or not _good(o) or o.get('club_room_only'): return None
    return {k: v for k, v in o.items() if k != 'store_prev'}


def _extent(s):
    """[lon0, lat0, lon1, lat1] of a row: its box, else its shape's box; None when the row has neither."""
    b = s.get('box')
    if isinstance(b, (list, tuple)) and len(b) == 4 and all(isinstance(v, (int, float)) for v in b): return [float(v) for v in b]
    pts = [q for q in s.get('shape') or [] if isinstance(q, (list, tuple)) and len(q) >= 2 and all(isinstance(v, (int, float)) for v in q[:2])]
    if not pts: return None
    return [min(q[0] for q in pts), min(q[1] for q in pts), max(q[0] for q in pts), max(q[1] for q in pts)]


def _centre(s):
    c = s.get('center')   # kpc_fers.py rows: [lat, lon]
    if isinstance(c, (list, tuple)) and len(c) == 2 and all(isinstance(v, (int, float)) for v in c): return float(c[1]), float(c[0])
    return None


def _in_box(pt, b, pad=1e-6):
    return pt is not None and b is not None and b[0] - pad <= pt[0] <= b[2] + pad and b[1] - pad <= pt[1] <= b[3] + pad


SAME_SIZE = 1.25   # the larger size (acres; metres of line for a trail / river row) at most 1.25 times the smaller, both ways
SAME_BOX = 2.0     # the old and new boxes: width and height each within a factor of 2 (a huge old box never matches a small spot)
BOX_FLOOR = 1e-4   # degrees (about 10 m): a box side below this counts as this (a straight east-west line has no height)


def same_spot(new, old):
    """'' when the old row is the SAME spot as the new one (grade of #201): the old centre lies inside the new spot's extent or the new
    centre inside the old one's; the boxes have the same size (width and height each within SAME_BOX); AND the sizes agree (the
    larger at most SAME_SIZE times the smaller: acres for an area row, len_m for a line row). Else the reason it is not. A row that
    carries no place, no box or no size is never the same spot. The rows carry no outline checksum, so this test is the rule."""
    if _pk(new) != _pk(old): return 'another pair or kind'
    nc, oc, ne, oe = _centre(new), _centre(old), _extent(new), _extent(old)
    if not (_in_box(oc, ne) or _in_box(nc, oe)): return 'the spot moved' if (nc and oc and (ne or oe)) else 'no place to compare'
    if ne is None or oe is None: return 'no box to compare'
    for i, side in ((0, 'width'), (1, 'height')):
        a_, b_ = max(ne[i + 2] - ne[i], BOX_FLOOR), max(oe[i + 2] - oe[i], BOX_FLOOR)
        if max(a_, b_) > SAME_BOX * min(a_, b_): return f'the spot changed shape (box {side})'
    key = 'acres' if new.get('kind') == 'area' else 'len_m'
    a, b = new.get(key), old.get(key)
    if not (isinstance(a, (int, float)) and isinstance(b, (int, float)) and a > 0 and b > 0): return f'no {key} to compare'
    if max(a, b) > SAME_SIZE * min(a, b): return f'the spot changed size ({b} -> {a} {key})'
    return ''


def keep_old_rows(new, old, today=None, final=True, carry=None):
    """KPC owner, 2026-11-15 (DEFAULT, owner question 1: keep the old row; saved PAD-US answers are not used yet). Never replace a good
    copy with a worse one: a row this store run left NOT SURE only because closed areas / ownership were not checked
    ('store_not_checked', set by closed_status() / owner_status()) is replaced by the last good copy of the SAME spot, tagged
    'kept: not checked in a store run' with the reason. The good copy is the previous file's live candidate row of the same id (else
    the only live row of the same pair and kind), and it is used only when same_spot() says it is the same place and size: a spot
    that moved or changed size keeps this run's NOT SURE row. A row the store run decided (water only, dropped, any other not-sure
    reason, the water not checked either) carries no mark and is never replaced; a row that was not a live candidate is never
    brought back (so a row not kept once is never kept by a later run).
    carry = {row id: good copy}: passes 1 and 2 rewrite every row ('pass 1', 'pass 2') before pass 3 decides it, so the good copies
    travel from pass to pass in a side file outside the data folder (install: store_prev_file), never in a row; carry is filled for
    the next pass (final=False) and not used after the final pass. Returns the number of rows kept."""
    if not isinstance(new, dict): return 0
    carry_in = dict(carry or {})
    if carry is not None: carry.clear()
    olds = [x for x in (old or {}).get('spots') or [] if isinstance(x, dict) and _live(x)] if isinstance(old, dict) else []
    by_id = {x.get('id'): x for x in olds if x.get('id')}
    by_pk = {}
    for x in olds: by_pk.setdefault(_pk(x), []).append(x)
    c_pk = {}
    for v in carry_in.values():
        if isinstance(v, dict): c_pk.setdefault(_pk(v), []).append(v)
    used, n, spots = set(), 0, new.get('spots') or []
    for i, x in enumerate(spots):
        if not isinstance(x, dict): continue
        x.pop('store_prev', None)
        prev = carry_in.get(x.get('id')) if isinstance(carry_in.get(x.get('id')), dict) and _pk(carry_in[x.get('id')]) == _pk(x) else None
        if prev is None and len(c_pk.get(_pk(x)) or []) == 1: prev = c_pk[_pk(x)][0]
        if prev is None:
            o = _old_match(x, by_id, by_pk)
            prev = _prev_of(o) if o is not None and id(o) not in used else None
            if prev is not None: used.add(id(o))
        if prev is not None and x.get('store_not_checked') and str(x.get('status') or '').startswith('not sure') and _good(prev):
            why = same_spot(x, prev)
            if why: x['not_kept'] = f'the last candidate row is not this spot ({why}): this run\'s answer stands'
            else:
                k = json.loads(json.dumps(prev))
                k['kept'] = KEPT_TAG
                k['kept_why'] = f"{x['store_not_checked']} not checked in a store run (this run said: {str(x.get('status'))[:160]})"
                k['kept_on'] = today or True
                spots[i] = k; n += 1
                if carry is not None and not final and k.get('id'): carry[k['id']] = prev
                continue
        if carry is not None and not final and prev is not None and _live(x) and x.get('id'): carry[x['id']] = prev
    KEPT['n'] += n
    return n


HELD_TAG = 'not re-checked (outline held privately)'
CARRIED = {}       # area -> rows carried unchanged by carry_held_rows in the last save of this process (every status)
CARRIED_LIVE = {}  # area -> of those, the live ones (candidate, very tight, water only, not sure ...: not dropped or merged)
CARRIED_JSON = {}  # area -> the exact JSON of each carried row: the write step lets exactly these through (nothing else naming the park)


def _canon(x): return json.dumps(x, sort_keys=True, ensure_ascii=False, default=str)


def held_refs_file(KF, area):
    """The private side file with the withheld refs of an area's carried rows (between passes), next to the store-prev side file."""
    f = store_prev_file(KF, area)
    return None if f is None else f.parent.parent / 'store-held' / f'{area}.json'


def carry_held_rows(KF, d, old):
    """OWNER RULE 'never worse' (KPC owner, 2026-11-15; store trial M2 + M3). On a PUBLIC store run a withheld park (a record of it is
    not publishable, or its line record is not) is never read, so its pairs cannot be tested. Its existing public rows must not
    vanish: every row of the previous PUBLIC file that names such a park is carried UNCHANGED (only the mark store_held =
    'not re-checked (outline held privately)' is added) and counted; no row naming it is computed or added from anything else, and
    nothing about it goes into any other row or file (the write step lets only these exact copies through). Pass 1 takes the rows
    from the previous public file; passes 2-5 take the marked rows of the file pass 1 wrote (the exact copies; whatever a pass did to
    them in memory is thrown away). Returns the number of rows carried."""
    if not isinstance(d, dict) or not d.get('st'): return 0
    area = d['st']
    hf = held_refs_file(KF, area)
    sec = set(withheld_refs())
    if int(getattr(KF, 'PASS', 1)) == 1:
        orig = [json.loads(_canon(x)) for x in (old or {}).get('spots') or [] if isinstance(x, dict) and set(x.get('refs') or []) & sec]
        for x in orig: x['store_held'] = HELD_TAG
        held = sorted({r for x in orig for r in x.get('refs') or [] if r in sec})
        if hf is not None:
            try:
                hf.parent.mkdir(parents=True, exist_ok=True); hf.write_text(json.dumps({'refs': held}), encoding='utf-8')
            except OSError: pass
    else:
        orig = [json.loads(_canon(x)) for x in (old or {}).get('spots') or [] if isinstance(x, dict) and x.get('store_held') == HELD_TAG]
        held = sorted(set(_read_json(hf).get('refs') or []) if hf is not None and hf.is_file() else set())
        sec |= set(held)
    keep = [x for x in d.get('spots') or [] if not (isinstance(x, dict) and (x.get('store_held') or set(x.get('refs') or []) & sec))]
    d['spots'] = keep + orig
    CARRIED[area] = len(orig); CARRIED_LIVE[area] = sum(1 for x in orig if _live(x))
    CARRIED_JSON[area] = {_canon(x) for x in orig}
    CARRIED_PUBLIC.update(r for x in orig for r in x.get('refs') or [] if r in sec)
    return len(orig)


def store_prev_file(KF, area):
    """Where the good copies of a store run's rows wait between passes: the private folder (a private run's own folder, or
    KPC_FERS_PRIVATE_LOG on a public run), else KPC_FERS_LIVE_DIR (cache/fers), never under the data folder kpc_fers.py writes
    (data/fers is published). None when no such folder exists (then only the previous file is compared, as in pass 3)."""
    if PRIVATE_OUT is not None: return pathlib.Path(PRIVATE_OUT) / 'store-prev' / f'{area}.json'   # a private run: its own folder only
    out = pathlib.Path(getattr(KF, 'OUT', 'data/fers')).resolve()
    for base in (PRIVATE_LOG_DIR, os.environ.get('KPC_FERS_LIVE_DIR') or 'cache/fers'):
        if not base: continue
        d = pathlib.Path(base).resolve() / 'store-prev'
        if _inside(d, out) or _inside(out, d): continue
        return d / f'{area}.json'
    return None


def _read_json(p):
    try: return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
    except Exception: return {}  # noqa: BLE001


def _write_carry(p, carry):
    p = pathlib.Path(p)
    try:
        if not carry: p.unlink(missing_ok=True); return
        p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(carry, ensure_ascii=False), encoding='utf-8')
    except OSError: pass


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
        if 'm' in p and not WORLD_ON['on']:
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
            if PRIVATE_WHY.search(why) and store.kind != 'private':
                HELD_PRIVATE.add(ref); continue   # held for licence / WDPA: never named in a public file or log (no MISSING_SAVED entry)
            KF.MISSING_SAVED[ref] = f'the outline store ({why}; flagged for the store filler)'
            continue
        FLAGS.pop(ref, None)
        ok.append(ref); boxes[ref] = list(info['box'])
        if info.get('private'): PRIVATE[ref] = info['private']
        else: READ_OK.add(ref)   # read from publishable records only: may be named
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


def _dicts(obj):
    """Every dict at ANY depth (iterative: no depth limit, no recursion limit)."""
    st = [obj]
    while st:
        o = st.pop()
        if isinstance(o, dict): yield o; st.extend(o.values())
        elif isinstance(o, (list, tuple)): st.extend(o)


HELD_PRIVATE = set()   # parks with records that are not publishable or are WDPA-derived (from the store index, ALL parks of the run's areas)
READ_OK = set()        # parks read on THIS run from publishable records only (they may be named)
READ_OK_RUN = set()    # KPC owner, 2026-11-15 (trial 2, CT): parks an EARLIER pass of this area's run read from publishable records only
WITHHELD = {'parks': 0, 'items': 0}   # anonymous counts: what the public files leave out
PRIVATE_WHY = re.compile(r'needs the private store|WDPA|Protected Planet|not publishable', re.I)
REFLIKE = re.compile(r'^[A-Za-z0-9]{1,4}-\d{1,6}$')
ROW_KEYS = ('refs', 'ref', 'pair', 'pairs', 'park', 'other', 'parks_in')


def withheld_refs():
    """The parks a PUBLIC file must never name: held or used for unpublishable / WDPA-derived records, unless this run read them
    from publishable records only. Every public file this module guards (redact, guard_write, the log filter, store-missing) uses
    this whole set; the only exception is a carried row (carry_held_rows): an unchanged copy of a row the previous PUBLIC file
    already had."""
    return (HELD_PRIVATE | set(PRIVATE)) - READ_OK - READ_OK_RUN


CARRIED_PUBLIC = set()   # withheld parks whose rows the previous public file already named (carried unchanged: carry_held_rows)


def secret_refs():
    """The list the KPC-Store push check scans every changed file for (keeper/fers_bot_run.py writes it at exit): the whole
    withheld_refs() set, parks of carried rows included (grade of #204, D3). A carried row (carry_held_rows) is let through by the
    push check only as the exact row of the previous public file (store_held mark aside); every other mention is refused."""
    return withheld_refs()


# the name guard (grade of #201): words that never make a name distinctive on their own (park kinds and plain place words)
COMMON_NAME_WORDS = frozenset((
    'the of and at on in de du des la le les el los las st saint ste mt mount fort ft '
    'park parks state national provincial regional county city municipal community memorial historic historical heritage site sites '
    'area areas recreation recreational wildlife management wma game fish land lands forest forests nf woods wood preserve reserve '
    'nature natural conservation refuge sanctuary wilderness scenic monument battlefield trail trails greenway river rivers creek '
    'lake lakes pond reservoir dam island islands beach bay coast shore marsh swamp wetland wetlands mountain mountains hill hills '
    'valley canyon falls spring springs north south east west upper lower big little new old grand great green').split())


def norm_name(t):
    """Case, accents, hyphens, spacing and punctuation all fold away: 'Zxsecret-Inner  Park' -> 'zxsecret inner park'."""
    import unicodedata
    t = unicodedata.normalize('NFKD', str(t or ''))
    t = ''.join(c for c in t if not unicodedata.combining(c)).lower()
    return ' '.join(re.findall(r'[a-z0-9]+', t))


def distinctive(n):
    """A name the guard looks for: at least two words, and at least one word that is not a common park / place word (so 'Park',
    'Lake Park' or 'State Park' never stop a run)."""
    w = n.split()
    return len(w) >= 2 and any(x not in COMMON_NAME_WORDS and not x.isdigit() for x in w)


NAMES = {}          # ref -> the park's name as the store gives it (index entry or park piece): to find a secret park's NAME in text
KF_REF = {'kf': None}   # install(): the kpc_fers module (its POTA pin list gives the other names)
_NAME_CACHE = {}


def _all_names():
    """ref -> normalised names, for every park known to this run (the store and kpc_fers.py's POTA pin list)."""
    pins = getattr(KF_REF['kf'], 'PINS', None) or {}
    out = {}
    for r, v in pins.items():
        if isinstance(v, (list, tuple)) and v and isinstance(v[0], str): out.setdefault(r, set()).add(norm_name(v[0]))
    for r, n in NAMES.items(): out.setdefault(r, set()).add(norm_name(n))
    return out


def secret_names(refs=None):
    """(the normalised names a public file must never carry, the public names that contain one of them). A name is looked for only
    when it is distinctive() and NO park outside the secret set has the same name (a public namesake: the ref guard still protects
    the withheld park). Public names that contain a secret name (secret 'Pine Ridge', public 'Pine Ridge Forest') are masked before
    the scan, so they never stop a run."""
    sec = set(secret_refs() if refs is None else refs)
    if not sec: return set(), set()
    key = (frozenset(sec), len(NAMES), len(getattr(KF_REF['kf'], 'PINS', None) or {}))
    if key in _NAME_CACHE: return _NAME_CACHE[key]
    allm = _all_names()
    pub = {n for r, ns in allm.items() if r not in sec for n in ns if n}
    out = {n for r in sec for n in allm.get(r, ()) if n and distinctive(n) and n not in pub}
    mask = {p for p in pub for n in out if f' {n} ' in f' {p} '}
    _NAME_CACHE.clear(); _NAME_CACHE[key] = (out, mask)
    return out, mask


def _no_ref_names(obj):
    """obj without the ref-keyed 'names' maps of rows ({ref: name}): those are checked by ref (a public park whose name equals a
    secret park's must not stop the run); every other text is scanned for secret names."""
    if isinstance(obj, dict):
        return {k: _no_ref_names(v) for k, v in obj.items()
                if not (k == 'names' and isinstance(v, dict) and all(REFLIKE.match(str(x)) for x in v))}
    if isinstance(obj, (list, tuple)): return [_no_ref_names(v) for v in obj]
    return obj


def _strings(obj):
    st = [obj]
    while st:
        o = st.pop()
        if isinstance(o, str): yield o
        elif isinstance(o, dict): st.extend(o.values()); st.extend(k for k in o if isinstance(k, str))
        elif isinstance(o, (list, tuple)): st.extend(o)


def name_hits(doc, names, mask):
    """The secret names found in any text of doc: whole words, after norm_name on both sides, masked public names taken out first."""
    hits = set()
    if not names: return hits
    for t in _strings(_no_ref_names(doc)):
        n = f' {norm_name(t)} '
        for m in sorted(mask, key=len, reverse=True):
            while f' {m} ' in n: n = n.replace(f' {m} ', ' ')
        for x in names:
            if f' {x} ' in n: hits.add(x)
    return hits


def _ref_rx(refs):
    refs = sorted({str(r) for r in refs if r}, key=len, reverse=True)
    return re.compile('(?:' + '|'.join(re.escape(r) for r in refs) + r')(?!\d)', re.I) if refs else None


def redact(doc, refs=None):
    """A public file never names a secret park (see secret_refs): a dict key that is such a ref, and any list item (row, entry,
    log line, [ref, name] pair) that mentions one, is left out; a text value that mentions one becomes '[withheld]'. Returns
    (doc, items left out). The write guard checks the result again."""
    rx = _ref_rx(withheld_refs() if refs is None else refs)
    if rx is None or not rx.search(json.dumps(doc, default=str, ensure_ascii=False)): return doc, 0
    n = [0]
    def walk(o):
        if isinstance(o, dict):
            out = {}
            for k, v in o.items():
                if rx.fullmatch(str(k)) or (rx.search(str(k)) and REFLIKE.match(str(k).split('+')[0])): n[0] += 1; continue
                if isinstance(v, str) and rx.search(v): out[k] = '[withheld]'; n[0] += 1; continue
                out[k] = walk(v)
            return out
        if isinstance(o, (list, tuple)):
            keep = []
            for v in o:
                if rx.search(json.dumps(v, default=str, ensure_ascii=False)): n[0] += 1; continue
                keep.append(walk(v))
            return keep
        return o
    return walk(doc), n[0]


def guard_write(path, doc, private=None, names=None):
    """THE WRITE STEP of a store run: every file kpc_fers.py saves (spot files, reuse, report, looked, missing, same-outline ...)
    and the store-missing list pass here first. Raises LeakRefused (the run fails, nothing is written) when the file
      - names a build that is never released (BLOCKED_BUILDS: as text or as a number), in any file;
      - is outside the private folder, on a private store run (every file of such a run is club room only);
      - is a public file and holds a row marked club_room_only (any depth), a row naming a park that is not US / Canada (world
        2-fers stay off the public site; any row shape: refs, ref, pair, pairs, park, other), or ANY mention (any case, any
        neighbour character) of a park held or used for records that are not publishable or are WDPA-derived.
    names = (normalised secret names, masked public names) when the caller has them from a list (another process: kpc_fers_expected.py).
    Every problem is counted; the message names none of them (LeakRefused)."""
    private = withheld_refs() if private is None else set(private)
    txt = json.dumps(doc, default=str, ensure_ascii=False)
    probs, kinds = [], set()
    for b in sorted(BLOCKED_BUILDS):
        if re.search(re.escape(b) + r'(?!\d)', txt, re.I) or re.search(r'(?<!\d)' + re.escape(b.split('-', 1)[1]) + r'(?!\d)', txt):
            probs.append(f'{path}: it names {b}, which is never released'); kinds.add('never-released build')
    if PRIVATE_OUT is not None:
        if not _inside(path, PRIVATE_OUT): probs.append(f'{path}: a private store run writes only into its private folder'); kinds.add('private run writing outside its folder')
        if probs: raise LeakRefused(probs, kinds)
        return
    for d in _dicts(doc):
        if d.get('club_room_only') or 'club_room_why' in d:
            probs.append(f"{path}: a row marked club_room_only ({'+'.join(map(str, d.get('refs') or [])) or '?'})"); kinds.add('club-room-only row')
        for k in ROW_KEYS:
            v = d.get(k)
            vals = v if isinstance(v, (list, tuple)) else [v]
            for x in vals:
                for r in (str(x).split('+') if isinstance(x, str) else []):
                    r = r.strip()
                    if REFLIKE.match(r) and not PUBLIC_REF.fullmatch(r.split('@')[0]):
                        probs.append(f'{path}: a row naming {r}, a park outside the US and Canada'); kinds.add('world park in a row')
    rx = _ref_rx(private)
    if rx is not None:
        for m in sorted({m.group(0).upper() for m in rx.finditer(txt)}):
            probs.append(f'{path}: it names {m}, held or used for records that are not publishable'); kinds.add('park with unpublishable records')
    # grade of #201 (item 3): a secret park's NAME in any text (a note of a carried old row, a log line), not only its ref
    nm, mask = secret_names(private) if names is None else (set(names[0]), set(names[1]))
    for m in sorted(name_hits(doc, nm, mask)):
        probs.append(f'{path}: it names the park "{m}", held or used for records that are not publishable'); kinds.add('park name with unpublishable records')
    if any('store_prev' in d for d in _dicts(doc)):
        probs.append(f'{path}: a row carries a store_prev copy (it stays in the side file)'); kinds.add('carried copy in a row')
    if probs: raise LeakRefused(probs, kinds)


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
            except Exception as e:  # noqa: BLE001  any error in a store run = NOT SURE, never 'ok' (kpc_fers.py's caller would say ok)
                s['check_failed'] = f'the land check stopped with an error ({type(e).__name__})'; CLOSED_NOT_CHECKED['n'] += 1
                return 'not checked'
            finally: KF.pad_closed = _no_closed
            if asked:   # the overlap needed the closed-area check and it could not run: never confirmed
                CLOSED_NOT_CHECKED['n'] += 1
                s['closed_check_water'] = r   # what the rest of the land check said ('ok' / 'water' / 'not checked'): only 'ok' may keep an old row
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
            m = AREA_FILE.fullmatch(pathlib.Path(p).name)
            off = AREA_OFF['fn'](m.group(1)) if m and AREA_OFF['fn'] is not None else ''
            if off:   # an area that does not use the store in this run (except list, not held, stale ...): its file stays as it was
                SKIPPED_FILES[m.group(1)] = off; return None
            if isinstance(d, dict) and pathlib.Path(p).name.startswith('report') and STORE_ON: d = dict(d, outline_store=store_counts())
            carried = []
            if PRIVATE_OUT is None and m and isinstance(d, dict) and CARRIED_JSON.get(m.group(1)) and isinstance(d.get('spots'), list):
                # the 'never worse' rows (carry_held_rows): exact copies of the previous public file's rows, checked on their own (no
                # club-room row, no world park, no never-released build), then put back; any other row naming the park is left out
                allow = CARRIED_JSON[m.group(1)]
                carried = [x for x in d['spots'] if isinstance(x, dict) and x.get('store_held') == HELD_TAG and _canon(x) in allow]
                if carried:
                    d = dict(d, spots=[x for x in d['spots'] if not (isinstance(x, dict) and x.get('store_held') == HELD_TAG and _canon(x) in allow)])
                    guard_write(p, {'spots': carried}, private=set(), names=(set(), set()))
            if PRIVATE_OUT is None:   # a public file: a park held or used for unpublishable / WDPA records is left out (counted only)
                d, n = redact(d); WITHHELD['items'] += n
            guard_write(p, d)
            if carried: d = dict(d, spots=list(d.get('spots') or []) + carried)
            out = raw(p, d, *a, **k)
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
    its widths are kpc_fers.py's (100 ft: 30.48 m from a centre line or from a river's bank, Nov 14, with the station 5 m inside
    the other park; a 25 m stretch). A line park whose line is not in the store is HELD (one door in); a line park the store has
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
    # C1 (store trial, KPC owner 2026-11-15): a data/trails line park far from this run's areas (its line's box more than NEAR_LINE_DEG
    # from the box of the run's own park pins) is still read when the store has it (pairs exactly as before), but when the store
    # does not have it, it is not listed as held: every run listed about 370 such North American line parks
    near = _near_run(KF, areas)
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
        meta = base.get(ref) or {}
        kind, not_sure = None, ''
        if not bad and rec:
            rules = {str(r.get('boundary_rule') or '') for r in rec} - {''}
            rcls = {str(r.get('river_class') or '') for r in rec} - {''}
            banks = {str(r.get('bank_status') or '') for r in rec} - {''}
            if 'designated_corridor_area' in rules or 'designated_corridor' in rcls:
                bad = f'{ref}: a designated-corridor river: its AREA is its official corridor polygon, which the store does not hold (the line is never its boundary)'
            elif 'unclear_river_class' in rules or 'unclear' in rcls:
                bad = f'{ref}: the river class is not sorted yet in the store (no boundary rule applied)'
            elif len(rules) > 1:
                bad = f'{ref}: its line records disagree on the boundary rule'
            elif 'line_missing' in banks:
                bad = f'{ref}: the store says its official line is missing'
            else:
                kind = {'trail_100ft': 'trail', 'river_100ft_from_bank': 'river'}.get(next(iter(rules), '')) or (meta.get('kind') if not rules else None)
                if kind is None: bad = f'{ref}: its store line has no boundary rule this bot knows' + (f' ({next(iter(rules))})' if rules else '')
            if not bad:   # owner ruling 2026-11-14: these lines are SKIPPED (counted; a 'river candidate: needs a look' row in the private folder only)
                skip = ''
                if (any(b.startswith('route line too coarse') for b in banks) or 'historic_route' in rcls) and ref in base:
                    # the four NPS water routes (US-4572, US-3791, US-4567, US-4581): treated exactly as on main (their data/trails
                    # line and today's water-route rule), never from the store's line
                    out[ref] = dict(base[ref]); MAIN_LINES[ref] = 'coarse NPS route: line and rule as on main'; FLAGS.pop(ref, None); continue
                if any(r.get('source') == 'nhd-by-name' or r.get('line_extent') for r in rec):
                    skip = 'its river line was found on USGS NHD by name: the park may be only a stretch of it'
                elif any(b.startswith('route line too coarse') for b in banks) or 'historic_route' in rcls:
                    skip = 'its route line is too coarse for a bank test'
                elif kind == 'river' and banks - {'covered', 'bank_not_needed', 'bank_missing'}:
                    skip = 'its bank status is ' + ', '.join(sorted(banks - {'covered', 'bank_not_needed', 'bank_missing'}))
                elif kind == 'river' and not banks:
                    skip = 'the store gives no bank status for this river line'
                if skip:
                    LINE_SKIPPED[ref] = skip; FLAGS[ref] = f'{ref}: line skipped: {skip}'; continue
        if not bad and rec:
            priv = {str(r.get('key')): {'licence_class': str(r.get('licence_class') or 'NOT RECORDED'), 'publish_basis': str(r.get('publish_basis') or 'none'),
                                        'private_reason': str(r.get('private_reason') or '')} for r in rec if not (r.get('publishable') is True and r.get('publish_basis') in PUBLISH_BASES)}
            if priv and st.kind == 'public': bad = f'{ref} needs the private store (line records not publishable: ' + ', '.join(f"{k} {v['licence_class']}" for k, v in sorted(priv.items())[:4]) + ')'
            elif priv: PRIVATE[ref] = priv
        if bad:
            if PRIVATE_WHY.search(bad): HELD_PRIVATE.add(ref); FLAGS[ref] = bad   # never named in a public file, nor in the log
            elif ref in base and not seen_area(st, areas, ref) and not near(base[ref]):
                FAR_LINES['n'] += 1   # far from the run: not this run's to list (counted only)
            else: FLAGS[ref] = bad; KF.LOG.append(f'outline store line: {bad[:120]}')
            continue
        if not rec: continue
        if not PRIVATE.get(ref): READ_OK.add(ref)
        ls = [ring_floats(e) for r in rec for e in (r.get('lines') or [])]
        ls = [x for x in ls if len(x) > 1]
        if not ls:
            if ref in base: FLAGS[ref] = f'{ref}: its line records in the outline store have no usable path'
            continue
        e = {'lines': ls, 'kind': kind,   # from the record's boundary_rule (never the park's name); data/trails only when the record has none
             'by': meta.get('by') or '; '.join(sorted({str(r.get('credit_line') or '') for r in rec} - {''})) or 'outline store',
             'type': meta.get('type') or str(rec[0].get('boundary_kind') or ''), 'date': min(str(r.get('date') or (park or {}).get('date') or '') for r in rec) or st.today,
             'from': 'outline store', **({'not_sure': not_sure} if not_sure else {}),
             **({'bank_missing': True} if kind == 'river' and any(r.get('bank_missing') is True or r.get('bank_status') == 'bank_missing' for r in rec) else {}),
             **({'boundary_rule': str(rec[0].get('boundary_rule'))} if rec[0].get('boundary_rule') else {})}
        if meta.get('water_parts'):
            if len(meta['lines']) == len(ls): e['water_parts'] = meta['water_parts']
            else: KF.LOG.append(f'{ref}: the store line has {len(ls)} pieces, data/trails {len(meta["lines"])}: its water / land split is not carried (bank test only, not sure)')
        out[ref] = e; STORE_LINES[ref] = e; FLAGS.pop(ref, None); seen.add(ref)
    return out


NEAR_LINE_DEG = 1.0   # about 100 km: a line park this close to the run's own park pins is the run's or a neighbour's
FAR_LINES = {'n': 0}


def _near_run(KF, areas):
    """-> f(line entry) True when the line's box comes within NEAR_LINE_DEG of the box of the POTA pins filed under the run's areas
    (no box known = always True: nothing is left unlisted)."""
    pins = getattr(KF, 'PINS', None) or {}
    pts = []
    for v in pins.values():
        if not (isinstance(v, (list, tuple)) and len(v) > 5 and isinstance(v[1], (int, float)) and isinstance(v[2], (int, float))): continue
        a_ = str(v[5]); a_ = a_ if a_.startswith(('CA-', 'W-', 'US-')) else 'US-' + a_
        if a_ in areas: pts.append((v[2], v[1]))
    if not pts: return lambda e: True
    b = (min(x for x, _ in pts) - NEAR_LINE_DEG, min(y for _, y in pts) - NEAR_LINE_DEG, max(x for x, _ in pts) + NEAR_LINE_DEG, max(y for _, y in pts) + NEAR_LINE_DEG)
    def near(e):
        q = [p for l in (e or {}).get('lines') or [] for p in l if isinstance(p, (list, tuple)) and len(p) >= 2]
        if not q: return True
        return not (max(p[0] for p in q) < b[0] or min(p[0] for p in q) > b[2] or max(p[1] for p in q) < b[1] or min(p[1] for p in q) > b[3])
    return near


def seen_area(st, areas, ref):
    """The run's areas whose store index lists ref (a line park of the run's own areas is always listed when held)."""
    return {ar for ar in areas if st.area(ar) is not None and ref in st.area(ar).entries}


def store_counts():
    """What the run report and the store-missing list say about format-4 records (counts and ids only, no geometry)."""
    tot = {}
    for v in GEOM_SKIPPED.values():
        for k, n in v.items(): tot[k] = tot.get(k, 0) + n
    return {'records left out of area outlines (not area)': dict(sorted(tot.items())), 'parks with records left out': len(GEOM_SKIPPED),
            'line parks read from the store': len(STORE_LINES), 'line parks skipped (by-name / coarse / no bank status)': len(LINE_SKIPPED), 'line parks as on main (coarse NPS routes)': len(MAIN_LINES), 'live pairs on the 100-ft line rule': dict(sorted(LINE_ROWS.items())),
            'water tiles': dict(WATER_READ), 'river rule with no bank data': dict(RIVER_NO_BANK), 'river tiers': dict(RIVER_TIERS),
            'river bank to-do (stretches)': len(RIVER_TODO), 'rows kept (kept: not checked in a store run)': KEPT['n'],
            'rows carried unchanged (' + HELD_TAG + ')': dict(sorted(CARRIED.items())), 'of them live rows': dict(sorted(CARRIED_LIVE.items())),
            'area files left as they were (area does not use the store)': len(SKIPPED_FILES),
            'line parks far from this run not in the store (not listed)': FAR_LINES['n']}


def river_bank_guard(KF, mode):
    """The river rule where there is NO bank data, behind ONE switch (KPC_FERS_RIVER_NO_BANK). Today (kpc_fers.line_spots) a
    US river stretch is measured 30.48 m from the BANK where a water area covers the line, and 30.48 m from the CENTRE LINE (the full
    100 ft since Nov 14) where none does; Canada always from the centre line (no bank source wired).
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
    _rad = max(catch, KF.close_m((min(q[0] for q in near), min(q[1] for q in near)), (max(q[0] for q in near), max(q[1] for q in near))) / 2 + RIVER_NO_BANK['catch_m'])
    RIVER_TODO.append({'refs': row['refs'], 'river': lref, 'park': oref, 'centre_line_m': round(dmin), 'signs': signs, 'tier': tier,
                       'lat': round(pts[k][1], 6), 'lon': round(pts[k][0], 6), 'radius_m': round(min(_rad, 50000)),
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


WATER_SOURCE = {'US': 'us-nhdplus-hr'}   # FORMAT-4: the area's water source. Canada (bc-fwa, ab-hydro, on-ohn) is not read here:
                                        # Canadian rivers keep today's behaviour (no bank source wired in the bot)
WATER_DAMAGED = object()                 # a stored tile that fails its check: NOT SURE, never a fall-through to another copy
WATER_TILE_NAME = re.compile(r'^(-?\d+)_(-?\d+)\.json\.gz$')


def _water_index(st):
    if not hasattr(st, '_widx'):
        try: st._widx = json.loads((pathlib.Path(st.dir) / 'water' / 'index.json').read_text(encoding='utf-8'))
        except Exception: st._widx = None  # noqa: BLE001
    return st._widx


def water_tile_ok(d):
    if not isinstance(d, dict) or not isinstance(d.get('f'), list) or not isinstance(d.get('d'), str): return False
    for x in d['f']:
        if not (isinstance(x, list) and len(x) == 2 and x[0] in ('area', 'wb') and isinstance(x[1], list)): return False
        for ring in x[1]:
            if not (isinstance(ring, list) and len(ring) >= 3 and all(isinstance(q, list) and len(q) >= 2 for q in ring)): return False
    return True


def store_water(st, areas, i, jt):
    """A 0.1-degree water tile from the store's water section (FORMAT-4): store/water/<source id>/<i>_<j>.json.gz, the source
    being the one mapped to the run's areas (US-* = us-nhdplus-hr; only that source decides: a border tile held by another
    source is never read). The tile must be listed in store/water/index.json with the same sha256, its source must be
    publishable on a public store run, and it must be in the bot's own tile form {'d', 'f': [[layer, rings]]}.
    -> the tile (its date as 'd', so rows keep today's dated wording), None (not in the store: the bot's own last good copy of
    the same USGS map is tried, as today) or WATER_DAMAGED (listed but damaged / unlisted / unpublishable: NOT SURE, no
    fall-through)."""
    srcs = [WATER_SOURCE[c] for c in ('US',) if any(str(a).startswith(c + '-') for a in areas)]
    if not srcs: return None
    sid = srcs[0]
    root = pathlib.Path(st.dir) / 'water'
    name = f'{int(i)}_{int(jt)}.json.gz'
    f = root / sid / name
    if not f.is_file(): WATER_READ['not in store'] += 1; return None
    idx = _water_index(st) or {}
    src = (idx.get('sources') or {}).get(sid) or {}
    want = ((idx.get('tiles') or {}).get(sid) or {}).get(name) or {}
    try:
        raw = f.read_bytes()
        if not want.get('sha256') or hashlib.sha256(raw).hexdigest() != want['sha256']: raise ValueError('not listed in water/index.json with this sha256')
        if st.kind != 'private' and src.get('publishable') is not True: raise ValueError('its source is not publishable')
        t = json.loads(gzip.decompress(raw))
        if not water_tile_ok(t): raise ValueError('not in the tile form')
    except Exception as e:  # noqa: BLE001
        WATER_READ['store tile refused'] = WATER_READ.get('store tile refused', 0) + 1
        private_note('water tile refused', [f'{sid}/{name}: {str(e)[:80]}'])
        return WATER_DAMAGED
    WATER_READ['store'] += 1
    d = str(t.get('d') or '')
    if d.startswith(sid): d = d[len(sid):].strip()
    return {'d': d or str(want.get('date') or ''), 'f': t['f']}


def water_reader(st, areas, orig):
    def wload(i, jt):
        t = store_water(st, areas, i, jt)
        if t is WATER_DAMAGED: return None   # NOT SURE: never another copy deciding alone
        return t if t is not None else (orig(i, jt) if orig else None)
    return wload


def scan_private(st, areas):
    """HELD_PRIVATE from the store index, for EVERY park of the run's areas (not only the parks read): a park with any record
    that is not publishable (with a verified-row / owner-confirmed basis) or that is or may be WDPA-derived. The index's
    record_meta is used; a park without it is read (checked) once. Such a park is never named in a public file."""
    n = 0
    for ar in areas:
        a = st.area(ar)
        if a is None: continue
        for ref, e in list(a.entries.items()) + [(r, None) for r in a.bad]:
            if e is None: continue
            if isinstance(e.get('name'), str): NAMES.setdefault(ref, e['name'])
            rm = e.get('record_meta') if isinstance(e.get('record_meta'), dict) else None
            secret = e.get('park_publishable') is False
            if rm:
                secret = secret or any(not (isinstance(m, dict) and m.get('publishable') is True and m.get('publish_basis') in PUBLISH_BASES and m.get('wdpa_derived') is False)
                                       for m in rm.values())
            else:
                try: p = a.park(ref) or {}
                except StoreError: p = {}
                secret = secret or wdpa_text(p) or any(not (r.get('publishable') is True and r.get('publish_basis') in PUBLISH_BASES and r.get('wdpa_derived') is False)
                                                     or wdpa_text(r) for r in p.get('records') or [] if isinstance(r, dict))
            if secret: HELD_PRIVATE.add(ref); n += 1
    return n


WITHHELD_DIR = 'store-withheld'   # in the private folder: one list per bot process (refs, names), read by kpc_fers_expected.py


def save_withheld_list(tag, pass_no):
    """Public store run: the WHOLE withheld list of this process (withheld_refs(), with the distinctive names) into
    <private folder>/store-withheld/<tag>-p<pass>.json, so a later step (kpc_fers_expected.py) leaves those parks out. -> the number of
    withheld parks over every list of this tag so far (the run's total), or None when there is no private folder."""
    if not PRIVATE_LOG_DIR: return None
    d = pathlib.Path(PRIVATE_LOG_DIR) / WITHHELD_DIR
    refs = sorted(withheld_refs())
    nm, mask = secret_names(set(refs)) if refs else (set(), set())
    try:
        d.mkdir(parents=True, exist_ok=True)
        (d / f'{tag}-p{pass_no}.json').write_text(json.dumps({'refs': refs, 'names': sorted(nm), 'mask': sorted(mask), 'read_ok': sorted(READ_OK)}), encoding='utf-8')
    except OSError: return None
    allr = set()
    for f in d.glob(f'{tag}-p*.json'): allr |= set(_read_json(f).get('refs') or [])
    return len(allr)


def read_ok_before(tag, pass_no):
    """The parks the earlier passes of this area's public run read from publishable records only (their store-withheld lists, in the
    private folder). KPC owner, 2026-11-15 (trial 2 on the real store, CT): a park with a publishable outline and an unpublishable line
    record is read (and may be named) in pass 1, which reads every park; pass 5 reads only some parks, so the same park counted as
    withheld there and the push check refused pass 1's own files. A later pass keeps the earlier passes' answer."""
    if not PRIVATE_LOG_DIR or not pass_no: return set()
    out = set()
    for f in (pathlib.Path(PRIVATE_LOG_DIR) / WITHHELD_DIR).glob(f'{tag}-p*.json'):
        m = re.fullmatch(re.escape(tag) + r'-p(\d+)\.json', f.name)
        if m and int(m.group(1)) < pass_no: out |= {str(x) for x in _read_json(f).get('read_ok') or []}
    return out


def load_withheld(private_dir):
    """(refs, names, mask) of every withheld list in a private folder: this module's own lists (store-withheld/) and the KPC-Store
    run's lists (withheld/*.json: refs, names, mask), unioned. None when the folder has no list at all (the caller fails closed)."""
    if not private_dir: return None
    refs, names, mask, n = set(), set(), set(), 0
    for sub in (WITHHELD_DIR, 'withheld'):
        for f in sorted((pathlib.Path(private_dir) / sub).glob('*.json')):
            if f.name == 'store-tokens.json': continue
            try: doc = json.loads(f.read_text(encoding='utf-8'))
            except (OSError, ValueError): return None   # a list that cannot be read: fail closed
            if not isinstance(doc, dict): return None
            n += 1
            refs |= {str(x) for x in doc.get('refs') or []}
            names |= {norm_name(x) for x in doc.get('names') or [] if norm_name(x)}
            mask |= {norm_name(x) for x in doc.get('mask') or [] if norm_name(x)}
    return (refs, names, mask) if n else None


def guard_public_file(path, doc, refs, names=(), mask=()):
    """For a writer in ANOTHER process of a public store run (kpc_fers_expected.py): redact + the write guard with the run's withheld
    list. -> (doc, items left out); raises LeakRefused like the bot's own write step."""
    doc, n = redact(doc, set(refs))
    guard_write(path, doc, private=set(refs), names=(set(names), set(mask)))
    return doc, n


def write_todo_csv():
    """The river bank to-do (tiers mode) as the spec's river-bank-todo.csv, in the PRIVATE folder only."""
    if not PRIVATE_LOG_DIR or not RIVER_TODO: return False
    import csv
    p = pathlib.Path(PRIVATE_LOG_DIR) / 'river-bank-todo.csv'
    with open(p, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh); w.writerow(['park ref', 'other park ref', 'lat', 'lon', 'radius m'])
        for t in RIVER_TODO: w.writerow([t['river'], t['park'], t['lat'], t['lon'], t['radius_m']])
    return True


BANK_EST = 'no water data: measured from the centre line (25.48 m), an estimate until the store has this bank'


def line_status(KF, doc):
    """Owner ruling 2026-11-14: a river line the store marks bank_missing is still decided by the bot's existing centre-line rule
    (exactly as on main). A row whose stretch was not measured from a real bank is marked 'river_bank' (an estimate) and its
    stretch goes on the PRIVATE river-bank-todo.csv so the store fetches that tile next. Its status is not changed."""
    n = 0
    for x in (doc or {}).get('spots') or []:
        if x.get('kind') != 'river' or str(x.get('status') or '').startswith(('dropped', 'merged')): continue
        for r in x.get('refs') or []:
            e = STORE_LINES.get(r) or {}
            if e.get('bank_missing') and not x.get('bank_ok'):
                x['river_bank'] = BANK_EST; n += 1
                c = x.get('center') or [None, None]
                o = [q for q in x.get('refs') or [] if q != r]
                if c[0] is not None and not any(t.get('row') == x.get('id') for t in RIVER_TODO):
                    RIVER_TODO.append({'river': r, 'park': o[0] if o else '', 'lat': c[0], 'lon': c[1], 'radius_m': max(250, round((x.get('len_m') or 0) / 2) + 250), 'row': x.get('id'), 'refs': x.get('refs')})
                break
    return n


def write_candidates_csv():
    """Lines the store gave but the bot skipped (by-name, coarse route, no bank status): 'river candidate: needs a look', in the
    PRIVATE folder only."""
    if not PRIVATE_LOG_DIR or not LINE_SKIPPED: return False
    import csv
    with open(pathlib.Path(PRIVATE_LOG_DIR) / 'river-candidates-needs-a-look.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh); w.writerow(['park ref', 'status', 'why'])
        for r, why in sorted(LINE_SKIPPED.items()): w.writerow([r, 'river candidate: needs a look', why])
    return True


def bank_check(KF):
    """Store run: a river stretch of a store line marked bank_missing is 'bank_ok' only when every point of it lies in mapped
    water (the 30.48 m-from-the-bank test really ran); line_status() makes the others NOT SURE."""
    orig = getattr(KF, 'line_spots', None)
    if orig is None or getattr(orig, '_bank', False): return
    def line_spots(lref, ls, oref, other, other_is_line, box, kind):
        got = orig(lref, ls, oref, other, other_is_line, box, kind)
        if kind == 'river' and (STORE_LINES.get(lref) or {}).get('bank_missing'):
            for x in got:
                pts = x.get('shape') or []
                b = KF.bbox_lines([pts]) if pts else None
                wg = KF.nhd_water([b[0] - .001, b[1] - .001, b[2] + .001, b[3] + .001], rivers_only=True) if b else None
                if wg and all(KF.pip_groups(wg, q[0], q[1]) for q in pts): x['bank_ok'] = True
        return got
    line_spots._bank = True; line_spots._store = getattr(orig, '_store', False)
    KF.line_spots = line_spots


def store_areas(path=None):
    """.github/fers-store-areas.json -> {'all': bool, 'list': set, 'except': {area: why}, 'world': bool}, or None with the reason
    when the file is missing or not in the one shape this reader knows (fail closed: then no area uses the store)."""
    p = pathlib.Path(path or STORE_AREAS_FILE)
    try: doc = json.loads(p.read_text(encoding='utf-8'))
    except Exception as e: return None, f'{p.name} cannot be read ({_err(e)})'  # noqa: BLE001
    if not isinstance(doc, dict): return None, f'{p.name} is not an object'
    a, ex, w = doc.get('areas'), doc.get('except', []), doc.get('world', 'off')
    if not (a == STORE_ALL or (isinstance(a, list) and all(isinstance(x, str) and STORE_AREA_RX.fullmatch(x) for x in a))):
        return None, f'{p.name}: "areas" must be "{STORE_ALL}" or a list of US / Canadian area codes'
    if not (isinstance(ex, list) and all(isinstance(x, str) and re.fullmatch(r'(US|CA|W)-[A-Z]{2}', x) for x in ex)):
        return None, f'{p.name}: "except" must be a list of area codes'
    if w not in ('on', 'off'): return None, f'{p.name}: "world" must be "on" or "off"'
    return {'all': a == STORE_ALL, 'list': set(a) if isinstance(a, list) else set(), 'except': set(ex), 'world': w == 'on'}, ''


def area_use(area, cfg):
    """'' when this area may be read from the store, else the plain reason it is not."""
    if area in NEVER_STORE: return NEVER_STORE[area]
    if area in cfg['except']: return 'on the except list of .github/fers-store-areas.json: it stays on the old path (run it with the switch off)'
    if re.fullmatch(r'W-[A-Z]{2}', area):
        return '' if cfg['world'] else 'world areas are switched off in .github/fers-store-areas.json ("world": "off")'
    if not STORE_AREA_RX.fullmatch(area): return 'not a US, Canadian or world area code'
    if cfg['all'] or area in cfg['list']: return ''
    return 'not listed in .github/fers-store-areas.json'


def install(KF, env=None, store=None):
    """Switch the imported kpc_fers module to the store for this process. False (nothing changed; the bot runs as today) when
    the switch is off, the run is Kentucky's, the run is the world's with the world switch off, or every named area is on the
    except list. An area of the run that may not use the store, or that the store does not hold (no index, another format, stale,
    damaged), is left out of this run with its reason (its row in store-missing-<tag>.json; it keeps its previous files). Exits
    87 when no area is left (or the list cannot be read, or the run names no area), 88 when the run will not fit, 89 when a world
    store run is not a private store run. Nothing is unpacked here."""
    global STORE_ON
    env = os.environ if env is None else env
    if mode(env) != 'on': return False
    if getattr(KF, '_STORE_INSTALLED', False): return True   # once per process (kpc_fers_store.py run + the hook in kpc_fers.main())
    region = getattr(KF, 'REGION', 'na')
    cfg, cfg_why = store_areas()
    world_on = region == 'world' and cfg is not None and cfg['world']
    if region != 'na' and not world_on:
        print(f'::notice title=2-fer outline store::{SWITCH} is on, but this is the {KF.REGION} run: the outline store is not used and the bot runs as today', flush=True)
        return False
    global PRIVATE_OUT, PRIVATE_LOG_DIR
    KF_REF['kf'] = KF
    st = store or Store.from_env(env)
    if world_on and st.kind != 'private':
        # world 2-fers are club room only (kpc_fers_publish.py and the write guard refuse world rows in a public file): a world
        # store run is a private store run or nothing
        public_print('::error title=2-fer outline store::a world store run must be a private store run (KPC_FERS_STORE_KIND=private): world 2-fers '
                     'are club room only. Nothing was read or saved.')
        raise SystemExit(EXIT_LEAK)
    if st.kind == 'private' and str(env.get('GITHUB_ACTIONS') or '').strip().lower() == 'true' and str(env.get('KPC_FERS_PRIVATE_RUNNER') or '').strip() != '1':
        # the log of a GitHub Actions run of a public repo is public: a private store run there only on a runner named private
        public_print('::error title=2-fer outline store::private store run refused under GitHub Actions: set KPC_FERS_PRIVATE_RUNNER=1 '
                     'only on a private runner whose log nobody outside the club can read. Nothing was read or saved.')
        raise SystemExit(EXIT_LEAK)
    if st.kind == 'private':
        # a private store holds records that are not publishable: every file of the run is club room only, so it goes to ONE
        # folder outside every git work tree (never the KPC-Data checkout); without one the run does not start
        po = str(env.get('KPC_FERS_PRIVATE_OUT') or '').strip()
        why = ('KPC_FERS_PRIVATE_OUT is not set' if not po else
               'KPC_FERS_PRIVATE_OUT is inside a git work tree' if in_git_tree(po) else
               'KPC_FERS_PRIVATE_OUT overlaps the working folder' if _inside(po, os.getcwd()) or _inside(os.getcwd(), po) else '')
        if why:
            public_print(f'::error title=2-fer outline store::private store run refused: {why}. A private store run writes only into a '
                         'private folder outside every git work tree (club room only); nothing was read or saved.')
            raise SystemExit(EXIT_LEAK)
        PRIVATE_OUT = pathlib.Path(po).resolve(); PRIVATE_OUT.mkdir(parents=True, exist_ok=True)
        KF.OUT = PRIVATE_LOG_DIR = PRIVATE_OUT
        silence(PRIVATE_OUT)   # every line the bot prints (pair ids, park names, progress) goes to the private log; stdout gets counts only
    else:
        pl = str(env.get('KPC_FERS_PRIVATE_LOG') or '').strip()   # optional on a public run: where details (never printed) may go
        if pl and not in_git_tree(pl) and not _inside(pl, os.getcwd()) and not _inside(os.getcwd(), pl):
            PRIVATE_LOG_DIR = pathlib.Path(pl).resolve(); PRIVATE_LOG_DIR.mkdir(parents=True, exist_ok=True)
        elif pl: public_print('::warning title=2-fer outline store::KPC_FERS_PRIVATE_LOG is inside a git work tree or the working folder: not used (no details are kept)')
        if not isinstance(sys.stdout, RedactOut): sys.stdout = RedactOut(sys.stdout)
        if not isinstance(sys.stderr, RedactOut): sys.stderr = RedactOut(sys.stderr)
    out_dir = pathlib.Path(getattr(KF, 'OUT', 'data/fers')).resolve()
    tag = getattr(KF, 'area_name', lambda: 'run')()
    if st.kind != 'private':   # trial 2 (CT): one answer per park for the whole run, so a later pass never withholds a park an earlier pass published
        READ_OK_RUN.update(read_ok_before(tag, int(getattr(KF, 'PASS', 0) or 0)))

    def write_rows():
        doc = {'about': 'Outline store use by the 2-fer bot: one row per area (ready / not ready / will not fit) and every held park with its reason. '
                        'A park held or used for records that are not publishable (licence) or are WDPA-derived is never named here: only counted. One door in: only the store filler fetches.',
               'date': st.today, 'kind': st.kind, 'areas': dict(sorted(AREA_ROWS.items())), 'parks': dict(sorted(FLAGS.items())),
               **store_counts(), 'area files left as they were': dict(sorted(SKIPPED_FILES.items()))}
        if st.kind == 'private': doc['store'] = str(st.dir); doc['private_records'] = dict(sorted(PRIVATE.items())); doc['river_bank_todo'] = RIVER_TODO
        else:
            doc, n = redact(doc); WITHHELD['items'] += n
        doc['withheld (parks held or used for unpublishable / WDPA records: not named)'] = len(withheld_refs()) if st.kind != 'private' else 0
        if st.kind != 'private':   # C9: the whole run (every pass of this area so far), not only this pass; and the full list, privately
            run = save_withheld_list(tag, int(getattr(KF, 'PASS', 0) or 0))
            if run is not None: doc['withheld over the run (all passes so far, not named)'] = run
        p = out_dir / f'store-missing-{tag}.json'
        guard_write(p, doc)
        try: write_todo_csv(); write_candidates_csv()
        except OSError: pass
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding='utf-8')
        except OSError: pass
    area_rx = r'W-[A-Z]{2}' if world_on else r'(US|CA)-[A-Z]{2}'
    named = sorted(getattr(KF, 'ONLY', None) or ())
    areas = sorted(a for a in named if re.fullmatch(area_rx, a))
    if cfg is None or not areas:
        why = (f'the store area list cannot be used: {cfg_why}' if cfg is None else
               'no area named (STATES): a store run names its areas, so an area on the old path is never rewritten from the store')
        for a in areas or ['(none)']: AREA_ROWS[a] = {'verdict': 'NOT READY', 'why': why}
        write_rows()
        public_print(f'::error title=2-fer outline store::{why}. Nothing of this run is read or saved.')
        raise SystemExit(EXIT_NOT_READY)
    st.allow = lambda a: area_use(a, cfg)
    off = {a: area_use(a, cfg) for a in areas if area_use(a, cfg)}
    if len(off) == len(areas):   # every named area stays on the old path: the bot runs as today for all of them
        st.allow = None
        public_print(f'::notice title=2-fer outline store::{SWITCH} is on, but no area of this run uses the store (' + '; '.join(f'{a}: {w}' for a, w in sorted(off.items()))
                     + '): the bot runs as today')
        return False
    for a, w in off.items(): AREA_ROWS[a] = {'verdict': 'NOT USED', 'why': w}
    for a in areas:   # an area the store does not hold (or cannot be read / is stale / another format) is left out with its reason
        if a not in off and st.area(a) is None: AREA_ROWS[a] = {'verdict': 'NOT READY', 'why': st.why[a]}
    ready = [a for a in areas if a not in AREA_ROWS]
    if not ready:
        write_rows()
        for a, r in sorted(AREA_ROWS.items()): public_print(f"::error title=2-fer outline store::{a}: {r['verdict']}: {r['why']}. Nothing of this run is read or saved; the area keeps its previous files.")
        raise SystemExit(EXIT_NOT_READY)
    if st.kind != 'private': scan_private(st, ready)   # every park of the areas, read or not
    lazy = bool(getattr(KF, 'FERS_LAZY_OK', False))   # set by the switch-over in kpc_fers.py once every pass keeps G lazy
    budget = int(env.get('KPC_FERS_STORE_BUDGET') or 2_000_000)
    ok, rows = fit_check(st, ready, int(env.get('KPC_FERS_STORE_LIMIT_MB') or 3000), budget, env_float(env, 'KPC_FERS_STORE_NEIGHBOURS', 1.5, 10.0), lazy)
    AREA_ROWS.update(rows)
    if not ok:
        write_rows()
        for a, r in sorted(rows.items()):
            if r['verdict'] != 'READY': public_print(f"::error title=2-fer outline store::{a}: {r['verdict']}: {r['why']}. Nothing of this run is read or saved; the area keeps its previous files.")
        raise SystemExit(EXIT_WONT_FIT)
    if len(ready) < len(areas):   # this run goes on with the areas the store can serve; the others keep their previous files
        if not str(getattr(KF, 'RUN_TAG', '') or ''): KF.RUN_TAG = tag   # the run's file names do not move
        KF.ONLY = set(ready) | (set(named) - set(areas))
        for a in sorted(set(areas) - set(ready)):
            public_print(f"::warning title=2-fer outline store::{a}: {AREA_ROWS[a]['verdict']}: {AREA_ROWS[a]['why']}. Left out of this run; the area keeps its previous files.")
    areas = ready
    WORLD_ON['on'] = world_on
    def area_off(a):   # also a border area of this run: a spot file of an area that does not use the store is never rewritten
        if a in areas: return ''
        return area_use(a, cfg) or ('' if st.area(a) is not None else st.why.get(a) or 'not read')
    AREA_OFF['fn'] = area_off
    # grade of #201 (item 5): the declared scope is 'none' (an ordinary switch-off run re-tests nothing). A store run stamps the parks
    # of the areas it runs from the store with this change's id, so their pairs are tested again on the first store run only
    orig_stamp = getattr(KF, 'rule_stamp', None)
    if orig_stamp is not None and not getattr(orig_stamp, '_store', False):
        def rule_stamp(r):
            out = list(orig_stamp(r))
            p_ = (getattr(KF, 'PINS', None) or {}).get(r) or ()
            a_ = str(p_[5]) if len(p_) > 5 else ''
            a_ = a_ if a_.startswith(('CA-', 'W-', 'US-')) else ('US-' + a_ if a_ else '')
            if a_ in areas: out.append(STORE_STAMP)
            return out
        rule_stamp._store = True
        KF.rule_stamp = rule_stamp
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
                owner_status(d)
                line_status(KF, d)
                if RIVER_NO_BANK['mode'] == 'tiers': bank_status(d)
                final = int(getattr(KF, 'PASS', 3)) >= 3
                cf = store_prev_file(KF, d['st'])
                carry = _read_json(cf) if cf is not None else {}
                k = keep_old_rows(d, old, st.today, final=final, carry=carry)
                if cf is not None: _write_carry(cf, carry if not final else None)
                if k: KF.LOG.append(f"{d['st']}: {k} candidate rows kept from the last file ({KEPT_TAG}: closed areas / ownership)")
                if st.kind != 'private':   # OWNER RULE 'never worse' (M2 + M3): a withheld park's public rows are carried unchanged
                    c = carry_held_rows(KF, d, old)
                    if c: KF.LOG.append(f"{d['st']}: {c} rows of parks whose outline is held privately carried unchanged ({HELD_TAG})")
                LINE_ROWS[d['st']] = sum(1 for x in d.get('spots') or [] if x.get('kind') in ('trail', 'river') and _live(x) and not x.get('store_held'))
        except Exception as e: KF.LOG.append(f'outline store row carry: {str(e)[:80]}')  # noqa: BLE001  (the write guard still checks the file)
        return d

    shut_door(KF)
    if getattr(KF, 'time', None) is not None and not isinstance(KF.time, _StoreTime): KF.time = _StoreTime(KF.time)
    bank_check(KF)
    river_bank_guard(KF, river_mode(env))
    orig_lines, orig_wload = getattr(KF, 'trail_lines', None), getattr(KF, '_wload', None)
    if orig_lines is not None and not world_on: KF.trail_lines = lambda: store_lines(KF, st, areas, orig_lines())   # world: no store lines (no line rule wired for world store areas)
    if orig_wload is not None:   # the store's water tile first; else the bot's own last good copy (WATER_STORE) as today; damaged = NOT SURE
        KF._wload = water_reader(st, areas, orig_wload)
    orig_ml = getattr(KF, 'missing_list', None)
    if orig_ml is not None:
        def missing_list(*a, **k):   # R12 list: a park the STORE held is listed with the store's reason, never 'no official boundary'
            out = orig_ml(*a, **k)
            for x in out:
                if isinstance(x, dict) and x.get('ref') in FLAGS: x['why'] = 'held by the outline store: ' + str(FLAGS[x['ref']])
            return out
        KF.missing_list = missing_list
    KF.download, KF.saved_us, KF.saved_ca, KF.live_load, KF.pc_tag = download, (lambda parks: saved_corridors(KF)), saved_ca, live_load, pc_tag
    KF.STORE = st; STORE_ON = True; KF._STORE_INSTALLED = True
    def rows_at_exit():
        try: write_rows()
        except LeakRefused: sys.stdout.flush(); sys.stderr.flush(); os._exit(EXIT_LEAK)   # at exit too: the run fails, nothing written
    atexit.register(rows_at_exit)   # written on every run, so an old list never outlives a filled gap
    public_print(f"::notice title=2-fer outline store::{SWITCH}=on ({st.kind} store, {len(areas)} area(s)); no boundary downloads; memory gate "
                 + ', '.join(f"{a} {r.get('estimate_mb')} MB" for a, r in sorted(rows.items())) + ('' if lazy else ' (outlines all unpacked until the bot keeps them lazy)'))
    if st.kind == 'private': atexit.register(lambda: public_print(f'::notice title=2-fer outline store::private store run: {len(STORE_LINES)} line parks, '
                                                                     f'{len(FLAGS)} held parks, {sum(LINE_ROWS.values())} live line rows; every detail is in the private folder'))
    return True


class _StoreTime:
    """kpc_fers.py's 'time' in a store run: the one-minute wait before pass 1's slow second try (it waits for an agency server
    that did not answer) is skipped: the second try only reads the store again. Every other use of time is unchanged."""
    def __init__(self, real): self._real = real
    def sleep(self, s):
        if s >= 60: return None
        return self._real.sleep(s)
    def __getattr__(self, k): return getattr(self._real, k)


class RedactOut:
    """Public store run: every line this process prints passes here; a park held or used for unpublishable / WDPA records is
    replaced by [withheld] (a GitHub Actions log of a public repo is public)."""
    def __init__(self, real): self.real, self._n, self._rx = real, -1, None
    def write(self, t):
        sec = withheld_refs()
        if len(sec) != self._n: self._n, self._rx = len(sec), _ref_rx(sec)
        if self._rx is not None and isinstance(t, str): t = self._rx.sub('[withheld]', t)
        return self.real.write(t)
    def flush(self): return self.real.flush()
    def __getattr__(self, k): return getattr(self.real, k)


def silence(folder):
    """Private store run: this process's stdout and stderr go to <private folder>/run-log.txt (pair ids, park names, progress,
    tracebacks); only public_print() reaches the real stdout, with counts."""
    fh = open(pathlib.Path(folder) / 'run-log.txt', 'a', encoding='utf-8', buffering=1)
    sys.stdout = sys.stderr = fh
    return fh


def unsilence():
    sys.stdout, sys.stderr = _REAL_OUT['out'], _REAL_OUT['err']


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
            # C7 (store trial): the change list names parks, withheld ones of the old public file too: it is a PRIVATE file. With
            # KPC_FERS_PRIVATE_LOG set it goes there (the stem's name only); otherwise a stem inside a git work tree is refused
            stem = pathlib.Path(a['--out'])
            pl = str(os.environ.get('KPC_FERS_PRIVATE_LOG') or '').strip()
            if pl: stem = pathlib.Path(pl) / stem.name; stem.parent.mkdir(parents=True, exist_ok=True)
            if in_git_tree(stem.parent):
                print('diff --out: the change list names parks (withheld ones too): write it outside every git work tree, or set KPC_FERS_PRIVATE_LOG'); return 2
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
        cfg, _ = store_areas()
        if KF.REGION != 'na' and not (KF.REGION == 'world' and cfg and cfg['world']): print(f'the {KF.REGION} run does not use the outline store: use kpc_fers.py'); return 2
        KF.main()   # the hook at the top of kpc_fers.main() installs the store (once)
        return 0
    print(f'unknown command {cmd!r}'); return 2


if __name__ == '__main__':
    sys.exit(main())
