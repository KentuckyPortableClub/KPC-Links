#!/usr/bin/env python3
"""26 Nov 2026, agency spelling (owner 5:17 PM). A record the agency numbers itself is spelled '<layer>0<agency digits>'
('SFT00006' -> 'sgmnb06'); a row number never starts with 0, so the two can never be the same id. Invented records only.
  a  agency 6 -> sgmnb06, row 6 stays sgmnb6, never equal; the shape [a-z]+\\d+ and the layer prefix are unchanged
  b  a PAD-US id is unchanged
  c  two records with the same agency id both keep their row spelling
  d  a waiting layer (AGENCY_ID_LATER) is spelled by its agency id only for an area switched to the fresh store
  e  the same-land proof still proves by the agency id, in a fresh state only
  f  the store reader / outline cutter / scorer spell a file by its own area
Prints PASS / FAIL, ends ALL PASS or SOME FAILED."""
import gzip, json, pathlib, re, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import kpc_same_land as SL  # noqa: E402
import kpc_store_attrs as SA  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


def rec(layer, oid, **a):
    return {'key': f'{layer}{oid}', 'layer': layer, 'record_id': str(oid), 'attributes': dict(a, OBJECTID=oid)}


# a
pk = SA.publish_keys([rec('sgmnb', 6, sft='SFT00006'), rec('sgmnb', 7, sft='SFT00038'), rec('sgmnb', 38)])
check("a: agency forest 6 -> 'sgmnb06'; row 38 keeps 'sgmnb38' beside agency 38 -> 'sgmnb038'", pk == ['sgmnb06', 'sgmnb038', 'sgmnb38'])
check("a: agency 6 and row 6 never equal ('sgmnb06' vs 'sgmnb6')",
      SA.publish_keys([rec('sgmnb', 1, sft='SFT00006'), rec('sgmnb', 6)]) == ['sgmnb06', 'sgmnb6'])
check("a: wildlife area 'WMA0038200' -> 'sgmna038200'", SA.publish_keys([rec('sgmna', 1, uniqueid='WMA0038200')]) == ['sgmna038200'])
check("a: every agency key still matches [a-z]+\\d+ and keeps its layer prefix",
      all(re.fullmatch(r'[a-z]+\d+', k) and re.match(r'[a-z]*', k).group(0) == p for k, p in zip(pk, ('sgmnb',) * 3)))
# b
pad = {'key': '237576', 'layer': 'PAD-US', 'record_id': '237576', 'record_name': 'Some Park', 'attributes': {'su_id': 5, 'sft': 'SFT00006'}, 'rings': []}
check('b: a PAD-US id is unchanged', SA.publish_keys([pad]) == ['237576'])
# c
two = SA.publish_keys([rec('sgmnb', 10, sft='SFT00006'), rec('sgmnb', 11, sft='SFT00006'), rec('sgmnb', 12, sft='SFT00007')])
check('c: two records with ONE agency id both fall back to their row spelling; the third keeps its agency spelling',
      two == ['sgmnb10', 'sgmnb11', 'sgmnb07'])
# d
later = [rec('sgtna', 3, tsp_uid=18), rec('sgtna', 4, tsp_uid=19)]
check('d: a waiting layer with no area keeps the row spelling', SA.publish_keys(later) == ['sgtna3', 'sgtna4'])
check('d: ... in a state NOT on the fresh store (US-OH) too', SA.publish_keys(later, 'US-OH') == ['sgtna3', 'sgtna4'])
check("d: ... in a fresh state (US-MN, MN) it is spelled by its agency id", SA.publish_keys(later, 'US-MN') == ['sgtna018', 'sgtna019']
      and SA.publish_keys(later, 'MN') == ['sgtna018', 'sgtna019'])
check('d: the Minnesota layers are spelled by agency id in every area (as before)', SA.publish_keys([rec('sgmnb', 1, sft='SFT00002')], 'US-OH') == ['sgmnb02'])
check('d: agency_fields', SL.agency_fields('sgtna', 'MN') == ('tsp_uid',) and SL.agency_fields('sgtna', 'OH') == () and SL.agency_fields('sgtna') == ())
# e
sq = [[[-90.0, 40.0], [-89.99, 40.0], [-89.99, 40.01], [-90.0, 40.01], [-90.0, 40.0]]]
def sl_rec(oid, uid, name):
    return {'OBJECTID': f'sgtna{oid}', 'Unit_Nm': name, 'GIS_Acres': 100, 'SA': {'tsp_uid': uid}, '_g': {'rings': sq}}
a, b = sl_rec(5, 'TSP-0018', 'Old Name'), sl_rec(900, 'TSP-0018', 'New Name')
lv, note = SL.prove(a, b, SL.id_spec('sgtna', 'MN'))
check(f'e: the same agency id proves the same land in a fresh state ({lv}: {note})', lv == 'id' and 'agency record id' in note)
check('e: ... a state not on the fresh store has no agency id proof for a waiting layer', SL.prove(a, b, SL.id_spec('sgtna', 'OH'))[0] != 'id')
check('e: a Minnesota layer proves by its agency id in any area', 'sft' in SL.id_spec('sgmnb'))
# f
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    for ar in ('US-MN', 'US-OH'):
        doc = {'area': ar, 'kpcstore_layers': True, 'made': '2026-11-26', 'records': [dict(x, q=6, rings=[[-90000000, 40000000, 10000, 0, 0, 10000, -10000, 0]]) for x in (rec('sgtna', 3, tsp_uid=18), rec('sgmnb', 6, sft='SFT00006'))],
               'manifest': {'sgtna': {'complete': True, 'source_count': 1, 'store_count': 1, 'read': '2026-11-26'}}}
        with gzip.open(td / f'{ar}.layer-records.json.gz', 'wt', encoding='utf-8') as fh: json.dump(doc, fh)
    SA.run(str(td), str(td / 'attrs.json.gz'), today='2026-11-26')
    with gzip.open(td / 'attrs.json.gz', 'rt', encoding='utf-8') as fh: r_ = json.load(fh)['records']
    check("f: the store reader spells MN's waiting layer by agency id and OH's by row ('sgtna018' and 'sgtna3' both there)", 'sgtna018' in r_ and 'sgtna3' in r_)
    import kpc_outlines_from_key as OK_
    check('f: the outline cutter spells each area by its own file', 'sgtna018' in OK_.store_records(str(td), 'US-MN') and 'sgtna3' in OK_.store_records(str(td), 'US-OH'))
    import kpc_outline_score as OS_
    by_id, _bn = OS_.store_index(str(td))
    check('f: the outline scorer too', {'sgtna018', 'sgtna3', 'sgmnb06'} <= set(by_id))
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
