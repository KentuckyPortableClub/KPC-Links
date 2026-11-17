# KPC-Store change file: the keeper writes layer requests (Handoff 3, third job, step 1)

For: KPC owner / the manager session, to apply in KPC-Store. Written 2026-11-17 without access to KPC-Store, from the
Handoff 3 text (lines 105-126) and KPC-Links .claude/notes/layer-refresh.md only. Every guess about the keeper's own code is
marked ASSUMED; check each one before applying. Nothing here fetches, starts a workflow, or changes a keeper setting.
The cache side that reads the file is the KPC-Links PR "Layer refresh: the old saved-shapes bots serve the keeper's requests".

## What changes (and what does not)

- The keeper's walk, when it finds a layer whose ETag or lastEditDate moved (the place it already reports
  result='changed', why='edited on the server (<old> -> <new>)'), adds ONE row to a request file. That is the whole change.
- It never fetches the layer, never starts a workflow, never dispatches anything, never writes to KPC-Links.
- keeper/keeper.py DEFAULTS (cycle_days 28, max_layers_checked_per_run 40, catch_up_after_days 31), the walk order, the
  schedules (07:41 UTC daily US + Canada, 05:17 UTC Thursdays world) and store/layers-seen.json stay exactly as they are.
- Whole layers never enter KPC-Store. The request file holds addresses and dates only, no geometry.

## The two files

