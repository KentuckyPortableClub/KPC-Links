"""SHARED LEAD TESTS (chat 2, Oct 27 2026; Fable's Discovery Bot design §2 step B: 'move the three testers into one shared file').
The pieces the explorers already use, in one place, so the Discovery Bot imports them instead of copying:
missing() / core() from kpc_outline_lead_test.py, name_field() from kpc_test_leads.py, official_org() from kpc_state_camps.py,
plus a bounded layer probe (attributes only, never geometry)."""
import json, re, sys, os, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from kpc_outline_lead_test import missing, core, low  # noqa: F401  (parks with no outline yet; name cores)
from kpc_test_leads import name_field  # noqa: F401
from kpc_state_camps import official_org, STATE_NAMES  # noqa: F401

UA = {'User-Agent': 'KPC discovery bot (kentuckyportableclub.github.io; ham radio club; 1 request a second)'}
FED_ORG = re.compile(r'bureau of land management|\bblm\b|forest service|\busfs\b|national park service|\bnps\b|fish (?:and|&) wildlife service|'
                     r'\busfws\b|army corps of engineers|\busace\b|u\.?s\.? geological survey|\busgs\b|bureau of reclamation|natural resources canada|'
                     r'parks canada|environment and climate change canada|statistics canada|government of (?:canada|alberta|british columbia|ontario|'
                     r'quebec|manitoba|saskatchewan|nova scotia|new brunswick|newfoundland|prince edward island|yukon|northwest territories|nunavut)', re.I)
LAST = {}


def get(url, params=None, timeout=20, tries=2):
    """1 request a second per host, 20 s timeout, 2 tries (design §2)."""
    host = urllib.parse.urlparse(url).netloc
    for i in range(tries):
        w = 1.0 - (time.time() - LAST.get(host, 0))
        if w > 0: time.sleep(w)
        LAST[host] = time.time()
        try:
            u = url + ('?' + urllib.parse.urlencode(params) if params else '')
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=timeout) as r:
                j = json.loads(r.read().decode('utf-8', 'replace'))
            if isinstance(j, dict) and j.get('error'): raise RuntimeError(str(j['error'])[:120])
            return j
        except Exception as e:  # noqa: BLE001
            last = e
            if '403' in str(e): break   # never retry a refusal (design §2 'what the bot never does')
            time.sleep(2 + 3 * i)
    raise last


def agency_org(name, st):
    """The state's own agency (the campground publisher test) or a federal / national agency."""
    return bool(name) and (official_org(name, st) or bool(FED_ORG.search(name)))


def probe_service(svc, miss, max_layers=6):
    """Does it answer, which layers, geometry, name field, record count, and how many parks with NO outline it names
    (name cores matched; attributes only, at most 5,000 names per layer). Returns a dict."""
    out = {'answers': False, 'layers': []}
    j = get(svc, {'f': 'json'})
    out['answers'] = True
    lays = (j.get('layers') or [])[:40]
    out['n_layers'] = len(lays)
    for L in lays[:max_layers]:
        lu = f"{svc.rstrip('/')}/{L.get('id')}"
        try: d = get(lu, {'f': 'json'})
        except Exception as e:  # noqa: BLE001
            out['layers'].append({'id': L.get('id'), 'err': str(e)[:60]}); continue
        nf = name_field(d.get('fields') or [])
        row = {'id': L.get('id'), 'name': (d.get('name') or '')[:60], 'geom': (d.get('geometryType') or '').replace('esriGeometry', ''), 'nameField': nf, 'fields': [x['name'] for x in (d.get('fields') or [])][:30]}
        if nf and not miss:
            try: row['records'] = get(lu + '/query', {'where': '1=1', 'returnCountOnly': 'true', 'f': 'json'}, timeout=30).get('count')
            except Exception: pass  # noqa: BLE001
        if nf and miss:
            names, off = set(), 0
            try:
                while off < 5000:
                    q = get(lu + '/query', {'where': '1=1', 'outFields': nf, 'returnGeometry': 'false', 'resultOffset': off, 'resultRecordCount': 1000, 'f': 'json'}, timeout=40)
                    fs = q.get('features') or []
                    names |= {core((f.get('attributes') or {}).get(nf)) for f in fs}
                    off += len(fs)
                    if not fs or not q.get('exceededTransferLimit'): break
                row['records'] = off
                hit = sorted({ref for ref, c, *_ in miss if c and c in names})
                row['names_missing'] = len(hit); row['parks'] = hit[:30]
            except Exception as e:  # noqa: BLE001
                row['qerr'] = str(e)[:60]
        out['layers'].append(row)
    return out
