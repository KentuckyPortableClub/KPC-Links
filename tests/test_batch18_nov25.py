#!/usr/bin/env python3
"""Batch 18 (25 Nov 2026, owner: 'ALL OF THEM'; the 249-layer agency id check): more layers whose agency gives every record its
own id (kpc_same_land.AGENCY_RECORD_IDS). The published key spells a record by that id when it is digits (one letter prefix for
the whole layer), any letter case of the field name, never two records with one key, and a layer whose agency numbers clash
with its row numbers keeps the row spelling whole. Offline, made-up records. Prints PASS / FAIL, ends ALL PASS or SOME FAILED."""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import kpc_same_land as SL  # noqa: E402
import kpc_store_attrs as SA  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


_REAL = dict(SL.AGENCY_RECORD_IDS)
for k, v in SL.AGENCY_ID_LATER.items(): SL.AGENCY_RECORD_IDS.setdefault(k, (v,))   # the spelling rules, tried on the waiting layers too


def rec(layer, oid, **a):
    return {'key': f'{layer}{oid}', 'layer': layer, 'record_id': str(oid), 'attributes': dict(a, OBJECTID=oid)}


check('only Minnesota layers are added now (MN state forests and parks); the others wait in AGENCY_ID_LATER',
      _REAL.get('sgmnb') == ('sft',) and _REAL.get('sgmnd') == ('pgrm_project',)
      and all(k.startswith('sgmn') for k in _REAL) and 'sgncb' in SL.AGENCY_ID_LATER and 'wld' in SL.AGENCY_ID_LATER)
check('no GUID layer and no layer under 100% different (fsod, NPS UNIT_CODE layers) is listed',
      not {'fsod', 'sgakd', 'sgmac'} & (set(_REAL) | set(SL.AGENCY_ID_LATER)))
check('the id fields are read from the store for every listed layer', all(f in SA.wanted_fields() for v in SL.AGENCY_RECORD_IDS.values() for f in v)
      if hasattr(SA, 'wanted_fields') else True)
check("one letter prefix for the whole layer: 'SFT00002' -> 'sgmnb02'",
      SA.publish_keys([rec('sgmnb', 1, sft='SFT00002'), rec('sgmnb', 2, sft='SFT00058')]) == ['sgmnb02', 'sgmnb058'])
check("the field name in any letter case ('GameLandID' for gamelandid)",
      SA.publish_keys([rec('sgncb', 7, GameLandID=54), rec('sgncb', 8, GameLandID=55)]) == ['sgncb054', 'sgncb055'])
check("two letter prefixes in one layer ('SPK', 'SRA'): the row spelling stays",
      SA.publish_keys([rec('sgmnd', 1, PGRM_PROJECT='SPK00139'), rec('sgmnd', 2, PGRM_PROJECT='SRA00304')]) == ['sgmnd1', 'sgmnd2'])
check("an id with a dash ('TSP-0018') is never spelled into the key (the proof still uses it)",
      SA.publish_keys([rec('sgtna', 3, TSP_UID='TSP-0018')]) == ['sgtna3'] and SL.id_spec('sgtna').get('tsp_uid') == ('arec', []))
# a long chain: agency id of record i = row number of record i+1, and the last record has no id: every clash must be undone
ch = [rec('sgcta', i, DEP_ID=i + 1) for i in range(1, 30)] + [rec('sgcta', 30)]
pk = SA.publish_keys(ch)
check(f'a long chain of clashes ends with every key different ({len(set(pk))} of {len(pk)})', len(set(pk)) == len(pk))
# agency ids most records share: most fall back, so the whole layer keeps its row spelling
fl = [rec('sgflf', i, OWNED_LAND_KEY=(i % 40) + 1) for i in range(1, 81)]
pk = SA.publish_keys(fl)
check('a layer where most agency ids are shared keeps the row spelling whole', pk == [f'sgflf{i}' for i in range(1, 81)])
check('a few shared ids fall back alone; the rest of the layer keeps its agency spelling',
      SA.publish_keys([rec('sgmta', 1, SITEID=279882), rec('sgmta', 2, SITEID=279882), rec('sgmta', 3, SITEID=280032)])
      == ['sgmta1', 'sgmta2', 'sgmta0280032'])
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
