"""Next round v2 C12 (Brandon's 10 answers, item 6, 'Yes, go with your picks', relayed via Super 8:55 AM CST Nov 5): the DESI
'Protected areas and forests of Queensland' layer was listed twice in data/world-key/extra-layers.json (MapServer/10 under
ParksTerrestrialProtectedAreas and FeatureServer/77 under AdminBoundariesFramework). The copy C7 reads (FeatureServer/77) stays;
MapServer/10 is dropped, so no QLD record is read twice. kpc_key_layers.py will not wire it back: its URL is in kpc_world_key.py
(C7's QLD_LAYERS), which it treats as already read. A data file only: no rules hash moves."""
import json, os, pathlib, types

ROOT = pathlib.Path(__file__).resolve().parent.parent
MS10 = 'spatial-gis.information.qld.gov.au/arcgis/rest/services/environment/parksterrestrialprotectedareas/mapserver/10'
FS77 = 'spatial-gis.information.qld.gov.au/arcgis/rest/services/boundaries/adminboundariesframework/featureserver/77'


def test_extra_layers_lists_the_qld_layer_once():
    au = json.load(open(ROOT / 'data' / 'world-key' / 'extra-layers.json', encoding='utf-8'))['countries']['AU']
    urls = [x['url'].lower().split('://')[-1] for x in au]
    assert MS10 not in urls and urls.count(FS77) == 1 and len(au) == 22


def test_world_key_reads_each_qld_record_once():
    here = os.getcwd(); os.chdir(ROOT)
    try:
        src = (ROOT / '.github' / 'scripts' / 'kpc_world_key.py').read_text(encoding='utf-8')
        m = types.ModuleType('wk'); m.__dict__['__file__'] = str(ROOT / '.github' / 'scripts' / 'kpc_world_key.py')
        exec(compile(src.split('\nfor cc in COUNTRIES:')[0], 'kpc_world_key.py', 'exec'), m.__dict__)
    finally: os.chdir(here)
    q = [s for s in m.SRC['AU'] if 'qld.gov.au' in str(s[2]).lower() and 'estatename' not in str(s) and
         str(s[2]).lower().split('://')[-1] in (MS10, FS77)]
    assert sorted(tuple(s[3]) for s in q) == sorted([(m.QLD_SF,), (m.QLD_REST,)]), q   # FS/77 twice: its SF, then the rest; MapServer/10 not at all


def test_layer_wiring_would_not_add_it_back():
    assert MS10 in (ROOT / '.github' / 'scripts' / 'kpc_world_key.py').read_text(encoding='utf-8').lower()
