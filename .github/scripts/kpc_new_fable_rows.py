#!/usr/bin/env python3
"""NEW PARK -> ITS FABLE-BOOK ROW (chat 10, Oct 30 2026; HQ 7:40 AM (b)). Run by kpc-new-refs.yml after kpc_new_refs.py.
For each new US / CA POTA park in kpc-new-refs.json with no OFFICIAL outline in the key: ONE row in
.claude/build/research/fable/<area>.md (one row per park: a park already in the file is left alone), why-not 'new park, no outline yet'.
The GIS hunter areas-run + the look-up read are started on the KPC-Data side (kpc_new_park_flow.py). Never posts. Never fails."""
import glob, json, pathlib, sys

FB = pathlib.Path('.claude/build/research/fable')


def load(p, d=None):
    try: return json.load(open(p, encoding='utf-8'))
    except Exception: return d  # noqa: BLE001


def main():
    items = (load('kpc-new-refs.json', {}) or {}).get('items') or []
    grade, area_of = {}, {}
    for f in glob.glob('data/us-key/US-*.json') + glob.glob('data/ca-key/CA-*.json'):
        for r, v in ((load(f, {}) or {}).get('parks') or {}).items():
            if isinstance(v, dict): grade[r] = v.get('g'); area_of[r] = pathlib.Path(f).stem
    n = 0
    for it in items:
        r = it.get('ref') or ''
        if it.get('prog') != 'pota' or not r.startswith(('US-', 'CA-')) or grade.get(r) == 'official': continue
        st = (it.get('st') or [''])[0]
        area = area_of.get(r) or (f'US-{st}' if r.startswith('US-') and st else '')
        if not area or area == 'US-KY': continue
        f = FB / f'{area}.md'
        if not f.exists(): continue
        t = f.read_text(encoding='utf-8')
        if f'| {r} |' in t: continue
        row = f"| {r} | {it.get('name', '')} | new park (POTA, found {it.get('found', '')}); pin {it.get('la')}, {it.get('lo')} | R-G7 step 1 | why-not: new park, no outline yet (GIS hunter areas-run + look-up read started) | 10 (bot) | {it.get('found', '')} |"
        lines = t.rstrip('\n').split('\n')
        done = next((i for i, l in enumerate(lines) if l.startswith('STATE ') and 'DONE' in l), None)   # 'STATE XX DONE' stays the last line
        if done is not None: lines.insert(done, row)
        else: lines.append(row)
        f.write_text('\n'.join(lines) + '\n', encoding='utf-8'); n += 1
    print(f'::notice title=New parks::{n} Fable-book rows written')


if __name__ == '__main__':
    try: main()
    except Exception as e: print(f'::notice title=New parks::rows stopped ({type(e).__name__}: {e})')  # noqa: BLE001
    sys.exit(0)
