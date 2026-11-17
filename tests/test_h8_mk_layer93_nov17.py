#!/usr/bin/env python3
"""Handoff 8 fix 8 (switch KPC_MK_LAYER_93): North Macedonia's sheet layer MapServer/94 has the monuments, natural rarities and
caves but no national park; MapServer/93 of the same service is the areas layer (Galichica, Mavrovo, Pelister ...). ON reads 93
as well as 94 (code only, no data file), and a record whose own Prot_Stat says 'proposed' never gives official land.
Part 1: the real kpc_world_key.py source list (no network) - OFF reads 94 only, ON reads 94 and 93.
Part 2: the real kpc_world_key.py run offline (tests/kpc_pinfill_fixture.py) on small saved copies whose records carry the real
ids, names, categories and Prot_Stat of the Nov 17 public read; boxes are made up around the real centres.
 - MK-0002 Galichica, MK-0003 Mavrovo, MK-0004 Pelister join (layer 93, 'protected');
 - MK-0074 Mariovo does NOT join: its only record (93 FID 24) is 'proposed' -> to a person, never official land;
 - must NOT: MK-0025 Duvalo (layer 94) joins as before.
Run:  python3 tests/test_h8_mk_layer93_nov17.py"""
import sys as _sys; _sys.dont_write_bytecode = True
import json, os, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests')); sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_pinfill_fixture as H  # noqa: E402  (refuses every socket on import)
import run_match_tests as RMT  # noqa: E402
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)

B = 'https://portal.app.gov.mk/arcgis/rest/services/PPRSM/karta37_PPRSM_namena_na_zemjiste_WMS_novo/MapServer/'
def urls(sw):
    os.environ['KPC_MK_LAYER_93'] = sw
    try: wk = RMT._load('kpc_world_key.py', '\nfor cc in COUNTRIES:')
    finally: os.environ.pop('KPC_MK_LAYER_93', None)
    return [str(s[2]).rstrip('/') for s in wk.SRC.get('MK', [])]
u0, u1 = urls('0'), urls('1')
check(B + '94' in u0 and B + '93' not in u0, 'OFF: North Macedonia reads MapServer/94 only (today)')
check(B + '94' in u1 and B + '93' in u1 and len(u1) == len(u0) + 1, 'ON: it reads 93 as well as 94 (94 keeps the monuments: Duvalo, Prevalec, Konche)')

L93, L94 = 'Заштитени подрачја (areas, MapServer/93)', 'Заштитени подрачја'
def rec(fid, name, cat, stat, la, lo, d, src):
    rs = [[[lo - d, la - d], [lo - d, la + d], [lo + d, la + d], [lo + d, la - d], [lo - d, la - d]]]
    return {'id': fid, 'n': name, 'ty': cat, 'src': src, '_bb': [lo - d, la - d, lo + d, la + d], '_r': rs,
            '_a': {'FID': fid, 'SiteName': name, 'Category': cat, 'Prot_Stat': stat}, 'code': '', 'dc': ''}
R94 = [rec(3, 'Duvalo', 'Natural rarity', 'protected', 41.1695, 20.8369, .002, L94)]
R93 = [rec(96, 'Galichica', 'National park', 'protected', 41.007, 20.856, .12, L93),
       rec(92, 'Mavrovo', 'National park', 'protected', 41.687, 20.667, .15, L93),
       rec(94, 'Pelister', 'National park', 'protected', 40.992, 21.185, .08, L93),
       rec(24, 'Mariovo', 'Protected landscape', 'proposed', 41.167, 21.696, .18, L93)]
def park(n, la, lo): return [n, '', '', '', '', la, lo, None, None, None, 'XX']
PARKS = {'MK': {'MK-0002': park('Galichica National Park', 41.0165, 20.8389), 'MK-0003': park('Mavrovo National Park', 41.6886, 20.7133),
                'MK-0004': park('Pelister National Park', 41.0222, 21.2008), 'MK-0074': park('Mariovo Protected Area', 41.1275, 21.7201),
                'MK-0025': park('Duvalo Protected Area', 41.1694, 20.8368)}}
def build(recs, sw):
    r, out = H.world_build(['MK'], PARKS, {'MK': recs}, {'KPC_MK_LAYER_93': sw})
    return r, json.loads(out.get('data/world-key/MK.json') or '{}').get('parks') or {}
r_off, k_off = build(R94, '0')          # what today's read gives (94 only)
r_on, k_on = build(R94 + R93, '1')      # what the switch's read gives (94 + 93)
r_x, k_x = build(R94 + R93, '0')        # the same 93 records without the 'proposed' rule (to show why it is needed)
check(all(r.returncode == 0 for r in (r_off, r_on, r_x)), 'the three offline builds ran')
m = lambda k, ref: [q[1] for q in (k.get(ref) or {}).get('m') or []]
for ref, nm in (('MK-0002', 'Galichica'), ('MK-0003', 'Mavrovo'), ('MK-0004', 'Pelister')):
    check(not m(k_off, ref) and m(k_on, ref) == [nm], f'{ref} {PARKS["MK"][ref][0]}: OFF nothing (94 has no national park); ON joins {nm} (93)')
check(m(k_x, 'MK-0074') == ['Mariovo'], "without the rule, MK-0074 would join Mariovo (93 FID 24, Prot_Stat 'proposed')")
check(not m(k_on, 'MK-0074') and any('PROPOSED' in q[3] for q in (k_on.get('MK-0074') or {}).get('c') or []),
      "ON: MK-0074 Mariovo does not join; the proposed record goes to a person, never official land")
check(m(k_off, 'MK-0025') == m(k_on, 'MK-0025') == ['Duvalo'], 'must NOT: MK-0025 Duvalo (layer 94) joins as before')
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
