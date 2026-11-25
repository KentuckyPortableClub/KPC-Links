#!/usr/bin/env python3
"""24 Nov 2026 (B1, #379): re-found outline-store records ('sgmnb@20': the agency renumbered its layer) never lend their id
fields to whatever record of the key's older copy carries that number. kpc_store_attrs format 4 files them under the key's own
id (key_record_id) when the store has it, else keeps them apart with their name and size; the key (store_fields) uses those
only when its saved record is provably the same record. Runs the REAL key code (the helper part of kpc_us_key, as the other
store-id tests do). Invented records. Prints PASS / FAIL and ends ALL PASS or SOME FAILED."""
import gzip, json, os, pathlib, re, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_store_attrs as S  # noqa: E402
import kpc_key_rules as KR  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


r = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_store_attrs.py'), '--selftest'], capture_output=True, text=True)
check('kpc_store_attrs self-test (format 5: every re-found record kept apart, with its name, size and key_record_id)', 'ALL PASS' in r.stdout)

src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
start = src.index('RA_USED = {}'); end = src.index('\ndef _maiden6')
ns = {'os': os, 're': re, 'json': json, 'gzip': gzip, 'KR': KR, 'notice': lambda *a: None}
exec(src[start:end], ns)
with tempfile.TemporaryDirectory() as td:
    f = pathlib.Path(td) / 'ra.json.gz'
    doc = {'format': 5,
           'records': {'sgzza7': {'URL': 'https://example.org/plain'}},
           'refound': {'sgzzb20': {'URL': 'https://example.org/alpha-refound', '_nm': 'Alpha State Forest', '_ac': 1000.0, '_kid': 'sgzzb15'},
                       'sgzzb31': {'URL': 'https://example.org/no-name'},
                       'sgzzb60': {'URL': 'https://example.org/gamma', '_nm': 'Gamma State Forest', '_ac': 500.0, '_kid': 'sgzzb7'}},
           'by_name': {'sgzzb': {'alphastateforest': [[1000.0, 'sgzzb20@']]}}}
    with gzip.open(f, 'wt') as fh: json.dump(doc, fh)
    os.environ['KPC_RECORD_ATTRS'] = str(f)
    ns['record_attrs']()
    sf = ns['store_fields']
    check('a plain record: fields by its number', sf('sgzza7', {'Unit_Nm': 'X'}) == ('id', {'URL': 'https://example.org/plain'}))
    check("a re-found record naming the key's id (key_record_id), same record: fields",
          sf('sgzzb15', {'Unit_Nm': 'Alpha State Forest', 'GIS_Acres': 1000}) == ('refound', {'URL': 'https://example.org/alpha-refound'}))
    check("key_record_id names a record the key has renumbered since (another forest now): refused (the MN 4:08 AM case)",
          sf('sgzzb7', {'Unit_Nm': 'Delta State Forest', 'GIS_Acres': 500}) == ('refused', None))
    check('a re-found record, same name and size: used, helper keys gone',
          sf('sgzzb20', {'Unit_Nm': 'Alpha State Forest', 'GIS_Acres': 1040}) == ('refound', {'URL': 'https://example.org/alpha-refound'}))
    check('another forest under the same number: refused (the MN case)', sf('sgzzb20', {'Unit_Nm': 'Beta State Forest', 'GIS_Acres': 1000}) == ('refused', None))
    check('same name, size far off: refused', sf('sgzzb20', {'Unit_Nm': 'Alpha State Forest', 'GIS_Acres': 3000})[0] == 'refused')
    check('a re-found record with no name: not proven, refused', sf('sgzzb31', {'Unit_Nm': 'Anything', 'GIS_Acres': 5})[0] == 'refused')
    check('nothing in the store: nothing', sf('sgzzb99', {'Unit_Nm': 'Y'}) == ('', None))
    br = ns['record_attrs_by_name']('sgzzb500', {'Unit_Nm': 'Alpha State Forest', 'GIS_Acres': '1000'})
    check("the name-and-size bridge reaches a re-found entry, without its helper keys", br == {'URL': 'https://example.org/alpha-refound'})
check('the key counts only records that really got fields, and the refused ones apart',
      "RA_USED[st] = nu" in src and "RA_REFUSED[st] = nr" in src and 'refused: another record' in src)
kt = (ROOT / 'tools/pc-keys/kpc_test_keys.py').read_text(encoding='utf-8')
check('the PC test makes its id file again when it is older than format 10 (R1, R5 fields)', 'fmt < 10' in kt)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
