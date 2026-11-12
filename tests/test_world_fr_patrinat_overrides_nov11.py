#!/usr/bin/env python3
"""Job 6 (KPC owner, 2026-11-11): the world overrides for the three Nov 11 French parks, on the layers kpc_world_key.py now reads.
  FR-10548  ids [IGN Géoplateforme ZNIEFF type II sea, znieff2_mer.7], no: the land zone znieff1.16597 and Corniche Varoise
  FR-10432  ids [IGN Géoplateforme Conservatoire du littoral, cdl.502]   (today: the EEA copy 5816, approximate)
  FR-11106  ids [IGN Géoplateforme RNN protection perimeters, pprnn.1]   (today: the EEA copy 3819, approximate)
Offline (every socket refused; the real builder on a saved copy, GEO_CACHE_MODE=only) on the SYNTHETIC fixtures of
tests/fixtures/world_fr_patrinat_nov11 (real ids and names, made-up rectangles). Checks:
  1. data/world-key/overrides.json: the three entries in the file's own form, every other entry (FR-14979 too) as on the base e567f6be,
     the file under 1,000,000 bytes and not a rule file (no hash moves with it);
  2. with the layers read: the three join the national record by id (the name agrees too, so the how-text stays 'name'), official;
  3. the record id holds when the name does not: a renamed marine zone / CdL site still joins by id ('reviewed (saved id)'; the key file
     grades it official, the website rule approximate), and W-2 still drops the EEA copy; a land zone renamed to the park's exact name
     would join without the override and is refused with it;
  4. before the layers are read (or when they fail): nothing changes for the three (FR-10548 no join, the two EEA copies approximate);
  5. no other France park's entry changes between the base overrides and these."""
import hashlib, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import kpc_fr_patrinat_fixture as H   # noqa: E402  (refuses every socket on import)

ok = True
def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)
def fp(x): return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()[:16]

OVF = H.ROOT / 'data/world-key/overrides.json'
ov = json.load(open(OVF, encoding='utf-8')); W = ov['parks']
LAB = {'FR-10548': 'IGN Géoplateforme ZNIEFF type II sea', 'FR-10432': 'IGN Géoplateforme Conservatoire du littoral', 'FR-11106': 'IGN Géoplateforme RNN protection perimeters'}
# 1. the file
check(all(W.get(r, {}).get('ids') == [[LAB[r], rid]] for r, rid in H.PARKS3.items()), 'the three entries join source + record id: znieff2_mer.7, cdl.502, pprnn.1')
check(W['FR-10548'].get('no') == ['znieff1.16597', 'Corniche Varoise'] and 'no' not in W['FR-10432'] and 'no' not in W['FR-11106'],
      'FR-10548 refuses the land zone of the same name and Corniche Varoise; the two EEA copies are not refused (they stay the fallback)')
check(all(set(W[r]) == {'ids', 'when', 'why'} | ({'no'} if r == 'FR-10548' else set()) and W[r]['when'] == '2026-11-11' and len(W[r]['why']) > 80 and 'join' not in W[r] for r in H.PARKS3),
      'the file\'s own form: ids / no / when / why (no name join: the real nom_site was not re-read)')
rest = {r: v for r, v in W.items() if r not in H.PARKS3}
check(len(rest) == 1890 and fp(rest) == 'e71534c43b9e187d' and fp(W['FR-14979']) == '9973d62aefc1cc29' and fp(ov['note']) == 'd755c84e5a86ec41',
      'every other entry, FR-14979 included, and the note are as on the base e567f6be')
check(list(W)[-3:] == ['FR-10548', 'FR-10432', 'FR-11106'], 'the three are added at the end, after FR-14979 (no other entry moved)')
check(OVF.stat().st_size < 1_000_000 and OVF.read_text(encoding='utf-8') == json.dumps(ov, indent=1, ensure_ascii=False) + '\n', f'{OVF.stat().st_size:,} bytes, written in the file\'s own layout')
import kpc_key_freeze as KF, kpc_preflight as PF   # noqa: E402
# fers: the changelog's newest fers hash (aa7561256260 on this branch), so an open 2-fer PR that declares its own fers move (#154, #155)
# does not have to edit this test when it merges first.
check(not any('overrides' in f for v in KF.RULE_FILES.values() for f in v) and KF.rules_hash('world-key') == '889d37136cf8' and PF.newest_hash('fers')
      and (KF.rules_hash('us-key'), KF.rules_hash('ca-key'), KF.rules_hash('fers')) == ('46ef34a04ab0', '4b4176190334', PF.newest_hash('fers')),
      'overrides.json feeds no rules hash: world stays 889d37136cf8 (job 6 rules), US / CA / fers unchanged')

