#!/usr/bin/env python3
"""FOUND TRAIL LINES -> the trail bot (chat 2, Nov 1 2026; Brandon 1:40 PM: 'there is a flaw in our system when we are finding stuff
but it never makes it in'). The outside research (KPC-Data data/intake/external-results.json) marks a trail park SURE on an official
LINE layer (same proper name, a line within 200 m of the POTA pin), but no bot ever turned those finds into trail lines: the layer
wiring bot (BOT W) skips line layers and the trail bots only read fixed lists. On Nov 1 that was ~100 trail parks still drawn as a pin
(the Mount Vernon Trail among them). This script hands every such find to kpc_us_trails.py (env EXTRA_TRAILS):
  - only result SURE, only polyline layers, only parks that are still a PIN in every state key (no joined piece at all)
  - not when chat 11 / a person said NO to that park + layer (any data/waiting/questions/*.json row with answer NO)
  - the line is read with  <name field> = '<record name>'  AND an envelope of 0.3 deg around the pin (a same-named trail in another
    forest never comes along); federal layers (NPS, Forest Service, BLM, FWS) before state ones; one source per park
  - 'by' names the agency host; the result goes through the waiting room like every trail file (chat 11 checks), then the key
    (kpc_us_key.py TRL) draws it as the park's line + POTA's 100-ft band
Writes the list to argv[1] (default /tmp/finds-lines.json) and data/trails/finds-lines-report.json. No network. Exit 0 always."""
import glob, json, os, pathlib, re, sys

FED = re.compile(r'nps\.gov|fs\.usda\.gov|fs\.fed\.us|blm\.gov|fws\.gov|fBc8EJBxQRMcHlei', re.I)
TRAILY = re.compile(r'\btrail\b|\btrails\b|\broute\b|greenway|\bpath\b|\bway\b|byway|towpath|rail.?trail', re.I)


def load(p, d):
    try: return json.load(open(p, encoding='utf-8'))
    except Exception: return d  # noqa: BLE001


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/finds-lines.json'
    D = pathlib.Path(os.environ.get('DATA') or 'kpcdata')
    ext = load(D / 'data/intake/external-results.json', {})
    pairs, layers = ext.get('pairs') or {}, ext.get('layers') or {}
    pins, names, typ = {}, {}, {}
    for f in glob.glob('data/parkinfo/US-*.json'):
        for r, v in (load(f, {}).get('parks') or {}).items():
            names[r] = v[0]; typ[r] = v[2] if len(v) > 2 else ''
            if len(v) > 6 and v[5] and v[6]: pins[r] = (float(v[5]), float(v[6]))
    joined, seen = set(), set()
    for f in glob.glob('data/us-key/US-*.json'):
        for r, p in (load(f, {}).get('parks') or {}).items():
            seen.add(r)
            if p.get('m'): joined.add(r)
    no = set()
    for f in glob.glob(str(D / 'data/waiting/questions/*.json')):
        s = load(f, {})
        rows = (s.get('open') or s.get('questions') or s.get('rows') or []) if isinstance(s, dict) else s
        rows = list(rows.values()) if isinstance(rows, dict) else rows
        if not isinstance(rows, list): continue
        for q in rows or []:
            if isinstance(q, dict) and re.match(r'\W*NO\b', str(q.get('answer') or ''), re.I):
                no.add((str(q.get('ref') or ''), str(q.get('layer') or q.get('url') or '').rstrip('/')))
    cand = {}
    for k, v in pairs.items():
        if v.get('result') != 'SURE' or '|' not in k: continue
        ref, url = k.split('|', 1)
        L = layers.get(url) or {}
        if 'Polyline' not in str(L.get('geometry')) or not L.get('name_field') or not v.get('record_name'): continue
        if not ref.startswith('US-') or ref not in seen or ref in joined or ref not in pins: continue
        if not (TRAILY.search(names.get(ref, '')) or 'Trail' in typ.get(ref, '')): continue
        if (ref, url.rstrip('/')) in no: continue
        cand.setdefault(ref, []).append((0 if FED.search(url) else 1, url, L, v))
    rows, rep = [], []
    for ref, cs in sorted(cand.items()):
        cs.sort(key=lambda c: c[0]); _, url, L, v = cs[0]
        m = re.match(r'(.+?)/(\d+)$', url.rstrip('/'))
        if not m: continue
        la, lo = pins[ref]; nm = str(v['record_name']).replace("'", "''")
        rows.append({'ref': ref, 'name': names.get(ref) or v['record_name'], 'url': m.group(1), 'layer': int(m.group(2)),
                     'where': f"{L['name_field']} = '{nm}'", 'bbox': [round(lo - .3, 4), round(la - .3, 4), round(lo + .3, 4), round(la + .3, 4)],
                     'kind': 'found', 'by': f"official agency layer '{L.get('title') or ''}' ({L.get('host') or url.split('/')[2]}); sure match found by the outside research, wired by kpc_finds_lines"})
        rep.append([ref, names.get(ref), v['record_name'], url])
    json.dump(rows, open(out, 'w'), indent=1, ensure_ascii=False)
    os.makedirs('data/trails', exist_ok=True)
    json.dump({'about': 'SURE trail-line finds handed to the trail bot (kpc_finds_lines.py)', 'count': len(rows), 'rows': rep},
              open('data/trails/finds-lines-report.json', 'w'), indent=1, ensure_ascii=False)
    print(f"::notice title=Found trail lines::{len(rows)} trail parks still a pin had a SURE official line in the outside research: handed to the trail bot ({len(no)} NO answers respected)")


if __name__ == '__main__':
    try: main()
    except Exception as e: print(f'::notice title=Found trail lines::stopped: {str(e)[:200]}')  # noqa: BLE001
    sys.exit(0)
