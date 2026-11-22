#!/usr/bin/env python3
"""kpc_keep_fields.py: which agency id fields the key keeps on each saved record (.github/keep-record-fields.json).

The key saves only a few fields of each joined record (kpc_source_fields: id, acres, owner, parent ...). An agency id that the
match checks could compare is lost when its field is not one of them (Minnesota DNR sft on sgmnb, pgrm_project on sgmnc).
This writes the keep-list from two counts-only reports, so it is config, not code:
  --layers  kpc_id_finder.py's layers.csv: every layer whose verdict is "ID found" or "ID on part of the layer" keeps its best id field
  --pairs   kpc_id_crosswalk.py's pairs.csv: every layer field whose pair is SAME ID or MAPPED keeps that field too (sgmnb sft and
            sgmnc pgrm_project are "possible ID" in the finder, but the crosswalk proved them)
WDPA fields are never kept. Layers the US key does not read by prefix (PAD-US, CPCAD, the Canadian and world layers) are kept in the
file as they come, and only the US key's state layers use it today.

  python3 .github/scripts/kpc_keep_fields.py --layers layers.csv --pairs pairs.csv     write .github/keep-record-fields.json
  python3 .github/scripts/kpc_keep_fields.py --selftest
"""
import csv, json, os, re, sys, tempfile

OUT = '.github/keep-record-fields.json'
KEEP_VERDICTS = ('ID found', 'ID on part of the layer')
KEEP_PAIRS = ('SAME ID', 'MAPPED')
TIES = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'link-id-ties.json')
WDPA = re.compile(r'wdpa', re.I)


def _rows(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def build(layers_csv, pairs_csv=None, ties_json=None):
    keep = {}

    def add(layer, field, why):
        if not layer or not field or WDPA.search(field) or field.startswith(':'):
            return
        e = keep.setdefault(layer, {'fields': [], 'why': []})
        if field not in e['fields']:
            e['fields'].append(field)
        if why not in e['why']:
            e['why'].append(why)
    for r in _rows(layers_csv):
        if r.get('verdict') in KEEP_VERDICTS and r.get('best id field'):
            add(r['layer'], r['best id field'], f"id finder: {r['verdict']} ({r.get('id kind') or 'id'}, grade {r.get('grade') or '?'})")
    if pairs_csv:
        for r in _rows(pairs_csv):
            if r.get('verdict') in KEEP_PAIRS and r.get('layer') and r.get('id field'):
                add(r['layer'], r['id field'], f"crosswalk: {r['verdict']} with {r.get('link id kind')}")
    if ties_json and os.path.exists(ties_json):   # job A (21 Nov): the web address fields that carry a link id
        with open(ties_json, encoding='utf-8') as f:
            for t in json.load(f).get('ties') or []:
                add(t.get('layer'), t.get('field'), f"web address carries the {t.get('kind')} (link-id-ties.json)")
    return {'about': "The agency id fields the key keeps on each saved record (kpc_source_fields.keep_fields). Made by "
                     "kpc_keep_fields.py from the id finder's layers.csv, the crosswalk's pairs.csv (counts only) and link-id-ties.json. "
                     "WDPA fields are never kept. Change the inputs or the rule, never this file by hand.",
            'layers': dict(sorted(keep.items()))}


def dumps(doc):
    return json.dumps(doc, indent=1, ensure_ascii=False) + '\n'


def selftest():
    bad = []

    def check(what, cond):
        print(f'  {"ok  " if cond else "FAIL"} {what}')
        if not cond:
            bad.append(what)
    with tempfile.TemporaryDirectory() as t:
        lp, pp = os.path.join(t, 'layers.csv'), os.path.join(t, 'pairs.csv')
        with open(lp, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f); w.writerow(['layer', 'verdict', 'best id field', 'id kind', 'grade'])
            w.writerows([['sgzza', 'ID found', 'UNIT_ID', 'unit id', 'A'], ['sgzzb', 'ID on part of the layer', 'PARK_NO', 'unit id', 'A'],
                         ['sgzzc', 'possible ID (check by eye)', 'sft', 'record id', 'B'], ['sgzzd', 'row number only', 'OBJECTID', 'row number', 'C'],
                         ['sgzze', 'ID found', 'WDPA_PID', 'wdpa', 'A']])
        with open(pp, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f); w.writerow(['link id kind', 'layer', 'id field', 'verdict'])
            w.writerows([['ZZ unit id', 'sgzzc', 'sft', 'SAME ID'], ['ZZ page', 'sgzzd', 'OBJECTID', 'NOT THE SAME']])
        d = build(lp, pp)['layers']
        check('ID found and ID on part keep their best id field', d.get('sgzza', {}).get('fields') == ['UNIT_ID'] and d.get('sgzzb', {}).get('fields') == ['PARK_NO'])
        check('a possible ID the crosswalk proved SAME ID is kept', d.get('sgzzc', {}).get('fields') == ['sft'])
        check('row number only, and a NOT THE SAME pair, keep nothing', 'sgzzd' not in d)
        check('a WDPA field is never kept', 'sgzze' not in d)
        tp = os.path.join(t, 'ties.json')
        json.dump({'ties': [{'kind': 'ZZ page', 'layer': 'sgzzf', 'field': 'URL', 'rx': 'x/(\\d+)'},
                            {'kind': 'ZZ page', 'layer': 'wdpa', 'field': 'WDPA_URL', 'rx': 'x/(\\d+)'}]}, open(tp, 'w'))
        d = build(lp, pp, tp)['layers']
        check('a web address field of link-id-ties.json is kept', d.get('sgzzf', {}).get('fields') == ['URL'])
        check('never a WDPA address field', 'wdpa' not in d)
    print('SELF-TEST PASSED' if not bad else f'SELF-TEST FAILED: {len(bad)}')
    return 0 if not bad else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if '--selftest' in argv:
        return selftest()
    if '--layers' not in argv:
        print(__doc__); return 2
    lp = argv[argv.index('--layers') + 1]
    pp = argv[argv.index('--pairs') + 1] if '--pairs' in argv else None
    tj = argv[argv.index('--ties') + 1] if '--ties' in argv else TIES
    doc = build(lp, pp, tj)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(dumps(doc))
    print(f"wrote {OUT}: {len(doc['layers'])} layers")
    return 0


if __name__ == '__main__':
    sys.exit(main())
