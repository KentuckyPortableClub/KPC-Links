"""layers.json never_contact is read by the host guard (kpc_net_guard.host_ok and kpc_master.live_ok). KPC owner, 2026-11-11."""
import json, os, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / '.github' / 'scripts'))
import kpc_net_guard as G
import kpc_master as M


def _lj(tmp_path, rows):
    p = tmp_path / 'layers.json'; p.write_text(json.dumps({'layers': rows})); return str(p)


def test_flagged_layer_refused(tmp_path, monkeypatch):
    monkeypatch.setenv('KPC_LAYERS_JSON', _lj(tmp_path, {
        'x1': {'url': 'https://gis.example.org/arcgis/rest/services/Secret/Lands/MapServer/3', 'never_contact': True},
        'x2': {'url': 'https://gis.example.org/arcgis/rest/services/Open/Lands/MapServer/0'}}))
    ok, why = G.host_ok('https://gis.example.org/arcgis/rest/services/Secret/Lands/MapServer/0/query?where=1=1')
    assert not ok and 'never_contact' in why
    assert not M.live_ok('https://GIS.example.org./arcgis/rest/services/secret/lands/MapServer/3')[0]
    assert not M.live_ok('https://gis.example.org/arcgis/rest/services/Secret/Lands/MapServer')[0]
    assert M.live_ok('https://gis.example.org/arcgis/rest/services/Open/Lands/MapServer/0/query')[0]
    assert M.live_ok('https://gis.example.org/arcgis/rest/services/Secret/LandsOther/MapServer/0')[0]


def test_flag_false_or_missing_is_allowed(tmp_path, monkeypatch):
    monkeypatch.setenv('KPC_LAYERS_JSON', _lj(tmp_path, {'x': {'url': 'https://a.example.org/s/MapServer/0', 'never_contact': False}}))
    assert G.host_ok('https://a.example.org/s/MapServer/0')[0]
    monkeypatch.setenv('KPC_LAYERS_JSON', str(tmp_path / 'none.json'))
    assert G.host_ok('https://a.example.org/s/MapServer/0')[0]


def test_malformed_layers_json_fails_closed(tmp_path, monkeypatch):
    p = tmp_path / 'layers.json'; p.write_text('{not json')
    monkeypatch.setenv('KPC_LAYERS_JSON', str(p))
    ok, why = G.host_ok('https://a.example.org/s/MapServer/0')
    assert not ok and 'fail closed' in why


def test_repo_flags_cover_ncnhde():
    flags = G.never_contact_flags(G.LAYERS_JSON)
    assert ('ncnhde.natureserve.org', '/arcgis/rest/services/nc_public/managed_areas') in flags
    for k, r in json.load(open(G.LAYERS_JSON))['layers'].items():
        if r.get('never_contact'): assert not G.host_ok(r['url'])[0], k


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
