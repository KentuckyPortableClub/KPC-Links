"""Match by more than name: the graded-sample re-score (counts only; the sample is read at run time, never kept here) (kpc_match_checks.py, switch KPC_MATCH_CHECKS; KPC owner, 20 Nov 2026).
Invented parks, records and facts only. No network: a socket guard refuses any connection."""
import csv, gzip, json, os, pathlib, re, socket, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))


def _no_net(*a, **k): raise RuntimeError('no network in tests')
socket.socket.connect = _no_net
import kpc_match_checks as MC  # noqa: E402

UNITS = {'INVP': {'ZZ'}, 'OTHR': {'YY'}}
TAG = {'witness': 'agency_document', 'witness_counts': True}   # a park-facts size tag that counts
TABLE = {'nps': {'agency': 'NPS', 'kind': 'park'}, 'fws': {'agency': 'FWS', 'kind': 'refuge'}, 'sgzza': {'agency': 'state parks', 'kind': 'park'}}
SQ = [[[-80.0, 40.0], [-79.9, 40.0], [-79.9, 40.1], [-80.0, 40.1], [-80.0, 40.0]]]   # about 2,100 acres
STATE_LINK = {'site': 'agency (known)', 'agency': 'ZZ State Parks'}
NPS_LINK = {'site': 'agency (known)', 'agency': 'US National Park Service', 'id_kind': 'NPS unit code', 'id_value': 'INVP'}


def fact(name='Invented Lake State Park', kind='State Park', link=None, size=None, page=None, area='US-ZZ'):
    f = {'area': area, 'name': name, 'type': kind, 'pin': [40.05, -79.95]}
    if link: f['link'] = dict({'page_kind': 'own page', 'usable': True, 'id_shared_by': 1, 'shared_by': 1}, **link)
    if size: f['size'] = dict({'how': 'name+kind', 'flags': []}, **size)
    if page: f['page'] = page
    return f


def srec(oid=1, name='Invented Lake', **kw):
    return dict({'OBJECTID': oid, 'Unit_Nm': name, 'Mang_Type': 'STAT', 'Mang_Name': 'SPR', 'Des_Tp': 'SP', 'GIS_Acres': 2000}, **kw)


def park(name='Invented Lake State Park', rows=None):
    return {'n': name, 't': 'State Park', 'm': rows if rows is not None else [[1, 'Invented Lake', 2000, 'name']], 'c': [], 'g': 'official'}


def run(parks, recs, facts, place=True, **kw):
    return MC.pass_state(parks, recs, facts, lambda ref, ids: place, st='ZZ', units=UNITS, **kw)


def test_sample_rescore_counts_only():
    V = 'is_our_outline_the_park (YES / NO / PART / BIGGER / CANNOT TELL)'
    W = 'records_that_are_not_the_park (ids)'
    R = 'our_outline_records (id | name | acres as the layer gives them)'
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t)
        for d in ('keys', 'cache', 'sample/answers-pass1', 'sample/kit-keys'): (t / d).mkdir(parents=True)
        key = {'parks': {'US-9001': {'n': 'Invented Lake State Park', 't': 'State Park', 'm': [[1, 'Invented Lake', 2000, 'name']], 'c': []},
                         'US-9003': {'n': 'Invented Ridge State Park', 't': 'State Park', 'm': [[3, 'Invented Ridge', 2000, 'name']], 'c': []},
                         'US-9004': {'n': 'Invented Bend State Park', 't': 'State Park', 'm': [[4, 'Invented Bend', 2000, 'name']], 'c': []}}}
        (t / 'keys' / 'US-ZZ.json').write_text(json.dumps(key)); (t / 'keys' / 'layers.json').write_text('{}')
        recs = [dict(srec(), _r=SQ), dict(srec(3, 'Invented Ridge', Mang_Type='FED', Mang_Name='BLM'), _r=SQ), dict(srec(4, 'Invented Bend'), _r=SQ)]
        with gzip.open(t / 'cache' / 'US-ZZ.json.gz', 'wt') as fh: json.dump({'recs': recs}, fh)
        facts = {'parks': {r: fact(name=key['parks'][r]['n'], link=STATE_LINK) for r in key['parks']}}
        with gzip.open(t / 'pf.json.gz', 'wt') as fh: json.dump(facts, fh)
        (t / 'lak.json').write_text(json.dumps({'layers': TABLE}))
        (t / 'units.json').write_text(json.dumps({'units': []}))
        (t / 'sample/kit-keys/sample-answer-key.json').write_text(json.dumps({'plants': ['S9']}))
        with open(t / 'sample/answers-pass1/jobS-random-sample.answers.csv', 'w', newline='') as fh:
            w = csv.DictWriter(fh, ['item', 'ref', 'area', 'name', 'park_type', V, W, R]); w.writeheader()
            w.writerow({'item': 'S1', 'ref': 'US-9001', 'area': 'US-ZZ', V: 'YES', W: '', R: '1 | Invented Lake | 2000'})
            w.writerow({'item': 'S2', 'ref': 'US-9003', 'area': 'US-ZZ', V: 'NO', W: '3', R: '3 | Invented Ridge | 2000'})
            w.writerow({'item': 'S9', 'ref': 'US-9004', 'area': 'US-ZZ', V: 'NO', W: '4', R: '4 | Invented Bend | 2000'})   # a plant: left out
        r = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_match_checks_sample.py'), '--sample', str(t / 'sample'),
                            '--keys', str(t / 'keys'), '--cache', str(t / 'cache'), '--facts', str(t / 'pf.json.gz'),
                            '--units', str(t / 'units.json'), '--layer-table', str(t / 'lak.json'), '--out', str(t / 'o.json')], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        o = json.load(open(t / 'o.json'))
        c = o['counts']
        assert (c['wrong records'], c['wrong caught'], c['right records'], c['right lost']) == (1, 1, 1, 0), c
        assert o['wrong caught by reason'] == {'agency': 1}
        assert 'Invented' not in r.stdout + (t / 'o.json').read_text()

if __name__ == '__main__':
    bad = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'):
            try: f(); print('PASS', k)
            except Exception as e: bad += 1; print('FAIL', k, repr(e))  # noqa: BLE001
    print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