g = H.load_prefix(); pk, how = H.parks()
base_ov = {'note': ov['note'], 'parks': rest}
print(f'     park list: {how}')
pg0 = H.pages()
def variant(**names):
    pg = json.loads(json.dumps(pg0))
    for typ, n in names.items(): pg[typ]['features'][0]['properties']['nom_site'] = n
    return pg

# 2. layers read, live overrides
kL, sL, _ = H.build(g, H.records(g, new=True), ov, pk)
kB, _, _ = H.build(g, H.records(g, new=True), base_ov, pk)
L = kL['parks']
for r, rid in H.PARKS3.items():
    p = L[r]
    check([x[0] for x in p['m']] == [rid] and p['m'][0][2] == LAB[r] and p['m'][0][3] == 'name' and 'g' not in p and H.web_official(p) is True and r in sL,
          f'{r}: joins {rid} only, how name, official (key file and website rule), saved outline written')
check(not any(str(x[0]) == 'znieff1.16597' or x[1] == 'Corniche Varoise' for x in L['FR-10548']['m']), 'FR-10548: neither refused record is joined')

# 3. the id holds when the name does not
pgv = variant(**{'patrinat_znieff2_mer:znieff2_mer': 'SYNTHETIC RENAMED MARINE ZONE', 'patrinat_cdl:cdl': 'SYNTHETIC RENAMED CDL SITE'})
kV, sV, _ = H.build(g, H.records(g, new=True, pg=pgv), ov, pk)
for r in ('FR-10548', 'FR-10432'):
    p = kV['parks'][r]
    check([x[0] for x in p['m']] == [H.PARKS3[r]] and p['m'][0][3] == 'reviewed (saved id)' and 'g' not in p and r in sV,
          f'{r}, record renamed: still joins {H.PARKS3[r]} by id; key file official, saved outline written; EEA copy dropped')
    check(H.web_official(p) is False, f'{r}, record renamed: the website rule shows it Approximate (how-text is not a name match)')
kV0, _, _ = H.build(g, H.records(g, new=True, pg=pgv), base_ov, pk)
check(kV0['parks']['FR-10432']['m'][0][0] == 5816 and kV0['parks']['FR-10432'].get('g') == 'approx' and not kV0['parks']['FR-10548']['m'],
      'without the overrides a renamed record would not join (FR-10432 keeps the EEA copy, FR-10548 nothing): the ids are what hold it')
pgl = variant(**{'patrinat_znieff1:znieff1': 'CAP DE SAINT-TROPEZ 2'})
kN0, _, _ = H.build(g, H.records(g, new=True, pg=pgl), base_ov, pk)
kN, _, _ = H.build(g, H.records(g, new=True, pg=pgl), ov, pk)
check(any(str(x[0]) == 'znieff1.16597' for x in kN0['parks']['FR-10548']['m']), 'a land zone named exactly like the park WOULD join without the override (the hazard)')
check([x[0] for x in kN['parks']['FR-10548']['m']] == ['znieff2_mer.7'], 'with the override the land zone is refused by id; only the marine zone joins')

# 4. before the layers are read (or when one fails): no change for the three
kA, _, _ = H.build(g, H.records(g, new=False), ov, pk)
live = json.load(open(H.ROOT / 'data/world-key/FR.json', encoding='utf-8'))['parks']
check(all(kA['parks'][r]['m'] == live[r]['m'] and kA['parks'][r].get('g') == live[r].get('g') for r in H.PARKS3),
      'without the new layers the three stay as in the live key (FR-10548 no join; FR-10432 / FR-11106 the EEA copy, approximate)')

# 5. nothing else changes
diff = [r for r in kB['parks'] if r not in H.PARKS3 and kB['parks'][r] != L.get(r)]
check(set(kB['parks']) == set(L) and not diff, f'no other France park\'s entry changes with these overrides ({len(kB["parks"]) - 3} compared; changed: {diff[:6]})')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
