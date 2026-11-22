"""Job B (KPC owner, 2026-11-21): the agency id field is kept on a layer's saved records, from a config keep-list.

Minnesota DNR ids tie on sgmnb (field sft) and sgmnc (field pgrm_project), but the saved record copies dropped those fields, so the
parks could not confirm. The key now adds the keep-list's fields (.github/keep-record-fields.json, made by kpc_keep_fields.py) to a
state layer's query and keeps them in record['SA']. Never a WDPA field. This test lifts the two helpers out of kpc_us_key.py
(importing it would run the key) and invents its records.
"""
import json, os, pathlib, re, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_source_fields as SF  # noqa: E402

SRC = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')


def _helpers():
    start, end = SRC.index('def state_layer_extra('), SRC.index('def _in_box(')
    ns = {'SF': SF, 're': re}
    exec(compile(SRC[start:end], 'kpc_us_key.py', 'exec'), ns)
    return ns['state_layer_extra'], ns['saved_attrs']


def test_sgmnb_keeps_sft_after_save():
    extra, saved = _helpers()
    fields = ['OBJECTID', 'name', 'acres', 'sft', 'Shape__Area']
    mp = SF.mapping('https://example.invalid/arcgis/rest/services/us_mn_state_dnr/bdry_state_forest/FeatureServer/4/query', '', fields)
    sfx = extra('sgmnb', mp, fields, ('OBJECTID', 'name', 'acres'))
    assert 'sft' in sfx, sfx
    rec = saved({'objectid': 7, 'name': 'Invented State Forest', 'acres': 10.0, 'sft': 'SFT0099999'}, sfx)
    assert rec.get('SA', {}).get('sft') == 'SFT0099999', rec


def test_sgmnc_keeps_pgrm_project():
    extra, saved = _helpers()
    fields = ['OBJECTID', 'sna_name', 'pgrm_project']
    sfx = extra('sgmnc', SF.mapping('', '', fields), fields, ('OBJECTID', 'sna_name'))
    assert saved({'objectid': 1, 'sna_name': 'X', 'pgrm_project': 'SNA00999'}, sfx)['SA']['pgrm_project'] == 'SNA00999'


def test_a_field_the_layer_does_not_list_is_not_asked_for():
    extra, _ = _helpers()
    assert 'sft' not in extra('sgmnb', SF.mapping('', '', ['OBJECTID', 'name']), ['OBJECTID', 'name'], ('OBJECTID', 'name'))


def test_keep_list_is_config_and_never_wdpa():
    with tempfile.TemporaryDirectory() as t:
        p = os.path.join(t, 'keep.json')
        json.dump({'layers': {'sgzza': {'fields': ['UNIT_NO', 'WDPA_PID']}}}, open(p, 'w'))
        assert SF.keep_fields('sgzza', path=p) == ['UNIT_NO']
        assert SF.keep_fields('sgzza', ['objectid', 'unit_no', 'wdpa_pid'], path=p) == ['unit_no']
        assert SF.keep_fields('sgzzb', path=p) == []
    keep = json.loads((ROOT / '.github/keep-record-fields.json').read_text(encoding='utf-8'))['layers']
    assert keep['sgmnb']['fields'] == ['sft'] and keep['sgmnc']['fields'] == ['pgrm_project']
    assert not any(re.search(r'wdpa', f, re.I) for e in keep.values() for f in e['fields'])


def test_the_generator_selftest():
    r = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_keep_fields.py'), '--selftest'], capture_output=True, text=True)
    assert r.returncode == 0 and 'SELF-TEST PASSED' in r.stdout, r.stdout + r.stderr


def test_keep_list_is_a_us_rule_file():
    import kpc_key_freeze as F
    assert '.github/keep-record-fields.json' in F.RULE_FILES['us-key'] and '.github/scripts/kpc_source_fields.py' in F.RULE_FILES['us-key']


if __name__ == '__main__':
    for n, f in list(globals().items()):
        if n.startswith('test_'):
            f(); print('PASS', n)
    print('ALL PASS')
