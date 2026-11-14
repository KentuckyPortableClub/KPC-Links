#!/usr/bin/env python3
"""Nov 8 (Brandon 4:31 PM CST, t764u: "for example GA it searches pad and state level that way it dont miss many").
Builds data/maprep-state-layers.json: the state / province layers the Tool Box searches next to PAD-US / CPCAD.
Source = the layers the answer keys already use (KPC-Data data/us-key/layers.json 'sg<st>?' rows, data/ca-key/layers.json).
Only layers whose host robots.txt allows the query path (a 401/403 robots answer counts as a disallow, so every
services*.arcgis.com layer is left out), never a banned host, never a hub portal. Each kept layer is asked once
(returnCountOnly) with an Origin header to see if a browser may read it (CORS). Run by hand only:
  DATA=<KPC-Data checkout> python3 .github/scripts/kpc_maprep_state_layers.py"""
import csv, json, os, re, sys, time, urllib.request, urllib.robotparser, urllib.parse, gzip
import kpc_net_guard; kpc_net_guard.install()
D = os.environ.get('DATA', '../KPC-Data'); OUT = 'data/maprep-state-layers.json'
BANNED = re.compile(r'ncnhde\.natureserve\.org|services\.arcgis\.com/33TOOklri9xpic7U|maps\.gov\.bc\.ca', re.I)
UA = 'KPC-Links maprep layer check (https://kentuckyportableclub.github.io)'
PROV = [('AB', r'\bAB\b|alberta'), ('BC', r'\bBC\b|british columbia'), ('SK', r'\bSK\b|saskatchewan'), ('MB', r'\bMB\b|manitoba'), ('ON', r'\bON\b|ontario'),
        ('QC', r'\bQC\b|qu[eé]bec'), ('NB', r'\bNB\b|new brunswick'), ('NS', r'\bNS\b|nova scotia'), ('PE', r'\bPE\b|\bPEI\b|prince edward'), ('NL', r'\bNL\b|newfoundland'),
        ('YT', r'yukon'), ('NT', r'\bNT\b|northwest territories'), ('NU', r'nunavut')]
def load(p):
    f = os.path.join(D, p)
    if os.path.exists(f): return json.load(open(f, encoding='utf-8'))
    if os.path.exists(f + '.gz'): return json.load(gzip.open(f + '.gz', 'rt', encoding='utf-8'))
    return {}
def get(u, hdr=None, t=20):
    r = urllib.request.Request(u, headers=dict({'User-Agent': UA, 'Accept': 'application/json, */*'}, **(hdr or {})))   # Nov 14: some servers answer HTTP 406 without an Accept header
    with urllib.request.urlopen(r, timeout=t) as x: return x.status, dict(x.headers), x.read()
RB = {}
def robots_ok(u):
    p = urllib.parse.urlparse(u); host = p.scheme + '://' + p.netloc
    if re.match(r'services(?:\d+|-[a-z0-9]+)?\.arcgis\.com$', p.netloc, re.I): return False, 'not available for this tool'
    if host not in RB:
        rp = urllib.robotparser.RobotFileParser()
        try:
            st, h, b = get(host + '/robots.txt'); rp.parse(b.decode('utf-8', 'replace').splitlines()); RB[host] = ('ok', rp)
        except urllib.error.HTTPError as e:
            RB[host] = ('deny', None) if e.code in (401, 403) else ('none', None)
        except Exception as e:
            RB[host] = ('none', None)
        time.sleep(1)
    k, rp = RB[host]
    if k == 'deny': return False, 'not available for this tool'
    if k == 'none': return True, 'available'
    return (rp.can_fetch(UA, u), 'available' if rp.can_fetch(UA, u) else 'not available for this tool')
# Nov 8 (Brandon 4:50 PM CST, t766u: do the state layers list ownership and management?): the fact fields each layer carries
FACTS = {'owner': r'^(owner|own_?name|owner_?name|own|ownership|landowner|own_?agency|owner_?e|propr\w*)$|owner',
         'manager': r'^(manager|mgr_?name|mang_?name|managed_?by|mgmt_?\w*|manag\w*|admin\w*|unit_?mgr)$|manag|admin',
         'agency': r'^(agency|agncy|agency_?name|dept|department|division|org\w*)$|agency',
         'designation': r'^(desig\w*|des_?tp|type|unit_?type|class\w*|category|park_?type|area_?type|land_?type|type_?e)$|desig',
         'acres': r'^(acres|gis_?acres|acreage|total_?acres|area_?ac\w*|calc_?acres|deeded_?acres)$|acre',
         'website': r'^(url|website|web_?site|web|link|webpage|web_?link|homepage|more_?info)$|url|website|webpage'}
