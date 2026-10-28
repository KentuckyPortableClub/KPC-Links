#!/usr/bin/env python3
"""DISCOVERY BOT (chat 2, Oct 27 2026; design: .claude/build/research/KPC_DiscoveryBot_Design_Fable.md; replaces the portal scout).
Asks the CATALOGS where agencies list what they publish, by keyword per gap, tests each NEW lead with the shared lead tests
(kpc_leadtest.py), grades it 0-6 automatically and writes ONE ranked file. It never adds anything to the live data, never emails,
never fails. People (chat 8, Brandon) read the top of data/discovery/leads.md.
RULE SHEET (design §1): a lead = published by the managing agency / the state or province GIS office / a national register, not
read yet, filling one of the gaps (outline, ownership, map page, closures, access, roads/water, trail line, replaces). Not a lead:
non-agency hosts, city/council parks, historic markers, closed licences (WDPA, 'no derivatives'), theme layers that only NAME a park,
over 10 years old. Grey areas (Brandon YES Oct 27 11:51 AM): D-1 county layers = 'second witness' only; D-2 a .gov layer with no
licence = 'licence unknown'; D-3 the Maps tab = allow-listed agency hosts, 1 page per 3 s, 300 pages a run; D-4 no world catalogs.
Steps (STEPS=A,B,C,D; STATES=OH; MIN_A/MIN_B/MIN_C minutes each):
  A catalog search: ArcGIS Online (by the state's agency org ids, then state name + keyword with the publisher test), Socrata
    Discovery (the state's open-data domains), CKAN (data.gov / open.canada.ca and provincial catalogs).
  B test each new lead with a service: answers, layers, geometry, name field, parks with no outline it names (attributes only).
  C the 'Maps' tab: agency park pages (allow list in maps-tab.json) -> map / PDF links for parks with no official map link.
  D write data/discovery/leads.json + leads.md (top 50) + one observation per NEW A lead."""
import json, os, pathlib, re, sys, time
sys.path.insert(0, os.path.dirname(__file__))
import kpc_leadtest as T
from kpc_save import save_json

D = pathlib.Path('data/discovery')
T0 = time.time()
STEPS = set((os.environ.get('STEPS') or 'A,B,D').upper().replace(' ', '').split(','))
STATES = [s.upper() for s in (os.environ.get('STATES') or 'OH').replace(',', ' ').split()]
BUDGET = {'A': float(os.environ.get('MIN_A') or 40), 'B': float(os.environ.get('MIN_B') or 60), 'C': float(os.environ.get('MIN_C') or 45)}
MAPDBG = []
STAT = {'hits': 0, 'new': 0, 'already_read': 0, 'not_agency': 0, 'not_a_lead': 0, 'tested': 0, 'sleeping': 0, 'pages': 0, 'errors': 0}
NOT_LEAD = re.compile(r'\bcity\b|council|municipal|historic marker|hunting unit|fire district|census place|zoning|parcel sales|'
                      r'school|voting|precinct|sewer|utility|hydrant|crime|permit applications?|\btest\b|\bcopy\b|sample', re.I)
CLOSED = re.compile(r'no derivatives|internal use|not for redistribution|wdpa|all rights reserved', re.I)
OPEN = re.compile(r'cc[- ]?by|creative commons|public domain|no restrictions|open government licen|odbl|cc0|freely available|unrestricted', re.I)
CA_CKAN = {'CA-ON': 'https://data.ontario.ca', 'CA-BC': 'https://catalogue.data.gov.bc.ca', 'CA-AB': 'https://open.alberta.ca',
           'CA-QC': 'https://www.donneesquebec.ca/recherche'}


def notice(m): print('::notice title=Discovery bot::' + str(m).replace('\n', ' ')[:900], flush=True)
def late(step, t0): return time.time() - t0 > BUDGET[step] * 60
def load(p, d):
    try: return json.load(open(p))
    except Exception: return d  # noqa: BLE001


