"""ASSEMBLY LINE disk cache (chat 2, Oct 27 2026; HQ 5:23 PM: fetcher -> worker -> checker, bundles as KPC-Data release assets).
Every map-server answer the 2-fer bot reads (outlines, ownership, water, roads, closures) can be kept on disk, so a later stage
or a rerun after a bug fix reads it from the bundle instead of asking the agency again (polite + fast).
HTTP_CACHE=<dir> turns it on; HTTP_CACHE_DAYS (default 21) = how old an answer may be; HTTP_OFFLINE=1 = never ask the
server (a miss raises 'not in the bundle'). Answers that are errors are never kept. Off when HTTP_CACHE is not set."""
import gzip, hashlib, json, os, pathlib, re, time

DIR = os.environ.get('HTTP_CACHE') or ''
DAYS = float(os.environ.get('HTTP_CACHE_DAYS') or 21)
OFFLINE = os.environ.get('HTTP_OFFLINE') == '1'
STATS = {'hit': 0, 'miss': 0, 'kept': 0}
LAST = None    # Oct 30 (B2): when the last answer was READ from the agency (a bundle hit = the file's date, a live answer = now)
TRACE = None   # Oct 28 (speed step 2): a list while a pair is computed = every answer it consumed (url, params, digest of the answer)


def _path(url, params):
    k = hashlib.sha1((url + '|' + json.dumps(params, sort_keys=True, default=str)).encode()).hexdigest()
    return pathlib.Path(DIR) / k[:2] / (k + '.json.gz')


EDIT = {}   # layer url -> its last edit time in seconds (None = the server does not say)
CHECKS = {'asked': 0, 'unchanged': 0}


def _layer_edit(url):
    """Oct 28 (Brandon: 'why read it live, it's not going to change'): ONE tiny request per map layer per run = the layer's own
    'last edited' date (ArcGIS editingInfo). A saved answer newer than that is still the layer's answer, however old."""
    m = re.match(r'(https?://.+/(?:MapServer|FeatureServer)/\d+)/query$', url)
    if not m or OFFLINE: return None
    L = m.group(1)
    if L not in EDIT:
        EDIT[L] = None; CHECKS['asked'] += 1
        try:
            import urllib.request, urllib.parse
            with urllib.request.urlopen(urllib.request.Request(L + '?f=json', headers={'User-Agent': 'KPC 2-fer bot (kentuckyportableclub.github.io)'}), timeout=30) as r:
                j = json.loads(r.read().decode('utf-8', 'replace'))
            ei = j.get('editingInfo') or {}
            t = ei.get('dataLastEditDate') or ei.get('lastEditDate')
            EDIT[L] = float(t) / 1000 if t else None
        except Exception: EDIT[L] = None  # noqa: BLE001
    return EDIT[L]


def cached(url, params, fetch):
    """fetch() = the real request (returns parsed JSON). Cached when HTTP_CACHE is set."""
    global LAST
    if not DIR: LAST = time.time(); return fetch()
    p = _path(url, params)
    try:
        fresh = p.exists() and time.time() - p.stat().st_mtime < DAYS * 86400
        if p.exists() and not fresh:   # older than the age limit: still good when the layer says it has not been edited since
            t = _layer_edit(url)
            if t and p.stat().st_mtime > t: fresh = True; CHECKS['unchanged'] += 1
        if fresh:
            STATS['hit'] += 1; LAST = p.stat().st_mtime
            raw = gzip.decompress(p.read_bytes())
            if TRACE is not None: TRACE.append((url, params, hashlib.sha1(raw).hexdigest()))
            return json.loads(raw)
    except Exception: pass  # noqa: BLE001
    STATS['miss'] += 1
    if OFFLINE: raise RuntimeError('not in the bundle (offline stage)')
    j = fetch(); LAST = time.time()
    raw = json.dumps(j, separators=(',', ':')).encode()
    if TRACE is not None: TRACE.append((url, params, hashlib.sha1(raw).hexdigest()))
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(gzip.compress(raw, 6)); STATS['kept'] += 1
    except Exception: pass  # noqa: BLE001
    return j


def report():
    return (f"bundle answers: {STATS['hit']} read from the bundle, {STATS['miss']} asked the servers ({STATS['kept']} kept)"
            + (f"; layer change checks: {CHECKS['asked']} asked, {CHECKS['unchanged']} old answers kept (layer not edited since)" if CHECKS['asked'] else '')) if DIR else ''
