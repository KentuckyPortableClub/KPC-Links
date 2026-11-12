#!/usr/bin/env python3
"""Job 6 (KPC owner, 2026-11-11; world rules change approved for this job): the world key reads three more French PatriNat layers from
the IGN Géoplateforme WFS it already reads the ZNIEFF layers from: patrinat_znieff2_mer (marine ZNIEFF type II; type I sea was already
read), patrinat_cdl (Conservatoire du littoral) and patrinat_pprnn (protection perimeters of national nature reserves).
Offline: every socket is refused and the builder runs on a saved copy (GEO_CACHE_MODE=only). The layer pages are SYNTHETIC fixtures
(tests/fixtures/world_fr_patrinat_nov11/README.md): real ids and names, made-up rectangles placed relative to the three pins.

  1. the three sources are declared like the ZNIEFF ones (kind wfs, same host, label, type name) and nothing else in the list moved;
  2. they are read by the same reader (pull_wfs, same query) and the record ids are the WFS feature ids: znieff2_mer.7, cdl.502, pprnn.1;
  3. the real builder on the fixture set, before / after the new layers: the 'before' build reproduces today's live key for the three parks;
     after it, FR-10548 joins the marine zone (pin inside; the land zone of the same name 2.61 km away is not joined), FR-10432 and FR-11106
     join the national record and lose the EEA copy (W-2), graded official in the key file and by the website rule, pin 2.81 / 3.50 km;
  4. each of the three gets a saved outline the page can draw (data/world-bounds), the EEA-only 'before' parks do not need one;
  5. no other France park's join or grade changes on the fixture set (KPC-Data's whole FR park list when present);
  6. hashes: world 9358c2ede2d5 -> 889d37136cf8 (declared in docs/key-rules-change.txt and the scope file); US, CA and fers unchanged."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import kpc_fr_patrinat_fixture as H   # noqa: E402  (refuses every socket on import)

ok = True
def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)

OLD_WORLD, NEW_WORLD = '9358c2ede2d5', '889d37136cf8'
g = H.load_prefix()
FR = g['SRC']['FR']

# 1. declared like the ZNIEFF sources
ign = [s for s in FR if s[0].startswith('IGN Géoplateforme')]
check([(s[0], s[1], s[2], s[3]) for s in ign] == [(l, 'wfs', H.WFS, t) for l, t in H.OLD_IGN + H.NEW], f'FR reads the 3 old + 3 new Géoplateforme layers, kind wfs on {H.WFS} ({[s[3] for s in ign]})')
check(sum(1 for s in FR if s[3:4] == ('patrinat_znieff1_mer:znieff1_mer',)) == 1 and sum(1 for s in FR if s[3:4] == ('patrinat_znieff2_mer:znieff2_mer',)) == 1,
      'the marine pair is whole: type I sea (already read) and type II sea (new), once each')
check([s[0] for s in FR if not s[0].startswith('IGN Géoplateforme')] == ['EEA Natura 2000', 'EEA nationally designated areas', 'ZNIEFF (INPN data, Esri France) layer 0', 'ZNIEFF (INPN data, Esri France) layer 1'],
      'the other FR sources are as before (EEA x2, the Esri ZNIEFF fallback x2)')
check(all(not s[0].startswith('IGN Géoplateforme ZNIEFF') for s in FR if s[3:4] in (('patrinat_cdl:cdl',), ('patrinat_pprnn:pprnn',))),
      'the CdL / RNN-perimeter labels do not start with "IGN Géoplateforme ZNIEFF" (so they never stop the Esri ZNIEFF fallback)')
check(not any(x[3] in (t for _, t in H.NEW) for c, v in g['SRC'].items() if c != 'FR' for x in v if len(x) > 3), 'no other country reads the new layers')
check(not g['saved_only'](H.WFS), 'the host rules let the Géoplateforme be read live, as for the ZNIEFF layers (robots.txt is still checked at run time)')
check(all(not g['kinds']('FR', l) for l, _ in H.NEW), 'the new labels carry no kind word (no Natura 2000 word), so they decide no kind')

# 2. same reader, same query, WFS feature ids
asked, got = [], {}
for label, typ in H.OLD_IGN[:1] + H.NEW:
    got[label] = H.read_wfs(g, label, typ, asked=asked)
shape = {k for k in asked[0] if k not in ('TYPENAMES',)}
check(all(set(q) - {'TYPENAMES'} == shape and q['SERVICE'] == 'WFS' and q['VERSION'] == '2.0.0' and q['COUNT'] == '1000' and q['STARTINDEX'] == '0' and q['SRSNAME'] == 'EPSG:4326' for q in asked)
      and [q['TYPENAMES'] for q in asked] == [t for _, t in H.OLD_IGN[:1] + H.NEW], 'one page each, the same GetFeature query as the ZNIEFF layer (WFS 2.0, EPSG:4326, COUNT 1000)')
want = {'IGN Géoplateforme ZNIEFF type II sea': 'znieff2_mer.7', 'IGN Géoplateforme Conservatoire du littoral': 'cdl.502', 'IGN Géoplateforme RNN protection perimeters': 'pprnn.1'}
check({l: [r['id'] for r in got[l]] for l in want} == {l: [i] for l, i in want.items()}, f'record ids are the WFS feature ids: {sorted(want.values())}')
check(all(r['n'] == r['_a']['nom_site'] and r['src'] == l and r['ty'] == l and r['_bb'] and r['_r'] and r['_a'].get('id_mnhn') for l in want for r in got[l]),
      'name = nom_site, source = the label, the INPN id kept with the record, outline and box read')
check([r['id'] for r in got[H.OLD_IGN[0][0]]] == ['znieff1.16597'], 'the existing ZNIEFF type I layer gives its ids the same way (znieff1.16597)')

# 3. the real builder, before / after
pk, how = H.parks()
ov = json.load(open(H.ROOT / 'data/world-key/overrides.json', encoding='utf-8'))
ov_base = {'note': ov.get('note'), 'parks': {r: v for r, v in ov['parks'].items() if r not in H.PARKS3}}   # this test needs none of job 6's overrides
kA, sA, _ = H.build(g, H.records(g, new=False), ov_base, pk)
kB, sB, _ = H.build(g, H.records(g, new=True), ov_base, pk)
print(f'     park list: {how}, {len(kB["parks"])} parks')
live = json.load(open(H.ROOT / 'data/world-key/FR.json', encoding='utf-8'))['parks']
strip = lambda p: {k: v for k, v in p.items() if k not in ('bk',)}
for r in ('FR-10432', 'FR-11106'):
    check(strip(kA['parks'][r]) == strip(live[r]) and kA['parks'][r]['g'] == 'approx', f'{r} before: as in the live key (EEA copy {live[r]["m"][0][0]}, approximate, pin well outside)')
check(kA['parks']['FR-10548']['m'] == [] == live['FR-10548']['m'] and [x[1] for x in kA['parks']['FR-10548']['c']] == ['Corniche Varoise'] == [x[1] for x in live['FR-10548']['c']],
      'FR-10548 before: as in the live key (no join; Corniche Varoise only a candidate)')
B = kB['parks']
check(B['FR-10548']['m'] == [['znieff2_mer.7', 'CAP DE SAINT-TROPEZ 2', 'IGN Géoplateforme ZNIEFF type II sea', 'name']] and B['FR-10548']['bk'][:2] == ['znieff2_mer.7', 0.0] and 'far' not in B['FR-10548'],
      'FR-10548 after: joins the marine ZNIEFF-2 znieff2_mer.7, pin inside')
check(not any(str(x[0]) == 'znieff1.16597' for x in B['FR-10548']['m'] + B['FR-10548']['c']) and not any(x[1] == 'Corniche Varoise' for x in B['FR-10548']['m']),
      'FR-10548 after: the land ZNIEFF of the same name (2.61 km away) and Corniche Varoise are not joined')
for r, rid, lab, km in (('FR-10432', 'cdl.502', 'IGN Géoplateforme Conservatoire du littoral', 2.81), ('FR-11106', 'pprnn.1', 'IGN Géoplateforme RNN protection perimeters', 3.50)):
    p = B[r]
    check([x[:3] for x in p['m']] == [[rid, p['m'][0][1], lab]] and p['m'][0][3] == 'name', f'{r} after: joins the national record {rid} by name; the EEA copy is dropped (W-2)')
    check('g' not in p and 'gsrc' not in p and H.web_official(p) is True, f'{r} after: official in the key file (no g) and by the website rule (how = name)')
    check(p['bk'][0] == rid and abs(p['bk'][1] - km) < 0.05 and p.get('far') == 'well outside', f'{r} after: pin {p["bk"][1]} km outside, recorded as before (documented {km})')
check(H.web_official(B['FR-10548']) is True, 'FR-10548 after: official by the website rule')

# 4. saved outlines
check(all(r in sB and sB[r]['s'] == B[r]['m'][0][2] and sB[r]['r'] for r in H.PARKS3), 'after: each of the three has a saved outline from its national record (data/world-bounds)')
check(not any(r in sA for r in H.PARKS3), 'before: none of them had one (EEA-only parks are drawn from the EEA layer by id; FR-10548 had no join)')

# 5. nothing else changes
other = [r for r in kA['parks'] if r not in H.PARKS3]
mch = [r for r in other if (kA['parks'][r].get('m'), kA['parks'][r].get('g')) != (B.get(r, {}).get('m'), B.get(r, {}).get('g'))]
cch = [r for r in other if kA['parks'][r] != B.get(r)]
check(set(kA['parks']) == set(B) and not mch, f'no other France park\'s join or grade changes ({len(other)} parks compared; changed: {mch[:6]})')
check(set(cch) <= {'FR-11523'}, f'only the candidate list of FR-11523 (Salin de saint-tropez, 4 km from the marine zone) gains a similar-name candidate ({cch[:6]})')
check({r for r in sB if r not in H.PARKS3} == set(sA) and all(sA[r] == sB[r] for r in sA), 'no other park\'s saved outline changes')
check(kB['counts']['areas'] == kA['counts']['areas'] + 3 and [s for s in kB['sources'] if s not in kA['sources']] == [], 'three more records read; the key file lists every source either way')

# 6. hashes
import kpc_key_freeze as KF, kpc_preflight as PF   # noqa: E402
got_h = {k: KF.rules_hash(k) for k in ('us-key', 'ca-key', 'world-key', 'fers')}
# fers: the value the changelog declares last (aa7561256260 on this branch; this change adds no fers line), so the open 2-fer PRs
# (#154, #155), which each declare their own fers move, do not have to edit this test when either merges first.
# Nov 12 (KPC owner, 2026-11-12; D6 tables out) CHANGED: later declared moves (US 46ef34a04ab0 -> d4ebfafce438, world 889d37136cf8 -> 1e262d7d3c0a) are the
# newest; each hash must equal the one its newest changelog line names (no literal to edit when a later change of the set moves it again).
check(got_h == {k: PF.newest_hash(k) for k in got_h} and PF.newest_hash('fers') is not None,
      f'world {OLD_WORLD} -> {NEW_WORLD}; US, CA and fers unchanged (fers = the changelog\'s newest fers hash {PF.newest_hash("fers")}) ({got_h})')
log = (H.ROOT / 'docs/key-rules-change.txt').read_text(encoding='utf-8')
sc = json.load(open(H.ROOT / '.github/world-key-rule-scope.json', encoding='utf-8'))
_wl = next((ln for ln in log.splitlines() if f'world rules {OLD_WORLD} -> {NEW_WORLD}' in ln), '')   # Nov 12 (D6) CHANGED: a link of the chain, not the newest line
check('APPROVED, decided_by KPC owner' in _wl and any(c.get('from') == OLD_WORLD for c in sc['changes']) and any(c.get('from') == NEW_WORLD for c in sc['changes']) or PF.newest_hash('world-key') == NEW_WORLD and not PF.check_hash_pair('world-key', OLD_WORLD, NEW_WORLD, log, sc), 'the changelog line says 9358c2ede2d5 -> 889d37136cf8, APPROVED, decided_by KPC owner, with a scope entry from 9358c2ede2d5')
check(json.load(open(H.ROOT / '.github/key-rules-version.json'))['world-key'] == 'v5b', 'the world version line is unchanged (v5b)')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