def svc_of(u):
    m = re.match(r'(https?://[^?#]+?/(?:Feature|Map)Server)', u or '', re.I)
    return m.group(1).rstrip('/') if m else (u or '').split('?')[0].rstrip('/')


def already_read():
    """Every service URL the data bots already read (rule 1b), found by scanning their files."""
    seen = set()
    files = ['data/state-gis.json', 'data/us-key/layers.json', 'data/ca-key/layers.json', 'data/access-layers.json',
             'data/campstate-layers.json', 'kpc-ky-data.json'] + [str(p) for p in pathlib.Path('data/trails').glob('index*.json')]
    for f in files:
        try: txt = open(f).read()
        except Exception: continue  # noqa: BLE001
        for u in re.findall(r'https?://[^"\s\\]+', txt): seen.add(svc_of(u).lower())
    return seen


def org_ids(st):
    """The state's agency ArcGIS Online org ids, from the hosts we already read (services*.arcgis.com/<org id>/)."""
    g = load('data/state-gis.json', {}).get('states', {}).get(st, [])
    return sorted({m.group(1) for x in g for m in [re.match(r'https?://services\d*\.arcgis\.com/([A-Za-z0-9]+)/', x.get('url', ''))] if m})


ORG = {}
def org_name(oid):
    if oid not in ORG:
        try: ORG[oid] = (T.get(f'https://www.arcgis.com/sharing/rest/portals/{oid}', {'f': 'json'}).get('name') or '')
        except Exception: ORG[oid] = ''  # noqa: BLE001
    return ORG[oid]


