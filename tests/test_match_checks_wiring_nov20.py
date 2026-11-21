"""Match by more than name: the US builder wiring, switches, rules hash and changelog (kpc_match_checks.py, switch KPC_MATCH_CHECKS; KPC owner, 20 Nov 2026).
Invented parks, records and facts only. No network: a socket guard refuses any connection."""
import gzip, json, os, pathlib, re, socket, subprocess, sys, tempfile

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


def test_builder_fails_closed_and_is_wired():
    src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
    fn = src[src.index('def match_checks_pass('):src.index('def _tract_store(')]
    assert 'raise RuntimeError' in fn and 'if not facts:' in fn                   # no facts file = the state is held
    assert 'MC.pass_state(' in fn and "_kr('KPC_MATCH_CHECKS')" in fn
    run_ = src[src.index('def run(st):'):]
    assert run_.index('_mc = match_checks_pass(') < run_.index('nonum = sorted(')    # before the counts and the save
    assert "notice(f'US key {st}', f'FAILED: {e}'); continue" in src              # a raise in run() writes no key file


def test_builder_pass_raises_without_facts():
    # the builder's own function, read from its source and run alone (importing the builder would start a build)
    src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
    fn = src[src.index('def match_checks_pass('):src.index('def _tract_store(')]

    class _PFR:
        @staticmethod
        def parks(): return {}
    ns = {'_kr': lambda name: True, 'PFR': _PFR, 'MC': MC}
    exec(fn, ns)
    try:
        ns['match_checks_pass']('ZZ', {}, [], {}, set())
    except RuntimeError as e:
        assert 'held' in str(e)
    else:
        raise AssertionError('no facts must hold the state')
    assert ns['match_checks_pass']('ZZ', {}, [], {}, set(), on=False) == {}

    class _MC:                                                                   # facts present, layer table missing
        @staticmethod
        def load_layer_table(path=None): raise FileNotFoundError('no table')
    ns2 = {'_kr': lambda name: True, 'PFR': _PFR, 'MC': _MC}
    exec(fn, ns2)
    try:
        ns2['match_checks_pass']('ZZ', {}, [], {}, set(), facts={'US-9001': {}})
    except RuntimeError as e:
        assert 'layer table' in str(e) and 'held' in str(e)
    else:
        raise AssertionError('no layer table must hold the state')


def test_rules_hash_and_switches():
    import kpc_key_freeze as F, kpc_key_rules as KR
    assert '.github/scripts/kpc_match_checks.py' in F.RULE_FILES['us-key']
    assert '.github/scripts/kpc_park_facts_read.py' in F.RULE_FILES['us-key']
    assert '.github/layer-agency-kind.json' in F.RULE_FILES['us-key']
    assert {'kpc_match_checks_count.py', 'kpc_match_checks_sample.py'} <= F.NOT_RULES
    assert KR.DEFAULTS['KPC_MATCH_CHECKS'] == '0'
    sw = json.load(open(ROOT / '.github/key-switches.json'))['switches']
    assert len(sw['KPC_MATCH_CHECKS']['on']) == 50 and 'KY' not in sw['KPC_MATCH_CHECKS']['on']
    ch = (ROOT / 'docs/key-rules-change.txt').read_text(encoding='utf-8')
    assert re.search(r'more than name.*APPROVED by owner Nov 20', ch)

if __name__ == '__main__':
    bad = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'):
            try: f(); print('PASS', k)
            except Exception as e: bad += 1; print('FAIL', k, repr(e))  # noqa: BLE001
    print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