def fact_fields(base):
    try: _, _, b = get(base + '?f=json'); j = json.loads(b)
    except Exception: return None
    fs = [(f.get('name') or '', f.get('alias') or '', f.get('type') or '') for f in j.get('fields') or []]
    out = {}
    for k, pat in FACTS.items():
        exact, loose = pat.split('|', 1)[0] + '|' + pat.split('|', 1)[1].split(')$|')[0] + ')$', pat.rsplit('|', 1)[1]
        for strict in (True, False):
            for n, a, t in fs:
                if k in ('owner', 'manager', 'agency') and re.search(r'(_st|_id|syst\w*|placename|_?code\w*|_cd|_num|_no)$|^code', n, re.I): continue   # a state code, an id or a place name is not a party
                if k != 'acres' and t not in ('esriFieldTypeString', 'esriFieldTypeSmallInteger', 'esriFieldTypeInteger'): continue
                if k == 'acres' and t not in ('esriFieldTypeDouble', 'esriFieldTypeSingle', 'esriFieldTypeInteger', 'esriFieldTypeSmallInteger'): continue
                if re.search(pat.split(')$|')[0] + ')$' if strict else loose, n, re.I) or (not strict and re.search(loose, a, re.I)):
                    out[k] = n; break
            if k in out: break
    return out
def name_field(base):
    try: _, _, b = get(base + '?f=json'); j = json.loads(b)
    except Exception: return None
    fs = [f['name'] for f in j.get('fields') or [] if f.get('type') == 'esriFieldTypeString']
    for pat in (r'^(name_?e|name_?en|nom_?e|name_?eng|parkname|park_name|name)$', r'name', r'nom'):
        for f in fs:
            if re.search(pat, f, re.I): return f
    return None
def svc_label(lab, u):
    m = re.search(r'/services/(?:[^/]+/)?([^/]+)/(?:MapServer|FeatureServer)/(\d+)', u)
    return lab + (' \u00b7 ' + m.group(1).replace('_', ' ') + (' ' + m.group(2) if m.group(2) not in ('0',) else '') if m else '')
