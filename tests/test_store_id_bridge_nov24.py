#!/usr/bin/env python3
"""24 Nov 2026 (owner 4:19 AM 'fix your part'): the park-id checks in store mode.
1. kpc_store_attrs.py keeps a state-layer record the store spells 'sgnya@68990' (before: every such record fell out, so New
   York DEC's web-address ids never reached the checks).
2. kpc_us_key.record_attrs_by_name: a saved record whose number the store does not know (the agency renumbered its layer)
   gets the store's id fields only when exactly ONE store record of the same layer has the same name and a size within 1%.
Invented records. Prints PASS / FAIL and ends ALL PASS or SOME FAILED."""
import gzip, json, os, pathlib, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_store_attrs as S  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


check("the store's 'sgnya@68990' is the key's 'sgnya68990'", S.record_key({'key': 'sgnya@68990', 'layer': 'sgnya', 'record_id': '68990'}) == 'sgnya68990')
check('a PAD-US record keeps its number', S.record_key({'key': '3245', 'layer': 'PAD-US', 'record_id': '3245'}) == '3245')
check('a point circle is not a record', S.record_key({'key': 'point-circle', 'layer': 'point-circle', 'record_id': ''}) == '')
r = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_store_attrs.py'), '--selftest'], capture_output=True, text=True)
check('kpc_store_attrs self-test (with the name-and-size index)', 'ALL PASS' in r.stdout)

# the key side: exec only the helper part of kpc_us_key (before 'idx = {}'), as the other tests do
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
start = src.index('RA_USED = {}'); end = src.index('\ndef _maiden6')
ns = {'os': os, 're': __import__('re'), 'json': json, 'gzip': gzip, 'notice': lambda *a: None}
exec(src[start:end], ns)
with tempfile.TemporaryDirectory() as td:
    f = pathlib.Path(td) / 'ra.json.gz'
    doc = {'format': 2, 'records': {'sgzza901': {'URL': 'https://dec.ny.gov/lands/111.html'},
                                    'sgzza902': {'URL': 'https://dec.ny.gov/lands/222.html'},
                                    'sgzza903': {'URL': 'https://dec.ny.gov/lands/333.html'}},
           'by_name': {'sgzza': {'heronmarshwildforest': [[1000.0, 'sgzza901']],
                                 'twinlakes': [[50.0, 'sgzza902'], [50.2, 'sgzza903']]}}}
    with gzip.open(f, 'wt') as fh: json.dump(doc, fh)
    os.environ['KPC_RECORD_ATTRS'] = str(f)
    ns['record_attrs']()
    bridge = ns['record_attrs_by_name']
    check('a renumbered record finds its fields by name and size (within 1%)',
          (bridge('sgzza65000', {'Unit_Nm': 'Heron Marsh Wild Forest', 'GIS_Acres': '1004'}) or {}).get('URL', '').endswith('/111.html'))
    check('a size more than 1% off: no fields', bridge('sgzza65000', {'Unit_Nm': 'Heron Marsh Wild Forest', 'GIS_Acres': '1200'}) is None)
    check('two store records fit: no fields (never a guess)', bridge('sgzza65001', {'Unit_Nm': 'Twin Lakes', 'GIS_Acres': '50.1'}) is None)
    check('another layer: no fields', bridge('sgzzb65000', {'Unit_Nm': 'Heron Marsh Wild Forest', 'GIS_Acres': '1000'}) is None)
    check('no size: no fields', bridge('sgzza65000', {'Unit_Nm': 'Heron Marsh Wild Forest'}) is None)
check('the key uses the bridge only for a record the store does not know and that carries no fields of its own',
      "if not x and not (a.get('SA') or {}):" in src and 'x = record_attrs_by_name(i, a)' in src)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