def step_a(st, kws, known, leads):
    t0 = time.time()
    sn = T.STATE_NAMES.get(st, st)
    orgs = org_ids(st)
    for gap, words in kws.items():
        for kw in words:
            if late('A', t0): return
            qs = [f'"{kw}" AND orgid:{o}' for o in orgs[:6]] + [f'"{kw}" AND "{sn}"']
            for q in qs:
                try: j = T.get('https://www.arcgis.com/sharing/rest/search', {'f': 'json', 'num': 100, 'q': q + ' AND (type:"Feature Service" OR type:"Map Service")'})
                except Exception: STAT['errors'] += 1; continue  # noqa: BLE001,E702
                for it in j.get('results') or []:
                    STAT['hits'] += 1
                    u = svc_of(it.get('url') or '')
                    if not u: continue
                    title = (it.get('title') or '')[:90]
                    if u.lower() in known: STAT['already_read'] += 1; continue
                    if NOT_LEAD.search(title) or CLOSED.search(it.get('licenseInfo') or ''): STAT['not_a_lead'] += 1; continue
                    org = org_name(it.get('orgId') or '')
                    county = bool(re.search(r'\bcounty\b', org, re.I))
                    if not T.agency_org(org, st) and not county: STAT['not_agency'] += 1; continue
                    # Oct 27 (Ohio test: Great Smoky Mountains layers topped the list): a publisher that is NOT the state's own agency
                    # (federal, county) counts only when the item's own title / snippet / tags name the state
                    if not T.official_org(org, st) and not re.search(r'\b' + re.escape(sn) + r'\b', ' '.join([title, it.get('snippet') or '', ' '.join(it.get('tags') or [])]), re.I):
                        STAT['not_this_state'] = STAT.get('not_this_state', 0) + 1; continue
                    lic = re.sub(r'<[^>]+>', ' ', it.get('licenseInfo') or '')[:200]
                    mod = time.strftime('%Y-%m-%d', time.gmtime((it.get('modified') or 0) / 1000)) if it.get('modified') else ''
                    if mod and mod < time.strftime('%Y-%m-%d', time.gmtime(time.time() - 10 * 365 * 86400)): STAT['not_a_lead'] += 1; continue
                    x = leads.setdefault(u.lower(), {'url': u, 'st': st, 'title': title, 'publisher': org[:70], 'catalog': 'ArcGIS Online',
                                                    'gaps': [], 'keywords': [], 'licence': lic.strip(), 'modified': mod, 'found': time.strftime('%Y-%m-%d'),
                                                    'kind': 'second witness' if county else 'new'})
                    if gap not in x['gaps']: x['gaps'].append(gap)
                    if kw not in x['keywords']: x['keywords'].append(kw)
            # Socrata (state open-data domains we know of in state-gis portals)
            for dom in socrata_domains(st):
                try: j = T.get('https://api.us.socrata.com/api/catalog/v1', {'domains': dom, 'q': kw, 'only': 'datasets,maps', 'limit': 50})
                except Exception: STAT['errors'] += 1; continue  # noqa: BLE001,E702
                for r in j.get('results') or []:
                    STAT['hits'] += 1
                    res = r.get('resource') or {}
                    u = (r.get('link') or '').rstrip('/')
                    if not u or u.lower() in known or NOT_LEAD.search(res.get('name') or ''): continue
                    x = leads.setdefault(u.lower(), {'url': u, 'st': st, 'title': (res.get('name') or '')[:90], 'publisher': dom, 'catalog': 'Socrata',
                                                    'gaps': [], 'keywords': [], 'licence': ((r.get('metadata') or {}).get('license') or '')[:120],
                                                    'modified': (res.get('updatedAt') or '')[:10], 'found': time.strftime('%Y-%m-%d'), 'kind': 'table (no map service)'})
                    if gap not in x['gaps']: x['gaps'].append(gap)
                    if kw not in x['keywords']: x['keywords'].append(kw)
            # CKAN (Canada: the federal catalog + provincial ones)
            for base in ckan_bases(st):
                try: j = T.get(base + '/api/3/action/package_search', {'q': kw, 'rows': 50})
                except Exception: STAT['errors'] += 1; continue  # noqa: BLE001,E702
                for p in (j.get('result') or {}).get('results') or []:
                    STAT['hits'] += 1
                    svcs = [svc_of(r.get('url') or '') for r in p.get('resources') or [] if re.search(r'/(Feature|Map)Server', r.get('url') or '', re.I)]
                    u = svcs[0] if svcs else f"{base}/dataset/{p.get('name')}"
                    if u.lower() in known or NOT_LEAD.search(p.get('title') or ''): continue
                    x = leads.setdefault(u.lower(), {'url': u, 'st': st, 'title': (p.get('title') or '')[:90], 'publisher': ((p.get('organization') or {}).get('title') or '')[:70],
                                                    'catalog': 'CKAN ' + base.split('//')[1].split('/')[0], 'gaps': [], 'keywords': [], 'licence': (p.get('license_title') or '')[:120],
                                                    'modified': (p.get('metadata_modified') or '')[:10], 'found': time.strftime('%Y-%m-%d'),
                                                    'kind': 'new' if svcs else 'download, needs a loader'})
                    if gap not in x['gaps']: x['gaps'].append(gap)
                    if kw not in x['keywords']: x['keywords'].append(kw)


def socrata_domains(st):
    P = load(D / 'portals.json', {}).get(st, {})
    return P.get('socrata', [])


def ckan_bases(st):
    P = load(D / 'portals.json', {}).get(st, {})
    b = list(P.get('ckan', []))
    if st.startswith('CA-'): b = ['https://open.canada.ca/data'] + ([CA_CKAN[st]] if st in CA_CKAN else []) + b
    return b


def grade(x):
    g = 0
    t = x.get('test') or {}
    if t.get('answers') and t.get('n_layers'): g += 1
    if any(l.get('nameField') and l.get('geom') for l in t.get('layers', [])): g += 1
    if T.agency_org(x.get('publisher', ''), x['st']) or re.search(r'\.gov\b|\.us\b|\.gc\.ca|\.gov\.[a-z]{2}\.ca', x['url']): g += 1
    lic = x.get('licence', '')
    if lic and OPEN.search(lic): g += 1
    elif not lic: x['licence_note'] = 'licence unknown'
    n = max([l.get('names_missing', 0) for l in t.get('layers', [])] or [0])
    if n >= 1: g += 1
    if n >= 5: g += 1
    x['parks_named'] = n
    x['grade'] = g
    x['band'] = 'A' if g >= 5 else 'B' if g >= 3 else 'C'
    if x.get('kind') == 'second witness': x['band'] = 'C'   # D-1: county layers never the outline
    return g


