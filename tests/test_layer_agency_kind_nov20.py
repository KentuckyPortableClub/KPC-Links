"""Each map layer's owning agency and kind (.github/layer-agency-kind.json, made by kpc_layer_agency_kind.py), 20 Nov 2026.
The agency and kind checks need it. Every layer of the club's table is there, the file matches the rules (no hand edits),
and a layer whose words don't say is 'unknown', never guessed."""
import json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
GEN = ROOT / '.github/scripts/kpc_layer_agency_kind.py'
OUT = ROOT / '.github/layer-agency-kind.json'


def _run(*a):
    return subprocess.run([sys.executable, str(GEN), *a], capture_output=True, text=True, cwd=ROOT)


def test_rules_selftest():
    r = _run('--selftest')
    assert r.returncode == 0 and 'SELF-TEST PASSED' in r.stdout, r.stdout + r.stderr


def test_file_matches_the_rules():
    r = _run('--check')
    assert r.returncode == 0, r.stdout + r.stderr


def test_every_layer_has_agency_and_kind():
    layers = json.loads((ROOT / 'data/us-key/layers.json').read_text(encoding='utf-8'))
    doc = json.loads(OUT.read_text(encoding='utf-8'))
    got = doc['layers']
    missing = sorted(set(layers) - set(got))
    assert not missing, missing
    assert 'PAD-US' in got and 'fws' in got
    for lid, v in got.items():
        assert v['agency'] and v['kind'] and v['why'], lid
    c = doc['counts']
    assert c['agency unknown'] == sum(1 for v in got.values() if v['agency'] == 'unknown')
    assert c['kind unknown'] == sum(1 for v in got.values() if v['kind'] == 'unknown')


if __name__ == '__main__':
    test_rules_selftest(); test_file_matches_the_rules(); test_every_layer_has_agency_and_kind(); print('ALL PASS')
