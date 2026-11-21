"""Job C (KPC owner, 21 Nov 2026): a hand-copied size counts in the key's size check only when it names its source page.
Invented parks and sizes only. No network."""
import pathlib, socket, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))


def _no_net(*a, **k): raise RuntimeError('no network in tests')
socket.socket.connect = _no_net
import kpc_match_checks as MC  # noqa: E402

PAGE = 'https://agency.invented.example/parks/invented-lake'


def fact(size):
    return {'area': 'US-ZZ', 'name': 'Invented Lake State Park', 'type': 'State Park', 'pin': [40.05, -79.95],
            'link': {'site': 'agency (known)', 'agency': 'ZZ State Parks'}, 'size': size}


def test_a_hand_copy_with_its_page_counts():
    assert MC.size_witnesses(fact({'acres': 2000, 'witness': 'hand_copy', 'source_url': PAGE}))


def test_a_hand_copy_with_no_page_never_counts():
    for src in (None, '', 'page not given', 'see the brochure', 'www', 'https://'):
        assert not MC.size_witnesses(fact({'acres': 2000, 'witness': 'hand_copy', 'source_url': src})), src
    assert not MC.tagged_witness({'acres': 2000, 'witness': 'hand_copy', 'how': 'hand copy (unknown agency, page not given)'})


def test_an_agency_document_is_unchanged():
    assert MC.size_witnesses(fact({'acres': 2000, 'witness': 'agency_document'}))


def test_an_unsourced_hand_copy_casts_no_size_vote():
    recs = {'1': {'OBJECTID': 1, 'Unit_Nm': 'Invented Lake', 'Mang_Type': 'STAT', 'Mang_Name': 'SPR', 'Des_Tp': 'SP', 'GIS_Acres': 2000}}
    for src, want in ((PAGE, ['size']), ('', [])):
        p = {'US-9001': {'n': 'Invented Lake State Park', 't': 'State Park', 'm': [[1, 'Invented Lake', 2000, 'name']], 'c': [], 'g': 'official'}}
        MC.pass_state(p, recs, {'US-9001': fact({'acres': 100, 'witness': 'hand_copy', 'source_url': src})}, lambda r, i: True, st='ZZ', units={})
        assert p['US-9001']['match'].get('why') == want, (src, p['US-9001']['match'])


if __name__ == '__main__':
    bad = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'):
            try: f(); print('PASS', k)
            except Exception as e: bad += 1; print('FAIL', k, repr(e))  # noqa: BLE001
    print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
