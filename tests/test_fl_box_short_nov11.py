"""FL sgflf short read (KPC owner, 2026-11-11): Florida's box takes in the Keys, and the master step refuses a one-state live read
that the box cut short of the layer's own total."""
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / '.github' / 'scripts'))
import kpc_master_fill as F

ROOT = pathlib.Path(__file__).resolve().parents[1]
_SRC = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')


def _chunk(a, b):
    i = _SRC.index(a); return _SRC[i:_SRC.index(b, i)]


class K:   # st_box and BOX_ADD only, run from the source (importing kpc_us_key runs a key build and writes key files)
    import os as _os
    _ns = {'json': json, 'os': _os}
    _cwd = _os.getcwd()
    _os.chdir(ROOT)
    try:
        exec(compile('STB = None\n' + _chunk('def st_box(st):', 'def fws_state('), 'kpc_us_key.py', 'exec'), _ns)
        st_box = staticmethod(lambda st, _n=_ns: _n['st_box'](st)); BOX_ADD = _ns['BOX_ADD']
        _ns['st_box']('FL')
    finally: _os.chdir(_cwd)


def test_fl_box_takes_in_the_keys():
    b = K.st_box('FL')
    for lon, lat in [(-81.78, 24.55), (-80.62, 24.90), (-82.87, 24.63), (-80.38, 25.12)]:   # Key West, Lignumvitae, Dry Tortugas, Key Largo
        assert b[0] <= lon <= b[2] and b[1] <= lat <= b[3], (lon, lat, b)
    assert b[3] > 30.9 and b[0] < -87.5   # still the panhandle


def test_other_boxes_unchanged():
    assert set(K.BOX_ADD) == {'FL'}
    ga = K.st_box('GA'); assert ga[1] > 30.0


def test_box_short_refuses(tmp_path):
    (tmp_path / 'layers.json').write_text(json.dumps({'layers': {}, 'caches': {}}))
    meta = {'area': 'US-FL', 'layer': 'sgflf', 'source': 'live', 'count_layer': 79689}
    why = F.box_short(meta, 77144, tmp_path)
    assert 'SHORT' in why and '2545' in why
    assert F.box_short(meta, 79689, tmp_path) == ''
    assert F.box_short({**meta, 'source': 'hand'}, 10, tmp_path) == ''
    assert F.box_short({k: v for k, v in meta.items() if k != 'count_layer'}, 10, tmp_path) == ''


def test_box_short_outside_box_ok(tmp_path):
    (tmp_path / 'layers.json').write_text(json.dumps({'layers': {'US-TX.sgtxa': {'outside_box_ok': 3}}, 'caches': {}}))
    meta = {'area': 'US-TX', 'layer': 'sgtxa', 'source': 'live', 'count_layer': 100}
    assert F.box_short(meta, 97, tmp_path) == ''
    assert F.box_short(meta, 96, tmp_path) != ''


def test_scope_entry_for_fl_box():
    d = json.load(open(pathlib.Path(__file__).resolve().parents[1] / '.github' / 'us-key-rule-scope.json'))
    e = next(c for c in d['changes'] if c['id'] == '2026-11-11-fl-box-keys')   # Nov 11 r3: a later entry follows it
    assert e['id'] == '2026-11-11-fl-box-keys' and e['from'] == '9e06aa4b4783' and e['scope'] == {'states': ['US-FL'], 'saved_ids': False}


def test_fl_box_takes_in_the_offshore_dep_parcels():
    """Nov 11 r3 (run 43037613117): 45 FL DEP state-owned parcels off Miami (lon -79.875 to -79.858) were outside the box, so the whole
    hand file (79,689) counted 79,644 in the box and was refused. The east edge is -79.8; Bimini (Bahamas, -79.30) stays outside."""
    b = K.st_box('FL')
    for lon, lat in [(-79.875, 25.941), (-79.858, 25.927)]:
        assert b[0] <= lon <= b[2] and b[1] <= lat <= b[3], (lon, lat, b)
    assert b[2] < -79.30   # North Bimini


def test_scope_entry_for_fl_box_east():
    d = json.load(open(pathlib.Path(__file__).resolve().parents[1] / '.github' / 'us-key-rule-scope.json'))
    e = d['changes'][-1]
    assert e['id'] == '2026-11-11-fl-box-east' and e['from'] == 'ad47ee2ff99a' and e['scope'] == {'states': ['US-FL'], 'saved_ids': False}


def test_hand_file_short_says_state_box(tmp_path):
    import kpc_master as M
    (tmp_path / 'layers.json').write_text(json.dumps({'layers': {}, 'caches': {}}))
    f = tmp_path / 'US-FL.sgflf.geojson.gz'
    M.write_layer_file(f, {'area': 'US-FL', 'layer': 'sgflf', 'source': 'hand', 'count_expected': 3, 'count_raw': 2}, [])
    ok, why = F.apply_layer_file(f, tmp_path, tmp_path, tmp_path / 'parks.json')
    assert not ok and 'SHORT' in why and 'state box' in why and '1 outside' in why


def test_hand_refused_is_an_error(tmp_path, monkeypatch):
    import contextlib, io
    monkeypatch.setenv('RUNNER_TEMP', str(tmp_path))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): F.hand_refused('US-FL sgflf: SHORT, not merged')
    assert buf.getvalue().startswith('::error ')
    assert 'hand file refused' in (tmp_path / 'kpc-hidden.txt').read_text()


class _MP:
    """The two monkeypatch calls these tests use, so the file runs as `python3 -B <file>` (kpc_full_suite.py)."""
    def __init__(self): self.env = {}
    def setenv(self, k, v):
        import os
        self.env.setdefault(k, os.environ.get(k)); os.environ[k] = v
    def undo(self):
        import os
        for k, v in self.env.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v


if __name__ == '__main__':
    import inspect, tempfile, traceback
    ok = True
    for name, fn in sorted((n, f) for n, f in globals().items() if n.startswith('test_') and callable(f)):
        mp = _MP()
        try:
            with tempfile.TemporaryDirectory() as d:
                args = {'tmp_path': pathlib.Path(d), 'monkeypatch': mp}
                fn(**{p: args[p] for p in inspect.signature(fn).parameters})
            print('PASS', name)
        except Exception:  # noqa: BLE001
            ok = False; print('FAIL', name); traceback.print_exc()
        finally: mp.undo()
    print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
