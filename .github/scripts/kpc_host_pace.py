"""kpc_host_pace.py: at most one request every 2 seconds to each host, for every urllib urlopen in a key builder.

Nov 3, 2026 (Mapping, code review of the key builders against the proposed rules, rule 29 / handoff hard rule: "at most 1
request every 2 s per host"): kpc_us_key, kpc_ca_key and kpc_world_key paged with 0.25-0.6 s pauses (PAD-US, FWS, CPCAD,
the state GIS tables). install() wraps urllib.request.urlopen once, so every call site in those scripts is paced by host without
editing each one. KPC_HOST_GAP sets the gap in seconds (default 2.0; it is never set lower than 2.0).
KPC owner, 2026-11-13: a slow host (kpc_net_guard.SLOW_HOSTS, apps.fs.usda.gov) waits its own longer gap (10 s).
The retry waits in each script (8 s x try) are on top of this. Nothing else changes: same User-Agent, same requests.
"""
import os, threading, time, urllib.parse, urllib.request
import kpc_net_guard
kpc_net_guard.install()   # never-contact hosts refused before any request (every importer gets it)

GAP = max(2.0, float(os.environ.get('KPC_HOST_GAP') or 2.0))
_last, _lk, _orig = {}, threading.Lock(), None
stat = {'requests': 0, 'waited_s': 0.0}


def host_of(req):
    u = getattr(req, 'full_url', None) or str(req)
    return urllib.parse.urlsplit(u).netloc.lower()


def wait(host):
    with _lk:
        now = time.monotonic()
        w = _last.get(host, -1e9) + max(GAP, kpc_net_guard.min_gap(host)) - now
        if w > 0:
            time.sleep(w); stat['waited_s'] += w
        _last[host] = time.monotonic(); stat['requests'] += 1


def install():
    """Wrap urllib.request.urlopen (once per process)."""
    global _orig
    if _orig is not None: return
    _orig = urllib.request.urlopen

    def paced(req, *a, **k):
        wait(host_of(req))
        return _orig(req, *a, **k)
    paced.__wrapped__ = _orig
    urllib.request.urlopen = paced
