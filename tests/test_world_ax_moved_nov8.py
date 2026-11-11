"""Nov 8 (KPC-Links #76): the Aland (AX) Naturreservat layer moved; the key files follow it and the move is declared."""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from kpc_moved_sources import moved_sources, apply_moved
OLD = 'https://kartor.regeringen.ax/arcgis/rest/services/Miljo/Skyddsomraden/MapServer/7'
NEW = 'https://kartor.regeringen.ax/arcgis/rest/services/Miljo/ALR_Naturreservat/MapServer/1'
bad = 0
def check(ok, msg):
    global bad; bad += not ok; print(('PASS ' if ok else 'FAIL ') + msg)
mv = moved_sources(ROOT)
check(any(m['cc'] == 'AX' and m['old'] == OLD and m['new'] == NEW and (m['f0'], m['f1']) == ('Namn', 'Nimi') for m in mv),
      'docs/key-rules-change.txt declares the AX move (#76)')
m = [dict(cc='AX', old='http://a/1', new='http://b/2', f0='Namn', f1='Nimi')]
check(apply_moved('{"url": "http://a/1", "name_field": "Namn"}, {"x": "Namn"}', m) == '{"url": "http://b/2", "name_field": "Nimi"}, {"x": "Namn"}',
      'apply_moved swaps only the url and the name field right after it')
print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
