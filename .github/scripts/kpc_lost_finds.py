#!/usr/bin/env python3
"""LOST FINDS CHECK (chat 2, Nov 1 2026; Brandon 1:40 PM: 'there is a flaw in our system when we are finding stuff but it never makes
it in'). Run after every US key build. Lists what we FOUND or DECIDED that never reached the key, so a leak is seen the next morning
instead of weeks later:
  A  a person's YES / join / alias in data/us-key/overrides.json, but the park is still a PIN (the record's layer is not read by the
     key, or the record id changed)
  B  a SURE find on an official AREA layer in the outside research (KPC-Data data/intake/external-results.json) for a park still a PIN,
     with no question about it waiting for chat 11 and no NO answer
  C  a SURE find on an official LINE layer for a trail park still a PIN (kpc_finds_lines.py should carry it: if it stays here a week,
     that bot or the trail run failed)
Writes data/us-key/lost-finds.json {made, counts, A, B, C} and one notice. No network. Exit 0 always."""
import glob, json, os, pathlib, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kpc_json_any import MissingInput, glob_json_any, load_json_any  # noqa: E402


def load(p, d):
    try: return json.load(open(p, encoding='utf-8'))
    except Exception: return d  # noqa: BLE001


def main():
    D = pathlib.Path(os.environ.get('DATA') or 'kpcdata')
    state, name = {}, {}
    joined = set()
    for f in glob.glob('data/us-key/US-??.json'):
        st = pathlib.Path(f).stem[3:]
        for r, p in (load(f, {}).get('parks') or {}).items():
            state.setdefault(r, st); name[r] = p.get('n') or name.get(r, '')
            if p.get('m'): joined.add(r)
    pin = lambda r: r in state and r not in joined   # noqa: E731
    ov = load('data/us-key/overrides.json', {}).get('parks') or {}
    A = [[r, state[r], name[r], ', '.join(k for k in ('join', 'alias', 'alias_all') if v.get(k)), str(v.get('why', ''))[-160:]]
         for r, v in sorted(ov.items()) if pin(r) and (v.get('join') or v.get('alias') or v.get('alias_all')) and not v.get('none')]
    # Nov 6: external-results.json and the question files are .gz in KPC-Data. Opening the plain
    # name and treating a miss as {} made every SURE find look like it was never asked.
    qdir = D / 'data/waiting/questions'
    if not qdir.is_dir():
        raise MissingInput(f'{qdir} is missing, so a NO answer would be ignored and the report would look empty')
    asked, said_no = set(), set()
    qfiles = glob_json_any(str(qdir / '*.json'))
    if not qfiles and any(qdir.iterdir()):
        raise MissingInput(f'{qdir} has files but no *.json or *.json.gz')
    for f in qfiles:
        s = load_json_any(f)
        rows = (s.get('open') or s.get('questions') or s.get('rows') or []) if isinstance(s, dict) else s
        rows = list(rows.values()) if isinstance(rows, dict) else rows
        if not isinstance(rows, list): continue
        for q in rows:
            if not isinstance(q, dict): continue
            r = str(q.get('ref') or '')
            if re.match(r'\W*NO\b', str(q.get('answer') or ''), re.I): said_no.add(r)
            elif not q.get('answer'): asked.add(r)
    ext = load_json_any(D / 'data/intake/external-results.json')
    layers = ext.get('layers') or {}
    B, C = {}, {}
    for k, v in (ext.get('pairs') or {}).items():
        if v.get('result') != 'SURE' or '|' not in k: continue
        r, url = k.split('|', 1)
        if not pin(r) or r in said_no or (r in ov and ov[r].get('none')): continue
        g = str((layers.get(url) or {}).get('geometry'))
        row = [r, state[r], name[r], v.get('record_name'), url]
        if 'Polyline' in g: C.setdefault(r, row)
        elif 'Polygon' in g and r not in asked: B.setdefault(r, row)
    doc = {'made': time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime()), 'counts': {'A_decided_not_in_key': len(A), 'B_sure_area_not_asked': len(B), 'C_sure_line_not_drawn': len(C)},
           'about': __doc__.split('\n')[0], 'A': A, 'B': sorted(B.values()), 'C': sorted(C.values())}
    json.dump(doc, open('data/us-key/lost-finds.json', 'w'), indent=1, ensure_ascii=False)
    print(f"::notice title=Lost finds::{len(A)} parks a person said YES / alias to are still a pin; {len(B)} SURE area finds for pins never asked; "
          f"{len(C)} SURE trail lines not drawn yet (data/us-key/lost-finds.json)")


if __name__ == '__main__':
    try: main()
    except MissingInput as e:
        print(f'::error title=Lost finds::{e}')
        sys.exit(1)
    except Exception as e: print(f'::notice title=Lost finds::stopped: {str(e)[:200]}')  # noqa: BLE001
    sys.exit(0)