def step_b(leads, miss):
    t0 = time.time()
    for x in sorted(leads.values(), key=lambda v: (bool(v.get('tested')), v['st'])):
        if late('B', t0): break
        if x.get('tested') or not re.search(r'/(Feature|Map)Server$', x['url'], re.I): continue
        if x.get('sleeping_until', '') > time.strftime('%Y-%m-%d'): STAT['sleeping'] += 1; continue
        st2 = x['st'] if x['st'].startswith('CA-') else x['st']
        try:
            x['test'] = T.probe_service(x['url'], miss.get(st2, []) if 'outline' in x['gaps'] else [])
            x['tested'] = time.strftime('%Y-%m-%d'); x.pop('fails', None); STAT['tested'] += 1
        except Exception as e:  # noqa: BLE001
            x['fails'] = x.get('fails', 0) + 1; x['last_error'] = str(e)[:80]
            if x['fails'] >= 2: x['sleeping_until'] = time.strftime('%Y-%m-%d', time.gmtime(time.time() + 60 * 86400))


def step_c(st, leads):
    """The 'Maps' tab with a real browser: agency park pages on the allow list -> map / PDF links."""
    cfg = load(D / 'maps-tab.json', {}).get(st)
    if not cfg: return
    try: from playwright.sync_api import sync_playwright
    except Exception: notice('Maps tab: no browser on this runner'); return  # noqa: BLE001,E702
    allow, files = cfg.get('hosts', []), cfg.get('files', [])
    have = load('data/parkinfo-web.json', {}).get('parks', {})
    parks = load(f'data/parkinfo/US-{st}.json', {}).get('parks', {})
    todo = [(r, v[0], v[1]) for r, v in parks.items() if v[1] and any(h in v[1] for h in allow) and not (have.get(r) or {}).get('map')]
    t0, pages, errs = time.time(), 0, {}
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(user_agent=T.UA['User-Agent'])
        for ref, name, url in todo[:int(cfg.get('max', 300))]:
            host = url.split('/')[2]
            if late('C', t0) or pages >= 300 or errs.get(host, 0) >= 5: break
            try:
                pg.goto(url, timeout=30000, wait_until='networkidle'); pages += 1
                links = pg.eval_on_selector_all('a[href]', 'as => as.map(a => [a.href, (a.innerText||"").trim().slice(0,60)])')
            except Exception: errs[host] = errs.get(host, 0) + 1; time.sleep(3); continue  # noqa: BLE001,E702
            hit = [(h, t) for h, t in links if re.search(r'map|\.pdf|geopdf|brochure', h + ' ' + t, re.I)
                   and any(f in h.split('/')[2] for f in files) and not re.search(r'google\.|bing\.|apple\.com/maps|mapquest', h, re.I)]
            if pages <= 3: MAPDBG.append({'ref': ref, 'url': url, 'links': len(links), 'map_like': [h for h, t in links if re.search(r'map|\.pdf', h + ' ' + t, re.I)][:8], 'kept': len(hit)})
            if hit:
                k = f'map-page:{ref}'
                leads[k] = {'url': hit[0][0], 'st': st, 'ref': ref, 'title': f'{name}: {hit[0][1] or "map"}', 'publisher': host, 'catalog': 'Maps tab',
                            'gaps': ['map page'], 'keywords': [], 'licence': '', 'found': time.strftime('%Y-%m-%d'), 'kind': 'map page',
                            'all_links': [h for h, _ in hit][:6], 'grade': 5 if hit[0][0].lower().endswith('.pdf') else 4}
                leads[k]['band'] = 'A' if leads[k]['grade'] >= 5 else 'B'
            time.sleep(3)
        b.close()
    STAT['pages'] += pages