def main():
    rows = []
    for pre, v in sorted(load('data/us-key/layers.json').items()):
        m = re.match(r'^sg([a-z]{2})[a-z]$', pre)
        if m and isinstance(v, list) and v and str(v[0]).startswith('https://'): rows.append({'area': m.group(1).upper(), 'pre': pre, 'url': v[0], 'field': v[1], 'label': re.sub(r'\s*\((?:[^()]*state GIS table|credit[^)]*|owner [^)]*|[A-Za-z ]*AGOL org[^)]*)\)', '', v[2]).strip()})
    for k, v in sorted(load('data/ca-key/layers.json').items()):
        u = (v[0] if isinstance(v, list) and v else v) if v else ''
        if not str(u).startswith('https://'): continue
        txt = k + ' ' + u; area = next((c for c, pat in PROV if re.search(pat, txt, re.I)), None)
        if not area: continue
        rows.append({'area': area, 'pre': 'ca' + re.sub(r'[^a-z]', '', k.lower())[:10], 'url': u.rstrip('/') + ('' if u.rstrip('/').endswith('/query') else '/query'), 'field': None, 'label': k.strip(), 'ca': True})
    out = {}
    for r in rows:
        u = r['url']; r['ok'] = False
        if BANNED.search(u): r['why'] = 'banned host'
        elif re.search(r'hub\.arcgis\.com|opendata\.arcgis\.com', u, re.I): r['why'] = 'hub portal (60 s crawl delay): not read live'
        else:
            ok, why = robots_ok(u); r['why'] = why
            if ok:
                base = u[:-6] if u.endswith('/query') else u
                if not r['field']: r['field'] = name_field(base)
                if not r['field']: r['why'] = 'no name field found'
                else:
                    try:
                        st, h, b = get(u + '?' + urllib.parse.urlencode({'where': '1=1', 'returnCountOnly': 'true', 'f': 'json'}), {'Origin': 'https://kentuckyportableclub.github.io'})
                        ac = {k.lower(): v for k, v in h.items()}.get('access-control-allow-origin', '')
                        j = json.loads(b); r['count'] = j.get('count')
                        if 'error' in j: r['why'] = 'layer error: ' + str(j['error'].get('message'))[:80]
                        elif ac not in ('*', 'https://kentuckyportableclub.github.io'): r['why'] = 'no CORS: a browser cannot read it'
                        else: r['ok'] = True
                    except Exception as e: r['why'] = 'did not answer: ' + str(e)[:80]
                    if r['ok']: r['facts'] = fact_fields(base) or {}
                time.sleep(1)
        out.setdefault(r['area'], []).append({k: r.get(k) for k in ('pre', 'url', 'field', 'label', 'ok', 'why', 'count', 'facts')})
    for a in out.values():   # the same agency twice in one place: add the service name (Iowa DNR · Public Lands)
        seen = {}
        for x in a: seen[x['label']] = seen.get(x['label'], 0) + 1
        for x in a:
            if seen[x['label']] > 1: x['label'] = svc_label(x['label'], x['url'])
    # Nov 8: hand-downloaded state/province layers (Brandon) kept as local site files as local site files (no live fetch)
    HAND = [
      ('GA', 'handgas', 'Georgia State Parks (DNR, hand download)', 'data/maprep-layers/us-ga-stateparks.geojson', 'PropName', 'gas', {'designation': 'PropName', 'acres': 'Acres'}),
      ('GA', 'handgaw', 'Georgia DNR Wildlife Resources (WMA / PFA / hatchery, hand download)', 'data/maprep-layers/us-ga-wma.geojson', 'PropName', 'gaw', {'owner': 'Owner', 'acres': 'Acres', 'designation': 'PropName'}),
      ('TX', 'handtxs', 'Texas Parks & Wildlife (state parks, hand download)', 'data/maprep-layers/us-tx-stateparks.geojson', 'ParkName', 'txs', {'designation': 'PropType'}),
      ('TX', 'handtxw', 'Texas Parks & Wildlife (WMAs, hand download)', 'data/maprep-layers/us-tx-wma.geojson', 'LoName', 'txw', {'designation': 'BndryType'}),
      ('PA', 'handpas', 'Pennsylvania Game Commission (State Game Lands, hand download)', 'data/maprep-layers/us-pa-sgl.geojson', 'sgl_name', 'pas', {'acres': 'gis_area_ac', 'designation': 'sgl_status'}),
      ('MB', 'handmbp', 'Manitoba provincial parks (hand download; replaces missing shapes)', 'data/maprep-layers/ca-mb-provparks.geojson', 'NAME_E', 'mbp', {'designation': 'TYPE_E', 'acres': 'O_AREA', 'website': 'URL', 'manager': 'MGMT_E', 'owner': 'OWNER_E'}),
    ]
    for st, pre, lab, f, field, k, facts in HAND:
        if not os.path.exists(f): continue
        fs = json.load(open(f, encoding='utf-8')).get('features') or []
        r = {'pre': pre, 'url': f, 'field': field, 'label': lab, 'ok': True,
             'why': 'the club keeps a hand-downloaded copy (Brandon Nov 8); kept as a site file (hand download); no live fetch',
             'local': 'hand', 'k': k, 'count': len(fs), 'facts': facts}
        out.setdefault(st, []); out[st] = [r] + [x for x in out.get(st, []) if not (x.get('local') == 'hand' and x.get('k') == k)]
    # follow-up to #94: Kentucky's official layers are the club's own map files (kpc-bounds.js KY list), not live servers
    KY = [('bstate', 'Kentucky State Parks', 'ky-state-parks.geojson'), ('bwma', 'Kentucky Fish & Wildlife WMAs and public hunting areas', 'ky-hunting-areas.geojson'),
          ('bsnp', 'Kentucky Office of Nature Preserves (state nature preserves)', 'ky-nature-preserves.geojson'), ('bsna', 'Kentucky Office of Nature Preserves (state natural areas)', 'ky-natural-areas.geojson'),
          ('bwild', 'Kentucky Office of Nature Preserves (wild river corridors)', 'ky-wild-rivers.geojson'), ('bdbnfo', 'U.S. Forest Service (Daniel Boone NF owned land)', 'ky-dbnf-owned.geojson'),
          ('bnps', 'National Park Service (Kentucky units)', 'ky-nps.geojson'), ('bwilder', 'U.S. Forest Service (wilderness areas)', 'ky-wilderness.geojson'), ('bfws', 'U.S. Fish & Wildlife Service (refuges and hatcheries)', 'ky-fws.geojson')]
    kyr = []
    for k, lab, f in KY:
        if not os.path.exists(f): continue
        fs = json.load(open(f, encoding='utf-8')).get('features') or []; props = set(x for ft in fs for x in (ft.get('properties') or {}))
        facts = {key: next(c for c in cands if c in props) for key, cands in (('owner', ['owner', 'OWNER']), ('manager', ['MANAGER']), ('designation', ['TYPE']), ('acres', ['ACRES']), ('website', ['URL'])) if any(c in props for c in cands)}
        r = {'pre': 'kyl' + k, 'url': f, 'field': 'NAME', 'label': lab, 'ok': True, 'why': "the club's own Kentucky map file (same layer Check all uses; read from this site, no outside server)", 'local': 'ky', 'k': k, 'count': len(fs), 'facts': facts}
        if k == 'bwma': r['owners'] = 'data/ky-wma-owners.json'
        kyr.append(r)
    if kyr: out['KY'] = kyr
    doc = {'about': __doc__.split('\n')[0] + ' Built by .github/scripts/kpc_maprep_state_layers.py (by hand).', 'built': time.strftime('%Y-%m-%d'), 'areas': out}
    if os.environ.get('VERIFIED'): print('verified list:', apply_verified(doc, os.environ['VERIFIED']))
    with open(OUT, 'w', encoding='utf-8', newline='') as f: json.dump(doc, f, indent=1, ensure_ascii=False); f.write('\n')
    n = sum(1 for a in out.values() for x in a if x['ok']); print(f'{n} layers OK of {len(rows)}')
    for a in ('GA', 'KY', 'IA', 'PA', 'TX'): print(a, [(x['label'][:40], x['ok'], x['why'][:50]) for x in out.get(a, [])])


