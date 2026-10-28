#!/usr/bin/env python3
"""SOUTHEAST SOURCE PROBE (chat 2, Oct 27 2026; HQ 9:46 PM, from chat 8's source book .claude/build/research/SE/).
Chat sessions cannot reach state map servers, so a runner tests every candidate layer ONCE: does it answer, what geometry,
which field holds the name, how many areas, three sample names, its copyright / licence text and any date, and (rule 14) which
field carries land ownership + the values in it. For a SERVER root it lists folders and services so we can see what exists
(TVA, the Florida water districts, NC). Writes .claude/build/research/SE/candidates-tested.json and prints one notice a layer.
Adds nothing to the live data. Never fails."""
import json, pathlib, re, sys, time, urllib.parse, urllib.request
UA = {'User-Agent': 'KPC park mapping (kentuckyportableclub.github.io; ham radio club)'}
D = pathlib.Path('.claude/build/research/SE')
OWNW = re.compile(r'owner|ownership|owncode|managing|manager|mang|agency|admin|fee|title|tenure', re.I)
NAMEW = re.compile(r'name|nm$|label|title|site|area|unit|prop', re.I)


def notice(m): print('::notice title=SE probe::' + str(m).replace('\n', ' ')[:900], flush=True)


def get(u, p=None, t=40):
    q = dict(p or {}); q.setdefault('f', 'json')
    with urllib.request.urlopen(urllib.request.Request(u + '?' + urllib.parse.urlencode(q), headers=UA), timeout=t) as r:
        j = json.loads(r.read().decode('utf-8', 'replace'))
    if isinstance(j, dict) and j.get('error'): raise RuntimeError(str(j['error'])[:140])
    return j


def layer(x):
    out = {k: x[k] for k in ('st', 'kind', 'ag', 'url', 'note') if k in x}
    j = get(x['url'])
    out['answers'] = True
    out['service'] = (j.get('name') or j.get('mapName') or j.get('documentInfo', {}).get('Title') or '')[:70]
    out['licence'] = re.sub(r'<[^>]+>', ' ', str(j.get('copyrightText') or (j.get('documentInfo') or {}).get('Copyright') or ''))[:200].strip()
    desc = re.sub(r'<[^>]+>', ' ', str(j.get('serviceDescription') or j.get('description') or ''))
    out['date_in_text'] = sorted(set(re.findall(r'\b(19|20)\d{2}\b', desc[:4000]) and re.findall(r'\b(?:19|20)\d{2}\b', desc[:4000])))[-3:]
    out['description'] = ' '.join(desc.split())[:300]
    lays = j.get('layers')
    if lays is None and 'geometryType' in j: lays = [{'id': None}]      # the URL is a layer already
    rows = []
    for L in (lays or [])[:12]:
        lu = x['url'] if L.get('id') is None else f"{x['url'].rstrip('/')}/{L['id']}"
        try: d = get(lu)
        except Exception as e: rows.append({'id': L.get('id'), 'error': str(e)[:70]}); continue
        flds = [f['name'] for f in d.get('fields') or []]
        nm = x.get('nm') or next((f for f in flds if NAMEW.search(f) and not re.search(r'own|mang|agency|type|county', f, re.I)), '')
        own = x.get('owner') or next((f for f in flds if OWNW.search(f)), '')
        row = {'id': L.get('id'), 'name': (d.get('name') or '')[:50], 'geom': (d.get('geometryType') or '').replace('esriGeometry', ''),
               'nameField': nm, 'ownerField': own, 'fields': flds[:25]}
        try: row['records'] = get(lu + '/query', {'where': '1=1', 'returnCountOnly': 'true'}).get('count')
        except Exception as e: row['countErr'] = str(e)[:60]
        for f, key, n in ((nm, 'sample', 5), (own, 'owner_values', 60)):
            if not f: continue
            try:
                q = get(lu + '/query', {'where': '1=1', 'outFields': f, 'returnGeometry': 'false', 'resultRecordCount': n,
                                        **({'returnDistinctValues': 'true'} if key == 'owner_values' else {})}, t=60)
                vals = [(ft.get('attributes') or {}).get(f) for ft in q.get('features') or []]
                row[key] = sorted({str(v)[:40] for v in vals if v})[:12] if key == 'owner_values' else [str(v)[:40] for v in vals][:5]
            except Exception as e: row[key + 'Err'] = str(e)[:60]
        rows.append(row)
        time.sleep(.5)
    out['layers'] = rows
    return out


def server(x):
    out = {k: x[k] for k in ('st', 'what', 'url')}
    j = get(x['url'])
    out['folders'] = (j.get('folders') or [])[:40]
    out['services'] = [s.get('name') for s in (j.get('services') or [])][:40]
    hits = []
    for f in out['folders'][:12]:
        try: sj = get(f"{x['url']}/{f}")
        except Exception: continue
        for s in sj.get('services') or []:
            n = s.get('name') or ''
            if re.search(r'land|park|boundar|recreat|public|wildlife|conserv|trail|reservoir|property|fee|owner', n, re.I):
                hits.append(f"{n} ({s.get('type')})")
        time.sleep(.4)
    out['likely'] = hits[:40]
    return out


def main():
    cfg = json.load(open(D / 'candidates.json'))
    res = {'about': 'Probe of chat 8\'s Southeast candidates, run on a GitHub runner (chat sessions cannot reach these servers).',
           'date': time.strftime('%Y-%m-%d'), 'layers': [], 'servers': []}
    for x in cfg.get('layers') or []:
        try: r = layer(x)
        except Exception as e: r = {k: x.get(k) for k in ('st', 'kind', 'url')}; r['answers'] = False; r['error'] = str(e)[:140]
        res['layers'].append(r)
        best = next((l for l in r.get('layers') or [] if l.get('records')), {})
        notice(f"{r['st']} {r.get('kind', '')}: " + ('OK ' + str(best.get('records')) + ' areas, name=' + str(best.get('nameField')) +
               ', owner=' + str(best.get('ownerField')) + ' ' + str(best.get('owner_values') or '')[:120] + ', licence: ' + (r.get('licence') or 'none stated')[:60]
               if r.get('answers') else 'DID NOT ANSWER: ' + r.get('error', '')))
    for x in cfg.get('servers') or []:
        try: r = server(x)
        except Exception as e: r = dict(x); r['error'] = str(e)[:140]
        res['servers'].append(r)
        notice(f"{r['st']} {r['what']}: " + (r.get('error') or f"{len(r.get('folders', []))} folders, likely: {', '.join(r.get('likely', [])[:8]) or 'none'}"))
    (D / 'candidates-tested.json').write_text(json.dumps(res, indent=1) + '\n')


if __name__ == '__main__':
    try: main()
    except Exception as e: notice(f'stopped: {e}')
    sys.exit(0)