1. store/layer-requests.json on the store-data branch (PRIVATE, the keeper's own record). One row per detected move:

```json
{"format": 1, "written": "2026-11-17 07:41 UTC",
 "requests": [{"layer": "<layer address as the keeper keys it>", "area": "US-TN", "moved": ["etag"],
               "date": "2026-11-17", "by": "keeper"}],
 "walked":   [{"layer": "<address>", "area": "US-TN"}],
 "unwalked": [{"layer": "<address>", "area": "US-OH"}]}
```

   - area: US-XX, CA-XX (or CA-ALL), W-XX.
   - moved: any of "etag", "lastEditDate" (exact spelling; the reader lowercases them).
   - date: the walk date, YYYY-MM-DD (UTC).
   - by: always "keeper" here. (R-LR4, still open, decides whether a chat or report may add a row with by: "chat" / "report" / "hand".)
   - walked: every layer that has a first reading in layers-seen.json (last_checked set).
   - unwalked: every layer on the keeper's list with NO first reading yet. These are UNKNOWN, never "unchanged".
     Leaving a layer out of both lists also makes it unknown on the cache side.

2. layer-requests.json, the PUBLIC copy the cache bots read (asset on the KPC-Links boundary-cache release).
   Same shape, but every "layer" value is replaced by "sha256:" + the first 16 hex of sha256(address). The cache bots
   only need the area, what moved and the date (they re-read the whole area file they already own), so no layer address,
   ETag value, edit date, record count, terms hash or host from the private store reaches a public file or log.
   The cache side never prints a layer value anyway, and refuses any row that names WDPA / Protected Planet.

## Code (ASSUMED shape of keeper.py; adapt names to the real ones)

New helper, keeper/layer_requests.py (a new file, so nothing else in keeper.py moves):

```python
"""The keeper asks, it never fetches (Handoff 3, KPC owner, 2026-11-17)."""
import datetime, hashlib, json, pathlib, re

REQ = pathlib.Path('store/layer-requests.json')          # ASSUMED: paths are relative to the store-data checkout
PUBLIC = pathlib.Path('store/layer-requests.public.json') # the copy for the release; see the open question Q1
NEVER = re.compile(r'wdpa|protected[ _-]?planet|world[ _-]?database[ _-]?of[ _-]?protected|unep-?wcmc', re.I)


def _load():
    try: d = json.loads(REQ.read_text(encoding='utf-8'))
    except (OSError, ValueError): d = {}
    if d.get('format') != 1: d = {'format': 1, 'requests': []}
    d.setdefault('requests', []); return d


def add_request(layer, area, moved, when=None):
    """One row: layer address, area, what moved (['etag'] / ['lastEditDate'] / both), the date. Never fetches."""
    if NEVER.search(str(layer)): return False             # WDPA is never a source
    moved = [m for m in ('etag', 'lastEditDate') if m in moved]
    if not moved: return False
    day = (when or datetime.datetime.now(datetime.timezone.utc)).strftime('%Y-%m-%d')
    d = _load()
    row = {'layer': layer, 'area': area, 'moved': moved, 'date': day, 'by': 'keeper'}
    if row not in d['requests']: d['requests'].append(row)   # the same move found twice the same day = one row
    _save(d); return True


def set_walked(walked, unwalked):
    """walked / unwalked: lists of (layer, area). Called once at the end of the walk."""
    d = _load()
    d['walked'] = [{'layer': l, 'area': a} for l, a in sorted(walked)]
    d['unwalked'] = [{'layer': l, 'area': a} for l, a in sorted(unwalked)]
    _save(d)


def _sha(x): return 'sha256:' + hashlib.sha256(str(x).encode('utf-8')).hexdigest()[:16]


def _save(d):
    d['written'] = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    REQ.write_text(json.dumps(d, indent=1, sort_keys=True) + '\n', encoding='utf-8', newline='\n')   # LF only
    pub = {'format': 1, 'written': d['written'],
           'requests': [dict(r, layer=_sha(r['layer'])) for r in d['requests']],
           'walked': [dict(r, layer=_sha(r['layer'])) for r in d.get('walked', [])],
           'unwalked': [dict(r, layer=_sha(r['layer'])) for r in d.get('unwalked', [])]}
    PUBLIC.write_text(json.dumps(pub, indent=1, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
```

In keeper/keeper.py, two calls and nothing else:

```python
from layer_requests import add_request, set_walked   # ASSUMED import style (keeper/ on sys.path)

# where the walk already records result='changed' for one layer (ASSUMED variable names):
#   old / new = the layer's previous and new layers-seen.json entries; area = the slice's area code
moved = [k for k in ('etag', 'lastEditDate') if (old or {}).get(k) and new.get(k) and old.get(k) != new.get(k)]
if moved: add_request(layer_address, area, moved)

# once, after the walk has saved layers-seen.json (ASSUMED: the keeper knows its full layer list with each layer's area):
set_walked([(l, a) for l, a in all_layers if seen.get(l, {}).get('last_checked')],
           [(l, a) for l, a in all_layers if not seen.get(l, {}).get('last_checked')])
```

Only a move of ETag or lastEditDate makes a row. A first reading (no old value) is not a move: that layer goes from
unwalked to walked and makes no request. last_modified, record count, terms_sha and the gone list do not make rows
(the handoff names ETag and lastEditDate only); R-LR2 (dying layers) may later add a "dying": true flag.

## ASSUMED (please check against the real keeper)

A1. keeper.py has one place where a layer's result becomes 'changed' with its old and new readings at hand.
A2. The walk knows each layer's area (US-XX / CA-XX / W-XX). layers-seen.json, as described, has no area field
    (record count, ETag, lastEditDate, last_modified, terms_sha, last_changed, last_checked, host, gone).
A3. layers-seen.json is keyed by the layer address (the service URL); the ETag field is spelled "etag" and the edit
    date "lastEditDate" (adapt the two names in `moved = ...`).
A4. The keeper has its full layer list (to name the unwalked ones), e.g. from data/state-gis.json and the key layer tables.
A5. The keeper's workflow already commits store/ files on store-data, so the two new files ride its existing save.

## Open questions for the owner

Q1. How the public copy reaches the KPC-Links boundary-cache release. The keeper runs in private KPC-Store and the
    cache bots in public KPC-Links. Either (a) the keeper workflow uploads store/layer-requests.public.json as the release
    asset layer-requests.json, which needs a KPC-Links-scoped token in KPC-Store (a settings / secret change: owner only), or
    (b) the manager session uploads it by hand before pressing the cache bot's button. Until this is ruled the cache bot finds
    no request file and fetches nothing.
Q2. Who clears a served row. Rows stay in the file until removed; pressing the button twice re-reads the same areas.
    The cache bot does not write back. Suggestion: the keeper drops a row once the area's release copy is newer than the
    row's date; not built, because nothing else in the keeper may change without a ruling.
Q3. R-LR1 to R-LR4 RULED 2026-11-17; the cache workflows default to them (180 / full / whole / keeper+hand). R-LR2's one full-detail save of a dying layer is built on the cache side (kpc_layer_full_save.sh, asset full-<area>.json.gz); the keeper only marks the row (moved 'gone' / 'retiring', or dying: true).

KPC owner, 2026-11-17