# Nov 14 review (owner answers): a layer on a services*.arcgis.com or apps.fs.usda.gov server is read LIVE IN THE MEMBER'S BROWSER only
# when the verified-layers list says so (the bots never contact those hosts: kpc_net_guard.py is unchanged). Applied offline, no requests.
#   publish yes                    -> shown, credit + licence class carried
#   private until licence read     -> shown on this members page as a live lookup only (never saved, never published)
#   terms forbid sharing / copying -> hidden, even for live lookups
# NO_SHARE_LIVE = layers on other servers whose agency forbids sharing (Minnesota DNR, NJDEP, Hawaii): hidden too.
NO_SHARE_LIVE = {'sgmna', 'sgmnb', 'sgmnc', 'sgmne', 'sgmnf', 'sgnja', 'sghia', 'sghib'}
DEAD = {'sgcod': 'service no longer answers (Nov 14 review)'}
def norm_url(u): return re.sub(r'/query$', '', u.split('?')[0].rstrip('/')).lower()
def apply_verified(doc, path):
    rows = {norm_url(r['layer address']): r for r in csv.DictReader(open(path, encoding='utf-8'))}
    n = {'live': 0, 'private': 0, 'hidden': 0, 'kept': 0}
    for layers in doc['areas'].values():
        for x in layers:
            r = rows.get(norm_url(x['url'])); pub = (r or {}).get('publish', '')
            if x['pre'] in DEAD: x.update(ok=False, why=DEAD[x['pre']] if x.get('read') != 'saved copy' else 'saved copy — not queried live (' + DEAD[x['pre']] + ')'); x.pop('verified', None); n['hidden'] += 1
            elif x['pre'] in NO_SHARE_LIVE: x.update(ok=False, why=('saved copy — not queried live (' if x.get('read') == 'saved copy' else '(') + 'agency terms forbid sharing: hidden)'); x.pop('verified', None); n['hidden'] += 1
            elif not r: continue
            elif r['fetch'] != 'yes' or pub.startswith('no (terms forbid'): x.update(ok=False, why=('saved copy — not queried live (' if x.get('read') == 'saved copy' else '(') + 'agency terms forbid sharing: hidden)'); x.pop('verified', None); n['hidden'] += 1
            elif BANNED.search(x['url']) or not x.get('field'): n['kept'] += 1   # banned host or no name field: left as it was
            elif pub == 'yes':
                x.update(ok=True, verified=True, why='licence checked ' + (r.get('date read') or '') + ': read live in the browser', credit=r.get('credit line') or '', licence=r.get('licence class') or ''); x.pop('private', None); n['live'] += 1
            elif pub.startswith('no (private until'):
                x.update(ok=True, verified=True, private=True, why='licence not read yet: live lookup only, never saved or published', credit=r.get('credit line') or '', licence=r.get('licence class') or ''); n['private'] += 1
            else: n['kept'] += 1
    return n


def facts_only():
    """refresh only the fact fields of the layers already marked ok (no robots or CORS re-check needed for those)"""
    doc = json.load(open(OUT, encoding='utf-8'))
    for a in doc['areas'].values():
        for x in a:
            if x.get('ok'): u = x['url']; x['facts'] = fact_fields(u[:-6] if u.endswith('/query') else u) or {}; time.sleep(1)
    with open(OUT, 'w', encoding='utf-8', newline='') as f: json.dump(doc, f, indent=1, ensure_ascii=False); f.write('\n')

def verified_only(path):
    """re-apply the verified-layers list to the file as it is (no requests): --verified-only <csv>"""
    doc = json.load(open(OUT, encoding='utf-8')); print('verified list:', apply_verified(doc, path))
    with open(OUT, 'w', encoding='utf-8', newline='') as f: json.dump(doc, f, indent=1, ensure_ascii=False); f.write('\n')

if __name__ == '__main__':
    verified_only(sys.argv[sys.argv.index('--verified-only') + 1]) if '--verified-only' in sys.argv else facts_only() if '--facts-only' in sys.argv else main()
