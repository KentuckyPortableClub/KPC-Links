#!/usr/bin/env python3
"""Coverage of the ONE source-field table (kpc_source_fields.py) over every layer the keys already read (Nov 6; Brandon: 'this program
is worldwide ... report coverage by country/state'). Metadata only: one '?f=json' per ArcGIS layer (its field list, no records),
through KPC-Data's kpc_manners (robots.txt obeyed, 2 s per host; a host whose robots.txt says no or cannot be read is NOT asked and
is listed as 'not probed (robots)'). WFS layers are listed as 'not probed (wfs)'. Never writes into the keys.

  KPC_MANNERS_DIR=<KPC-Data/.github/scripts> python3 kpc_source_fields_coverage.py [--minutes 20] [--out data/status/source-fields-coverage.json]
Layers: US = KPC-Data/KPC-Links data/state-gis.json (every state-agency layer) + the federal rows of the table; Canada = data/ca-key/
layers.json; world = kpc_world_key.SRC (read from the source text, nothing run).
"""
import ast, json, os, pathlib, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kpc_source_fields as SF  # noqa: E402

ROLES = ('id', 'acres', 'owner', 'parent')
PROV = set('AB BC MB NB NL NS NT NU ON PE QC SK YT'.split())


def world_src():
    # Nov 12 (KPC owner, 2026-11-12; D6): the built-in world sources are data now (data/world-key/area-tables.json 'SRC'); a tree from
    # before D6 still has them as the SRC literal in kpc_world_key.py (read below)
    at = pathlib.Path(__file__).resolve().parents[2] / 'data/world-key/area-tables.json'
    if at.is_file():
        return {cc: [tuple(x) for x in v] for cc, v in (json.loads(at.read_text(encoding='utf-8')).get('SRC') or {}).items()}
    t = (pathlib.Path(__file__).parent / 'kpc_world_key.py').read_text(encoding='utf-8')
    tree = ast.parse(t)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(x, 'id', '') == 'SRC' for x in node.targets):
            return eval(compile(ast.Expression(node.value), 'SRC', 'eval'), {'__builtins__': {'range': range, 'str': str, 'len': len}})  # literal + comprehensions only
    return {}


def layers():
    out = []
    for f in ('data/state-gis.json', os.path.join(os.environ.get('DATA') or '../KPC-Data', 'data/state-gis.json')):
        if os.path.exists(f):
            for st, ls in (json.load(open(f)).get('states') or {}).items():
                for x in ls:
                    if x.get('url'): out.append(('CA', 'CA-' + st, x.get('ag') or x.get('kind') or '', x['url'], 'arcgis') if st in PROV else ('US', 'US-' + st, x.get('ag') or x.get('kind') or '', x['url'], 'arcgis'))
            break
    if os.path.exists('data/ca-key/layers.json'):
        for k, v in json.load(open('data/ca-key/layers.json')).items():
            u = v[0] if isinstance(v, list) else v
            out.append(('CA', 'CA-' + k[:2] if k[:2] in PROV else 'CA (national / other)', k, re.sub(r'/query$', '', u), 'arcgis'))
    try:
        for cc, ls in world_src().items():
            for x in ls: out.append(('world', cc, x[0], x[2], x[1]))
    except Exception as e:  # noqa: BLE001
        print('world SRC not read:', type(e).__name__, e)
    return out


def main():
    a = sys.argv[1:]
    mins = float(a[a.index('--minutes') + 1]) if '--minutes' in a else 20.0
    outf = pathlib.Path(a[a.index('--out') + 1] if '--out' in a else 'data/status/source-fields-coverage.json')
    sys.path.insert(0, os.environ.get('KPC_MANNERS_DIR') or '../KPC-Data/.github/scripts')
    import kpc_manners as KM
    M = KM.Manners('KPC source-field coverage (layer field lists only)')
    end = time.time() + mins * 60
    rows, seen = [], {}
    for grp, area, label, url, kind in layers():
        r = {'group': grp, 'area': area, 'layer': label, 'url': url}
        key = SF.find(url, label)
        r['table_row'] = key['key'] if key else None
        if kind not in ('arcgis', 'arcgis_alt'): r['probe'] = f'not probed ({kind})'; rows.append(r); continue
        if 'services.arcgis.com/33TOOklri9xpic7U' in url: r['probe'] = 'never (banned server)'; rows.append(r); continue
        if url in seen: fl, r['probe'] = seen[url]
        elif time.time() > end: r['probe'] = 'not probed (time)'; rows.append(r); continue
        else:
            fl = None
            try:
                st, _h, body, _u = M.get(url.rstrip('/') + '?f=json')
                if st == 200 and body:
                    j = json.loads(body if isinstance(body, str) else body.decode('utf-8', 'replace'))
                    fl = [f.get('name') for f in j.get('fields') or [] if f.get('name')] or None
                    r['probe'] = 'ok' if fl else 'no fields'
                else: r['probe'] = 'not probed (robots)' if KM.robots_block(st) else f'no answer ({st})'
            except Exception as e:  # noqa: BLE001
                r['probe'] = f'error {type(e).__name__}'
            seen[url] = (fl, r.get('probe'))
        if fl:
            mp = SF.mapping(url, label, fl)
            r['how'] = mp['how']
            for k in ROLES: r[k] = mp.get(k) if (mp.get(k) and (mp['how'] == 'auto' or mp.get(k) in fl)) else None
        rows.append(r)
    by = {}
    for r in rows:
        b = by.setdefault(r['area'], {'layers': 0, 'probed': 0, 'table_row': 0, 'id': 0, 'acres': 0, 'owner': 0, 'parent': 0, 'not_probed': 0})
        b['layers'] += 1; b['table_row'] += bool(r.get('table_row'))
        if r.get('probe') == 'ok':
            b['probed'] += 1
            for k in ROLES: b[k] += bool(r.get(k))
        elif r.get('probe', '').startswith('not probed') or r.get('probe', '').startswith('no answer'): b['not_probed'] += 1
    outf.parent.mkdir(parents=True, exist_ok=True)
    outf.write_text(json.dumps({'about': __doc__.split('\n\n')[0], 'when': time.strftime('%Y-%m-%d %H:%M %Z'), 'by_area': by, 'layers': rows}, indent=1, ensure_ascii=False) + '\n')
    tot = {k: sum(v[k] for v in by.values()) for k in ('layers', 'probed', 'id', 'acres', 'owner', 'parent', 'not_probed')}
    print(f'::notice title=Source-field coverage::{len(by)} areas, ' + ', '.join(f'{k} {v}' for k, v in tot.items()) + f' -> {outf}')


if __name__ == '__main__':
    main()
