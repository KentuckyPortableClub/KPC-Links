#!/usr/bin/env python3
"""Offline test, Nov 4 PM fix bundle item 6 (Brandon's yes relayed via Super Head Bot, 4:53 PM CST Nov 4): the world warning
'BS, CV and NC: every park is a pin now' is a REGRESSION. extra-layers.json (BOT W, Nov 2) lists 35 of Brandon's sheet layers first,
so kpc_world_key.py skipped the sheet layer and lost its park-name field (namef) and type field. Runs the real source-list part of
kpc_world_key.py (everything before COUNTRIES; no network) on the real data files and checks every sheet layer keeps its namef."""
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent.parent
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


import os
os.chdir(HERE)
src = open('.github/scripts/kpc_world_key.py', encoding='utf-8').read()
g = {'__name__': 'kpc_world_key_prefix', '__file__': '.github/scripts/kpc_world_key.py'}
exec(compile(src[:src.index('COUNTRIES = (os.environ')], 'kpc_world_key.py', 'exec'), g)
S = json.load(open('data/world-key/sheet-countries.json', encoding='utf-8'))['countries']
norm = lambda u: str(u).rstrip('/').lower()   # noqa: E731
lost, dup = [], 0
for cc, v in S.items():
    for l in v.get('layers') or []:
        if not l.get('namef'): continue
        src_urls = [str(s[2]) for s in g['SRC'].get(cc, []) if norm(s[2]) == norm(l['url'])]
        if len(src_urls) != 1: lost.append((cc, 'listed %d times' % len(src_urls))); continue
        if (cc, norm(l['url'])) in g['EXTRA_URLS']: dup += 1
        if g['LAYER_NAMEF'].get(src_urls[0]) != l['namef'] or src_urls[0] not in g['SHEET_URLS']: lost.append((cc, l['namef']))
# LAYER_NAMEF is one entry per url (all countries): a layer shared by several countries with different name fields (the FWS / NPS
# layers of UM GU AS) keeps one of them, as before this patch. Those are reported, not counted as lost.
shared = {norm(l['url']) for cc, v in S.items() for l in v.get('layers') or [] if len({l2.get('namef') for c2, v2 in S.items() for l2 in v2.get('layers') or [] if norm(l2['url']) == norm(l['url'])}) > 1}
lost = [x for x in lost if not any(norm(l['url']) in shared for l in S[x[0]]['layers'] if l.get('namef') == x[1])]
print(f'note: {len(shared)} layer url(s) are shared by countries with different name fields (one name field per url, unchanged): ' + ' '.join(sorted(u.split('/services/')[1][:40] for u in shared)))
# the patch only ADDS name fields: no url that had one before gets another
import subprocess
BASE = next((r for r in ('origin/main', 'main') if subprocess.run(['git', 'rev-parse', '-q', '--verify', r], capture_output=True).returncode == 0), 'HEAD')
old_src = subprocess.run(['git', 'show', f'{BASE}:.github/scripts/kpc_world_key.py'], capture_output=True, text=True).stdout
if 'Nov 4 PM fix bundle (item 6' not in old_src:
    g0 = {'__name__': 'old', '__file__': '.github/scripts/kpc_world_key.py'}
    exec(compile(old_src[:old_src.index('COUNTRIES = (os.environ')], 'old', 'exec'), g0)
    changed = [u for u, f in g0['LAYER_NAMEF'].items() if g['LAYER_NAMEF'].get(u) != f]
    check(not changed and set(g0['SRC']) == set(g['SRC']) and all(len(g0['SRC'][c]) == len(g['SRC'][c]) for c in g['SRC']), f"vs {BASE}: no name field changed ({changed[:3]}), the same layers are read; {len(g['LAYER_NAMEF']) - len(g0['LAYER_NAMEF'])} name fields come back")
check(dup >= 30, f'the real data: {dup} sheet layers are also in extra-layers.json (35 counted on Nov 4 main, LR twice)')
check(not lost, f'every sheet layer is read once and keeps its name field + type field (lost: {lost[:8]})')
for cc, f in (('BS', 'AREANAM'), ('CV', 'designacao'), ('NC', 'NOM'), ('BW', 'Label')):
    u = next(str(s[2]) for s in g['SRC'][cc] if norm(s[2]) == norm(S[cc]['layers'][0]['url']))
    check(g['LAYER_NAMEF'].get(u) == f, f'{cc}: the park names are read from {f} again (Nov 4 build: every park a pin)')
check(g['LAYER_NAMEF'].get(next(str(s[2]) for s in g['SRC']['CV'] if 'areas_protegidas' in str(s[2]))) == 'designacao', "CV: Brandon's sheet (designacao) wins over BOT W's 'ilha' (island name)")
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
