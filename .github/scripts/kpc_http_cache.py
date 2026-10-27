"""ASSEMBLY LINE disk cache (chat 2, Oct 27 2026; HQ 5:23 PM: fetcher -> worker -> checker, bundles as KPC-Data release assets).
Every map-server answer the 2-fer bot reads (outlines, ownership, water, roads, closures) can be kept on disk, so a later stage
or a rerun after a bug fix reads it from the bundle instead of asking the agency again (polite + fast).
HTTP_CACHE=<dir> turns it on; HTTP_CACHE_DAYS (default 21) = how old an answer may be; HTTP_OFFLINE=1 = never ask the
server (a miss raises 'not in the bundle'). Answers that are errors are never kept. Off when HTTP_CACHE is not set."""
import gzip, hashlib, json, os, pathlib, time

DIR = os.environ.get('HTTP_CACHE') or ''
DAYS = float(os.environ.get('HTTP_CACHE_DAYS') or 21)
OFFLINE = os.environ.get('HTTP_OFFLINE') == '1'
STATS = {'hit': 0, 'miss': 0, 'kept': 0}


def _path(url, params):
    k = hashlib.sha1((url + '|' + json.dumps(params, sort_keys=True, default=str)).encode()).hexdigest()
    return pathlib.Path(DIR) / k[:2] / (k + '.json.gz')


def cached(url, params, fetch):
    """fetch() = the real request (returns parsed JSON). Cached when HTTP_CACHE is set."""
    if not DIR: return fetch()
    p = _path(url, params)
    try:
        if p.exists() and time.time() - p.stat().st_mtime < DAYS * 86400:
            STATS['hit'] += 1
            return json.loads(gzip.decompress(p.read_bytes()))
    except Exception: pass  # noqa: BLE001
    STATS['miss'] += 1
    if OFFLINE: raise RuntimeError('not in the bundle (offline stage)')
    j = fetch()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(gzip.compress(json.dumps(j, separators=(',', ':')).encode(), 6)); STATS['kept'] += 1
    except Exception: pass  # noqa: BLE001
    return j


def report():
    return f"bundle answers: {STATS['hit']} read from the bundle, {STATS['miss']} asked the servers ({STATS['kept']} kept)" if DIR else ''