def main():
    kws = load(D / 'keywords.json', {}).get('gaps', {})
    if not kws: notice('no keywords.json: nothing to search'); return
    known = already_read()
    old = load(D / 'leads.json', {}).get('leads', {})
    # Oct 27: leads kept from an earlier run must pass today's publisher test too (the Ohio test kept Great Smoky Mountains layers)
    leads = {k: v for k, v in old.items() if v.get('catalog') == 'Maps tab' or T.official_org(v.get('publisher', ''), v['st'])
             or re.search(r'\b' + re.escape(T.STATE_NAMES.get(v['st'], v['st'])) + r'\b', v.get('title', ''), re.I)}
    before = set(leads)
    miss = T.missing() if 'B' in STEPS else {}
    for st in STATES:
        st_key = st if st.startswith('CA-') else st
        if 'A' in STEPS: step_a(st_key, kws, known, leads)
        if 'C' in STEPS: step_c(st_key, leads)
        save_json(D / 'leads.json', {'about': 'Discovery bot leads (never used by the live data; chat 8 reads leads.md).', 'date': time.strftime('%Y-%m-%d'), 'leads': leads}, indent=1)
    if 'B' in STEPS: step_b(leads, miss)
    for x in leads.values():
        if x.get('catalog') != 'Maps tab': grade(x)
    new = sorted(set(leads) - before)
    STAT['new'] = len(new)
    # learning loop: which keyword found what this run
    found = {}
    for k in new:
        for kw in leads[k].get('keywords', []): found.setdefault(kw, []).append(leads[k]['url'])
    rank = sorted(leads.values(), key=lambda v: (-v.get('grade', 0), not T.official_org(v.get('publisher', ''), v['st']), -v.get('parks_named', 0), v['st']))
    save_json(D / 'leads.json', {'about': 'Discovery bot leads (never used by the live data; chat 8 reads leads.md).', 'date': time.strftime('%Y-%m-%d'),
                                 'stats': STAT, 'maps_tab_sample': MAPDBG, 'found_by_keyword_this_run': found, 'leads': leads}, indent=1)
    md = ['# Discovery bot: top 50 leads', f"Run {time.strftime('%Y-%m-%d')}, states {' '.join(STATES)}. The bot's number is the queue order only; chat 8 gives the real A/B/C.", '',
          '| Band | Grade | State | Gap | What | Publisher | Parks named | Kind | Link |', '|---|---|---|---|---|---|---|---|---|']
    for x in rank[:50]:
        md.append(f"| {x.get('band', '')} | {x.get('grade', 0)} | {x['st']} | {', '.join(x.get('gaps', []))} | {x.get('title', '')[:60].replace('|', '/')} | "
                  f"{x.get('publisher', '')[:40].replace('|', '/')} | {x.get('parks_named', '')} | {x.get('kind', '')}{' · ' + x['licence_note'] if x.get('licence_note') else ''} | {x['url']} |")
    (D / 'leads.md').write_text('\n'.join(md) + '\n')
    obs = [leads[k] for k in new if leads[k].get('band') == 'A']
    if obs:
        save_json(D / 'new-a-leads.json', {'date': time.strftime('%Y-%m-%d'), 'leads': [{'st': x['st'], 'title': x['title'], 'url': x['url'], 'gaps': x['gaps']} for x in obs]}, indent=1)
    bands = {b: sum(1 for x in leads.values() if x.get('band') == b) for b in 'ABC'}
    notice(f"{' '.join(STATES)}: {STAT} · bands {bands} · {len(obs)} new A · {round((time.time() - T0) / 60)} min")


if __name__ == '__main__':
    try: main()
    except Exception as e:  # noqa: BLE001
        notice(f'stopped: {type(e).__name__}: {e}')
    sys.exit(0)
